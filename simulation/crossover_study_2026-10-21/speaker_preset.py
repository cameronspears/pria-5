"""Room-independent SPEAKER preset: correct the speaker, not the room.

Target (anechoic, listening window): flat from ~120 Hz to 12 kHz; bass rolls
off with an 8th-order Butterworth at 55 Hz (same alignment as the house-curve
work).  The speaker therefore gets full baffle-step compensation; placement
(desk / wall / free) is a separate optional one-filter layer, and room
correction a separate optional cuts-only layer.

Filters: bass = high-pass pair + one broad lift (woofer bank only);
mid/treble = M peaking filters, identical in both banks.  Fitted on the
room-free model in speaker_anechoic.py.
"""
import json, sys
import numpy as np
from scipy.optimize import least_squares
from scipy.signal import butter
sys.path.insert(0, '.')
from speaker_anechoic import Speaker, GRID
from common import rbj, db

S = Speaker(8.0)


def hp8(f, fc=55.0):
    b, a = butter(8, 1.0, btype="high", analog=True)
    s = 1j * f / fc
    return db(np.polyval(b, s) / np.polyval(a, s))


TARGET = hp8(GRID)                     # 0 dB passband
SEL = (GRID >= 40) & (GRID <= 14000)
W = np.where(GRID < 50, 0.4, 1.0)


def smooth(x, frac=6, ppo=96):
    n = int(round(ppo / frac / 2))
    p = 10 ** (x / 10)
    return 10 * np.log10(np.convolve(np.pad(p, n, mode="edge"), np.ones(2 * n + 1) / (2 * n + 1), mode="valid"))


def unpack(x, m):
    bass = [("High-pass", np.exp(x[0]), x[1], 0.0), ("High-pass", np.exp(x[0]), x[2], 0.0),
            ("Peaking", np.exp(x[3]), x[4], x[5])]
    common = [("Peaking", np.exp(x[6 + 3 * i]), x[7 + 3 * i], x[8 + 3 * i]) for i in range(m)]
    return bass, common


def err(lw):
    """Deviation from target with the free overall level removed (weighted)."""
    e = smooth(lw) - TARGET
    return e - np.average(e[SEL], weights=W[SEL])


def resid(x, m):
    bass, common = unpack(x, m)
    return (err(S.response(bass, common)["lw"]) * W)[SEL]


def fit(m, seeds=6, hp_min=35.0):
    rng = np.random.default_rng(5)
    best = None
    for s in range(seeds):
        x0 = [np.log(rng.uniform(max(hp_min, 45) + 0.5, 62)), .75, .75, np.log(rng.uniform(60, 150)), rng.uniform(.5, 1.0), rng.uniform(3, 7.5)]
        lb = [np.log(hp_min), .55, .55, np.log(55), .4, 0.]      # lift never below the protective HP region
        ub = [np.log(70), 1.0, 1.0, np.log(400), 1.2, 8.]
        for i in range(m):
            x0 += [np.log(np.exp(rng.uniform(np.log(800), np.log(10000)))), rng.uniform(1, 4), rng.uniform(-4, 0)]
            lb += [np.log(300), .4, -8.]; ub += [np.log(16000), 6., 4.]
        r = least_squares(resid, x0, bounds=(lb, ub), args=(m,), max_nfev=600)
        if best is None or r.cost < best.cost:
            best = r
    bass, common = unpack(best.x, m)
    resp = S.response(bass, common)
    e = err(resp["lw"])
    off = np.average((smooth(resp["lw"]) - TARGET)[SEL], weights=W[SEL])
    ea = smooth(resp["axis"]) - TARGET - off
    band = (GRID >= 60) & (GRID <= 12000)
    return dict(m=m, bass=bass, common=common, offset=off, resp=resp,
                lw_rms=float(np.sqrt(np.mean(e[band] ** 2))), lw_range=[float(e[band].min()), float(e[band].max())],
                axis_rms=float(np.sqrt(np.mean(ea[band] ** 2))), axis_range=[float(ea[band].min()), float(ea[band].max())])


if __name__ == "__main__":
    # the speaker with NO EQ beyond the crossover, for reference
    raw = S.response([], [])
    print("level match model->measured woofer (dB):", round(raw["level_match_db"], 2))
    base = smooth(raw["lw"]) - np.median(smooth(raw["lw"])[(GRID > 300) & (GRID < 3000)])
    print("No-EQ listening window (re 300 Hz-3 kHz median):",
          {h: round(float(np.interp(np.log(h), np.log(GRID), base)), 1) for h in (40, 50, 60, 80, 100, 150, 200, 300, 500, 700, 1000, 1500, 2000, 3000, 5000, 8000, 12000)})
    results = {}
    for m in (2, 3, 4, 5):
        r = fit(m)
        results[m] = r
        print(f"\nM={m}: LW RMS {r['lw_rms']:.2f} dB ({r['lw_range'][0]:+.1f}/{r['lw_range'][1]:+.1f}), on-axis RMS {r['axis_rms']:.2f} dB, 60 Hz-12 kHz")
        for t, f0, q, g in r["bass"] + r["common"]:
            print(f"    {t:10s} {f0:8.1f} Hz  Q {q:.2f}  {g:+.1f} dB")
    json.dump({m: {k: v for k, v in r.items() if k != "resp"} for m, r in results.items()},
              open("speaker_preset_scan.json", "w"), indent=1, default=float)
