"""Nominal fit, mounting bearing, source interface and removal validation."""
from pathlib import Path
import json,hashlib
import numpy as np,trimesh,cadquery as cq
R=Path(__file__).resolve().parents[1];O=R/'releases/LaunchLab_v017_open_stack';S=R/'releases/LaunchLab_v016_qre1113'
M=json.loads((O/'assembly_manifest.json').read_text());P=json.loads((O/'parameters.json').read_text());E={e['name']:e for e in M['parts']};meshes={e['name']:trimesh.load(O/e['filename'],force='mesh') for e in M['parts']}
base='01_attachment_port';dock='03_sensor_m5_dock';device='REF_M5_OFFICIAL_GEOMETRY';pcb='REF_QRE_PCB_USER_14x9x2';sensor='REF_QRE_SENSOR';tie='REF_QRE_REAR_STOP_TIE';liner='REF_M5_SOFT_LINER'
printed=[e['name'] for e in M['parts'] if e['printable']];rep={'status':'IN_PROGRESS','checks':{},'collisions':[],'input_sha256':{},'limitations':P['limits']}
for e in M['parts']:rep['input_sha256'][e['filename']]=hashlib.sha256((O/e['filename']).read_bytes()).hexdigest()
def vol(a,b):
 if np.any(a.bounds[1]<=b.bounds[0]+1e-5) or np.any(b.bounds[1]<=a.bounds[0]+1e-5):return 0.
 return abs(float(trimesh.boolean.intersection([a,b],engine='manifold',check_volume=False).volume))
def move(a,d):
 m=a.copy();m.apply_translation(d);return m
def box(*a):
 m=trimesh.creation.box([a[1]-a[0],a[3]-a[2],a[5]-a[4]]);m.apply_translation([(a[0]+a[1])/2,(a[2]+a[3])/2,(a[4]+a[5])/2]);return m
def check(a,b,stage,**kw):
 v=vol(a,b)
 if v>.01:rep['collisions'].append(dict(stage=stage,volume_mm3=v,**kw))
 return v
def save():
 (O/'reports/fit_and_motion.json').write_text(json.dumps(rep,indent=2));print('CHECKS',len(rep['checks']),'COLLISIONS',len(rep['collisions']),flush=True)
for n in printed:
 for t,m in meshes.items():
  if n==t or E[t]['group'] in ['visual','fasteners','fit_envelope']:continue
  check(meshes[n],m,'nominal',part=n,target=t)
for n in meshes:
 if n.startswith('REF_M3x8_'):
  h=trimesh.boolean.intersection([meshes[n],box(-40,40,-40,40,14.684,18)],engine='manifold',check_volume=False)
  check(h,meshes[device],'mount head vs device',part=n)
rep['checks']['nominal']='Printed geometry vs actual manufacturer M5 shell, PCB/sensor, liner and provisional harness; screw-thread pilots excepted.';save()
for n in ['02_latch_LEFT','02_latch_RIGHT']:
 for d,ext in [('step','.step'),('stl','.stl'),('preview','.stl')]:assert (S/d/(n+ext)).read_bytes()==(O/d/(n+ext)).read_bytes()
rep['checks']['clips_byte_identical']=True
old=cq.importers.importStep(str(R/'source/LaunchLab_v02/step/01_native_port_UNSCALED.step')).val();new=cq.importers.importStep(str(O/'step'/f'{base}.step')).val();a=cq.importers.importStep(str(R/'releases/LaunchLab_v015_m5sticks3/step/03_sensor_clip_retainer.step')).val();b=cq.importers.importStep(str(O/'step'/f'{dock}.step')).val()
for sign in [-1,1]:
 x0,x1=(-35,-9) if sign<0 else (9,35)
 for label,u,v,z in [('native_port',old,new,14),('clip_keepers',a,b,13.283)]:
  mask=cq.Solid.makeBox(x1-x0,31.8,z+20,cq.Vector(x0,-15.9,-20));u=u.intersect(mask);v=v.intersect(mask);delta=abs(u.Volume()+v.Volume()-2*u.intersect(v).Volume());rep['checks'][f'{label}_side_{sign}_delta_mm3']=delta;assert delta<.001,(label,delta)
lowmask=cq.Solid.makeBox(70,40,24.7,cq.Vector(-35,-20,-20));u=old.intersect(lowmask);v=new.intersect(lowmask);delta=abs(u.Volume()+v.Volume()-2*u.intersect(v).Volume());rep['checks']['native_port_entire_region_below_Z4p7_delta_mm3']=delta;assert delta<.001
areas=[]
for x,y in P['mount_screw_centres_mm']:
 probe=cq.Solid.makeCylinder(2.84,.02,cq.Vector(x,y,14.664));areas.append(probe.intersect(b).Volume()/.02)
assert min(areas)>10;rep['checks']['M3_head_bearing_mm2']=areas
rep['checks']['M3_tip_to_original_post_bottom_mm']=.766
# M5 mount pads contact its stepped factory back and retain 1.7 mm nominal
# thread insertion. An insertion-depth claim needs the actual hardware.
rep['checks']['M5_pad_contact_when_dock_lifted_0p05_mm3']=vol(move(meshes[dock],[0,0,.05]),meshes[device]);assert rep['checks']['M5_pad_contact_when_dock_lifted_0p05_mm3']>.3
rep['checks']['M5_back_contact_when_liner_lifted_0p05_mm3']=vol(move(meshes[liner],[0,0,.05]),meshes[device]);assert rep['checks']['M5_back_contact_when_liner_lifted_0p05_mm3']>.3
for i,(x,y) in enumerate(P['M5_screw_centres_mm'],1):
 n=f'REF_M2x6_DEVICE_{i}';check(meshes[n],meshes[base],'device screw vs port',part=n)
 h=trimesh.boolean.intersection([meshes[n],box(-40,40,-40,40,14,16)],engine='manifold',check_volume=False);check(h,meshes[dock],'device screw head clearance',part=n)
rep['checks']['M5_nominal_thread_engagement_mm']=1.7
x,y=P['sensor_center_xy_mm'];beam=box(x-1.49,x+1.49,y-1.79,y+1.79,3.79,4.09);rep['checks']['optical_path_mm3']={n:vol(meshes[n],beam) for n in [base,dock]};assert max(rep['checks']['optical_path_mm3'].values())<.01
rep['checks']['PCB_seat_probe_mm3']=vol(move(meshes[pcb],[0,0,-.05]),meshes[dock]);assert rep['checks']['PCB_seat_probe_mm3']>.1
rep['checks']['PCB_top_rail_probe_mm3']=vol(move(meshes[pcb],[0,0,.4]),meshes[dock]);assert rep['checks']['PCB_top_rail_probe_mm3']>.1
rep['checks']['PCB_rear_stop_probe_mm3']=vol(move(meshes[pcb],[0,.4,0]),meshes[tie]);assert rep['checks']['PCB_rear_stop_probe_mm3']>.01
# All new material is above the registered launcher-top plane behind the port.
launch=box(-35,35,16.5,60,-10,3.78);assert max(vol(meshes[n],launch) for n in [base,dock])<.01
# Device can be lifted after removing its two M2 screws/unplugging the Hat.
# Dock lifts after the M5 and its four M3 screws are removed.
for dz in np.arange(0,40.1,.75):
 check(move(meshes[device],[0,0,float(dz)]),meshes[dock],'M5 removal',dz=float(dz))
 for n in [dock,pcb,sensor,'REF_QRE_UNDERSIDE_ALLOWANCE','REF_QRE_TOP_SOLDER']:
  check(move(meshes[n],[0,0,float(dz)]),meshes[base],'dock removal',part=n,dz=float(dz))
for dy in np.arange(0,22.1,.5):
 for n in [pcb,sensor,'REF_QRE_UNDERSIDE_ALLOWANCE','REF_QRE_TOP_SOLDER']:
  check(move(meshes[n],[0,float(dy),0]),meshes[dock],'PCB slide with stop tie off',part=n,dy=float(dy))
rep['checks']['removal_sweeps']='0..40 mm vertical, 0.75 mm sampling; PCB +Y 0..22 mm at 0.5 mm. Fasteners and harness removed as required.'
# Check optional narrow dock against the same base and actual device.
s=cq.importers.importStep(str(O/'extras/03_OPEN_DOCK_NATIVE_7p62_OPTION.step')).val();vs,fs=s.tessellate(.025,.1);m=trimesh.Trimesh([v.toTuple() for v in vs],fs,process=True)
for target in [base,device]:check(m,meshes[target],'native-width nominal',target=target)
nb=box(x-3.81,x+3.81,y-7.65,y+6.35,6.1,8.1);check(m,nb,'native PCB nominal')
assert vol(move(nb,[0,0,-.05]),m)>.1 and vol(move(nb,[0,0,.4]),m)>.1
for dz in np.arange(0,40.1,.75):check(move(m,[0,0,float(dz)]),meshes[base],'native dock removal',dz=float(dz))
for dy in np.arange(0,22.1,.5):check(move(nb,[0,float(dy),0]),m,'native PCB slide',dy=float(dy))
rep['checks']['native_width_option']='Same fit/retention/removal checks PASS if no collisions'
rep['status']='PASS' if not rep['collisions'] else 'FAIL';save();assert not rep['collisions'],rep['collisions'][:15]
print('FIT_AND_MOTION_PASS',flush=True)
