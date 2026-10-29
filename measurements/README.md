# Measurements

## Current: Tuning30, 2026-10-22

[`tuning30_2026-10-22/`](tuning30_2026-10-22/) holds the measurements of the speaker as it is
now: the R4.35 build with 8 g on each radiator, running Tuning30. It includes the full
performance report and the data behind every chart. The file in use, Tuning31, is modelled from
those sweeps and hasn't been measured. [`docs/tuning-status.md`](../docs/tuning-status.md) lists
each prediction next to what was measured.

## History: the first prototype, September

Measured on the first complete prototype, 2026-09-29 to 2026-10-02, with a miniDSP UMIK-1
(using its own calibration file) and REW, playing sweeps over Bluetooth, in a normal room. None of this is
anechoic, and there's no full polar set.

Each folder below holds the CSV behind one September plot. Frequencies are in Hz and levels
in dB SPL as REW exported them.

| Folder | What was measured | Plot |
|---|---|---|
| `bass_nearfields_2026-09-29/` | Woofer and each passive radiator, close-miked one at a time, 20 to 500 Hz. The radiators carried 9 g and 8 g (recorded at the time as 11 g each). Unsmoothed. | `docs/images/bass-nearfields.png` |
| `tweeter_delay_2026-09-30/` | Above the listening axis, with the tweeter delayed 2, 3 and 4 samples. One file with the full room window, one with a 3 ms window to reduce room reflections. | `docs/images/tweeter-delay.png` |
| `horizontal_30deg_2026-09-29/` | On axis and 30° left and right, full room window. | `docs/images/horizontal-30deg.png` |
| `room_average_tuning12_2026-09-30/` | Twelve-position average after Tuning11 and Tuning12, the Tuning12 prediction, and the target. | `docs/images/room-average-tuning12.png` |

### What the September numbers say

- **Tuning.** The woofer's nearfield dip is at 50.54 Hz and both radiators peak at 49.07 Hz,
  so the box is tuned to about 50 Hz. That isn't a measured −3 dB point for the whole speaker.
- **Room average.** After Tuning12, the twelve-position average was within −0.82 / +0.89 dB of
  the target from 1 to 16 kHz, and −1.41 / +2.58 dB from 60 Hz to 16 kHz. The last three
  positions read lower than the rest.
- **Later tuning.** Tuning22 changed the EQ toward a gentler target. Its response is a
  prediction from the Tuning12 measurement (−1.09 / +0.80 dB from 180 Hz to 16 kHz). I didn't
  re-measure after it.

The October retune superseded these results. The original REW `.mdat` files aren't in this
repository.
