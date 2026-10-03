"""Replace the small block with a tapered tab blended smoothly into its plate."""
from pathlib import Path
import ast,hashlib,json,shutil
import cadquery as cq
import numpy as np
import trimesh
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[1];S=R/'inspection/M5_smooth_rectangle_v048';O=R/'inspection/M5_soft_ramp_v049'
assert not (O/'SHA256SUMS.txt').exists(),'Delivered prototype is immutable'
for d in ['preview','stl','step','references','renders','reports','provenance']:(O/d).mkdir(parents=True,exist_ok=True)
hashes={}
for line in (S/'SHA256SUMS.txt').read_text().splitlines():
    h,n=line.split('  ',1)
    if n.startswith(('preview/','stl/')) or n in ['parameters.json','assembly_manifest.json','LICENSE.txt']:
        assert hashlib.sha256((S/n).read_bytes()).hexdigest()==h,n;hashes[n]=h
for source,names in [('build_compact_v010.py',['repair_collinear_boundary']),('build_m5_rotated_rectangle_v047.py',['box','inter','diff','vol'])]:
    for node in ast.parse((R/'scripts'/source).read_text()).body:
        if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),'helpers','exec'))
def diff(a,b):
    if not len(a.faces):return trimesh.Trimesh()
    if not len(b.faces):return a.copy()
    return trimesh.boolean.difference([a,b],engine='manifold')
P=json.loads((S/'parameters.json').read_text());M=json.loads((S/'assembly_manifest.json').read_text())
old=trimesh.load(S/'preview/01_M5_smooth_rectangle_platform.stl',force='mesh')
FACE=-11.5;CENTER_Z=.375;HEIGHT=1.25;RADIUS=.8
# Analytic proxy plate lets the base edges receive a true concave blend. Only
# the tab and 0.01 mm of root below the plate surface are kept for the mesh union.
plate=cq.Workplane('XY').box(12,10,.6,centered=(True,True,False)).translate((0,0,-.6))
body=cq.Workplane('XY').rect(6.25,4.25).workplane(offset=HEIGHT).rect(3.75,1.75).loft(ruled=True)
combined=plate.union(body).val()
edges=[e for e in combined.Edges() if e.Center().z>=-1e-6 and abs(e.Center().x)<4 and abs(e.Center().y)<3]
assert len(edges)==12
smooth=combined.fillet(RADIUS,edges);assert smooth.isValid()
patch=smooth.intersect(cq.Solid.makeBox(8.6,6.6,HEIGHT+.01,cq.Vector(-4.3,-3.3,-.01)))
patch=patch.rotate((0,0,0),(0,1,0),-90).translate((FACE,0,CENTER_Z))
cq.exporters.export(patch,str(O/'step/Soft_center_ramp_ONLY.step'))
v,f=patch.tessellate(.008,.035)
raw_tab=trimesh.Trimesh([p.toTuple() for p in v],f,process=True)
tab=raw_tab.copy()
# Rounded CAD face seams may contain coincident, zero-area triangles. Weld at
# one-micron precision and remove only duplicate/degenerate faces before union.
tab.merge_vertices(digits_vertex=6);tab.update_faces(tab.nondegenerate_faces());tab.update_faces(tab.unique_faces());tab.remove_unreferenced_vertices()
tab=repair_collinear_boundary(tab);assert tab.is_watertight and tab.is_winding_consistent
seam_delta=max(cKDTree(raw_tab.vertices).query(tab.vertices)[0].max(),cKDTree(tab.vertices).query(raw_tab.vertices)[0].max());assert seam_delta<.000002
tab.export(O/'references/Soft_center_ramp.stl')
core=diff(old,box([-13,-1.8,-2.5],[FACE,1.8,3.5]))
new=trimesh.boolean.union([core,tab],engine='manifold');new.merge_vertices(digits_vertex=7);new.remove_unreferenced_vertices()
assert new.is_watertight and new.is_winding_consistent and len(new.split())==1
NAME='01_M5_soft_ramp_platform';new.export(O/'preview'/(NAME+'.stl'))
printed=new.copy();printed.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]))
shift=np.r_[-printed.bounds[:,:2].mean(0),-printed.bounds[0,2]];printed.apply_translation(shift);printed.export(O/'stl'/(NAME+'.stl'))
readback=trimesh.load(O/'stl'/(NAME+'.stl'),force='mesh')
delta=max(cKDTree(printed.vertices).query(readback.vertices)[0].max(),cKDTree(readback.vertices).query(printed.vertices)[0].max())
assert delta<.0001 and readback.is_watertight and len(readback.split())==1
ROI=box([-13,-3,-3.6],[FACE+.0101,3,4.3])
outside=vol(diff(diff(old,new),ROI))+vol(diff(diff(new,old),ROI));assert outside<.002
probe=box([-13,-3,-3.6],[FACE-.00001,3,4.3]);actual=inter(new,probe)
projection=FACE-actual.bounds[0,0];assert abs(projection-HEIGHT)<1e-5
factory=trimesh.load(S/'preview/REF_M5Stick_factory_geometry.stl',force='mesh')
rep=dict(status='PASS',units='mm',watertight=new.is_watertight,winding_consistent=new.is_winding_consistent,components=len(new.split()),source_sha256=hashes,shape='Trapezoidal loft with rounded corners and concave base blend',projection_mm=float(projection),nominal_base_yz_size_mm=[4.25,6.25],nominal_top_yz_size_mm=[1.75,3.75],edge_and_base_fillet_mm=RADIUS,analytic_feature_valid=patch.isValid(),CAD_seam_weld_delta_mm=float(seam_delta),degenerate_or_duplicate_CAD_faces_removed=len(raw_tab.faces)-len(tab.faces),protrusion_bounds_mm=actual.bounds.tolist(),changed_material_outside_feature_mm3=outside,STL_export_delta_mm=float(delta),M5_overlap_mm3=vol(inter(new,factory)),print_bounds_mm=printed.bounds.tolist(),preserved={})
assert rep['M5_overlap_mm3']<.002
for name,roi in [('M5_deck_screw_recesses_standoffs_and_supports',box([-2,-30,-20],[25,30,20])),('left_launcher_receiver',box([-13,-30,-20],[-2,-3.01,20])),('right_launcher_receiver',box([-13,3.01,-20],[-2,30,20])),('underlying_plate',box([-11.4899,-30,-20],[-2,30,20]))]:
    f=inter(old,roi);g=inter(new,roi);vv=vol(diff(f,g))+vol(diff(g,f));assert vv<.002,(name,vv);rep['preserved'][name+'_symmetric_difference_mm3']=vv
parts=[dict(name=NAME,filename=f'preview/{NAME}.stl',color='#357B73',description='v048 carrier with a broader center ramp and 0.8 mm rounded transitions',group='M5',reference=False,printable=True,source='Frozen v048 carrier and analytic soft ramp')]
for e in M['parts']:
    if not e['reference']:continue
    shutil.copy2(S/e['filename'],O/e['filename']);parts.append(dict(e))
M.update(version='0.49',parts=parts,print_package_created=False)
P.update(version='0.49',architecture='Recessed-screw M5 carrier with a broad, softly rounded center ramp',print_package_created=False,center_rectangle=dict(plate_face_x_mm=FACE,projection_mm=HEIGHT,footprint_rotation_deg=90,center_yz_mm=[0,CENTER_Z],nominal_base_yz_size_mm=[4.25,6.25],nominal_top_yz_size_mm=[1.75,3.75],edge_and_base_fillet_mm=RADIUS,edge_finish='Broader shallow slopes, 0.8 mm rounded top and side corners, concave blend to plate'),print_translation_mm=shift.tolist(),physical_fit='CAD geometry checked; smoothed launcher contact and retention untested')
P['limits']=[x for x in P.get('limits',[]) if 'Center rectangle' not in x and 'unsliced replacement' not in x]+['Center ramp has a wider blended base; physical launcher fit remains untested.','One unsliced replacement carrier; no printer dispatch.']
shutil.copy2(S/'LICENSE.txt',O/'LICENSE.txt');shutil.copy2(S/'references/USER_center_rectangle.png',O/'references/USER_center_rectangle.png')
(O/'parameters.json').write_text(json.dumps(P,indent=2));(O/'assembly_manifest.json').write_text(json.dumps(M,indent=2));(O/'reports/cad_validation.json').write_text(json.dumps(rep,indent=2))
(O/'README.md').write_text('M5 softer center ramp v049\n\nThe center tab uses a broader nominal 4.25 x 6.25 mm base, a nominal 1.75 x 3.75 mm top, and 0.8 mm fillets at the top, side corners and concave junction with the plate. The sides are 45 degrees before rounding and the blended base extends slightly beyond the nominal footprint. The center, accepted direction and 1.25 mm projection are preserved. This replaces the narrower 0.3 mm blends in v048.\n\nOne replacement carrier. Unsliced STL and generic 3MF retain the existing side print orientation. Existing M5 mounting geometry, screw-head recesses and launcher receivers are preserved. Complete carrier is editable mesh geometry in Blender; STEP describes only the analytic ramp and a 0.01 mm root into the plate. Reference meshes are not printable parts. Revised launcher contact and retention remain physically untested. No printer dispatch.\n')
shutil.copy2(__file__,O/'provenance'/Path(__file__).name)
print('PASS',O,'broad ramp / 0.8 mm base and edge blends / projection',projection,flush=True)
