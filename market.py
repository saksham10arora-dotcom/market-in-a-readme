#!/usr/bin/env python3
"""
market-in-a-readme: a live limit order book inside a GitHub README.
Orders submitted via GitHub Issues. Matching runs on every issue event + cron.
State persisted in state.json committed to the repo.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from github import Github

REPO_NAME = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["GITHUB_TOKEN"]

ORDER_RE = re.compile(r"^(BUY|SELL)\s+(\d+(?:\.\d+)?)\s+@\s+(\d+(?:\.\d+)?)$", re.IGNORECASE)
STATE_FILE = "state.json"
README_FILE = "README.md"
ORDER_LABEL = "order"

BOOK_START = "<!-- ORDERBOOK_START -->"
BOOK_END = "<!-- ORDERBOOK_END -->"


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"bids": [], "asks": [], "trades": [], "filled_issues": []}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def parse_order(title):
    m = ORDER_RE.match(title.strip())
    if not m:
        return None
    side, qty, price = m.group(1).upper(), float(m.group(2)), float(m.group(3))
    return {"side": side, "qty": qty, "price": price}


def match_orders(state):
    trades = []
    bids = sorted(state["bids"], key=lambda x: (-x["price"], x["ts"]))
    asks = sorted(state["asks"], key=lambda x: (x["price"], x["ts"]))

    while bids and asks and bids[0]["price"] >= asks[0]["price"]:
        bid, ask = bids[0], asks[0]
        fill_qty = min(bid["qty"], ask["qty"])
        fill_price = ask["price"]  # price-time: ask sets the price

        trades.append({
            "price": fill_price,
            "qty": fill_qty,
            "ts": datetime.now(timezone.utc).strftime("%H:%M UTC"),
            "bid_issue": bid["issue"],
            "ask_issue": ask["issue"],
        })

        bid["qty"] -= fill_qty
        ask["qty"] -= fill_qty

        if bid["qty"] == 0:
            bids.pop(0)
            state["filled_issues"].append(bid["issue"])
        if ask["qty"] == 0:
            asks.pop(0)
            state["filled_issues"].append(ask["issue"])

    state["bids"] = [b for b in bids if b["qty"] > 0]
    state["asks"] = [a for a in asks if a["qty"] > 0]
    state["trades"] = (trades + state["trades"])[:20]  # keep last 20
    return trades


def build_orderbook_md(state):
    bids = sorted(state["bids"], key=lambda x: -x["price"])
    asks = sorted(state["asks"], key=lambda x: x["price"])

    # Merge by price level
    bid_levels = {}
    for b in bids:
        bid_levels[b["price"]] = bid_levels.get(b["price"], 0) + b["qty"]
    ask_levels = {}
    for a in asks:
        ask_levels[a["price"]] = ask_levels.get(a["price"], 0) + a["qty"]

    all_prices = sorted(set(list(bid_levels.keys()) + list(ask_levels.keys())), reverse=True)

    rows = []
    for p in all_prices:
        bid_qty = f"**{bid_levels[p]:.0f}**" if p in bid_levels else ""
        ask_qty = f"**{ask_levels[p]:.0f}**" if p in ask_levels else ""
        rows.append(f"| {bid_qty} | {p:.2f} | {ask_qty} |")

    book_table = "\n".join(rows) if rows else "| | *empty* | |"

    trades_rows = []
    for t in state["trades"][:10]:
        trades_rows.append(f"| {t['ts']} | {t['price']:.2f} | {t['qty']:.0f} |")
    trades_table = "\n".join(trades_rows) if trades_rows else "| | *no trades yet* | |"

    spread = ""
    if bids and asks:
        best_bid = max(bid_levels.keys())
        best_ask = min(ask_levels.keys())
        spread = f"\n> **Best bid:** {best_bid:.2f} | **Best ask:** {best_ask:.2f} | **Spread:** {best_ask - best_bid:.2f}"

    last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""## 📊 Live Order Book
{spread}

| Bid Qty | Price | Ask Qty |
|--------:|------:|:--------|
{book_table}

## 🔄 Recent Trades (last 10)

| Time | Price | Qty |
|------|------:|----:|
{trades_table}

> Last updated: {last_updated}"""


def update_readme(orderbook_md):
    with open(README_FILE) as f:
        content = f.read()

    start = content.find(BOOK_START)
    end = content.find(BOOK_END)
    if start == -1 or end == -1:
        print("ERROR: README markers not found")
        sys.exit(1)

    new_content = (
        content[: start + len(BOOK_START)]
        + "\n"
        + orderbook_md
        + "\n"
        + content[end:]
    )

    with open(README_FILE, "w") as f:
        f.write(new_content)


def main():
    g = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)
    state = load_state()

    # Sync open issues tagged 'order' into the book
    try:
        label = repo.get_label(ORDER_LABEL)
    except Exception:
        label = repo.create_label(ORDER_LABEL, "0075ca")

    open_orders = repo.get_issues(state="open", labels=[ORDER_LABEL])
    known_issues = {o["issue"] for o in state["bids"] + state["asks"]}

    for issue in open_orders:
        if issue.number in known_issues or issue.number in state["filled_issues"]:
            continue
        order = parse_order(issue.title)
        if not order:
            issue.create_comment("❌ Invalid format. Use: `BUY 10 @ 100` or `SELL 5 @ 99`")
            issue.edit(state="closed")
            continue

        order["issue"] = issue.number
        order["ts"] = issue.created_at.timestamp()
        order["user"] = issue.user.login

        if order["side"] == "BUY":
            state["bids"].append(order)
        else:
            state["asks"].append(order)

        issue.create_comment(
            f"✅ Order received: **{order['side']} {order['qty']:.0f} @ {order['price']:.2f}**\n"
            f"Your order is in the book. Check the README for the current state."
        )

    # Match
    new_trades = match_orders(state)

    # Notify on fills
    for t in new_trades:
        for issue_num in [t["bid_issue"], t["ask_issue"]]:
            try:
                issue = repo.get_issue(issue_num)
                issue.create_comment(
                    f"🎯 **FILLED** — {t['qty']:.0f} @ {t['price']:.2f}"
                )
                issue.edit(state="closed")
            except Exception:
                pass

    save_state(state)
    update_readme(build_orderbook_md(state))
    print(f"Done. Bids: {len(state['bids'])}, Asks: {len(state['asks'])}, Trades: {len(state['trades'])}")


if __name__ == "__main__":
    main()
