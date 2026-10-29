# Simulation

Models used to make design decisions. They compare options against each other. None of it is
measured performance.

- [`crossover_study_2026-10-21/`](crossover_study_2026-10-21/): the study behind the current
  tuning. A room-free model of the speaker (bass model, the cabinet's baffle step by BEM, and
  the measured drivers) used to pick the crossover, the radiator mass, the bass target and the
  speaker preset. Tuning30 was built from it and measured on 2026-10-22; its README has the
  corrections since.
- The files below are the earlier pre-build models used to choose the V5.2 layout. The built
  speaker differs from them: the radiators carry 8 g each where the model used 7.8 g, and the
  crossover is about 2.2 kHz acoustic where the model planned 2.5 kHz.

| File | What it is |
|---|---|
| `waveguide/v5_2_close_coupled_ellipse_3d_confirmation.png` | A full 3-D finite-element run of the 98 × 50 × 16 mm waveguide at 2, 2.5 and 3 kHz, horizontal and vertical, out to 70°. |
| `waveguide/*.json` | The waveguide's profile parameters and the FEM results. |
| `system/FULL_FREQUENCY_RESPONSE_COMPARISON.md` | V5.0/V5.1 against V5.2 in the system model: one rear radiator against two side ones. |
| `system/response_squeeze_v5_2.*`, `system/full_frequency_response_comparison.*` | The modelled responses behind that comparison. |
| `system_model.py` | The electro-mechanical and directivity helpers the system model is built on (numpy and scipy). |
