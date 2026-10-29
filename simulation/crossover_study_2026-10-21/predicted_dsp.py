"""Complete predicted DSP settings for the new build and the response they give.

Bass rows: minimal_eq.structured_bass(3) (HP pair, one broad lift, three
room-peak cuts); mid/treble rows: minimal_eq.fit_upper(5).
Writes predictions/predicted_dsp_settings.{json,csv} and fig6_predicted_dsp.png.
These are STARTING values: the bass rows depend on room and placement and
must be re-derived from the next room average (and after the ~85 Hz placement
test); the mid/treble rows are mostly speaker-related and should hold.
"""
import csv, json, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, '.')
import minimal_eq as E
from common import rbj, db, MEAS
from final_design import sections_B, realise
from xover_model import Model

bass = E.structured_bass(3)
upper = E.fit_upper(5)
rec = json.load(open("recommended_crossover.json"))
lo_s, hi_s = sections_B()

rows = []
for t, f0, q, g in bass["rows"]:
    rows.append(dict(bank="Woofer EQ", purpose="bass (room + voicing)", type=t, hz=round(f0, 1), q=round(q, 2), gain_db=round(g, 1)))
for t, f0, q, g in sorted(upper["rows"], key=lambda r: r[1]):
    for bank in ("Woofer EQ", "Tweeter EQ"):
        rows.append(dict(bank=bank, purpose="mid/treble (identical in both banks)", type=t, hz=round(f0, 0), q=round(q, 2), gain_db=round(g, 1)))
xover_rows = [dict(bank="Woofer EQ (or crossover block LR48)", purpose="crossover", type="Low-pass", hz=f0, q=q, gain_db=0.0) for _, f0, q in lo_s] + \
             [dict(bank="Tweeter EQ (or crossover block)", purpose="crossover", type="High-pass", hz=round(f0, 0), q=q, gain_db=0.0) for _, f0, q in hi_s]
settings = dict(
    note="Predicted starting values from the 2026-10-21 study; bass rows to be re-derived after the next room average / placement test.",
    crossover=dict(rows=xover_rows, tweeter_polarity="inverted relative to the September wiring (check V1 first)",
                   tweeter_delay_samples=rec["tweeter_delay_samples"], woofer_trim_db=-4.0, tweeter_trim_db=rec["tweeter_trim_db"]),
    eq_rows=rows,
    pr_added_mass_g_each=8.0,
    counts=dict(today=dict(woofer_eq_rows=15, tweeter_eq_rows=13, unique_corrective_filters=14),
                new=dict(woofer_eq_rows=len(bass["rows"]) + len(upper["rows"]), tweeter_eq_rows=len(upper["rows"]),
                         unique_corrective_filters=len(bass["rows"]) - 2 + len(upper["rows"]),
                         plus_crossover_rows=dict(woofer=4, tweeter=2))),
    fit=dict(bass_rms_db_1_3oct=bass["rms"], bass_headroom_vs_today_db=bass["headroom"], bass_first_limit=bass["limits"],
             upper_rms_db_1_3oct=upper["rms"], upper_range_db=[upper["min"], upper["max"]]))
json.dump(settings, open("predictions/predicted_dsp_settings.json", "w"), indent=1, default=float)
with open("predictions/predicted_dsp_settings.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, ["bank", "purpose", "type", "hz", "q", "gain_db"])
    w.writeheader(); w.writerows(xover_rows + rows)

# ---------------------------------------------------- full predicted response
G, FB = E.G, E.FB
h_b = np.interp(np.log(G), np.log(FB), db(bass["h"]), left=db(bass["h"])[0], right=0.0)
h_u = upper["h"]
base_lo = np.interp(np.log(G), np.log(FB), E.room8, left=E.room8[0], right=E.room8[-1])
wlo = np.clip((np.log(450) - np.log(G)) / (np.log(450) - np.log(250)), 0, 1)
base = wlo * base_lo + (1 - wlo) * E.noeq_new
pred_fine = base + h_b + h_u
n13 = int(round(192 / 6))
pred = np.where(G < 400, 10 * np.log10(np.convolve(np.pad(10 ** (pred_fine / 10), n13, mode="edge"),
                                                    np.ones(2 * n13 + 1) / (2 * n13 + 1), mode="valid")), pred_fine)
T = E.T_u
today = E.t22
sel = (G >= 180) & (G <= 16000)
e = pred[sel] - T[sel]
summary = dict(new_vs_target_180_16k=dict(min=float(e.min()), max=float(e.max()), rms=float(np.sqrt(np.mean(e ** 2)))),
               levels_re_500={str(h): round(float(np.interp(np.log(h), np.log(G), pred) - np.interp(np.log(500), np.log(G), pred)), 1)
                              for h in (45, 50, 55, 60, 70, 85, 100, 150, 1000, 2000, 5000, 10000, 16000)})
settings["predicted_response"] = summary
json.dump(settings, open("predictions/predicted_dsp_settings.json", "w"), indent=1, default=float)
print(json.dumps({k: settings[k] for k in ("counts", "fit", "predicted_response")}, indent=1, default=float))
for r in xover_rows + rows:
    print(f"  {r['bank']:38s} {r['type']:10s} {r['hz']:8.1f} Hz  Q {r['q']:.2f}  {r['gain_db']:+5.1f} dB   ({r['purpose']})")

# --------------------------------------------------------------------- figure
SURF, INK2, GRID = "#fcfcfb", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.grid": True, "grid.color": GRID,
                     "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2,
                     "legend.frameon": False, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
fig, axs = plt.subplots(1, 2, figsize=(15, 5.4), gridspec_kw=dict(width_ratios=[1.4, 1]))
ref = np.interp(np.log(500), np.log(G), today)
show = (G >= 30) & (G <= 16000)
a = axs[0]
a.plot(G[show], T[show] - ref, color=INK2, lw=1.2, ls=(0, (4, 3)), label="target (house curve)")
a.plot(G[show], today[show] - ref, color=ORANGE, label="today: Tuning22 (28 EQ rows)")
a.plot(G[show], pred[show] - ref, color=BLUE, label=f"predicted: new build + {len(rows)} EQ rows")
a.set_xscale("log"); a.set_xlim(30, 16000); a.set_ylim(-20, 10); a.minorticks_off()
tk = [30, 40, 50, 60, 80, 100, 200, 500, 1000, 2000, 5000, 10000]
a.set_xticks(tk); a.set_xticklabels([f"{t/1000:g}k" if t >= 1000 else str(t) for t in tk])
a.set_xlabel("Frequency (Hz)"); a.set_ylabel("dB (re 500 Hz)")
a.set_title("Predicted in-room response with the proposed filters (1/3 octave)", loc="left", fontweight="semibold")
a.legend(loc="lower center")
# total EQ curves
ROWS = list(csv.DictReader(open(MEAS / "2026-10-02_tuning22_refine/sorted_eq.csv")))
fr = np.geomspace(20, 20000, 800)


def bank_db(rows_, name):
    h = np.ones_like(fr, complex)
    for r in rows_:
        if r["bank"] == name:
            f0, q, g = float(r["hz"]), float(r["q"]), float(r["gain_db"])
            h = h * (rbj("hp", f0, q, fr) if r["type"] == "High-pass" else rbj("peak", f0, q, fr, g))
    return db(h)


today_rows = [dict(bank=r["block"], type=r["type"], hz=r["frequency_hz"], q=r["q"], gain_db=r["boost_db"]) for r in ROWS]
today_w = bank_db(today_rows, "Woofer EQ")
today_t = bank_db(today_rows, "Tweeter EQ")
new_w = bank_db(rows, "Woofer EQ")
new_t = bank_db(rows, "Tweeter EQ")
b = axs[1]
b.plot(fr, today_w, color=ORANGE, label="today: woofer bank")
b.plot(fr, today_t, color=ORANGE, lw=1.2, ls=(0, (4, 2)), label="today: tweeter bank")
b.plot(fr, new_w, color=BLUE, label="predicted: woofer bank")
b.plot(fr, new_t, color=BLUE, lw=1.2, ls=(0, (4, 2)), label="predicted: tweeter bank")
b.axhline(0, color=INK2, lw=0.8)
b.set_xscale("log"); b.set_xlim(20, 20000); b.set_ylim(-30, 15); b.minorticks_off()
tk = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
b.set_xticks(tk); b.set_xticklabels([f"{t/1000:g}k" if t >= 1000 else str(t) for t in tk])
b.set_xlabel("Frequency (Hz)"); b.set_ylabel("EQ gain (dB, crossover excluded)")
b.set_title("Total EQ in each bank (excluding crossover)", loc="left", fontweight="semibold")
b.legend(loc="lower right", fontsize=8.5)
fig.tight_layout(); fig.savefig("fig6_predicted_dsp.png", dpi=150)
