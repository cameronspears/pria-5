"""Reference curves for the first measurement on the current (rebuilt) speaker.

The model's driver data and its polarity come from the 2026-09-30 build.  If
the rebuild's tweeter is wired the other way round, every DSP 'invert'
setting in this study flips.  One on-axis sweep (1 m, woofer/tweeter
midpoint height, the user's current Tuning22-based preset) tells which:

  same wiring  -> smooth 1.5-4 kHz (within ~3 dB of the 'same' curve)
  reversed     -> a deep (>10 dB) notch near 2.3-2.6 kHz

Curves are written for the 3 ms window and the full (room-included) window.
"""
import csv, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, '.')
from common import *

ROWS = list(csv.DictReader(open(MEAS / "2026-10-02_tuning22_refine/sorted_eq.csv")))


def bank(name, f):
    h = np.ones_like(f, complex)
    for r in ROWS:
        if r["block"] != name or r["bypass"] == "True":
            continue
        f0, q, g = float(r["frequency_hz"]), float(r["q"]), float(r["boost_db"])
        h = h * (rbj("hp", f0, q, f) if r["type"] == "High-pass" else rbj("peak", f0, q, f, g))
    return h


out = {}
grid = log_grid(500, 16000, 48)
for window in ("3ms", "native"):
    f, win, nat = load_driver_set(window)
    W = (win[0] + win[1]) / 2
    T = (win[2] + win[3]) / 2
    wc, tc = measured_chain(f)
    Wr, Tr = W / wc, T / tc
    lo, hi = crossover("LR4", 3000, f)
    wt = Wr * lo * 10 ** (-4 / 20) * rbj("hp", 50, .71, f) ** 2 * bank("Woofer EQ", f)
    tt = Tr * hi * 10 ** (-10 / 20) * bank("Tweeter EQ", f) * delay(3, f)
    for pol, name in ((1, "same wiring as Sept"), (-1, "tweeter reversed")):
        s = smooth_complex_power(f, wt + pol * tt, grid, 12)
        out[(window, name)] = s - np.median(s[(grid > 4000) & (grid < 8000)])
with open("predictions/polarity_check_today_preset.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["frequency_hz"] + [f"{a}_{b.replace(' ', '_')}_db" for a, b in out])
    for i, g in enumerate(grid):
        w.writerow([round(g, 2)] + [round(float(v[i]), 2) for v in out.values()])
plt.rcParams.update({"figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "axes.grid": True,
                     "grid.color": "#e4e3df", "axes.spines.top": False, "axes.spines.right": False,
                     "lines.linewidth": 2, "legend.frameon": False})
fig, ax = plt.subplots(figsize=(9, 4.6))
for (window, name), y in out.items():
    if window != "3ms":
        continue
    ax.plot(grid, y, color="#2a78d6" if name.startswith("same") else "#eb6834", label=name)
ax.set_xscale("log"); ax.set_xlim(800, 12000); ax.set_ylim(-25, 8); ax.minorticks_off()
ax.set_xticks([1000, 1500, 2000, 3000, 5000, 10000]); ax.set_xticklabels(["1k", "1.5k", "2k", "3k", "5k", "10k"])
ax.set_xlabel("Frequency (Hz)"); ax.set_ylabel("dB (re 4-8 kHz median)")
ax.set_title("Polarity check: today's Tuning22 preset, on-axis 1 m (3 ms window)", loc="left", fontweight="semibold")
ax.legend(loc="lower left")
fig.tight_layout(); fig.savefig("fig4_polarity_check.png", dpi=150)
for (window, name), y in out.items():
    b = (grid > 1500) & (grid < 4000)
    print(f"{window:6s} {name:20s} 1.5-4 kHz min {y[b].min():6.1f} dB at {grid[b][np.argmin(y[b])]:.0f} Hz")
