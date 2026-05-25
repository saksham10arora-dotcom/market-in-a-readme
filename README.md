# market-in-a-readme

> A fully functioning limit order book inside a GitHub README.
> Submit orders by opening an issue. The matching engine runs every 5 minutes via GitHub Actions.
> Built by [@saksham10arora-dotcom](https://github.com/saksham10arora-dotcom)

## 📬 How to Trade

1. Open a new issue in this repo
2. Title it: `BUY 10 @ 100` or `SELL 5 @ 99`
3. Wait up to 5 minutes for the engine to match your order
4. Check back here -- the order book updates automatically

**Rules:**
- Qty and price can be decimals (`BUY 2.5 @ 100.50`)
- Price-time priority matching (FIFO at each price level)
- Full fills only -- partial fills not yet supported
- The asset is fictional. This is a stunt, not a brokerage.

<!-- ORDERBOOK_START -->
## 📊 Live Order Book


| Bid Qty | Price | Ask Qty |
|--------:|------:|:--------|
| | *empty* | |

## 🔄 Recent Trades (last 10)

| Time | Price | Qty |
|------|------:|----:|
| 16:20 UTC | 100.00 | 10 |

> Last updated: 2026-05-25 16:20 UTC
<!-- ORDERBOOK_END -->

## How it works

```
GitHub Issue (BUY 10 @ 100)
        ↓
GitHub Actions (triggers on issue open + every 5 min)
        ↓
market.py (parses issue, inserts into order book, runs matching)
        ↓
state.json (persists order book state in the repo)
        ↓
README.md (updated with current bids, asks, trades)
```

- Matching: price-time priority. Best bid vs best ask. If bid >= ask, fill at ask price.
- State: committed to `state.json` after every run.
- Fills: matched issues are closed with a comment.

## Stack

- Python + PyGithub
- GitHub Actions (cron + issue trigger)
- Zero external infrastructure. The repo IS the exchange.
