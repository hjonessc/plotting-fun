#!/usr/bin/env python3
"""
plot.py — Pull and plot stock data for a ticker symbol.

Usage:   python plot.py AAPL
         python plot.py AAPL MSFT TSLA

Output:  results/<TICKER>.png for each symbol

Data:    yfinance (no API key required)
  - Top panel:    past year, daily closing price
  - Bottom panel: most recent trading day, 5-minute intervals
"""

import sys
import os
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker


def smart_ylim(series, pad_pct=0.06, min_pad=0.10):
    """Y-axis bounds: data range + padding. Never starts at zero for price data."""
    lo, hi = series.min(), series.max()
    span = hi - lo
    pad = max(span * pad_pct, min_pad)
    return lo - pad, hi + pad


def plot_ticker(symbol: str):
    symbol = symbol.upper()
    ticker = yf.Ticker(symbol)

    # --- Fetch data ---
    year_data = ticker.history(period="1y", interval="1d")
    day_data  = ticker.history(period="5d", interval="5m")  # 5d to catch last trading day

    if year_data.empty:
        print(f"  [{symbol}] No data found — check the ticker symbol.")
        return

    # Trim day_data to the most recent trading day only
    if not day_data.empty:
        last_date = day_data.index[-1].date()
        day_data = day_data[day_data.index.date == last_date]

    # --- Layout ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8), gridspec_kw={"hspace": 0.4})

    last_price  = year_data["Close"].iloc[-1]
    start_price = year_data["Close"].iloc[0]
    ytd_pct     = (last_price - start_price) / start_price * 100
    arrow       = "▲" if ytd_pct >= 0 else "▼"
    ytd_color   = "#2e7d32" if ytd_pct >= 0 else "#c62828"

    fig.suptitle(
        f"{symbol}   ${last_price:,.2f}  {arrow} {abs(ytd_pct):.1f}% past year",
        fontsize=15, fontweight="bold", y=0.98
    )

    # ── Top: year view ──────────────────────────────────────────────────────
    closes = year_data["Close"]
    ax1.plot(year_data.index, closes, linewidth=1.4, color="#1565C0")
    ax1.fill_between(year_data.index, closes, closes.min(), alpha=0.08, color="#1565C0")

    ax1.set_ylim(*smart_ylim(closes))
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.2f"))
    ax1.xaxis.set_major_locator(mdates.MonthLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    plt.setp(ax1.get_xticklabels(), rotation=30, ha="right", fontsize=8)
    ax1.set_title("Past Year — Daily Close", fontsize=10, color="#555")
    ax1.grid(True, alpha=0.25, linestyle="--")
    ax1.spines[["top", "right"]].set_visible(False)

    # Mark 52-week high / low
    hi_idx = closes.idxmax()
    lo_idx = closes.idxmin()
    ax1.annotate(f"52w high\n${closes[hi_idx]:,.2f}",
                 xy=(hi_idx, closes[hi_idx]),
                 xytext=(0, 12), textcoords="offset points",
                 ha="center", fontsize=7.5, color="#1565C0",
                 arrowprops=dict(arrowstyle="-", color="#aaa", lw=0.8))
    ax1.annotate(f"52w low\n${closes[lo_idx]:,.2f}",
                 xy=(lo_idx, closes[lo_idx]),
                 xytext=(0, -22), textcoords="offset points",
                 ha="center", fontsize=7.5, color="#555",
                 arrowprops=dict(arrowstyle="-", color="#aaa", lw=0.8))

    # ── Bottom: most recent trading day ─────────────────────────────────────
    if not day_data.empty:
        day_closes = day_data["Close"]
        open_price = day_data["Open"].iloc[0]
        day_color  = "#2e7d32" if day_closes.iloc[-1] >= open_price else "#c62828"

        ax2.plot(day_data.index, day_closes, linewidth=1.4, color=day_color)
        ax2.axhline(open_price, color="#999", linestyle="--", linewidth=0.9,
                    label=f"Open  ${open_price:.2f}")

        ax2.set_ylim(*smart_ylim(day_closes, pad_pct=0.08))
        ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.2f"))
        ax2.xaxis.set_major_locator(mdates.HourLocator())
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        plt.setp(ax2.get_xticklabels(), fontsize=8)

        day_label = day_data.index[-1].strftime("%b %d, %Y")
        ax2.set_title(f"{day_label} — 5-Minute Intervals", fontsize=10, color="#555")
        ax2.legend(fontsize=8, framealpha=0.5)
        ax2.grid(True, alpha=0.25, linestyle="--")
        ax2.spines[["top", "right"]].set_visible(False)
    else:
        ax2.text(0.5, 0.5, "No intraday data available\n(market may be closed)",
                 ha="center", va="center", transform=ax2.transAxes,
                 color="#999", fontsize=11)
        ax2.set_title("Most Recent Trading Day — 5-Minute Intervals", fontsize=10, color="#555")
        ax2.axis("off")

    # ── Save ────────────────────────────────────────────────────────────────
    os.makedirs("results", exist_ok=True)
    out = f"results/{symbol}.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  [{symbol}] Saved → {out}")


if __name__ == "__main__":
    symbols = sys.argv[1:] if len(sys.argv) > 1 else ["AAPL"]
    if not symbols:
        print("Usage: python plot.py AAPL [MSFT TSLA ...]")
        sys.exit(1)
    for sym in symbols:
        print(f"Fetching {sym.upper()}...")
        plot_ticker(sym)
