# DSP settings

Pria 5 runs on a Dayton Audio KABD-250 board (ADAU1701 DSP). I programmed it in SigmaStudio 4.7
through Dayton's KPX programmer. Bluetooth stereo is summed to mono, then split into a woofer
branch (DAC1) and a tweeter branch (DAC0).

## Files

| File | What it is |
|---|---|
| `Tuning22_Refine.dspproj` | The SigmaStudio project for Tuning22 (2026-10-02). This is the last project file I checked line by line against the planned values. |
| `tuning22_eq.csv` | Every EQ row in Tuning22, both branches, sorted by frequency. |

## Signal chain in Tuning22

**Woofer branch** (the EQ feeds the bass lift, which feeds the 150 Hz split)

- Two 50 Hz high-pass filters in series, Q 0.71 each, to keep the woofer out of excursion it
  can't use
- Fifteen EQ rows: the two high-passes, a 70 Hz boost (Q 0.7, +9 dB), and twelve peaking
  filters shared with the tweeter branch
- Low-volume bass lift (SigmaStudio "Dynamic Enhancement": −24 dB threshold, 500 ms, +4 dB,
  70 Hz)
- A 150 Hz Linkwitz-Riley 24 dB/oct split with a limiter on the bass band only, then recombined
- 3 kHz Linkwitz-Riley 24 dB/oct low-pass, branch gain −4 dB

**Tweeter branch**

- Thirteen peaking filters: the twelve shared ones and a 3.5 kHz cut (Q 3, −2 dB)
- A matching 150 Hz split and sum, so the two branches stay in phase
- 3 kHz Linkwitz-Riley 24 dB/oct high-pass, branch gain −10 dB, no polarity inversion
- 3 samples of delay (62.5 µs at 48 kHz)

A final peak limiter is driven from the woofer signal and applies to both.

The twelve shared filters were fitted to a twelve-position room average, aiming at a target
that falls 0.5 dB per octave from a 500 Hz reference.

## What I listen with now

After Tuning22 I changed a few levels by ear:

| Control | Tuning22 file | Now |
|---|---|---|
| Both mixers | −12 dB | −4 dB |
| Bass detector | −6 dB | −3 dB |
| Single 1 (limiter detector) | −6 dB | −6 dB |
| Woofer high-pass filters | 50 Hz | 50 Hz (I tried 80 Hz and went back) |

These later values are what I set on the board. I haven't saved and re-checked a project file
with them, so the `.dspproj` here still has the Tuning22 values.

## Before you load it

The project was built for my board, power supply and drivers. Load it to RAM first, at low
volume, and listen before writing it to EEPROM. The levels and limiters protect my drivers at
my listening levels; they aren't a measured maximum-output limit.
