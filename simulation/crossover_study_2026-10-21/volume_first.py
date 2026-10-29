"""Volume-first bass study (user: deep bass can go if output/cleanliness improve).

In-room target = today's liked in-room bass shape (room x 11 g speaker x T22
bass EQ without its 50 Hz high-pass) multiplied by an 8th-order Butterworth
high-pass at FT (a steep, PR-like low cut).  For every PR mass, FT and an
optional cap on the boost that fills the ~85 Hz room dip, the woofer EQ is
re-solved, and we report clean headroom (sine, worst frequency 35-200 Hz,
ND91 4.6 mm / PR 6 mm / 12 V) relative to today's setup.
"""
import json, sys
import numpy as np
from scipy.signal import butter
sys.path.insert(0, '.')
import fit_lf as F
from lf_model import *
from common import rbj
from inroom_pr_study import T22_BASS, eq_bass, room_raw, f, VMAX

MASSES = [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14]
FTS = [45, 50, 55, 60, 65, 70]
CAPS = [None, 6.0, 3.0]          # max boost allowed in 75-115 Hz (dB re today's target)


def hp8(fr, ft):
    b, a = butter(8, 1.0, btype="high", analog=True)
    s = 1j * fr / ft
    return np.polyval(b, s) / np.polyval(a, s)


def eq_nohp(fr):
    h = np.ones_like(fr, complex)
    for f0, q, gdb in T22_BASS:
        h = h * rbj("peak", f0, q, fr, gdb)
    return h


def headroom(r, eq_mag, wf, pr):
    xw = r["xw"] * eq_mag * np.sqrt(2)
    xp = r["xp"] * eq_mag * np.sqrt(2)
    lim = np.minimum.reduce([wf.xmax / np.maximum(xw, 1e-15), pr.xmax / np.maximum(xp, 1e-15),
                             VMAX / np.maximum(eq_mag, 1e-15)])
    who = np.argmax(np.vstack([xw / wf.xmax, xp / pr.xmax, eq_mag / VMAX]), axis=0)
    band = (f >= 35) & (f <= 200)
    i = np.argmin(lim[band])
    return float(20 * np.log10(lim[band][i])), float(f[band][i]), ["woofer", "PR", "amp"][who[band][i]]


def run(fit):
    q, wf, pr, box = F.make(np.asarray(fit["x"]))
    p11 = farfield(solve(f, wf, pr, box, 11.0, 1.0))
    base_eq = np.abs(eq_bass(f))                       # today: T22 + 2 x 50 Hz HP
    r11 = solve(f, wf, pr, box, 11.0, 1.0)
    base_h, _, _ = headroom(r11, base_eq, wf, pr)
    today_target = np.abs(base_eq * p11)
    rows = []
    for m in MASSES:
        r = solve(f, wf, pr, box, m, 1.0)
        pm = farfield(r)
        for ft in FTS:
            target = np.abs(eq_nohp(f) * p11 * hp8(f, ft))
            for cap in CAPS:
                eq_mag = target / np.abs(pm)
                tgt = target.copy()
                if cap is not None:
                    w = np.exp(-0.5 * (np.log(f / 90) / 0.18) ** 2)      # ~75-110 Hz window
                    lim = 10 ** (cap / 20) * np.abs(eq_nohp(f)) / 10 ** (12.1 / 20)  # scale
                    # cap: reduce target there so EQ never exceeds `cap` dB of total boost
                    tot = db(eq_mag)
                    excess = np.maximum(tot - cap, 0) * w
                    eq_mag = eq_mag / 10 ** (excess / 20)
                    tgt = tgt / 10 ** (excess / 20)
                h, hz, who = headroom(r, eq_mag, wf, pr)
                loss = db(tgt / today_target)
                rows.append(dict(added_g=m, fb=float(r["fb"]), ft=ft, cap=cap,
                                 headroom_gain_db=h - base_h, worst_hz=hz, limited_by=who,
                                 max_eq_boost_db=float(db(eq_mag)[(f > 40) & (f < 200)].max()),
                                 level_change_db={str(x): float(np.interp(x, f, loss)) for x in (40, 45, 50, 55, 60, 70, 85, 100)}))
    return rows


if __name__ == "__main__":
    ens = json.load(open("lf_ensemble.json"))
    allrows = {f"{e['vb_l']:.2f}": run(e) for e in ens}
    json.dump(allrows, open("volume_first.json", "w"), indent=1)
    keys = list(allrows)
    for cap in CAPS:
        print(f"\n### boost cap in 75-115 Hz: {cap}   (headroom gain vs today, dB; min..max across 5 fits; best mass per cutoff)")
        for ft in FTS:
            line = []
            best = None
            for m in MASSES:
                vals = [next(r for r in allrows[k] if r["added_g"] == m and r["ft"] == ft and r["cap"] == cap) for k in keys]
                lo = min(v["headroom_gain_db"] for v in vals); hi = max(v["headroom_gain_db"] for v in vals)
                line.append(f"{m}g:{lo:+.1f}")
                if best is None or lo > best[0]:
                    best = (lo, hi, m, vals[2])
            lo, hi, m, v = best
            lc = v["level_change_db"]
            print(f" cutoff {ft:2d} Hz | best {m:2d} g -> {lo:+.1f}..{hi:+.1f} dB ({v['limited_by']} @ {v['worst_hz']:.0f} Hz) | level vs today @45/50/55/60/85: {lc['45']:+.1f}/{lc['50']:+.1f}/{lc['55']:+.1f}/{lc['60']:+.1f}/{lc['85']:+.1f} | all: " + " ".join(line))
