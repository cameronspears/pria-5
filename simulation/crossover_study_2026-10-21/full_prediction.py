"""Predicted full-range response after D1 (crossover) + D2 (8 g PRs) + D3 (bass target).

In-room (12-position average, 1/3 octave), built on the Tuning22 static prediction
of the Tuning12 measured average (`measurements/2026-10-02_tuning22_refine/prediction.csv`):
  * below ~300 Hz: PR-mass ratio from the LF model (2.7 L fit) and a new bass EQ
    = ideal EQ to the house curve (85 Hz fill capped at +8 dB) smoothed to 1/3
    octave, standing in for a practical handful of filters;
  * above ~500 Hz: crossover change as the model's power-weighted response ratio
    (on-axis, +/-15 deg vertical, +/-30 and +/-60 deg horizontal) and a re-trim of
    the existing 1220 / 1690 / 3300 Hz and tweeter 3500 Hz rows (gains only).
On-axis (1 m, 3 ms window) is the measured-driver model with the full EQ.
"""
import csv, json, sys
import numpy as np
from scipy.optimize import least_squares
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, '.')
from xover_model import *
from final_design import sections_B, realise
import fit_lf as F
from lf_model import solve, farfield
from inroom_pr_study import eq_bass, room_raw, f as FB
import bass_target_study as BT

P = np.genfromtxt(MEAS / "2026-10-02_tuning22_refine/prediction.csv", delimiter=",", names=True)
G = P["frequency_hz"]
today = P["predicted_linear_trial_db"]
ANCHOR = BT.ANCHOR
house = np.loadtxt("Pria5_bass_target_house_curve.txt", comments="*")
target_new = ANCHOR + np.interp(np.log(G), np.log(house[:, 0]), house[:, 1])
target_old = P["gentler_target_db"]


def third_oct(x_db, ppo=192):
    n = int(round(ppo / 6))
    p = 10 ** (x_db / 10)
    return 10 * np.log10(np.convolve(np.pad(p, n, mode="edge"), np.ones(2 * n + 1) / (2 * n + 1), mode="valid"))


# ------------------------------------------------------------------ bass
ens = json.load(open("lf_ensemble.json"))
fit = next(e for e in ens if abs(e["vb_l"] - 2.7) < .01)
q, wf, pr, box = F.make(np.asarray(fit["x"]))
p11 = farfield(solve(FB, wf, pr, box, 11.0, 1.0))
p8 = farfield(solve(FB, wf, pr, box, 8.0, 1.0))
d_pr = db(p8 / p11)
_, room11 = room_raw()
room8 = room11 + d_pr
tgt_b = ANCHOR + np.interp(np.log(FB), np.log(house[:, 0]), house[:, 1])
eq_ideal = tgt_b - room8
w = np.exp(-0.5 * (np.log(FB / 90) / 0.18) ** 2)
eq_ideal = eq_ideal - np.maximum(eq_ideal - 8.0, 0) * w
# Practical-EQ stand-in: follow the ideal EQ wherever it CUTS (room peaks can be
# notched), but where it boosts use only its 1/3-octave smoothed value (never
# chase narrow room dips).  FB is log-uniform, so a fixed kernel is 1/3 octave.
step = np.log(FB[1] / FB[0])
n13 = int(round(np.log(2) / 6 / step))
p_ = np.convolve(np.pad(10 ** (eq_ideal / 10), n13, mode="edge"), np.ones(2 * n13 + 1) / (2 * n13 + 1), mode="valid")
eq_real = np.minimum(eq_ideal, 10 * np.log10(p_))
# New in-room bass computed directly (1/6-oct room x model x EQ), then 1/3-oct
# smoothed for display, and cross-faded into the Tuning22 curve at 250-450 Hz.
nb_pow = np.convolve(np.pad(10 ** ((room8 + eq_real) / 10), n13, mode="edge"),
                     np.ones(2 * n13 + 1) / (2 * n13 + 1), mode="valid")
new_bass_G = np.interp(np.log(G), np.log(FB), 10 * np.log10(nb_pow))
w_bass = np.clip((np.log(450) - np.log(G)) / (np.log(450) - np.log(250)), 0, 1)

# ------------------------------------------------------------ crossover
M = Model()
ROWS = list(csv.DictReader(open(MEAS / "2026-10-02_tuning22_refine/sorted_eq.csv")))


def bank(name, gains=None):
    h = np.ones_like(M.g, complex)
    for r in ROWS:
        if r["block"] != name:
            continue
        f0, qq, g = float(r["frequency_hz"]), float(r["q"]), float(r["boost_db"])
        if r["type"] == "High-pass":
            h = h * rbj("hp", f0, qq, M.g)
            continue
        if gains and (name, f0) in gains:
            g = gains[(name, f0)]
        h = h * rbj("peak", f0, qq, M.g, g)
    return h


lo_t, hi_t = M.filters("LR4", 3000)
lo_n, hi_n = realise(M, sections_B()[0]), realise(M, sections_B()[1])
rec = json.load(open("recommended_crossover.json"))


def config(lo, hi, tg, d, pol, gains=None):
    wb, tb = bank("Woofer EQ", gains), bank("Tweeter EQ", gains)
    _, _, o = M.responses(lo * wb, hi * tb, tg, d, pol, -4)
    return o


o_today = config(lo_t, hi_t, -10.0, 3, 1)


def gains_from(x):
    g1220, g1690, g3300, g3500, g5200 = x
    return {("Woofer EQ", 1220.0): g1220, ("Tweeter EQ", 1220.0): g1220,
            ("Woofer EQ", 1690.0): g1690, ("Tweeter EQ", 1690.0): g1690,
            ("Woofer EQ", 3300.0): g3300, ("Tweeter EQ", 3300.0): g3300,
            ("Tweeter EQ", 3500.0): g3500,
            ("Woofer EQ", 5200.0): g5200, ("Tweeter EQ", 5200.0): g5200}


def upper_delta(x):
    o_new = config(lo_n, hi_n, rec["tweeter_trim_db"], rec["tweeter_delay_samples"], -1, gains_from(x))
    ratio = M.smooth(M.power_proxy(o_new), 3) - M.smooth(M.power_proxy(o_today), 3)
    return np.interp(np.log(G), np.log(M.g), ratio, left=0.0, right=ratio[-1]), o_new


fit_band = (G >= 700) & (G <= 12000)


def resid(x):
    dlt, _ = upper_delta(x)
    fade_u = np.clip((np.log(G) - np.log(400)) / (np.log(700) - np.log(400)), 0, 1)
    return (today + dlt * fade_u - target_new)[fit_band]


x0 = [-4.0, -3.0, -2.0, -2.0, -4.0]
r = least_squares(resid, x0, bounds=([-8, -8, -6, -6, -8], [2, 2, 2, 2, 2]))
d_up, o_new = upper_delta(r.x)
fade_u = np.clip((np.log(G) - np.log(400)) / (np.log(700) - np.log(400)), 0, 1)
upper = today + d_up * fade_u
new = 10 * np.log10(w_bass * 10 ** (new_bass_G / 10) + (1 - w_bass) * 10 ** (upper / 10))


def stats(y, t, lo, hi):
    b = (G >= lo) & (G <= hi)
    e = y[b] - t[b]
    return dict(min=float(e.min()), max=float(e.max()), rms=float(np.sqrt(np.mean(e ** 2))))


summary = dict(
    retrimmed_rows_db=dict(zip(["1220 Hz Q6 (both, was -4)", "1690 Hz Q1.9 (both, was -3)", "3300 Hz Q3.2 (both, was -2)", "3500 Hz Q3 (tweeter, was -2)", "5200 Hz Q1.1 (both, was -4)"], map(lambda v: round(float(v), 2), r.x))),
    today_vs_its_target_180_16k=stats(today, target_old, 180, 16000),
    new_vs_new_target_180_16k=stats(new, target_new, 180, 16000),
    new_vs_new_target_60_16k=stats(new, target_new, 60, 16000),
    today_vs_new_target_60_16k=stats(today, target_new, 60, 16000),
    new_levels_re_500hz={str(h): round(float(np.interp(np.log(h), np.log(G), new) - np.interp(np.log(500), np.log(G), new)), 1) for h in (40, 45, 50, 55, 60, 70, 85, 100, 150, 1000, 2000, 5000, 10000, 16000)},
    new_minus_target_at={str(h): round(float(np.interp(np.log(h), np.log(G), new - target_new)), 1) for h in (45, 50, 55, 60, 70, 85, 100, 150, 200, 300, 500, 1000, 1500, 2000, 3000, 5000, 10000)},
    today_levels_re_500hz={str(h): round(float(np.interp(np.log(h), np.log(G), today) - np.interp(np.log(500), np.log(G), today)), 1) for h in (40, 45, 50, 55, 60, 70, 85, 100, 150, 1000, 2000, 5000, 10000, 16000)})
json.dump(summary, open("predictions/full_response_summary.json", "w"), indent=1)
with open("predictions/inroom_full_range_1-3oct.csv", "w", newline="") as fh:
    wr = csv.writer(fh)
    wr.writerow(["frequency_hz", "today_tuning22_db", "predicted_new_db", "new_target_db", "old_target_db"])
    for i in range(0, len(G), 4):
        wr.writerow([round(G[i], 2), round(today[i], 2), round(new[i], 2), round(target_new[i], 2), round(target_old[i], 2)])
print(json.dumps(summary, indent=1))

# ------------------------------------------------------------------ figure
SURF, INK2, GRID = "#fcfcfb", "#52514e", "#e4e3df"
BLUE, ORANGE = "#2a78d6", "#eb6834"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.grid": True, "grid.color": GRID,
                     "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2,
                     "legend.frameon": False, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
fig, axs = plt.subplots(1, 2, figsize=(15, 5.4), gridspec_kw=dict(width_ratios=[1.55, 1]))
ref = np.interp(np.log(500), np.log(G), today)
a = axs[0]
show = (G >= 30) & (G <= 16000)
a.plot(G[show], target_new[show] - ref, color=INK2, lw=1.2, ls=(0, (4, 3)), label="new target (house curve)")
a.plot(G[show], today[show] - ref, color=ORANGE, label="today (Tuning22, 11 g, LR4 3 kHz)")
a.plot(G[show], new[show] - ref, color=BLUE, label="predicted: 8 g + new crossover + new bass EQ")
a.set_xscale("log"); a.set_xlim(30, 16000); a.set_ylim(-20, 10); a.minorticks_off()
tk = [30, 40, 50, 60, 80, 100, 200, 500, 1000, 2000, 5000, 10000]
a.set_xticks(tk); a.set_xticklabels([f"{t/1000:g}k" if t >= 1000 else str(t) for t in tk])
a.set_xlabel("Frequency (Hz)"); a.set_ylabel("dB (re 500 Hz)")
a.set_title("Predicted in-room response (12-position average, 1/3 octave)", loc="left", fontweight="semibold")
a.legend(loc="lower center")
b = axs[1]
for o, col, lab in ((o_today, ORANGE, "today"), (o_new, BLUE, "predicted")):
    y = M.smooth(db(o["axis"]), 6)
    yl = M.smooth(M.listening_window(o), 6)
    rr = np.mean(y[M.band(900, 1100)])
    b.plot(M.g, y - rr, color=col, label=f"{lab}: on-axis")
    b.plot(M.g, yl - rr, color=col, lw=1.2, ls=(0, (4, 2)), label=f"{lab}: listening window")
b.set_xscale("log"); b.set_xlim(700, 16000); b.set_ylim(-12, 6); b.minorticks_off()
tk = [1000, 2000, 3000, 5000, 10000]
b.set_xticks(tk); b.set_xticklabels(["1k", "2k", "3k", "5k", "10k"])
b.set_xlabel("Frequency (Hz)"); b.set_ylabel("dB (re 1 kHz)")
b.set_title("Direct sound at 1 m, full EQ (3 ms window)\nincludes the deliberate treble tilt", loc="left", fontweight="semibold")
b.legend(loc="lower left", fontsize=8.5)
fig.tight_layout(); fig.savefig("fig5_predicted_response.png", dpi=150)
