"""Fit one 'effective vertical path' factor k to the measured off-axis records.

k scales the geometric woofer-tweeter path difference change between the
axis mic and an off-axis mic.  k = 1 is pure geometry.  Fitted on absolute
1.5-5 kHz magnitudes of all five +/-15 deg records (one free broadband level
per position to absorb mic placement), and cross-checked on the deltas.
"""
import json
import numpy as np, sys
from scipy.optimize import minimize_scalar
sys.path.insert(0, '.')
from common import *
from geometry import *

WIN = sys.argv[1] if len(sys.argv) > 1 else "3ms"
f, win, nat = load_driver_set(WIN)
W = (win[0] + win[1]) / 2
T = (win[2] + win[3]) / 2
cut = rbj("peak", 3500, 3.0, f, -2.0)
g = log_grid(1500, 5000, 48)


def sm(x):
    return smooth_complex_power(f, x, g, 12)


def meas(folder, names):
    xs = [np.load(MEAS / folder / f"{n}.npz")[WIN] for n in names]
    return 10 * np.log10(np.mean([10 ** (sm(x) / 10) for x in xs], axis=0))


AX = mic_position(0, 0)
UP = np.array([0, Y_MID + 259, 966.])
DN = np.array([0, Y_MID - 259, 966.])
RECS = {
    "above": (UP, [("2026-09-30_tuning03_window", ["record_3"], 2),
                   ("2026-09-30_tuning04_above", ["record_1"], 3),
                   ("2026-09-30_tuning02_v15", ["above"], 4)]),
    "below": (DN, [("2026-09-30_tuning03_below", ["trial_1", "trial_2"], 2),
                   ("2026-09-30_tuning02_v15", ["below"], 4)]),
}
DATA = {p: (mic, [(meas(a, b), d) for a, b, d in recs]) for p, (mic, recs) in RECS.items()}


def scaled_predict(mic, d, k):
    wd, td = directivities()
    gw, vw, _ = driver_transfer(f, Y_WOOFER, mic, AX)
    gt, vt, _ = driver_transfer(f, Y_TWEETER, mic, AX)
    # relative phase between drivers scaled by k (common phase irrelevant)
    rel = np.angle(gw / gt)
    gw2 = np.abs(gw) * np.exp(1j * k * rel)
    return sm(W * wd(f, abs(vw)) * gw2 + T * cut * delay(d, f) * td(f, vt, "vertical") * np.abs(gt))


def cost(k, report=False):
    err = []
    out = {}
    for p, (mic, items) in DATA.items():
        e = np.concatenate([scaled_predict(mic, d, k) - m for m, d in items])
        e = e - np.median(e)           # one free level per position
        err.append(e)
        out[p] = float(np.sqrt(np.mean(e ** 2)))
    e = np.concatenate(err)
    if report:
        return out
    return float(np.sqrt(np.mean(e ** 2)))


ks = np.arange(0.5, 4.01, 0.25)
scan = {float(k): cost(k) for k in ks}
best = minimize_scalar(cost, bounds=(0.5, 4.0), method="bounded")
res = dict(window=WIN, scan_rms_db=scan, best_k=float(best.x), best_rms_db=float(best.fun),
           per_position_rms_best=cost(best.x, True), per_position_rms_k1=cost(1.0, True))
print(json.dumps(res, indent=1))
json.dump(res, open(f"effective_spacing_{WIN}.json", "w"), indent=1)
