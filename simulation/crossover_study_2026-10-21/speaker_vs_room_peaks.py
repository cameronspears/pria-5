"""Is a narrow feature the speaker's or the room's?  Peak frequency/height at
every retained mic position (full window, 1/24-1/48 octave).  A feature at the
same frequency everywhere belongs to the speaker; one that wanders is room.
Result 2026-10-21: ~1.2 kHz = speaker (1.14-1.31 kHz, +4..+9 dB everywhere);
~680 Hz = room/desk (603-766 Hz); ~85 Hz dip = room (see room_dip_evidence.py).
"""
import json, sys
import numpy as np
sys.path.insert(0, '.')
from common import MEAS

RECS = [("axis 9-29", "2026-09-29_v15/axis_1_native.npz"), ("above 9-29", "2026-09-29_v15/v15_1_native.npz"),
        ("below 9-29", "2026-09-29_v15/v15_3_native.npz"), ("30L", "2026-09-29_h30/h30_1_native.npz"),
        ("30R", "2026-09-29_h30/h30_3_native.npz"), ("woofer-only 9-30", "2026-09-30_crossover_corrected/record_1.npz"),
        ("combined axis 9-30", "2026-09-30_crossover_corrected/record_5.npz"),
        ("above 9-30", "2026-09-30_tuning03_window/record_3.npz"), ("below 9-30", "2026-09-30_tuning03_below/trial_1.npz")]


def scan(lo, hi, blo, bhi, frac):
    g = lo * 2 ** (np.arange(0, int(np.log2(hi / lo) * 96) + 1) / 96)
    out = {}
    for lab, p in RECS:
        d = np.load(MEAS / p)
        f, s = d["frequency_hz"], d["spl_db"]
        y = np.array([10 * np.log10(np.mean(10 ** (s[(f >= x / 2 ** (1 / (2 * frac))) & (f <= x * 2 ** (1 / (2 * frac)))] / 10))) for x in g])
        b = (g >= blo) & (g <= bhi)
        i = np.argmax(y[b])
        base = np.median(np.r_[y[g < blo], y[g > bhi]])
        out[lab] = dict(peak_hz=round(float(g[b][i]), 0), height_db=round(float(y[b][i] - base), 1))
    return out


res = {"1.2 kHz": scan(1000, 1500, 1100, 1350, 48), "680 Hz": scan(500, 900, 600, 780, 24)}
json.dump(res, open("speaker_vs_room_peaks.json", "w"), indent=1)
for k, v in res.items():
    print(k, v)
