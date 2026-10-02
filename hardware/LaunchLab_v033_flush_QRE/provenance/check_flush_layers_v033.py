"""Read actual model deposition on both sides of the narrowed center joins."""
from pathlib import Path
from zipfile import ZipFile
import json,re,xml.etree.ElementTree as ET
import numpy as np,trimesh
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[1];O=R/'releases/LaunchLab_v033_flush_QRE'
P=json.loads((O/'parameters.json').read_text());M=json.loads((O/'assembly_manifest.json').read_text());name='01_QRE_minimal_port';entry=next(e for e in M['parts'] if e['name']==name)
with ZipFile(O/'bambu/LaunchLab_v033_P1S_PLA_BASE_TREE_SLIM.3mf') as z:
 ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'};prod='http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
 cfg=ET.fromstring(z.read('Metadata/model_settings.config'));target=next(ob for ob in cfg.findall('object') if ob.find("metadata[@key='name']").attrib['value']==name)
 root=ET.fromstring(z.read('3D/3dmodel.model'));item=root.find(f"m:build/m:item[@objectid='{target.attrib['id']}']",ns);obj=root.find(f"m:resources/m:object[@id='{target.attrib['id']}']",ns);comp=obj.find('m:components/m:component',ns)
 child=ET.fromstring(z.read(comp.attrib['{'+prod+'}path'].lstrip('/')));v=np.array([[float(v.attrib[k]) for k in 'xyz'] for v in child.findall('.//m:vertex',ns)])
 def matrix(s):
  a=np.array([float(v) for v in s.split()]).reshape(4,3);t=np.eye(4);t[:3,:3]=a[:3].T;t[:3,3]=a[3];return t
 inverse=np.linalg.inv(matrix(item.attrib['transform'])@matrix(comp.attrib['transform']))
 source=trimesh.load(O/'stl'/(name+'.stl'),force='mesh');child_shift=v.min(0)-source.bounds[0]
 assert max(cKDTree(v-child_shift).query(source.vertices)[0].max(),cKDTree(source.vertices).query(v-child_shift)[0].max())<.001
 settings=json.loads(z.read('Metadata/project_settings.config'));meta=json.loads(z.read('Metadata/plate_1.json'))
 tool=np.array([float(v) for v in settings['extruder_offset'][int(meta['first_extruder'])].split('x')]+[0.]);g=z.read('Metadata/plate_1.gcode').decode()
assert entry['print_rotation_deg']==[0,-90,0] and settings['layer_height']=='0.2'
shift=np.array(entry['print_translation_mm']);undo_rotation=trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0])[:3,:3]
known={'Outer wall','Inner wall','Top surface','Bottom surface','Internal solid infill','Bridge','Overhang wall','Floating vertical shell','Gap infill','Sparse infill'}
state=np.zeros(3);relative=False;E=0.;layer=None;height=None;feature='';all_layers={};web={s:{} for s in ['LEFT','RIGHT']};layer_x={}
for line in g.splitlines():
 if line.startswith('; FEATURE: '):feature=line[11:].strip()
 if line.startswith('; Z_HEIGHT: '):layer=float(line[12:])
 if line.startswith('; LAYER_HEIGHT: '):height=float(line[16:])
 code=line.split(';',1)[0].strip();fields=code.split()
 if not fields:continue
 cmd=fields[0];d={k:float(v) for k,v in re.findall(r'([XYZE])(-?(?:\d*\.)?\d+)',code)}
 if cmd=='M83':relative=True
 elif cmd=='M82':relative=False
 elif cmd=='G92' and 'E' in d:E=d['E']
 elif cmd in ['G0','G1','G2','G3']:
  nxt=state.copy()
  for i,k in enumerate('XYZ'):
   if k in d:nxt[i]=d[k]
  de=d.get('E',0.) if relative else d.get('E',E)-E
  if 'E' in d:E=E+d['E'] if relative else d['E']
  if cmd=='G1' and de>0 and feature in known and np.linalg.norm(nxt-state)>.001 and layer is not None:
   all_layers[layer]=all_layers.get(layer,0)+1
   for t in [.1,.3,.5,.7,.9]:
    world=state+(nxt-state)*t+tool;world[2]-=height/2
    point=undo_rotation@((inverse@np.r_[world,1])[:3]-child_shift-shift)
    layer_x[layer]=float(point[0])
    if 5<point[1]<10 and 4.79<point[2]<5.39:
     edge=P['central_left_boundary']['slope_dx_dy']*point[1]+P['central_left_boundary']['new_intercept_mm']
     for side,bound in [('LEFT',edge),('RIGHT',P['central_right_boundary_mm'][1])]:
      if abs(point[0]-bound)<.3:web[side][layer]=web[side].get(layer,0)+1
  state=nxt
assert len(all_layers)==216 and min(all_layers.values())>0,len(all_layers)
checks={}
for side,bound in [('LEFT',P['central_left_boundary']['slope_dx_dy']*7.5+P['central_left_boundary']['new_intercept_mm']),('RIGHT',P['central_right_boundary_mm'][1])]:
 lo=max((x,l) for l,x in layer_x.items() if x<bound);hi=min((x,l) for l,x in layer_x.items() if x>bound)
 assert abs(hi[0]-lo[0]-.2)<.0001,(lo,hi)
 assert web[side].get(lo[1],0)>0 and web[side].get(hi[1],0)>0,(side,lo,hi,web[side])
 checks[side]=dict(boundary_x_mm=bound,adjacent_CAD_layer_x_mm=[lo[0],hi[0]],actual_print_z_mm=[lo[1],hi[1]],positive_model_path_samples=[web[side][lo[1]],web[side][hi[1]]])
report=dict(status='PASS',actual_model_layer_count=len(all_layers),layer_height_mm=.2,joining_height_mm=.62,join_checks=checks,method='Positive model extrusions through the 0.62 mm shoulder overlap at Y5..10; saved 3MF transforms, child centering, nozzle offset and deposited layer midpoint mapped back to delivered CAD. Adjacent layers on both sides deposit material in the join.',limits='Toolpaths establish deposited geometry, not printed strength or installed fit.')
(O/'reports/base_layers.json').write_text(json.dumps(report,indent=2));print('V033_ACTUAL_JOIN_PATHS_PASS',json.dumps(checks),flush=True)
