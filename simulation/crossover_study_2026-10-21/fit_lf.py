"""Fit the lumped LF model to the 2026-09-29 woofer + both-PR nearfields.

Measured state: 11 g added to EACH DS115-PR (incl. screw), 2 x 50 Hz HP on,
no lining (pre-lining), sealed by user.  Complex (magnitude AND phase) fit;
datasheet values are priors, not fixed truths.  Woofer 25-400 Hz; PRs
36-90 Hz only (above ~100 Hz the PR microphones are dominated by woofer
sound leaking around the cabinet, below ~35 Hz they are in the noise).
"""
import json, sys
import numpy as np
from dataclasses import replace, asdict
from scipy.optimize import least_squares
sys.path.insert(0, '.')
from lf_model import *

ADDED_G = 11.0
d = load_nearfields()
f, pw, snr_w = d["woofer"]
_, pr_r, snr_r = d["pr_right"]
_, pr_l, snr_l = d["pr_left"]
pp = (pr_r + pr_l) / 2
mw = (f >= 25) & (f <= 400) & (snr_w > 10)
mp = (f >= 36) & (f <= 90)
H = dsp_chain_bass(f)

NAMES = ["logG", "tau_ms", "phi0", "w_mms", "w_cms", "w_rms", "w_bl",
         "vb", "ql", "p_cms", "p_rms", "p_mass", "p_sd"]
PRIOR = dict(w_mms=(0, .15), w_cms=(0, .25), w_rms=(0, .5), w_bl=(0, .15),
             vb=(0, .4), ql=(np.log(10), 1.2), p_cms=(0, .4), p_rms=(0, 1.0),
             p_mass=(0, .05), p_sd=(0, .1))


def make(x):
    q = dict(zip(NAMES, x))
    wf = replace(Woofer(), mms=Woofer.mms * np.exp(q["w_mms"]), cms=Woofer.cms * np.exp(q["w_cms"]),
                 rms=Woofer.rms * np.exp(q["w_rms"]), bl=Woofer.bl * np.exp(q["w_bl"]))
    total_mass = (Radiator.mms + ADDED_G * 1e-3) * np.exp(q["p_mass"])
    pr = replace(Radiator(), cms=Radiator.cms * np.exp(q["p_cms"]), rms=Radiator.rms * np.exp(q["p_rms"]),
                 sd=Radiator.sd * np.exp(q["p_sd"]), mms=total_mass - ADDED_G * 1e-3)
    box = replace(Box(), vb=Box.vb * np.exp(q["vb"]), ql=np.exp(q["ql"]))
    return q, wf, pr, box


def predict(x):
    q, wf, pr, box = make(x)
    r = solve(f, wf, pr, box, ADDED_G, 1.0, H)
    k = np.exp(q["logG"]) * np.exp(1j * (q["phi0"] - 2 * np.pi * f * q["tau_ms"] * 1e-3))
    return k * nearfield(r, "woofer", wf, pr), k * nearfield(r, "pr", wf, pr), r, (wf, pr, box)


def resid(x):
    a, b, _, _ = predict(x)
    ew = np.log(pw[mw] / a[mw])
    ep = np.log(pp[mp] / b[mp])
    # phase residual wrapped
    out = [ew.real, np.angle(np.exp(1j * ew.imag)) * 0.5,
           ep.real * 1.5, np.angle(np.exp(1j * ep.imag)) * 0.75]
    q = dict(zip(NAMES, x))
    pri = [(q[k] - m) / s * 0.3 for k, (m, s) in PRIOR.items()]
    return np.concatenate(out + [np.array(pri)])


def fit():
    x0 = np.zeros(len(NAMES))
    x0[NAMES.index("ql")] = np.log(10)
    # start scale from data
    a, _, _, _ = predict(x0)
    x0[0] = np.median(np.log(np.abs(pw[mw] / a[mw])))
    best = None
    for phi in (0.0, np.pi):
        for vb in (0.0, 0.4):
            x = x0.copy(); x[2] = phi; x[NAMES.index("vb")] = vb
            r = least_squares(resid, x, method="lm" if False else "trf", max_nfev=4000)
            if best is None or r.cost < best.cost:
                best = r
    return best


if __name__ == "__main__":
    r = fit()
    q, wf, pr, box = make(r.x)
    a, b, res, _ = predict(r.x)
    ew = 20 * np.log10(np.abs(pw / a)); ep = 20 * np.log10(np.abs(pp / b))
    phw = np.degrees(np.angle(pw / a)); php = np.degrees(np.angle(pp / b))
    fs_w = 1 / (2 * np.pi * np.sqrt(wf.mms * wf.cms))
    qes = 2 * np.pi * fs_w * wf.mms * wf.re / wf.bl ** 2
    qms = 2 * np.pi * fs_w * wf.mms / wf.rms
    vas = RHO * C ** 2 * wf.sd ** 2 * wf.cms * 1e3
    summary = dict(
        cost=float(r.cost),
        woofer=dict(fs_hz=fs_w, qms=qms, qes=qes, qts=qms * qes / (qms + qes), vas_l=vas,
                    mms_g=wf.mms * 1e3, cms_mm_per_n=wf.cms * 1e3, bl=wf.bl),
        box=dict(vb_l=box.vb * 1e3, ql=box.ql),
        pr=dict(moving_mass_total_g=(pr.mms + ADDED_G * 1e-3) * 1e3, stock_mass_implied_g=pr.mms * 1e3,
                cms_mm_per_n=pr.cms * 1e3, rms=pr.rms, sd_cm2=pr.sd * 1e4,
                fs_free_air_with_11g_hz=1 / (2 * np.pi * np.sqrt((pr.mms + ADDED_G * 1e-3) * pr.cms))),
        fb_hz=float(res["fb"]),
        fit_quality=dict(woofer_mag_rms_db=float(np.sqrt(np.mean(ew[mw] ** 2))),
                         woofer_phase_rms_deg=float(np.sqrt(np.mean(phw[mw] ** 2))),
                         pr_mag_rms_db=float(np.sqrt(np.mean(ep[mp] ** 2))),
                         pr_phase_rms_deg=float(np.sqrt(np.mean(php[mp] ** 2)))),
        params=dict(zip(NAMES, map(float, r.x))))
    print(json.dumps(summary, indent=1))
    json.dump(summary, open("lf_fit.json", "w"), indent=1)
    for hz in (30, 35, 40, 45, 49, 52, 55, 60, 70, 80, 100, 150, 200, 300):
        i = np.argmin(abs(f - hz))
        print(f"{hz:4d} W meas {db(pw[i]/P_REF):5.1f} model {db(a[i]/P_REF):5.1f}  ph {np.angle(pw[i],deg=True):6.0f}/{np.angle(a[i],deg=True):6.0f} | PR meas {db(pp[i]/P_REF):5.1f} model {db(b[i]/P_REF):5.1f} ph {np.angle(pp[i],deg=True):6.0f}/{np.angle(b[i],deg=True):6.0f}")
