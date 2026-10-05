"""Rebuild the complete v0.68 carrier from its frozen pre-hook mesh and parameters."""
import argparse
import hashlib
import json
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh

PACKAGE = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='New output directory, outside the frozen package')
    args = parser.parse_args()
    output = args.output.resolve()
    if output == PACKAGE or PACKAGE in output.parents or output.exists():
        parser.error('Choose a new directory outside the frozen package')
    params = json.loads((PACKAGE / 'parameters.json').read_text())
    validation = json.loads((PACKAGE / 'reports/cad_validation.json').read_text())
    baseline = PACKAGE / 'source/carrier_before_hook.stl'
    assert hashlib.sha256(baseline.read_bytes()).hexdigest() == validation['source_sha256']
    settings = params['cable_hook']
    cx, cy = settings['center_xy_mm']
    bottom = params['M5_screw_seat_z_mm']
    height = settings['protrusion_below_bottom_mm']
    width = settings['width_mm']
    wall = settings['wall_mm']
    half = settings['depth_mm'] / 2
    inner = half - wall
    mouth = settings['minimum_nominal_mouth_gap_mm']
    floor = height - wall
    profile = [(-half, settings['root_overlap_into_plate_mm']), (-half, -height),
               (half, -height), (half, -mouth), (inner, -mouth), (inner, -floor),
               (-inner, -floor), (-inner, settings['root_overlap_into_plate_mm'])]
    hook = (cq.Workplane('YZ', origin=(cx - width / 2, cy, bottom))
            .polyline(profile).close().extrude(width)
            .edges('|X').fillet(settings['profile_radius_mm'])
            .edges('not |X').fillet(settings['edge_radius_mm']).val())
    vertices, faces = hook.tessellate(.01, .045)
    hook_mesh = trimesh.Trimesh([v.toTuple() for v in vertices], faces, process=True)
    old = trimesh.load(baseline, force='mesh')
    new = trimesh.boolean.union([old, hook_mesh], engine='manifold')
    new.merge_vertices(digits_vertex=7)
    new.remove_unreferenced_vertices()
    assert new.is_watertight and new.is_winding_consistent and len(new.split()) == 1
    printed = new.copy()
    printed.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0]))
    printed.apply_translation(params['print_translation_mm'])
    output.mkdir(parents=True)
    new.export(output / 'carrier_native.stl')
    printed.export(output / 'carrier_print.stl')
    cq.exporters.export(hook, str(output / 'CABLE_HOOK_ONLY.step'))
    print('Rebuilt one watertight v0.68 carrier:', output)


if __name__ == '__main__':
    main()
