# Design history

Pria 5 went through 23 named versions (V1 to V5.2) and then 39 numbered revisions of V5.2:
four front and rear revisions (Front R2, R3, R3.1 and Rear R1) and R4.1 to R4.35. This page
lists them with the reason for each change. Dates are 2026. Where no date was recorded, the
row has none.

## V1 to V4.8: the enclosure

| Version | Date | What changed and why |
|---|---|---|
| V1 | Aug 30 | Withdrawn. The exported body had an open floor where two rounded-rectangle outlines didn't line up. |
| V2 | Aug 30 | Closed 4 mm floor and walls, heat-set insert interface (Ruthex RX-M3S×4), single rear passive radiator. An earlier V2 archive was dropped because its insert pockets were shallower than Ruthex's 5 mm minimum. |
| V2.1 to V2.6 | | Rear layout cleaned up, status LED moved, woofer seat support strategy, an automatic support preset, an optional magnetic fabric grille. |
| V3 | | Front and body merged into one shell: five required parts became four. |
| V3.1 | | Amplifier mount built in and radiator retention moved to the rear panel: four parts became three. |
| V3.2 | Aug 31 | Amplifier fixed to four blind insert pockets in the floor, no posts or tray. |
| V4 | | "Enclosure first": taller and narrower, 140 × 230 mm, with a replaceable waveguide cassette. |
| V4.1 | | My own compact waveguide for the OT19. |
| V4.2 | | Switched to a published third-party waveguide shape for the OT19. |
| V4.3 | | Waveguide made printable without supports. |
| V4.4 | | Waveguide compacted so the drivers sit closer (104 to 80 mm centre to centre), because the speaker sits above ear height. From here the surface no longer matches the published shape. |
| V4.5 to V4.8 | | Round waveguide mouths and front proportions (dual circles, golden ratio, a "phi" layout), driver spacing between 86 and 95 mm. |

## V5 to V5.2: the acoustics

| Version | Date | What changed and why |
|---|---|---|
| V5 | | Clean sheet from the drivers outward: a system model, a simulated elliptical waveguide (104 × 64 × 18 mm), a single radiator. Earlier prints became a measurement mule. |
| V5.1 | | Appearance only. Acoustics locked. |
| V5.2 | by Sep 4 | Two opposed side radiators in place of one rear one, a smaller analytic waveguide (98 × 50 × 16 mm), drivers 10 mm closer together. The model's predictions improved. The change notes say those numbers are only for ranking options. |
| Rear R1, R1.1 | Sep 4, 5 | The first rear print: the AUX nut couldn't engage, keys were missing, the panel warped. R1.1 added clearance. |
| S01, E02 | Sep 6 | A plinth for the electronics (rejected on looks) and a continuous-shell concept (not released). |
| Front R2 | Sep 7 | The first front failed to print: an unsupported 5.1 mm ledge at the waveguide opening. R2 uses a straight opening. |
| Front R3, R3.1 | Sep 8 | Body holes had no inserts, the woofer frame caught on its recess, tools couldn't reach. R3.1 widened the woofer recess to the manufacturer's drawing after a scan had read it too small. |

## R4: making it buildable

| Revision | Date | What changed and why |
|---|---|---|
| R4, R4.1 | Sep 9 | Redesign for assembly. I couldn't screw the amplifier down in the old bay and the stock wires didn't fit. The amplifier and controls now mount on the rear part, on the bench. Size approved at 142 × 230 × 180 mm. |
| R4.2 | Sep 9 | Engineering audit of the CAD and toolpaths: a sealed wire pass-through, radiator gasket channels, 45° roofs instead of flat bridges, more woofer clearance. |
| R4.3, R4.4 | | Every gasketed joint redesigned around one 1 × 8 mm foam tape. |
| R4.5 | | Adjustable tweeter clamp, thicker wire plate, longer rear screws. |
| R4.6, R4.7 | | Flush radiator covers. A magnetic frame over the six front screws. |
| R4.8 | Sep 15 to 26 | The waveguide's slender legs bent while printing, so it became a flat-backed guide on gussets with four M3 screws. Then fourteen print iterations (C1 to C14) against baffle and body warping: cooling, a reinforced core, removable anchors, a home-made warp simulation, joint changes. The physical fixes that mattered were a loose nozzle clamp and moving to the stock Bambu presets. C14 added 3 mm of depth. |
| First listen | Sep 28 | The full prototype was assembled and played. Measuring and tuning followed (see below). |
| R4.9 | Oct 4 | Rear cut from about 48 mm to 30 mm deep, bringing the cabinet to about 167 mm. |
| R4.10 to R4.13 | Oct 4 to 6 | The tweeter carrier, clamp and pressure ring merged into one retainer, then resized from caliper readings and test fits. |
| R4.14 | Oct 7 | Final assembly failures: amplifier plugs stuck out past the rear, glued magnets damaged the parts, inserts failed, radiator openings sagged. Fewer magnets of one size (38 to 16), printed insert starts, radiator covers dropped. |
| R4.15, R4.16 | Oct 7, 8 | Slimmer rear and lower circuit board posts. A wide body recess printed with removable comb supports. |
| R4.17 | Oct 8 | Volume knob removed: volume comes from the Bluetooth source. |
| R4.18 to R4.24 | Oct 12, 13 | Printed grilles. Magnets sealed into the print during a pause, which came out well. Support keys for the radiator openings. A press-in woofer cover. Magnet pockets with headroom after a layer shift. Rear vents styled like the grille. |
| R4.25, R4.26 | Oct 13 | Withdrawn. A printed check ring showed the radiator frame is about 4.65 mm thick where the drawing suggested 2.6 mm, so the existing seat was already flush. An O-ring waveguide seal was also dropped. |
| R4.27 | Oct 14 | A radiator support key fell over mid-print: braced keys. |
| R4.28, R4.29 | Oct 16 | A fabric grille, rejected. Back to a plain magnetic frame over the screws, drivers showing. |
| R4.30, R4.31 | Oct 16 to 18 | Magnet pockets: ribbed ones were too tight, plain ones let the toolhead pull the magnets out. Three test coupons settled on six barb tabs and a printed seating tool. |
| R4.32 | Oct 20 | An air leak at the tweeter: retainer 0.50 mm shallower, with shims. |
| R4.33 to R4.35 | Oct 20 | A four-hole wire plate couldn't be sealed. One hole, then sized for the actual four 2.2 mm wires in heat shrink, with a hot-glue cup. |

## Measuring and tuning (Sep 29 to Oct 2)

Equipment: a calibrated UMIK-1, REW, Bluetooth playback, and SigmaStudio through Dayton's KPX
programmer.

| Round | What changed |
|---|---|
| Baselines | Calibrated sweeps, with and without Windows input processing. Woofer and radiator nearfields: woofer dip at 50.5 Hz, radiator peaks at 49 Hz, so about 50 Hz tuning. Off-axis sweeps at ±30° horizontal and ±15° vertical. |
| Tuning01 | Tweeter cut at 3.5 kHz (Q 3, −2 dB). |
| Tuning02 to 04 | Tweeter delay tried at 4, 2 and 3 samples. Kept 3. |
| Tuning05 | Woofer boost at 70 Hz. Acoustic foam lining installed and the cabinet resealed. |
| Tuning06 to 08 | Level checks, the 70 Hz boost raised to +9 dB, a full-range sweep. |
| Tuning09 to 12 | Broad voicing, then EQ fitted to a 20-position room average (Tuning10), then 12-position averages (Tuning11, 12). Tuning12 measured 1 to 16 kHz within −0.82 / +0.89 dB of target. |
| Tuning13 to 19 | Gain staging, a linked peak limiter, a rejected full-drive bass setting that made an excursion-like sound, a 150 Hz split with a bass-only limiter, a low-volume bass lift. |
| Tuning20 to 26 | A gentler target slope (Tuning22, the last project file I audited), detector and level trials, a high-pass at 80 Hz tried and reverted. |
| Listening preset | Both mixers −4 dB, bass detector −3 dB, Single 1 −6 dB, high-pass back at 50 Hz. Set by ear after Tuning22. |
