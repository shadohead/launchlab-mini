"""Extend the existing launcher-facing center rectangle outward by exactly 1 mm."""
from pathlib import Path
import ast,hashlib,json,shutil
import cadquery as cq
import numpy as np
import trimesh
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[1]
S=R/'inspection/M5_recessed_screws_v045'
O=R/'inspection/M5_raised_rectangle_v046'
assert not (O/'SHA256SUMS.txt').exists(),'Delivered prototype is immutable'
for d in ['preview','stl','step','references','renders','reports','provenance']:(O/d).mkdir(parents=True,exist_ok=True)
hashes={}
for line in (S/'SHA256SUMS.txt').read_text().splitlines():
    h,n=line.split('  ',1)
    if n.startswith(('preview/','stl/')) or n in ['parameters.json','assembly_manifest.json','LICENSE.txt']:
        assert hashlib.sha256((S/n).read_bytes()).hexdigest()==h,n
        hashes[n]=h
for node in ast.parse((R/'scripts/build_compact_v010.py').read_text()).body:
    if isinstance(node,ast.FunctionDef) and node.name=='repair_collinear_boundary':exec(compile(ast.Module(body=[node],type_ignores=[]),'helper','exec'))
def cm(s):
    v,f=s.tessellate(.015,.06)
    m=repair_collinear_boundary(trimesh.Trimesh([p.toTuple() for p in v],f,process=True))
    assert m.is_watertight
    return m
def box(a,b):return trimesh.creation.box(extents=np.array(b)-a,transform=trimesh.transformations.translation_matrix((np.array(a)+b)/2))
def inter(a,b):return trimesh.boolean.intersection([a,b],engine='manifold')
def diff(a,b):return trimesh.boolean.difference([a,b],engine='manifold')
def vol(m):return abs(float(m.volume)) if m is not None and len(m.faces) else 0.
P=json.loads((S/'parameters.json').read_text());M=json.loads((S/'assembly_manifest.json').read_text())
old=trimesh.load(S/'preview/01_M5_recessed_screw_platform.stl',force='mesh')
FACE=-11.5;SHIFT=1.;ROOT_Y=(-1.875,1.875);ROOT_Z=(-.5,1.25)
# Preserve the factory rounded outer cap, including all its tiny edge blends.
cap=inter(old,box([-12,-2,-.6],[FACE-.00001,2,1.35]))
assert cap.is_watertight and len(cap.split())==1
assert abs(cap.bounds[0,0]+11.75)<1e-5
newcap=cap.copy();newcap.apply_translation([-SHIFT,0,0])
newcap.export(O/'references/Translated_original_rounded_cap.stl')
cap.export(O/'references/Original_center_rectangle_cap.stl')
# A 1 mm rectangular root extends the feature normal to the plate. The tiny
# overlaps ensure a single fused mesh without altering the original outer cap.
root=cq.Solid.makeBox(SHIFT+.00011,ROOT_Y[1]-ROOT_Y[0],ROOT_Z[1]-ROOT_Z[0],cq.Vector(FACE-SHIFT-.0001,ROOT_Y[0],ROOT_Z[0]))
cq.exporters.export(root,str(O/'step/Added_rectangle_root_ONLY.step'))
new=trimesh.boolean.union([old,cm(root),newcap],engine='manifold')
new.merge_vertices(digits_vertex=7);new.remove_unreferenced_vertices()
assert new.is_watertight and new.is_winding_consistent and len(new.split())==1
NAME='01_M5_raised_rectangle_platform'
new.export(O/'preview'/(NAME+'.stl'))
printed=new.copy();printed.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]))
shift=np.r_[-printed.bounds[:,:2].mean(0),-printed.bounds[0,2]];printed.apply_translation(shift)
printed.export(O/'stl'/(NAME+'.stl'))
readback=trimesh.load(O/'stl'/(NAME+'.stl'),force='mesh')
delta=max(cKDTree(printed.vertices).query(readback.vertices)[0].max(),cKDTree(readback.vertices).query(printed.vertices)[0].max())
assert delta<.0001 and readback.is_watertight and len(readback.split())==1
ROI=box([-12.8,-2,-.6],[FACE+.00002,2,1.35])
addition=diff(new,old);outside=vol(diff(addition,ROI));removed=vol(diff(old,new))
assert outside<.002 and removed<.002
round_roi=box([-13,-2,-.6],[FACE-SHIFT-.00011,2,1.35])
a=inter(new,round_roi);b=inter(newcap,round_roi)
round_delta=vol(diff(a,b))+vol(diff(b,a));assert round_delta<.002
factory=trimesh.load(S/'preview/REF_M5Stick_factory_geometry.stl',force='mesh')
rep=dict(status='PASS',units='mm',watertight=new.is_watertight,winding_consistent=new.is_winding_consistent,components=len(new.split()),source_sha256=hashes,outward_extension_mm=SHIFT,extension_vector_world_mm=[-1,0,0],plate_face_x_mm=FACE,original_tip_x_mm=float(cap.bounds[0,0]),revised_tip_x_mm=float(newcap.bounds[0,0]),original_projection_mm=FACE-cap.bounds[0,0],revised_projection_mm=FACE-newcap.bounds[0,0],same_yz_position=True,original_rounded_cap_symmetric_difference_mm3=round_delta,added_material_mm3=vol(addition),removed_material_mm3=removed,changed_material_outside_feature_mm3=outside,STL_export_delta_mm=float(delta),M5_overlap_mm3=vol(inter(new,factory)),print_bounds_mm=printed.bounds.tolist(),preserved={})
assert rep['M5_overlap_mm3']<.002
for name,roi in [
    ('M5_deck_screw_recesses_standoffs_and_supports',box([-2,-30,-20],[25,30,20])),
    ('left_launcher_receiver',box([-13,-30,-20],[-2,-2.01,20])),
    ('right_launcher_receiver',box([-13,2.01,-20],[-2,30,20])),
]:
    f=inter(old,roi);g=inter(new,roi);vv=vol(diff(f,g))+vol(diff(g,f));assert vv<.002,(name,vv)
    rep['preserved'][name+'_symmetric_difference_mm3']=vv
old.export(O/'references/Original_v045_carrier.stl')
# A center section shows the original and revised projection at actual scale.
section_roi=box([-13,-.001,-1],[-10.5,2,2])
inter(old,section_roi).export(O/'references/SECTION_original_rectangle.stl')
inter(new,section_roi).export(O/'references/SECTION_revised_rectangle.stl')
parts=[dict(name=NAME,filename=f'preview/{NAME}.stl',color='#357B73',description='v045 carrier with center rectangle extended outward 1 mm, original rounded cap retained',group='M5',reference=False,printable=True,source='Frozen v045 carrier')]
for e in M['parts']:
    if not e['reference']:continue
    shutil.copy2(S/e['filename'],O/e['filename']);parts.append(dict(e))
M.update(version='0.46',parts=parts,print_package_created=False)
P.update(version='0.46',architecture='Existing recessed-screw M5 carrier with center rectangle projecting an additional 1 mm',print_package_created=False,center_rectangle=dict(plate_face_x_mm=FACE,original_projection_mm=.25,revised_projection_mm=1.25,added_projection_mm=1,extension_vector_world_mm=[-1,0,0],root_y_bounds_mm=ROOT_Y,root_z_bounds_mm=ROOT_Z,position_yz_unchanged=True,edge_finish='Original rounded outer cap translated intact'),print_translation_mm=shift.tolist(),physical_fit='CAD geometry checked; revised launcher contact and retention untested')
P['limits']=[x for x in P.get('limits',[]) if 'printer dispatch' not in x]+['Center rectangle now projects 1.25 mm from its original face; revised physical launcher fit remains untested.','One unsliced replacement carrier; no printer dispatch.']
shutil.copy2(S/'LICENSE.txt',O/'LICENSE.txt')
shutil.copy2('/var/folders/j6/tpr5xxbj73lcxcl008r78q940000gn/T/codex-clipboard-97400b50-14af-4782-b490-45875d460540.png',O/'references/USER_center_rectangle.png')
(O/'references/request.json').write_text(json.dumps(dict(request='Tiny center rectangle 1 mm higher',clarification='Make it stick out farther',interpreted_change='1 mm extension normal to the launcher-facing plate, original location retained'),indent=2))
(O/'parameters.json').write_text(json.dumps(P,indent=2));(O/'assembly_manifest.json').write_text(json.dumps(M,indent=2));(O/'reports/cad_validation.json').write_text(json.dumps(rep,indent=2))
(O/'README.md').write_text('M5 raised center rectangle v046\n\nThe tiny rectangular feature on the launcher-facing plate extends outward an additional 1 mm: its projection increases from 0.25 to 1.25 mm. Its position and footprint stay the same, and its original rounded outer cap is copied intact. This follows the user clarification: Make it stick out farther.\n\nThe v045 underside screw-head recesses, M5 standoffs, opposite-end supports, right-block trim, and remaining launcher attachment geometry are preserved. Supply one replacement carrier. STL and generic 3MF use the existing side print orientation and are unsliced. The complete carrier is mesh geometry, editable in Blender; the STEP file describes only the newly added root. Section and original meshes are inspection references. No printer dispatch. Revised physical launcher contact and retention need a fit check.\n')
shutil.copy2(__file__,O/'provenance'/Path(__file__).name)
print('PASS',O,'projection',rep['original_projection_mm'],'->',rep['revised_projection_mm'],flush=True)
