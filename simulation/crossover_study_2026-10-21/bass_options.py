"""Room-dip boost trade-off and the bass options compared in the README.

Uses the 2.7 L LF fit (middle of the ensemble; all fits agree within ~0.5 dB
on these deltas) and the same in-room ratio method as volume_first.py.
"""
import json, sys
import numpy as np
from scipy.optimize import least_squares
sys.path.insert(0, '.')
import fit_lf as F
from lf_model import *
from common import rbj
from inroom_pr_study import eq_bass, room_raw, f
from volume_first import hp8, eq_nohp, headroom

ens = json.load(open("lf_ensemble.json"))
fit = next(e for e in ens if abs(e["vb_l"] - 2.7) < 0.01)
q, wf, pr, box = F.make(np.asarray(fit["x"]))
p11 = farfield(solve(f, wf, pr, box, 11.0, 1.0))
r11 = solve(f, wf, pr, box, 11.0, 1.0)
today = np.abs(eq_bass(f))
base_h, _, _ = headroom(r11, today, wf, pr)
today_target = today * np.abs(p11)
_, room = room_raw()


def required(m, ft, cap):
    r = solve(f, wf, pr, box, m, 1.0)
    target = np.abs(eq_nohp(f) * p11 * hp8(f, ft))
    eq = target / np.abs(farfield(r))
    if cap is not None:
        w = np.exp(-0.5 * (np.log(f / 90) / 0.18) ** 2)
        excess = np.maximum(db(eq) - cap, 0) * w
        eq = eq / 10 ** (excess / 20)
        target = target / 10 ** (excess / 20)
    return r, eq, target


print("Room-dip boost cap sweep (dB headroom gain vs today | in-room level change @85 Hz):")
for ft in (55, 60):
    for m in (11, 8):
        cells = []
        for cap in (None, 10, 8, 6, 4):
            r, eq, tgt = required(m, ft, cap)
            h, hz, who = headroom(r, eq, wf, pr)
            cells.append(f"cap {str(cap):>4s}: {h-base_h:+4.1f} dB ({who[0]}@{hz:3.0f}) / {np.interp(85, f, db(tgt/today_target)):+4.1f}")
        print(f" cutoff {ft} Hz, {m:2d} g | " + " | ".join(cells))


out = {}
OPTIONS = {
    "today (11 g, T22 bass EQ)": (11, None, None),
    "DSP only: 11 g, 55 Hz cut, 85 Hz boost <= +8 dB": (11, 55, 8.0),
    "Recommended: 8 g, 55 Hz cut, 85 Hz boost <= +8 dB": (8, 55, 8.0),
    "More output: 8 g, 60 Hz cut, 85 Hz boost <= +6 dB": (8, 60, 6.0),
}
for name, (m, ft, cap) in OPTIONS.items():
    if ft is None:
        r, eq, tgt = r11, today, today_target
    else:
        r, eq, tgt = required(m, ft, cap)
    h, hz, who = headroom(r, eq, wf, pr)
    out[name] = dict(added_g=m, cutoff_hz=ft, dip_cap_db=cap, fb_hz=float(r["fb"]),
                     headroom_gain_db=h - base_h, first_limit=f"{who} @ {hz:.0f} Hz",
                     inroom_change_vs_today_db={str(x): float(np.interp(x, f, db(tgt / today_target))) for x in (40, 45, 50, 55, 60, 70, 85, 100, 150)})
    print(f"{name}: Fb {r['fb']:.1f} Hz | headroom vs today {h-base_h:+.1f} dB (first limit {who} @ {hz:.0f} Hz)")
    print("   in-room vs today: " + " ".join(f"{k}:{v:+.1f}" for k, v in out[name]["inroom_change_vs_today_db"].items()))
# NOTE: an automatic few-biquad fit of these targets was tried and rejected
# (1.3-3.2 dB RMS misfit; room modes make the target too lumpy).  The final
# bass EQ is to be designed from a fresh room average after the PR change.
json.dump(out, open("bass_options.json", "w"), indent=1)
