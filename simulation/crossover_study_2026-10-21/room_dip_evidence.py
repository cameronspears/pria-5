"""Where does the ~85 Hz dip come from?  Dip frequency and depth in every
retained measurement (1/24-octave, full room-inclusive window).

Result (2026-10-21): no dip in the 5 mm woofer/PR nearfields, so it is not
the speaker.  At 1 m it is 20-27 dB deep at 85-87 Hz, the same 30 deg left or
right, but shallower 26 cm above (18 dB) or below (13 dB); 11 dB in the
12-position room average.  The pattern depends on height, not on left/right,
so a boundary or room-mode cancellation tied to where the speaker sits
(floor/ceiling or the wall behind it) is the likely cause.
"""
import json, sys
import numpy as np
sys.path.insert(0, '.')
from common import MEAS

g = 50 * 2 ** (np.arange(0, int(np.log2(250 / 50) * 48) + 1) / 48)


def sm(f, s, frac=24):
    out = []
    for x in g:
        sel = (f >= x / 2 ** (1 / (2 * frac))) & (f <= x * 2 ** (1 / (2 * frac)))
        out.append(10 * np.log10(np.mean(10 ** (s[sel] / 10))) if sel.any() else np.nan)
    return np.array(out)


def dip(f, s):
    y = sm(f, s)
    b = (g >= 70) & (g <= 105)
    i = np.argmin(y[b]); fd, yd = g[b][i], y[b][i]
    lo = np.nanmax(y[(g >= 60) & (g < fd)]); hi = np.nanmax(y[(g > fd) & (g <= 130)])
    return dict(dip_hz=round(float(fd), 1), depth_db=round(float(yd - min(lo, hi)), 1))


REC = [("1 m on-axis, 2026-09-29 #1", "2026-09-29_v15/axis_1_native.npz"),
       ("1 m on-axis, 2026-09-29 #2", "2026-09-29_v15/axis_2_native.npz"),
       ("+15 deg (26 cm above)", "2026-09-29_v15/v15_1_native.npz"),
       ("-15 deg (26 cm below)", "2026-09-29_v15/v15_3_native.npz"),
       ("30 deg left", "2026-09-29_h30/h30_1_native.npz"),
       ("30 deg right", "2026-09-29_h30/h30_3_native.npz"),
       ("1 m on-axis, 2026-09-30 combined", "2026-09-30_crossover_corrected/record_5.npz"),
       ("1 m on-axis, 2026-09-30 woofer only", "2026-09-30_crossover_corrected/record_1.npz"),
       ("26 cm above, 2026-09-30", "2026-09-30_tuning03_window/record_3.npz"),
       ("26 cm below, 2026-09-30", "2026-09-30_tuning03_below/trial_1.npz")]
out = {}
for lab, p in REC:
    d = np.load(MEAS / p)
    out[lab] = dip(d["frequency_hz"], d["spl_db"])
for lab, p in (("woofer nearfield 5 mm", "2026-09-29_bass_20_500/recording_3_native.csv"),
               ("PR nearfield 5 mm", "2026-09-29_bass_20_500/recording_1_native.csv")):
    a = np.genfromtxt(MEAS / p, delimiter=",", names=True)
    out[lab] = dip(a["frequency_hz"], a["nearfield_spl_db"])
d = np.load(MEAS / "2026-09-30_tuning12_measured/measured.npz")
out["12-position room average (Tuning12)"] = dip(d["frequency_hz"], d["measured_db"])
json.dump(out, open("room_dip_evidence.json", "w"), indent=1)
for k, v in out.items():
    print(f"{k:40s} {v['dip_hz']:6.1f} Hz  {v['depth_db']:6.1f} dB")
