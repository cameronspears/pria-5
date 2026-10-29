"""Off-axis model: measured on-axis complex driver data + geometry + directivity.

Positions are the locked V5.2 baffle coordinates (mm): ND91 centre Y81,
OT19 centre Y153.2286 (72.2286 mm centre spacing), both on the baffle
centreline.  Driver depth offsets are already inside the measured on-axis
phase; at the angles used here their second-order effect is < 1 us.
"""
from __future__ import annotations

import json
import numpy as np
from common import HERE, C_SOUND, smooth_complex_power

Y_WOOFER = 81.0
Y_TWEETER = 153.2286
Y_MID = (Y_WOOFER + Y_TWEETER) / 2


def _read_frd(path):
    rows = [l.split() for l in open(path) if l.strip() and l[0] not in "*#;\""]
    a = np.array([[float(x) for x in r[:3]] for r in rows])
    return a[:, 0], a[:, 1], a[:, 2]


class WooferDirectivity:
    """ND91-4 manufacturer horizontal FRDs (0/15/30/45), magnitude relative to 0."""

    def __init__(self):
        ref = HERE / "reference"
        f0, m0, _ = _read_frd(ref / "ND91-4_hor_deg+000.frd")
        self.f = f0
        self.angles = [0.0, 15.0, 30.0, 45.0]
        rel = [np.zeros_like(m0)]
        for a in (15, 30, 45):
            fp, mp, _ = _read_frd(ref / f"ND91-4_hor_deg+{a:03d}.frd")
            fn, mn, _ = _read_frd(ref / f"ND91-4_hor_deg-{a:03d}.frd")
            m = 10 * np.log10((10 ** (np.interp(f0, fp, mp) / 10)
                               + 10 ** (np.interp(f0, fn, mn) / 10)) / 2)
            r = m - m0
            # 1/6-octave smoothing of the relative curve; below 300 Hz the
            # manufacturer data include a nearfield splice: force 0 dB there.
            k = np.array([np.mean(r[(f0 > f / 2 ** (1 / 12)) & (f0 < f * 2 ** (1 / 12))]) for f in f0])
            k[f0 < 300] = 0.0
            rel.append(np.minimum(k, 1.0))
        self.rel_db = np.array(rel)  # (angle, freq)

    def __call__(self, f, angle_deg):
        a = min(abs(angle_deg), 45.0)
        per_angle = np.array([np.interp(np.log(f), np.log(self.f), r) for r in self.rel_db])
        return 10 ** (np.array([np.interp(a, self.angles, per_angle[:, i])
                                 for i in range(len(f))]) / 20)


class TweeterDirectivity:
    """V5.2 98x50x16 waveguide FEM sections (1.6-10 kHz), held outside."""

    def __init__(self):
        raw = json.loads((HERE / "reference/v5_2_smooth_close_coupled_ellipse_98x50x16.json").read_text())
        self.f = np.asarray(raw["frequencies_hz"])
        self.sec = {p: (np.asarray(raw["sections"][p]["angles_deg"]),
                        np.asarray(raw["sections"][p]["directivity_db"]))
                    for p in ("horizontal", "vertical")}

    def __call__(self, f, angle_deg, plane):
        ang, d = self.sec[plane]
        a = min(abs(angle_deg), ang[-1])
        per_f = np.array([np.interp(a, ang, row) for row in d])
        lf = np.clip(np.log(f), np.log(self.f[0]), np.log(self.f[-1]))
        out = np.interp(lf, np.log(self.f), per_f)
        out[f < self.f[0]] *= np.clip((np.log(f[f < self.f[0]]) - np.log(400)) / (np.log(self.f[0]) - np.log(400)), 0, 1)
        return 10 ** (out / 20)


WD = None
TD = None


def directivities():
    global WD, TD
    if WD is None:
        WD, TD = WooferDirectivity(), TweeterDirectivity()
    return WD, TD


def mic_position(vertical_deg=0.0, horizontal_deg=0.0, radius_mm=1000.0):
    """Mic aimed at the baffle midpoint on a sphere of ``radius_mm``."""
    v, h = np.radians(vertical_deg), np.radians(horizontal_deg)
    return np.array([radius_mm * np.cos(v) * np.sin(h),
                     Y_MID + radius_mm * np.sin(v),
                     radius_mm * np.cos(v) * np.cos(h)])


def driver_transfer(f, y_driver, mic, ref_mic):
    """Path-length phase/level change from the reference mic to ``mic``."""
    src = np.array([0.0, y_driver, 0.0])
    r = np.linalg.norm(mic - src)
    r0 = np.linalg.norm(ref_mic - src)
    d = mic - src
    vert = np.degrees(np.arctan2(d[1], np.hypot(d[0], d[2])))
    horiz = np.degrees(np.arctan2(d[0], d[2]))
    g = (r0 / r) * np.exp(-2j * np.pi * f * (r - r0) / 1000.0 / C_SOUND)
    return g, vert, horiz


def predict(f, w_axis, t_axis, mic, ref_mic=None):
    """Complex sum at ``mic`` from on-axis (ref_mic) complex driver data."""
    if ref_mic is None:
        ref_mic = mic_position(0, 0)
    wd, td = directivities()
    gw, vw, hw = driver_transfer(f, Y_WOOFER, mic, ref_mic)
    gt, vt, ht = driver_transfer(f, Y_TWEETER, mic, ref_mic)
    aw = np.hypot(vw, hw)
    dw = wd(f, aw)
    if abs(vt) >= abs(ht):
        dt = td(f, vt, "vertical") * td(f, ht, "horizontal") if ht else td(f, vt, "vertical")
    else:
        dt = td(f, ht, "horizontal") * (td(f, vt, "vertical") if vt else 1.0)
    return w_axis * dw * gw, t_axis * dt * gt
