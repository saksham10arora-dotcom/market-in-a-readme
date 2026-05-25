# market-in-a-readme

> The only exchange where you can short $COMMIT. On GitHub. In a README.

**How to trade:** Open an issue titled `BUY 10 STAR @ 100` | `SELL 5 COMMIT @ 48` | `MARKET BUY 10 FORK` | `CANCEL #7`

Tickers: `$STAR` `$COMMIT` `$FORK` -- the currency of GitHub, traded on GitHub.

---

## Exchange Stats

<!-- STATS_START -->
| Ticker | Last | Volume | Spread |
|--------|------|--------|--------|
| **$STAR** | 98.00 | 30 | -- |
| **$COMMIT** | 48.00 | 20 | -- |
| **$FORK** | 9.00 | 100 | -- |
<!-- STATS_END -->

---

## $STAR

<!-- STAR_START -->
<img src="assets/star-price.svg" width="49%"> <img src="assets/star-depth.svg" width="49%">

**Order Book**

| Bid Qty | Price | Ask Qty |
|--------:|------:|:--------|
| **20** | 100.00 |  |

**Recent Trades**

| Time | Price | Qty |
|------|------:|----:|
| 17:42 UTC | 98.00 | 30 |
<!-- STAR_END -->

---

## $COMMIT

<!-- COMMIT_START -->
<img src="assets/commit-price.svg" width="49%"> <img src="assets/commit-depth.svg" width="49%">

**Order Book**

| Bid Qty | Price | Ask Qty |
|--------:|------:|:--------|
| | *empty* | |

**Recent Trades**

| Time | Price | Qty |
|------|------:|----:|
| 17:44 UTC | 48.00 | 20 |
<!-- COMMIT_END -->

---

## $FORK

<!-- FORK_START -->
<img src="assets/fork-price.svg" width="49%"> <img src="assets/fork-depth.svg" width="49%">

**Order Book**

| Bid Qty | Price | Ask Qty |
|--------:|------:|:--------|
| | *empty* | |

**Recent Trades**

| Time | Price | Qty |
|------|------:|----:|
| 17:43 UTC | 9.00 | 100 |
<!-- FORK_END -->

---

## Leaderboard

<!-- LEADERBOARD_START -->
| Rank | Trader | Volume | Trades | P&L |
|------|--------|--------|--------|-----|
| 1 | @saksham10arora-dotcom | 9,600 | 6 | +0 |
<!-- LEADERBOARD_END -->

---

## How it works

```
GitHub Issue: "BUY 10 STAR @ 100"
        ↓
GitHub Actions (triggers on issue open + every 5 min)
        ↓
market.py: parse → match → update portfolio + leaderboard
charts.py: regenerate 6 SVGs (price + depth per ticker)
        ↓
state.json + README.md + assets/ committed to main
```

- Matching: price-time priority. Full fills for limit orders.
- Market orders fill immediately at best available price.
- Cancel any open order: `CANCEL #<issue_number>`
- State lives in `state.json`. The repo IS the exchange.

<!-- TIMESTAMP_START -->
> Last updated: 2026-05-25 17:44 UTC
<!-- TIMESTAMP_END -->
