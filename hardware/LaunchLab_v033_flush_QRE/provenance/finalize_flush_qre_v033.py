"""Verify saved geometry, actual join paths and frozen source, then package v033."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,shutil,struct,ast
import cadquery as cq
import numpy as np,trimesh
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[1];O=R/'releases/LaunchLab_v033_flush_QRE';S=R/'releases/LaunchLab_v032_balanced_QRE'
assert not (O/'SHA256SUMS.txt').exists()
for name in ['fit_and_motion.json','blender_saved_readback.json','project_readback.json','base_layers.json','section_readback.json']:
 assert json.loads((O/'reports'/name).read_text())['status']=='PASS',name
metrics=json.loads((O/'reports/slicing_metrics.json').read_text());assert list(metrics)==['new_base'];assert all(m['cli_exit']==0 and not m['log_warnings'] for m in metrics.values())
M=json.loads((O/'assembly_manifest.json').read_text());P=json.loads((O/'parameters.json').read_text())
data=(O/'LaunchLab_v033_flush_QRE.glb').read_bytes();length,kind=struct.unpack_from('<II',data,12);assert kind==0x4E4F534A
g=json.loads(data[20:20+length]);binlen,binkind=struct.unpack_from('<II',data,20+length);assert binkind==0x004E4942
binary=memoryview(data)[28+length:28+length+binlen]
assert {n['name'] for n in g['nodes'] if 'mesh' in n}=={e['name'] for e in M['parts']}
def positions(index):
 a=g['accessors'][index];v=g['bufferViews'][a['bufferView']];assert a['componentType']==5126 and a['type']=='VEC3'
 return np.ndarray((a['count'],3),dtype='<f4',buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',12),4)).astype(float)
scene=trimesh.load(O/'LaunchLab_v033_flush_QRE.glb',force='scene');deltas={}
for e in M['parts']:
 n=next(n for n in g['nodes'] if n['name']==e['name']);prims=g['meshes'][n['mesh']]['primitives'];vertices=np.concatenate([positions(p['attributes']['POSITION']) for p in prims]);transform,_=scene.graph.get(e['name']);vertices=trimesh.transform_points(vertices,transform)*1000
 b=trimesh.load(O/e['filename'],force='mesh');expected=b.vertices[:,[0,2,1]]*np.array([1,1,-1]);delta=max(cKDTree(vertices).query(expected)[0].max(),cKDTree(expected).query(vertices)[0].max());assert delta<.002
 assert sum(g['accessors'][p['indices']]['count']//3 for p in prims)==len(b.faces);deltas[e['name']]=float(delta)
for n in ['01_QRE_minimal_port','02_QRE_clip_keeper','03_QRE_pressure_bar']:
 s=cq.Shape.importBrep(str(O/'step'/(n+'.brep')));assert s.isValid() and len(s.Solids())==1
protected={}
for src in [S,R/'releases/LaunchLab_v024_stepped_platform']:
 files=0
 for line in (src/'SHA256SUMS.txt').read_text().splitlines():
  h,n=line.split('  ',1);assert hashlib.sha256((src/n).read_bytes()).hexdigest()==h,(src.name,n);files+=1
 protected[src.name]=dict(all_frozen_files_unchanged=True,files=files)
for name in ['01_lowered_assembly','02_narrowed_underside','03_before_after','04_new_base','05_center_section']:
 assert (O/'renders'/(name+'.png')).stat().st_size>100000,name
assert P['replacement_parts']==['01_QRE_minimal_port']
review=dict(version='0.33',status='DIGITAL_CHECKS_PASS_PHYSICAL_FIT_UNVERIFIED',requested_changes=dict(trim_per_side_mm=.5,center_platform_and_sensor_drop_mm=1,side_clips_fixed=True),confirmed_interpretation=P['interpretation'],new_center_width_at_Y0_mm=P['new_center_step_width_at_y0_mm'],PCB_slot_width_mm=9.24,PCB_seat_z_mm=5.4,optical_face_z_mm=3.1,replacement_parts=P['replacement_parts'],reuse=P['reuse'],valid_single_solid_CAD=True,watertight_STLs=True,Blender_saved_and_reopened=True,GLB_vertex_deltas_mm=deltas,protected_release_checks=protected,actual_model_layers=216,actual_join_paths='PASS',local_slice=dict(time=metrics['new_base']['estimated_time'],PLA_g=metrics['new_base']['total_header_g'],support_g=metrics['new_base']['support_g'],supports='Tree Slim'),printer_dispatch='None',limits=P['limits'])
(O/'reports/release_review.json').write_text(json.dumps(review,indent=2))
names=['build_flush_qre_v033.py','check_flush_qre_v033.py','section_flush_qre_v033.py','render_flush_qre_v033.py','prepare_flush_qre_v033.py','check_flush_layers_v033.py','finalize_flush_qre_v033.py','build_balanced_qre_v032.py','build_compact_v010.py','blender_helpers_v09.py','render_minimal_qre_v025.py','slice_comparison_v05.py','finalize_low_stack_v018.py']
for n in names:shutil.copy2(R/'scripts'/n,O/'provenance'/n)
(O/'provenance/REBUILD.md').write_text('Requires the custom-beypass checkout and frozen v032 release. Choose a new output path for edits. Run build_flush_qre_v033.py, check_flush_qre_v033.py, section_flush_qre_v033.py, Blender --background --factory-startup --python scripts/render_flush_qre_v033.py, prepare_flush_qre_v033.py, check_flush_layers_v033.py, then finalize_flush_qre_v033.py. CAD/STL mm; Blender/GLB metres. One base-only local Tree Slim slice. No printer dispatch.\n')
files=sorted(p for p in O.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt');(O/'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(O)}\n' for p in files))
package=R/'releases/LaunchLab_v033_FLUSH_QRE_package.zip';assert not package.exists()
with ZipFile(package,'w',ZIP_DEFLATED) as z:
 for p in sorted(O.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(O.parent))
with ZipFile(package) as z:
 assert z.testzip() is None
 for line in (O/'SHA256SUMS.txt').read_text().splitlines():
  h,n=line.split('  ',1);assert hashlib.sha256(z.read(O.name+'/'+n)).hexdigest()==h,n
print('V033_PACKAGED',package,'files',len(files)+1,'bytes',package.stat().st_size,flush=True)
