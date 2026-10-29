"""PR added-mass study: response, required EQ and excursion-limited output.

For every LF fit in lf_ensemble.json and each added mass, the DSP EQ needed to
hit one common anechoic target (flat passband, 4th-order Butterworth high-pass
at FT Hz) is computed exactly as T/R.  The excursion each driver then needs
for a sine at every frequency gives the passband SPL at which the first part
(ND91 4.6 mm, PR 6 mm, or 12 V amplifier rms) reaches its limit.
"""
import json, sys
import numpy as np
sys.path.insert(0, '.')
import fit_lf as F
from lf_model import *

VMAX = 12.0                         # V rms per channel, KABD-250 @ 24 V (approx.)
MASSES = np.arange(0, 15.5, 0.5)
f = np.geomspace(20, 400, 600)


def target(f, ft, order=8):
    s = 1j * f / ft
    from scipy.signal import butter, freqs
    b, a = butter(order, 1.0, btype="high", analog=True)
    return np.polyval(b, s) / np.polyval(a, s)


def study(x, ft, masses=MASSES):
    q, wf, pr, box = F.make(np.asarray(x))
    rows = []
    for m in masses:
        r = solve(f, wf, pr, box, m, 1.0)                 # 1 V rms, no DSP
        p = farfield(r)
        ref = np.median(np.abs(p[(f > 150) & (f < 300)]))
        raw_db = db(p / ref)
        T = target(f, ft)
        E = T / (p / ref)                                  # required EQ (complex)
        e_db = db(E)
        # passband SPL (1 m, 4pi) per volt of passband drive
        spl_per_v = db(ref / P_REF)
        # for a sine at f with passband-level L: V(f) = 10^((L - spl_per_v)/20) * |E(f)|
        xw = r["xw"] * np.abs(E)       # m per V of passband drive
        xp = r["xp"] * np.abs(E)
        v = np.abs(E)
        lim_w = spl_per_v + 20 * np.log10(wf.xmax / np.sqrt(2) / np.maximum(xw, 1e-12))
        lim_p = spl_per_v + 20 * np.log10(pr.xmax / np.sqrt(2) / np.maximum(xp, 1e-12))
        lim_v = spl_per_v + 20 * np.log10(VMAX / np.maximum(v, 1e-12))
        lim = np.minimum(np.minimum(lim_w, lim_p), lim_v)
        band = (f >= 35) & (f <= 200)
        i = np.argmin(lim[band])
        who = ["ND91", "PR", "amp"][int(np.argmin([lim_w[band][i], lim_p[band][i], lim_v[band][i]]))]
        pb = (f >= 45) & (f <= 200)
        rows.append(dict(spl_1v_4pi_db=float(spl_per_v),
            added_g=float(m), fb_hz=float(r["fb"]),
            raw_db_at={str(h): float(np.interp(h, f, raw_db)) for h in (40, 50, 60, 70, 80, 100, 150)},
            eq_max_boost_db=float(e_db[pb].max()), eq_boost_hz=float(f[pb][np.argmax(e_db[pb])]),
            eq_rms_db=float(np.sqrt(np.mean(e_db[(f >= 50) & (f <= 200)] ** 2))),
            max_passband_spl_db=float(lim[band][i]), limit_hz=float(f[band][i]), limited_by=who,
            woofer_limit_db=float(lim_w[band].min()), pr_limit_db=float(lim_p[band].min()),
            amp_limit_db=float(lim_v[band].min())))
    return rows


if __name__ == "__main__":
    ens = json.load(open("lf_ensemble.json"))
    out = {}
    for ft in (50.0, 55.0, 60.0, 65.0):
        out[str(ft)] = {}
        for e in ens:
            rows = study(e["x"], ft)
            out[str(ft)][f"{e['vb_l']:.2f}"] = rows
        print(f"\nTarget: flat with 8th-order BW high-pass at {ft:.0f} Hz (PR-like steep roll-off)")
        print(" added_g  Fb   | EQ max boost (dB@Hz) per fit      | max clean passband SPL @1m per fit (limiter)")
        for k, m in enumerate(MASSES):
            if m not in (0, 1, 2, 3, 4, 5, 6, 8, 11, 14):
                continue
            cells = [out[str(ft)][key][k] for key in out[str(ft)]]
            print(f"  {m:4.1f}  {cells[0]['fb_hz']:5.1f} | " +
                  " ".join(f"{c['eq_max_boost_db']:+5.1f}@{c['eq_boost_hz']:3.0f}" for c in cells) + " | " +
                  " ".join(f"{c['max_passband_spl_db']:5.1f}{c['limited_by'][0]}@{c['limit_hz']:3.0f}" for c in cells))
    json.dump(out, open("pr_mass_study.json", "w"), indent=1)
