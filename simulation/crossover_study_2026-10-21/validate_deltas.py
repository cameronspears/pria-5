"""Does the geometric model predict the MEASURED change between delay states
at a fixed off-axis position?  (Position-specific effects cancel in deltas.)"""
import json
import numpy as np, sys
sys.path.insert(0, '.')
from common import *
from geometry import *

WIN = sys.argv[1] if len(sys.argv) > 1 else "3ms"
f, win, nat = load_driver_set(WIN)
W = (win[0] + win[1]) / 2
T = (win[2] + win[3]) / 2
cut = rbj("peak", 3500, 3.0, f, -2.0)
g = log_grid(1000, 8000, 24)


def sm(x):
    return smooth_complex_power(f, x, g, 12)


def meas(folder, names):
    xs = [np.load(MEAS / folder / f"{n}.npz")[WIN] for n in names]
    return 10 * np.log10(np.mean([10 ** (sm(x) / 10) for x in xs], axis=0))


AX = mic_position(0, 0)
UP = np.array([0, Y_MID + 259, 966.])
DN = np.array([0, Y_MID - 259, 966.])


def pred(mic, d):
    pw, pt = predict(f, W, T * cut * delay(d, f), mic, AX)
    return sm(pw + pt)


pairs = [
    ("above d3-d2 (same mic)", UP, ("2026-09-30_tuning04_above", ["record_1"], 3), ("2026-09-30_tuning03_window", ["record_3"], 2)),
    ("above d4-d2", UP, ("2026-09-30_tuning02_v15", ["above"], 4), ("2026-09-30_tuning03_window", ["record_3"], 2)),
    ("below d4-d2", DN, ("2026-09-30_tuning02_v15", ["below"], 4), ("2026-09-30_tuning03_below", ["trial_1", "trial_2"], 2)),
    ("axis d4-d2", AX, ("2026-09-30_tuning02", ["trial_1", "trial_2"], 4), ("2026-09-30_tuning03_window", ["record_1", "record_2"], 2)),
]
out = {}
print("Hz     " + " ".join(f"{p[0]:>24s}" for p in pairs))
rows = []
for name, mic, a, b in pairs:
    md = meas(a[0], a[1]) - meas(b[0], b[1])
    pdlt = pred(mic, a[2]) - pred(mic, b[2])
    rows.append((md, pdlt))
    band = (g >= 1500) & (g <= 5000)
    e = (md - pdlt)[band]
    out[name] = dict(median_abs_err_db=float(np.median(abs(e))), max_abs_err_db=float(abs(e).max()),
                     corr=float(np.corrcoef(md[band], pdlt[band])[0, 1]))
for i in range(0, len(g), 4):
    print(f"{g[i]:6.0f} " + " ".join(f"{m[i]:+11.1f}/{p[i]:+6.1f}      " for m, p in rows))
print(json.dumps(out, indent=1))
