"""Apples-to-apples: today's crossover WITH its crossover-region EQ vs design B
(and a higher-margin B variant), plus margin variants of B."""
import json, sys
import numpy as np
sys.path.insert(0, '.')
from xover_model import *
from standard_asym import branch

M = Model()


def eqrows(rows, tweeter_only=()):
    common = np.ones_like(M.g, complex)
    for f0, q, gdb in rows:
        common = common * rbj("peak", f0, q, M.g, gdb)
    tw = np.ones_like(M.g, complex)
    for f0, q, gdb in tweeter_only:
        tw = tw * rbj("peak", f0, q, M.g, gdb)
    return common, tw


def run(lo, hi, tg, d, pol, common=None, tw=None):
    hi2 = hi * (tw if tw is not None else 1)
    return M.evaluate(lo, hi2, tg, d, pol, eq=common, w_gain_db=-4)


TODAY_XO_EQ = [(1220, 6.0, -4.0), (1690, 1.9, -3.0), (3300, 3.2, -2.0)]
TODAY_TW_EQ = [(3500, 3.0, -2.0)]
lo_t, hi_t = branch(M, "lo", "LR4", 3000), branch(M, "hi", "LR4", 3000)
c, t = eqrows(TODAY_XO_EQ, TODAY_TW_EQ)
rows = {}
rows["today, no EQ"] = run(lo_t, hi_t, -10, 3, 1)
rows["today + its 4 crossover-region EQ filters"] = run(lo_t, hi_t, -10, 3, 1, c, t)
for sc, label in ((1.0, "B"), (1.06, "B +6% corners"), (1.12, "B +12% corners")):
    lo, hi = branch(M, "lo", "LR8", 2381 * sc), branch(M, "hi", "BES4", 3367 * sc)
    best = None
    for d in range(1, 6):
        for tg in np.arange(-12, -8.9, 0.25):
            m = run(lo, hi, tg, d, -1)
            if best is None or score(m) < best[0]:
                best = (score(m), d, tg, m)
    s, d, tg, m = best
    rows[f"{label} (d{d}, trim {tg:.2f}), no EQ"] = m
    c1, t1 = eqrows([], [(3420, 4.0, -2.0)])
    rows[f"{label} (d{d}, trim {tg:.2f}) + 1 tweeter cut 3.42k Q4 -2"] = run(lo, hi, tg, d, -1, None, t1)
for k, m in rows.items():
    print(f"{k:60s} score {score(m):.2f} | axis {m['on_rms']:.2f} (p-p {m['on_ptp']:.1f}) | LW {m['lw_rms']:.2f} (p-p {m['lw_ptp']:.1f}) | vert {m['vert_rms']:.2f} dip {m['vert_min']:.1f} | tweeter Xmax at {m['tweeter_limit']:.1f} dB @ {m['tweeter_limit_hz']:.0f} | XO {m['acoustic_xo_hz']:.0f}")
json.dump({k: dict(score=score(v), **v) for k, v in rows.items()}, open("compare_final.json", "w"), indent=1)
