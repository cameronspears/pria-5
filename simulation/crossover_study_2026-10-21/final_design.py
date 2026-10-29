"""Rounded, implementable recommendation and its predicted effects."""
import json, sys
import numpy as np
sys.path.insert(0, '.')
import xover_model as XM
from xover_model import *

LR8Q = (0.5412, 1.3066)
BES4 = ((1.4192, 0.5219), (1.5912, 0.8055))


def sections_B(fl=2500.0, fh=3550.0):
    lo = [("LP", fl, LR8Q[0]), ("LP", fl, LR8Q[1]), ("LP", fl, LR8Q[0]), ("LP", fl, LR8Q[1])]
    hi = [("HP", fh / k, q) for k, q in BES4]
    return lo, hi


def realise(M, secs):
    h = np.ones_like(M.g, complex)
    for t, f0, q in secs:
        h = h * rbj(t.lower(), f0, q, M.g)
    return h


if __name__ == "__main__":
    M = Model()
    lo_s, hi_s = sections_B()
    lo, hi = realise(M, lo_s), realise(M, hi_s)
    grid = []
    for d in range(0, 7):
        for tg in np.arange(-12, -8.9, 0.25):
            m = M.evaluate(lo, hi, tg, d, -1, w_gain_db=-4)
            grid.append((score(m), d, float(tg), m))
    grid.sort(key=lambda r: r[0])
    s, d, tg, m = grid[0]
    today = M.evaluate(*M.filters("LR4", 3000), -10.0, 3, 1, w_gain_db=-4)
    # in-room shift proxy: power-weighted average of all modelled directions
    _, _, ob = M.responses(lo, hi, tg, d, -1, -4)
    _, _, ot = M.responses(*M.filters("LR4", 3000), -10.0, 3, 1, -4)
    pb, pt = M.smooth(M.power_proxy(ob), 3), M.smooth(M.power_proxy(ot), 3)
    shift = pb - pt
    ref = np.mean(shift[M.band(400, 800)])
    inroom_shift = {str(h): float(np.interp(np.log(h), np.log(M.g), shift - ref)) for h in (1000, 1500, 2000, 2500, 3000, 4000, 6000, 10000)}
    rec = dict(
        woofer_lowpass=[dict(type=t, hz=f0, q=q) for t, f0, q in lo_s],
        tweeter_highpass=[dict(type=t, hz=round(f0, 0), q=q) for t, f0, q in hi_s],
        tweeter_polarity="inverted", tweeter_delay_samples=d, tweeter_trim_db=tg, woofer_trim_db=-4.0,
        metrics=m, score=s, today=dict(score=score(today), **today),
        predicted_inroom_shift_vs_today_db=inroom_shift,
        alternatives=[dict(score=r[0], delay=r[1], trim=r[2]) for r in grid[:6]])
    json.dump(rec, open("recommended_crossover.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in rec.items() if k not in ("metrics", "today")}, indent=1))
    print("B-final", {k: round(v, 2) for k, v in m.items()}, round(s, 3))
    print("today  ", {k: round(v, 2) for k, v in today.items()}, round(score(today), 3))
