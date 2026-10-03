from pathlib import Path
import json,cadquery as cq,trimesh,numpy as np
R=Path(__file__).resolve().parents[1];O=R/'inspection/minimal_TCRT_stack_v041';Q=R/'releases/LaunchLab_v033_flush_QRE'
load=lambda p:cq.importers.importStep(str(p)).val()
base=load(O/'step/01_TCRT_minimal_cradle.step');old=load(Q/'step/01_QRE_minimal_port.step');cap=load(O/'step/03_TCRT_M5_clamp_dock.step');keeper=load(O/'step/02_TCRT_clip_keeper.step')
rep={'status':'PASS','protected_hinge_geometry':{},'tool_clearances':{}}
for a,b in [(-35,-16),(16,35)]:
 roi=cq.Solid.makeBox(b-a,12,40,cq.Vector(a,-6,-20));s=old.intersect(roi);t=base.intersect(roi);v=s.cut(t).Volume()+t.cut(s).Volume();assert v<.002;rep['protected_hinge_geometry'][str((a,b))]=v
for x in [-9,9]:
 tool=cq.Solid.makeCylinder(2,20.6,cq.Vector(x,-19,0));v=base.intersect(tool).Volume()+keeper.intersect(tool).Volume();assert v<.002;rep['tool_clearances'][f'M5 screw {x}']=v
for x,y in json.loads((O/'parameters.json').read_text())['clamp_screw_axes_mm']:
 tool=cq.Solid.makeCylinder(1.95,15,cq.Vector(x,y,17.71));v=cap.intersect(tool).Volume();assert v<.002;rep['tool_clearances'][f'Sensor screw {x}']=v
M=json.loads((O/'assembly_manifest.json').read_text())
for e in M['parts']:
 if e['printable'] and 'latch' in e['name']:
  m=trimesh.load(O/e['filename'],force='mesh')
  for n in ['01_TCRT_minimal_cradle','02_TCRT_clip_keeper','03_TCRT_M5_clamp_dock']:
   a=trimesh.load(O/'preview'/(n+'.stl'),force='mesh');i=trimesh.boolean.intersection([a,m],engine='manifold');v=abs(i.volume) if i is not None and len(i.faces) else 0;assert v<.002,(n,e['name'],v)
  assert np.array_equal((O/'stl'/(e['name']+'.stl')).read_bytes(),(Q/'stl'/(e['name'].replace('TCRT','QRE')+'.stl')).read_bytes())
(O/'reports/independent_checks.json').write_text(json.dumps(rep,indent=2))
# Existing display reference is illustrative; the intact factory shell is the fit reference.
T=R/'releases/LaunchLab_v019_tcrt5000_open_stack';TE={e['name']:e for e in json.loads((T/'assembly_manifest.json').read_text())['parts']};e=dict(TE['REF_M5_SCREEN_VISUAL_ONLY']);m=trimesh.load(T/e['filename'],force='mesh');m.apply_translation((0,-4,-1));m.export(O/e['filename']);M['parts'].append(e);(O/'assembly_manifest.json').write_text(json.dumps(M,indent=2))
print('PASS: protected hinges, latch collisions, screw access and reused latches')
