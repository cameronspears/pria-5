# Woofer baffle step by BEM (2026-10-21)

`run_bem_woofer.py` drives the ND91 as a 30.4 cm² piston in the real cabinet
shape and solves the sound field around it (boundary-element method). It uses
the validated solver formulation and the `flush` mesh from
`development/hf_bem_2026_09_04/`: 142 × 230 × 142 mm, woofer 81 mm and tweeter
153.2 mm above the bottom. The sweep runs 150 Hz–3 kHz in 22 steps. Output:
`bem_woofer_results.json`, far-field values for the horizontal and vertical
arcs plus a 400-point sphere.

Result, on-axis relative to the same source radiating in free space:

| Hz | 150 | 306 | 470 | 720 | 958 | 1275–1470 | 2–3 k |
|---|---|---|---|---|---|---|---|
| dB | +0.15 | +1.2 | +3.2 | +5.2 | +6.8 | +9.0 (front-edge diffraction peak) | +7.4 to +8.4 |

Sound power rises only about 3 dB over the same range, so the directivity
index reaches about 5.5–6 dB by 1.3 kHz.

Notes:

* **Solver tolerance.** GMRES uses 1e-4 instead of the original study's 2e-6,
  which stalled at 60 Hz (residual 3e-5). This only matters at low
  frequency, where the cabinet is acoustically tiny.
* **Below 150 Hz.** `speaker_anechoic.py` fades the baffle effect to 0 dB by
  60 Hz.
* **Cabinet depth.** The current build is ~180 mm deep, not 142 mm. This has
  little effect on the front-panel step.
* **PRs.** They are rigid in the mesh; they radiate as monopoles in the model.

Run with the solver environment from the HF BEM study's `requirements.txt` (not included here)
(bempp-cl 0.4.2, numba 0.60, numpy 2.0.2, scipy 1.13.1, trimesh). It takes
about 45 min on one core.
