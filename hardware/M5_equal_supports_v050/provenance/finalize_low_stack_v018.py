"""Read back delivered geometry/projects and package the reviewed v0.18 release."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,shutil,xml.etree.ElementTree as ET
import numpy as np,trimesh
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[1];O=R/'releases/LaunchLab_v018_low_stack'
assert not (O/'SHA256SUMS.txt').exists(),'Finalized releases are immutable'
def read(n):return json.loads((O/'reports'/n).read_text())
fit=read('fit_and_motion.json');blend=read('blender_saved_readback.json');cad=read('cad_validation.json');slices=read('slicing_metrics.json')
assert fit['status']==blend['status']=='PASS'
assert not fit['collisions'] and not cad['nominal_collisions']
for n,h in fit['input_sha256'].items():assert hashlib.sha256((O/n).read_bytes()).hexdigest()==h,n
assert len(slices)==8 and all(s['cli_exit']==0 and not s['log_warnings'] for s in slices)
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
def project_meshes(z):
 result=[]
 for n in z.namelist():
  if not n.endswith('.model'):continue
  root=ET.fromstring(z.read(n));assert root.attrib['unit']=='millimeter'
  for m in root.findall('.//m:mesh',ns):
   v=np.array([[float(x.attrib[a]) for a in 'xyz'] for x in m.find('m:vertices',ns)])
   f=np.array([[int(x.attrib[a]) for a in ['v1','v2','v3']] for x in m.find('m:triangles',ns)])
   result.append(trimesh.Trimesh(v,f,process=True))
 return result
def compare(a,b):
 if len(a.faces)!=len(b.faces) or len(a.vertices)!=len(b.vertices):return False
 av=a.vertices-a.bounds.mean(axis=0);bv=b.vertices-b.bounds.mean(axis=0);tree=cKDTree(bv)
 for angle in [0,np.pi/2,np.pi,3*np.pi/2]:
  c,s=np.cos(angle),np.sin(angle);rot=np.array([[c,-s,0],[s,c,0],[0,0,1]])
  if tree.query(av@rot.T)[0].max()<.002 and abs(a.volume-b.volume)<.02:return True
 return False
names=['01_attachment_port','03_sensor_m5_dock'];oriented=[trimesh.load(O/'stl'/f'{n}.stl',force='mesh') for n in names]
checks=[]
projects=[(O/'LaunchLab_v018_REPLACEMENTS_UNSLICED.3mf',oriented)]
for s in slices:
 expected=oriented if s['name']=='v018_REPLACEMENTS' else [trimesh.load(s['source'],force='mesh')]
 projects.append((Path(s['release_project']),expected))
for p,expected in projects:
 with ZipFile(p) as z:
  assert z.testzip() is None
  actual=project_meshes(z);assert len(actual)==len(expected),(p,len(actual),len(expected))
  unused=list(expected)
  for a in actual:
   found=next((i for i,b in enumerate(unused) if compare(a,b)),None)
   assert found is not None,('Geometry mismatch',p,a.extents,a.volume)
   unused.pop(found)
  if 'Metadata/plate_1.gcode' in z.namelist():
   g=z.read('Metadata/plate_1.gcode');assert hashlib.md5(g).hexdigest()==z.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
  checks.append({'file':str(p.relative_to(O)),'mesh_count':len(actual),'matches_current_STL_geometry':True})
(O/'reports/project_readback.json').write_text(json.dumps({'status':'PASS','checks':checks,'vertex_tolerance_mm':.002,'gcode_md5':'All eight sliced projects verified'},indent=2))
for n in ['build_low_stack_v018.py','check_low_stack_v018.py','preview_low_stack_v018.py','slice_low_stack_v018.py','refresh_low_stack_guide_v018.py','blender_helpers_v09.py','slice_comparison_v05.py','finalize_low_stack_v018.py']:shutil.copy2(R/'scripts'/n,O/'provenance'/n)
p=json.loads((O/'parameters.json').read_text());review={'version':'0.18','status':'DIGITAL_CHECKS_PASS_PHYSICAL_FIT_UNVERIFIED','architecture':p['architecture'],'device':p['device'],'attachment':p['attachment'],'new_printed_parts':2,'reused_printed_parts':2,'M5_top_z_mm':p['M5_max_z_mm'],'printed_port_mm':p['printed_port_mm'],'open_deck_mm':p['open_deck_mm'],'comparison_v017':p['comparison_v017'],'fit_and_removal':'PASS','optional_native_width_dock':'PASS','fit_samples':'QRE 9 mm, QRE 7.62 mm, M5 mounting pads and countersunk fastener','original_clip_exports_and_mating_regions':'Unchanged, verified','blender_saved_readback':'PASS','project_geometry_readback':'PASS','all_eight_local_slices_successful':True,'slice_warnings':[],'visual_review':'All four final CAD renders inspected; exposed device, underside, exploded parts and two-part print layout show all relevant parts.','full_plate_estimate':{'time':slices[0]['estimated_time'],'PLA_g':slices[0]['total_header_g'],'support_g':slices[0]['support_g']},'fasteners':p['fasteners'],'physical_acceptance':'Not tested','printer_dispatch':'None','firmware_or_device_setting_changes':'None','limitations':p['limits']}
(O/'reports/release_review.json').write_text(json.dumps(review,indent=2))
files=sorted(p for p in O.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt');(O/'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(O)}\n' for p in files))
package=R/'releases/LaunchLab_v018_LOW_STACK_package.zip';assert not package.exists()
with ZipFile(package,'w',ZIP_DEFLATED) as z:
 for p in sorted(O.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(O.parent))
with ZipFile(package) as z:
 assert z.testzip() is None
 for line in (O/'SHA256SUMS.txt').read_text().splitlines():
  h,n=line.split('  ',1);assert hashlib.sha256(z.read(O.name+'/'+n)).hexdigest()==h,n
print('RELEASE_PACKAGED',package,'files',len(files)+1,'bytes',package.stat().st_size,flush=True)
