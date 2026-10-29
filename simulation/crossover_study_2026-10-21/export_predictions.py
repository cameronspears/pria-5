"""Write the predictions that the next measurements will be checked against."""
import csv, json, sys
import numpy as np
sys.path.insert(0, '.')
from xover_model import *
from final_design import sections_B, realise
import fit_lf as F
from lf_model import solve, nearfield, dsp_chain_bass, P_REF

M = Model()
rec = json.load(open("recommended_crossover.json"))
loB, hiB = realise(M, sections_B()[0]), realise(M, sections_B()[1])
loT, hiT = M.filters("LR4", 3000)
cols, data = ["frequency_hz"], [M.g]
for name, (lo, hi, tg, d, pol) in {"today": (loT, hiT, -10.0, 3, 1),
                                    "recommended": (loB, hiB, rec["tweeter_trim_db"], rec["tweeter_delay_samples"], -1)}.items():
    _, _, o = M.responses(lo, hi, tg, d, pol, -4)
    ref = np.mean(M.smooth(M.listening_window(o), 6)[M.band(1000, 10000)])
    for k, lab in (("axis", "onaxis"), ("v+15", "above15"), ("v-15", "below15")):
        cols.append(f"{name}_{lab}_db"); data.append(M.smooth(db(o[k]), 6) - ref)
    cols.append(f"{name}_listening_window_db"); data.append(M.smooth(M.listening_window(o), 6) - ref)
sel = (M.g >= 500) & (M.g <= 16000)
with open("predictions/crossover_3ms_1m_midpoint.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(cols)
    for i in np.flatnonzero(sel)[::2]:
        w.writerow([round(float(c[i]), 3) for c in data])

ens = json.load(open("lf_ensemble.json"))
f = np.geomspace(20, 300, 1200)
rows, peaks = {}, {}
for e in ens:
    q, wf, pr, box = F.make(np.asarray(e["x"]))
    for m in (8.0, 11.0):
        r = solve(f, wf, pr, box, m, 1.0, dsp_chain_bass(f))
        pn = db(nearfield(r, "pr", wf, pr) / P_REF)
        wn = db(nearfield(r, "woofer", wf, pr) / P_REF)
        band = (f > 40) & (f < 70)
        dip = (f > 0.9 * r["fb"]) & (f < 1.15 * r["fb"])        # local woofer minimum near Fb
        peaks.setdefault(m, []).append(dict(vb_l=round(e["vb_l"], 2), fb_hz=round(float(r["fb"]), 2),
                                            pr_peak_hz=round(float(f[band][np.argmax(pn[band])]), 2),
                                            woofer_dip_hz=round(float(f[dip][np.argmin(wn[dip])]), 2)))
        if abs(e["vb_l"] - 2.7) < .01:
            rows[f"pr_{m:.0f}g_db"] = pn
            rows[f"woofer_{m:.0f}g_db"] = wn
with open("predictions/nearfield_shapes_2p7L_fit.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["frequency_hz"] + list(rows))
    for i in range(len(f)):
        w.writerow([round(f[i], 2)] + [round(float(v[i]), 2) for v in rows.values()])

summary = dict(
    basis="2026-09-29/30 measurements of the September build; model predictions, not measurements",
    polarity_check=dict(
        how="today's preset, one on-axis sweep, 1 m at the woofer/tweeter midpoint, view with a ~3 ms window",
        same_wiring="1.5-4 kHz within about +/-2 dB of predictions/polarity_check_today_preset.csv",
        reversed_tweeter="notch about -17 dB near 2.6 kHz (about -6 dB at 3.2 kHz with a full room window)",
        if_reversed="every 'invert' instruction in this study flips"),
    pr_nearfield_8g=dict(measure="mic 5 mm from one PR cone centre, 20-500 Hz, measurement project (no EQ), same as 2026-09-29",
                         predicted=peaks[8.0], today_11g=peaks[11.0],
                         note="2026-09-29 measured with 11 g: PR peak 49.07 Hz, woofer dip 50.54 Hz (model 48.6 / 50.8)",
                         expect_pr_peak_hz_within=[50.5, 54.0]),
    crossover=dict(file="predictions/crossover_3ms_1m_midpoint.csv",
                   recommended=dict(onaxis_rms_1_10k_db=rec["metrics"]["on_rms"], lw_rms_db=rec["metrics"]["lw_rms"],
                                    acoustic_xo_hz=rec["metrics"]["acoustic_xo_hz"], tweeter_xmax_sine_db_1m=rec["metrics"]["tweeter_limit"]),
                   today=dict(onaxis_rms_1_10k_db=rec["today"]["on_rms"], lw_rms_db=rec["today"]["lw_rms"],
                              acoustic_xo_hz=rec["today"]["acoustic_xo_hz"]),
                   inroom_shift_vs_today_db=rec["predicted_inroom_shift_vs_today_db"]),
    bass_target=dict(file="Pria5_bass_target_house_curve.txt",
                     target="-0.5 dB/oct line, +4 dB low shelf at 100 Hz, 8th-order roll-off -3 dB at 55 Hz, 85 Hz fill <= +8 dB",
                     with_8g=dict(headroom_vs_today_db=[2.4, 3.2], punch_50_100_db=-0.3, warmth_120_250_db=0.6, deep_40_50_db=-9.5)),
    seal_sensitivity="a perfectly sealed box changes the bass headroom results by <= 0.1 dB (seal_sensitivity.json)")
json.dump(summary, open("predictions/predictions.json", "w"), indent=1)
print(json.dumps(summary["pr_nearfield_8g"], indent=1))
