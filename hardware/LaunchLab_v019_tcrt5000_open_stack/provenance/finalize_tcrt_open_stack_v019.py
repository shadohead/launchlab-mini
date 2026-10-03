"""Verify complete OLD TCRT inventory, project geometry, preserved releases and ZIP bytes."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import ast,hashlib,json,shutil,xml.etree.ElementTree as ET
import numpy as np,trimesh
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[1];O=R/'releases/LaunchLab_v019_tcrt5000_open_stack'
assert not (O/'SHA256SUMS.txt').exists(),'Delivered releases are immutable'
def read(n):return json.loads((O/'reports'/n).read_text())
fit=read('fit_and_motion.json');blend=read('blender_saved_readback.json');cad=read('cad_validation.json');slices=read('slicing_metrics.json');inv=json.loads((O/'print_inventory.json').read_text())
assert fit['status']==blend['status']=='PASS'
assert blend['embedded_guide_matches_release_README']
assert not fit['collisions'] and not cad['nominal_collisions']
assert len(slices)==8 and all(s['cli_exit']==0 and not s['log_warnings'] for s in slices)
assert read('visual_review.json')['status']=='PASS'
for n,h in fit['input_sha256'].items():assert hashlib.sha256((O/n).read_bytes()).hexdigest()==h,n
assert len(inv['printed_parts'])==sum(e['quantity_first_build'] for e in inv['printed_parts'])==5
assert sum(e['quantity_upgrade'] for e in inv['printed_parts'])==3
names=[e['name'] for e in inv['printed_parts']];assert set(p.stem for p in (O/'stl').glob('*.stl'))==set(names)
assert set(p.stem for p in (O/'extras').glob('*.stl'))=={'11_TCRT_SEAT_FIT','12_TCRT_KEEPER_FIT','13_M5_MOUNT_FIT'}
with ZipFile(R/'reference files/LaunchLab_v02_CAD_package.zip') as z:
 for n in names[3:]:
  for folder,ext in [('stl','.stl'),('preview','.stl'),('step','.step')]:assert (O/folder/(n+ext)).read_bytes()==z.read('LaunchLab_v02/'+folder+'/'+n+ext),(n,folder)
for e in inv['printed_parts']:
 assert hashlib.sha256((O/e['print_filename']).read_bytes()).hexdigest()==e['sha256']
 m=trimesh.load(O/e['print_filename'],force='mesh');assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
for n in ast.parse((R/'scripts/finalize_low_stack_v018.py').read_text()).body:
 if isinstance(n,ast.FunctionDef) and n.name in ['project_meshes','compare']:exec(compile(ast.Module(body=[n],type_ignores=[]),'readback_helpers','exec'))
meshes={e['name']:trimesh.load(O/e['print_filename'],force='mesh') for e in inv['printed_parts']}
fit_names=['11_TCRT_SEAT_FIT','12_TCRT_KEEPER_FIT'];fit_meshes=[trimesh.load(O/'extras'/f'{n}.stl',force='mesh') for n in fit_names]
groups={'ALL_PARTS':[meshes[n] for n in names],'REPLACEMENTS':[meshes[n] for n in names[:3]],'CLIPS':[meshes[n] for n in names[3:]],'PORT':[meshes[names[0]]],'SENSOR_CRADLE':[meshes[names[1]]],'M5_TOP_DOCK':[meshes[names[2]]],'SENSOR_FIT':fit_meshes,'M5_MOUNT_FIT':[trimesh.load(O/'extras/13_M5_MOUNT_FIT.stl',force='mesh')]}
projects=[(O/f'LaunchLab_v019_{name}_UNSLICED.3mf',groups[name]) for name in ['ALL_PARTS','REPLACEMENTS','CLIPS','SENSOR_FIT']]
projects += [(Path(s['release_project']),groups[s['name'].split('v019_OLD_TCRT_',1)[1]]) for s in slices]
checks=[]
for p,expected in projects:
 with ZipFile(p) as z:
  assert z.testzip() is None
  actual=project_meshes(z);build_count=0
  for n in z.namelist():
   if not n.endswith('.model'):continue
   root=ET.fromstring(z.read(n));build_count+=len(root.findall('.//m:build/m:item',ns))
   for t in root.findall('.//*[@transform]'):
    v=[float(x) for x in t.attrib['transform'].split()];assert len(v)==12;mat=np.array(v[:9]).reshape(3,3);assert np.allclose(mat@mat.T,np.eye(3),atol=1e-6) and abs(np.linalg.det(mat)-1)<1e-6
  assert build_count==len(actual)==len(expected),(p,build_count,len(actual),len(expected))
  unused=list(expected)
  for a in actual:
   assert a.is_watertight and len(a.split())==1
   i=next((i for i,b in enumerate(unused) if compare(a,b)),None);assert i is not None,('Geometry mismatch',p,a.extents,a.volume);unused.pop(i)
  if 'Metadata/plate_1.gcode' in z.namelist():assert hashlib.md5(z.read('Metadata/plate_1.gcode')).hexdigest()==z.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
  checks.append({'file':str(p.relative_to(O)),'build_items':build_count,'mesh_count':len(actual),'geometry_matches_current_STLs':True,'unit_scale_transforms':True,'zip_integrity':'PASS'})
(O/'reports/project_readback.json').write_text(json.dumps({'status':'PASS','checks':checks,'vertex_tolerance_mm':.002,'gcode_md5':'All eight sliced projects verified'},indent=2))
protected={**cad['protected_v017_packages_sha256'],**inv['protected_packages_sha256']}
for n,h in protected.items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
for folder in ['LaunchLab_v017_open_stack','LaunchLab_v017_complete_first_build','LaunchLab_v018_low_stack']:
 src=R/'releases'/folder
 for l in (src/'SHA256SUMS.txt').read_text().splitlines():
  h,n=l.split('  ',1);assert hashlib.sha256((src/n).read_bytes()).hexdigest()==h,(folder,n)
for n in ['build_tcrt_open_stack_v019.py','check_tcrt_open_stack_v019.py','preview_tcrt_open_stack_v019.py','slice_tcrt_open_stack_v019.py','refresh_tcrt_guide_v019.py','finalize_tcrt_open_stack_v019.py','build_low_stack_v018.py','build_compact_v010.py','check_open_stack_v017.py','finalize_low_stack_v018.py','blender_helpers_v09.py','slice_comparison_v05.py']:shutil.copy2(R/'scripts'/n,O/'provenance'/n)
p=json.loads((O/'parameters.json').read_text());review={'version':'0.19','variant':p['variant'],'status':'COMPLETE_FIRST_BUILD_DIGITAL_CHECKS_PASS_PHYSICAL_FIT_UNVERIFIED','sensor_identity':p['sensor_identity'],'measurement_source':p['measurement_source'],'core_footprint_mm':p['core_footprint_mm'],'clip_span_mm':p['clip_span_mm'],'height_above_launcher_mm':p['height_above_launcher_mm'],'M5_top_z_mm':p['M5_max_z_mm'],'sensor_PCB_mm':p['sensor_PCB_mm'],'sensor_component_thickness_mm':p['sensor_total_component_thickness_mm'],'pot_to_M5_gap_mm':p['pot_to_M5_gap_mm'],'PCB_xy_clearance_mm':p['PCB_xy_clearance_mm'],'PCB_vertical_capture_play_mm':p['PCB_vertical_capture_play_mm'],'complete_printed_piece_count':5,'replacement_piece_count':3,'printed_parts':names,'original_clip_exports_unchanged':True,'fit_and_removal':'PASS','saved_Blender_and_project_readback':'PASS','all_eight_local_slices_successful':True,'slice_warnings':[],'full_plate_estimate':{'time':slices[0]['estimated_time'],'PLA_g':slices[0]['total_header_g'],'support_g':slices[0]['support_g']},'fasteners':p['fasteners'],'preserved_packages_sha256':protected,'physical_acceptance':'Not tested','printer_dispatch':'None','firmware_or_device_setting_changes':'None','limitations':p['limits']}
(O/'reports/release_review.json').write_text(json.dumps(review,indent=2))
files=sorted(p for p in O.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt');(O/'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(O)}\n' for p in files))
package=R/'releases/LaunchLab_v019_OLD_TCRT_OPEN_STACK_package.zip';assert not package.exists()
with ZipFile(package,'w',ZIP_DEFLATED) as z:
 for p in sorted(O.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(O.parent))
with ZipFile(package) as z:
 assert z.testzip() is None
 for l in (O/'SHA256SUMS.txt').read_text().splitlines():
  h,n=l.split('  ',1);assert hashlib.sha256(z.read(O.name+'/'+n)).hexdigest()==h,n
 for e in inv['printed_parts']:assert O.name+'/'+e['print_filename'] in z.namelist()
 assert json.loads(z.read(O.name+'/print_inventory.json'))['first_build_printed_piece_count']==5
print('COMPLETE_OLD_TCRT_ZIP_VERIFIED',package,'files',len(files)+1,'bytes',package.stat().st_size,flush=True)
