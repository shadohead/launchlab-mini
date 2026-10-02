"""Freeze the reviewed M5-only revision after export and slice readback."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,shutil,struct
import numpy as np,trimesh
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[1];O=R/'releases/LaunchLab_v040_right_block_print';S=R/'releases/LaunchLab_v024_stepped_platform'
assert not (O/'SHA256SUMS.txt').exists()
for n in ['cad_validation.json','blender_saved_readback.json','project_readback.json','actual_paths.json']:assert json.loads((O/'reports'/n).read_text())['status']=='PASS'
M=json.loads((O/'assembly_manifest.json').read_text());P=json.loads((O/'parameters.json').read_text());metrics=json.loads((O/'reports/slicing_metrics.json').read_text());assert all(m['cli_exit']==0 and not m['log_warnings'] for m in metrics.values())
data=(O/'LaunchLab_v040_right_block_print.glb').read_bytes();length,kind=struct.unpack_from('<II',data,12);assert kind==0x4E4F534A
g=json.loads(data[20:20+length]);binlen,binkind=struct.unpack_from('<II',data,20+length);assert binkind==0x004E4942;binary=memoryview(data)[28+length:28+length+binlen]
assert {n['name'] for n in g['nodes'] if 'mesh' in n}=={e['name'] for e in M['parts']}
def positions(index):
 a=g['accessors'][index];v=g['bufferViews'][a['bufferView']];assert a['componentType']==5126 and a['type']=='VEC3'
 return np.ndarray((a['count'],3),dtype='<f4',buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',12),4)).astype(float)
scene=trimesh.load(O/'LaunchLab_v040_right_block_print.glb',force='scene');deltas={}
for e in M['parts']:
 n=next(n for n in g['nodes'] if n['name']==e['name']);prims=g['meshes'][n['mesh']]['primitives'];v=np.concatenate([positions(p['attributes']['POSITION']) for p in prims]);t,_=scene.graph.get(e['name']);v=trimesh.transform_points(v,t)*1000
 source=trimesh.load(O/e['filename'],force='mesh');expected=source.vertices[:,[0,2,1]]*np.array([1,1,-1]);delta=max(cKDTree(v).query(expected)[0].max(),cKDTree(expected).query(v)[0].max());assert delta<.002
 assert sum(g['accessors'][p['indices']]['count']//3 for p in prims)==len(source.faces);deltas[e['name']]=float(delta)
 if e['reference']:assert (O/e['filename']).read_bytes()==(S/e['filename']).read_bytes()
source=trimesh.load(O/'preview/01_M5_stepped_platform.stl',force='mesh');printed=trimesh.load(O/'stl/01_M5_stepped_platform.stl',force='mesh');expected=source.copy();expected.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]));expected.apply_translation(P['print_translation_mm'])
assert max(cKDTree(expected.vertices).query(printed.vertices)[0].max(),cKDTree(printed.vertices).query(expected.vertices)[0].max())<.0001
for n in ['01_topdown_before_after','02_assembled','03_bare_mount']:assert (O/'renders'/(n+'.png')).stat().st_size>50000
for line in (S/'SHA256SUMS.txt').read_text().splitlines():
 h,n=line.split('  ',1);assert hashlib.sha256((S/n).read_bytes()).hexdigest()==h,n
(O/'reports/release_review.json').write_text(json.dumps(dict(status='DIGITAL_CHECKS_PASS_PHYSICAL_THUMB_REACH_UNVERIFIED',version='0.40',matching_factory_edge=P['edge_finish'],GLB_vertex_deltas_mm=deltas,factory_pose_and_fastener_references_byte_identical=True,manufacturing_pose='Existing +90 degree Y side orientation, independently checked',only_replacement='01_M5_stepped_platform',local_slice=metrics,source_v024_unchanged=True,printer_dispatch='None'),indent=2))
for n in ['build_matching_edge_v040.py','render_matching_edge_v040.py','prepare_matching_edge_v040.py','finalize_matching_edge_v040.py','check_right_block_paths_v040.py','build_compact_v010.py','blender_helpers_v09.py','render_minimal_qre_v025.py','slice_comparison_v05.py','finalize_low_stack_v018.py']:shutil.copy2(R/'scripts'/n,O/'provenance'/n)
if (O/'README_source_v024.md').exists():shutil.move(O/'README_source_v024.md',O/'provenance/README_source_v024.md')
metric=next(iter(metrics.values()))
with (O/'README.md').open('a') as f:f.write(f"\nReplacement slice estimate: {metric['estimated_time']}, {metric['total_header_g']:.2f} g PLA. All manufacturing layers and the saved 3MF geometry/settings/G-code checksum pass digital checks.\n")
files=sorted(p for p in O.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt');(O/'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(O)}\n' for p in files))
package=R/'releases/LaunchLab_v040_RIGHT_BLOCK_PRINT_package.zip';assert not package.exists()
with ZipFile(package,'w',ZIP_DEFLATED) as z:
 for p in sorted(O.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(O.parent))
with ZipFile(package) as z:
 assert z.testzip() is None
 for line in (O/'SHA256SUMS.txt').read_text().splitlines():
  h,n=line.split('  ',1);assert hashlib.sha256(z.read(O.name+'/'+n)).hexdigest()==h
print('V040_M5_PACKAGE_VERIFIED',package,flush=True)
