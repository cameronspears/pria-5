"""Re-score shortlisted crossover designs under every alternative assumption."""
import json, sys
import numpy as np
sys.path.insert(0, '.')
import xover_model as XM
from xover_model import *
from standard_asym import branch as std_branch
from optimize_xover import branch as free_branch

opt = json.load(open("optimised_3ms.json"))


def free(p):
    def mk(M):
        lo = free_branch(M, "lo", p["fam_lo"], p["fc_lo"], *p["q_lo"])
        hi = free_branch(M, "hi", p["fam_hi"], p["fc_hi"], *p["q_hi"])
        return lo, hi
    return mk


def std(lf, fl, hf, fh):
    return lambda M: (std_branch(M, "lo", lf, fl), std_branch(M, "hi", hf, fh))


DESIGNS = {
    "today (LR4 3k, d3, -10)": (std("LR4", 3000, "LR4", 3000), -10.0, 3, 1),
    "LR4 3k re-trimmed (d5,-11.5)": (std("LR4", 3000, "LR4", 3000), -11.5, 5, 1),
    "LR4 2.4k sym (d6,-12.25)": (std("LR4", 2416, "LR4", 2416), -12.25, 6, 1),
    "A free-opt (tw>=100)": (free(opt["100.0"]["params"]), opt["100.0"]["params"]["t_gain"], opt["100.0"]["delay_samples"], opt["100.0"]["polarity"]),
    "A' free-opt (tw>=103)": (free(opt["103.0"]["params"]), opt["103.0"]["params"]["t_gain"], opt["103.0"]["delay_samples"], opt["103.0"]["polarity"]),
    "B LR8 2.38k / Bessel4 3.37k inv d3": (std("LR8", 2381, "BES4", 3367), -10.5, 3, -1),
    "C LR8 2.38k / LR4 2.38k inv d4": (std("LR8", 2381, "LR4", 2381), -11.5, 4, -1),
}

SCEN = {
    "3ms (base)": dict(window="3ms", k=2.0),
    "5ms": dict(window="5ms", k=2.0),
    "8ms": dict(window="8ms", k=2.0),
    "3ms pure geometry k=1": dict(window="3ms", k=1.0),
    "3ms k=2.5": dict(window="3ms", k=2.5),
}
res = {}
models = {}
for sname, sc in SCEN.items():
    XM.K_VERT = sc["k"]
    M = Model(sc["window"])
    res[sname] = {}
    for dname, (mk, tg, d, pol) in DESIGNS.items():
        lo, hi = mk(M)
        m = M.evaluate(lo, hi, tg, d, pol, w_gain_db=-4)
        # also: best re-trim within +/-1.5 dB and +/-1 sample (practical tolerance)
        res[sname][dname] = dict(score=score(m), **m)
XM.K_VERT = 2.0
print(f"{'design':38s} " + " ".join(f"{s:>22s}" for s in SCEN))
for dname in DESIGNS:
    print(f"{dname:38s} " + " ".join(f"{res[s][dname]['score']:5.2f} ({res[s][dname]['on_rms']:.2f}/{res[s][dname]['lw_rms']:.2f}/{res[s][dname]['vert_rms']:.2f})" for s in SCEN))
print("\ntweeter limit (dB SPL @1m sine, worst freq) and acoustic crossover, base scenario:")
for dname in DESIGNS:
    r = res["3ms (base)"][dname]
    print(f"  {dname:38s} {r['tweeter_limit']:6.1f} dB @ {r['tweeter_limit_hz']:5.0f} Hz | acoustic XO {r['acoustic_xo_hz']:5.0f} Hz | worst +/-15 dip {r['vert_min']:5.1f} dB")
json.dump(res, open("robustness.json", "w"), indent=1)
