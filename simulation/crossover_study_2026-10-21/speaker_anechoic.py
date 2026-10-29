"""Room-free (anechoic) full-range model of the NEW build: 8 g PRs, crossover D1.

* Below ~600 Hz: fitted LF model (2.7 L fit) volume velocities.  Woofer
  radiation is shaped by the BEM baffle transfer of the real cabinet
  (bem_woofer/); PRs radiate as monopoles (omni at the frequencies where
  they matter).
* Above ~850 Hz: measured 3 ms driver data through the crossover
  (xover_model.Model, with off-axis directions added for the listening window).
* Splice: the model woofer is level-matched to the measured woofer over
  700-1200 Hz; magnitudes are cross-faded over 550-850 Hz.

Listening window here = power average of 0, +/-10 deg vertical, +/-10, +/-20
and +/-30 deg horizontal (the CTA-2034 set).
"""
import json, sys
import numpy as np
sys.path.insert(0, '.')
import xover_model as XM
from xover_model import Model
from common import rbj, db, delay, log_grid
from geometry import directivities, driver_transfer, Y_WOOFER, Y_TWEETER, Y_MID
from final_design import sections_B, realise
import fit_lf as F
from lf_model import solve

RHO = 1.204
GRID = log_grid(20, 20000, 96)
LW_DIRS = [("h", 0), ("v", 10), ("v", -10), ("h", 10), ("h", -10), ("h", 20), ("h", -20), ("h", 30), ("h", -30)]


class Speaker:
    def __init__(self, mass_g=8.0, bem_path="bem_woofer/bem_woofer_results.json"):
        ens = json.load(open("lf_ensemble.json"))
        fit = next(e for e in ens if abs(e["vb_l"] - 2.7) < .01)
        q, self.wf, self.pr, self.box = F.make(np.asarray(fit["x"]))
        self.mass = mass_g
        self.r = solve(GRID, self.wf, self.pr, self.box, mass_g, 1.0)
        w = 2 * np.pi * GRID
        self.pw4 = 1j * w * RHO * self.r["Uw"] / (4 * np.pi)
        self.pp4 = 1j * w * RHO * self.r["Up"] / (4 * np.pi)
        # BEM baffle transfer (magnitude re free-field monopole) per direction
        b = json.load(open(bem_path))
        self.bem_f = np.array([x["frequency_hz"] for x in b["results"]])
        rel = np.array([x["rel_monopole_db"] for x in b["results"]])          # (nf, ndir)
        self.bem_tags = b["tags"]
        self.bem_rel = rel
        sph = [i for i, t in enumerate(self.bem_tags) if t.startswith("s")]
        self.bem_power_db = 10 * np.log10(np.mean(10 ** (rel[:, sph] / 10), axis=1))
        # HF model with extra directions
        self.M = Model(lo=300.0, hi=20000.0)
        self._add_dirs()

    # ---------------------------------------------------------- directions
    def _measured_h(self, a_deg):
        """Horizontal tweeter directivity: waveguide FEM below 3 kHz, the
        measured 2026-09-29 +/-30 deg data above 5 kHz (where the tweeter
        dominates the sum), scaled as (angle/30)^2 for other angles.  The FEM
        overstates high-treble output off axis (+1 dB at 30 deg, 10 kHz,
        versus about -2.5 dB measured)."""
        M = self.M
        _, td = directivities()
        fem = db(td(M.g, a_deg, "horizontal"))
        m = json.load(open("measured_hf_directivity.json"))
        meas = np.interp(np.log(M.g), np.log(m["f"]), m["h30"], left=m["h30"][0], right=m["h30"][-1])
        meas = meas * (abs(a_deg) / 30.0) ** 2
        t = np.clip((np.log(M.g) - np.log(3000)) / (np.log(5000) - np.log(3000)), 0, 1)
        return 10 ** (((1 - t) * fem + t * np.minimum(meas, fem)) / 20)

    def _add_dirs(self):
        M = self.M
        wd, td = directivities()
        ax = np.array([0, Y_MID, 1000.0])
        M.dirs["h30"] = (M.dirs["h30"][0], self._measured_h(30))
        M.dirs["h60"] = (M.dirs["h60"][0], self._measured_h(60))
        for plane, a in LW_DIRS + [("h", 40), ("h", 60), ("h", 90), ("v", 20), ("v", -20), ("v", 30), ("v", -30)]:
            key = f"{plane}{a}"
            if key in M.dirs:
                continue
            t = np.radians(a)
            if plane == "h":
                mic = np.array([1000 * np.sin(t), Y_MID, 1000 * np.cos(t)])
                M.dirs[key] = (wd(M.g, min(abs(a), 45)), self._measured_h(a))
            else:
                mic = np.array([0, Y_MID + 1000 * np.sin(t), 1000 * np.cos(t)])
                gw, vw, _ = driver_transfer(M.g, Y_WOOFER, mic, ax)
                gt, vt, _ = driver_transfer(M.g, Y_TWEETER, mic, ax)
                rel = np.angle(gw / gt)
                M.dirs[key] = (wd(M.g, abs(vw)) * np.abs(gw) * np.exp(1j * XM.K_VERT * rel),
                               td(M.g, vt, "vertical") * np.abs(gt))
        M.dirs["h0"] = M.dirs["axis"]

    def _lf_taper(self, curve_db):
        """BEM sweep starts at 150 Hz; below it fade to 0 dB (omnidirectional,
        full-space radiation) by 60 Hz."""
        t = np.clip((np.log(GRID) - np.log(60)) / (np.log(self.bem_f[0]) - np.log(60)), 0, 1)
        return np.where(GRID < self.bem_f[0], curve_db * t, curve_db)

    def bem_dir_db(self, key):
        tag = {"h0": "h0"}.get(key, key)
        if tag.startswith("h") and int(tag[1:]) < 0:
            tag = f"h{-int(tag[1:])}"
        i = self.bem_tags.index(tag)
        c = np.interp(np.log(GRID), np.log(self.bem_f), self.bem_rel[:, i],
                      left=self.bem_rel[0, i], right=self.bem_rel[-1, i])
        return self._lf_taper(c)

    # ------------------------------------------------------------- response
    def response(self, bass_eq=(), common_eq=(), tweeter_eq=(), xover=None):
        """Return dict of dB curves on GRID: 'axis', 'lw', 'power_lf' + HF dirs.

        bass_eq: woofer-only rows; common_eq: rows in both banks; rows are
        (type, hz, q, gain).  xover: (lo_sections, hi_sections, t_trim, delay, pol)."""
        if xover is None:
            lo_s, hi_s = sections_B()
            rec = json.load(open("recommended_crossover.json"))
            xover = (lo_s, hi_s, rec["tweeter_trim_db"], rec["tweeter_delay_samples"], -1)
        lo_s, hi_s, ttrim, dly, pol = xover
        M = self.M

        def chain(rows, fr):
            h = np.ones_like(fr, complex)
            for t, f0, q, g in rows:
                h = h * (rbj("hp", f0, q, fr) if t.lower().startswith("high") else
                         rbj("lp", f0, q, fr) if t.lower().startswith("low") else rbj("peak", f0, q, fr, g))
            return h

        lo_hf = chain([("Low-pass", f, q, 0) for _, f, q in lo_s], M.g) * chain(bass_eq, M.g) * chain(common_eq, M.g)
        hi_hf = chain([("High-pass", f, q, 0) for _, f, q in hi_s], M.g) * chain(common_eq, M.g) * chain(tweeter_eq, M.g)
        wv, tv, out = M.responses(lo_hf, hi_hf, ttrim, dly, pol, -4)
        # LF woofer + PR (woofer chain applies to both: same electrical drive)
        hw_lf = chain([("Low-pass", f, q, 0) for _, f, q in lo_s], GRID) * chain(bass_eq, GRID) * chain(common_eq, GRID)
        # level match model woofer (with baffle) to measured woofer, 700-1200 Hz, same chain
        on_bem = 10 ** (self.bem_dir_db("h0") / 20)
        model_w = np.abs(self.pw4) * on_bem * np.abs(hw_lf) * 10 ** (-4 / 20)
        meas_w = np.interp(np.log(GRID), np.log(M.g), np.abs(wv), left=np.nan, right=np.nan)
        band = (GRID >= 700) & (GRID <= 1200)
        k = np.median(meas_w[band] / model_w[band])
        res = {}
        lw_lf_pow = 0
        for key in ["h0"] + [f"{p}{a}" for p, a in LW_DIRS[1:]]:
            b = 10 ** (self.bem_dir_db(key) / 20)
            lf = k * np.abs(self.pw4 * b + self.pp4) * np.abs(hw_lf) * 10 ** (-4 / 20)
            hf_key = "axis" if key == "h0" else key
            hf = np.interp(np.log(GRID), np.log(M.g), np.abs(out[hf_key]), left=np.nan, right=np.nan)
            xf = np.clip((np.log(GRID) - np.log(550)) / (np.log(850) - np.log(550)), 0, 1)
            comb = 10 ** ((1 - xf) * db(lf) / 20 + xf * np.nan_to_num(db(hf), nan=-200) / 20)
            res[key] = db(comb)
            lw_lf_pow = lw_lf_pow + comb ** 2
        res["axis"] = res["h0"]
        res["lw"] = 10 * np.log10(lw_lf_pow / len(LW_DIRS))
        res["level_match_db"] = float(20 * np.log10(k))
        # LF sound power (woofer band, BEM sphere) for in-room estimates
        pw_power = 10 ** (self._lf_taper(np.interp(np.log(GRID), np.log(self.bem_f), self.bem_power_db,
                                                    left=self.bem_power_db[0], right=self.bem_power_db[-1])) / 20)
        res["power_lf"] = db(k * np.abs(self.pw4 * pw_power + self.pp4) * np.abs(hw_lf) * 10 ** (-4 / 20))
        res["hf_out"] = out
        return res
