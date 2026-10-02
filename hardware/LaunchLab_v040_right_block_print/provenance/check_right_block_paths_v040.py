"""Check actual deposition through all layers of the replacement M5 mount."""
from pathlib import Path
from zipfile import ZipFile
import json,re,xml.etree.ElementTree as ET
import numpy as np,trimesh
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[1];O=R/'releases/LaunchLab_v040_right_block_print'
path=O/'bambu/LaunchLab_v040_P1S_PLA_M5_RIGHT_BLOCK_TREE_SLIM.3mf';ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'};prod='http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
def matrix(s):
 a=np.array([float(v) for v in s.split()]).reshape(4,3);t=np.eye(4);t[:3,:3]=a[:3].T;t[:3,3]=a[3];return t
objects={}
with ZipFile(path) as z:
 cfg=ET.fromstring(z.read('Metadata/model_settings.config'));root=ET.fromstring(z.read('3D/3dmodel.model'))
 for ob in cfg.findall('object'):
  name=ob.find("metadata[@key='name']").attrib['value'];item=root.find(f"m:build/m:item[@objectid='{ob.attrib['id']}']",ns);parent=root.find(f"m:resources/m:object[@id='{ob.attrib['id']}']",ns);comp=parent.find('m:components/m:component',ns)
  child=ET.fromstring(z.read(comp.attrib['{'+prod+'}path'].lstrip('/')));v=np.array([[float(v.attrib[k]) for k in 'xyz'] for v in child.findall('.//m:vertex',ns)])
  source=trimesh.load(O/'stl'/(name+'.stl'),force='mesh');shift=v.min(0)-source.bounds[0];inverse=np.linalg.inv(matrix(item.attrib['transform'])@matrix(comp.attrib['transform']))
  assert max(cKDTree(v-shift).query(source.vertices)[0].max(),cKDTree(source.vertices).query(v-shift)[0].max())<.001
  objects[name]=dict(inverse=inverse,shift=shift,bounds=source.bounds,layers=set(),support_count=0)
 settings=json.loads(z.read('Metadata/project_settings.config'));meta=json.loads(z.read('Metadata/plate_1.json'));tool=np.array([float(v) for v in settings['extruder_offset'][int(meta['first_extruder'])].split('x')]+[0.]);g=z.read('Metadata/plate_1.gcode').decode()
known={'Outer wall','Inner wall','Top surface','Bottom surface','Internal solid infill','Bridge','Overhang wall','Floating vertical shell','Gap infill','Sparse infill'}
state=np.zeros(3);relative=False;E=0.;layer=None;height=None;feature=''
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
  if cmd=='G1' and de>0 and np.linalg.norm(nxt-state)>.001 and layer is not None and (feature in known or feature.startswith('Support')):
   world=(state+nxt)/2+tool;world[2]-=height/2
   for name,ob in objects.items():
    p=(ob['inverse']@np.r_[world,1])[:3]-ob['shift'];bounds=ob['bounds']
    if np.all(p>=bounds[0]-.01) and np.all(p<=bounds[1]+.01):
     if feature in known:ob['layers'].add(layer)
     else:ob['support_count']+=1
  state=nxt
checks={}
for name,ob in objects.items():
 expected=np.round(np.arange(1,int(np.ceil(ob['bounds'][1,2]/.2))+1)*.2,6)
 assert np.allclose(sorted(ob['layers']),expected,atol=.011),(name,sorted(ob['layers']),expected)
 checks[name]=dict(actual_model_layers=len(ob['layers']),first_layer_mm=min(ob['layers']),last_layer_mm=max(ob['layers']),support_paths_inside_model_bounding_box=ob['support_count'])
assert set(checks)=={'01_M5_stepped_platform'}
(O/'reports/actual_paths.json').write_text(json.dumps(dict(status='PASS',objects=checks,method='Positive model deposition mapped through saved 3MF transforms, child centering and configured nozzle offset; deposited layer midplanes. Brim and support paths excluded from model counts.'),indent=2));print('M5_ACTUAL_LAYER_PATHS_PASS',json.dumps(checks),flush=True)
