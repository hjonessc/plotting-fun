#!/usr/bin/env python3
"""
weather_plot.py — Fetch weather data from Open-Meteo and plot it.

Usage:
  python weather_plot.py --lat 37.77 --lon -122.42 [--label "San Francisco"]
  python weather_plot.py --lat 40.71 --lon -74.01

No API key required — uses Open-Meteo (open-meteo.com).

Two panels:
  Top:    past year — daily high/low band with mean temperature
  Bottom: past 24 hours — hourly temperature and precipitation
"""

import argparse
import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import numpy as np


# ── Data fetching ─────────────────────────────────────────────────────────────

def fetch(url):
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.load(r)


def get_weather(lat, lon):
    """Fetch past year (daily) and past 2 days (hourly) from Open-Meteo."""

    # Past year: daily high/low/mean
    year_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum"
        f"&past_days=365&forecast_days=1"
        f"&temperature_unit=fahrenheit"
        f"&precipitation_unit=inch"
        f"&timezone=auto"
    )

    # Past 48 hours: hourly temp + precip
    hourly_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,precipitation"
        f"&past_days=2&forecast_days=0"
        f"&temperature_unit=fahrenheit"
        f"&precipitation_unit=inch"
        f"&timezone=auto"
    )

    year   = fetch(year_url)
    hourly = fetch(hourly_url)
    return year, hourly


# ── Plotting ──────────────────────────────────────────────────────────────────

def parse_dates(date_strings):
    return [datetime.strptime(d, "%Y-%m-%d") for d in date_strings]


def parse_datetimes(dt_strings):
    return [datetime.strptime(d, "%Y-%m-%dT%H:%M") for d in dt_strings]


def make_plot(lat, lon, label, year_data, hourly_data):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8), gridspec_kw={"hspace": 0.45})

    loc_str  = label or f"{lat:.2f}°, {lon:.2f}°"
    now_str  = datetime.now().strftime("%Y-%m-%d")
    timezone = year_data.get("timezone_abbreviation", "")

    fig.suptitle(
        f"Weather — {loc_str}  ({now_str})",
        fontsize=14, fontweight="bold", y=0.98
    )

    # ── Top: past year daily ──────────────────────────────────────────────────
    daily    = year_data["daily"]
    dates    = parse_dates(daily["time"])
    hi       = np.array(daily["temperature_2m_max"],  dtype=float)
    lo       = np.array(daily["temperature_2m_min"],  dtype=float)
    mean     = np.array(daily["temperature_2m_mean"], dtype=float)
    precip_y = np.array(daily["precipitation_sum"],   dtype=float)

    # Mask NaN
    valid = ~(np.isnan(hi) | np.isnan(lo))
    dates_v = [d for d, v in zip(dates, valid) if v]
    hi_v    = hi[valid];  lo_v = lo[valid];  mean_v = mean[valid]

    ax1.fill_between(dates_v, lo_v, hi_v, alpha=0.25, color="#1565C0", label="Daily high/low range")
    ax1.plot(dates_v, mean_v, linewidth=1.4, color="#1565C0", label="Daily mean")

    # Annotation: hottest and coldest day
    hi_max_i = np.nanargmax(hi);  lo_min_i = np.nanargmin(lo)
    ax1.annotate(f"High {hi[hi_max_i]:.0f}°F",
                 xy=(dates[hi_max_i], hi[hi_max_i]),
                 xytext=(0, 10), textcoords="offset points",
                 ha="center", fontsize=7.5, color="#C62828",
                 arrowprops=dict(arrowstyle="-", color="#aaa", lw=0.8))
    ax1.annotate(f"Low {lo[lo_min_i]:.0f}°F",
                 xy=(dates[lo_min_i], lo[lo_min_i]),
                 xytext=(0, -18), textcoords="offset points",
                 ha="center", fontsize=7.5, color="#1565C0",
                 arrowprops=dict(arrowstyle="-", color="#aaa", lw=0.8))

    lo_ylim = np.nanmin(lo) - 5
    hi_ylim = np.nanmax(hi) + 5
    ax1.set_ylim(lo_ylim, hi_ylim)
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f°F"))
    ax1.xaxis.set_major_locator(mdates.MonthLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    plt.setp(ax1.get_xticklabels(), rotation=30, ha="right", fontsize=8)
    ax1.set_title("Past Year — Daily High / Mean / Low", fontsize=10, color="#444")
    ax1.legend(loc="upper right", fontsize=8, framealpha=0.6)
    ax1.grid(True, alpha=0.2, linestyle="--")
    ax1.spines[["top", "right"]].set_visible(False)

    # ── Bottom: past 24 hours hourly ──────────────────────────────────────────
    hourly   = hourly_data["hourly"]
    dts_all  = parse_datetimes(hourly["time"])
    temp_all = np.array(hourly["temperature_2m"], dtype=float)
    prec_all = np.array(hourly["precipitation"],  dtype=float)

    # Trim to past 24 hours
    cutoff = datetime.now() - timedelta(hours=24)
    mask   = [dt >= cutoff for dt in dts_all]
    dts    = [dt for dt, m in zip(dts_all, mask) if m]
    temp   = temp_all[mask]
    prec   = prec_all[mask]

    if len(dts) > 0:
        color = "#C62828" if temp[-1] >= temp[0] else "#1565C0"
        ax2.plot(dts, temp, linewidth=1.5, color=color, label="Temperature")

        # Precipitation as bar overlay on twin axis
        if np.any(prec > 0):
            ax2b = ax2.twinx()
            ax2b.bar(dts, prec, width=1/48, color="#4CAF50", alpha=0.4,
                     align="center", label="Precip")
            ax2b.set_ylim(0, max(prec.max() * 4, 0.1))
            ax2b.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f"'))
            ax2b.set_ylabel('Precip (in)', fontsize=8, color="#4CAF50")
            ax2b.tick_params(axis="y", colors="#4CAF50", labelsize=8)
            ax2b.spines[["top"]].set_visible(False)

        lo24 = np.nanmin(temp) - 3;  hi24 = np.nanmax(temp) + 3
        ax2.set_ylim(lo24, hi24)
        ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f°F"))
        ax2.xaxis.set_major_locator(mdates.HourLocator(interval=3))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        plt.setp(ax2.get_xticklabels(), fontsize=8)

        current_temp = temp[-1] if not np.isnan(temp[-1]) else "N/A"
        ax2.set_title(
            f"Past 24 Hours — Hourly  (current: {current_temp:.0f}°F  {timezone})",
            fontsize=10, color="#444"
        )
        ax2.legend(loc="upper left", fontsize=8, framealpha=0.6)
    else:
        ax2.text(0.5, 0.5, "No recent hourly data available",
                 ha="center", va="center", transform=ax2.transAxes, color="#999")

    ax2.grid(True, alpha=0.2, linestyle="--")
    ax2.spines[["top", "right"]].set_visible(False)

    # ── Save ─────────────────────────────────────────────────────────────────
    os.makedirs("results", exist_ok=True)
    slug     = (label or f"{lat}_{lon}").replace(" ", "_").replace(",", "")
    out_path = f"results/weather_{slug}.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved → {out_path}")
    return out_path


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot weather data from Open-Meteo")
    parser.add_argument("--lat",   required=True, type=float, help="Latitude")
    parser.add_argument("--lon",   required=True, type=float, help="Longitude")
    parser.add_argument("--label", default="",                help="Location label for title")
    args = parser.parse_args()

    print(f"Fetching weather for {args.label or f'{args.lat}, {args.lon}'} …")
    year_data, hourly_data = get_weather(args.lat, args.lon)
    make_plot(args.lat, args.lon, args.label, year_data, hourly_data)
