"""Family of LF fits with the box volume pinned to physically plausible values.

The nearfield data cannot separate box volume from radiator area/stiffness
on their own, so each fit pins Vb and lets the rest float.  A PR-mass
conclusion is only trusted if it holds across every fit that matches the
data well.
"""
import json, sys
import numpy as np
from scipy.optimize import least_squares
sys.path.insert(0, '.')
import fit_lf as F
from lf_model import *

VBS = [2.3, 2.5, 2.7, 2.9, None]


def fit_pinned(vb_l):
    names = F.NAMES
    iv = names.index("vb")
    if vb_l is None:
        r = F.fit()
        return r.x, r.cost
    vbx = np.log(vb_l / (Box.vb * 1e3))

    def res(xr):
        x = np.insert(xr, iv, vbx)
        return F.resid(x)
    x0 = np.zeros(len(names)); x0[names.index("ql")] = np.log(10)
    a, _, _, _ = F.predict(x0)
    x0[0] = np.median(np.log(np.abs(F.pw[F.mw] / a[F.mw])))
    best = None
    for phi in (0.0, np.pi, -2.8):
        for pc in (0.0, -0.8):
            x = x0.copy(); x[2] = phi; x[names.index("p_cms")] = pc
            r = least_squares(res, np.delete(x, iv), max_nfev=5000)
            if best is None or r.cost < best.cost:
                best = r
    return np.insert(best.x, iv, vbx), best.cost


def describe(x):
    q, wf, pr, box = F.make(x)
    a, b, res, _ = F.predict(x)
    ew = 20 * np.log10(np.abs(F.pw / a))[F.mw]; ep = 20 * np.log10(np.abs(F.pp / b))[F.mp]
    phw = np.degrees(np.angle(F.pw / a))[F.mw]; php = np.degrees(np.angle(F.pp / b))[F.mp]
    fs_w = 1 / (2 * np.pi * np.sqrt(wf.mms * wf.cms))
    qes = 2 * np.pi * fs_w * wf.mms * wf.re / wf.bl ** 2
    qms = 2 * np.pi * fs_w * wf.mms / wf.rms
    return dict(vb_l=box.vb * 1e3, ql=box.ql, fb=float(res["fb"]),
                w_fs=fs_w, w_qes=qes, w_qms=qms, w_bl=wf.bl,
                pr_cms_mm_n=pr.cms * 1e3, pr_sd_cm2=pr.sd * 1e4, pr_mass_total_g=(pr.mms + 11e-3) * 1e3,
                pr_rms=pr.rms,
                rms_w_db=float(np.sqrt(np.mean(ew ** 2))), rms_w_deg=float(np.sqrt(np.mean(phw ** 2))),
                rms_p_db=float(np.sqrt(np.mean(ep ** 2))), rms_p_deg=float(np.sqrt(np.mean(php ** 2))))


if __name__ == "__main__":
    out = []
    for vb in VBS:
        x, cost = fit_pinned(vb)
        dsc = describe(x)
        dsc.update(cost=float(cost), x=list(map(float, x)), pinned=vb)
        out.append(dsc)
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in dsc.items() if k != "x"})
    json.dump(out, open("lf_ensemble.json", "w"), indent=1)
