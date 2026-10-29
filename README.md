# Pria 5

A compact mono two-way speaker that I designed, 3D printed, measured and tuned at home.
It uses a 3.5 in woofer, a 19 mm tweeter in a printed waveguide, two side-firing passive
radiators and a small DSP amplifier board. The "5" is the fifth design generation.

![Pria 5, rendered from the R4.35 release files](docs/images/renders/hero.png)

The current mechanical release is **R4.35** (2026-10-20). Getting there took 23 named versions
(V1 to V5.2) and 39 numbered revisions of V5.2 after that. Each one changed because a print
failed, a part didn't fit, a measurement said so, or I changed my mind about how it should look.
This repository has the printable files, the measurements and DSP settings it was tuned with,
and the reasons behind the main changes.

> **Status.** The speaker runs **Tuning31**. Tuning30 was measured on 2026-10-22, on one unit in
> one room with a UMIK-1. Tuning31 refines Tuning30's EQ; it's modelled from those sweeps and
> **hasn't been measured**. Maximum SPL, far-field distortion and power handling aren't
> measured either. Nothing here was measured in an anechoic space or across a full polar set.
> [`docs/tuning-status.md`](docs/tuning-status.md) separates what's measured from what's
> predicted.

## At a glance

| | |
|---|---|
| Woofer | Dayton Audio ND91-4, 3.5 in aluminium cone |
| Tweeter | Tymphany (Peerless) OT19NC00-04, 19 mm ring radiator, with a 33 µF / 100 V bipolar capacitor in series for protection |
| Bass loading | 2 × Dayton Audio DS115-PR passive radiators, mounted on opposite sides, 8 g added to each |
| Amplifier and DSP | Dayton Audio KABD-250 (ADAU1701), programmed in SigmaStudio, 24 V / 5 A supply |
| Crossover | Woofer 8th-order Linkwitz-Riley low-pass at 2.5 kHz, tweeter 4th-order Bessel high-pass, tweeter inverted and delayed 3 samples (62.5 µs at 48 kHz). Acoustic crossover about 2.2 kHz |
| Waveguide | Printed elliptical waveguide, 98 × 50 × 16 mm |
| Bass | Radiators tuned to 49.1 Hz; room-free −3 dB at 48 Hz (measured, Tuning30) |
| Cabinet | 142 × 230 mm face, about 167 mm deep, PLA, five print plates |
| Input | Bluetooth (stereo summed to mono) |

## How it's built

![Exploded view of the R4.35 parts](docs/images/renders/exploded.png)

**Cabinet.** Five plates on a Bambu Lab X2D: the front baffle, a magnetic front frame, the body,
the rear, and a plate with the waveguide and the woofer cover. The body holds the
acoustic chamber. The rear holds the amplifier in its own bay, sealed from the chamber by a
bulkhead and a small plate that the speaker wires pass through. The joints are sealed with
1 × 8 mm closed-cell foam tape, and the inside is lined with 1/2 in acoustic foam.

**Front.** No grille. A slim frame covers the six front screws and is held on by four
8 × 2 mm magnets that are sealed inside the print (the printer pauses so they can be dropped in,
then prints over them). The baffle's matching magnets sit in tabbed pockets, settled after three
test coupons.

**Waveguide.** An analytic flare, 98 × 50 × 16 mm, wider than it is tall. It replaced an earlier
borrowed waveguide shape and a series of round ones. Its size was driven by driver spacing: a
smaller guide lets the drivers sit closer (75.6 mm centre to centre), which widens the vertical
range where they add up cleanly. That matters because the speaker sits above ear height.

**Passive radiators.** Two radiators on opposite sides instead of one on the back. Mounted
opposite each other, they push on the cabinet in opposite directions so the forces cancel,
and the pair gave a better low-frequency alignment in the model. Each carries 8 g of added
mass on a rear-mounted screw, and they measure within 0.3 dB of each other.

![Cutaway through the centre of the speaker](docs/images/renders/cutaway.png)

**DSP.** The KABD-250 runs the crossover, EQ and protection. The tuning corrects the speaker
and leaves the room alone, so the same settings suit every unit. Tuning31 has 14 filters:

- the crossover, built from EQ rows: four low-pass rows at 2.5 kHz on the woofer, a 4th-order
  Bessel high-pass on the tweeter, and the tweeter inverted and delayed 3 samples
- two 50 Hz high-pass rows (Q 1.0) to protect the woofer, and +4.2 dB at 64.4 Hz for the bass
  alignment
- three corrective rows: 510 Hz +3.3 dB and 1440 Hz −2.1 dB on the woofer, 3300 Hz −2.4 dB on
  the tweeter
- a +5 dB bass tilt shelf at 100 Hz, set for placement and taste
- a bass-only limiter at −12 dBFS (from measured 10% THD points), a clip guard at −1 dBFS on
  each driver, and mixers at −6.5 dB so full source volume is the clean maximum

Every row is in [`dsp/`](dsp/), for both Tuning31 and the measured Tuning30.

## Measurements

Measured on 2026-10-22 with Tuning30, using a calibrated UMIK-1 and REW over Bluetooth, on one
unit in one room. The 1 m curves are gated to 3 to 5 ms to cut room reflections; the bass is
close-miked. They aren't anechoic data. The full write-up, with methods and limits, is
[`measurements/tuning30_2026-10-22/PERFORMANCE_REPORT.md`](measurements/tuning30_2026-10-22/PERFORMANCE_REPORT.md).

**Response without the room.** −3 dB at 48 Hz, and within −2.4/+1.7 dB of the average from 1 to
12 kHz on axis. The bass sits 8 to 10 dB above the midrange from 65 to 100 Hz on purpose: that's
the +5 dB tilt and the +4.2 dB alignment boost. The worst remaining dip, −2.3 dB near 1.2 kHz,
came from a Tuning30 EQ row that cut too much.

![Room-free response, measured with Tuning30](measurements/tuning30_2026-10-22/derived/t30_roomfree_response.png)

**Tweeter polarity.** With the tweeter in normal polarity the drivers cancel into a 17 dB hole at
2.3 kHz. Inverted, 1.5 to 4 kHz stays within −1.4/+1.6 dB. Both sweeps came from one mic position
with nothing moved, so the difference is the polarity alone.

![Tweeter normal and inverted, measured](measurements/tuning30_2026-10-22/derived/t30_polarity.png)

**Off-axis.** Turned 30° left or right, or 15° above or below tweeter height, the response stays
within −2.5/+1.6 dB of on-axis to 12 kHz. Vertically it did better than the model predicted.

![Off-axis responses minus on-axis, measured](measurements/tuning30_2026-10-22/derived/t30_offaxis_deltas.png)

**Tuning31 (modelled, not measured).** Applying the refined EQ to the Tuning30 sweeps predicts
the listening-window error falling from 0.90 to 0.49 dB RMS over 300 Hz to 12 kHz, with five
fewer filters. I haven't run the sweeps that would confirm it.

![Tuning31 listening window: modelled, not measured](measurements/tuning30_2026-10-22/derived/t31_predicted_listening_window.png)

*Tuning31: modelled, not measured.*

**In the room.** A 12-seat average shows a 9 to 12 dB dip at 80 Hz. The room-free curve has no
dip there, so it comes from where the speaker sits, not the speaker, and EQ can't fill it.
Moving the speaker is the fix.

**Bass limits.** The woofer runs out before the radiators. It reaches 10% THD at about −11 dBFS
on the bass limiter at 56 to 63 Hz, so the limiter ceiling sits at −12 dBFS.

[`docs/tuning-status.md`](docs/tuning-status.md) lists each prediction next to what was measured.
The first prototype's September measurements (Tuning01 to Tuning26) are in
[`measurements/`](measurements/) as history.

## How it got here

The full timeline is in [`docs/design-history.md`](docs/design-history.md). The decisions that
mattered most:

1. **V5 started over from the acoustics.** V1 to V4.8 were mostly about the enclosure: part
   count, inserts, layout and proportions. V5 began from the drivers and a
   simulated system model, picked the box and waveguide to suit them, and turned the earlier prints into a measurement mule.
2. **V5.2 moved to two side radiators and a smaller waveguide.** One rear radiator became two
   opposed side ones, and the waveguide shrank from 104 × 64 × 18 to 98 × 50 × 16 mm to bring
   the drivers closer together.
3. **R4 was redesigned so it could be assembled.** I couldn't screw the amplifier down in the
   old bay and the stock wires didn't reach. R4 moved the electronics onto the rear part so they
   can be fitted on the bench.
4. **Fourteen rounds of fighting warping.** The big flat baffle kept lifting at the corners. I
   tried cooling, reinforced cores, removable anchors, a home-made warp simulation and joint
   changes (C1 to C14). The real fixes were a loose nozzle clamp and switching to the stock
   Bambu presets.
5. **Correct the speaker, not the room.** The first tuning (September) was fitted to my room by
   ear and by room averages. In October I rebuilt it as a speaker preset that's the same in
   every unit: a model of the speaker without the room, a new crossover with the tweeter
   inverted, bass limits set from measured distortion, and room effects left to placement.
   Measuring it showed the radiators had carried 9 g and 8 g all along, not the 11 g I'd
   recorded.
6. **Trusting measured parts over drawings.** A printed test ring showed the radiator's frame
   is about 4.65 mm thick where the drawing suggested 2.6 mm, so a planned "flush radiator"
   revision was withdrawn. The tweeter retainer was resized several times from caliper readings
   and test fits.
7. **Dropping the grille.** Printed grilles from R4.18 to R4.24, then a fabric one in R4.28,
   ended with a plain magnetic frame and the drivers showing.
8. **Small parts, real leaks.** The last four revisions fix air leaks: a tweeter retainer
   0.5 mm shallower, and a wire pass-through sized for the actual four 2.2 mm wires and sealed
   with heat shrink and hot glue.

<p>
  <img src="docs/images/photos/baffle-warp.jpg" width="35%" alt="An early baffle print from the warping series, rough and stringy where the corners lifted">
  <img src="docs/images/photos/tweeter-retainer.jpg" width="62%" alt="An earlier printed tweeter retainer next to the OT19 tweeter, on top of the speaker body">
</p>

<sub>Left: a front baffle from the warping series. Right: an earlier tweeter retainer and the OT19 tweeter.</sub>

## Build one

Everything you print is in [`cad/`](cad/). Start with [`cad/PRINT_GUIDE.md`](cad/PRINT_GUIDE.md).

- **Printer settings I use:** Bambu Lab X2D, 0.4 mm nozzle, "0.20mm Standard" process,
  3 walls, 30% infill, no brim, supports off. Keep 0.20 mm layers; the built-in support tips
  depend on them.
- **Plates:** five STLs in `cad/plates/`, plus Bambu Studio projects in `cad/bambu/` with the
  magnet pauses already set (plate 1 pauses before layer 44, plate 2 before layer 17).
- **Hardware:** the drivers, radiators and amplifier listed above, M3 heat-set inserts
  (Ruthex RX-M3S×4) and M3 screws, eight 8 × 2 mm disc magnets, 1 × 8 mm foam tape,
  1/2 in acoustic foam, heat shrink and hot glue.
- **Desk stand (optional):** a tilt stand at 15°, 18° or 22° in `cad/stand/`.

These files are CAD and slicer checked. Fit, sealing and heat still need checking on a real
print, and I'd treat the newest front and rear parts as untested until I've printed them.

## Renders

The renders above come straight from the STLs in `cad/parts/`, placed with
[`tools/render/assemble.py`](tools/render/assemble.py) and lit in Blender with
[`tools/render/scene.py`](tools/render/scene.py). The woofer is Dayton Audio's reference model,
which isn't included here. There's no CAD for the tweeter or the passive radiators, so they are
simplified stand-ins built from the datasheet dimensions and my own measurements
([`ot19.py`](tools/render/ot19.py), [`ds115pr.py`](tools/render/ds115pr.py)), placed on the
seats the printed parts give them. They're for the pictures only.

| | |
|---|---|
| ![Front](docs/images/renders/front.png) | ![Rear](docs/images/renders/rear.png) |
| ![Side](docs/images/renders/side.png) | |

## Repository layout

| Folder | What's in it |
|---|---|
| `cad/` | R4.35 print plates, individual parts, Bambu projects, tilt stand, gasket templates, print guide |
| `dsp/` | DSP settings and the last audited SigmaStudio EQ list |
| `measurements/` | Measurement data behind the plots |
| `simulation/` | Pre-build waveguide and system models |
| `docs/` | Design history, tuning log and images |
| `tools/render/` | Scripts that produced the renders |

## Tools

Python (trimesh, manifold3d, shapely, numpy, matplotlib) for parametric CAD and checks,
OpenSCAD for early versions, Bambu Studio, REW with a UMIK-1, SigmaStudio, and Blender for
the renders. I worked through most of this with AI coding assistants, which
wrote and ran a lot of the CAD and analysis code while I made the design calls, printed,
assembled, measured and listened.

## License

[CC BY-NC 4.0](LICENSE): build one for yourself, learn from it and share changes with credit, but don't sell it.
