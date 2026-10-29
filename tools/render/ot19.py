"""Simplified OT19NC00-04 tweeter for the renders (no vendor CAD exists for it).

Built by revolving a profile drawn from Tymphany's datasheet drawing: 33.4 mm frame, 31 mm front
ring, 6.4 mm phase plug standing 8.6 mm proud of the front face (25.7 mm overall less the 17.1 mm
body), 2.4 cm effective radiating diameter, and two 2.8 x 0.5 mm terminals. The depth from the front
face to the back where the retainer floor touches it is the project's R4.32 value, 16.37 mm.
The rear housing curve is approximate. Use it for pictures only, never for fit.

Local frame: axis along Z, front face at Z=0, the phase plug toward -Z, the housing toward +Z.
build() returns the body, radiating ring and phase plug as separate meshes. Run on its own, it
writes them to the given folder as ot19_body.stl, ot19_ring.stl and ot19_plug.stl.
"""
import os, sys
import numpy as np
import trimesh as tm

FRAME_R, RING_R, PLUG_R = 33.4 / 2, 31.0 / 2, 6.4 / 2
PLUG_PROUD, DEPTH = 25.7 - 17.1, 16.37
RAD_IN, RAD_OUT = 4.6, 12.0          # radiating ring, 2.4 cm effective diameter
N = 160


def revolve(rz):
    """rz: (radius, z) points from the axis outward and back to the axis, open polyline."""
    return tm.creation.revolve(np.asarray(rz, float), sections=N)


# housing and front frame: frame lip at Z0..1.4, a shoulder down to the 31 mm ring face, then the
# rear housing narrowing to a rounded back at DEPTH
t = np.linspace(0, np.pi / 2, 12)
back = [(10.5 + 2.5 * np.cos(a), DEPTH - 2.5 + 2.5 * np.sin(a)) for a in t][::-1]
body = revolve([(0, -0.3), (RAD_IN, -0.3), (RAD_IN, 0.4), (RAD_OUT + 0.4, 0.4), (RAD_OUT + 0.4, -0.6),
                (RING_R, -0.6), (RING_R, 0.0), (FRAME_R, 0.0), (FRAME_R, 1.4), (FRAME_R - 1.2, 2.6),
                (14.6, 6.0), (13.6, 11.0)] + back + [(0, DEPTH)])
# terminals: two tabs on opposite sides of the housing
for s in (-1, 1):
    tab = tm.creation.box((6.4, 0.5, 2.8))
    tab.apply_translation((s * (13.6 + 2.6), 0, 10.0))
    body = tm.util.concatenate([body, tab])
# radiating ring: a shallow convex toroid between RAD_IN and RAD_OUT
th = np.linspace(0, np.pi, 40)
mid, half = (RAD_IN + RAD_OUT) / 2, (RAD_OUT - RAD_IN) / 2
ring = revolve([(RAD_IN, 0.4)] + [(mid - half * np.cos(a), 0.4 - 1.9 * np.sin(a)) for a in th] + [(RAD_OUT, 0.4)])
# phase plug: a bullet, flat base on the face, rounded tip PLUG_PROUD forward
u = np.linspace(0, 1, 30)
plug = revolve([(0, 0.0), (PLUG_R, 0.0)] + [(PLUG_R * np.sqrt(1 - x ** 2), -PLUG_PROUD * x ** 0.85) for x in u[1:]])


def build():
    return {'ot19_body': body, 'ot19_ring': ring, 'ot19_plug': plug}


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    for name, m in build().items():
        m.export(os.path.join(out, name + '.stl'))
        print(name, m.bounds.round(2).tolist())
