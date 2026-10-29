# Renders

The images in `docs/images/renders/` come from the R4.35 STLs in `cad/parts/`.

1. Place the parts in one assembly frame (needs Python with numpy and trimesh):

   ```sh
   python3 tools/render/assemble.py cad/parts build/asm
   ```

   Add a path to Dayton Audio's ND91-4 model as a third argument to include the woofer. It
   isn't redistributed here.

2. Render with Blender 4.2 or newer (Cycles):

   ```sh
   blender -b -P tools/render/scene.py -- build/asm docs/images/renders hero,front,rear,side,exploded,cutaway 160
   ```

The poses follow the project's own build scripts and were checked against earlier assembly
meshes. The materials are approximate filament colours.

`assemble.py` also builds two stand-ins, because there's no vendor CAD for them:

- `ot19.py`: the OT19 tweeter, from Tymphany's datasheet drawing (33.4 mm frame, 31 mm ring,
  6.4 mm phase plug 8.6 mm proud, 17.1 mm body). It sits 0.70 mm behind the waveguide, where
  the compressed front seal puts it, with its back on the R4.32 retainer floor.
- `ds115pr.py`: the DS115-PR radiators, from Dayton's listed dimensions (115.57 mm frame,
  106.93 mm bolt circle, 29.72 mm depth) and my measurements (92 mm rubber, frame top 4.65 mm
  above the seat). They sit on the body's side seats, 4.8 mm below each face.

The rear housings, basket, screw heads and the added-mass washers are approximate. Don't use
any of these for fit.
