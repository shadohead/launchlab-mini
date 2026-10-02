"""Narrow the launcher-facing center step and lower the central sensor platform."""
from pathlib import Path
import ast,hashlib,json,shutil
import cadquery as cq
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];S=R/'releases/LaunchLab_v032_balanced_QRE';O=R/'releases/LaunchLab_v033_flush_QRE'
assert not (O/'SHA256SUMS.txt').exists(),'Frozen release'
for d in ['step','preview','stl','reports','renders','references','provenance','bambu']:(O/d).mkdir(parents=True,exist_ok=True)
source_hashes={}
for line in (S/'SHA256SUMS.txt').read_text().splitlines():
 h,n=line.split('  ',1);assert hashlib.sha256((S/n).read_bytes()).hexdigest()==h,n
 source_hashes[n]=h
for node in ast.parse((R/'scripts/build_balanced_qre_v032.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['box','cyl','load','mesh']:exec(compile(ast.Module(body=[node],type_ignores=[]),'helper','exec'))
for node in ast.parse((R/'scripts/build_compact_v010.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['bb','repair_collinear_boundary']:exec(compile(ast.Module(body=[node],type_ignores=[]),'helper','exec'))
P=json.loads((S/'parameters.json').read_text());M=json.loads((S/'assembly_manifest.json').read_text());E={e['name']:e for e in M['parts']}
old=load(S/'step/01_QRE_minimal_port.step')
# The measured native planar center step has one slightly slanted side.
# Derive both boundaries from the actual STEP face; retain its slope at scale 1.
f=max((f for f in old.Faces() if abs(f.BoundingBox().zmin-3.78)<1e-5 and abs(f.BoundingBox().zmax-3.78)<1e-5),key=lambda f:f.Area())
v=np.array([p.toTuple()[:2] for p in f.outerWire().Vertices()]);left=v[v[:,0]<0];right=float(v[:,0].max())
slope,intercept=np.polyfit(left[:,1],left[:,0],1)
fit_error=float(max(abs(left[:,0]-(slope*left[:,1]+intercept))));assert fit_error<.001
trim=.5;drop=1.;shoulder_z=4.78
left_at=lambda y:float(slope*y+intercept)
def region(inset=0):
 points=[cq.Vector(left_at(-20)+inset,-20,-20),cq.Vector(right-inset,-20,-20),cq.Vector(right-inset,20,-20),cq.Vector(left_at(20)+inset,20,-20)]
 return cq.Solid.extrudeLinear(cq.Wire.makePolygon(points,close=True),[],cq.Vector(0,0,50))
outer=region();center=region(trim)
# Lower the entire center solid, including PCB lands, pocket, screw bosses,
# optics/header relief and flat floor. Do not scale the PCB pocket.
old_center=old.intersect(center);lower=old_center.translate((0,0,-drop))
# The 0.5 mm side strips are relieved up to the original outer shoulder ceiling.
# Outer latch beds, clip screw posts, side foot contacts and clip poses stay fixed.
side_relief=outer.cut(center).intersect(box(-30,30,-20,20,-10,shoulder_z))
base=old.cut(center).cut(side_relief).fuse(lower).clean()
assert base.isValid() and len(base.Solids())==1
rep={'status':'BUILDING','cad':{},'mesh':{},'sources':source_hashes,'changes':{'trim_per_side_mm':trim,'platform_and_sensor_drop_mm':drop,'region':'Launcher-facing central underside step, not PCB slot','center_left_slope_dx_dy':float(slope),'center_left_intercept_mm':float(intercept),'source_edge_plane_fit_max_error_mm':fit_error,'old_right_x_mm':right,'new_right_x_mm':right-trim,'side_relief_to_z_mm':shoulder_z},'preserved':{}}
manifest=dict(M,version='0.33',parts=[])
for e in M['parts']:
 n=e['name'];e=dict(e)
 if n=='01_QRE_minimal_port':
  cq.exporters.export(base,str(O/'step'/(n+'.step')));base.exportBrep(str(O/'step'/(n+'.brep')))
  a=mesh(base);a.export(O/e['filename']);p=a.copy()
  for ax,angle in zip([(1,0,0),(0,1,0),(0,0,1)],e['print_rotation_deg']):
   if angle:p.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(angle),ax))
  shift=np.r_[-p.bounds[:,:2].mean(axis=0),-p.bounds[0,2]];p.apply_translation(shift);p.export(O/'stl'/(n+'.stl'))
  e.update(print_translation_mm=shift.tolist(),description='Center underside step trimmed 0.5 mm per side; central platform, board seat and sensor screw posts 1 mm lower.',source='v033 modified v032 native CAD')
  rep['cad'][n]=dict(volume_mm3=base.Volume(),bounds_mm=bb(base),solids=1)
  rep['mesh'][n]=dict(volume_mm3=a.volume,watertight=a.is_watertight,components=len(a.split()),bed_min_z_mm=float(p.bounds[0,2]))
 elif e['printable']:
  z=-drop if n=='03_QRE_pressure_bar' else 0
  s=load(S/'step'/(n+'.step')).translate((0,0,z))
  if z:
   cq.exporters.export(s,str(O/'step'/(n+'.step')));s.exportBrep(str(O/'step'/(n+'.brep')))
   a=trimesh.load(S/e['filename'],force='mesh');a.apply_translation((0,0,z));a.export(O/e['filename'])
   # Same shape: reuse the physical part and byte-identical manufacturing STL.
   e['print_translation_mm'][1]+=drop
  else:
   for d,ext in [('step','.step'),('step','.brep'),('preview','.stl')]:
    src=S/d/(n+ext)
    if src.exists():shutil.copy2(src,O/d/(n+ext))
  shutil.copy2(S/'stl'/(n+'.stl'),O/'stl'/(n+'.stl'))
  e.update(description='Reuse existing v032 part; '+('installed 1 mm lower on the new sensor posts.' if z else 'unchanged assembly pose.'),source='v032 reused manufacturing STL')
  rep['cad'][n]=dict(volume_mm3=s.Volume(),bounds_mm=bb(s),solids=1)
 elif e['reference']:
  z=-drop if e['group']!='hardware' or n.startswith('REF_M2x4_SENSOR') else 0
  a=trimesh.load(S/e['filename'],force='mesh');a.apply_translation((0,0,z));a.export(O/e['filename'])
  e['source']='v032 nominal component envelope'+(' translated exactly 1 mm downward' if z else ' at unchanged pose')
 manifest['parts'].append(e)
# Independent intent checks: entire moved solid matches the old center exactly;
# only the two narrow underside relief strips differ outside that moving region.
assert lower.cut(base).Volume()<.001
outside_before=old.cut(center).cut(side_relief);outside_after=base.cut(center)
diff=outside_before.cut(outside_after).Volume()+outside_after.cut(outside_before).Volume();assert diff<.001,diff
rep['preserved']['outside_intentional_region_symmetric_difference_mm3']=diff
for label,roi in [('hinge_LEFT',box(-35,-16,-6,6,-20,13.284)),('hinge_RIGHT',box(16,35,-6,6,-20,13.284))]:
 a=old.intersect(roi);b=base.intersect(roi);diff=a.cut(b).Volume()+b.cut(a).Volume();assert diff<.001
 rep['preserved'][label+'_symmetric_difference_mm3']=diff
# Exact source section solids are supplied for transparent inspection.
for n,s in [('REF_OLD_center',old_center),('REF_NEW_center',lower),('REF_side_relief',old.intersect(side_relief))]:
 cq.exporters.export(s,str(O/'references'/(n+'.step')))
 vs,fs=s.tessellate(.025,.08);trimesh.Trimesh([v.toTuple() for v in vs],fs,process=True).export(O/'references'/(n+'.stl'))
params=dict(P);params.update(version='0.33',architecture='Narrowed launcher-facing step and 1 mm lower center platform; side clips fixed',replacement_parts=['01_QRE_minimal_port'],reuse=['v032 centered pressure plate','v032 thicker latch crossbar','original latches','existing separate v024 M5 platform','two M2x4 sensor screws','two M2x5 clip screws'],physical_feedback='Photo IMG_7549: central step too wide for launcher black area; narrow 0.5 mm per side and lower center/sensor 1 mm',interpretation='User confirmed: lower center platform and sensor; keep side clips fixed',central_step_trim_per_side_mm=trim,central_platform_drop_mm=drop,old_center_step_width_at_y0_mm=right-intercept,new_center_step_width_at_y0_mm=right-intercept-2*trim,central_left_boundary=dict(slope_dx_dy=float(slope),old_intercept_mm=float(intercept),new_intercept_mm=float(intercept+trim)),central_right_boundary_mm=[right,right-trim],minimum_center_to_side_join_height_mm=5.4-4.78)
for key in ['optical_face_z_mm','header_tail_relief_floor_z_mm','keeper_tab_bottom_z_mm','keeper_tab_top_z_mm','keeper_nominal_contact_z_mm','main_flat_floor_z_mm','flattening_patch_bottom_z_mm','keeper_front_bridge_bottom_z_mm','keeper_front_bridge_top_z_mm']:params[key]-=drop
for key in ['PCB_box_mm','keeper_flat_contact_box_mm']:
 params[key]=list(params[key]);params[key][4]-=drop;params[key][5]-=drop
params['main_flat_floor_z_mm']=5.4;params['outer_flat_floor_z_mm']=6.4
params['comparison']={'central_platform_drop_mm':drop,'center_width_reduction_mm':1.0,'old_base_volume_mm3':old.Volume(),'new_base_volume_mm3':base.Volume()}
params['limits']=['Digital checks cover modeled parts; installed launcher clearance, retention and optical response need a physical fit check.','The new central step and sensor seat intentionally change the original optical datum by minus 1 mm; the prior launcher-top reference is not a measured collision model.','Side clips, hinge beds, crossbar and separate M5 platform retain their prior poses.','Nominal board and plugs retain v032 clearances; solder tails, wire routing and purchased screw envelopes remain provisional.','Center-to-side wall connection is 0.62 mm high at the flat shoulder; printed strength needs inspection.','No printer dispatch.']
params['legacy_launcher_top_reference_z_mm']=params.pop('launcher_top_z_mm')
(O/'parameters.json').write_text(json.dumps(params,indent=2));(O/'assembly_manifest.json').write_text(json.dumps(manifest,indent=2))
rep['status']='CAD_EXPORT_PASS';(O/'reports/cad_validation.json').write_text(json.dumps(rep,indent=2))
parts=[load(O/'step'/(e['name']+'.step')) for e in manifest['parts'] if e['printable']]
cq.exporters.export(cq.Compound.makeCompound(parts),str(O/'LaunchLab_v033_flush_QRE_assembly.step'))
for n in ['LICENSE.txt','references/QRE_BP_port_LICENSE.txt']:shutil.copy2(S/n,O/n)
shutil.copy2('/tmp/IMG_7549-thumb.png',O/'references/IMG_7549_preview.png');shutil.copy2('/tmp/IMG_7549-ref.png',O/'references/IMG_7549_auxiliary.png')
(O/'references/photo_provenance.json').write_text(json.dumps(dict(source='/Users/mingj/Downloads/IMG_7549.HEIC',sha256=hashlib.sha256(Path('/Users/mingj/Downloads/IMG_7549.HEIC').read_bytes()).hexdigest(),preview_stream=51,auxiliary_stream=64,interpretation='Center underside stripe above black launcher section; photo provides feedback, not metric calibration'),indent=2))
print('V033_BASE_READY',json.dumps(rep['changes']),flush=True)
