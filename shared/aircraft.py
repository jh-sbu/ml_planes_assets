"""Blender-only mesh, material, export and preview helpers for basic airframes."""

import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


class Aircraft:
    def __init__(self, script, plane_id, span):
        self.asset = Path(script).resolve().parents[1]
        self.plane_id, self.span = plane_id, span
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.scene = bpy.context.scene
        self.scene.unit_settings.system = 'METRIC'
        self.scene.unit_settings.scale_length = 1.0
        self.collection = bpy.data.collections.new(plane_id.replace('_', ' ').title())
        self.scene.collection.children.link(self.collection)
        self.root = bpy.data.objects.new(plane_id, None)
        self.collection.objects.link(self.root)
        self.root['plane_id'] = plane_id
        self.root['wingspan_m'] = span
        self.root['source_axes'] = '+X nose, +Y right wing, +Z up'
        self.root['origin'] = 'Nominal center of gravity; visual placeholder'
        self.paint = self.material('Airframe | pearl gray', (.62, .70, .73), .3, .32)
        self.teal = self.material('Livery | deep teal', (.018, .18, .21), .35, .3)
        self.orange = self.material('Livery | safety orange', (.95, .22, .035), .15, .35)
        self.glass = self.material('Glazing | smoked blue', (.025, .08, .13), .65, .16)
        self.metal = self.material('Powerplant | titanium', (.19, .22, .24), .8, .32)
        self.dark = self.material('Powerplant | cavity', (.008, .012, .016), .1, .65)

    @staticmethod
    def material(name, color, metallic=0, roughness=.4):
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = (*color, 1)
        mat.use_nodes = True
        shader = mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = (*color, 1)
        shader.inputs['Metallic'].default_value = metallic
        shader.inputs['Roughness'].default_value = roughness
        return mat

    def mesh(self, name, vertices, faces, mat, smooth=False):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name, mesh)
        self.collection.objects.link(obj)
        obj.parent = self.root
        mesh.materials.append(mat)
        for face in mesh.polygons:
            face.use_smooth = smooth
        return obj

    def loft(self, name, stations, mat, y=0, segments=32):
        """Elliptical stations: (X, half width, half height, center Z)."""
        verts = [(x, y + ry * math.cos(2 * math.pi * i / segments),
                  z + rz * math.sin(2 * math.pi * i / segments))
                 for x, ry, rz, z in stations for i in range(segments)]
        faces = [tuple(reversed(range(segments)))]
        for j in range(len(stations) - 1):
            for i in range(segments):
                a, b = j * segments + i, j * segments + (i + 1) % segments
                faces.append((a, b, b + segments, a + segments))
        faces.append(tuple((len(stations) - 1) * segments + i for i in range(segments)))
        return self.mesh(name, verts, faces, mat, True)

    def slab(self, name, outline, thickness, mat, axis='Z'):
        direction = {'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}[axis]
        delta = Vector(direction) * thickness / 2
        verts = [tuple(Vector(p) + sign * delta) for sign in (-1, 1) for p in outline]
        n = len(outline)
        faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
        faces += [(i, (i+1) % n, (i+1) % n+n, i+n) for i in range(n)]
        obj = self.mesh(name, verts, faces, mat)
        bevel = obj.modifiers.new('Soft manufactured edges', 'BEVEL')
        bevel.width, bevel.segments = min(.08, thickness * .2), 2
        obj.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
        return obj

    def skin(self, name, stations, xs, angles, side, mat, lift=.025):
        """Decorative patch following a fuselage; include intervening loft stations."""
        xs = sorted(set(xs + [s[0] for s in stations if min(xs) < s[0] < max(xs)]))
        verts = []
        for x in xs:
            a, b = next((a, b) for a, b in zip(stations, stations[1:]) if a[0] <= x <= b[0])
            t = (x - a[0]) / (b[0] - a[0])
            ry, rz, z = [a[i] + t * (b[i] - a[i]) for i in range(1, 4)]
            for angle in angles:
                verts.append((x, side * (ry + lift) * math.cos(angle),
                              z + (rz + lift) * math.sin(angle)))
        n = len(angles)
        faces = [(j*n+k, (j+1)*n+k, (j+1)*n+k+1, j*n+k+1)
                 for j in range(len(xs)-1) for k in range(n-1)]
        obj = self.mesh(name, verts, faces, mat, True)
        # Skin panels must face away from the centerline, including the mirrored side.
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        for face in bm.faces:
            if face.normal.y * side < 0:
                face.normal_flip()
        bm.to_mesh(obj.data)
        bm.free()
        return obj

    def engine(self, name, x, y, z, radius):
        """Short turbofan with recessed fan, metal lip, and aft exhaust."""
        def sections(values):
            return [(x + dx*radius, r*radius, r*radius, z) for dx, r in values]
        self.loft('Engine nacelle_' + name, sections([
            (-2.2, .65), (-1.5, .98), (.7, 1), (1.45, .92),
            (1.5, .78), (1.04, .76)]), self.paint, y)
        self.loft('Intake rim_' + name, sections([
            (1.28, .945), (1.46, .925), (1.52, .78), (1.3, .775)]), self.metal, y)
        self.loft('Recessed fan_' + name, sections([(1.01, .762), (1.03, .762)]), self.dark, y)
        for i in range(12):
            angle = i * math.tau / 12
            verts = [(x + 1.045*radius, y + r*radius*math.cos(angle+a),
                      z + r*radius*math.sin(angle+a))
                     for r, a in [(.22, 0), (.71, .10), (.71, .29), (.22, .32)]]
            self.mesh(f'Fan blade_{name}_{i+1:02}', verts, [(0, 1, 2, 3)], self.metal)
        self.loft('Fan hub_' + name, sections([(1.04, .23), (1.4, .04)]), self.metal, y, 24)
        self.loft('Exhaust nozzle_' + name, sections([
            (-2, .65), (-2.5, .51), (-2.5, .41), (-2.2, .40)]), self.metal, y)
        self.loft('Exhaust cavity_' + name, sections([(-2.21, .402), (-2.19, .402)]), self.dark, y)

    def finish(self, rear=False):
        bpy.ops.object.select_all(action='DESELECT')
        meshes = [o for o in self.collection.objects if o.type == 'MESH']
        for obj in meshes:
            bpy.context.view_layer.objects.active = obj
            for modifier in list(obj.modifiers):
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            obj.data.calc_loop_triangles()
        bpy.context.view_layer.update()
        points = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
        span = max(v.y for v in points) - min(v.y for v in points)
        assert abs(span - self.span) < .001, span
        assert all(math.isfinite(c) for v in points for c in v)
        assert all(o.parent == self.root for o in meshes)
        assert all(t.area > 1e-10 for o in meshes for t in o.data.loop_triangles)
        triangles = sum(len(o.data.loop_triangles) for o in meshes)
        self.root['triangle_count'] = triangles
        print(f'ASSET CHECK {self.plane_id}: {len(meshes)} meshes, {triangles} triangles, span {span:.3f} m')
        exports = self.asset / 'exports'
        exports.mkdir(exist_ok=True)
        for obj in self.collection.objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = self.root
        bpy.ops.export_scene.gltf(
            filepath=str(exports / f'{self.plane_id}.glb'), export_format='GLB',
            use_selection=True, export_yup=True, export_extras=True,
            export_cameras=False, export_lights=False,
        )

        studio = bpy.data.collections.new('Preview Studio (not exported)')
        self.scene.collection.children.link(studio)

        def move(obj):
            for collection in list(obj.users_collection):
                collection.objects.unlink(obj)
            studio.objects.link(obj)

        def aim(obj):
            obj.rotation_euler = (Vector((0, 0, self.span*.025)) - obj.location).to_track_quat('-Z', 'Y').to_euler()

        s = self.span / 10
        bpy.ops.mesh.primitive_plane_add(size=200*s, location=(0, 0, min(v.z for v in points)-.35*s))
        floor = bpy.context.object
        floor.name = 'Studio floor'
        floor.data.materials.append(self.material('Studio | slate', (.045, .068, .09), roughness=.85))
        move(floor)
        bpy.ops.object.camera_add(location=(14*s, -18*s, 11*s))
        camera = bpy.context.object
        camera.name = 'Preview camera'
        camera.data.type, camera.data.ortho_scale = 'ORTHO', 14.8*s
        camera.data.clip_end = 1000*s
        aim(camera)
        move(camera)
        self.scene.camera = camera
        for name, location, energy, size in [
            ('Key', (4, -6, 12), 2300, 8), ('Fill', (1, 8, 7), 1700, 7),
            ('Rim', (-8, -2, 9), 2600, 6),
        ]:
            bpy.ops.object.light_add(type='AREA', location=tuple(c*s for c in location))
            lamp = bpy.context.object
            lamp.name, lamp.data.energy = name, energy*s*s
            lamp.data.shape, lamp.data.size = 'DISK', size*s
            aim(lamp)
            move(lamp)
        scene = self.scene
        scene.world = bpy.data.worlds.new('Studio world')
        scene.world.use_nodes = True
        scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.22, .28, .36, 1)
        scene.world.node_tree.nodes['Background'].inputs[1].default_value = .5
        scene.render.engine = 'CYCLES'
        scene.cycles.samples, scene.cycles.use_denoising = 48, True
        scene.render.resolution_x, scene.render.resolution_y = 1400, 1100
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = 'PNG'
        scene.render.filepath = str(exports / f'{self.plane_id}_preview.png')
        scene.render.film_transparent = False
        scene.view_settings.view_transform = 'AgX'
        for obj in studio.objects:
            obj.hide_set(True)
        bpy.ops.object.select_all(action='DESELECT')
        self.root.select_set(True)
        bpy.context.view_layer.objects.active = self.root
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    view = area.spaces.active
                    view.region_3d.view_rotation = camera.rotation_euler.to_quaternion()
                    view.region_3d.view_distance = 19*s
                    view.region_3d.view_location = (0, 0, .25*s)
                    view.shading.color_type = 'MATERIAL'
        bpy.ops.wm.save_as_mainfile(filepath=str(self.asset / 'source' / f'{self.plane_id}.blend'))
        bpy.ops.render.render(write_still=True)
        if rear:
            camera.location = (-14*s, -18*s, 9*s)
            aim(camera)
            scene.render.filepath = str(exports / f'{self.plane_id}_rear_preview.png')
            bpy.ops.render.render(write_still=True)
