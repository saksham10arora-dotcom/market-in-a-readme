<div align="center">

# gitrade

**The only exchange where you can short `$COMMIT`. On GitHub. In a README.**

[![Engine](https://img.shields.io/github/actions/workflow/status/saksham10arora-dotcom/gitrade/market.yml?style=flat-square&label=engine&logo=githubactions&logoColor=white)](https://github.com/saksham10arora-dotcom/gitrade/actions)
[![Open Orders](https://img.shields.io/github/issues/saksham10arora-dotcom/gitrade?style=flat-square&label=open+orders&color=orange)](https://github.com/saksham10arora-dotcom/gitrade/issues)
[![Python](https://img.shields.io/badge/python-3.11-blue?style=flat-square&logo=python&logoColor=white)](market.py)
[![Infra](https://img.shields.io/badge/infra-zero-black?style=flat-square)](state.json)

[**Live Dashboard**](https://saksham10arora-dotcom.github.io/gitrade/) &nbsp;·&nbsp; [Open a Trade](https://github.com/saksham10arora-dotcom/gitrade/issues/new) &nbsp;·&nbsp; [Order History](https://github.com/saksham10arora-dotcom/gitrade/issues?q=is%3Aissue)

</div>

---

## How to Trade

Open a new issue. The title IS your order. The matching engine runs on every issue open and every 5 min.

| Order Type | Title Format | Example |
|------------|-------------|---------|
| Limit buy | `BUY {qty} {ticker} @ {price}` | `BUY 10 STAR @ 100` |
| Limit sell | `SELL {qty} {ticker} @ {price}` | `SELL 5 COMMIT @ 48` |
| Market buy | `MARKET BUY {qty} {ticker}` | `MARKET BUY 10 FORK` |
| Market sell | `MARKET SELL {qty} {ticker}` | `MARKET SELL 5 STAR` |
| Cancel | `CANCEL #{issue_number}` | `CANCEL #7` |

Tickers: **`$STAR`** **`$COMMIT`** **`$FORK`** -- the currency of GitHub, traded on GitHub.

---

## Exchange Stats

<!-- STATS_START -->
| Ticker | Last | Volume | Spread |
|--------|------|--------|--------|
| **$STAR** | 98.00 | 30 | -- |
| **$COMMIT** | 48.00 | 20 | -- |
| **$FORK** | 9.00 | 100 | -- |
<!-- STATS_END -->

<!-- MERMAID_START -->
```mermaid
xychart-beta
  title "Volume by Ticker"
  x-axis ["$STAR", "$COMMIT", "$FORK"]
  y-axis "Volume" 0 --> 130
  bar [30, 20, 100]
```
<!-- MERMAID_END -->

---

## $STAR &nbsp; `GitHub Stars`

<!-- STAR_START -->
<img src="assets/star-price.svg" width="49%"> <img src="assets/star-depth.svg" width="49%">

<img src="assets/star-flow.svg" width="100%">

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

## $COMMIT &nbsp; `GitHub Commits`

<!-- COMMIT_START -->
<img src="assets/commit-price.svg" width="49%"> <img src="assets/commit-depth.svg" width="49%">

<img src="assets/commit-flow.svg" width="100%">

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

## $FORK &nbsp; `GitHub Forks`

<!-- FORK_START -->
<img src="assets/fork-price.svg" width="49%"> <img src="assets/fork-depth.svg" width="49%">

<img src="assets/fork-flow.svg" width="100%">

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
<img src="assets/leaderboard.svg" width="100%">

| Rank | Trader | Volume | Trades | P&L |
|------|--------|--------|--------|-----|
| 1 | @saksham10arora-dotcom | 9,600 | 6 | +0 |
<!-- LEADERBOARD_END -->

---

## How It Works

```
GitHub Issue: "BUY 10 STAR @ 100"
        ↓
GitHub Actions  (triggers on issue open + cron every 5 min)
        ↓
market.py       parse order → match → update portfolio + leaderboard
charts.py       regenerate 10 SVGs (price, depth, flow per ticker + leaderboard)
        ↓
state.json + README.md + assets/  committed to main
```

- **Matching:** price-time priority (FIFO at each price level)
- **Limit orders:** full fills only
- **Market orders:** partial fills, fills at best available price
- **Cancel:** `CANCEL #<issue_number>` removes your order from the book
- **State:** lives in `state.json` -- the repo IS the exchange

<!-- TIMESTAMP_START -->
> Last updated: 2026-05-26 21:18 UTC
<!-- TIMESTAMP_END -->
