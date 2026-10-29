"""Raw (crossover-removed) complex driver responses on the measurement grid.

Source: Crossover_check2_corrected (2026-09-30), both repeats averaged, 3 ms
(default) diagnostic window, common acoustic timing reference, mic 1 m on the
woofer/tweeter midpoint axis.  The audited DSP chain at that time (2 x 50 Hz
HP, 3 kHz LR24, -4 / -10 dB trims, no EQ, no delay) is divided out.

Where the de-embedded data run into the noise floor they are replaced by a
smooth extension, cross-faded over one octave:
  * woofer above ~12 kHz -> ND91-4 manufacturer on-axis magnitude shape with
    the measured woofer's fitted excess delay (its contribution is >30 dB down
    for any crossover studied here);
  * tweeter below ~1.1 kHz -> OT19 datasheet T/S model driven through the
    33 uF series capacitor, scaled/time-aligned to the measurement at
    1.1-2 kHz (it reproduces the measured 1.1-4 kHz shape within ~1.5 dB).
"""
from __future__ import annotations

import numpy as np
from scipy.signal import freqs
from common import *

XMAX_TWEETER_M = 0.1e-3      # OT19NC00-04 datasheet
SD_TWEETER_M2 = 4.5e-4
RHO = 1.204


def _crossfade(f, a, b, f0, f1):
    """a below f0, b above f1, log cross-fade in between."""
    t = np.clip((np.log(f) - np.log(f0)) / (np.log(f1) - np.log(f0)), 0, 1)
    t = 0.5 - 0.5 * np.cos(np.pi * t)
    return a * (1 - t) + b * t


def _excess_delay(f, x, lo, hi):
    sel = (f >= lo) & (f <= hi)
    ph = np.unwrap(np.angle(x[sel]))
    slope = np.polyfit(f[sel], ph, 1)[0]
    return -slope / (2 * np.pi)


def raw_drivers(window="3ms"):
    f, win, _ = load_driver_set(window)
    W = (win[0] + win[1]) / 2
    T = (win[2] + win[3]) / 2
    wc, tc = measured_chain(f)
    Wr, Tr = W / wc, T / tc

    # --- woofer HF extension (manufacturer magnitude, measured delay)
    from geometry import _read_frd
    ff, mm, _ = _read_frd(HERE / "reference/ND91-4_hor_deg+000.frd")
    m_man = np.interp(np.log(f), np.log(ff), mm)
    sel = (f > 6000) & (f < 11000)
    off = np.median(db(Wr[sel]) - m_man[sel])
    tau = _excess_delay(f, Wr, 3000, 8000)
    ext = 10 ** ((m_man + off) / 20) * np.exp(-2j * np.pi * f * tau)
    # keep measured phase trend continuous at the splice
    i0 = np.argmin(abs(f - 11000))
    ext *= np.exp(1j * (np.angle(Wr[i0]) - np.angle(ext[i0])))
    Wr = _crossfade(f, Wr, ext, 11000, 14000)

    # --- tweeter LF extension: OT19NC00-04 T/S model with the 33 uF series
    # capacitor (matches measured within ~1.5 dB over 1.1-4 kHz), scaled and
    # time-aligned to the measured tweeter over 1.1-2 kHz.
    H = ot19_with_cap(f)
    sel = (f >= 1100) & (f <= 2000)
    ratio = Tr[sel] / H[sel]
    mag = np.exp(np.median(np.log(np.abs(ratio))))
    ph = np.unwrap(np.angle(ratio))
    slope, icpt = np.polyfit(f[sel], ph, 1)
    ext = H * mag * np.exp(1j * (icpt + slope * f))
    Tr = _crossfade(f, ext, Tr, 950, 1150)
    info = dict(woofer_manufacturer_offset_db=float(off), woofer_excess_delay_us=float(tau * 1e6),
                tweeter_extension="OT19 T/S + 33 uF model below 1.15 kHz",
                tweeter_model_scale_db=float(20 * np.log10(mag)),
                tweeter_model_excess_delay_us=float(-slope / (2 * np.pi) * 1e6))
    return f, Wr, Tr, info


OT19 = dict(re=3.17, le=0.01e-3, fs=1029.44, qms=7.03, qes=1.56, mms=0.2e-3, bl=1.64)


def ot19_with_cap(f, cap=33e-6):
    """Relative on-axis pressure (acceleration) of the OT19 driven through the
    series capacitor from a voltage source (datasheet T/S)."""
    p = OT19
    cms = 1 / ((2 * np.pi * p["fs"]) ** 2 * p["mms"])
    rms = 2 * np.pi * p["fs"] * p["mms"] / p["qms"]
    s = 2j * np.pi * np.asarray(f, float)
    zm = rms + s * p["mms"] + 1 / (s * cms)
    ze = p["re"] + s * p["le"] + (1 / (s * cap) if cap else 0)
    i = 1 / (ze + p["bl"] ** 2 / zm)
    return s * p["bl"] * i / zm


def tweeter_excursion_m(f, t_pressure_pa_rms, r_m=1.0):
    """Peak diaphragm excursion from on-axis tweeter pressure (half-space
    compact-source radiation; waveguide gain ignored -> conservative)."""
    w = 2 * np.pi * f
    return np.sqrt(2) * t_pressure_pa_rms * 2 * np.pi * r_m / (RHO * w ** 2 * SD_TWEETER_M2)
