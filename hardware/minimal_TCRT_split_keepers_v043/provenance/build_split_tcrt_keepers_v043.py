"""Apply user markup: independent screwable clip caps, clean QRE lower plate."""
from pathlib import Path
import ast,hashlib,json,shutil
import cadquery as cq,numpy as np,trimesh
R=Path(__file__).resolve().parents[1];S=R/'inspection/minimal_TCRT_sensor_only_v042';Q=R/'releases/LaunchLab_v033_flush_QRE';O=R/'inspection/minimal_TCRT_split_keepers_v043'
assert not (O/'SHA256SUMS.txt').exists(),'Preserve delivered prototype'
for d in ['step','preview','stl','renders','reports','references','provenance']:(O/d).mkdir(parents=True,exist_ok=True)
for node in ast.parse((R/'scripts/build_minimal_tcrt_v041.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['box','cyl','load','mesh']:exec(compile(ast.Module(body=[node],type_ignores=[]),'helpers','exec'))
for node in ast.parse((R/'scripts/build_compact_v010.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name=='repair_collinear_boundary':exec(compile(ast.Module(body=[node],type_ignores=[]),'helpers','exec'))
base=load(S/'step/01_TCRT_sensor_cradle.step');oldbase=base;oldkeeper=load(Q/'step/02_QRE_clip_keeper.step');pressure=load(S/'step/03_TCRT_sensor_pressure_keeper.step')
P=json.loads((S/'parameters.json').read_text());QP=json.loads((Q/'parameters.json').read_text());AXES=[(-13.2,0),(13.2,0)];BOTTOM=11.484;TOP=13.284
caps={}
for suffix,side,(x,y) in zip(['LEFT','RIGHT'],[-1,1],AXES):
 a,b=sorted((side*15,side*35));cap=oldkeeper.intersect(box(a,b,-3.4,3.4,10.8,TOP))
 cap=cap.fuse(cyl(3,x,y,BOTTOM,TOP))
 a,b=sorted((x,side*16.3));cap=cap.fuse(box(a,b,-2.4,3.4,12.1,TOP))
 # Make both holes last, after every rib and ear has been joined.
 cap=cap.cut(cyl(1.2,x,y,10,TOP+.1)).cut(cq.Solid.makeCone(1.2,2.25,1.05,cq.Vector(x,y,TOP-1.05))).clean()
 assert cap.intersect(cyl(1.19,x,y,10.9,TOP-.01)).Volume()<.002
 caps[f'02_TCRT_clip_cap_{suffix}']=cap
# Fill only the obsolete QRE component recess ahead of the TCRT optical window.
# This stays above the exact narrowed/lowered QRE underside.
X=.1418;Y=-7.8658
frontfill=box(X-3.95,X+3.95,Y-6.53,Y-3.4,3.2,5.4)
base=base.fuse(frontfill)
# Lift the two small outer shoulder indent floors flush to the existing 6.4mm surface.
flush_patches=[]
for f in oldbase.Faces():
 bb=f.BoundingBox()
 if abs(bb.zmin-5.918)<.00001 and abs(bb.zmax-5.918)<.00001 and bb.ymin<-11 and bb.ymax<-6 and (bb.xmax<-11 or bb.xmin>11):
  patch=cq.Solid.extrudeLinear(f.outerWire(),[],cq.Vector(0,0,6.4-5.918));flush_patches.append(patch);base=base.fuse(patch)
assert len(flush_patches)==2
# Strip all remaining old crossbar stubs while keeping the latch beds and native receiver shape.
# Restore only the old crossbar clearance in the thin PCB rails, avoiding solder allowances.
# The empty crossbar space is now intentionally open; no bridging member is added.
for cap in caps.values():base=base.cut(cap)
for x,y in AXES:base=base.cut(cyl(.85,x,y,8,BOTTOM+.1))
base=base.clean()
solids={'01_TCRT_sensor_cradle':base,**caps,'03_TCRT_sensor_pressure_keeper':pressure}
M=json.loads((S/'assembly_manifest.json').read_text());E={e['name']:e for e in M['parts']};M.update(version='0.43',parts=[])
rep={'status':'BUILDING','mesh':{},'collisions':{},'source_sha256':{},'protected':{},'changes':{'crossbar_removed':True,'independent_clip_caps':2,'clip_through_hole_diameter_mm':2.4,'clip_countersink_diameter_mm':4.5,'clip_countersink_depth_mm':1.05,'gray_indent_patch_count':2,'old_QRE_front_recess_filled':True,'orange_clip_lips':'Unchanged per user clarification'}}
for n,s in solids.items():
 assert s.isValid() and len(s.Solids())==1,(n,s.isValid(),len(s.Solids()))
 if n=='03_TCRT_sensor_pressure_keeper':
  e=dict(E[n]);shutil.copy2(S/e['filename'],O/e['filename']);shutil.copy2(S/'stl'/(n+'.stl'),O/'stl'/(n+'.stl'));shutil.copy2(S/'step'/(n+'.step'),O/'step'/(n+'.step'));m=trimesh.load(O/e['filename'],force='mesh')
 else:
  cq.exporters.export(s,str(O/'step'/(n+'.step')));m=mesh(s);m.export(O/'preview'/(n+'.stl'));p=m.copy();rot=[0,-90,0] if n.startswith('01') else [0,0,0]
  for ax,angle in zip([(1,0,0),(0,1,0),(0,0,1)],rot):
   if angle:p.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(angle),ax))
  shift=np.r_[-p.bounds[:,:2].mean(axis=0),-p.bounds[0,2]];p.apply_translation(shift);p.export(O/'stl'/(n+'.stl'))
  e=dict(name=n,filename=f'preview/{n}.stl',color='#48545D' if n.startswith('01') else '#398B83',reference=False,printable=True,group='printed',source='User-marked v043 sensor-only revision',description='Smoothed narrow lower plate' if n.startswith('01') else 'Independent clip cap with vertical M2 clearance hole and countersunk seat',print_rotation_deg=rot,print_translation_mm=shift.tolist())
 M['parts'].append(e);rep['mesh'][n]=dict(watertight=m.is_watertight,components=len(m.split()),volume_mm3=m.volume,bounds_mm=m.bounds.tolist())
for n,e in E.items():
 if n in solids or n=='02_TCRT_clip_keeper':continue
 if e['reference'] or 'latch' in n:
  if n.startswith('REF_M2x5_CLIP'):continue
  shutil.copy2(S/e['filename'],O/e['filename'])
  if e['printable']:
   for d,ext in [('step','.step'),('stl','.stl')]:shutil.copy2(S/d/(n+ext),O/d/(n+ext))
  M['parts'].append(dict(e))
for i,(x,y) in enumerate(AXES,1):
 # Nominal M2x5 flat-head envelope; cylindrical stem enters the printed pilot.
 stem=cyl(1,x,y,TOP-5,TOP-1.05);head=cq.Solid.makeCone(1,2,1.05,cq.Vector(x,y,TOP-1.05));n=f'REF_M2x5_CLIP_{i}'
 mesh(stem.fuse(head)).export(O/'preview'/(n+'.stl'));M['parts'].append(dict(name=n,filename=f'preview/{n}.stl',reference=True,printable=False,group='hardware',color='#AAB1BA',source='Nominal fastener envelope',description='M2x5 countersunk screw, reuse existing clip screws'))
for n,s in solids.items():
 for nn,t in solids.items():
  if n<nn:
   v=s.intersect(t).Volume();rep['collisions'][n+' / '+nn]=v;assert v<.002,(n,nn,v)
for e in M['parts']:
 n=e['name']
 if n.startswith('REF_TCRT') or n=='REF_SENSOR_SOCKET_ALLOWANCE' or 'latch' in n:
  r=trimesh.load(O/e['filename'],force='mesh')
  for sn in solids:
   m=trimesh.load(O/'preview'/(sn+'.stl'),force='mesh');i=trimesh.boolean.intersection([m,r],engine='manifold');v=abs(i.volume) if i is not None and len(i.faces) else 0
   rep['collisions'][sn+' / '+n]=v;assert np.isfinite(v) and v<.002,(sn,n,v)
qbase=load(Q/'step/01_QRE_minimal_port.step');lower=box(-35,35,-25,25,-10,3.1)
a=qbase.intersect(lower);b=base.intersect(lower);v=a.cut(b).Volume()+b.cut(a).Volume();assert v<.002;rep['protected']['exact_QRE_narrow_lower_underside_difference_mm3']=v
for a,b in [(-35,-16),(16,35)]:
 roi=box(a,b,-6,6,-20,10.8);f=qbase.intersect(roi);t=base.intersect(roi);v=f.cut(t).Volume()+t.cut(f).Volume();assert v<.002;rep['protected'][f'hinge_{a}_{b}_difference_mm3']=v
for n,s in caps.items():
 side=-1 if 'LEFT' in n else 1;a,b=sorted((side*16,side*35));roi=box(a,b,-3.4,3.4,10.8,TOP)
 old=oldkeeper.intersect(roi);new=s.intersect(roi);v=old.cut(new).Volume()+new.cut(old).Volume();assert v<.002;rep['protected'][n+'_latch_bearing_faces_difference_mm3']=v
for i,(x,y) in enumerate(AXES):
 tool=cyl(1.9,x,y,TOP+.01,35);v=sum(s.intersect(tool).Volume() for s in solids.values());assert v<.002;rep['protected'][f'clip_screw_{i+1}_driver_overlap_mm3']=v
 for shank in [cyl(1.19,x,y,BOTTOM+.01,TOP-.1),cyl(.84,x,y,8.01,BOTTOM-.01)]:
  # Clearance above the pilot and pilot core are both fully round and unobstructed.
  v=base.intersect(shank).Volume();assert v<.002
for p in [S/'step/01_TCRT_sensor_cradle.step',S/'step/03_TCRT_sensor_pressure_keeper.step',Q/'step/02_QRE_clip_keeper.step',Q/'parameters.json',O/'references/USER_marked_exploded.png']:
 rep['source_sha256'][str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
P.update(version='0.43',clip_keeper_design='Two independent removable clip caps, no crossbar',clip_cap_through_hole_diameter_mm=2.4,clip_cap_countersink_diameter_mm=4.5,clip_cap_screw_axes_mm=AXES,central_step_width_at_y0_mm=QP['new_center_step_width_at_y0_mm'],central_platform_drop_mm=QP['central_platform_drop_mm'],central_trim_per_side_mm=QP['central_step_trim_per_side_mm'],gray_plate_cleanup='Unused QRE front recess filled flush to5.4; outer shoulder indent floors filled flush to6.4',orange_clip_lips='Kept unchanged per user answer',sensor_keeper='Existing v042 part, manufacturing STL byte-identical',replacement_parts=['01_TCRT_sensor_cradle','02_TCRT_clip_cap_LEFT','02_TCRT_clip_cap_RIGHT'])
rep['status']='PASS';(O/'reports/cad_validation.json').write_text(json.dumps(rep,indent=2));(O/'parameters.json').write_text(json.dumps(P,indent=2));(O/'assembly_manifest.json').write_text(json.dumps(M,indent=2))
allparts=[load(O/'step'/(e['name']+'.step')) for e in M['parts'] if e['printable']];cq.exporters.export(cq.Compound.makeCompound(allparts),str(O/'TCRT_split_keepers_v043.step'))
for n in ['LICENSE.txt','references/TCRT5000_measurements.md','references/BP_port_LICENSE.txt']:shutil.copy2(S/n,O/n)
(O/'README.md').write_text('TCRT5000 sensor-only mount v043\n\nUser markup changes: remove the teal U crossbar; replace it with two separate screw-on clip caps, each with a clear round M2 hole and countersunk seat. Smooth only the gray plate, retaining the orange clip lips. Keep the exact QRE narrow/lowered underside: 0.5 mm trim per side and 1 mm center drop.\n\nOld QRE front sensor relief is filled to the flat 5.4 mm center surface; the two outer gray shoulder indent floors are filled to their existing 6.4 mm height. TCRT seat and optical datum remain fixed.\n\nReuse the v042 sensor pressure keeper, two original launcher latches, two M2x4 sensor screws and two M2x5 countersunk clip screws. Print replacements: cradle + left clip cap + right clip cap. All six printable pieces are included in the unsliced STL package. The M5 carrier remains separate and unchanged.\n\nPhysical fit, screw preload and optical alignment remain unverified. No printer dispatch.\n')
shutil.copy2(__file__,O/'provenance'/Path(__file__).name)
print('PASS',O,flush=True)
