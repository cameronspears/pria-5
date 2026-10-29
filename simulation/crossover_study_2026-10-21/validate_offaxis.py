"""Compare the off-axis model against every retained 9-30 vertical record."""
import numpy as np, sys
sys.path.insert(0, '.')
from common import *
from geometry import *

WIN = sys.argv[1] if len(sys.argv) > 1 else "3ms"
f, win, nat = load_driver_set(WIN)
W = (win[0] + win[1]) / 2
T = (win[2] + win[3]) / 2
g = log_grid(1000, 12000, 24)
cut = rbj("peak", 3500, 3.0, f, -2.0)


def sm(x):
    return smooth_complex_power(f, x, g, 12)


def meas(folder, names):
    xs = [np.load(MEAS / folder / f"{n}.npz")[WIN] for n in names]
    return 10 * np.log10(np.mean([10 ** (sm(x) / 10) for x in xs], axis=0))


AX = mic_position(0, 0)
UP = np.array([0, Y_MID + 259, 966.])
DN = np.array([0, Y_MID - 259, 966.])
cases = [
    ("axis d0+cut", "2026-09-30_tuning01", ["trial_1", "trial_2"], AX, 0),
    ("axis d4", "2026-09-30_tuning02", ["trial_1", "trial_2"], AX, 4),
    ("axis d2", "2026-09-30_tuning03_window", ["record_1", "record_2"], AX, 2),
    ("above d4", "2026-09-30_tuning02_v15", ["above"], UP, 4),
    ("above d2", "2026-09-30_tuning03_window", ["record_3"], UP, 2),
    ("above d3", "2026-09-30_tuning04_above", ["record_1"], UP, 3),
    ("below d4", "2026-09-30_tuning02_v15", ["below"], DN, 4),
    ("below d2", "2026-09-30_tuning03_below", ["trial_1", "trial_2"], DN, 2),
]
rows = {}
for name, folder, recs, mic, d in cases:
    m = meas(folder, recs)
    pw, pt = predict(f, W, T * cut * delay(d, f), mic, AX)
    p = sm(pw + pt)
    rows[name] = (m, p)
print("Hz      " + " ".join(f"{n:>14s}" for n in rows))
for i in range(0, len(g), 3):
    print(f"{g[i]:6.0f}  " + " ".join(f"{rows[n][0][i]:6.1f}/{rows[n][1][i]:6.1f}" for n in rows))
band = (g > 1500) & (g < 5000)
for n, (m, p) in rows.items():
    e = (m - p)[band]
    print(f"{n:12s} median(m-p) {np.median(e):+.2f}  spread(p95-p05) {np.percentile(e,95)-np.percentile(e,5):.2f}")
