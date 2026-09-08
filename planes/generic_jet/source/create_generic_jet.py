"""Build with: blender --background --python planes/generic_jet/source/create_generic_jet.py

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
aircraft = bpy.data.collections.new('Generic Jet')
scene.collection.children.link(aircraft)
studio = bpy.data.collections.new('Preview Studio (not exported)')
scene.collection.children.link(studio)
root = bpy.data.objects.new('generic_jet', None)
aircraft.objects.link(root)
root['plane_id'] = 'generic_jet'
root['wingspan_m'] = 10.0
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
    bevel.width = min(0.035, thickness * 0.2)
    bevel.segments = 2
    obj.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
    return obj


loft('Fuselage', [
    (-5.45, 0.36, 0.36, 0.03), (-4.9, 0.49, 0.46, 0.02),
    (-3.6, 0.64, 0.59, 0), (-1.7, 0.78, 0.70, 0),
    (0.6, 0.79, 0.72, 0), (2.1, 0.66, 0.65, 0.015),
    (3.3, 0.49, 0.48, 0.01), (4.4, 0.28, 0.28, -0.035),
    (5.2, 0.09, 0.10, -0.065), (5.5, 0.008, 0.008, -0.07),
], paint)
loft('Nose radome', [
    (4.4, 0.282, 0.282, -0.035), (5.2, 0.092, 0.102, -0.065),
    (5.51, 0.009, 0.009, -0.07),
], teal)
loft('Canopy surround', [
    (0.2, 0.22, 0.08, 0.65), (0.7, 0.47, 0.32, 0.71),
    (1.6, 0.49, 0.47, 0.71), (2.35, 0.35, 0.37, 0.64),
    (3.1, 0.05, 0.05, 0.49),
], teal)
loft('Cockpit canopy', [
    (0.25, 0.20, 0.07, 0.71), (0.7, 0.455, 0.33, 0.77),
    (1.6, 0.475, 0.48, 0.77), (2.35, 0.335, 0.38, 0.70),
    (3.05, 0.04, 0.04, 0.55),
], glass)

for side, sign in [('right', 1), ('left', -1)]:
    def mirror(points):
        return [(x, sign * y, z) for x, y, z in points]

    slab('Wing_' + side, mirror([
        (1.1, 0.52, -0.13), (-1.48, 4.65, 0.04), (-1.72, 5.0, 0.06),
        (-2.36, 5.0, 0.06), (-2.40, 4.65, 0.04), (-2.42, 0.52, -0.13),
    ]), 0.13, paint)
    slab('Wingtip_' + side, mirror([
        (-1.48, 4.65, 0.111), (-1.72, 5.0, 0.131),
        (-2.36, 5.0, 0.131), (-2.40, 4.65, 0.111),
    ]), 0.012, orange)
    slab('Aileron marking_' + side, mirror([
        (-2.05, 2.65, 0.03), (-2.10, 4.45, 0.107),
        (-2.37, 4.45, 0.107), (-2.38, 2.65, 0.03),
    ]), 0.01, teal)
    slab('Horizontal stabilizer_' + side, mirror([
        (-3.3, 0.35, 0.18), (-4.4, 2.12, 0.27),
        (-5.12, 2.12, 0.27), (-4.95, 0.35, 0.18),
    ]), 0.10, teal)
    loft('Intake fairing_' + side, [
        (-2.4, 0.12, 0.20, -0.12), (-1.4, 0.34, 0.41, -0.13),
        (0.65, 0.38, 0.40, -0.10), (0.9, 0.34, 0.36, -0.10),
        (0.9, 0.27, 0.29, -0.10), (0.56, 0.25, 0.27, -0.10),
    ], paint, y=sign * 1.02)
    loft('Intake cavity_' + side, [
        (0.55, 0.252, 0.272, -0.10), (0.57, 0.252, 0.272, -0.10),
    ], dark, y=sign * 1.02)

slab('Vertical stabilizer', [
    (-2.72, 0, 0.46), (-3.92, 0, 2.72), (-4.63, 0, 2.72),
    (-5.00, 0, 0.42),
], 0.16, teal, axis='Y')
slab('Fin cap', [
    (-3.79, 0, 2.48), (-3.92, 0, 2.74), (-4.63, 0, 2.74),
    (-4.67, 0, 2.48),
], 0.172, orange, axis='Y')
loft('Exhaust nozzle', [
    (-4.99, 0.45, 0.43, 0.03), (-5.55, 0.39, 0.37, 0.03),
    (-5.55, 0.31, 0.29, 0.03), (-5.24, 0.30, 0.28, 0.03),
], metal)
loft('Exhaust cavity', [
    (-5.25, 0.302, 0.282, 0.03), (-5.23, 0.302, 0.282, 0.03),
], dark)

# Bake edge modifiers for a predictable standalone mesh export.
bpy.ops.object.select_all(action='DESELECT')
for obj in list(aircraft.objects):
    if obj.type != 'MESH':
        continue
    bpy.context.view_layer.objects.active = obj
    for modifier in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.data.calc_loop_triangles()

meshes = [obj for obj in aircraft.objects if obj.type == 'MESH']
points = [obj.matrix_world @ v.co for obj in meshes for v in obj.data.vertices]
span = max(v.y for v in points) - min(v.y for v in points)
assert abs(span - 10.0) < 0.001, span
assert all(math.isfinite(c) for v in points for c in v)
triangles = sum(len(obj.data.loop_triangles) for obj in meshes)
print(f'ASSET CHECK: {len(meshes)} meshes, {triangles} triangles, span {span:.3f} m')

exports = ASSET / 'exports'
exports.mkdir(exist_ok=True)
for obj in aircraft.objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = root
bpy.ops.export_scene.gltf(
    filepath=str(exports / 'generic_jet.glb'), export_format='GLB',
    use_selection=True, export_yup=True, export_extras=True,
    export_cameras=False, export_lights=False,
)


def studio_object(obj):
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    studio.objects.link(obj)


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -1.1))
floor = bpy.context.object
floor.name = 'Studio floor'
floor.data.materials.append(material('Studio | slate', (0.045, 0.068, 0.09), roughness=0.85))
studio_object(floor)
bpy.ops.object.camera_add(location=(14, -18, 12))
camera = bpy.context.object
camera.name = 'Preview camera'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 15.4
aim(camera, (0, 0, 0.25))
studio_object(camera)
scene.camera = camera
for name, location, energy, size in [
    ('Key', (4, -6, 12), 2300, 8),
    ('Fill', (1, 8, 7), 1700, 7),
    ('Rim', (-8, -2, 9), 2600, 6),
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
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.22, 0.28, 0.36, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = 0.5
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x = 1400
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(exports / 'generic_jet_preview.png')
scene.view_settings.view_transform = 'AgX'
# Keep modeling view clean while retaining the studio for repeatable renders.
for obj in studio.objects:
    obj.hide_set(True)
bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
bpy.context.view_layer.objects.active = root
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_rotation = camera.rotation_euler.to_quaternion()
            area.spaces.active.region_3d.view_distance = 19
            area.spaces.active.region_3d.view_location = (0, 0, 0.25)
            area.spaces.active.shading.color_type = 'MATERIAL'
scene.render.film_transparent = False
bpy.ops.wm.save_as_mainfile(filepath=str(ASSET / 'source' / 'generic_jet.blend'))
bpy.ops.render.render(write_still=True)
