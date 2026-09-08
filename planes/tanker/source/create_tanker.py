"""Build with: blender --background --python planes/tanker/source/create_tanker.py

Uses only Blender's bundled Python API. Rebuilding replaces this asset's outputs.
"""

import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ASSET = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
aircraft = bpy.data.collections.new('Tanker')
scene.collection.children.link(aircraft)
studio = bpy.data.collections.new('Preview Studio (not exported)')
scene.collection.children.link(studio)
root = bpy.data.objects.new('tanker', None)
aircraft.objects.link(root)
root['plane_id'] = 'tanker'
root['wingspan_m'] = 40.0
root['source_axes'] = '+X nose, +Y right wing, +Z up'
root['origin'] = 'Nominal center of gravity; visual placeholder'


def material(name, color, metallic=0.0, roughness=0.4):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = roughness
    return mat


paint = material('Airframe | pearl gray', (0.62, 0.70, 0.73), 0.3, 0.32)
teal = material('Livery | deep teal', (0.018, 0.18, 0.21), 0.35, 0.3)
orange = material('Livery | safety orange', (0.95, 0.22, 0.035), 0.15, 0.35)
glass = material('Canopy | smoked blue', (0.025, 0.08, 0.13), 0.65, 0.16)
metal = material('Engine | titanium', (0.19, 0.22, 0.24), 0.8, 0.32)
dark = material('Engine | cavity', (0.008, 0.012, 0.016), 0.1, 0.65)


def mesh_object(name, vertices, faces, mat, smooth=False):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    aircraft.objects.link(obj)
    obj.parent = root
    obj.data.materials.append(mat)
    for face in mesh.polygons:
        face.use_smooth = smooth
    return obj


def rod(name, start, end, radius, mat, end_radius=None):
    start, end = Vector(start), Vector(end)
    bpy.ops.mesh.primitive_cone_add(
        vertices=24, radius1=radius,
        radius2=radius if end_radius is None else end_radius,
        depth=(end - start).length, location=(start + end) / 2,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = (end - start).to_track_quat('Z', 'Y').to_euler()
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    aircraft.objects.link(obj)
    obj.parent = root
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = len(face.vertices) == 4
    return obj


def loft(name, stations, mat, y=0.0, segments=32):
    """Closed elliptical sections: (longitudinal X, half-width, half-height, Z)."""
    verts = [
        (x, y + ry * math.cos(2 * math.pi * i / segments),
         z + rz * math.sin(2 * math.pi * i / segments))
        for x, ry, rz, z in stations for i in range(segments)
    ]
    faces = [tuple(reversed(range(segments)))]
    for j in range(len(stations) - 1):
        for i in range(segments):
            a = j * segments + i
            b = j * segments + (i + 1) % segments
            faces.append((a, b, b + segments, a + segments))
    faces.append(tuple((len(stations) - 1) * segments + i for i in range(segments)))
    return mesh_object(name, verts, faces, mat, smooth=True)


def slab(name, outline, thickness, mat, axis='Z'):
    delta = Vector((0, 0, thickness / 2) if axis == 'Z' else (0, thickness / 2, 0))
    verts = [tuple(Vector(p) + sign * delta) for sign in (-1, 1) for p in outline]
    n = len(outline)
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    obj = mesh_object(name, verts, faces, mat)
    bevel = obj.modifiers.new('Soft manufactured edges', 'BEVEL')
    bevel.width = min(0.08, thickness * 0.2)
    bevel.segments = 2
    obj.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
    return obj

# Artistic transport proportions; the 40 m span comes from tanker.plane.ron.
fuselage_stations = [
    (-20.0, 0.10, 0.16, 0.55), (-18.5, 0.65, 0.65, 0.35),
    (-15.0, 1.45, 1.45, 0.1), (-10.0, 1.85, 1.85, 0),
    (8.5, 1.85, 1.85, 0), (13.0, 1.72, 1.73, -0.03),
    (15.5, 1.32, 1.36, -0.15), (17.2, 0.87, 0.92, -0.35),
    (18.5, 0.35, 0.43, -0.49), (19.0, 0.035, 0.06, -0.52),
]
loft('Fuselage', fuselage_stations, paint, segments=48)
loft('Nose radome', [
    (17.2, 0.88, 0.93, -0.35), (18.5, 0.36, 0.44, -0.49),
    (19.015, 0.035, 0.06, -0.52),
], teal, segments=48)


def skin_point(x, angle, side, lift=0.025):
    """Sample the fuselage loft for flush decorative panels."""
    for a, b in zip(fuselage_stations, fuselage_stations[1:]):
        if a[0] <= x <= b[0]:
            t = (x - a[0]) / (b[0] - a[0])
            ry, rz, z = [a[i] + t * (b[i] - a[i]) for i in (1, 2, 3)]
            return (x, side * (ry + lift) * math.cos(angle),
                    z + (rz + lift) * math.sin(angle))
    raise ValueError(x)


for side, sign in [('right', 1), ('left', -1)]:
    def mirror(points):
        return [(x, sign * y, z) for x, y, z in points]

    # Cockpit glazing follows the tapered nose, with narrow painted mullions.
    for i, (back, front) in enumerate([(12.6, 13.8), (13.94, 15.35), (15.49, 16.55)]):
        xs = [back] + [s[0] for s in fuselage_stations if back < s[0] < front] + [front]
        angles = [0.34 + j * (0.87 - 0.34) / 6 for j in range(7)]
        verts = [skin_point(x, angle, sign) for x in xs for angle in angles]
        faces = [(j*7+k, (j+1)*7+k, (j+1)*7+k+1, j*7+k+1)
                 for j in range(len(xs)-1) for k in range(6)]
        mesh_object(f'Cockpit window_{side}_{i + 1}', verts, faces, glass)

    # A thin stripe makes the transport fuselage readable at a distance.
    xs = [-15, -10, 8.5, 12.2]
    verts = [skin_point(x, angle, sign) for x in xs for angle in (0.03, 0.15)]
    faces = [(2*i, 2*i+2, 2*i+3, 2*i+1) for i in range(len(xs)-1)]
    mesh_object('Fuselage stripe_' + side, verts, faces, teal)

    slab('Wing_' + side, mirror([
        (4.0, 1.25, -0.65), (-5.9, 20.0, 0.72),
        (-7.45, 20.0, 0.72), (-6.4, 10.0, -0.01),
        (-4.1, 1.25, -0.65),
    ]), 0.30, paint)
    slab('Wingtip_' + side, mirror([
        (-5.48, 19.2, 0.817), (-5.9, 20.0, 0.875),
        (-7.45, 20.0, 0.875), (-7.366, 19.2, 0.817),
    ]), 0.018, orange)
    slab('Aileron marking_' + side, mirror([
        (-6.25, 13.0, 0.364), (-6.9, 18.6, 0.773),
        (-7.25, 18.6, 0.773), (-6.65, 13.0, 0.364),
    ]), 0.012, teal)
    slab('Flap marking_' + side, mirror([
        (-3.5, 3.0, -0.352), (-5.5, 9.5, 0.123),
        (-6.22, 9.5, 0.123), (-4.48, 3.0, -0.352),
    ]), 0.012, teal)
    slab('Horizontal stabilizer_' + side, mirror([
        (-12.5, 0.55, 0.8), (-16.5, 7.8, 1.34),
        (-18.9, 7.8, 1.34), (-18.5, 0.55, 0.8),
    ]), 0.22, paint)
    slab('Elevator marking_' + side, mirror([
        (-17.6, 2.0, 1.03), (-18.2, 7.5, 1.44),
        (-18.86, 7.5, 1.44), (-18.53, 2.0, 1.03),
    ]), 0.012, teal)

    for engine, x, y, z in [('inner', 2.0, 6.4, -2.0), ('outer', -1.6, 12.6, -1.55)]:
        suffix = f'{side}_{engine}'
        wing_z = -0.65 + (y - 1.25) * 1.37 / 18.75
        slab('Engine pylon_' + suffix, mirror([
            (x + 0.6, y, z + 0.6), (x + 0.3, y, wing_z),
            (x - 1.7, y, wing_z), (x - 1.7, y, z + 0.6),
        ]), 0.25, teal, axis='Y')
        # Hollow front lip leads to a recessed fan; the aft nozzle is separate.
        loft('Engine nacelle_' + suffix, [
            (x-2.3, .65, .65, z), (x-1.6, .99, .99, z),
            (x+.7, 1.03, 1.03, z), (x+1.55, .94, .94, z),
            (x+1.6, .79, .79, z), (x+1.13, .76, .76, z),
        ], paint, y=sign*y)
        loft('Intake rim_' + suffix, [
            (x+1.40, .957, .957, z), (x+1.56, .95, .95, z),
            (x+1.62, .79, .79, z), (x+1.44, .78, .78, z),
        ], metal, y=sign*y)
        loft('Recessed fan_' + suffix, [
            (x+1.10, .762, .762, z), (x+1.12, .762, .762, z),
        ], dark, y=sign*y)
        for blade in range(12):
            angle = 2 * math.pi * blade / 12
            vertices = [(x+1.135, sign*y + r*math.cos(angle+a),
                         z + r*math.sin(angle+a))
                        for r, a in [(.23, 0), (.71, .10), (.71, .29), (.23, .32)]]
            mesh_object(f'Fan blade_{suffix}_{blade+1:02}', vertices, [(0,1,2,3)], metal)
        loft('Fan hub_' + suffix, [
            (x+1.13, .23, .23, z), (x+1.48, .045, .045, z),
        ], metal, y=sign*y, segments=24)
        loft('Exhaust nozzle_' + suffix, [
            (x-2.0, .65, .65, z), (x-2.65, .51, .51, z),
            (x-2.65, .41, .41, z), (x-2.3, .40, .40, z),
        ], metal, y=sign*y)
        loft('Exhaust cavity_' + suffix, [
            (x-2.31, .402, .402, z), (x-2.29, .402, .402, z),
        ], dark, y=sign*y)

slab('Vertical stabilizer', [
    (-11.0, 0, 1.25), (-15.4, 0, 7.3), (-18.0, 0, 7.3),
    (-19.1, 0, 0.65),
], .30, teal, axis='Y')
slab('Fin cap', [
    (-15.04, 0, 6.8), (-15.4, 0, 7.3), (-18.0, 0, 7.3),
    (-18.083, 0, 6.8),
], .315, orange, axis='Y')
slab('Rudder marking', [
    (-17.4, 0, 2.0), (-17.15, 0, 6.55), (-18.04, 0, 6.55),
    (-18.8, 0, 2.0),
], .32, paint, axis='Y')

# Deployed centerline flying boom, with a narrow telescoping tip and V fins.
loft('Boom pivot fairing', [
    (-16.2, .12, .12, -.85), (-14.8, .48, .48, -1.1),
    (-13.7, .36, .36, -1.25),
], teal)
rod('Refueling boom', (-14.9, 0, -1.25), (-21.6, 0, -3.45), .26, paint, .19)
rod('Boom telescoping tube', (-21.5, 0, -3.42), (-24.1, 0, -4.28), .115, metal, .10)
rod('Boom nozzle', (-23.8, 0, -4.18), (-24.4, 0, -4.38), .15, orange, .12)
for side, sign in [('right', 1), ('left', -1)]:
    slab('Boom control fin_' + side, [
        (-19.25, sign*.12, -2.62), (-20.0, sign*1.55, -1.65),
        (-21.2, sign*1.55, -1.65), (-20.8, sign*.12, -3.16),
    ], .09, teal)

# Bake modifiers and validate the exported aircraft, including its world-space scale.
bpy.ops.object.select_all(action='DESELECT')
for obj in list(aircraft.objects):
    if obj.type == 'MESH':
        bpy.context.view_layer.objects.active = obj
        for modifier in list(obj.modifiers):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        obj.data.calc_loop_triangles()
bpy.context.view_layer.update()
meshes = [obj for obj in aircraft.objects if obj.type == 'MESH']
points = [obj.matrix_world @ v.co for obj in meshes for v in obj.data.vertices]
span = max(v.y for v in points) - min(v.y for v in points)
assert abs(span - 40.0) < 0.001, span
assert all(math.isfinite(c) for v in points for c in v)
assert all(obj.parent == root for obj in meshes)
triangles = sum(len(obj.data.loop_triangles) for obj in meshes)
print(f'ASSET CHECK: {len(meshes)} meshes, {triangles} triangles, span {span:.3f} m')
exports = ASSET / 'exports'
exports.mkdir(exist_ok=True)
for obj in aircraft.objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = root
bpy.ops.export_scene.gltf(
    filepath=str(exports / 'tanker.glb'), export_format='GLB',
    use_selection=True, export_yup=True, export_extras=True,
    export_cameras=False, export_lights=False,
)


def studio_object(obj):
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    studio.objects.link(obj)


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


bpy.ops.mesh.primitive_plane_add(size=500, location=(0, 0, -5.6))
floor = bpy.context.object
floor.name = 'Studio floor'
floor.data.materials.append(material('Studio | slate', (.045, .068, .09), roughness=.85))
studio_object(floor)
bpy.ops.object.camera_add(location=(49, -66, 39))
camera = bpy.context.object
camera.name = 'Preview camera'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 58
aim(camera, (-2, 0, .1))
studio_object(camera)
scene.camera = camera
for name, location, energy, size in [
    ('Key', (16, -24, 48), 36800, 32),
    ('Fill', (4, 32, 28), 27200, 28),
    ('Rim', (-32, -8, 36), 41600, 24),
]:
    bpy.ops.object.light_add(type='AREA', location=location)
    lamp = bpy.context.object
    lamp.name = name
    lamp.data.energy = energy
    lamp.data.shape = 'DISK'
    lamp.data.size = size
    aim(lamp, (0, 0, 0))
    studio_object(lamp)
scene.world = bpy.data.worlds.new('Studio world')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.22, .28, .36, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .5
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x = 1400
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(exports / 'tanker_preview.png')
scene.view_settings.view_transform = 'AgX'
for obj in studio.objects:
    obj.hide_set(True)
bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
bpy.context.view_layer.objects.active = root
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_rotation = camera.rotation_euler.to_quaternion()
            area.spaces.active.region_3d.view_distance = 75
            area.spaces.active.region_3d.view_location = (-2, 0, .1)
            area.spaces.active.shading.color_type = 'MATERIAL'
scene.render.film_transparent = False
bpy.ops.wm.save_as_mainfile(filepath=str(ASSET / 'source' / 'tanker.blend'))
bpy.ops.render.render(write_still=True)
# Second angle makes the defining tanker equipment easy to inspect.
camera.location = (-52, -62, 26)
aim(camera, (-3, 0, -.2))
scene.render.filepath = str(exports / 'tanker_rear_preview.png')
bpy.ops.render.render(write_still=True)
