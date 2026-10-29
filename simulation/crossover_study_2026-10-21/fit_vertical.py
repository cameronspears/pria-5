"""Fit effective +/-15 deg vertical driver transfers to the multi-delay records.

Magnitude-only fit (per-record sub-sample timing jitter cancels).  At each
position the woofer and tweeter get smooth gain curves (quadratic in octaves
about 2.5 kHz) and one extra relative delay tau (woofer minus tweeter, us).
Pure geometry predicts tau = +54.5 us above and -54.5 us below.
"""
import json
import numpy as np, sys
from scipy.optimize import least_squares
sys.path.insert(0, '.')
from common import *

WIN = sys.argv[1] if len(sys.argv) > 1 else "3ms"
LO, HI = float(sys.argv[2]) if len(sys.argv) > 2 else 1200., float(sys.argv[3]) if len(sys.argv) > 3 else 6000.
f, win, nat = load_driver_set(WIN)
W = (win[0] + win[1]) / 2
T = (win[2] + win[3]) / 2
cut = rbj("peak", 3500, 3.0, f, -2.0)
g = log_grid(LO, HI, 48)
Wg, Tg, cg = (to_grid_complex(f, x, g) for x in (W, T, cut))


def sm(x):
    return smooth_complex_power(f, x, g, 12)


def meas(folder, names):
    xs = [np.load(MEAS / folder / f"{n}.npz")[WIN] for n in names]
    return 10 * np.log10(np.mean([10 ** (sm(x) / 10) for x in xs], axis=0))


POS = {
    "above": [("2026-09-30_tuning03_window", ["record_3"], 2),
              ("2026-09-30_tuning04_above", ["record_1"], 3),
              ("2026-09-30_tuning02_v15", ["above"], 4)],
    "below": [("2026-09-30_tuning03_below", ["trial_1", "trial_2"], 2),
              ("2026-09-30_tuning02_v15", ["below"], 4)],
}
x = np.log2(g / 2500)


def model(p, d):
    cw0, cw1, cw2, ct0, ct1, ct2, tau = p
    aw = 10 ** ((cw0 + cw1 * x + cw2 * x * x) / 20) * np.exp(-2j * np.pi * g * tau * 1e-6)
    at = 10 ** ((ct0 + ct1 * x + ct2 * x * x) / 20)
    # smooth on the fly: model is evaluated on the log grid then compared with
    # 1/12-oct smoothed data; the model is smooth enough that this is fair.
    return 20 * np.log10(np.abs(aw * Wg + at * Tg * cg * np.exp(-2j * np.pi * g * d / FS)))


results = {}
for pos, recs in POS.items():
    data = [(meas(folder, names), d) for folder, names, d in recs]

    def resid(p):
        return np.concatenate([model(p, d) - m for m, d in data])

    best = None
    for tau0 in np.arange(-150, 151, 15):
        r = least_squares(resid, [0, 0, 0, 0, 0, 0, tau0])
        if best is None or r.cost < best.cost:
            best = r
    p = best.x
    rms = float(np.sqrt(np.mean(best.fun ** 2)))
    geo = 54.5 if pos == "above" else -54.5
    # fit with tau pinned to geometry for comparison
    r_geo = least_squares(lambda q: resid(np.r_[q, geo]), p[:6])
    rms_geo = float(np.sqrt(np.mean(r_geo.fun ** 2)))
    results[pos] = dict(params=p.tolist(), rms_db=rms, tau_us=float(p[6]),
                        rms_db_tau_geometry=rms_geo, geometry_tau_us=geo)
    print(f"{pos}: tau {p[6]:+.1f} us (geometry {geo:+.1f}); fit RMS {rms:.2f} dB vs {rms_geo:.2f} dB with geometric tau")
    for hz in (1500, 2000, 2500, 3000, 4000, 5000):
        xx = np.log2(hz / 2500)
        print(f"   {hz}: woofer {p[0]+p[1]*xx+p[2]*xx*xx:+.1f} dB  tweeter {p[3]+p[4]*xx+p[5]*xx*xx:+.1f} dB")
json.dump(results, open(f"vertical_fit_{WIN}.json", "w"), indent=1)
