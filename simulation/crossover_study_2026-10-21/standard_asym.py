"""Block-friendly asymmetric designs: standard LR/BW/Bessel slopes with
independent low/high corners, polarity, integer delay and tweeter trim."""
import json, sys, itertools
import numpy as np
from scipy.optimize import minimize_scalar
sys.path.insert(0, '.')
from xover_model import *

# 2nd-order section Qs and corner scalings (Bessel normalised to -3 dB at fc)
FAM = {
    "LR4": [(1.0, .7071), (1.0, .7071)],
    "BW4": [(1.0, .5412), (1.0, 1.3066)],
    "BES4": [(1.4192, .5219), (1.5912, .8055)],   # -3 dB at fc
    "LR8": [(1.0, .5412), (1.0, 1.3066), (1.0, .5412), (1.0, 1.3066)],
}


def branch(model, side, fam, fc):
    t = "lp" if side == "lo" else "hp"
    h = np.ones_like(model.g, complex)
    for k, q in FAM[fam]:
        f0 = fc * k if side == "lo" else fc / k
        h = h * rbj(t, f0, q, model.g)
    return h


def best_for(model, fl_fam, fh_fam, limit):
    best = None
    for fl in 1500 * 2 ** (np.arange(0, 21) / 12):
        lo = branch(model, "lo", fl_fam, fl)
        for fh in 1500 * 2 ** (np.arange(0, 21) / 12):
            hi = branch(model, "hi", fh_fam, fh)
            for pol in (1, -1):
                for d in range(-2, 10):
                    for tg in np.arange(-14, -7.9, 0.5):
                        m = model.evaluate(lo, hi, tg, d, pol, w_gain_db=-4)
                        if m["tweeter_limit"] < limit:
                            continue
                        s = score(m)
                        if best is None or s < best[0]:
                            best = (s, dict(lo=fl_fam, fl=float(fl), hi=fh_fam, fh=float(fh), pol=pol, delay=d, t_gain=float(tg)), m)
    return best


if __name__ == "__main__":
    model = Model()
    limit = float(sys.argv[1]) if len(sys.argv) > 1 else 100.0
    out = []
    for fl_fam, fh_fam in itertools.product(("LR4", "LR8"), ("LR4", "BW4", "BES4", "LR8")):
        b = best_for(model, fl_fam, fh_fam, limit)
        if b is None:
            continue
        s, p, m = b
        out.append(dict(score=s, **p, **m))
        print(f"lo {fl_fam}@{p['fl']:5.0f} hi {fh_fam}@{p['fh']:5.0f} pol {p['pol']:+d} d {p['delay']} tg {p['t_gain']:5.1f} | score {s:.3f} on {m['on_rms']:.2f} lw {m['lw_rms']:.2f} vert {m['vert_rms']:.2f} vmin {m['vert_min']:.1f} tw {m['tweeter_limit']:.1f} xo {m['acoustic_xo_hz']:.0f}", flush=True)
    json.dump(out, open(f"standard_asym_{limit:.0f}.json", "w"), indent=1)
