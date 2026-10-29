# Tuning30 measurements, 2026-10-22 (and the Tuning31 prediction)

The measurements of the current speaker: the R4.35 build with 8 g on each passive radiator,
running Tuning30. Tuning30 is the crossover, speaker EQ, bass tilt and limiting worked out in
the [2026-10-21 study](../../simulation/crossover_study_2026-10-21/). Tuning31, the file on the
speaker now, refines Tuning30's EQ. It was modelled from these sweeps and **hasn't been
measured**.

Measured with REW 5.31 and a UMIK-1 (0° calibration), driving the KABD-250 over Bluetooth, in
one room, on one unit. Setup and processing for each measurement are in the report's "Method and
limitations" section.

- [`PERFORMANCE_REPORT.md`](PERFORMANCE_REPORT.md): the write-up. Results, methods, limitations,
  the final DSP rows, and the Tuning31 prediction.
- `derived/`: the data behind each chart, as CSV, with a PNG of each. These are processed curves
  (gated, smoothed, some normalised), not raw REW exports. The raw `.mdat` and `.dspproj` files
  aren't in this repository.

| File | What it shows | Basis |
|---|---|---|
| `t30_polarity.*` | On-axis 1 m: tweeter normal vs inverted | Measured |
| `t30_roomfree_response.*` | Room-free response: close-mic woofer and radiators below about 300 Hz, gated 1 m above | Measured |
| `t30_offaxis_deltas.*` | ±30° horizontal and ±15° vertical, each minus on-axis | Measured |
| `t30_bass_alignment.*` | Close-mic woofer and both radiators at −50 dBFS | Measured |
| `t30_room_average.*` | 12-seat power average against the room-free curve | Measured |
| `t30_distortion.*` | Stepped-sine THD against level at the bass limiter, 40 to 125 Hz | Measured |
| `t31_predicted_listening_window.*` | Listening window: Tuning30 as built against Tuning31 | Tuning30 measured, Tuning31 **modelled, not measured** |
| `dsp_signal_chain.md` | The Tuning30 signal chain, input to amplifiers | DSP file |

What hasn't been measured: Tuning31 itself, maximum SPL, far-field distortion, intermodulation
and power handling.
