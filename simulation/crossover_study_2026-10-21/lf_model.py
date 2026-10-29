"""Lumped woofer + twin passive radiator + box model, fitted to measured nearfields.

Physics (SI, outward-positive displacements, N identical PRs moving together):
  electrical : V = (Re + jw Le) i + Bl v_w
  woofer     : Zw v_w = Bl i - Sd p_b
  each PR    : Zp v_p = - Sp p_b
  box        : p_b = (Sd v_w + N Sp v_p) / (jw Cab + 1/Ral)     (Cab = Vb / rho c^2)
Radiated volume velocity U = Sd v_w + N Sp v_p.  Far field (4 pi) pressure
p = j w rho U / (4 pi r).  Keele nearfield: p_nf = j w rho u (sqrt(a^2+z^2) - z).
"""
from __future__ import annotations

from dataclasses import dataclass, replace, asdict
import numpy as np
from common import MEAS, rbj, crossover, db

RHO, C = 1.204, 343.0
P_REF = 20e-6


@dataclass(frozen=True)
class Woofer:            # ND91-4 datasheet
    re: float = 4.3
    le: float = 0.83e-3
    mms: float = 4.8e-3
    cms: float = 0.96e-3
    rms: float = 2 * np.pi * 74.0 * 4.8e-3 / 4.24
    bl: float = 4.59
    sd: float = 30.4e-4
    xmax: float = 4.6e-3


@dataclass(frozen=True)
class Radiator:          # DS115-PR datasheet (no added mass)
    mms: float = 13.0e-3
    cms: float = 2.27e-3
    rms: float = 0.7
    sd: float = 54.1e-4
    xmax: float = 6.0e-3


@dataclass(frozen=True)
class Box:
    vb: float = 2.57e-3          # m^3 (nominal CAD estimate, unmeasured)
    ql: float = 15.0             # leakage Q at the PR tuning (large = tight)
    n_pr: int = 2


def solve(f, wf: Woofer, pr: Radiator, box: Box, added_g: float, volts=1.0, h=None):
    f = np.asarray(f, float)
    w = 2 * np.pi * f
    s = 1j * w
    mp = pr.mms + added_g * 1e-3
    zw = wf.rms + s * wf.mms + 1 / (s * wf.cms)
    zp = pr.rms + s * mp + 1 / (s * pr.cms)
    cab = box.vb / (RHO * C ** 2)
    fb = np.sqrt((1 / pr.cms + box.n_pr * pr.sd ** 2 / cab) / mp) / (2 * np.pi)
    ral = box.ql / (2 * np.pi * fb * cab)           # leak resistance (acoustic)
    yb = s * cab + 1 / ral                           # box admittance
    # PR velocity from box pressure: v_p = -Sp p_b / Zp
    # p_b = (Sd v_w + N Sp v_p)/yb  ->  p_b (yb + N Sp^2/Zp) = Sd v_w
    ya = yb + box.n_pr * pr.sd ** 2 / zp
    # woofer: Zw v_w = Bl i - Sd^2 v_w / ya
    zload = wf.sd ** 2 / ya
    ze = wf.re + s * wf.le
    v_in = volts * (np.ones_like(f, complex) if h is None else h)
    i = v_in / (ze + wf.bl ** 2 / (zw + zload))
    vw = wf.bl * i / (zw + zload)
    pb = wf.sd * vw / ya
    vp = -pr.sd * pb / zp
    U = wf.sd * vw + box.n_pr * pr.sd * vp
    return dict(f=f, vw=vw, vp=vp, i=i, U=U, Uw=wf.sd * vw, Up=box.n_pr * pr.sd * vp,
                z=v_in / i, xw=np.abs(vw / s), xp=np.abs(vp / s), pb=pb, fb=fb)


def farfield(res, r=1.0):
    return 1j * 2 * np.pi * res["f"] * RHO * res["U"] / (4 * np.pi * r)


def nearfield(res, which, wf, pr, z=0.005):
    w = 2 * np.pi * res["f"]
    if which == "woofer":
        a = np.sqrt(wf.sd / np.pi)
        return 1j * w * RHO * res["vw"] * (np.sqrt(a * a + z * z) - z)
    a = np.sqrt(pr.sd / np.pi)
    return 1j * w * RHO * res["vp"] * (np.sqrt(a * a + z * z) - z)


def dsp_chain_bass(f):
    """Woofer chain during the 2026-09-29 nearfields: 2 x RBJ HP 50 Hz Q .71,
    3 kHz LR24 low, -4 dB (absolute gain is fitted separately)."""
    return rbj("hp", 50, .71, f) ** 2 * crossover("LR4", 3000, f)[0]


def load_nearfields():
    folder = MEAS / "2026-09-29_bass_20_500"
    out = {}
    for i, name in ((1, "pr_right"), (2, "pr_left"), (3, "woofer")):
        a = np.genfromtxt(folder / f"recording_{i}_native.csv", delimiter=",", names=True)
        n = np.genfromtxt(folder / f"recording_{i}_noise.csv", delimiter=",", names=True)
        f = a["frequency_hz"]
        p = 10 ** (a["nearfield_spl_db"] / 20) * P_REF * np.exp(1j * np.deg2rad(a["phase_degrees"]))
        nf = np.interp(f, n[n.dtype.names[0]], n[n.dtype.names[1]])
        out[name] = (f, p, a["nearfield_spl_db"] - nf)
    return out
