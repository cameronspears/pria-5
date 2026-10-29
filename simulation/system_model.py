"""Reusable electro-mechanical and directivity helpers for Acoustic V5.

All dimensions are SI unless a name explicitly ends in ``_mm`` or ``_l``.
Published T/S data are treated as nominal.  These functions rank concepts;
they do not turn nominal datasheet curves into measurements of an enclosure.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from scipy import signal
from scipy.special import j1


RHO = 1.204
C = 343.0
P_REF = 20e-6


@dataclass(frozen=True)
class ActiveDriver:
    re: float = 4.28
    le: float = 0.00083
    fs: float = 74.0
    qms: float = 4.24
    mms: float = 0.0048
    cms: float = 0.00096
    sd: float = 0.00304
    bl: float = 4.59
    xmax: float = 0.0046

    @property
    def rms(self) -> float:
        return 2.0 * np.pi * self.fs * self.mms / self.qms


@dataclass(frozen=True)
class PassiveRadiator:
    fs: float = 29.3
    qms: float = 3.66
    mms: float = 0.013
    cms: float = 0.00227
    sd: float = 0.00541
    xmax: float = 0.006
    rms: float = 0.7


ND91 = ActiveDriver()
DS115 = PassiveRadiator()


def lr4_highpass(freq: np.ndarray, fc: float) -> np.ndarray:
    s = 1j * 2.0 * np.pi * freq
    wc = 2.0 * np.pi * fc
    denominator = s**2 + np.sqrt(2.0) * wc * s + wc**2
    return (s**2 / denominator) ** 2


def lr4_pair(freq: np.ndarray, fc: float) -> tuple[np.ndarray, np.ndarray]:
    """Complex acoustic LR4 low/high pair whose on-axis sum is all-pass."""
    s = 1j * freq / fc
    denominator = s**2 + np.sqrt(2.0) * s + 1.0
    low = (1.0 / denominator) ** 2
    high = (s**2 / denominator) ** 2
    return low, high


def solve_alignment(
    freq: np.ndarray,
    volume_l: float,
    added_mass_g: float,
    voltage_rms: float = 2.83,
    highpass_hz: float | None = None,
    rear_path_m: float = 0.205,
    pr_count: int = 1,
) -> dict[str, np.ndarray]:
    """Solve ND91 + one or more identical DS115-PRs + cabinet.

    ``added_mass_g`` is the mass added to each radiator.  Identical passive
    radiators are assumed to see the same box pressure and move in phase.  The
    returned PR excursion is per radiator; radiated volume velocity includes
    every radiator.
    """
    if pr_count < 1:
        raise ValueError("pr_count must be at least 1")
    w = 2.0 * np.pi * freq
    volume = volume_l / 1000.0
    mass_pr = DS115.mms + added_mass_g / 1000.0
    stiffness_air = RHO * C**2 / volume
    filt = (np.ones_like(freq, dtype=complex) if highpass_hz is None
            else lr4_highpass(freq, highpass_hz))
    source = voltage_rms * filt

    current = np.zeros_like(freq, dtype=complex)
    velocity_d = np.zeros_like(freq, dtype=complex)
    velocity_p = np.zeros_like(freq, dtype=complex)
    pressure_box = np.zeros_like(freq, dtype=complex)
    for n, omega in enumerate(w):
        ze = ND91.re + 1j * omega * ND91.le
        zmd = ND91.rms + 1j * omega * ND91.mms + 1.0 / (1j * omega * ND91.cms)
        zmp = DS115.rms + 1j * omega * mass_pr + 1.0 / (1j * omega * DS115.cms)
        pressure_per_flow = stiffness_air / (1j * omega)
        matrix = np.asarray([
            [ze, ND91.bl, 0.0, 0.0],
            [-ND91.bl, zmd, 0.0, ND91.sd],
            [0.0, 0.0, zmp, DS115.sd],
            [0.0, -pressure_per_flow * ND91.sd,
             -pressure_per_flow * pr_count * DS115.sd, 1.0],
        ], dtype=complex)
        solution = np.linalg.solve(matrix, np.asarray([source[n], 0.0, 0.0, 0.0]))
        current[n], velocity_d[n], velocity_p[n], pressure_box[n] = solution

    q_driver = ND91.sd * velocity_d
    q_pr = (pr_count * DS115.sd * velocity_p
            * np.exp(-1j * 2.0 * np.pi * freq * rear_path_m / C))
    p_driver = 1j * w * RHO * q_driver / (2.0 * np.pi)
    p_pr = 1j * w * RHO * q_pr / (2.0 * np.pi)
    p_total = p_driver + p_pr
    return {
        "frequency_hz": freq,
        "pressure_total": p_total,
        "pressure_driver": p_driver,
        "pressure_pr": p_pr,
        "spl_total_db": 20.0 * np.log10(np.maximum(np.abs(p_total), 1e-14) / P_REF),
        "spl_driver_db": 20.0 * np.log10(np.maximum(np.abs(p_driver), 1e-14) / P_REF),
        "spl_pr_db": 20.0 * np.log10(np.maximum(np.abs(p_pr), 1e-14) / P_REF),
        "driver_excursion_mm": np.abs(velocity_d / (1j * w)) * 1000.0,
        "pr_excursion_mm": np.abs(velocity_p / (1j * w)) * 1000.0,
        "impedance_ohm": np.divide(source, current, out=np.full_like(source, np.nan),
                                    where=np.abs(current) > 1e-15),
        "box_pressure_pa": pressure_box,
        "filter": filt,
    }


def tuning_formula(volume_l: float, added_mass_g: float,
                   pr_count: int = 1) -> float:
    if pr_count < 1:
        raise ValueError("pr_count must be at least 1")
    volume = volume_l / 1000.0
    mass = DS115.mms + added_mass_g / 1000.0
    stiffness = (1.0 / DS115.cms
                 + pr_count * RHO * C**2 * DS115.sd**2 / volume)
    return math.sqrt(stiffness / mass) / (2.0 * math.pi)


def impedance_tuning(freq: np.ndarray, impedance: np.ndarray) -> float:
    magnitude = np.abs(impedance)
    band = (freq >= 25.0) & (freq <= 110.0)
    indices = np.flatnonzero(band)
    minima, _ = signal.find_peaks(-magnitude[band])
    if len(minima):
        return float(freq[indices[minima[0]]])
    return float(freq[indices[np.argmin(magnitude[band])]])


def contiguous_lower_f3(freq: np.ndarray, spl_db: np.ndarray) -> float:
    """Lower -3 dB edge contiguous with the 150--250 Hz passband."""
    reference = float(np.median(spl_db[(freq >= 150.0) & (freq <= 250.0)]))
    threshold = reference - 3.0
    start = int(np.argmin(np.abs(freq - 150.0)))
    index = start
    while index > 0 and spl_db[index] >= threshold:
        index -= 1
    if index == start:
        return float("nan")
    return float(freq[min(index + 1, len(freq) - 1)])


def voltage_before_xmax(result_at_1v: dict[str, np.ndarray], freq: np.ndarray,
                        lower_hz: float = 20.0) -> tuple[float, str]:
    band = (freq >= lower_hz) & (freq <= 250.0)
    driver_limit = ND91.xmax * 1000.0 / np.max(result_at_1v["driver_excursion_mm"][band])
    pr_limit = DS115.xmax * 1000.0 / np.max(result_at_1v["pr_excursion_mm"][band])
    if driver_limit <= pr_limit:
        return float(driver_limit), "ND91"
    return float(pr_limit), "DS115-PR"


def group_delay_ms(freq: np.ndarray, pressure: np.ndarray) -> np.ndarray:
    phase = np.unwrap(np.angle(pressure))
    omega = 2.0 * np.pi * freq
    return -np.gradient(phase, omega) * 1000.0


def piston_directivity(sd_m2: float, frequency_hz: np.ndarray | float,
                       angles_deg: np.ndarray) -> np.ndarray:
    """Infinite-baffle circular-piston magnitude with the same Sd."""
    radius = math.sqrt(sd_m2 / math.pi)
    frequency = np.asarray(frequency_hz, dtype=float)
    angle = np.asarray(angles_deg, dtype=float)
    x = (2.0 * np.pi / C) * np.multiply.outer(frequency, np.sin(np.deg2rad(angle))) * radius
    output = np.ones_like(x)
    nz = np.abs(x) > 1e-12
    output[nz] = np.abs(2.0 * j1(x[nz]) / x[nz])
    return np.maximum(output, 1e-7)


def rounded_rectangle_area_mm2(width_mm: float, height_mm: float,
                               radius_mm: float) -> float:
    return width_mm * height_mm - (4.0 - math.pi) * radius_mm**2


def ray_distances_to_rectangle(width_mm: float, height_mm: float,
                               x_mm: float, y_mm: float) -> np.ndarray:
    distances = []
    for angle_deg in np.arange(0.0, 360.0, 5.0):
        angle = math.radians(angle_deg)
        dx, dy = math.cos(angle), math.sin(angle)
        hits = []
        if dx > 1e-12:
            hits.append((width_mm / 2.0 - x_mm) / dx)
        elif dx < -1e-12:
            hits.append((-width_mm / 2.0 - x_mm) / dx)
        if dy > 1e-12:
            hits.append((height_mm - y_mm) / dy)
        elif dy < -1e-12:
            hits.append((0.0 - y_mm) / dy)
        distances.append(min(value for value in hits if value > 0.0))
    return np.asarray(distances)


def edge_coherence(width_mm: float, height_mm: float, x_mm: float,
                   y_mm: float, roundover_mm: float = 0.0) -> float:
    """Unitless 72-ray first-edge coherence proxy; lower is preferable."""
    distance = ray_distances_to_rectangle(width_mm, height_mm, x_mm, y_mm) / 1000.0
    freq = np.geomspace(600.0, 6000.0, 500)
    phasor = np.exp(-1j * 2.0 * np.pi * freq[:, None] * distance[None, :] / C)
    coherence = np.abs(np.mean(phasor, axis=1))
    # A roundover reduces the abruptness of the edge but does not eliminate it.
    smooth = 1.0 / np.sqrt(1.0 + (2.0 * np.pi * freq * roundover_mm / 1000.0 / C)**2)
    return float(np.sqrt(np.mean((coherence * smooth)**2)))
