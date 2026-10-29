# Tuning status

Where Pria 5's tuning stands, what was decided, and which predictions held when measured.
Last updated 2026-10-29.

The speaker runs **Tuning31**. Tuning30 was built and measured on 2026-10-22. Tuning31 refines
Tuning30's EQ. It was modelled from the 2026-10-22 sweeps and **hasn't been measured**.

- Measurements and the full report: [`measurements/tuning30_2026-10-22/`](../measurements/tuning30_2026-10-22/)
- The study the tuning came from: [`simulation/crossover_study_2026-10-21/`](../simulation/crossover_study_2026-10-21/)
- DSP rows: [`dsp/`](../dsp/)

## What's on the speaker now

| Item | State | Evidence |
|---|---|---|
| DSP file | Tuning31 | In use since 2026-10-22 |
| Build | R4.35 kit, same acoustic cavity, driver positions and lining as September | CAD |
| Passive-radiator mass | **8 g each, matched.** Every measurement up to 2026-10-22 had 9 g on one radiator and 8 g on the other, not the 11 g recorded on 2026-09-29 | Checked 2026-10-22 |
| Radiator tuning | 49.1 Hz; left and right within 0.3 dB | Measured 2026-10-22 |
| Tweeter polarity | **Inverted in the DSP**, by an IIR row with b0 = −1 | Measured 2026-10-22 |
| Crossover | Built from EQ rows. Woofer: 8th-order Linkwitz-Riley (LR48), four low-pass rows at 2500 Hz (Q 0.5412, 1.3066, 0.5412, 1.3066), −4 dB on the first. Tweeter: 4th-order Bessel, high-pass 2501 Hz Q 0.5219 (−10.5 dB) and 2231 Hz Q 0.8055. Tweeter delayed 3 samples. Acoustic crossover about 2.2 kHz | DSP file |
| Speaker EQ (Tuning31) | **Woofer:** high-pass 50 Hz Q 1.0 ×2; peak 64.4 Hz Q 1.2 +4.2 dB; peak 510 Hz Q 0.56 +3.3 dB; peak 1440 Hz Q 1.5 −2.1 dB; low shelf 100 Hz Q 0.71 +5.0 dB (bass tilt). **Tweeter:** peak 3300 Hz Q 3.5 −2.4 dB. 14 filters including crossover and inversion, down from 19 | Modelled |
| Speaker EQ (Tuning30, measured) | Woofer as above, but with 372 Hz Q 0.44 +2.7 dB, 1220 Hz Q 5 −4.0 dB, 1577 Hz Q 1.83 −2.4 dB and 3444 Hz Q 6 −2.7 dB in **both** banks instead of the three Tuning31 rows | Measured 2026-10-22 |
| Bass limiter | On the band below 150 Hz only. −12 dBFS flat, hold 30 ms, decay 50 dB/s, soft knee. Set from measured 10% THD points (below) | Measured 2026-10-22 |
| Clip guard | Each driver on its own channel, −1 dBFS flat, hold 5 ms, decay 100 dB/s | DSP file |
| Quiet-level bass lift | +4 dB below −24 dB, 70 Hz. Acts only at quiet levels | DSP file |
| Gain | Both mixers −6.5 dB. A full-scale source at 100% peaks at −1.4 to −1 dBFS, at the clip guard, so full source volume is the clean maximum | Measured 2026-10-22 |
| Volume | No volume pots. The source is the volume control | DSP file |
| Lining | 12.7 mm acoustic foam on top, bottom, sides and back | Added 2026-09-30 |

## How the DSP is organised

I plan to build more of these for other rooms, so the tuning corrects the speaker and leaves
the room alone. The DSP has three layers:

1. a **speaker preset**, the same in every unit;
2. a **bass tilt** shelf, set for placement and taste;
3. optional **room cuts**, cuts only. None are used.

## Decisions

| ID | Change | Expected | Status |
|---|---|---|---|
| D8 | **Tuning31 EQ.** Three rows replace Tuning30's four shared rows: woofer 510 Hz Q 0.56 +3.3 dB (was 372 Hz +2.7 dB in both banks); woofer 1440 Hz Q 1.5 −2.1 dB (was 1220 Hz Q 5 −4.0 dB and 1577 Hz −2.4 dB in both banks); tweeter 3300 Hz Q 3.5 −2.4 dB (was 3444 Hz Q 6 −2.7 dB in both banks) | Listening-window error 0.90 → 0.49 dB RMS over 300 Hz to 12 kHz; worst listening-window dip −3.0 → −1.9 dB; on-axis 1.07 → 0.74 dB RMS; 19 → 14 filters; 80 to 150 Hz 0.3 to 0.6 dB lower. Expected to hold within about 0.5 dB | **In use; predicted, not measured** |
| D6 | **Speaker preset**: 50 Hz high-pass pair; +4.2 dB at 64.4 Hz; four rows in both banks; 100 Hz bass tilt shelf +5 dB | Speaker within −1.0/+1.2 dB over the listening window, 60 Hz to 12 kHz | **Built as Tuning30 and measured.** On-axis 1 to 12 kHz −2.4/+1.7 dB: the 1220 Hz row cut more than needed. Superseded by D8 |
| D1 | **Crossover**: woofer LR48 at 2.5 kHz; tweeter 4th-order Bessel, −3 dB at 3.55 kHz; tweeter inverted; delay 3 samples; tweeter trim −10.5 dB | Flatter on-axis and listening window, about 40% less lobing at ±15° | **Done**, from EQ rows. Polarity confirmed; ±15° better than predicted |
| D2 | **Radiators to 8 g each**, matched | More clean bass output | **Done.** The real change was only 9/8 g to 8/8 g, because the starting mass was never 11 g |
| D7 | **Limiting cleanup**: bass-band limiter, per-driver clip guard at −1 dBFS, mixers set so full source volume meets the clip guard | No more vocals and treble ducking with the bass, no breathing | **Done** with measured values: ceiling −12 dBFS, mixers −6.5 dB |
| D4 | Fix the room's 80 Hz dip by moving the speaker | Dip filled without boosting | Open, optional |

## The 80 Hz room dip

The 12-seat room average with Tuning30 shows a dip centred on 80 Hz, 9 to 12 dB deep. The
room-free curve (close-mic plus gated 1 m) has no dip there, so it comes from the room and the
speaker's position, not the speaker. The September data agree: no dip in the close-mic
nearfields, a dip that changes with mic height but not with left and right. The likely cause is
a wall or floor about 1.1 m away cancelling near 80 Hz. EQ can't fill a cancellation (boosting
raises the reflection as much as the direct sound), so it's left alone. Moving the speaker is
the fix, and the bass tilt is the placement control.

## Predictions against measurements

Each prediction was written down before measuring. Measured on 2026-10-22 with Tuning30 unless
noted. ✅ confirmed, ⚠️ off but usable, ⏭ skipped or superseded.

| Check | Prediction | Measured | Status |
|---|---|---|---|
| Tweeter polarity | Reversed polarity gives a notch of about 17 dB near the crossover; inverted keeps 1.5 to 4 kHz within ±2 dB | Normal: **−17 dB hole at 2.3 kHz**. Inverted: 1.5 to 4 kHz within **−1.4/+1.6 dB**, and it sounded clearly better | ✅ |
| Radiator tuning after the mass change | 49.6 Hz, re-predicted once the real 9/8 g start was known (52 Hz assuming 11 g) | **49.1 Hz**; woofer dips about 14 dB at 49 Hz; radiators out-produce the woofer below about 56 Hz; left and right within 0.3 dB | ✅ |
| On-axis with the new crossover | Crossover alone about 0.7 dB RMS, 1 to 10 kHz; acoustic crossover about 2.17 kHz | With the speaker preset: 1 to 12 kHz **−2.4/+1.7 dB**; 1.5 to 4 kHz −1.4/+1.6 dB; 1.07 dB RMS | ✅ crossover, ⚠️ overall |
| Speaker preset on-axis, 1 to 12 kHz | Within about ±1.5 dB, 1.2 kHz peak gone | −2.4/+1.7 dB. The peak is gone, but the 1220 Hz Q 5 row dug a −2.3 dB hole | ⚠️, addressed by Tuning31 (predicted) |
| ±30° horizontal | Small change from on-axis | Within **−2.5/+1.6 dB** of on-axis to 12 kHz | ✅ |
| ±15° vertical | Worst dip about −4.3 dB | 15° up −1.5/+0.8 dB, 15° down −1.9/+1.1 dB, to 12 kHz | ✅ better than predicted |
| Room-free bass extension | (none) | **−3 dB at 48 Hz**, −6 dB at 46 Hz, −10 dB at 45 Hz. 65 to 100 Hz sits 8 to 10 dB above 1 to 12 kHz by design | Measured |
| Tuning31 listening window and on-axis | 0.49 dB RMS (Tuning30 measured 0.90); worst dip −1.9 dB; on-axis 0.74 dB RMS | Not measured yet | open |

## Measured bass limits

REW stepped sine, THD against level, mic close to the woofer dust cap, bass limiter opened up
for the test. The woofer runs out before the radiators from about 52 to 150 Hz.

| Hz | 10% THD at the bass limiter (dBFS) |
|---|---|
| 40 | −17.1 |
| 45 | −9.8 |
| 50 | −13.7 |
| 56 | −11.3 |
| 63 | −10.9 |
| 71 | about −9 |
| 80 | above −12, likely about −7 |
| 100 | above −15, likely about −5 |
| 125 | above −19, likely about −5 |

From 71 Hz up the microphone saturated (about 119 dB SPL at the cone), so those points are
extrapolated. 3% THD came at a third or less of the woofer's rated excursion, so 10% (Klippel's
Xmax definition) is the limit used. At the −12 dBFS ceiling, 56 to 125 Hz stays at or under
about 9% THD, 50 Hz reaches about 12% and 40 Hz about 17%. A stricter rule (lowest 10% point
minus 1 dB) would give −18 dBFS, set entirely by 40 Hz, where the speaker is already 10 dB
down.

## Not measured

Tuning31 itself, maximum SPL, far-field distortion, intermodulation and power handling. The
proof sweeps for Tuning31 (on- and off-axis, close-mic, room average) are planned but not run.
