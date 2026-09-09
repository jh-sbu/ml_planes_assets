"""Reopen Blender sources and re-import exported GLBs to verify the fleet.

Run from any directory: blender --background --python shared/validate_assets.py
"""

import json
import math
import struct
from pathlib import Path

import bpy


REPO = Path(__file__).resolve().parents[1]


def geometry(objects):
    bpy.context.view_layer.update()
    meshes = [o for o in objects if o.type == 'MESH']
    points = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
    assert points and all(math.isfinite(c) for p in points for c in p)
    bounds = [(min(p[i] for p in points), max(p[i] for p in points)) for i in range(3)]
    triangles = 0
    for obj in meshes:
        obj.data.calc_loop_triangles()
        triangles += len(obj.data.loop_triangles)
    return len(meshes), triangles, bounds


for asset in sorted((REPO / 'planes').iterdir()):
    if not asset.is_dir():
        continue
    plane_id = asset.name
    source = asset / 'source' / f'{plane_id}.blend'
    exported = asset / 'exports' / f'{plane_id}.glb'
    assert source.is_file() and exported.is_file(), f'Missing asset: {plane_id}'
    bpy.ops.wm.open_mainfile(filepath=str(source))
    root = bpy.data.objects[plane_id]
    expected_span = root['wingspan_m']
    assert root.location.length < 1e-6
    source_geometry = geometry(root.children_recursive)
    assert abs(source_geometry[2][1][1] - source_geometry[2][1][0] - expected_span) < .001

    # Check the actual glTF axis convention and packaging before Blender undoes Y-up.
    data = exported.read_bytes()
    magic, version, length, json_length, chunk_type = struct.unpack_from('<4sIIII', data)
    assert magic == b'glTF' and version == 2 and length == len(data)
    assert chunk_type == 0x4E4F534A
    gltf = json.loads(data[20:20+json_length])
    assert len(gltf['scenes']) == 1 and len(gltf['scenes'][0]['nodes']) == 1
    assert not gltf.get('cameras') and not gltf.get('images')
    assert all('uri' not in b for b in gltf['buffers'])
    assert all('camera' not in n and 'KHR_lights_punctual' not in n.get('extensions', {})
               for n in gltf['nodes'])
    assert not any('Studio' in n.get('name', '') or 'Preview' in n.get('name', '')
                   for n in gltf['nodes'])
    positions = [gltf['accessors'][p['attributes']['POSITION']]
                 for mesh in gltf['meshes'] for p in mesh['primitives']]
    exported_span = max(p['max'][2] for p in positions) - min(p['min'][2] for p in positions)
    assert abs(exported_span - expected_span) < .001, 'GLB wingspan must run along Z'

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(exported))
    root = bpy.data.objects[plane_id]
    assert root['plane_id'] == plane_id and root.location.length < 1e-6
    assert all(o == root or o.parent == root for o in bpy.context.scene.objects)
    imported = geometry(root.children_recursive)
    assert source_geometry[:2] == imported[:2], (plane_id, source_geometry, imported)
    assert all(abs(a-b) < .001 for pair_a, pair_b in zip(source_geometry[2], imported[2])
               for a, b in zip(pair_a, pair_b)), f'GLB changed dimensions: {plane_id}'
    print(f'VALIDATED {plane_id}: {imported[0]} meshes, {imported[1]} triangles, '
          f'{expected_span:g} m span, {len(gltf["materials"])} materials', flush=True)
