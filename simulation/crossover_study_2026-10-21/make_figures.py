"""Figures for the crossover / PR-mass study (static PNG, light surface)."""
import json, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, '.')
from xover_model import *
from final_design import sections_B, realise
import fit_lf as F
from lf_model import solve, farfield, nearfield, P_REF
from inroom_pr_study import eq_bass, room_raw, f as FB
from volume_first import hp8, eq_nohp, headroom

SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
RAMP = ["#b7d3f6", "#6da7ec", "#2a78d6", "#184f95"]
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": GRID,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
                     "lines.linewidth": 2, "lines.solid_capstyle": "round", "font.size": 10,
                     "axes.titlesize": 11, "axes.titleweight": "semibold", "legend.frameon": False,
                     "axes.spines.top": False, "axes.spines.right": False})


def logx(ax, lo, hi, ticks):
    ax.set_xscale("log"); ax.set_xlim(lo, hi)
    ax.set_xticks(ticks); ax.set_xticklabels([f"{t/1000:g}k" if t >= 1000 else f"{t:g}" for t in ticks])
    ax.minorticks_off(); ax.set_xlabel("Frequency (Hz)")


# ------------------------------------------------------------ crossover
M = Model()
rec = json.load(open("recommended_crossover.json"))
lo_s, hi_s = sections_B()
loB, hiB = realise(M, lo_s), realise(M, hi_s)
loT, hiT = M.filters("LR4", 3000)
cfg = {"Today: LR4 3 kHz, +3 samples": (loT, hiT, -10.0, 3, 1, ORANGE),
       "Recommended: LR48 2.5 kHz / Bessel-24 3.55 kHz, inverted, +3": (loB, hiB, rec["tweeter_trim_db"], rec["tweeter_delay_samples"], -1, BLUE)}
fig, axs = plt.subplots(2, 2, figsize=(12, 8.2))
g = M.g
b = M.band(1000, 10000)
for name, (lo, hi, tg, d, pol, col) in cfg.items():
    wv, tv, out = M.responses(lo, hi, tg, d, pol, -4)
    ax_ = M.smooth(db(out["axis"]), 6); lw = M.smooth(M.listening_window(out), 6)
    ref = np.mean(lw[b])
    axs[0, 0].plot(g, ax_ - ref, color=col, label=name.split(":")[0])
    axs[0, 1].plot(g, lw - ref, color=col, label=name.split(":")[0])
    for k, ls in (("v+15", "-"), ("v-15", (0, (4, 3)))):
        axs[1, 0].plot(g, M.smooth(db(out[k]), 6) - M.smooth(db(out["axis"]), 6), color=col, ls=ls, lw=2,
                       label=f"{name.split(':')[0]} {'+15° above' if k == 'v+15' else '−15° below'}")
    x = __import__("drivers").tweeter_excursion_m(g, np.abs(tv) * P_REF)
    lim = M.smooth(db(out["axis"]), 6) + 20 * np.log10(1e-4 / x)
    axs[1, 1].plot(g, lim, color=col, label=name.split(":")[0])
for a, t in ((axs[0, 0], "On-axis (1 m, crossover only, no EQ)"), (axs[0, 1], "Listening window (0°, ±15° vertical, ±30° horizontal)")):
    logx(a, 700, 16000, [1000, 2000, 3000, 5000, 10000]); a.set_ylim(-6, 6); a.set_ylabel("dB (re 1–10 kHz mean)")
    a.set_title(t, loc="left"); a.axvspan(1000, 10000, color=GRID, alpha=0.25, lw=0)
axs[0, 0].legend(loc="lower left")
a = axs[1, 0]; logx(a, 1000, 8000, [1000, 1500, 2000, 3000, 5000, 8000]); a.set_ylim(-14, 6)
a.set_ylabel("dB relative to on-axis"); a.set_title("Vertical lobing at ±15° (fitted to your off-axis data)", loc="left")
a.legend(loc="lower right", fontsize=8.5)
a = axs[1, 1]; logx(a, 700, 8000, [1000, 1500, 2000, 3000, 5000]); a.set_ylim(90, 125)
a.set_ylabel("System sine SPL @ 1 m (dB)"); a.set_title("Level at which the OT19 reaches Xmax (0.1 mm)", loc="left")
for name, (lo, hi, tg, d, pol, col) in cfg.items():
    m = M.evaluate(lo, hi, tg, d, pol, w_gain_db=-4)
    a.annotate(f"{m['tweeter_limit']:.1f} dB", (m["tweeter_limit_hz"], m["tweeter_limit"]), xytext=(8, -14 if col == BLUE else 6),
               textcoords="offset points", color=INK2, fontsize=9)
    a.plot([m["tweeter_limit_hz"]], [m["tweeter_limit"]], "o", ms=7, color=col, mec=SURF, mew=2)
a.legend(loc="upper right")
fig.suptitle("Pria 5 crossover: today vs recommended (built from your measured woofer + tweeter, old crossover removed)", x=0.01, ha="left", fontsize=12, fontweight="semibold")
fig.tight_layout(rect=(0, 0, 1, 0.96)); fig.savefig("fig1_crossover.png", dpi=150); plt.close(fig)

# ------------------------------------------------------------ PR mass
ens = json.load(open("lf_ensemble.json"))
e27 = next(e for e in ens if abs(e["vb_l"] - 2.7) < .01)
q, wf, pr, box = F.make(np.asarray(e27["x"]))
fig, axs = plt.subplots(1, 3, figsize=(16.5, 5.4))
fa = np.geomspace(25, 300, 400)
for m, col in zip((0, 4, 8, 11), RAMP):
    r = solve(fa, wf, pr, box, m, 1.0); p = farfield(r)
    rel = db(p) - np.median(db(p)[(fa > 150) & (fa < 300)])
    axs[0].plot(fa, rel, color=col, label=f"+{m} g (tunes {r['fb']:.0f} Hz)" + ("  ← now" if m == 11 else ""))
a = axs[0]; logx(a, 30, 300, [30, 40, 50, 60, 80, 100, 150, 200, 300]); a.set_ylim(-24, 4)
a.set_ylabel("dB (re 150–300 Hz)"); a.set_title("Speaker's own bass (anechoic, no DSP)", loc="left"); a.legend(loc="lower right")
vf = json.load(open("volume_first.json"))
keys = list(vf)
masses = sorted({r["added_g"] for r in vf[keys[0]]})
for ft, col in zip((50, 55, 60, 65), RAMP):
    lo_ = [min(next(r["headroom_gain_db"] for r in vf[k] if r["added_g"] == m and r["ft"] == ft and r["cap"] == 6.0) for k in keys) for m in masses]
    hi_ = [max(next(r["headroom_gain_db"] for r in vf[k] if r["added_g"] == m and r["ft"] == ft and r["cap"] == 6.0) for k in keys) for m in masses]
    axs[1].fill_between(masses, lo_, hi_, color=col, alpha=0.15, lw=0)
    axs[1].plot(masses, np.mean([lo_, hi_], axis=0), color=col, marker="o", ms=4, label=f"bass cut-off {ft} Hz")
a = axs[1]; a.axhline(0, color=INK2, lw=1); a.set_xlim(0, 14); a.set_ylim(-12, 7)
a.axvline(8, color=GRID, lw=6, alpha=0.6, zorder=0); a.annotate("8 g", (8, 6.3), ha="center", color=INK2)
a.annotate("0 = today (11 g, current EQ)", (14, -1.7), ha="right", color=INK2, fontsize=9)
a.set_xlabel("Added mass per PR (g)"); a.set_ylabel("Clean headroom vs today (dB)")
a.set_title("Volume-first: clean headroom vs PR mass\n(85 Hz room-dip boost capped at +6 dB; shading = all 5 fits)", loc="left")
a.legend(loc="lower right")
# predicted in-room bass
p11 = farfield(solve(FB, wf, pr, box, 11.0, 1.0))
meas, room = room_raw()
today_t = np.abs(eq_bass(FB) * p11)
inroom_today = room + db(eq_bass(FB))   # = measured T22-equivalent in-room bass
for label, m, ft, cap, col in (("today (11 g, current EQ)", None, None, None, ORANGE),
                               ("DSP only: 11 g, 55 Hz cut,\n  85 Hz boost ≤ +8 dB", 11, 55, 8.0, AQUA),
                               ("8 g, 55 Hz cut,\n  85 Hz boost ≤ +8 dB", 8, 55, 8.0, BLUE)):
    if m is None:
        y = inroom_today
    else:
        tgt = np.abs(eq_nohp(FB) * p11 * hp8(FB, ft))
        r = solve(FB, wf, pr, box, m, 1.0)
        eqm = tgt / np.abs(farfield(r))
        w = np.exp(-0.5 * (np.log(FB / 90) / 0.18) ** 2)
        excess = np.maximum(db(eqm) - cap, 0) * w
        tgt = tgt / 10 ** (excess / 20); eqm = eqm / 10 ** (excess / 20)
        h, _, _ = headroom(r, eqm, wf, pr)
        h0, _, _ = headroom(solve(FB, wf, pr, box, 11.0, 1.0), np.abs(eq_bass(FB)), wf, pr)
        y = inroom_today + db(tgt / today_t)
        label += f"  → +{h-h0:.1f} dB headroom"
    axs[2].plot(FB, y - np.median(inroom_today[(FB > 150) & (FB < 300)]), color=col, label=label)
a = axs[2]; logx(a, 30, 300, [30, 40, 50, 60, 80, 100, 150, 200, 300]); a.set_ylim(-25, 12)
a.set_ylabel("dB (re 150–300 Hz)"); a.set_title("Predicted in-room bass\n(your 12-position room average)", loc="left"); a.legend(loc="lower right", fontsize=8.5, bbox_to_anchor=(1.0, 0.0))
a.set_ylim(-30, 10)
fig.tight_layout(); fig.savefig("fig2_pr_mass.png", dpi=150); plt.close(fig)

# ------------------------------------------------------------ validation
fig, axs = plt.subplots(1, 3, figsize=(16.5, 5.0))
a, b_, res, _ = F.predict(np.asarray(e27["x"]))
for y, mdl, lab, col, sel in ((F.pw, a, "woofer", BLUE, F.mw), (F.pp, b_, "PR (avg L/R)", ORANGE, F.mp)):
    axs[0].plot(F.f, db(y / P_REF), color=col, lw=1.0, alpha=0.5, label=f"{lab} measured")
    axs[0].plot(F.f[sel], db(mdl / P_REF)[sel], color=col, lw=2.2, label=f"{lab} model (fit range)")
a0 = axs[0]; logx(a0, 25, 400, [30, 50, 80, 100, 200, 400]); a0.set_ylim(35, 95); a0.set_ylabel("dB SPL (5 mm nearfield)")
a0.set_title("Bass model vs 2026-09-29 nearfields\n(~0.5 dB / ~5° error; PR tuning 50.4 Hz)", loc="left"); a0.legend(loc="lower right", fontsize=8.5)
# on-axis delay trials
fd, win, _ = load_driver_set("3ms")
W = (win[0] + win[1]) / 2; T = (win[2] + win[3]) / 2
cut = rbj("peak", 3500, 3.0, fd, -2.0)
gg = log_grid(800, 16000, 48)
sm = lambda x: smooth_complex_power(fd, x, gg, 12)
for (folder, recs, d), col, off in ((("2026-09-30_tuning01", ["trial_1", "trial_2"], 0), RAMP[1], 0),
                                    (("2026-09-30_tuning03_window", ["record_1", "record_2"], 2), RAMP[2], -8),
                                    (("2026-09-30_tuning02", ["trial_1", "trial_2"], 4), RAMP[3], -16)):
    m = 10 * np.log10(np.mean([10 ** (sm(np.load(MEAS / folder / f"{r}.npz")["3ms"]) / 10) for r in recs], axis=0))
    pr_ = sm(W + T * cut * delay(d, fd))
    axs[1].plot(gg, m + off, color=col, lw=1.0, alpha=0.6)
    axs[1].plot(gg, pr_ + off, color=col, lw=2.2, ls=(0, (4, 2)), label=f"tweeter delay {d}: measured (thin) / predicted (dashed)")
a1 = axs[1]; logx(a1, 800, 16000, [1000, 2000, 3000, 5000, 10000]); a1.set_ylabel("dB SPL (curves offset 8 dB)"); a1.set_ylim(44, 78)
a1.set_title("Crossover model vs your delay trials\n(predicted from the driver set; median error ≈ 0 dB)", loc="left"); a1.legend(loc="lower left", fontsize=8.5)
ks = json.load(open("effective_spacing_3ms.json"))
kk = sorted(map(float, ks["scan_rms_db"])); vv = [ks["scan_rms_db"][str(k) if str(k) in ks["scan_rms_db"] else repr(k)] for k in kk]
axs[2].plot(kk, vv, color=BLUE, marker="o", ms=5)
axs[2].plot([1.0], [ks["scan_rms_db"]["1.0"]], "o", ms=8, color=ORANGE, mec=SURF, mew=2)
axs[2].annotate("pure geometry", (1.0, ks["scan_rms_db"]["1.0"]), xytext=(8, 6), textcoords="offset points", color=INK2)
axs[2].annotate(f"best fit k = {ks['best_k']:.2f}", (ks["best_k"], ks["best_rms_db"]), xytext=(-40, 16), textcoords="offset points", color=INK2)
a2 = axs[2]; a2.set_xlabel("Vertical path-difference factor k"); a2.set_ylabel("RMS error, ±15° records, 1.5–5 kHz (dB)")
a2.set_title("Off-axis model fitted to your ±15° records\n(5 records, 3 tweeter delays)", loc="left")
fig.tight_layout(); fig.savefig("fig3_model_validation.png", dpi=150); plt.close(fig)
