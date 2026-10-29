"""Place the R4.35 release parts in one assembly frame for rendering.

Frame: X across the front, Y up, -Z toward the listener (the frame the project's own QA code uses).
The poses follow the project's build scripts and were checked against the earlier R4.6/R4.8
assembly meshes by nearest-point distance. The printed parts come from cad/parts/ unchanged; only
the PR support keys, the comb supports and zero-volume skins are dropped from the body, since they
are print aids that are removed after printing.

    python3 tools/render/assemble.py cad/parts build/asm [path/to/ND91-4.stl]

The woofer mesh is optional. It is Dayton Audio's reference model and is not redistributed here.
The tweeter is a simplified stand-in built by ot19.py from the datasheet drawing.
"""
import json, os, sys
import numpy as np
import trimesh as tm

PARTS, OUT = sys.argv[1], sys.argv[2]
ND91 = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(OUT, exist_ok=True)
T = lambda x, y, z: tm.transformations.translation_matrix((x, y, z))
Ry = lambda d: tm.transformations.rotation_matrix(np.radians(d), (0, 1, 0))
Rx = lambda d: tm.transformations.rotation_matrix(np.radians(d), (1, 0, 0))
load = lambda n: tm.load_mesh(os.path.join(PARTS, n))

poses = {}
b = load('body_with_removable_supports.stl')
poses['body'] = (max(b.split(only_watertight=False), key=lambda s: s.volume), T(0, 0, 125) @ Ry(180) @ T(-128, -13, 0))
poses['rear'] = (load('rear_grille_vents.stl'), T(0, 0, 155) @ Ry(180) @ T(-128, -13, 0))
poses['baffle'] = (load('baffle.stl'), Ry(180) @ T(-128, -13, 0))              # printed face up
poses['frame'] = (load('magnetic_frame.stl'), T(0, 0, -13.2) @ T(-128, -13, 0))  # printed face down; 1.2 mm proud of the face
wg = load('waveguide.stl'); c = wg.bounds.mean(0)
poses['waveguide'] = (wg, T(0, 163.2, -4) @ Ry(180) @ T(-c[0], -c[1], -8))       # tweeter axis Y163.2, mouth flush with the face
poses['woofer_cover'] = (load('woofer_cover.stl'), T(0, 87.6, -12) @ T(-128, -128, 0))  # woofer axis Y87.6, flush with the face
r = load('retainer.stl'); c = r.bounds.mean(0)
poses['retainer'] = (r, T(0, 163.2, 4 + r.bounds[1, 2]) @ Ry(180) @ T(-c[0], -c[1], 0))
# simplified tweeter (tools/render/ot19.py): front face 0.70 mm behind the waveguide (the compressed
# front seal), back on the R4.32 retainer floor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ot19
for k, m in ot19.build().items():
    poses[k] = (m, T(0, 163.2, 4 + 0.70))
# simplified passive radiators (tools/render/ds115pr.py) on the body's side seats: axis Y127 Z60.7,
# seat X+-66.2, 4.8 mm below each side face (measured from body.stl)
import ds115pr
for sx, side in ((1, 'right'), (-1, 'left')):
    for k, m in ds115pr.build().items():
        poses[f'{k}_{side}'] = (m, T(sx * 66.2, 127.0, 60.7) @ Ry(90 * sx))
if ND91:
    poses['woofer_nd91'] = (tm.load_mesh(ND91), T(0, 87.6, -8.5) @ Rx(-90))     # frame top 3 mm below the face

info = {}
for k, (m, M) in poses.items():
    m = m.copy(); m.apply_transform(M); m.export(os.path.join(OUT, k + '.stl'))
    info[k] = m.bounds.round(2).tolist()
json.dump(info, open(os.path.join(OUT, 'bounds.json'), 'w'), indent=1)
print(json.dumps(info))
