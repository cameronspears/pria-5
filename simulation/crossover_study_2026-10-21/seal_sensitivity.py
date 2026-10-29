"""Does a better-sealed rebuild change the PR-mass / bass-target answer?

The fitted leakage Q of the measured September build is ~36-39 (already tight).
Re-score the recommended bass target with the box made tighter (QL 100,
essentially sealed) and leakier (QL 10), for every LF fit.
"""
import json, sys
import numpy as np
from dataclasses import replace
sys.path.insert(0, '.')
import fit_lf as F
import bass_target_study as B

ens = json.load(open("lf_ensemble.json"))
_make = F.make
out = {}
for ql in (None, 100.0, 10.0):
    def make_ql(x, _ql=ql):
        q, wf, pr, box = _make(x)
        return q, wf, pr, (box if _ql is None else replace(box, ql=_ql))
    F.make = make_ql
    B.F.make = make_ql
    label = "fitted (~37)" if ql is None else f"{ql:.0f}"
    out[label] = {}
    for mass in (7, 8, 9, 10, 11):
        rs = [B.evaluate(e, mass, 4, 55, 8, 8.0, 100.0) for e in ens]
        out[label][mass] = dict(headroom=[min(r["headroom"] for r in rs), max(r["headroom"] for r in rs)],
                                punch=float(np.mean([r["punch"] for r in rs])),
                                deep=float(np.mean([r["deep"] for r in rs])))
    print(f"QL {label}: " + "  ".join(f"{m} g {v['headroom'][0]:+.1f}..{v['headroom'][1]:+.1f}" for m, v in out[label].items()))
F.make = _make
json.dump(out, open("seal_sensitivity.json", "w"), indent=1)
