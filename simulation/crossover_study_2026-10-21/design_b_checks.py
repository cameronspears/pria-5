"""Tolerance and remaining-EQ checks for the recommended design B."""
import json, sys
import numpy as np
sys.path.insert(0, '.')
from xover_model import *
from standard_asym import branch
from optimize_xover import eq_budget

M = Model()
DESIGNS = {
    "today": (("LR4", 3000), ("LR4", 3000), -10.0, 3, 1),
    "B": (("LR8", 2381), ("BES4", 3367), -10.5, 3, -1),
}
out = {}
for name, ((lf, fl), (hf, fh), tg, d, pol) in DESIGNS.items():
    lo, hi = branch(M, "lo", lf, fl), branch(M, "hi", hf, fh)
    base = M.evaluate(lo, hi, tg, d, pol, w_gain_db=-4)
    tol = {}
    for dd in (-1, 1):
        tol[f"delay{dd:+d}"] = score(M.evaluate(lo, hi, tg, d + dd, pol, w_gain_db=-4))
    for dg in (-1.0, -0.5, 0.5, 1.0):
        tol[f"trim{dg:+.1f}"] = score(M.evaluate(lo, hi, tg + dg, d, pol, w_gain_db=-4))
    for sc in (0.95, 1.05):
        lo2, hi2 = branch(M, "lo", lf, fl * sc), branch(M, "hi", hf, fh * sc)
        tol[f"corners x{sc}"] = score(M.evaluate(lo2, hi2, tg, d, pol, w_gain_db=-4))
    tol["polarity flipped"] = score(M.evaluate(lo, hi, tg, d, -pol, w_gain_db=-4))
    eqb = eq_budget(M, lo, hi, tg, d, pol, nmax=4, band=(1000, 12000))
    out[name] = dict(score=score(base), metrics=base, tolerance=tol, eq_budget=eqb)
    print(f"\n{name}: score {score(base):.3f}  " + " ".join(f"{k}:{v:.2f}" for k, v in tol.items()))
    for e in eqb:
        print(f"   {e['n']} EQ filters -> LW 1-12 kHz RMS {e['lw_rms']:.2f} dB" + (f", p-p {e['lw_ptp']:.1f}, axis RMS {e['on_rms']:.2f}" if e['n'] else "") + "  " + " | ".join(f"{x['hz']:.0f} Hz Q{x['q']} {x['gain_db']:+.1f}" for x in e["filters"]))
json.dump(out, open("design_b_checks.json", "w"), indent=1)
