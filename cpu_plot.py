#!/usr/bin/env python3
"""
cpu_plot.py — Sample /proc/stat and plot live CPU usage over time.

Usage:   python cpu_plot.py [duration_seconds] [interval_seconds]
Default: 30 seconds, 0.5s interval

Output:  results/cpu_<timestamp>.png

Two panels:
  Top:    aggregate CPU % with user/system/iowait breakdown (stacked area)
  Bottom: per-core CPU % as individual lines
"""

import sys
import time
import os
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


# ── /proc/stat helpers ────────────────────────────────────────────────────────

def read_stat():
    """Return dict of cpu_name -> [user, nice, system, idle, iowait, irq, softirq, steal]"""
    stats = {}
    with open("/proc/stat") as f:
        for line in f:
            if not line.startswith("cpu"):
                break
            parts = line.split()
            name   = parts[0]
            values = list(map(int, parts[1:9]))  # first 8 fields only
            while len(values) < 8:
                values.append(0)
            stats[name] = values
    return stats


def delta_pct(prev, curr):
    """CPU usage % between two raw stat readings, broken down by type."""
    total = sum(curr) - sum(prev)
    if total == 0:
        return dict(user=0, system=0, iowait=0, other=0, idle=100)

    def d(i): return curr[i] - prev[i]

    user    = max(0, d(0) + d(1))          # user + nice
    system  = max(0, d(2) + d(5) + d(6))   # system + irq + softirq
    iowait  = max(0, d(4))
    steal   = max(0, d(7))
    idle    = max(0, d(3))
    other   = max(0, total - user - system - iowait - steal - idle)

    scale = 100 / total
    return dict(
        user   = user   * scale,
        system = system * scale,
        iowait = iowait * scale,
        other  = (steal + other) * scale,
        idle   = idle   * scale,
    )


def total_pct(breakdown):
    return breakdown["user"] + breakdown["system"] + breakdown["iowait"] + breakdown["other"]


# ── Sampling ──────────────────────────────────────────────────────────────────

def sample(duration=30, interval=0.5):
    print(f"Sampling /proc/stat every {interval}s for {duration}s …")
    prev = read_stat()
    time.sleep(interval)

    timestamps  = []
    aggregate   = []   # list of breakdown dicts
    per_core    = {}   # core_name -> list of total %

    cores = sorted(k for k in prev if k != "cpu")
    for c in cores:
        per_core[c] = []

    elapsed = interval
    while elapsed <= duration:
        curr = read_stat()
        ts   = datetime.now()

        timestamps.append(ts)
        aggregate.append(delta_pct(prev["cpu"], curr["cpu"]))
        for c in cores:
            if c in curr:
                per_core[c].append(total_pct(delta_pct(prev[c], curr[c])))

        prev    = curr
        elapsed += interval
        time.sleep(interval)

    print(f"  Collected {len(timestamps)} samples across {len(cores)} core(s).")
    return timestamps, aggregate, per_core, cores


# ── Plotting ──────────────────────────────────────────────────────────────────

COLORS = {
    "user":   "#1565C0",
    "system": "#C62828",
    "iowait": "#F57F17",
    "other":  "#6A1B9A",
}

CORE_PALETTE = [
    "#1565C0", "#2E7D32", "#C62828", "#F57F17",
    "#6A1B9A", "#00838F", "#4E342E", "#37474F",
]


def make_plot(timestamps, aggregate, per_core, cores, out_path):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8), gridspec_kw={"hspace": 0.45})

    ts_sec = [(t - timestamps[0]).total_seconds() for t in timestamps]
    now_str = timestamps[0].strftime("%Y-%m-%d %H:%M:%S")
    n_cores = len(cores)

    fig.suptitle(
        f"CPU Usage — {n_cores}-core system   ({now_str})",
        fontsize=14, fontweight="bold", y=0.98
    )

    # ── Top: stacked area breakdown ──────────────────────────────────────────
    keys   = ["user", "system", "iowait", "other"]
    labels = ["User", "System", "I/O Wait", "Other"]
    stacks = [[a[k] for a in aggregate] for k in keys]
    bottoms = np.zeros(len(timestamps))

    for stack, label, key in zip(stacks, labels, keys):
        arr = np.array(stack)
        ax1.fill_between(ts_sec, bottoms, bottoms + arr,
                         label=label, color=COLORS[key], alpha=0.85)
        bottoms += arr

    avg_total = np.mean([total_pct(a) for a in aggregate])
    peak      = max(total_pct(a) for a in aggregate)

    ax1.set_ylim(0, 105)
    ax1.set_xlim(0, ts_sec[-1])
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax1.set_xlabel("Seconds elapsed", fontsize=9)
    ax1.set_title(
        f"Aggregate CPU   avg {avg_total:.1f}%  peak {peak:.1f}%",
        fontsize=10, color="#444"
    )
    ax1.legend(loc="upper right", fontsize=8, framealpha=0.6, ncol=4)
    ax1.grid(True, alpha=0.2, linestyle="--")
    ax1.spines[["top", "right"]].set_visible(False)

    # ── Bottom: per-core lines ───────────────────────────────────────────────
    for i, core in enumerate(cores):
        data   = per_core[core]
        n      = min(len(data), len(ts_sec))
        color  = CORE_PALETTE[i % len(CORE_PALETTE)]
        label  = f"cpu{i}"
        ax2.plot(ts_sec[:n], data[:n], linewidth=1.3,
                 color=color, label=label, alpha=0.85)

    ax2.set_ylim(0, 105)
    ax2.set_xlim(0, ts_sec[-1])
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax2.set_xlabel("Seconds elapsed", fontsize=9)
    ax2.set_title(f"Per-Core Breakdown ({n_cores} cores)", fontsize=10, color="#444")
    ax2.legend(loc="upper right", fontsize=8, framealpha=0.6,
               ncol=min(n_cores, 8))
    ax2.grid(True, alpha=0.2, linestyle="--")
    ax2.spines[["top", "right"]].set_visible(False)

    os.makedirs("results", exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  Saved → {out_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    duration = float(sys.argv[1]) if len(sys.argv) > 1 else 30
    interval = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5

    timestamps, aggregate, per_core, cores = sample(duration, interval)

    stamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = f"results/cpu_{stamp}.png"
    make_plot(timestamps, aggregate, per_core, cores, out_path)
