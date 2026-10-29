# DSP signal chain (Pria 5, Tuning30 report)

The diagram holds labels only, no numeric series, so there is no CSV or PNG.

**Only the bass band is limited; each driver has its own clip guard**

Flow, top to bottom (boxes in **bold** are the two the diagram highlights):

1. Stereo input: left and right; also sent unprocessed to the line outputs
2. Stereo-to-mono mixers: one per driver, −6.5 dB each; a full-scale source lands at the clip guard
3. Splits into two driver paths:

| Step | Woofer path | Tweeter path |
|---|---|---|
| 1 | Woofer EQ: 12 rows: high-passes, speaker EQ, bass tilt, LR48 | Tweeter EQ: 7 rows: shared EQ, Bessel-24 high-pass, polarity |
| 2 | Bass Enhance: +4 dB at 70 Hz, only on quiet passages | Phase match: 150 Hz split and sum, same phase as the woofer |
| 3 | Bass split, 150 Hz: low band to the limiter, high band past it | Delay: 3 samples, 62.5 µs |
| 4 | **Bass limiter** (below 150 Hz only): −12 dBFS peak, 30 ms hold, 50 dB/s; above 150 Hz bypasses it | (no limiter) |
| 5 | Bass sum: low and high bands rejoined | |
| Guard | **Clip guard, per driver**: −1 dBFS peak; each side detects its own driver (unlinked); 5 ms hold, 100 dB/s | same clip guard, own detector |
| Output | Woofer amplifier, DAC1: Dayton ND91-4 | Tweeter amplifier, DAC0: Tymphany OT19NC00-04 |
