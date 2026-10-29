"""Simplified Dayton Audio DS115-PR passive radiator for the renders (no vendor CAD is used).

Dimensions from Dayton's listing as recorded in the project: frame OD 115.57 mm, bolt circle
106.93 mm, depth 29.72 mm. From my own measurements: the rubber surround is 92 mm across, and the
frame top sits 4.65 mm above the printed seat (frame plus foam gasket). The surround's height above
the frame is the drawing's 3.7 mm, which I haven't checked. The front is a paper cone with a centre
cap, and the added mass (11 g per radiator, including the screw) hangs on Dayton's rear-mounted
mass screw, inside the cabinet. The cone depth, basket shape, screw heads and washer stack are
approximate. Use it for pictures only, never for fit.

Local frame: axis along Z, the printed seat at Z=0, the diaphragm toward +Z (out of the cabinet),
the basket toward -Z (inside it). build() returns the parts as separate meshes.
"""
import numpy as np
import trimesh as tm

FRAME_R, BOLT_R, DEPTH = 115.57 / 2, 106.93 / 2, 29.72
RUBBER_R, FRAME_TOP, ROLL_UP = 92.0 / 2, 4.65, 3.7
GASKET = 0.7
N = 192


def revolve(rz, sections=N):
    return tm.creation.revolve(np.asarray(rz, float), sections=sections)


def build():
    inner = RUBBER_R - 0.5
    # stamped frame: screw flange on the gasket, a raised lip that the surround is glued to, and
    # the basket running back into the cabinet
    frame = revolve([(inner, FRAME_TOP), (FRAME_R - 1.0, FRAME_TOP), (FRAME_R, FRAME_TOP - 1.0),
                     (FRAME_R, GASKET), (inner + 2.0, GASKET), (inner - 1.0, -4.0), (30.0, -DEPTH + 1.5),
                     (24.0, -DEPTH), (22.5, -DEPTH), (28.5, -DEPTH + 2.5), (inner - 2.0, -4.0), (inner - 1.0, FRAME_TOP - 1.2),
                     (inner, FRAME_TOP)])
    gasket = revolve([(inner + 2.0, 0.0), (FRAME_R - 1.5, 0.0), (FRAME_R - 1.5, GASKET), (inner + 2.0, GASKET), (inner + 2.0, 0.0)])
    # rubber half-roll from the frame lip inward, peaking ROLL_UP above the frame top
    roll_w = 7.0
    th = np.linspace(0, np.pi, 48)
    rubber = revolve([(RUBBER_R, FRAME_TOP)] +
                     [(RUBBER_R - roll_w / 2 + roll_w / 2 * np.cos(a), FRAME_TOP + ROLL_UP * np.sin(a)) for a in th] +
                     [(RUBBER_R - roll_w, FRAME_TOP + 0.4)])
    # paper cone dishing into the cabinet, closed by a shallow centre cap
    cone_r, cap_r, cone_depth = RUBBER_R - roll_w, 13.0, 7.0
    neck = FRAME_TOP + 0.4 - cone_depth
    th = np.linspace(0, np.pi / 2, 16)
    diaphragm = revolve([(0, neck + 2.6)] + [(cap_r * np.sin(a), neck + 2.6 * np.cos(a)) for a in th[1:]] +
                        [(cone_r, FRAME_TOP + 0.4), (cone_r, FRAME_TOP - 0.2), (cap_r, neck - 0.6), (0, neck - 0.6)])
    # added mass on Dayton's rear-mounted screw, behind the cone: two washers and the screw head
    back = neck - 0.6
    mass = tm.util.concatenate([
        tm.creation.cylinder(radius=9.0, height=1.6, sections=96).apply_translation((0, 0, back - 0.8)),
        tm.creation.cylinder(radius=7.5, height=1.6, sections=96).apply_translation((0, 0, back - 2.4)),
        tm.creation.icosphere(subdivisions=3, radius=3.6).apply_scale((1, 1, 0.45)).apply_translation((0, 0, back - 3.2)),
    ])
    screws = []
    for a in np.radians([45, 135, 225, 315]):
        head = tm.creation.icosphere(subdivisions=3, radius=2.8).apply_scale((1, 1, 0.5))
        screws.append(head.apply_translation((BOLT_R * np.cos(a), BOLT_R * np.sin(a), FRAME_TOP - 1.0)))
    return {'pr_frame': tm.util.concatenate([frame] + screws), 'pr_gasket': gasket, 'pr_rubber': rubber,
            'pr_diaphragm': diaphragm, 'pr_mass': mass}


if __name__ == '__main__':
    import os, sys
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    for name, m in build().items():
        m.export(os.path.join(out, name + '.stl'))
        print(name, m.bounds.round(2).tolist())
