"""Fast crossover evaluator on a 1/96-octave log grid.

All candidate responses are built from the measured raw driver data
(drivers.py), so every driver irregularity, the tweeter capacitor and the
real acoustic offsets are included.  Off-axis directions use geometry.py with
the empirically fitted vertical path factor K_VERT (fit_effective_spacing.py).
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfreqz
from common import *
from drivers import raw_drivers, tweeter_excursion_m, XMAX_TWEETER_M
from geometry import (directivities, driver_transfer, mic_position,
                      Y_WOOFER, Y_TWEETER, Y_MID)

K_VERT = 2.0          # fitted effective vertical path factor (3 ms and 5 ms fits)
P_REF = 20e-6
PPO = 96


class Model:
    def __init__(self, window="3ms", lo=300.0, hi=20000.0):
        f, Wr, Tr, self.info = raw_drivers(window)
        self.g = log_grid(lo, hi, PPO)
        self.W = to_grid_complex(f, Wr, self.g)
        self.T = to_grid_complex(f, Tr, self.g)
        wd, td = directivities()
        ax = mic_position(0, 0)
        self.dirs = {}
        g = self.g
        # vertical +/-15 deg (empirical K_VERT scaling of relative phase)
        for name, sgn in (("v+15", 1), ("v-15", -1)):
            mic = np.array([0, Y_MID + sgn * 259.0, 966.0])
            gw, vw, _ = driver_transfer(g, Y_WOOFER, mic, ax)
            gt, vt, _ = driver_transfer(g, Y_TWEETER, mic, ax)
            rel = np.angle(gw / gt)
            aw = wd(g, abs(vw)) * np.abs(gw) * np.exp(1j * K_VERT * rel)
            at = td(g, vt, "vertical") * np.abs(gt)
            self.dirs[name] = (aw, at)
        for name, h in (("h30", 30.0), ("h60", 60.0)):
            self.dirs[name] = (wd(g, min(h, 45.0)) * (1.0 if h < 45 else 10 ** (-3 / 20)),
                               td(g, h, "horizontal"))
        self.dirs["axis"] = (np.ones_like(g), np.ones_like(g))
        self.band = lambda lo, hi: (self.g >= lo) & (self.g <= hi)

    # ---------------------------------------------------------------- filters
    def filters(self, kind, fc, extra_lo=(), extra_hi=()):
        """Electrical low/high transfers on the grid.

        ``extra_*``: iterables of (type, f0, q[, gain]) RBJ sections appended
        to the respective branch (custom / asymmetric slopes).
        """
        lo, hi = crossover(kind, fc, self.g)
        for sec in extra_lo:
            lo = lo * rbj(sec[0], sec[1], sec[2], self.g, *(sec[3:] or ()))
        for sec in extra_hi:
            hi = hi * rbj(sec[0], sec[1], sec[2], self.g, *(sec[3:] or ()))
        return lo, hi

    def responses(self, lo, hi, t_gain_db, t_delay, polarity=1, w_gain_db=0.0,
                  eq=None):
        wv = self.W * lo * 10 ** (w_gain_db / 20)
        tv = self.T * hi * polarity * 10 ** (t_gain_db / 20) * delay(t_delay, self.g)
        if t_delay < 0:  # negative = delay the woofer instead
            tv = self.T * hi * polarity * 10 ** (t_gain_db / 20)
            wv = wv * delay(-t_delay, self.g)
        if eq is not None:
            wv, tv = wv * eq, tv * eq
        out = {k: aw * wv + at * tv for k, (aw, at) in self.dirs.items()}
        return wv, tv, out

    # --------------------------------------------------------------- metrics
    def smooth(self, x_db, frac=6):
        n = int(round(PPO / frac / 2))
        p = 10 ** (x_db / 10)
        k = np.ones(2 * n + 1) / (2 * n + 1)
        return 10 * np.log10(np.convolve(np.pad(p, n, mode="edge"), k, mode="valid"))

    def spl(self, x):
        return db(x)

    def listening_window(self, out):
        keys = ("axis", "v+15", "v-15", "h30")
        p = np.mean([np.abs(out[k]) ** 2 for k in keys], axis=0)
        return 10 * np.log10(p)

    def power_proxy(self, out):
        keys = ("axis", "v+15", "v-15", "h30", "h60")
        w = np.array([1, 1, 1, 2, 2], float)
        p = np.sum([wi * np.abs(out[k]) ** 2 for wi, k in zip(w, keys)], axis=0) / w.sum()
        return 10 * np.log10(p)

    def flat_dev(self, x_db, lo=1000, hi=10000, frac=6):
        s = self.smooth(x_db, frac)
        b = self.band(lo, hi)
        e = s[b] - np.mean(s[b])
        return float(np.sqrt(np.mean(e ** 2))), float(np.ptp(e))

    def tweeter_limit_db(self, tv, total_axis):
        """System on-axis sine SPL at 1 m (current measurement scale offset
        removed: returns dB re the sum) at which the tweeter reaches Xmax."""
        p_t = np.abs(tv) * P_REF                      # Pa rms per measured dB
        x = tweeter_excursion_m(self.g, p_t)
        s = self.smooth(db(total_axis), 6)
        margin = s + 20 * np.log10(XMAX_TWEETER_M / np.maximum(x, 1e-15))
        b = self.band(300, 20000)
        i = np.argmin(margin[b])
        return float(margin[b][i]), float(self.g[b][i])

    def evaluate(self, lo, hi, t_gain_db, t_delay, polarity=1, eq=None, w_gain_db=0.0):
        wv, tv, out = self.responses(lo, hi, t_gain_db, t_delay, polarity, w_gain_db, eq)
        ax = db(out["axis"])
        lw = self.listening_window(out)
        on_rms, on_ptp = self.flat_dev(ax)
        lw_rms, lw_ptp = self.flat_dev(lw)
        b = self.band(1500, 5000)
        sa = self.smooth(ax, 6)
        vu = self.smooth(db(out["v+15"]), 6) - sa
        vd = self.smooth(db(out["v-15"]), 6) - sa
        vert_rms = float(np.sqrt(np.mean(np.r_[vu[b], vd[b]] ** 2)))
        vert_min = float(min(vu[b].min(), vd[b].min()))
        tlim, tlim_f = self.tweeter_limit_db(tv, out["axis"])
        # acoustic crossover point (|W| = |T| on axis)
        d = db(wv) - db(tv)
        bb = self.band(800, 8000)
        idx = np.flatnonzero(np.diff(np.sign(d[bb])))
        xo = float(self.g[bb][idx[0]]) if len(idx) else float("nan")
        return dict(on_rms=on_rms, on_ptp=on_ptp, lw_rms=lw_rms, lw_ptp=lw_ptp,
                    vert_rms=vert_rms, vert_min=vert_min, tweeter_limit=tlim,
                    tweeter_limit_hz=tlim_f, acoustic_xo_hz=xo)


def score(m):
    return 0.35 * m["on_rms"] + 0.45 * m["lw_rms"] + 0.20 * m["vert_rms"]
