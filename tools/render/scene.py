"""Blender scene for Pria 5 renders. Run:
blender -b -P scene.py -- <asm_dir> <out_dir> <shot>[,<shot>...] [samples]
Geometry is the R4.35 release STLs placed by assemble.py; nothing is modelled here except the
studio backdrop. Front of the speaker faces +Y, up is +Z, units are metres."""
import bpy, sys, math, os
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
ASM, OUT, SHOTS = argv[0], argv[1], argv[2].split(',')
SAMPLES = int(argv[3]) if len(argv) > 3 else 160
os.makedirs(OUT, exist_ok=True)

COLORS = {  # base colour, roughness
    'white': ((0.80, 0.78, 0.74, 1), 0.55),
    'orange': ((0.62, 0.115, 0.03, 1), 0.5),
    'black': ((0.018, 0.018, 0.02, 1), 0.6),
    'driver': ((0.03, 0.03, 0.033, 1), 0.35),
    'ring': ((0.06, 0.06, 0.065, 1), 0.3),
    'plug': ((0.02, 0.02, 0.022, 1), 0.2),
    'steel': ((0.55, 0.55, 0.56, 1), 0.3),
}
PARTS = {'body': 'white', 'rear': 'white', 'baffle': 'orange', 'frame': 'orange', 'retainer': 'orange',
         'waveguide': 'orange', 'woofer_cover': 'orange', 'woofer_nd91': 'driver',
         'ot19_body': 'driver', 'ot19_ring': 'ring', 'ot19_plug': 'plug'}
for _side in ('left', 'right'):
    PARTS.update({f'pr_frame_{_side}': 'driver', f'pr_gasket_{_side}': 'black', f'pr_rubber_{_side}': 'ring',
                  f'pr_diaphragm_{_side}': 'plug', f'pr_mass_{_side}': 'steel'})
# exploded offsets along the speaker axis (mm, + = toward the listener)
EXPLODE = {'frame': 300, 'woofer_cover': 230, 'waveguide': 200, 'woofer_nd91': 160, 'baffle': 100,
           'ot19_body': 70, 'ot19_ring': 70, 'ot19_plug': 70, 'retainer': 45, 'body': 0, 'rear': -90}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    try:
        prefs.compute_device_type = 'METAL'; prefs.get_devices()
        for d in prefs.devices: d.use = True
        sc.cycles.device = 'GPU'
    except Exception:
        pass
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1600, 1200
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.exposure = float(os.environ.get('EXPOSURE', '-4.0'))
    sc.view_settings.look = 'AgX - Medium High Contrast'
    return sc


def material(name, kind):
    col, rough = COLORS[kind]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = rough
    if kind == 'white':  # faint marble fleck, like the Polymaker Marble filament
        noise = nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 900.0
        noise.inputs['Detail'].default_value = 2.0
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = 0.62; ramp.color_ramp.elements[0].color = col
        ramp.color_ramp.elements[1].position = 0.66; ramp.color_ramp.elements[1].color = (0.25, 0.24, 0.23, 1)
        nt.links.new(noise.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    else:
        bsdf.inputs['Base Color'].default_value = col
        if kind == 'steel':
            bsdf.inputs['Metallic'].default_value = 1.0
    return m


def load_parts(explode=False, cut=False):
    root = bpy.data.objects.new('speaker', None); bpy.context.collection.objects.link(root)
    root.rotation_euler = (math.radians(90), 0, 0); root.scale = (0.001,) * 3
    objs = {}
    for name, kind in PARTS.items():
        path = os.path.join(ASM, name + '.stl')
        if not os.path.exists(path):  # the woofer, tweeter and radiator meshes are optional
            continue
        bpy.ops.wm.stl_import(filepath=path)
        o = bpy.context.selected_objects[0]; o.name = name
        o.data.materials.append(material(name + '_mat', kind))
        o.parent = root
        if explode and name.startswith('pr_'):          # radiators move out sideways
            o.location.x = 110 if name.endswith('_right') else -110
        elif explode: o.location.z = -EXPLODE[name]          # asm -Z is toward the listener
        for p in o.data.polygons: p.use_smooth = False
        objs[name] = o
    if cut:  # section on the vertical centre plane: remove the +X half (asm frame)
        cutter = bpy.data.objects.new('cutter', bpy.data.meshes.new('cutter')); bpy.context.collection.objects.link(cutter)
        import bmesh
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(cutter.data); bm.free()
        cutter.parent = root; cutter.scale = (400, 600, 600); cutter.location = (200 + 0.0, 115, 70)
        cutter.hide_render = True; cutter.display_type = 'WIRE'
        for name, o in list(objs.items()):
            xs = [c[0] for c in o.bound_box]                # object coords are assembly mm
            if min(xs) >= 0:                                # wholly in the removed half
                bpy.data.objects.remove(o); objs.pop(name); continue
            if max(xs) <= 0:
                continue
            mod = o.modifiers.new('cut', 'BOOLEAN'); mod.operation = 'DIFFERENCE'; mod.object = cutter
            mod.solver = 'EXACT'
    bpy.context.view_layer.update()
    return root, objs


def studio(sc, floor_z, d):
    world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.9, 0.9, 0.9, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.25
    # sweep backdrop
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, floor_z))
    fl = bpy.context.object; fl.name = 'floor'
    m = bpy.data.materials.new('floor'); m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.86, 0.86, 0.85, 1)
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
    fl.data.materials.append(m)
    # backdrop wall 1.2 m behind the speaker as seen from the camera, facing it
    h = Vector((d[0], d[1], 0)).normalized()
    bpy.ops.mesh.primitive_plane_add(size=20, location=(-h.x * 1.2, -h.y * 1.2, floor_z + 10),
                                     rotation=(math.radians(90), 0, math.atan2(h.x, -h.y)))
    bpy.context.object.data.materials.append(m)
    def area(loc, energy, size, color=(1, 1, 1)):
        bpy.ops.object.light_add(type='AREA', location=loc); l = bpy.context.object
        l.data.energy = energy; l.data.size = size; l.data.color = color
        d = Vector((0, 0, 0.12)) - Vector(loc); l.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    area((0.6, 0.9, 0.9), 260, 0.9)            # key, front right high
    area((-0.9, 0.5, 0.4), 90, 1.2, (0.92, 0.95, 1))  # fill, left
    area((-0.3, -0.8, 0.9), 160, 0.8)          # rim from behind
    area((0, 0.2, 1.4), 60, 1.5)               # top soft


def camera(sc, loc, target, lens=70, ortho=None):
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    if ortho:
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho
    cam.data.dof.use_dof = False
    sc.camera = cam
    return cam


def frame_target(objs):
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in objs.values():
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    return lo, hi


SHOT_DEFS = {
    # name: (explode, cut, camera direction from centre (front=+Y), distance, lens, resolution, ortho)
    'hero': (False, False, (0.55, 1.0, 0.32), 1.25, 85, (1600, 1200), None),
    'front': (False, False, (0, 1, 0.08), 1.6, 100, (1200, 1600), 0.30),
    'rear': (False, False, (-0.6, -1.0, 0.35), 1.25, 85, (1600, 1200), None),
    'side': (False, False, (1, 0.05, 0.12), 1.3, 85, (1600, 1200), None),
    'exploded': (True, False, (1.25, 0.55, 0.38), 1.9, 70, (1800, 1100), None),
    'cutaway': (False, True, (1.0, 0.7, 0.3), 1.25, 80, (1600, 1200), None),
}

for shot in SHOTS:
    explode, cut, d, dist, lens, res, ortho = SHOT_DEFS[shot]
    sc = reset(); k = float(os.environ.get('RES', '1')); sc.render.resolution_x, sc.render.resolution_y = int(res[0]*k), int(res[1]*k)
    print('DEVICE', sc.cycles.device, [d.name for d in bpy.context.preferences.addons['cycles'].preferences.devices if d.use])
    root, objs = load_parts(explode, cut)
    lo, hi = frame_target(objs)
    centre = (lo + hi) / 2
    studio(sc, lo.z, d)
    dv = Vector(d).normalized()
    camera(sc, centre + dv * dist, centre, lens, ortho)
    sc.render.filepath = os.path.join(OUT, f'{shot}.png')
    bpy.ops.render.render(write_still=True)
    print('RENDERED', shot, tuple(round(v, 3) for v in lo), tuple(round(v, 3) for v in hi))
