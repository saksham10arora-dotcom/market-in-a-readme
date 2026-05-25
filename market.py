#!/usr/bin/env python3
"""
market-in-a-readme v2: 3-ticker exchange ($STAR, $COMMIT, $FORK) in a GitHub README.
Orders submitted via GitHub Issues. State persisted in state.json.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from github import Github

REPO_NAME = os.environ.get("GITHUB_REPOSITORY", "")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

TICKERS = ["STAR", "COMMIT", "FORK"]

LIMIT_RE  = re.compile(r"^(BUY|SELL)\s+(\d+(?:\.\d+)?)\s+(STAR|COMMIT|FORK)\s+@\s+(\d+(?:\.\d+)?)$", re.IGNORECASE)
MARKET_RE = re.compile(r"^MARKET\s+(BUY|SELL)\s+(\d+(?:\.\d+)?)\s+(STAR|COMMIT|FORK)$", re.IGNORECASE)
CANCEL_RE = re.compile(r"^CANCEL\s+#(\d+)$", re.IGNORECASE)

STATE_FILE  = "state.json"
README_FILE = "README.md"


# ---------- state ----------

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        t: {"bids": [], "asks": [], "trades": [], "filled_issues": []}
        for t in TICKERS
    } | {"portfolios": {}, "leaderboard": {}}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ---------- parsing ----------

def parse_order(title: str):
    t = title.strip()

    m = LIMIT_RE.match(t)
    if m:
        side, qty, ticker, price = m.group(1).upper(), float(m.group(2)), m.group(3).upper(), float(m.group(4))
        return {"side": side, "ticker": ticker, "qty": qty, "price": price, "order_type": "LIMIT"}

    m = MARKET_RE.match(t)
    if m:
        side, qty, ticker = m.group(1).upper(), float(m.group(2)), m.group(3).upper()
        return {"side": side, "ticker": ticker, "qty": qty, "price": None, "order_type": "MARKET"}

    m = CANCEL_RE.match(t)
    if m:
        return {"order_type": "CANCEL", "target_issue": int(m.group(1))}

    return None


# ---------- matching ----------

def compute_mid(state: dict, ticker: str):
    bids = state[ticker]["bids"]
    asks = state[ticker]["asks"]
    trades = state[ticker]["trades"]
    if bids and asks:
        return (max(b["price"] for b in bids) + min(a["price"] for a in asks)) / 2
    if trades:
        return trades[0]["price"]
    return None


def compute_pnl(qty: float, avg_cost: float, mid: float) -> float:
    return (mid - avg_cost) * qty


def _update_portfolio(state: dict, user: str, ticker: str, side: str, qty: float, price: float):
    if user not in state["portfolios"]:
        state["portfolios"][user] = {
            t: {"qty": 0.0, "avg_cost": 0.0} for t in TICKERS
        }
    p = state["portfolios"][user][ticker]
    if side == "BUY":
        total_cost = p["avg_cost"] * p["qty"] + price * qty
        p["qty"] += qty
        p["avg_cost"] = total_cost / p["qty"] if p["qty"] > 0 else 0.0
    else:  # SELL
        p["qty"] = max(0.0, p["qty"] - qty)


def _update_leaderboard(state: dict, user: str, volume: float):
    if user not in state["leaderboard"]:
        state["leaderboard"][user] = {"volume": 0.0, "trades": 0, "pnl": 0.0}
    state["leaderboard"][user]["volume"] += volume
    state["leaderboard"][user]["trades"] += 1


def match_orders(state: dict, ticker: str) -> list:
    trades = []
    bids = sorted(state[ticker]["bids"], key=lambda x: (-x["price"], x["ts"]))
    asks = sorted(state[ticker]["asks"], key=lambda x: (x["price"], x["ts"]))

    while bids and asks and bids[0]["price"] >= asks[0]["price"]:
        bid, ask = bids[0], asks[0]
        fill_qty   = min(bid["qty"], ask["qty"])
        fill_price = ask["price"]

        trade = {
            "price": fill_price,
            "qty": fill_qty,
            "ts": datetime.now(timezone.utc).strftime("%H:%M UTC"),
            "bid_issue": bid["issue"],
            "ask_issue": ask["issue"],
            "bid_user":  bid["user"],
            "ask_user":  ask["user"],
        }
        trades.append(trade)

        _update_portfolio(state, bid["user"], ticker, "BUY",  fill_qty, fill_price)
        _update_portfolio(state, ask["user"], ticker, "SELL", fill_qty, fill_price)
        _update_leaderboard(state, bid["user"], fill_qty * fill_price)
        _update_leaderboard(state, ask["user"], fill_qty * fill_price)

        bid["qty"] -= fill_qty
        ask["qty"] -= fill_qty

        if bid["qty"] == 0:
            bids.pop(0)
            state[ticker]["filled_issues"].append(bid["issue"])
        if ask["qty"] == 0:
            asks.pop(0)
            state[ticker]["filled_issues"].append(ask["issue"])

    state[ticker]["bids"]   = [b for b in bids if b["qty"] > 0]
    state[ticker]["asks"]   = [a for a in asks if a["qty"] > 0]
    state[ticker]["trades"] = (trades + state[ticker]["trades"])[:50]
    return trades


def match_market_order(state: dict, ticker: str, side: str, qty: float, issue_num: int, user: str) -> list:
    """Fill a market order against the book. Partial fills allowed."""
    trades = []
    if side == "BUY":
        book = sorted(state[ticker]["asks"], key=lambda x: (x["price"], x["ts"]))
        other_key = "asks"
    else:
        book = sorted(state[ticker]["bids"], key=lambda x: (-x["price"], x["ts"]))
        other_key = "bids"

    remaining = qty
    filled_entries = []

    for entry in book:
        if remaining <= 0:
            break
        fill_qty   = min(remaining, entry["qty"])
        fill_price = entry["price"]

        if side == "BUY":
            bid_issue, ask_issue = issue_num, entry["issue"]
            bid_user,  ask_user  = user, entry["user"]
        else:
            bid_issue, ask_issue = entry["issue"], issue_num
            bid_user,  ask_user  = entry["user"], user

        trade = {
            "price": fill_price, "qty": fill_qty,
            "ts": datetime.now(timezone.utc).strftime("%H:%M UTC"),
            "bid_issue": bid_issue, "ask_issue": ask_issue,
            "bid_user": bid_user,   "ask_user": ask_user,
        }
        trades.append(trade)

        _update_portfolio(state, bid_user, ticker, "BUY",  fill_qty, fill_price)
        _update_portfolio(state, ask_user, ticker, "SELL", fill_qty, fill_price)
        _update_leaderboard(state, bid_user, fill_qty * fill_price)
        _update_leaderboard(state, ask_user, fill_qty * fill_price)

        entry["qty"] -= fill_qty
        remaining    -= fill_qty
        if entry["qty"] == 0:
            filled_entries.append(entry["issue"])
            state[ticker]["filled_issues"].append(entry["issue"])

    state[ticker][other_key] = [e for e in state[ticker][other_key] if e["issue"] not in filled_entries]
    state[ticker]["trades"]  = (trades + state[ticker]["trades"])[:50]
    return trades


# ---------- README building ----------

def _replace_section(readme: str, marker: str, content: str) -> str:
    start_tag = f"<!-- {marker}_START -->"
    end_tag   = f"<!-- {marker}_END -->"
    start = readme.find(start_tag)
    end   = readme.find(end_tag)
    if start == -1 or end == -1:
        return readme
    return readme[: start + len(start_tag)] + "\n" + content + "\n" + readme[end:]


def build_stats_row(state: dict) -> str:
    rows = []
    for ticker in TICKERS:
        trades = state[ticker]["trades"]
        last   = f"{trades[0]['price']:.2f}" if trades else "--"
        volume = sum(t["qty"] for t in trades)
        bids   = state[ticker]["bids"]
        asks   = state[ticker]["asks"]
        if bids and asks:
            spread = f"{min(a['price'] for a in asks) - max(b['price'] for b in bids):.2f}"
        else:
            spread = "--"
        rows.append(f"| **${ticker}** | {last} | {volume:,.0f} | {spread} |")
    header = "| Ticker | Last | Volume | Spread |\n|--------|------|--------|--------|"
    return header + "\n" + "\n".join(rows)


def build_ticker_section(state: dict, ticker: str) -> str:
    bids   = sorted(state[ticker]["bids"],  key=lambda x: -x["price"])
    asks   = sorted(state[ticker]["asks"],  key=lambda x:  x["price"])
    trades = state[ticker]["trades"][:10]

    bid_levels: dict = {}
    for b in bids:
        bid_levels[b["price"]] = bid_levels.get(b["price"], 0) + b["qty"]
    ask_levels: dict = {}
    for a in asks:
        ask_levels[a["price"]] = ask_levels.get(a["price"], 0) + a["qty"]

    all_prices = sorted(set(list(bid_levels) + list(ask_levels)), reverse=True)
    book_rows  = []
    for p in all_prices:
        bq = f"**{bid_levels[p]:.0f}**" if p in bid_levels else ""
        aq = f"**{ask_levels[p]:.0f}**" if p in ask_levels else ""
        book_rows.append(f"| {bq} | {p:.2f} | {aq} |")

    book_table   = "\n".join(book_rows) if book_rows else "| | *empty* | |"
    trades_rows  = [f"| {t['ts']} | {t['price']:.2f} | {t['qty']:.0f} |" for t in trades]
    trades_table = "\n".join(trades_rows) if trades_rows else "| | *no trades yet* | |"

    return f"""\
<img src="assets/{ticker.lower()}-price.svg" width="49%"> <img src="assets/{ticker.lower()}-depth.svg" width="49%">

<img src="assets/{ticker.lower()}-flow.svg" width="100%">

**Order Book**

| Bid Qty | Price | Ask Qty |
|--------:|------:|:--------|
{book_table}

**Recent Trades**

| Time | Price | Qty |
|------|------:|----:|
{trades_table}"""


def build_leaderboard(state: dict) -> str:
    lb = state["leaderboard"]
    if not lb:
        return '<img src="assets/leaderboard.svg" width="100%">\n\n*No trades yet. Open an issue to start trading.*'

    for user, entry in lb.items():
        pnl = 0.0
        for ticker in TICKERS:
            portfolio = state["portfolios"].get(user, {}).get(ticker, {})
            qty       = portfolio.get("qty", 0.0)
            avg_cost  = portfolio.get("avg_cost", 0.0)
            mid       = compute_mid(state, ticker)
            if mid and qty > 0:
                pnl += compute_pnl(qty, avg_cost, mid)
        entry["pnl"] = pnl

    sorted_lb = sorted(lb.items(), key=lambda x: -x[1]["volume"])[:10]
    rows = []
    for rank, (user, entry) in enumerate(sorted_lb, 1):
        pnl_str = f"+{entry['pnl']:.0f}" if entry["pnl"] >= 0 else f"{entry['pnl']:.0f}"
        rows.append(f"| {rank} | @{user} | {entry['volume']:,.0f} | {entry['trades']} | {pnl_str} |")

    header = "| Rank | Trader | Volume | Trades | P&L |\n|------|--------|--------|--------|-----|"
    table = header + "\n" + "\n".join(rows)
    return f'<img src="assets/leaderboard.svg" width="100%">\n\n{table}'


def update_readme(state: dict):
    with open(README_FILE) as f:
        content = f.read()

    content = _replace_section(content, "STATS",       build_stats_row(state))
    for ticker in TICKERS:
        content = _replace_section(content, ticker,    build_ticker_section(state, ticker))
    content = _replace_section(content, "LEADERBOARD", build_leaderboard(state))

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    content = _replace_section(content, "TIMESTAMP",   f"> Last updated: {ts}")

    with open(README_FILE, "w") as f:
        f.write(content)


# ---------- main ----------

def main():
    g    = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)
    state = load_state()

    known_issues = {
        o["issue"]
        for ticker in TICKERS
        for o in state[ticker]["bids"] + state[ticker]["asks"]
    }
    all_filled = {
        i
        for ticker in TICKERS
        for i in state[ticker]["filled_issues"]
    }

    for issue in repo.get_issues(state="open"):
        if issue.number in known_issues or issue.number in all_filled:
            continue

        parsed = parse_order(issue.title)

        if parsed is None:
            issue.create_comment(
                "❌ Invalid format. Use:\n"
                "- `BUY 10 STAR @ 100`\n"
                "- `SELL 5 COMMIT @ 48`\n"
                "- `MARKET BUY 10 FORK`\n"
                "- `CANCEL #7`\n\n"
                "Tickers: `STAR`, `COMMIT`, `FORK`"
            )
            issue.edit(state="closed")
            continue

        if parsed["order_type"] == "CANCEL":
            target = parsed["target_issue"]
            for ticker in TICKERS:
                state[ticker]["bids"] = [b for b in state[ticker]["bids"] if b["issue"] != target]
                state[ticker]["asks"] = [a for a in state[ticker]["asks"] if a["issue"] != target]
            try:
                repo.get_issue(target).create_comment("🚫 Order cancelled.")
                repo.get_issue(target).edit(state="closed")
            except Exception:
                pass
            issue.create_comment(f"✅ Cancelled order #{target}.")
            issue.edit(state="closed")
            continue

        ticker = parsed["ticker"]

        if parsed["order_type"] == "MARKET":
            book_side = state[ticker]["asks"] if parsed["side"] == "BUY" else state[ticker]["bids"]
            if not book_side:
                issue.create_comment(f"❌ No liquidity on the {ticker} {'ask' if parsed['side'] == 'BUY' else 'bid'} side. Try a limit order.")
                issue.edit(state="closed")
                continue
            new_trades = match_market_order(state, ticker, parsed["side"], parsed["qty"], issue.number, issue.user.login)
            issue.create_comment(
                f"🎯 Market order filled: **{sum(t['qty'] for t in new_trades):.0f} {ticker}** across {len(new_trades)} fill(s)."
            )
            issue.edit(state="closed")

        else:  # LIMIT
            order = {
                "issue": issue.number,
                "qty":   parsed["qty"],
                "price": parsed["price"],
                "ts":    issue.created_at.timestamp(),
                "user":  issue.user.login,
            }
            if parsed["side"] == "BUY":
                state[ticker]["bids"].append(order)
            else:
                state[ticker]["asks"].append(order)

            issue.create_comment(
                f"✅ **{parsed['side']} {parsed['qty']:.0f} ${ticker} @ {parsed['price']:.2f}** is in the book.\n"
                "Check the README for the current order book state."
            )

            new_trades = match_orders(state, ticker)
            for t in new_trades:
                for issue_num in [t["bid_issue"], t["ask_issue"]]:
                    try:
                        filled_issue = repo.get_issue(issue_num)
                        filled_issue.create_comment(f"🎯 **FILLED** -- {t['qty']:.0f} ${ticker} @ {t['price']:.2f}")
                        filled_issue.edit(state="closed")
                    except Exception:
                        pass

    save_state(state)
    update_readme(state)
    print(f"Done. State: { {t: {'bids': len(state[t]['bids']), 'asks': len(state[t]['asks']), 'trades': len(state[t]['trades'])} for t in TICKERS} }")


if __name__ == "__main__":
    main()
