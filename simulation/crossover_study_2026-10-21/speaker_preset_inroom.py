"""What the room-independent speaker preset sounds like in the CURRENT room.

Preset: speaker_preset.fit(3, hp_min=50).  In-room prediction uses the same
room data and ratio method as predicted_dsp.py (bass: room x 8 g model;
upper: Tuning22 in-room with its EQ removed, new crossover, preset EQ).
Curves are level-matched to today at 300 Hz-1 kHz (equal midrange loudness).
Also evaluates two optional layers that are NOT room correction:
  * 'feel' voicing: a low shelf (100 Hz) of +S dB;
  * desk/near-wall placement: the opposite shelf, for rooms that add bass.
"""
import json, sys
import numpy as np
sys.path.insert(0, '.')
import speaker_preset as SP
import minimal_eq as E
from common import rbj, db
from speaker_anechoic import GRID
import bass_target_study as BT
import fit_lf as F
from lf_model import solve
from inroom_pr_study import eq_bass, f as FB
from volume_first import headroom

preset = SP.fit(3, seeds=8, hp_min=50.0)
# Plus one measured-evidence row: a narrow ~1.2 kHz peak (+4 to +9 dB) appears at
# 1.14-1.31 kHz at EVERY mic position (axis, +/-15 deg, +/-30 deg, woofer-only,
# two sessions), so it belongs to the speaker (woofer + cabinet edge), not the
# room.  The 3 ms model window is too coarse to resolve it.  (speaker_vs_room_peaks.py)
ROWS = preset["bass"] + preset["common"] + [("Peaking", 1220.0, 5.0, -4.0)]


def chain_db(rows, fr):
    h = np.ones_like(fr, complex)
    for t, f0, q, g in rows:
        h = h * (rbj("hp", f0, q, fr) if t.startswith("High") else rbj("peak", f0, q, fr, g))
    return db(h)


def shelf_db(fr, s, f0=100.0):
    return BT.low_shelf_db(fr, s, f0)


G = E.G
T22 = E.t22


def inroom(rows, extra_shelf=0.0):
    bass_lo = E.third(E.room8 + chain_db(rows, FB) + shelf_db(FB, extra_shelf), FB)
    up = E.noeq_new + chain_db([r for r in rows if r[0] == "Peaking" and r[1] > 300], G)
    lo_G = np.interp(np.log(G), np.log(FB), bass_lo, left=bass_lo[0], right=bass_lo[-1])
    w = np.clip((np.log(450) - np.log(G)) / (np.log(450) - np.log(250)), 0, 1)
    y = 10 * np.log10(w * 10 ** (lo_G / 10) + (1 - w) * 10 ** (up / 10))
    mid = (G >= 300) & (G <= 1000)
    return y - np.median(y[mid]) + np.median(T22[mid])


def head(rows, extra_shelf=0.0):
    ens = json.load(open("lf_ensemble.json"))
    eqv = 10 ** ((chain_db(rows, FB) + shelf_db(FB, extra_shelf)) / 20)
    mid_new = chain_db(rows, np.array([500.0]))[0]
    t22rows = [("Peaking", 350, 3, -1.25), ("Peaking", 680, 3, -3.75), ("Peaking", 1220, 6, -4), ("Peaking", 1690, 1.9, -3),
               ("Peaking", 3300, 3.2, -2), ("Peaking", 5200, 1.1, -4), ("Peaking", 10000, .5, -2.5)]
    mid_today = db(eq_bass(np.array([500.0])))[0] + chain_db(t22rows, np.array([500.0]))[0]
    out = []
    for e in ens:
        q, wf, pr, box = F.make(np.asarray(e["x"]))
        a11 = solve(FB, wf, pr, box, 11.0, 1.0); a8 = solve(FB, wf, pr, box, 8.0, 1.0)
        h0, _, _ = headroom(a11, np.abs(eq_bass(FB)), wf, pr)
        h1, _, _ = headroom(a8, eqv, wf, pr)
        out.append(h1 - h0 + (mid_new - mid_today))
    return min(out), max(out)


if __name__ == "__main__":
    print("Preset rows:")
    for r in ROWS:
        print(f"   {r[0]:10s} {r[1]:8.1f} Hz Q {r[2]:.2f} {r[3]:+.1f}")
    res = {}
    for s in (-3.0, 0.0, 3.0, 4.0, 5.0, 6.0):
        y = inroom(ROWS, s)
        lv = {str(h): round(float(np.interp(np.log(h), np.log(G), y - T22)), 1) for h in (45, 50, 55, 60, 70, 85, 100, 150, 200, 500, 1000, 2000, 3000, 5000, 10000, 15000)}
        hr = head(ROWS, s)
        res[s] = dict(vs_today_db=lv, headroom=hr)
        print(f"\n'feel' shelf +{s:.0f} dB @100 Hz: headroom vs today {hr[0]:+.1f}..{hr[1]:+.1f} dB (equal midrange loudness)")
        print("   in-room vs today:", lv)
    json.dump(dict(rows=ROWS, lw_rms=preset["lw_rms"], lw_range=preset["lw_range"], axis_rms=preset["axis_rms"],
                   feel_options={str(k): v for k, v in res.items()}), open("speaker_preset.json", "w"), indent=1, default=float)
