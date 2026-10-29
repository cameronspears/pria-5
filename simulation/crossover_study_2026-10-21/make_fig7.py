"""fig7: the room-independent speaker preset (room-free result and in this room)."""
import json, sys, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, '.')
import speaker_preset_inroom as SI
import speaker_preset as SP
from speaker_anechoic import GRID
import minimal_eq as E

SURF, INK2, GRIDC = "#fcfcfb", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.grid": True, "grid.color": GRIDC,
                     "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2,
                     "legend.frameon": False, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
rows = SI.ROWS
bass = [r for r in rows if r[0] == "High-pass" or r[1] < 200]
common = [r for r in rows if r not in bass]
S = SP.S
raw = S.response([], [])
pre = S.response(bass, common)


def norm(y):
    y = SP.smooth(y)
    return y - np.average((y - SP.TARGET)[SP.SEL], weights=SP.W[SP.SEL])


fig, axs = plt.subplots(1, 2, figsize=(15, 5.4))
a = axs[0]
show = (GRID >= 30) & (GRID <= 16000)
a.plot(GRID[show], SP.TARGET[show], color=INK2, lw=1.2, ls=(0, (4, 3)), label="speaker target (flat, 55 Hz roll-off)")
a.plot(GRID[show], norm(raw["lw"])[show], color=ORANGE, label="new build, crossover only: listening window")
a.plot(GRID[show], norm(pre["lw"])[show], color=BLUE, label="with the 6-row speaker preset: listening window")
a.plot(GRID[show], norm(pre["axis"])[show], color=BLUE, lw=1.2, ls=(0, (4, 2)), label="with preset: on-axis")
a.set_xscale("log"); a.set_xlim(30, 16000); a.set_ylim(-20, 8); a.minorticks_off()
tk = [30, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
a.set_xticks(tk); a.set_xticklabels([f"{t/1000:g}k" if t >= 1000 else str(t) for t in tk])
a.set_xlabel("Frequency (Hz)"); a.set_ylabel("dB")
a.set_title("The speaker itself, no room (anechoic model)", loc="left", fontweight="semibold")
a.legend(loc="lower center", fontsize=9)
b = axs[1]
G = E.G
showg = (G >= 30) & (G <= 16000)
ref = np.interp(np.log(500), np.log(G), E.t22)
b.plot(G[showg], E.t22[showg] - ref, color=ORANGE, label="today (Tuning22, room-tuned, 28 rows)")
for s, col, lw, lab in ((0.0, AQUA, 1.6, "speaker preset only (bass tilt 0)"),
                        (5.0, BLUE, 2.0, "speaker preset + bass tilt +5 dB (7 rows)")):
    y = SI.inroom(rows, s)
    b.plot(G[showg], y[showg] - ref, color=col, lw=lw, label=lab)
b.set_xscale("log"); b.set_xlim(30, 16000); b.set_ylim(-20, 8); b.minorticks_off()
b.set_xticks(tk); b.set_xticklabels([f"{t/1000:g}k" if t >= 1000 else str(t) for t in tk])
b.set_xlabel("Frequency (Hz)"); b.set_ylabel("dB (re 500 Hz)")
b.set_title("Predicted in YOUR room (12-position average, 1/3 octave)", loc="left", fontweight="semibold")
b.legend(loc="lower center", fontsize=9)
fig.tight_layout(); fig.savefig("fig7_speaker_preset.png", dpi=150)
with open("predictions/speaker_preset.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["bank", "type", "hz", "q", "gain_db", "layer"])
    for t, f0, q, g in rows:
        banks = ["Woofer EQ"] if (t == "High-pass" or f0 < 200) else ["Woofer EQ", "Tweeter EQ"]
        for bk in banks:
            w.writerow([bk, t, round(f0, 1), round(q, 2), round(g, 1), "speaker (same in every unit)"])
    w.writerow(["Woofer EQ", "Low shelf (or broad peaking)", 100, 0.71, "0 to +6", "bass tilt (placement/feel), +5 in the current room"])
print("saved")
