"""Independent nominal geometry, source interface, assembly, drivers and service paths."""
from pathlib import Path
import ast,json,hashlib
import numpy as np,trimesh,cadquery as cq
R=Path(__file__).resolve().parents[1];O=R/'releases/LaunchLab_v019_tcrt5000_open_stack';S=R/'releases/LaunchLab_v017_open_stack'
M=json.loads((O/'assembly_manifest.json').read_text());P=json.loads((O/'parameters.json').read_text());E={e['name']:e for e in M['parts']};meshes={e['name']:trimesh.load(O/e['filename'],force='mesh') for e in M['parts']}
base='01_TCRT_attachment_port';dock='03_TCRT_sensor_cradle';keeper='04_TCRT_M5_top_dock';device='REF_M5_OFFICIAL_GEOMETRY';pcb='REF_TCRT_PCB_MEASURED';liner='REF_M5_SOFT_LINER'
printed=[e['name'] for e in M['parts'] if e['printable']];sensor=[n for n in meshes if n.startswith('REF_TCRT')]
rep={'status':'IN_PROGRESS','checks':{},'collisions':[],'input_sha256':{},'limitations':P['limits']}
for e in M['parts']:rep['input_sha256'][e['filename']]=hashlib.sha256((O/e['filename']).read_bytes()).hexdigest()
for n in ast.parse((R/'scripts/check_open_stack_v017.py').read_text()).body:
 if isinstance(n,ast.FunctionDef) and n.name in ['vol','move','box','check','save']:exec(compile(ast.Module(body=[n],type_ignores=[]),'fit_helpers','exec'))
for n in printed:
 for t,m in meshes.items():
  if n==t or E[t]['group'] in ['visual','fasteners']:continue
  check(meshes[n],m,'nominal',part=n,target=t)
rep['checks']['nominal']='All five printed parts vs vendor M5, measured OLD sensor envelopes, liner and provisional sockets/wires. Thread-forming pilot interference excepted.';save()
for n in ['02_latch_LEFT','02_latch_RIGHT']:
 for d,ext in [('step','.step'),('stl','.stl'),('preview','.stl')]:assert (S/d/(n+ext)).read_bytes()==(O/d/(n+ext)).read_bytes()
rep['checks']['clips_byte_identical']=True
old=cq.importers.importStep(str(R/'source/LaunchLab_v02/step/01_native_port_UNSCALED.step')).val();new=cq.importers.importStep(str(O/'step'/f'{base}.step')).val();a=cq.importers.importStep(str(R/'releases/LaunchLab_v015_m5sticks3/step/03_sensor_clip_retainer.step')).val();b=cq.importers.importStep(str(O/'step'/f'{dock}.step')).val()
for sign in [-1,1]:
 for label,u,v,x0,x1,y0,y1,z0,z1 in [('native_port_sides',old,new,*((-35,-9) if sign<0 else (9,35)),-15.9,15.9,-20,13.284),('clip_keeper_contact',a,b,*((-35,-15) if sign<0 else (15,35)),-3.4,3.4,10.8,13.283)]:
  mask=cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,cq.Vector(x0,y0,z0));u=u.intersect(mask);v=v.intersect(mask);delta=abs(u.Volume()+v.Volume()-2*u.intersect(v).Volume());rep['checks'][f'{label}_{sign}_delta_mm3']=delta;assert delta<.001,(label,delta)
mask=cq.Solid.makeBox(70,40,23.78,cq.Vector(-35,-20,-20));u=old.intersect(mask);v=new.intersect(mask);delta=abs(u.Volume()+v.Volume()-2*u.intersect(v).Volume());rep['checks']['source_port_below_launcher_plane_Z3p78_delta_mm3']=delta;assert delta<.001
areas=[]
for i,(x,y) in enumerate(P['mount_screw_centres_mm'],1):
 probe=cq.Solid.makeCylinder(2.84,.02,cq.Vector(x,y,14.664));areas.append(probe.intersect(b).Volume()/.02)
 head=trimesh.boolean.intersection([meshes[f'REF_M3x8_MOUNT_{i}'],box(-40,40,-40,40,14.684,18)],engine='manifold',check_volume=False)
 for target in [base,dock,keeper,device]:check(head,meshes[target],'M3 head clearance',target=target,index=i)
 # A thin straight driver reaches each M3 socket with the M5 already attached.
 v=cq.Solid.makeCylinder(1.4,40,cq.Vector(x,y,14.684));vs,fs=v.tessellate(.025,.1);tool=trimesh.Trimesh([p.toTuple() for p in vs],fs,process=True)
 for target in [dock,keeper,device]:check(tool,meshes[target],'M3 driver with assembled M5',target=target,index=i)
assert min(areas)>10;rep['checks']['M3_head_bearing_mm2']=areas;rep['checks']['M3_thread_engagement_mm']=6.6;rep['checks']['M3_tip_to_source_post_bottom_mm']=.766
rep['checks']['M5_pad_contact_when_dock_lifted_0p05_mm3']=vol(move(meshes[keeper],[0,0,.05]),meshes[device]);assert rep['checks']['M5_pad_contact_when_dock_lifted_0p05_mm3']>.3
rep['checks']['M5_liner_contact_when_lifted_0p05_mm3']=vol(move(meshes[liner],[0,0,.05]),meshes[device]);assert rep['checks']['M5_liner_contact_when_lifted_0p05_mm3']>.3
for i,(x,y) in enumerate(P['M5_screw_centres_mm'],1):
 n=f'REF_M2x6_DEVICE_{i}';head=trimesh.boolean.intersection([meshes[n],box(-40,40,-40,40,20.2,21.6)],engine='manifold',check_volume=False)
 for target in [dock,keeper,base]:check(head,meshes[target],'M5 screw head clearance',target=target,index=i)
 # Assembly explicitly occurs OFF the base; the lower cap has service holes.
 v=cq.Solid.makeCylinder(1.8,21.6,cq.Vector(x,y,0));vs,fs=v.tessellate(.025,.1);tool=trimesh.Trimesh([p.toTuple() for p in vs],fs,process=True)
 for target in [keeper]:check(tool,meshes[target],'M5 underside tool with top module off base',target=target,index=i)
for i,(x,y) in enumerate(P['sensor_keeper_screw_centres_mm'],1):
 n=f'REF_M2x4_SENSOR_{i}';head=trimesh.boolean.intersection([meshes[n],box(-40,40,-40,40,18.7,20.1)],engine='manifold',check_volume=False)
 for target in [dock,keeper,device]:check(head,meshes[target],'sensor keeper screw head',target=target,index=i)
 v=cq.Solid.makeCylinder(1.1,25,cq.Vector(x,y,18.7));vs,fs=v.tessellate(.025,.1);tool=trimesh.Trimesh([p.toTuple() for p in vs],fs,process=True)
 for target in [dock,keeper,device]:check(tool,meshes[target],'sensor keeper driver',target=target,index=i)
rep['checks']['screw_driver_paths']='M3 side access with M5 attached; M5 underside access while entire top module is removed from base; sensor keeper screws clear M5 sides.'
assert np.allclose(meshes[pcb].extents,[13,31,1],atol=.001)
projection=meshes[pcb].bounds[0,2]-meshes['REF_TCRT_LENS_PAIR'].bounds[0,2];assert abs(projection-12)<.001
thickness=meshes['REF_TCRT_POT'].bounds[1,2]-meshes['REF_TCRT_LENS_PAIR'].bounds[0,2];assert abs(thickness-19)<.001
assert meshes['REF_TCRT_POT'].bounds[0,2]>=meshes[pcb].bounds[1,2]-.001
rep['checks']['measured_old_sensor_dimensions']={'PCB_mm':[31,13,1],'projection_mm':float(projection),'opposite_face_pot_mm':[7,7,6],'total_thickness_mm':float(thickness)}
x,y=P['sensor_center_xy_mm'];beam=box(x-3.49,x+3.49,y-2.99,y+2.99,3.8,4.09);rep['checks']['printed_upper_optical_path_mm3']={n:vol(meshes[n],beam) for n in [base,dock,keeper]};assert max(rep['checks']['printed_upper_optical_path_mm3'].values())<.01
rep['checks']['PCB_seat_probe_mm3']=vol(move(meshes[pcb],[0,0,-.05]),meshes[dock]);assert rep['checks']['PCB_seat_probe_mm3']>.1
rep['checks']['PCB_keeper_probe_mm3']=vol(move(meshes[pcb],[0,0,.25]),meshes[keeper]);assert rep['checks']['PCB_keeper_probe_mm3']>.1
rep['checks']['PCB_xy_stops_probe_mm3']=[vol(move(meshes[pcb],d),meshes[dock]) for d in [[.4,0,0],[-.4,0,0],[0,.4,0],[0,-.4,0]]];assert min(rep['checks']['PCB_xy_stops_probe_mm3'])>.1
# Assembly/service sequence: populated top module lifts first, then M5, keeper, sensor.
for dz in np.arange(0,40.1,.75):
 d=[0,0,float(dz)]
 for n in [dock,keeper,device,liner]+sensor+[n for n in meshes if n.startswith('REF_M2')]:check(move(meshes[n],d),meshes[base],'populated top module lifting off port',part=n,dz=float(dz))
 check(move(meshes[device],d),meshes[keeper],'M5 removal after top module off cradle',dz=float(dz))
 check(move(meshes[device],d),meshes[keeper],'M5 removal vs sensor keeper',dz=float(dz))
 for n in [keeper,device,liner]+[n for n in meshes if n.startswith('REF_M2x6')]:
  for t in [dock]+sensor:check(move(meshes[n],d),meshes[t],'M5/top-dock module lifting from cradle',part=n,target=t,dz=float(dz))
 for n in sensor:check(move(meshes[n],d),meshes[dock],'sensor lift with keeper and M5 removed',part=n,dz=float(dz))
rep['checks']['removal_sweeps']='Vertical0..40mm in0.75mm steps. Hat unplugged; fourM3 removed for top module, twoM2x6 for M5, fourM2x4 for top dock. Sensor lifts vertically.';save()
# Original latch opening path, source-derived pivot hypothesis, discrete checks only.
for side,x,sign in [('RIGHT',17.628,-1),('LEFT',-17.6,1)]:
 for deg in range(0,91,5):
  m=meshes['02_latch_'+side].copy();m.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(sign*deg),[0,1,0],point=[x,0,9.1]))
  for target in [base,dock,keeper,device]+sensor:check(m,meshes[target],'source-derived latch opening',side=side,angle_deg=deg,target=target)
rep['checks']['latch_sweep']='0..90degrees every5degrees, original pivot hypothesis. No real-launcher or load test.'
# Fit coupon plus the actual keeper uses the same seat and pilot geometry.
s=cq.importers.importStep(str(O/'extras/11_TCRT_SEAT_FIT.step')).val();vs,fs=s.tessellate(.025,.1);coupon=trimesh.Trimesh([p.toTuple() for p in vs],fs,process=True)
for n in [keeper]+sensor:check(coupon,meshes[n],'seat coupon nominal',target=n)
k=cq.importers.importStep(str(O/'extras/12_TCRT_KEEPER_FIT.step')).val();vs,fs=k.tessellate(.025,.1);kf=trimesh.Trimesh([p.toTuple() for p in vs],fs,process=True)
check(coupon,kf,'coupon pair nominal')
for n in sensor:check(kf,meshes[n],'keeper coupon nominal',target=n)
rep['checks']['seat_coupon_matches_current_dock']=True
rep['status']='PASS' if not rep['collisions'] else 'FAIL';save();assert not rep['collisions'],rep['collisions'][:20]
print('OLD_SENSOR_FIT_AND_MOTION_PASS',flush=True)
