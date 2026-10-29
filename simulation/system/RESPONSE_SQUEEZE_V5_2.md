# V5.2 response-squeeze decision

The current V5.1 is already close to the useful limit of a pre-measurement
model. A prettier nominal axial line would be false precision. Two physical
changes still produce gains large enough to survive the model uncertainty.

## Worth carrying into a V5.2 CAD study

1. **Two opposed side DS115-PRs**, **2.60 L net**, **+7.8 g on each PR**, and
   a provisional **40 Hz LR4 high-pass**. Relative 65--250 Hz error improves
   from **+/-2.13 dB** to
   **+/-0.99 dB**, F3 moves from
   **63.1 Hz** to **60.5 Hz**, and the
   modeled 80--200 Hz ceiling rises **1.2 dB**.
2. A **98 x 50 x 16 mm smooth analytic OT19 waveguide** with a side-only hidden
   mount, **72.23 mm CTC**, and a provisional **2.50 kHz LR4 acoustic
   handoff**. Sectional-FEM PIR residual improves from
   **0.263 dB** to
   **0.183 dB RMS**;
   worst +/-20-degree crossover-band level improves from
   **-2.51 dB** to
   **-2.09 dB**; and the
   geometric first null moves from **60.3 degrees** to
   **71.8 degrees**.
   Full 3-D FEM independently gives **-2.05 dB**
   versus **-1.77 dB** at 20 degrees at each
   design's crossover.
3. Moving the PRs off the rear wall permits a **solid, lined rear wall behind
   the ND91**. This is the most credible way to reduce rear-wave return and PR
   midrange leakage, but its exact benefit cannot be claimed until the real
   cabinet is measured.

The cubic flare is monotonic and tangent to the baffle at its mouth, so the
inherited contour's terraces and visible termination ring are gone. The
98 x 50 acoustic aperture can still sit inside a visually integrated outer
halo; it does not require a rectangular fastener island. The 72.23 mm CTC
assumes a 52 mm cosmetic nose and leaves 2 mm to the ND91 frame; the hidden
clamp therefore has to move to the sides.

## What the gain does not mean

- The nominal axial proxy is already essentially unchanged: **0.303 dB RMS**
  for V5.1 versus **0.312 dB RMS** for the
  2.50 kHz candidate. The improvement is coverage/directivity, not a magic
  flatter on-axis trace.
- Lowering the handoff to 2.30 kHz buys only a few tenths of a decibel of
  vertical coverage while spending unmeasured OT19 excursion and distortion
  margin. Keep 2.50 kHz as the pre-measurement target.
- Increasing box volume enough to chase a much lower F3 trades away the
  80--200 Hz balance and output. With this ND91, the dual-PR 2.60 L alignment
  is the useful knee rather than an arbitrary endpoint.
- These are nominal T/S, ideal-filter, rigid-wall, and geometry-only results.
  They do not include production-unit variation, real acoustic-center offset,
  finite-baffle diffraction, grille effects, losses, or nonlinear distortion.

## Decision

Do not revise the released V5.1 STLs from this study alone. If another enclosure
iteration is acceptable, build **V5.2 as one coordinated package**: dual opposed
side PRs, solid/damped rear wall, and the close-coupled waveguide. Then measure
the current V5.1 mule before locking crossover polarity, delay, or EQ.
