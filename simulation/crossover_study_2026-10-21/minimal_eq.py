"""Predicted DSP filter list for the new build, with as few filters as possible.

Bass (woofer bank only): in-room room x 8 g model (same basis as
full_prediction.py) fitted to the house curve with a high-pass pair plus N
peaking filters.  The ~85 Hz room null is not chased (deficits there are
weighted down and total boost at 75-115 Hz is capped at +8 dB); excursion
headroom is checked against today.

Mid/treble (both banks, so relative woofer/tweeter phase is untouched):
Tuning22's in-room prediction with ALL of its EQ removed, the new crossover
applied (power-weighted model ratio), then M peaking filters fitted to the
house curve, 300 Hz-14 kHz, 1/3 octave.

The smallest N and M that reach the accuracy of the ideal-EQ prediction are
reported.
"""
import csv, json, sys
import numpy as np
from scipy.optimize import least_squares
sys.path.insert(0, '.')
from xover_model import *
from final_design import sections_B, realise
import fit_lf as F
from lf_model import solve, farfield
from inroom_pr_study import eq_bass, room_raw, f as FB
from volume_first import headroom
import bass_target_study as BT

house = np.loadtxt("Pria5_bass_target_house_curve.txt", comments="*")
ANCHOR = BT.ANCHOR


def tgt(fr):
    return ANCHOR + np.interp(np.log(fr), np.log(house[:, 0]), house[:, 1])


# ------------------------------------------------------------------ bass
ens = json.load(open("lf_ensemble.json"))
fit = next(e for e in ens if abs(e["vb_l"] - 2.7) < .01)
q, wf, pr, box = F.make(np.asarray(fit["x"]))
r11 = solve(FB, wf, pr, box, 11.0, 1.0)
r8 = solve(FB, wf, pr, box, 8.0, 1.0)
_, room11 = room_raw()
room8 = room11 + db(farfield(r8) / farfield(r11))
T_b = tgt(FB)
base_h, _, _ = headroom(r11, np.abs(eq_bass(FB)), wf, pr)
null = np.exp(-0.5 * (np.log(FB / 90) / 0.18) ** 2)
bsel = (FB >= 38) & (FB <= 300)


def bass_eq(x, n):
    fh, q1, q2 = np.exp(x[0]), x[1], x[2]
    h = rbj("hp", fh, q1, FB) * rbj("hp", fh, q2, FB)
    rows = [("High-pass", fh, q1, 0.0), ("High-pass", fh, q2, 0.0)]
    for i in range(n):
        f0, qq, g = np.exp(x[3 + 3 * i]), x[4 + 3 * i], x[5 + 3 * i]
        h = h * rbj("peak", f0, qq, FB, g)
        rows.append(("Peaking", f0, qq, g))
    return h, rows


def bass_resid(x, n):
    h, _ = bass_eq(x, n)
    e = room8 + db(h) - T_b
    w = np.where(FB < 45, 0.4, 1.0)
    w = np.where(e < 0, w * (1 - 0.85 * null), w)        # don't chase the null
    over = np.maximum(db(h) - 8.0, 0) * null * 3          # cap boost in the null band
    boost = [0.10 * max(x[5 + 3 * i], 0) for i in range(n)]  # prefer cuts over boosts
    return np.r_[(e * w)[bsel], over[bsel], boost]


def third(xdb, fr):
    step = np.log(fr[1] / fr[0])
    k = int(round(np.log(2) / 6 / step))
    p = np.convolve(np.pad(10 ** (xdb / 10), k, mode="edge"), np.ones(2 * k + 1) / (2 * k + 1), mode="valid")
    return 10 * np.log10(p)


def fit_bass(n, seeds=16):
    best = None
    rng = np.random.default_rng(7)
    for s in range(seeds):
        x0 = [np.log(rng.uniform(40, 60)), rng.uniform(.55, .95), rng.uniform(.55, .95)]
        lb = [np.log(30), .5, .5]; ub = [np.log(80), 1.0, 1.0]        # ordinary (non-resonant) high-pass
        for i in range(n):
            if i == 0:   # seed one broad bass lift, like today's 70 Hz / Q.7 row
                x0 += [np.log(rng.uniform(60, 90)), rng.uniform(.6, 1.0), rng.uniform(5, 9)]
            else:
                x0 += [np.log(rng.uniform(100, 250)), rng.uniform(1, 4), rng.uniform(-6, 0)]
            lb += [np.log(40), .4, -12.]; ub += [np.log(300), 5., 10.]
        r = least_squares(bass_resid, x0, bounds=(lb, ub), args=(n,), max_nfev=3000)
        if best is None or r.cost < best.cost:
            best = r
    h, rows = bass_eq(best.x, n)
    e = third(room8 + db(h), FB) - third(T_b, FB)          # 1/3 octave, like the room tuning
    sel = (FB >= 45) & (FB <= 300) & (null < 0.5)
    hr, hz, who = headroom(r8, np.abs(h), wf, pr)
    return dict(n=n, rows=rows, rms=float(np.sqrt(np.mean(e[sel] ** 2))), maxabs=float(np.abs(e[sel]).max()),
                dip85=float(np.interp(np.log(85), np.log(FB), e)),
                headroom=hr - base_h, limit=f"{who}@{hz:.0f}", h=h)


# ------------------------------------------------------------ mid/treble
P = np.genfromtxt(MEAS / "2026-10-02_tuning22_refine/prediction.csv", delimiter=",", names=True)
G = P["frequency_hz"]
t22 = P["predicted_linear_trial_db"]
ROWS = list(csv.DictReader(open(MEAS / "2026-10-02_tuning22_refine/sorted_eq.csv")))
common = [(float(r["frequency_hz"]), float(r["q"]), float(r["boost_db"])) for r in ROWS
          if r["block"] == "Tweeter EQ" and float(r["frequency_hz"]) != 3500.0]
M = Model()
lo_t, hi_t = M.filters("LR4", 3000)
wv, tv, _ = M.responses(lo_t, hi_t, -10.0, 3, 1, -4)
share_t = np.abs(tv) ** 2 / (np.abs(wv) ** 2 + np.abs(tv) ** 2)
share_t = np.interp(np.log(G), np.log(M.g), M.smooth(10 * np.log10(np.maximum(share_t, 1e-9)), 3), left=-90, right=0)
share_t = 10 ** (share_t / 10)
c_db = np.zeros_like(G)
for f0, qq, g in common:
    c_db += db(rbj("peak", f0, qq, G, g))
tw_db = 10 * np.log10((1 - share_t) + share_t * np.abs(rbj("peak", 3500, 3.0, G, -2.0)) ** 2)
noeq_today = t22 - c_db - tw_db
_, _, ot = M.responses(lo_t, hi_t, -10.0, 3, 1, -4)
rec = json.load(open("recommended_crossover.json"))
lo_n, hi_n = realise(M, sections_B()[0]), realise(M, sections_B()[1])
_, _, on = M.responses(lo_n, hi_n, rec["tweeter_trim_db"], rec["tweeter_delay_samples"], -1, -4)
dx = M.smooth(M.power_proxy(on), 3) - M.smooth(M.power_proxy(ot), 3)
dx = np.interp(np.log(G), np.log(M.g), dx, left=0.0, right=dx[-1])
fade = np.clip((np.log(G) - np.log(400)) / (np.log(700) - np.log(400)), 0, 1)
noeq_new = noeq_today + dx * fade
T_u = tgt(G)
usel = (G >= 300) & (G <= 14000)


def upper_eq(x, m):
    h = np.zeros_like(G)
    rows = []
    for i in range(m):
        f0, qq, g = np.exp(x[3 * i]), x[3 * i + 1], x[3 * i + 2]
        h += db(rbj("peak", f0, qq, G, g))
        rows.append(("Peaking", f0, qq, g))
    return h, rows


def fit_upper(m, seeds=12):
    best = None
    rng = np.random.default_rng(11)
    for s in range(seeds):
        x0, lb, ub = [], [], []
        for i in range(m):
            x0 += [np.log(np.exp(rng.uniform(np.log(300), np.log(12000)))), rng.uniform(.5, 3), rng.uniform(-4, 2)]
            lb += [np.log(250), .4, -8.]; ub += [np.log(16000), 6., 4.]
        if m == 0:
            break
        r = least_squares(lambda x: (noeq_new + upper_eq(x, m)[0] - T_u)[usel], x0, bounds=(lb, ub), max_nfev=3000)
        if best is None or r.cost < best.cost:
            best = r
    h, rows = upper_eq(best.x if m else [], m)
    e = (noeq_new + h - T_u)[usel]
    return dict(m=m, rows=rows, rms=float(np.sqrt(np.mean(e ** 2))), min=float(e.min()), max=float(e.max()), h=h)


if __name__ == "__main__":
    out = {"bass": [], "upper": []}
    print("Bass (woofer bank), fitted 45-300 Hz excluding the 85 Hz null:")
    for n in (1, 2, 3, 4, 5):
        b = fit_bass(n)
        out["bass"].append({k: v for k, v in b.items() if k != "h"})
        print(f"  HP pair + {n} peaking: 1/3-oct RMS {b['rms']:.2f} dB, max {b['maxabs']:.1f} dB, 85 Hz {b['dip85']:+.1f} dB, headroom vs today {b['headroom']:+.1f} dB ({b['limit']}) | " + " ".join(f"{t[:2]} {a:.0f}/Q{q:.2f}/{g:+.1f}" for t, a, q, g in b['rows']))
    print("Mid/treble (both banks), 300 Hz-14 kHz:")
    for m in (0, 1, 2, 3, 4, 5, 6):
        u = fit_upper(m)
        out["upper"].append({k: v for k, v in u.items() if k != "h"})
        print(f"  {m} peaking: RMS {u['rms']:.2f} dB, range {u['min']:+.1f}/{u['max']:+.1f} dB")
    json.dump(out, open("minimal_eq_scan.json", "w"), indent=1, default=float)


# ------------------------------------------------- structured bass set (used)
def structured_bass(n_cuts, seeds=24):
    """HP pair (Q 0.6-0.9) + ONE broad lift (Q <= 1.2, <= +10 dB) + n_cuts
    cuts (gain <= 0) for room peaks.  No narrow boosts: they would chase room
    dips (55 Hz, 85 Hz) and waste excursion/voltage."""
    def build(x):
        h = rbj("hp", np.exp(x[0]), x[1], FB) * rbj("hp", np.exp(x[0]), x[2], FB)
        rows = [("High-pass", np.exp(x[0]), x[1], 0.0), ("High-pass", np.exp(x[0]), x[2], 0.0),
                ("Peaking", np.exp(x[3]), x[4], x[5])]
        h = h * rbj("peak", np.exp(x[3]), x[4], FB, x[5])
        for i in range(n_cuts):
            f0, qq, g = np.exp(x[6 + 3 * i]), x[7 + 3 * i], x[8 + 3 * i]
            h = h * rbj("peak", f0, qq, FB, g)
            rows.append(("Peaking", f0, qq, g))
        return h, rows

    def res(x):
        h, _ = build(x)
        e = room8 + db(h) - T_b
        w = np.where(FB < 45, 0.4, 1.0)
        w = np.where(e < 0, w * (1 - 0.85 * null), w)
        over = np.maximum(db(h) - 8.0, 0) * null * 3
        return np.r_[(e * w)[bsel], over[bsel]]

    rng = np.random.default_rng(3)
    best = None
    for s in range(seeds):
        x0 = [np.log(rng.uniform(42, 58)), .71, .71, np.log(rng.uniform(60, 85)), rng.uniform(.6, 1.1), rng.uniform(5, 9)]
        lb = [np.log(35), .6, .6, np.log(50), .5, 0.]
        ub = [np.log(70), .9, .9, np.log(110), 1.2, 10.]
        for i in range(n_cuts):
            x0 += [np.log(rng.uniform(65, 260)), rng.uniform(1.5, 4.5), rng.uniform(-6, -1)]
            lb += [np.log(60), 1., -10.]; ub += [np.log(320), 6., 0.]
        r = least_squares(res, x0, bounds=(lb, ub), max_nfev=4000)
        if best is None or r.cost < best.cost:
            best = r
    h, rows = build(best.x)
    e = third(room8 + db(h), FB) - third(T_b, FB)
    sel = (FB >= 45) & (FB <= 300) & (null < 0.5)
    hs = []
    for e_ in ens:
        q_, wf_, pr_, box_ = F.make(np.asarray(e_["x"]))
        a11 = solve(FB, wf_, pr_, box_, 11.0, 1.0); a8 = solve(FB, wf_, pr_, box_, 8.0, 1.0)
        h0, _, _ = headroom(a11, np.abs(eq_bass(FB)), wf_, pr_)
        h1, hz, who = headroom(a8, np.abs(h), wf_, pr_)
        hs.append((h1 - h0, f"{who}@{hz:.0f}"))
    return dict(n_cuts=n_cuts, rows=rows, h=h, rms=float(np.sqrt(np.mean(e[sel] ** 2))),
                maxabs=float(np.abs(e[sel]).max()), err_at={str(k): float(np.interp(np.log(k), np.log(FB), e)) for k in (45, 50, 55, 60, 70, 85, 100, 140, 200, 250)},
                headroom=[min(v for v, _ in hs), max(v for v, _ in hs)], limits=sorted({l for _, l in hs}))
