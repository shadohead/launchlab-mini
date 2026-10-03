"""Turn the raised center rectangle's footprint 90 degrees in its plate plane."""
from pathlib import Path
import ast,hashlib,json,shutil
import cadquery as cq
import numpy as np
import trimesh
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[1];S=R/'inspection/M5_raised_rectangle_v046';O=R/'inspection/M5_rotated_rectangle_v047'
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
def box(a,b):return trimesh.creation.box(extents=np.array(b)-a,transform=trimesh.transformations.translation_matrix((np.array(a)+b)/2))
def inter(a,b):return trimesh.boolean.intersection([a,b],engine='manifold')
def diff(a,b):return trimesh.boolean.difference([a,b],engine='manifold')
def vol(m):return abs(float(m.volume)) if m is not None and len(m.faces) else 0.
P=json.loads((S/'parameters.json').read_text());M=json.loads((S/'assembly_manifest.json').read_text())
old=trimesh.load(S/'preview/01_M5_raised_rectangle_platform.stl',force='mesh')
FACE=-11.5;CENTER=[FACE,0,.375]
# Include a 0.01 mm root inside the existing plate to fuse the rotated feature.
feature=inter(old,box([-13,-1.876,-.501],[FACE+.01,1.876,1.251]))
assert feature.is_watertight and len(feature.split())==1
rotation=trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0],point=CENTER)
rotated=feature.copy();rotated.apply_transform(rotation)
rotated.export(O/'references/Rotated_actual_rectangle.stl')
core=diff(old,box([-13,-2,-.6],[FACE,2,1.35]))
new=trimesh.boolean.union([core,rotated],engine='manifold')
new.merge_vertices(digits_vertex=7);new.remove_unreferenced_vertices()
assert new.is_watertight and new.is_winding_consistent and len(new.split())==1
NAME='01_M5_rotated_rectangle_platform'
new.export(O/'preview'/(NAME+'.stl'))
printed=new.copy();printed.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]))
shift=np.r_[-printed.bounds[:,:2].mean(0),-printed.bounds[0,2]];printed.apply_translation(shift)
printed.export(O/'stl'/(NAME+'.stl'))
readback=trimesh.load(O/'stl'/(NAME+'.stl'),force='mesh')
delta=max(cKDTree(printed.vertices).query(readback.vertices)[0].max(),cKDTree(readback.vertices).query(printed.vertices)[0].max())
assert delta<.0001 and readback.is_watertight and len(readback.split())==1
ROI=box([-13,-2,-1.6],[FACE+.0101,2,2.35])
outside=vol(diff(diff(old,new),ROI))+vol(diff(diff(new,old),ROI));assert outside<.002
protrusion_roi=box([-13,-2,-1.6],[FACE-.0001,2,2.35])
a=inter(new,protrusion_roi);b=inter(rotated,protrusion_roi)
rotated_delta=vol(diff(a,b))+vol(diff(b,a));assert rotated_delta<.002
protrusion_bounds=a.bounds.tolist();projection=FACE-a.bounds[0,0]
assert abs(projection-1.25)<1e-5
assert abs((a.bounds[0,2]+a.bounds[1,2])/2-.375)<1e-5
assert abs((a.bounds[0,1]+a.bounds[1,1])/2)<1e-5
factory=trimesh.load(S/'preview/REF_M5Stick_factory_geometry.stl',force='mesh')
rep=dict(status='PASS',units='mm',watertight=new.is_watertight,winding_consistent=new.is_winding_consistent,components=len(new.split()),source_sha256=hashes,footprint_rotation_deg=90,normal_axis_world=[1,0,0],rotation_center_mm=CENTER,rotation_transform=rotation.tolist(),root_original_yz_size_mm=[3.75,1.75],root_revised_yz_size_mm=[1.75,3.75],growth_at_each_short_side_mm=1,projection_mm=float(projection),rotated_protrusion_bounds_mm=protrusion_bounds,actual_rotated_geometry_symmetric_difference_mm3=rotated_delta,changed_material_outside_feature_mm3=outside,STL_export_delta_mm=float(delta),M5_overlap_mm3=vol(inter(new,factory)),print_bounds_mm=printed.bounds.tolist(),preserved={})
assert rep['M5_overlap_mm3']<.002
for name,roi in [
    ('M5_deck_screw_recesses_standoffs_and_supports',box([-2,-30,-20],[25,30,20])),
    ('left_launcher_receiver',box([-13,-30,-20],[-2,-2.01,20])),
    ('right_launcher_receiver',box([-13,2.01,-20],[-2,30,20])),
    ('underlying_plate',box([-11.4999,-30,-20],[-2,30,20])),
]:
    f=inter(old,roi);g=inter(new,roi);vv=vol(diff(f,g))+vol(diff(g,f));assert vv<.002,(name,vv)
    rep['preserved'][name+'_symmetric_difference_mm3']=vv
root=cq.Solid.makeBox(1.00011,1.75,3.75,cq.Vector(FACE-1.0001,-.875,-1.5))
cq.exporters.export(root,str(O/'step/Rotated_rectangle_root_ONLY.step'))
parts=[dict(name=NAME,filename=f'preview/{NAME}.stl',color='#357B73',description='v046 carrier with the raised center rectangle footprint rotated 90 degrees on the plate',group='M5',reference=False,printable=True,source='Frozen v046 carrier')]
for e in M['parts']:
    if not e['reference']:continue
    shutil.copy2(S/e['filename'],O/e['filename']);parts.append(dict(e))
M.update(version='0.47',parts=parts,print_package_created=False)
P.update(version='0.47',architecture='Recessed-screw M5 carrier with taller center rectangle footprint in the other direction',print_package_created=False,center_rectangle=dict(plate_face_x_mm=FACE,projection_mm=1.25,footprint_rotation_deg=90,rotation_center_mm=CENTER,root_y_bounds_mm=[-.875,.875],root_z_bounds_mm=[-1.5,2.25],root_yz_size_mm=[1.75,3.75],growth_at_each_short_side_mm=1,edge_finish='Actual v046 rectangle and rounded cap rotated intact'),print_translation_mm=shift.tolist(),physical_fit='CAD geometry checked; revised launcher contact and retention untested')
P['limits']=[x for x in P.get('limits',[]) if 'Center rectangle' not in x and 'unsliced replacement' not in x]+['Center rectangle footprint turned 90 degrees: 1.75 x 3.75 mm at the root, with the existing 1.25 mm projection.','One unsliced replacement carrier; no printer dispatch.']
shutil.copy2(S/'LICENSE.txt',O/'LICENSE.txt')
shutil.copy2(S/'references/USER_center_rectangle.png',O/'references/USER_center_rectangle.png')
(O/'references/request.json').write_text(json.dumps(dict(request='Rectangle in the other direction, growing bottom left and top right in preview',interpretation='Turn existing footprint 90 degrees: new short-side growth 1 mm at each end, retaining 1.25 mm projection',preview_mapping='Camera (1,1,1.5) in print pose: print X / original world Z is the bottom-left and top-right direction'),indent=2))
(O/'parameters.json').write_text(json.dumps(P,indent=2));(O/'assembly_manifest.json').write_text(json.dumps(M,indent=2));(O/'reports/cad_validation.json').write_text(json.dumps(rep,indent=2))
(O/'README.md').write_text('M5 taller center rectangle v047\n\nThe raised center rectangle turns 90 degrees in the plane of the launcher-facing plate. Its root footprint changes from 3.75 x 1.75 mm to 1.75 x 3.75 mm. It grows 1 mm at each end in the short direction shown toward bottom-left and top-right in the preview. Its center and 1.25 mm outward projection stay the same. The actual v046 rectangle, including its rounded cap, is rotated intact.\n\nOne replacement carrier. STL and generic 3MF are unsliced and retain the existing side print orientation. The underlying plate, launcher receivers, M5 screw-head recesses, standoffs and supports are unchanged. The complete carrier is editable mesh geometry in Blender; STEP describes only the rotated analytic root. Reference meshes are not printable parts. Revised physical launcher contact and retention remain untested. No printer dispatch.\n')
shutil.copy2(__file__,O/'provenance'/Path(__file__).name)
print('PASS',O,'root footprint 1.75 x 3.75; projection',projection,flush=True)
