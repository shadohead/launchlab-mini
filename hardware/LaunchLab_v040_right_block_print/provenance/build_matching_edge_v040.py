"""Printable circled-block revision with the factory opposite-end edge copied."""
from pathlib import Path
import hashlib
import json
import shutil
import numpy as np
import trimesh

R = Path(__file__).resolve().parents[1]
BASE = R/'releases/LaunchLab_v024_stepped_platform'
S = R/'inspection/m5_circled_right_block_v039'
O = R/'releases/LaunchLab_v040_right_block_print'
assert not (O/'SHA256SUMS.txt').exists(), 'Frozen release'
for directory in ['preview','stl','references','reports','renders','provenance','bambu']:
    (O/directory).mkdir(parents=True,exist_ok=True)

def box(lo,hi):
    lo,hi=np.array(lo),np.array(hi)
    return trimesh.creation.box(extents=hi-lo,
        transform=trimesh.transformations.translation_matrix((lo+hi)/2))

def volume(m):return abs(float(m.volume)) if len(m.faces) else 0.
def intersection(a,b):return trimesh.boolean.intersection([a,b],engine='manifold')
def difference(a,b):return trimesh.boolean.difference([a,b],engine='manifold')

for line in (BASE/'SHA256SUMS.txt').read_text().splitlines():
    digest,name=line.split('  ',1)
    assert hashlib.sha256((BASE/name).read_bytes()).hexdigest()==digest
assert json.loads((S/'reports/cad_validation.json').read_text())['status']=='PASS'
old=trimesh.load(BASE/'preview/01_M5_stepped_platform.stl',force='mesh')
sharp=trimesh.load(S/'preview/01_M5_stepped_platform.stl',force='mesh')
# Copy the entire native 0.5 mm beveled cap at the opposite end, including
# its three-way corner, rather than approximating the factory edge by a radius.
native_cap=intersection(old,box([-20,18,9],[-2,30,20]))
transform=np.eye(4);transform[1,1]=-1;transform[1,3]=3
copied_cap=native_cap.copy();copied_cap.apply_transform(transform)
cap_roi=box([-20,-30,9],[-2,-15,20])
new=trimesh.boolean.union([difference(sharp,cap_roi),copied_cap],engine='manifold')
new.merge_vertices(digits_vertex=7);new.remove_unreferenced_vertices()
assert new.is_watertight and new.is_winding_consistent and len(new.split())==1
assert volume(difference(new,sharp))<.002
name='01_M5_stepped_platform'
new.export(O/'preview'/(name+'.stl'))
removed=difference(old,new)
removed.export(O/'references/REMOVED_circled_right_3mm_visual.stl')
M=json.loads((S/'assembly_manifest.json').read_text())
for item in M['parts']:
    if item['reference']:shutil.copy2(BASE/item['filename'],O/item['filename'])
    else:item.update(description='Circled right block trimmed 3 mm left; native opposite-end 0.5 mm bevel copied to the new edge.',
        geometry_revision='v0.40 matching factory edge, printable')
M.update(version='0.40',print_package_created=True)
(O/'assembly_manifest.json').write_text(json.dumps(M,indent=2))
P=json.loads((S/'parameters.json').read_text())
printed=new.copy();printed.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]))
shift=np.r_[-printed.bounds[:,:2].mean(0),-printed.bounds[0,2]]
printed.apply_translation(shift);printed.export(O/'stl'/(name+'.stl'))
P.update(version='0.40',architecture='Circled right block shortened 3 mm with matching native beveled end',
    print_package_created=True,print_translation_mm=shift.tolist(),
    edge_finish=dict(type='Factory 0.5 mm bevel copied from opposite end, including corner',
        width_mm=.5,native_source_y_mm=[18,18.5],revised_y_mm=[-15.5,-15],top_edge_z_mm=[9,9.5],
        copied_native_cap_transform=transform.tolist()),
    replacement_printed_parts=1,physical_fit='User-reviewed direction; printed thumb reach and strength still unverified')
(O/'parameters.json').write_text(json.dumps(P,indent=2))
report=dict(status='PASS',watertight=True,winding_consistent=True,components=1,
    source_v039_sha256=hashlib.sha256((S/'preview'/(name+'.stl')).read_bytes()).hexdigest(),
    volume_original_mm3=volume(old),volume_sharp_trim_mm3=volume(sharp),volume_new_mm3=volume(new),
    bevel_material_removed_mm3=volume(sharp)-volume(new),preserved={})
for label,roi in [
    ('remaining_v039_geometry_outside_new_end_cap',box([-20,-14.9999,-20],[30,30,20])),
    ('entire_lower_attachment_foot',box([-20,-30,-20],[30,30,-.0001])),
    ('M5_deck_and_screw_posts',box([-1.9999,-30,-20],[30,30,20])),
    ('both_curved_receiver_regions',box([-20,-14,-20],[30,14,20]))]:
    a,b=intersection(sharp,roi),intersection(new,roi)
    delta=volume(difference(a,b))+volume(difference(b,a))
    assert delta<.002,(label,delta)
    report['preserved'][label+'_symmetric_difference_mm3']=delta
finished_cap=intersection(new,cap_roi)
cap_delta=volume(difference(finished_cap,copied_cap))+volume(difference(copied_cap,finished_cap))
assert cap_delta<.002
report['copied_native_end_cap_symmetric_difference_mm3']=cap_delta
factory=trimesh.load(O/'preview/REF_M5Stick_factory_geometry.stl',force='mesh')
report['M5_overlap_mm3']=volume(intersection(new,factory));assert report['M5_overlap_mm3']<.002
raised=intersection(new,box([-20,-30,.0001],[-2.0001,30,20]))
assert abs(raised.bounds[0,1]+15.5)<.001
report['new_right_block_edge_y_mm']=float(raised.bounds[0,1])
report['print_bounds_mm']=printed.bounds.tolist()
report['limits']=['Digital model and native edge matching do not establish printed thumb reach or mechanical strength.']
(O/'reports/cad_validation.json').write_text(json.dumps(report,indent=2))
shutil.copy2(S/'references/USER_circled_topdown.png',O/'references/USER_circled_topdown.png')
shutil.copy2(S/'references/circle_provenance.json',O/'references/circle_provenance.json')
shutil.copy2(S/'LICENSE.txt',O/'LICENSE.txt')
(O/'README.md').write_text('''# LaunchLab v0.40 — trimmed M5 block with matching edge

The user-circled raised right block is shortened 3 mm toward the left in the
top view with USB-C on the right. Its end changes from Y-18.5 to Y-15.5.
The opposite end's native 0.5 mm bevel, including its corner, is copied onto
the new top edge. The lower launcher foot, curved receivers, M5 position,
2 mm deck, screw posts and the other raised block are unchanged.

Only the M5 carrier needs replacing. Reuse the v0.33 sensor assembly and
two M2x6 screws. Open the M5-only Bambu 3MF in bambu/ for P1S 0.4 mm,
PLA, 0.2 mm layers, Arachne, 5 mm outer brim and Tree Slim supports.
Assign the project's PLA to AMS filament 3 in the print dialog.
The individual manufacturing STL is in stl/; preview/ uses assembly coordinates.
No printer job has been started. Physical thumb reach and printed strength
still need checking after printing.

The editable Blender and GLB show actual part and factory M5 meshes.
Source: Migbello native grip / BP Gear Port, Thingiverse 6856080,
CC BY-SA (version unspecified). See LICENSE.txt.
''')
shutil.copy2(__file__,O/'provenance'/Path(__file__).name)
print('V040_MATCHING_FACTORY_EDGE_PASS',json.dumps(report),flush=True)
