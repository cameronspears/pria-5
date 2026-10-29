"""Shared loaders and exact DSP-filter math for the crossover / PR study.

Filters follow the same RBJ / bilinear (48 kHz) math used in every earlier
Pria 5 audit, so de-embedding here matches those analyses.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
from scipy.signal import butter, freqz

HERE = Path(__file__).resolve().parent
MEAS = HERE.parent / "measurements"
FS = 48000.0
C_SOUND = 343.0


# ----------------------------------------------------------------- filters
def _resp(b, a, f):
    return freqz(b, a, worN=np.asarray(f, float), fs=FS)[1]


def butter_section(kind, fc, order, f):
    b, a = butter(order, fc, btype=kind, fs=FS)
    return _resp(b, a, f)


def rbj(kind, f0, q, f, gain_db=0.0):
    w = 2 * np.pi * f0 / FS
    alpha = np.sin(w) / (2 * q)
    cw = np.cos(w)
    if kind == "hp":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "lp":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "peak":
        A = 10 ** (gain_db / 40)
        b = [1 + alpha * A, -2 * cw, 1 - alpha * A]
        a = [1 + alpha / A, -2 * cw, 1 - alpha / A]
    else:
        raise ValueError(kind)
    return _resp(np.array(b) / a[0], np.array(a) / a[0], f)


def crossover(kind, fc, f):
    """Return (low, high) complex electrical transfer for a named alignment.

    LR2/LR4/LR8 are squared Butterworth sections (SigmaStudio's
    Linkwitz-Riley blocks).  BW3 is a 3rd-order Butterworth pair.
    LR2 high is polarity-inverted so the pair sums flat, as usual.
    """
    if kind == "LR2":
        lo = butter_section("lowpass", fc, 1, f) ** 2
        hi = -butter_section("highpass", fc, 1, f) ** 2
    elif kind == "LR4":
        lo = butter_section("lowpass", fc, 2, f) ** 2
        hi = butter_section("highpass", fc, 2, f) ** 2
    elif kind == "LR8":
        lo = butter_section("lowpass", fc, 4, f) ** 2
        hi = butter_section("highpass", fc, 4, f) ** 2
    elif kind == "BW3":
        lo = butter_section("lowpass", fc, 3, f)
        hi = butter_section("highpass", fc, 3, f)
    else:
        raise ValueError(kind)
    return lo, hi


def delay(samples, f):
    return np.exp(-2j * np.pi * f * samples / FS)


def db(x):
    return 20 * np.log10(np.maximum(np.abs(x), 1e-20))


# ------------------------------------------------------- smoothing helpers
def log_grid(lo=50.0, hi=20000.0, ppo=48):
    n = int(np.ceil(np.log2(hi / lo) * ppo)) + 1
    return lo * 2 ** (np.arange(n) / ppo)


def smooth_complex_power(f, x, grid, frac=12):
    """Fractional-octave power smoothing of |x|^2 onto ``grid`` (dB out)."""
    p = np.abs(x) ** 2
    out = np.empty(len(grid))
    half = 2 ** (1 / (2 * frac))
    cs = np.concatenate([[0], np.cumsum(p)])
    for i, g in enumerate(grid):
        lo, hi = np.searchsorted(f, g / half), np.searchsorted(f, g * half)
        lo = min(lo, len(f) - 1)
        hi = min(max(hi, lo + 1), len(f))
        out[i] = (cs[hi] - cs[lo]) / (hi - lo)
    return 10 * np.log10(np.maximum(out, 1e-30))


def to_grid_complex(f, x, grid):
    """Linear interpolation of complex data (real/imag) onto ``grid``."""
    return np.interp(grid, f, x.real) + 1j * np.interp(grid, f, x.imag)


# ----------------------------------------------------------------- loaders
# Default input: Crossover_check2_corrected (2026-09-30 build).  A newer
# capture imported with import_driver_set.py is used instead when the
# environment variable PRIA_DRIVER_SET points at its folder.
import json as _json
import os as _os

DEFAULT_SET = MEAS / "2026-09-30_crossover_corrected"
DEFAULT_CHAIN = {"woofer": {"xo": ["LR4", 3000], "trim_db": -4, "hp50_pair": True},
                 "tweeter": {"xo": ["LR4", 3000], "trim_db": -10, "invert": False,
                             "delay_samples": 0, "peq": []}}


def _driver_set():
    folder = Path(_os.environ.get("PRIA_DRIVER_SET", DEFAULT_SET))
    meta = folder / "driver_set.json"
    if meta.exists():
        d = _json.loads(meta.read_text())
        roles = [r["role"] for r in d["records"]]
        return folder, roles, d["capture_chain"]
    return folder, ["W", "W", "T", "T", "C", "C"], DEFAULT_CHAIN


def load_driver_set(window="5ms"):
    """Records ordered W..., T..., C...; returns f, [windowed], [native].

    Callers average the first two of each role, so captures should contain
    two of each (a single one is duplicated)."""
    folder, roles, _ = _driver_set()
    recs = {r: [] for r in "WTC"}
    for i, role in enumerate(roles, 1):
        recs[role].append(np.load(folder / f"record_{i}.npz"))
    ordered = []
    for r in "WTC":
        got = recs[r] if len(recs[r]) >= 2 else recs[r] * 2
        ordered += got[:2]
    f = ordered[0]["frequency_hz"]
    return f, [r[window] for r in ordered], [r["native"] for r in ordered]


def measured_chain(f):
    """DSP active during the capture (audited for the 2026-09-30 set:
    woofer 2 x RBJ HP 50 Hz Q .71 + LR24 low 3 kHz - 4 dB; tweeter LR24 high
    3 kHz - 10 dB, flat EQ, no delay, no invert)."""
    _, _, ch = _driver_set()
    wc, tc = ch["woofer"], ch["tweeter"]
    w = crossover(wc["xo"][0], wc["xo"][1], f)[0] * 10 ** (wc["trim_db"] / 20)
    if wc.get("hp50_pair", False):
        w = w * rbj("hp", 50, .71, f) ** 2
    for f0, q, g in wc.get("peq", []):
        w = w * rbj("peak", f0, q, f, g)
    t = crossover(tc["xo"][0], tc["xo"][1], f)[1] * 10 ** (tc["trim_db"] / 20)
    t = t * (-1 if tc.get("invert") else 1) * delay(tc.get("delay_samples", 0), f)
    for f0, q, g in tc.get("peq", []):
        t = t * rbj("peak", f0, q, f, g)
    return w, t


# ------------------------------------------------------ short-window spectra
def _half_tukey_window(size, start, center, end):
    from scipy.signal.windows import tukey
    w = np.zeros(size)
    w[start:center + 1] = tukey(2 * (center - start) + 1, .25)[:center - start + 1]
    w[center:end + 1] = tukey(2 * (end - center) + 1, .25)[end - center:]
    return w


def windowed_spectrum(npz, ms, ref_index=48000, pre_samples=24):
    """Uncalibrated complex short-window FFT on the record's native grid.

    Identical window recipe to every earlier Pria 5 diagnostic (0.5 ms
    left / ``ms`` right Tukey .25 about the saved reference index).  Mic
    calibration is a common smooth factor that cancels in same-session
    ratios, so callers only use these spectra in ratios.
    """
    imp = npz["impulse"]
    f = npz["frequency_hz"]
    step = f[1] - f[0]
    win = _half_tukey_window(len(imp), ref_index - pre_samples, ref_index,
                             ref_index + int(round(ms * 48)))
    spec = np.fft.rfft(imp * win)
    offset = int(round(f[0] / step))
    spec = spec[offset:offset + len(f)]
    # Reference phase to the saved window reference, like REW's native phase.
    return spec * np.exp(2j * np.pi * f * ref_index / FS)
