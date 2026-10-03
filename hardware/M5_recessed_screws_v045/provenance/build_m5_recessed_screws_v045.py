"""Recess the two M5 screw heads beneath the existing v044 deck."""
from pathlib import Path
import ast, hashlib, json, shutil
import cadquery as cq
import numpy as np
import trimesh
from scipy.spatial import cKDTree

R = Path(__file__).resolve().parents[1]
S = R / 'inspection/M5_level_support_v044'
O = R / 'inspection/M5_recessed_screws_v045'
assert not (O / 'SHA256SUMS.txt').exists(), 'Delivered prototype is immutable'
for d in ['preview', 'stl', 'step', 'references', 'renders', 'reports', 'provenance']:
    (O / d).mkdir(parents=True, exist_ok=True)
source_hashes = {}
for line in (S / 'SHA256SUMS.txt').read_text().splitlines():
    h, n = line.split('  ', 1)
    assert hashlib.sha256((S / n).read_bytes()).hexdigest() == h, n
    source_hashes[n] = h
for node in ast.parse((R / 'scripts/build_compact_v010.py').read_text()).body:
    if isinstance(node, ast.FunctionDef) and node.name == 'repair_collinear_boundary':
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'helper', 'exec'))

def cm(s):
    v, f = s.tessellate(.015, .06)
    m = repair_collinear_boundary(trimesh.Trimesh([p.toTuple() for p in v], f, process=True))
    assert m.is_watertight
    return m

def box(a, b):
    return trimesh.creation.box(extents=np.array(b)-a, transform=trimesh.transformations.translation_matrix((np.array(a)+b)/2))

def inter(a, b): return trimesh.boolean.intersection([a, b], engine='manifold')
def diff(a, b): return trimesh.boolean.difference([a, b], engine='manifold')
def vol(m): return abs(float(m.volume)) if m is not None and len(m.faces) else 0.

P = json.loads((S / 'parameters.json').read_text())
M = json.loads((S / 'assembly_manifest.json').read_text())
old = trimesh.load(S / 'preview/01_M5_level_platform.stl', force='mesh')
factory = trimesh.load(S / 'preview/REF_M5Stick_factory_geometry.stl', force='mesh')
DECK = P['platform_top_z_mm']
FLOOR = DECK - P['platform_thickness_mm']
FACE = P['M5_mount_face_z_mm']
HEAD_D = 3.8
HEAD_H = 1.4
BORE_D = HEAD_D + .4
SEAT = FLOOR + HEAD_H
AXES = P['M5_axes_xy_mm']
cutters = []
for i, (x, y) in enumerate(AXES, 1):
    s = cq.Solid.makeCylinder(BORE_D/2, HEAD_H+.05, cq.Vector(x, y, FLOOR-.05))
    cq.exporters.export(s, str(O / 'step' / f'Counterbore_cutter_{i}_ONLY.step'))
    m = cm(s)
    cutters.append(m)
    m.export(O / 'references' / f'Counterbore_cutter_{i}.stl')

new = diff(old, trimesh.boolean.union(cutters, engine='manifold'))
new.merge_vertices(digits_vertex=7)
new.remove_unreferenced_vertices()
assert new.is_watertight and new.is_winding_consistent and len(new.split()) == 1
n = '01_M5_recessed_screw_platform'
new.export(O / 'preview' / (n+'.stl'))
printed = new.copy()
printed.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
shift = np.r_[-printed.bounds[:, :2].mean(0), -printed.bounds[0, 2]]
printed.apply_translation(shift)
printed.export(O / 'stl' / (n+'.stl'))
readback = trimesh.load(O / 'stl' / (n+'.stl'), force='mesh')
export_delta = max(cKDTree(printed.vertices).query(readback.vertices)[0].max(), cKDTree(readback.vertices).query(printed.vertices)[0].max())
assert export_delta < .0001 and readback.is_watertight and len(readback.split()) == 1

parts = [dict(name=n, filename=f'preview/{n}.stl', color='#357B73', description='v044 carrier with two flat-bottom underside screw-head recesses', group='M5', reference=False, printable=True, source='Frozen v044 carrier')]
for e in M['parts']:
    if not e['reference']: continue
    e = dict(e)
    if e['name'].startswith('REF_M2x6'):
        m = trimesh.load(S / e['filename'], force='mesh')
        m.apply_translation((0, 0, HEAD_H))
        m.export(O / e['filename'])
        e['description'] = 'Previous nominal 3.8 x 1.4 mm head / M2x6 reference seated in new recess; actual user fastener dimensions unconfirmed'
        e['geometry_revision'] = 'v045 head bottom flush with deck underside'
    else:
        shutil.copy2(S / e['filename'], O / e['filename'])
    parts.append(e)
M.update(version='0.45', parts=parts, print_package_created=False)

rep = dict(status='PASS', units='mm', watertight=new.is_watertight, winding_consistent=new.is_winding_consistent, components=len(new.split()), source_sha256=source_hashes, old_volume_mm3=vol(old), new_volume_mm3=vol(new), removed_material_mm3=vol(old)-vol(new), added_material_mm3=vol(diff(new, old)), M5_overlap_mm3=vol(inter(new, factory)), recess_diameter_mm=BORE_D, recess_depth_mm=HEAD_H, head_reference_diameter_mm=HEAD_D, head_reference_thickness_mm=HEAD_H, head_bottom_z_mm=SEAT-HEAD_H, deck_bottom_z_mm=FLOOR, screw_bearing_face_z_mm=SEAT, head_bottom_flush_delta_mm=abs(SEAT-HEAD_H-FLOOR), remaining_clamped_material_mm=FACE-SEAT, thread_reach_gain_mm=HEAD_H, STL_export_delta_mm=float(export_delta), preserved={}, seats=[])
assert rep['M5_overlap_mm3'] < .002 and rep['added_material_mm3'] < .002
assert rep['head_bottom_flush_delta_mm'] < 1e-8
for name, roi in [
    ('native_head_and_receivers', box([-25,-30,-20],[-1.9999,30,20])),
    ('deck_top_and_standoffs', box([-2,-30,SEAT+.0001],[24,30,20])),
    ('opposite_end_supports', box([-2,10,-10],[24,20,0])),
    ('trimmed_right_block', box([-25,-30,0],[-2,-14.99,20])),
]:
    f = inter(old, roi); g = inter(new, roi)
    vv = vol(diff(f, g))+vol(diff(g, f))
    assert vv < .002, (name, vv)
    rep['preserved'][name+'_symmetric_difference_mm3'] = vv
for i, ((x,y), cut) in enumerate(zip(AXES, cutters), 1):
    assert vol(inter(new, cut)) < .002
    # A small annular probe just above the counterbore shoulder must be solid.
    ring = cq.Solid.makeCylinder(1.75,.05,cq.Vector(x,y,SEAT+.01)).cut(cq.Solid.makeCylinder(1.3,.1,cq.Vector(x,y,SEAT)))
    probe = cm(ring)
    bearing_volume = vol(inter(new, probe))
    assert abs(bearing_volume-vol(probe)) < .002
    screw = trimesh.load(O / f'preview/REF_M2x6_{i}.stl', force='mesh')
    overlap = vol(inter(new, screw))
    assert overlap < .002, overlap
    rep['seats'].append(dict(axis_xy_mm=[x,y], bearing_probe_solid_fraction=bearing_volume/vol(probe), screw_carrier_overlap_mm3=overlap, nominal_6mm_thread_engagement_mm=SEAT+6-FACE, nominal_4mm_thread_engagement_mm=SEAT+4-FACE))

# True section through both hole axes, exported only for inspection renders.
section_roi = box([-1.3,-25,-9],[22.1,-21,-3.4])
inter(new, section_roi).export(O / 'references/SECTION_carrier.stl')
for i in [1,2]:
    m = trimesh.load(O / f'preview/REF_M2x6_{i}.stl', force='mesh')
    inter(m, box([-3,-25,-10],[24,-21,3])).export(O / 'references' / f'SECTION_screw_{i}.stl')

P.update(version='0.45', architecture='Existing v044 carrier with two underside screw-head counterbores', print_package_created=False, M5_screw_seat_z_mm=SEAT, nominal_insert_engagement_mm=SEAT+6-FACE, fasteners='Actual user screw length unconfirmed; nominal reference uses M2x6 / 3.8 x 1.4 mm pan heads', screw_head_recesses=dict(axes_xy_mm=AXES, diameter_mm=BORE_D, depth_mm=HEAD_H, head_diameter_assumed_mm=HEAD_D, head_thickness_assumed_mm=HEAD_H, head_radial_clearance_mm=(BORE_D-HEAD_D)/2, underside_plane_z_mm=FLOOR, bearing_face_z_mm=SEAT, thread_reach_gain_mm=HEAD_H, remaining_clamped_material_mm=FACE-SEAT, shape='Cylindrical flat-bottom counterbore, existing 2.4 mm through holes preserved'), print_translation_mm=shift.tolist(), physical_fit='CAD head flushness verified against prior nominal screw reference; actual hardware fit unverified', limits=['Head dimensions are inherited from the existing nominal reference pending user measurement.','Recess moves the bearing seat 1.4 mm toward the M5, reducing the clamped thickness from 4.3 to 2.9 mm.','Nominal M2x4 provides 1.1 mm of thread reach; nominal M2x6 provides 3.1 mm. Actual screw length and usable insert depth remain unmeasured.','Opposite-end supports retain their v044 0.5 mm height.','Unsliced replacement STL; no printer dispatch.'])
shutil.copy2(S / 'LICENSE.txt', O / 'LICENSE.txt')
shutil.copy2(S / 'references/USER_M5_level_markup.png', O / 'references/USER_M5_level_markup.png')
(O / 'parameters.json').write_text(json.dumps(P,indent=2))
(O / 'assembly_manifest.json').write_text(json.dumps(M,indent=2))
(O / 'reports/cad_validation.json').write_text(json.dumps(rep,indent=2))
(O / 'README.md').write_text('M5 recessed screw heads v045\n\nTwo cylindrical recesses are cut into the underside of the existing v044 carrier: diameter 4.2 mm, depth 1.4 mm, centered on the existing M2 holes. Their flat shoulders seat the previous nominal 3.8 mm diameter x 1.4 mm thick screw heads flush with the deck underside. The existing 2.4 mm through holes and 5 mm diameter standoffs remain unchanged.\n\nThis advances each screw 1.4 mm and reduces the clamped material from 4.3 mm to 2.9 mm. A nominal 4 mm screw reaches 1.1 mm into the device, and a nominal 6 mm screw reaches 3.1 mm; usable insert depth and actual fastener dimensions have not been measured. The reference screws show the existing 6 mm example, not a new hardware selection.\n\nThe launcher attachment, device pose, right-block trim, rounded bevel, and opposite-end support pads (0.5 mm high) are preserved. No sensor mount change. The complete carrier is supplied as a mesh and editable Blender file; STEP files describe only the counterbore cutters. Section meshes and hardware are inspection references, not printable parts. Replacement STL is in its existing side print orientation and is unsliced. No printer dispatch.\n')
shutil.copy2(__file__, O / 'provenance' / Path(__file__).name)
print('PASS', O, 'counterbores', BORE_D, 'x', HEAD_H, 'reach gain', HEAD_H, flush=True)
