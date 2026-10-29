# DSP settings

Pria 5 runs on a Dayton Audio KABD-250 board (ADAU1701 DSP, 48 kHz), programmed in SigmaStudio
4.7 through Dayton's KPX programmer. Bluetooth stereo is summed to mono, then split into a woofer
path (DAC1) and a tweeter path (DAC0). The source is the volume control; there are no pots.

The speaker runs **Tuning31**. Its EQ is modelled from the Tuning30 measurements and **hasn't
been measured**. Tuning30 was measured on 2026-10-22. See
[`docs/tuning-status.md`](../docs/tuning-status.md) for what was measured and what's predicted.

## Files

| File | What it is |
|---|---|
| `tuning31_eq.csv` | Every EQ row in Tuning31, the file in use. 14 filters, including the crossover and the tweeter inversion |
| `tuning30_eq.csv` | Every EQ row in Tuning30, in row order, as measured on 2026-10-22. 19 filters |
| `tuning22/` | The earlier Tuning22 SigmaStudio project and its EQ list, from the September tuning. History only |

The Tuning30 and Tuning31 SigmaStudio projects aren't in this repository. The rows above are
everything they change in the EQ; the signal chain is in
[`measurements/tuning30_2026-10-22/derived/dsp_signal_chain.md`](../measurements/tuning30_2026-10-22/derived/dsp_signal_chain.md).

## Signal chain

**Crossover.** Built from EQ rows; SigmaStudio's crossover block isn't used. The woofer gets an
8th-order Linkwitz-Riley low-pass (four 2nd-order rows at 2500 Hz). The tweeter gets a 4th-order
Bessel high-pass (2501 Hz Q 0.5219 and 2231 Hz Q 0.8055), is **inverted** (an IIR row with
b0 = −1), and is delayed 3 samples (62.5 µs). The acoustic crossover lands near 2.2 kHz. With
normal polarity the drivers cancel into a 17 dB hole at 2.3 kHz (measured).

**Speaker preset.** The same in every unit: two 50 Hz high-pass rows (Q 1.0) to protect the
woofer, +4.2 dB at 64.4 Hz for the bass alignment, a baffle-step lift, and cuts for the speaker's
own peaks. In Tuning31 those are three rows (510 Hz +3.3 dB and 1440 Hz −2.1 dB on the woofer,
3300 Hz −2.4 dB on the tweeter) where Tuning30 had four rows in both banks.

**Bass tilt.** A 100 Hz low shelf, +5 dB, set for placement and taste.

**Bass limiter.** On the band below 150 Hz only, split off and recombined with a 150 Hz
Linkwitz-Riley pair (the tweeter path has a matching pair so both stay in phase). −12 dBFS flat,
hold 30 ms, decay 50 dB/s, soft knee. The ceiling comes from measured 10% THD points.

**Quiet-level bass lift.** +4 dB below −24 dB, at 70 Hz. It does nothing at normal levels.

**Clip guard.** Each driver on its own channel at −1 dBFS, hold 5 ms, decay 100 dB/s.

**Gain.** Both mixers at −6.5 dB, so a full-scale source at 100% peaks at −1.4 to −1 dBFS, at
the clip guard. Full source volume is the clean maximum (measured).

## Before you load anything

These settings were made for my board, power supply, drivers and radiator masses (8 g each).
Load to RAM first, at low volume, and listen before writing to EEPROM. The limiter ceiling comes
from my woofer's measured distortion; it isn't a measured maximum-output limit for the speaker.
