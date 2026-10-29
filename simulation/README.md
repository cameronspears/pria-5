# Simulation

These are the models I used to choose the V5.2 layout before anything was measured. They
compare options against each other. None of it is measured performance, and the built
speaker differs from the model in places (for example, the radiators ended up with 11 g of
added mass each, where the model used 7.8 g, and the crossover settled at 3 kHz).

| File | What it is |
|---|---|
| `waveguide/v5_2_close_coupled_ellipse_3d_confirmation.png` | A full 3-D finite-element run of the 98 × 50 × 16 mm waveguide at 2, 2.5 and 3 kHz, horizontal and vertical, out to 70°. |
| `waveguide/*.json` | The waveguide's profile parameters and the FEM results. |
| `system/FULL_FREQUENCY_RESPONSE_COMPARISON.md` | V5.0/V5.1 against V5.2 in the system model: one rear radiator against two side ones. |
| `system/response_squeeze_v5_2.*`, `system/full_frequency_response_comparison.*` | The modelled responses behind that comparison. |
| `system_model.py` | The electro-mechanical and directivity helpers the system model is built on (numpy and scipy). |
