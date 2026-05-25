#!/usr/bin/env python3
"""
charts.py: Generate SVG charts for all tickers.
Dark theme compatible with GitHub dark mode.
"""

import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

TICKERS    = ["STAR", "COMMIT", "FORK"]
STATE_FILE = "state.json"
ASSETS_DIR = "assets"

BG_COLOR   = "#0d1117"
GRID_COLOR = "#21262d"
TEXT_COLOR = "#c9d1d9"
GREEN      = "#3fb950"
RED        = "#f85149"
WHITE      = "#e6edf3"
ACCENT     = "#58a6ff"


def _style_ax(ax):
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors=TEXT_COLOR, labelsize=7)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_COLOR)
    ax.grid(color=GRID_COLOR, linewidth=0.5, linestyle="--")


def price_chart(trades: list, ticker: str):
    """2-panel chart: price line (top) + volume bars (bottom)."""
    fig = plt.figure(figsize=(6, 2.4))
    fig.patch.set_facecolor(BG_COLOR)
    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.05)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    _style_ax(ax1)
    _style_ax(ax2)

    if len(trades) < 2:
        ax1.text(0.5, 0.5, f"${ticker} -- no trades yet",
                 ha="center", va="center", color=TEXT_COLOR,
                 transform=ax1.transAxes, fontsize=9)
        ax2.set_visible(False)
        fig.tight_layout(pad=0.3)
        fig.savefig(f"{ASSETS_DIR}/{ticker.lower()}-price.svg", format="svg", bbox_inches="tight")
        plt.close(fig)
        return

    prices  = [t["price"] for t in reversed(trades[-50:])]
    volumes = [t["qty"]   for t in reversed(trades[-50:])]
    xs      = list(range(len(prices)))
    color   = GREEN if prices[-1] >= prices[0] else RED

    ax1.plot(xs, prices, color=color, linewidth=1.5, zorder=3)
    ax1.fill_between(xs, prices, min(prices), alpha=0.1, color=color)
    ax1.set_xlim(0, len(xs) - 1)
    ax1.set_title(f"${ticker} price", color=TEXT_COLOR, fontsize=8, pad=3)
    plt.setp(ax1.get_xticklabels(), visible=False)

    ax2.bar(xs, volumes, color=color, alpha=0.6, width=0.8)
    ax2.set_xlim(0, len(xs) - 1)
    ax2.set_xticks([])
    ax2.set_ylabel("vol", color=TEXT_COLOR, fontsize=6)

    fig.tight_layout(pad=0.3)
    fig.savefig(f"{ASSETS_DIR}/{ticker.lower()}-price.svg", format="svg", bbox_inches="tight")
    plt.close(fig)


def depth_chart(bids: list, asks: list, ticker: str):
    """Cumulative bid/ask depth."""
    fig, ax = plt.subplots(figsize=(6, 1.8))
    fig.patch.set_facecolor(BG_COLOR)
    _style_ax(ax)

    bid_levels: dict = {}
    for b in bids:
        bid_levels[b["price"]] = bid_levels.get(b["price"], 0) + b["qty"]
    ask_levels: dict = {}
    for a in asks:
        ask_levels[a["price"]] = ask_levels.get(a["price"], 0) + a["qty"]

    if not bid_levels and not ask_levels:
        ax.text(0.5, 0.5, f"${ticker} -- no orders",
                ha="center", va="center", color=TEXT_COLOR,
                transform=ax.transAxes, fontsize=9)
        fig.tight_layout(pad=0.3)
        fig.savefig(f"{ASSETS_DIR}/{ticker.lower()}-depth.svg", format="svg", bbox_inches="tight")
        plt.close(fig)
        return

    bid_prices = sorted(bid_levels.keys(), reverse=True)
    bid_cumqty = np.cumsum([bid_levels[p] for p in bid_prices])
    ask_prices = sorted(ask_levels.keys())
    ask_cumqty = np.cumsum([ask_levels[p] for p in ask_prices])

    if bid_prices:
        ax.step([bid_prices[-1]] + list(reversed(bid_prices)),
                [0] + list(reversed(bid_cumqty)),
                color=GREEN, linewidth=1.5, where="post")
        ax.fill_between([bid_prices[-1]] + list(reversed(bid_prices)),
                        [0] + list(reversed(bid_cumqty)),
                        step="post", alpha=0.15, color=GREEN)

    if ask_prices:
        ax.step([ask_prices[0]] + ask_prices,
                [0] + list(ask_cumqty),
                color=RED, linewidth=1.5, where="post")
        ax.fill_between([ask_prices[0]] + ask_prices,
                        [0] + list(ask_cumqty),
                        step="post", alpha=0.15, color=RED)

    if bid_prices and ask_prices:
        mid = (max(bid_prices) + min(ask_prices)) / 2
        ax.axvline(mid, color=WHITE, linewidth=0.8, linestyle="--", alpha=0.6)

    ax.set_title(f"${ticker} depth", color=TEXT_COLOR, fontsize=8, pad=3)
    fig.tight_layout(pad=0.3)
    fig.savefig(f"{ASSETS_DIR}/{ticker.lower()}-depth.svg", format="svg", bbox_inches="tight")
    plt.close(fig)


def trade_flow_chart(trades: list, ticker: str):
    """Scatter: trade index vs price, bubble size = qty. Blue dots."""
    fig, ax = plt.subplots(figsize=(6, 1.8))
    fig.patch.set_facecolor(BG_COLOR)
    _style_ax(ax)

    if not trades:
        ax.text(0.5, 0.5, f"${ticker} -- no trades yet",
                ha="center", va="center", color=TEXT_COLOR,
                transform=ax.transAxes, fontsize=9)
        fig.tight_layout(pad=0.3)
        fig.savefig(f"{ASSETS_DIR}/{ticker.lower()}-flow.svg", format="svg", bbox_inches="tight")
        plt.close(fig)
        return

    recent = list(reversed(trades[-30:]))
    xs     = list(range(len(recent)))
    prices = [t["price"] for t in recent]
    sizes  = [max(20, t["qty"] * 3) for t in recent]

    ax.scatter(xs, prices, s=sizes, color=ACCENT, alpha=0.7, zorder=3, edgecolors="none")
    ax.set_xlim(-0.5, max(len(xs) - 0.5, 1))
    ax.set_xticks([])
    ax.set_title(f"${ticker} trade flow", color=TEXT_COLOR, fontsize=8, pad=3)

    fig.tight_layout(pad=0.3)
    fig.savefig(f"{ASSETS_DIR}/{ticker.lower()}-flow.svg", format="svg", bbox_inches="tight")
    plt.close(fig)


def leaderboard_chart(leaderboard: dict):
    """Horizontal bar chart of top traders by volume."""
    fig, ax = plt.subplots(figsize=(6, 2.2))
    fig.patch.set_facecolor(BG_COLOR)
    _style_ax(ax)

    if not leaderboard:
        ax.text(0.5, 0.5, "No traders yet",
                ha="center", va="center", color=TEXT_COLOR,
                transform=ax.transAxes, fontsize=9)
        fig.tight_layout(pad=0.3)
        fig.savefig(f"{ASSETS_DIR}/leaderboard.svg", format="svg", bbox_inches="tight")
        plt.close(fig)
        return

    sorted_lb = sorted(leaderboard.items(), key=lambda x: -x[1]["volume"])[:10]
    names   = [f"@{u[:16]}" for u, _ in reversed(sorted_lb)]
    volumes = [e["volume"]   for _, e in reversed(sorted_lb)]
    colors  = [GREEN if e.get("pnl", 0) >= 0 else RED for _, e in reversed(sorted_lb)]

    ys = range(len(names))
    ax.barh(list(ys), volumes, color=colors, alpha=0.75, height=0.6)
    ax.set_yticks(list(ys))
    ax.set_yticklabels(names, color=TEXT_COLOR, fontsize=7)
    ax.set_xlabel("Volume", color=TEXT_COLOR, fontsize=7)
    ax.set_title("Leaderboard by Volume", color=TEXT_COLOR, fontsize=8, pad=3)
    ax.xaxis.label.set_color(TEXT_COLOR)

    fig.tight_layout(pad=0.4)
    fig.savefig(f"{ASSETS_DIR}/leaderboard.svg", format="svg", bbox_inches="tight")
    plt.close(fig)


def main():
    with open(STATE_FILE) as f:
        state = json.load(f)

    os.makedirs(ASSETS_DIR, exist_ok=True)

    for ticker in TICKERS:
        price_chart(state[ticker]["trades"], ticker)
        depth_chart(state[ticker]["bids"], state[ticker]["asks"], ticker)
        trade_flow_chart(state[ticker]["trades"], ticker)
        print(f"Generated charts for ${ticker}")

    leaderboard_chart(state.get("leaderboard", {}))
    print("Generated leaderboard chart")


if __name__ == "__main__":
    main()
