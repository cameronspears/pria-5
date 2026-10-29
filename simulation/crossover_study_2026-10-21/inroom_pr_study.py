"""Keep the in-room bass you already like; what does each PR mass cost?

Room transfer is taken from the 12-position Tuning12 average (the room and
listening positions are what they are); the speaker's change with PR mass is
the ratio of fitted LF models (mass m / 11 g).  Below ~300 Hz the source is
compact, so its room interaction does not depend on the mass, which is what
makes this ratio method sound.

For each mass the woofer EQ is re-solved so the in-room response is
IDENTICAL to today's (Tuning22 bass EQ, 2 x 50 Hz HP).  We then compare
the EQ effort and the excursion/voltage each mass needs for that same sound.
Variant B lets the protective high-pass track the new tuning (HP at 0.9 Fb):
less output below Fb, much less excursion.
"""
import json, sys
import numpy as np
sys.path.insert(0, '.')
import fit_lf as F
from lf_model import *
from common import rbj, crossover, MEAS

VMAX = 12.0
MASSES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14]
f = np.geomspace(25, 400, 500)

T22_BASS = [(58, 1.0, 7.5), (69, 5.0, -9.0), (70, 0.7, 9.0), (92, 2.0, 3.0),
            (143, 3.0, -7.5), (220, 3.5, -4.75), (350, 3.0, -1.25)]


def eq_bass(fr, hp=50.0, hp_q=0.71):
    h = rbj("hp", hp, hp_q, fr) ** 2
    for f0, q, gdb in T22_BASS:
        h = h * rbj("peak", f0, q, fr, gdb)
    return h


def room_raw():
    d = np.load(MEAS / "2026-09-30_tuning12_measured/measured.npz")
    fr, m = d["frequency_hz"], d["measured_db"]
    # 1/6-octave power smoothing onto f
    out = []
    for x in f:
        sel = (fr >= x / 2 ** (1 / 12)) & (fr <= x * 2 ** (1 / 12))
        out.append(10 * np.log10(np.mean(10 ** (m[sel] / 10))))
    meas = np.array(out)
    # T12 woofer EQ (same as T22 below 200 Hz apart from 220 Hz -5.5) + LR24 low
    t12 = [(58, 1.0, 7.5), (69, 5.0, -9.0), (70, 0.7, 9.0), (92, 2.0, 3.0),
           (143, 3.0, -7.5), (220, 3.5, -5.5), (420, 3.0, 0.5)]
    h = rbj("hp", 50, .71, f) ** 2 * crossover("LR4", 3000, f)[0]
    for f0, q, gdb in t12:
        h = h * rbj("peak", f0, q, f, gdb)
    return meas, meas - db(h)


def run():
    ens = json.load(open("lf_ensemble.json"))
    meas, raw_room = room_raw()
    eq_now = eq_bass(f)
    results = {}
    for e in ens:
        q, wf, pr, box = F.make(np.asarray(e["x"]))
        ref = solve(f, wf, pr, box, 11.0, 1.0)
        p11 = farfield(ref)
        rows = []
        for m in MASSES:
            r = solve(f, wf, pr, box, m, 1.0)
            ratio = farfield(r) / p11
            row = dict(added_g=m, fb_hz=float(r["fb"]))
            for variant in ("same_sound", "hp_tracks_fb"):
                if variant == "same_sound":
                    target = eq_now * p11                      # in-room shape kept
                else:
                    hp = 0.9 * r["fb"]
                    target = eq_bass(f, hp) * p11
                eq_m = target / farfield(r)                    # |EQ| needed
                drive = np.abs(eq_m)
                xw = r["xw"] * drive * np.sqrt(2)
                xp = r["xp"] * drive * np.sqrt(2)
                # input level (re 1 V passband) before first limit at each f
                lim = np.minimum.reduce([wf.xmax / np.maximum(xw, 1e-15),
                                         pr.xmax / np.maximum(xp, 1e-15),
                                         VMAX / np.maximum(drive, 1e-15)])
                who = np.argmax(np.vstack([xw / wf.xmax, xp / pr.xmax, drive / VMAX]), axis=0)
                band = (f >= 40) & (f <= 150)
                i = np.argmin(lim[band])
                eqdb = db(eq_m / eq_now) if variant == "same_sound" else db(eq_m)
                row[variant] = dict(
                    worst_hz=float(f[band][i]), limited_by=["ND91", "PR", "amp"][who[band][i]],
                    headroom_db=float(20 * np.log10(lim[band][i])),
                    headroom_by_band_db={f"{a}-{b}": float(20 * np.log10(lim[(f >= a) & (f < b)].min()))
                                         for a, b in ((40, 50), (50, 60), (60, 80), (80, 120))},
                    eq_change_vs_now_db={str(h): float(np.interp(h, f, db(eq_m / eq_now))) for h in (45, 50, 55, 60, 70, 80, 100)},
                    total_eq_db={str(h): float(np.interp(h, f, db(eq_m))) for h in (45, 50, 55, 60, 70, 80, 100)},
                    peak_boost_db=float(db(eq_m)[(f >= 40) & (f <= 200)].max()),
                    inroom_raw_db={str(h): float(np.interp(h, f, raw_room + db(ratio))) for h in (40, 50, 60, 70, 80, 100, 150, 200)},
                    inroom_result_db={str(h): float(np.interp(h, f, raw_room + db(ratio) + db(eq_m))) for h in (40, 45, 50, 55, 60, 70, 80, 100, 150)})
            rows.append(row)
        results[f"{e['vb_l']:.2f}"] = rows
    return results, f, meas, raw_room


if __name__ == "__main__":
    res, fr, meas, raw = run()
    json.dump(res, open("inroom_pr_study.json", "w"), indent=1)
    keys = list(res)
    for variant in ("same_sound", "hp_tracks_fb"):
        print(f"\n=== {variant} ===  headroom = how much louder before first limit (sine, 40-150 Hz), all 5 fits")
        base = {k: res[k][MASSES.index(11)][variant]["headroom_db"] for k in keys}
        for j, m in enumerate(MASSES):
            cells = [res[k][j][variant] for k in keys]
            print(f" +{m:2d} g Fb {res[keys[2]][j]['fb_hz']:5.1f} | dHeadroom vs 11 g: " +
                  " ".join(f"{c['headroom_db']-base[k]:+5.1f}{c['limited_by'][0]}@{c['worst_hz']:3.0f}" for c, k in zip(cells, keys)) +
                  f" | peak EQ boost {cells[2]['peak_boost_db']:+5.1f} dB | EQ change @55/60/70: "
                  f"{cells[2]['eq_change_vs_now_db']['55']:+5.1f}/{cells[2]['eq_change_vs_now_db']['60']:+5.1f}/{cells[2]['eq_change_vs_now_db']['70']:+5.1f}")
    print("\nIn-room raw response (no EQ, 2.7 L fit), dB:")
    for j, m in enumerate(MASSES):
        r = res[keys[2]][j]["same_sound"]["inroom_raw_db"]
        print(f" +{m:2d} g " + " ".join(f"{h}:{v:5.1f}" for h, v in r.items()))
