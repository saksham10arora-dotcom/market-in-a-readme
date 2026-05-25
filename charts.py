#!/usr/bin/env python3
"""
charts.py: Generate SVG price charts and depth charts for all tickers.
Outputs to assets/{ticker}-price.svg and assets/{ticker}-depth.svg.
Dark theme compatible with GitHub dark mode.
"""

import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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


def _base_fig():
    fig, ax = plt.subplots(figsize=(6, 1.8))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors=TEXT_COLOR, labelsize=7)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_COLOR)
    ax.grid(color=GRID_COLOR, linewidth=0.5, linestyle="--")
    return fig, ax


def price_chart(trades: list, ticker: str):
    fig, ax = _base_fig()

    if len(trades) < 2:
        ax.text(0.5, 0.5, f"${ticker} -- no trades yet",
                ha="center", va="center", color=TEXT_COLOR,
                transform=ax.transAxes, fontsize=9)
        fig.tight_layout(pad=0.3)
        fig.savefig(f"{ASSETS_DIR}/{ticker.lower()}-price.svg", format="svg", bbox_inches="tight")
        plt.close(fig)
        return

    prices  = [t["price"] for t in reversed(trades[-50:])]
    volumes = [t["qty"]   for t in reversed(trades[-50:])]
    xs      = list(range(len(prices)))
    color   = GREEN if prices[-1] >= prices[0] else RED

    ax2 = ax.twinx()
    ax2.set_facecolor(BG_COLOR)
    ax2.bar(xs, volumes, color=color, alpha=0.25, width=0.8)
    ax2.set_ylim(0, max(volumes) * 5)
    ax2.set_yticks([])
    ax2.spines["right"].set_visible(False)

    ax.plot(xs, prices, color=color, linewidth=1.5, zorder=3)
    ax.fill_between(xs, prices, min(prices), alpha=0.1, color=color)
    ax.set_xlim(0, len(xs) - 1)
    ax.set_xticks([])
    ax.set_title(f"${ticker} price", color=TEXT_COLOR, fontsize=8, pad=3)
    ax.yaxis.label.set_color(TEXT_COLOR)

    fig.tight_layout(pad=0.3)
    fig.savefig(f"{ASSETS_DIR}/{ticker.lower()}-price.svg", format="svg", bbox_inches="tight")
    plt.close(fig)


def depth_chart(bids: list, asks: list, ticker: str):
    fig, ax = _base_fig()

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
    ax.tick_params(colors=TEXT_COLOR, labelsize=7)

    fig.tight_layout(pad=0.3)
    fig.savefig(f"{ASSETS_DIR}/{ticker.lower()}-depth.svg", format="svg", bbox_inches="tight")
    plt.close(fig)


def main():
    with open(STATE_FILE) as f:
        state = json.load(f)

    os.makedirs(ASSETS_DIR, exist_ok=True)

    for ticker in TICKERS:
        price_chart(state[ticker]["trades"], ticker)
        depth_chart(state[ticker]["bids"], state[ticker]["asks"], ticker)
        print(f"Generated charts for ${ticker}")


if __name__ == "__main__":
    main()
