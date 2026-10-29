# Printing Pria 5 (R4.35)

Five plates. I print them on a Bambu Lab X2D with a 0.4 mm nozzle, using these settings on
every part:

- process "0.20mm Standard", 3 walls, 30% sparse infill
- no brim, supports off (the support that's needed is built into the models)
- PLA (I use Polymaker PLA Marble)

Keep 0.20 mm layers. The built-in support tips and the magnet pause layers depend on them.

| Plate | File in `plates/` | Colour I use | Pause |
|---|---|---|---|
| 1 | Baffle, tweeter retainer, wire plate, gasket aids, magnet seating tool | Orange | Before layer 44: four magnets, marked face **up** |
| 2 | Magnetic front frame | Orange | Before layer 17: four magnets, marked face **down** |
| 3 | Body, with removable comb supports and two braced support keys for the radiator openings | White | none |
| 4 | Rear, with the amplifier bay and vents | White | none |
| 5 | Waveguide and woofer cover | Orange | none |

`bambu/` has Bambu Studio projects for plates 1 and 2 with the pauses already in the G-code,
plus single-part projects for reprints. Plate 1 takes about 3 h 44 min and 179 g; plate 2
about 53 min and 36 g (Bambu Studio estimates).

`parts/` has every part on its own, for reprinting one piece or remixing.

## Magnet pauses

You need eight 8 × 2 mm disc magnets. Mark one face of each so the polarity is consistent.

**Plate 1, before layer 44.** The seating tool is the small round knob on plate 1; it finishes
long before the pause. Drop a magnet into each pocket, marked face up. Put the tool's stem on
it and press until the knob sits flat on the baffle. The magnet clicks past six small tabs that
stop the toolhead pulling it out. Check all four are flat and below the tabs, then resume.

**Plate 2, before layer 17.** Drop each magnet in flat, marked face down. The steel build plate
holds it in place. Resume.

Before assembling, hold the frame to the baffle and check that all four corners attract.

## After printing

- Snap the three combs off the inside of the body and pull the two support keys out of the
  radiator openings. They are only there to hold up overhangs while printing.
- The tweeter retainer ships with 0.2 mm and 0.4 mm shims, for when the tweeter doesn't seat
  firmly.

## Sealing the speaker wires

The four speaker wires (2.2 mm each) pass from the amplifier bay into the acoustic chamber
through the wire plate. It has one 6.4 mm hole and a short cup on the amplifier side.

1. Hold the four wires together and slide about 25 mm of 1/4 in heat shrink over them where
   they'll pass through the plate. Push a little hot glue into the bundle under the tube first,
   then shrink it. The glue fills the gaps between the round wires.
2. Push the jacketed bundle through the plate from the flat side, before soldering the wires
   to the drivers. Leave a loose service loop.
3. With the cup facing up, fill it with hot glue around the jacket. A low-temperature glue gun
   is kinder to PLA.
4. Lay 8 mm foam tape in the plate's channel and screw it over the bulkhead opening with two
   M3 × 8 screws.

## Other files

- `gaskets/`: 1:1 cut templates (SVG and DXF) for the foam gaskets.
- `optional_checks/`: two small test prints, one for the sealed magnet pocket and one for the
  body recess supports, if you want to check your printer before a full plate.
- `stand/`: the tilt stand at 15°, 18° and 22°. One per speaker, printed flat with no supports.

## Status

These parts are checked in CAD and in the slicer. I've printed and used the body. The baffle
magnet pocket was proven in a test coupon, but the full R4.31 to R4.35 front parts, the frame
and the tilt stand haven't been printed yet. Fit, sealing and temperature still need checking on
real prints.
