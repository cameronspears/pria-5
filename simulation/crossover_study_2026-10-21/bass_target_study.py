"""What in-room bass target gives the most *felt* bass and clean volume?

Target family (in-room, 1/6-octave, same 500 Hz anchor and -0.5 dB/oct line
as Tuning22):  line + low-shelf S (corner F0) + Butterworth high-pass
(corner FC, order N).  The ~85 Hz room null may be filled by at most CAP dB
of total EQ.  For each PR mass the woofer EQ is re-solved (room x model ratio,
as in inroom_pr_study.py) and scored against today:

  punch      50-100 Hz power-average level at the same volume knob
  deep       40-50 Hz level at the same volume
  headroom   how much louder before the first excursion/voltage limit
  max punch  punch + headroom  = loudest clean 50-100 Hz SPL
  warmth     120-250 Hz level at the same volume (the user asked for subtly
             LESS warmth in Tuning22, so this should stay near 0)

History: the first pick (+4 dB shelf at 150 Hz) added +1.7 dB of 120-250 Hz
warmth; the shelf corner was moved to 100 Hz (+0.6 dB) the same day.
"""
import json, sys, itertools
import numpy as np
from scipy.signal import butter
sys.path.insert(0, '.')
import fit_lf as F
from lf_model import *
from common import MEAS
from inroom_pr_study import eq_bass, room_raw, f, VMAX
from volume_first import headroom

ANCHOR, SLOPE = 65.87939154200144, -0.5
ens = json.load(open("lf_ensemble.json"))


def line(fr):
    return ANCHOR + SLOPE * np.log2(fr / 500)


def low_shelf_db(fr, s, f0=150.0):
    # RBJ low shelf, S=1 slope, evaluated in the analog domain
    A = 10 ** (s / 40)
    w = fr / f0
    num = (A - w ** 2) ** 2 + (np.sqrt(A) * w * np.sqrt(2)) ** 2 / 1.0
    den = (1 - A * w ** 2) ** 2 + (np.sqrt(A) * w * np.sqrt(2)) ** 2
    return 10 * np.log10(A ** 2 * num / den) if s else np.zeros_like(fr)


def hp_db(fr, fc, n):
    b, a = butter(n, 1.0, btype="high", analog=True)
    s = 1j * fr / fc
    return db(np.polyval(b, s) / np.polyval(a, s))


def band(x, lo, hi):
    sel = (f >= lo) & (f <= hi)
    return 10 * np.log10(np.mean(10 ** (x[sel] / 10)))


def evaluate(fit, mass, S, FC, N, CAP, F0=100.0):
    q, wf, pr, box = F.make(np.asarray(fit["x"]))
    meas, room11 = room_raw()                    # room11: in-room, 11 g, no EQ
    p11 = farfield(solve(f, wf, pr, box, 11.0, 1.0))
    r = solve(f, wf, pr, box, mass, 1.0)
    room_m = room11 + db(farfield(r) / p11)
    target = line(f) + low_shelf_db(f, S, F0) + hp_db(f, FC, N)
    eq = target - room_m
    if CAP is not None:
        w = np.exp(-0.5 * (np.log(f / 90) / 0.18) ** 2)
        eq = eq - np.maximum(eq - CAP, 0) * w
    result = room_m + eq
    today = meas                                  # today's measured in-room (T12 = T22 below 120 Hz)
    r11 = solve(f, wf, pr, box, 11.0, 1.0)
    h0, _, _ = headroom(r11, np.abs(eq_bass(f)), wf, pr)
    h, hz, who = headroom(r, 10 ** (eq / 20), wf, pr)
    punch = band(result, 50, 100) - band(today, 50, 100)
    return dict(mass=mass, shelf=S, shelf_hz=F0, fc=FC, order=N, cap=CAP,
                warmth=band(result, 120, 250) - band(today, 120, 250),
                headroom=h - h0, limit=f"{who}@{hz:.0f}",
                punch=punch, deep=band(result, 40, 50) - band(today, 40, 50),
                max_punch=punch + (h - h0), result=result.tolist(), eq_db=eq.tolist())


RECOMMENDED = dict(S=4.0, F0=100.0, FC=55.0, N=8, CAP=8.0)


def write_house_curve(path="Pria5_bass_target_house_curve.txt", S=4.0, F0=100.0, FC=55.0, N=8):
    fr = np.unique(np.round(np.geomspace(20, 20000, 241), 2))
    t = SLOPE * np.log2(fr / 500) + low_shelf_db(fr, S, F0) + hp_db(fr, FC, N)
    t = t - np.interp(500, fr, t)
    hdr = ["* Pria 5 in-room bass target (\"punchy\"), 2026-10-21",
           f"* REW house curve: 0 dB at 500 Hz, -0.5 dB/oct tilt, +{S:g} dB low shelf ({F0:g} Hz),",
           f"* roll-off -3 dB at {FC:g} Hz (re the bass plateau), {N}th order (48 dB/oct) below.",
           "* Use with a 12-position RMS room average; 1/6-octave smoothing.",
           "* Do not let EQ fill the ~85 Hz room dip by more than +8 dB total boost."]
    with open(path, "w") as fh:
        fh.write("\n".join(hdr) + "\n")
        for a, b in zip(fr, t):
            fh.write(f"{a:.2f} {b:.2f}\n")
    return fr, t


if __name__ == "__main__":
    write_house_curve()
    fit = next(e for e in ens if abs(e["vb_l"] - 2.7) < .01)
    rows = []
    for mass, S, F0, FC, N, CAP in itertools.product((8, 9, 11), (3, 4, 5, 6), (85, 100, 150), (50, 55, 60), (4, 8), (6.0, 8.0)):
        rows.append(evaluate(fit, mass, S, FC, N, CAP, F0))
    slim = [{k: v for k, v in r.items() if k not in ("result", "eq_db")} for r in rows]
    json.dump(slim, open("bass_target_study.json", "w"), indent=1, default=float)
    print("Most headroom with punch >= today - 0.5 dB and |warmth| <= 0.75 dB:")
    ok = [r for r in slim if r["punch"] >= -0.5 and abs(r["warmth"]) <= 0.75]
    for r in sorted(ok, key=lambda r: -r["headroom"])[:10]:
        print(f"  {r['mass']:2d} g  shelf +{r['shelf']} dB @ {r['shelf_hz']} Hz  -3 dB @ {r['fc']} Hz (order {r['order']})  cap +{r['cap']:.0f} | headroom {r['headroom']:+.1f}  punch {r['punch']:+.1f}  warmth {r['warmth']:+.1f}  deep {r['deep']:+.1f}  ({r['limit']})")
    print("\nRecommended target across all five LF fits:")
    for mass in (7, 8, 9, 10, 11):
        rs = [evaluate(e, mass, 4.0, 55, 8, 8.0, 100.0) for e in ens]
        h = [r["headroom"] for r in rs]
        print(f"  {mass:2d} g: headroom {min(h):+.1f}..{max(h):+.1f}  punch {np.mean([r['punch'] for r in rs]):+.1f}  warmth {np.mean([r['warmth'] for r in rs]):+.1f}  deep {np.mean([r['deep'] for r in rs]):+.1f}  limits {sorted(set(r['limit'] for r in rs))}")
