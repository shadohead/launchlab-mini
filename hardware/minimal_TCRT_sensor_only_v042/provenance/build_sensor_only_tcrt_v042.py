"""Sensor-only alternate: old TCRT5000 held by the two-clip launcher mount."""
from pathlib import Path
import ast,json,shutil,hashlib
import cadquery as cq
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];O=R/'inspection/minimal_TCRT_sensor_only_v042';Q=R/'releases/LaunchLab_v033_flush_QRE';T=R/'releases/LaunchLab_v019_tcrt5000_open_stack';PRIOR=R/'inspection/minimal_TCRT_stack_v041'
assert not (O/'SHA256SUMS.txt').exists(),'Preserve delivered prototype'
for d in ['step','preview','stl','renders','reports','references','provenance']:(O/d).mkdir(parents=True,exist_ok=True)
# Load pure helpers only. The rejected stacked builder is never executed.
for node in ast.parse((R/'scripts/build_minimal_tcrt_v041.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['box','cyl','load','mesh']:exec(compile(ast.Module(body=[node],type_ignores=[]),'helpers','exec'))
for node in ast.parse((R/'scripts/build_compact_v010.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name=='repair_collinear_boundary':exec(compile(ast.Module(body=[node],type_ignores=[]),'helpers','exec'))
X=.1418;Y=-7.8658;x0,x1=X-6.5,X+6.5;y0,y1=Y-4,Y+27;PCB=15.1;TOP=16.1;AXES=[(X-9.8,3.6),(X+9.8,3.6)]
# The previously checked cradle is already sensor-only; restore its unclipped side-wall tops.
# Keep the same lower optical datum and original launcher hinge beds.
base=load(PRIOR/'step/01_TCRT_minimal_cradle.step')
for a,b in [(x0-1.8,x0-.2),(x1+.2,x1+1.8)]:base=base.fuse(box(a,b,y0-.8,y1+.8,14.184,TOP+.2))
# Small U keeper surrounds components and bears on four bare PCB edge lands.
cap=None
for a,b,pa,pb in [(x0-1.4,x0-.05,x0-1.4,x0+.6),(x1+.05,x1+1.4,x1-.6,x1+1.4)]:
 s=box(a,b,y0-1.6,y1-.6,TOP+.3,TOP+1.5)
 for c,d in [(y0+.6,y0+2.1),(y1-2.1,y1-.6)]:s=s.fuse(box(pa,pb,c,d,TOP,TOP+1.2))
 cap=s if cap is None else cap.fuse(s)
# Bridge completely ahead of the PCB, rather than across its soldered surface.
cap=cap.fuse(box(x0-1.4,x1+1.4,y0-1.6,y0-.2,TOP+.3,TOP+1.5))
for x,y in AXES:
 cap=cap.fuse(cyl(2.3,x,y,TOP,TOP+1.6))
 a,b=sorted((x,x0 if x<X else x1));cap=cap.fuse(box(a,b,y-1.2,y+1.2,TOP,TOP+1.6)).cut(cyl(1.1,x,y,TOP-.1,TOP+1.7))
cap=cap.clean();keeper=load(PRIOR/'step/02_TCRT_clip_keeper.step');base=base.cut(cap).cut(keeper).clean()
# Recut both pilots after all connecting ribs have been joined.
for x,y in AXES:base=base.cut(cyl(.85,x,y,TOP-3.4,TOP))
base=base.clean()
for x,y in AXES:assert base.intersect(cyl(.84,x,y,TOP-3.39,TOP-.01)).Volume()<.002
solids={'01_TCRT_sensor_cradle':base,'02_TCRT_clip_keeper':keeper,'03_TCRT_sensor_pressure_keeper':cap}
M={'version':'0.42','units':'mm','architecture':'Sensor-only two-clip mount; M5 remains on separate existing v040 launcher attachment','parts':[]}
rep={'status':'BUILDING','mesh':{},'collisions':{},'protected_launcher_interface':{},'source_sha256':{},'pressure_land_contacts_mm2':[]}
for n,s in solids.items():
 assert s.isValid() and len(s.Solids())==1,(n,s.isValid(),len(s.Solids()))
 cq.exporters.export(s,str(O/'step'/(n+'.step')));m=mesh(s);m.export(O/'preview'/(n+'.stl'))
 p=m.copy();rot=[0,-90,0] if n.startswith('01') else [-90,0,0] if n.startswith('03') else [0,0,0]
 for ax,angle in zip([(1,0,0),(0,1,0),(0,0,1)],rot):
  if angle:p.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(angle),ax))
 shift=np.r_[-p.bounds[:,:2].mean(axis=0),-p.bounds[0,2]];p.apply_translation(shift);p.export(O/'stl'/(n+'.stl'))
 rep['mesh'][n]=dict(watertight=m.is_watertight,components=len(m.split()),volume_mm3=m.volume,bounds_mm=m.bounds.tolist(),print_bounds_mm=p.bounds.tolist())
 M['parts'].append(dict(name=n,filename=f'preview/{n}.stl',color='#48545D' if n.startswith('01') else '#D0A96A' if n.startswith('03') else '#398B83',reference=False,printable=True,group='printed',source='v042 TCRT sensor-only mount',description=n,print_rotation_deg=rot,print_translation_mm=shift.tolist()))
E={e['name']:e for e in json.loads((Q/'assembly_manifest.json').read_text())['parts']}
for n in ['08_QRE_latch_LEFT','09_QRE_latch_RIGHT']:
 e=dict(E[n]);nn=n.replace('QRE','TCRT');e.update(name=nn,filename=f'preview/{nn}.stl',description='Existing launcher latch, unchanged')
 for d in ['preview','stl','step']:
  ext='.step' if d=='step' else '.stl';shutil.copy2(Q/d/(n+ext),O/d/(nn+ext))
 M['parts'].append(e)
TE={e['name']:e for e in json.loads((T/'assembly_manifest.json').read_text())['parts']}
for n in ['REF_TCRT_PCB_MEASURED','REF_TCRT_HEAD_AND_LEGS','REF_TCRT_LENS_PAIR','REF_TCRT_POT','REF_TCRT_HEADER','REF_TCRT_UNDERSIDE_SOLDER','REF_TCRT_TOP_SOLDER','REF_SENSOR_SOCKET_ALLOWANCE']:
 e=dict(TE[n]);m=trimesh.load(T/e['filename'],force='mesh');m.apply_translation((0,0,-1));m.export(O/e['filename']);M['parts'].append(e)
for i,(x,y) in enumerate(AXES,1):
 s=cyl(1,x,y,13.7,17.7).fuse(cyl(1.9,x,y,17.7,19.1));n=f'REF_M2x4_SENSOR_{i}';mesh(s).export(O/'preview'/(n+'.stl'));M['parts'].append(dict(name=n,filename=f'preview/{n}.stl',reference=True,printable=False,group='hardware',color='#AAB1BA',source='Nominal screw envelope',description='M2x4 pan head keeper screw'))
for n,s in solids.items():
 for nn,ss in solids.items():
  if n<nn:
   v=s.intersect(ss).Volume();rep['collisions'][n+' / '+nn]=v;assert v<.002,(n,nn,v)
refsolids={'PCB':box(x0,x1,y0,y1,PCB,TOP),'head':box(X-5,X+5,Y-3,Y+3,5.6,PCB),'lens':box(X-3.5,X+3.5,Y-3,Y+3,3.1,5.6),'pot':box(X-.8,X+6.2,y1-19,y1-12,TOP,TOP+6),'header':box(X-5,X+5,y1-2,y1+6,TOP,TOP+4)}
for n,s in solids.items():
 for rn,rs in refsolids.items():
  v=s.intersect(rs).Volume();rep['collisions'][n+' / '+rn]=v;assert v<.002,(n,rn,v)
for rn in ['REF_TCRT_UNDERSIDE_SOLDER','REF_TCRT_TOP_SOLDER','REF_SENSOR_SOCKET_ALLOWANCE','08_TCRT_latch_LEFT','09_TCRT_latch_RIGHT']:
 rm=trimesh.load(O/'preview'/(rn+'.stl'),force='mesh')
 for n in solids:
  inter=trimesh.boolean.intersection([trimesh.load(O/'preview'/(n+'.stl'),force='mesh'),rm],engine='manifold');v=abs(inter.volume) if inter is not None and len(inter.faces) else 0
  rep['collisions'][n+' / '+rn]=v;assert np.isfinite(v) and v<.002,(n,rn,v)
old=load(Q/'step/01_QRE_minimal_port.step')
for a,b in [(-35,-16),(16,35)]:
 roi=box(a,b,-6,6,-20,20);s=old.intersect(roi);t=base.intersect(roi);v=s.cut(t).Volume()+t.cut(s).Volume();assert v<.002;rep['protected_launcher_interface'][f'hinge_{a}_{b}_difference_mm3']=v
# Verify four finite pressure-contact areas on the PCB top, and open vertical screw access.
for a,b in [(x0,x0+.6),(x1-.6,x1)]:
 for c,d in [(y0+.6,y0+2.1),(y1-2.1,y1-.6)]:
  land=box(a,b,c,d,TOP,TOP+.01);area=cap.intersect(land).Volume()/.01;assert area>.85,(a,b,c,d,area);rep['pressure_land_contacts_mm2'].append(area)
for x,y in AXES:
 tool=cyl(1.9,x,y,17.71,35);assert cap.intersect(tool).Volume()<.002
for p in [Q/'step/01_QRE_minimal_port.step',PRIOR/'step/01_TCRT_minimal_cradle.step',PRIOR/'step/02_TCRT_clip_keeper.step',R/'reference files/TCRT5000_user_measurements_2026-09-21.md']:
 rep['source_sha256'][str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
params=dict(version='0.42',sensor='OLD TCRT5000/LM393',architecture=M['architecture'],PCB_mm=[31,13,1],optical_projection_mm=12,pot_mm=[7,7,6],sensor_seat_z_mm=PCB,optics_z_mm=3.1,clamp_screw_axes_mm=AXES,clamp_screws='2 x M2x4 pan head',clip_keeper_screws='2 x M2x5 countersunk (existing)',side_guide_wall_mm=1.6,keeper_side_rail_mm=1.35,keeper_body_mm=1.2,xy_play_per_side_mm=.2,preload_ear_gap_mm=.4,keeper_max_z_mm=17.7,sensor_max_z_mm=22.1,M5_attachment='Existing v040 separate carrier, unchanged and excluded from this design',limits=['Component locations and bare corner lands follow earlier TCRT CAD assumptions; physically check the contact lands.','Connector housing and wire bends remain provisional; header end stays open.','Optical alignment through the actual launcher opening needs physical verification.','CAD prototype and unsliced STL package; no printer dispatch.'])
rep['status']='PASS';(O/'reports/cad_validation.json').write_text(json.dumps(rep,indent=2));(O/'parameters.json').write_text(json.dumps(params,indent=2));(O/'assembly_manifest.json').write_text(json.dumps(M,indent=2))
allparts=[load(O/'step'/(e['name']+'.step')) for e in M['parts'] if e['printable']];cq.exporters.export(cq.Compound.makeCompound(allparts),str(O/'TCRT_sensor_only_v042.step'))
shutil.copy2(R/'reference files/TCRT5000_user_measurements_2026-09-21.md',O/'references/TCRT5000_measurements.md');shutil.copy2(Q/'LICENSE.txt',O/'LICENSE.txt');shutil.copy2(Q/'references/QRE_BP_port_LICENSE.txt',O/'references/BP_port_LICENSE.txt')
(O/'README.md').write_text('TCRT5000 sensor-only launcher mount v042\n\nOnly the sensor mount is redesigned. The M5 stays on the existing separate v040 launcher attachment. No M5 support, deck, mounting holes, risers or M5 electronics are included.\n\nMeasured old sensor: 31 x 13 x 1 mm PCB, 12 mm optical projection, 7 x 7 x 6 mm adjustment block. Thin side guides, four PCB seats and end stops locate the board. Two centered M2x4 screws hold a small U keeper that presses on four bare edge lands. The adjustment block and header are open.\n\nParts: 01 cradle, 02 launcher clip keeper, 03 sensor pressure keeper, two unchanged latches. Reuse the existing latches and two M2x5 countersunk clip keeper screws. This modified clip keeper moves its crossbar forward to clear the larger PCB solder envelope.\n\nThe five STL files are prototype manufacturing orientations. They are unsliced. Physical fit, screw preload, exact corner contact lands, wiring and optical clearance require a check.\n')
shutil.copy2(__file__,O/'provenance'/Path(__file__).name)
print('PASS',O,flush=True)
