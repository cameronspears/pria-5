"""Grid search: standard symmetric crossovers x frequency x delay x polarity,
with the tweeter trim optimised for each.  No EQ (raw drivers + crossover)."""
import csv, json, sys, time
import numpy as np
sys.path.insert(0, '.')
from xover_model import *

M = Model()
TYPES = ["LR2", "BW3", "LR4", "LR8"]
FCS = 1500 * 2 ** (np.arange(0, 25) / 16)        # 1.5 .. ~4.5 kHz, 1/16 oct
DELAYS = range(-4, 11)
GAINS = np.arange(-18, -5.9, 0.25)
rows = []
t0 = time.time()
for kind in TYPES:
    for fc in FCS:
        lo, hi = M.filters(kind, fc)
        for pol in (1, -1):
            for d in DELAYS:
                best = None
                for tg in GAINS:
                    m = M.evaluate(lo, hi, tg, d, pol, w_gain_db=-4)
                    s = score(m)
                    if best is None or s < best[0]:
                        best = (s, tg, m)
                s, tg, m = best
                rows.append(dict(type=kind, fc=round(float(fc), 1), polarity=pol, delay=d,
                                 t_gain=float(tg), score=s, **m))
print("evaluated", len(rows), "in", round(time.time() - t0, 1), "s")
keys = list(rows[0].keys())
with open("symmetric_search.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, keys)
    w.writeheader()
    w.writerows(rows)
# best per type/fc
best = {}
for r in rows:
    k = (r["type"], r["fc"])
    if k not in best or r["score"] < best[k]["score"]:
        best[k] = r
for kind in TYPES:
    print(kind)
    for fc in FCS:
        r = best[(kind, round(float(fc), 1))]
        print(f"  fc {fc:6.0f} pol {r['polarity']:+d} d {r['delay']:+3d} tg {r['t_gain']:6.2f} | score {r['score']:.2f} on {r['on_rms']:.2f} lw {r['lw_rms']:.2f} vert {r['vert_rms']:.2f} vmin {r['vert_min']:6.1f} | tw-limit {r['tweeter_limit']:6.1f} dB @ {r['tweeter_limit_hz']:5.0f} | acoustic xo {r['acoustic_xo_hz']:5.0f}")
