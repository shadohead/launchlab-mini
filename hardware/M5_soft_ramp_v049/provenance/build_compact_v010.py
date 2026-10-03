"""Integrated-mount v0.10. First generate compact modules with build_compact_modules_v010.py."""
from pathlib import Path
import json,shutil,hashlib,sys,math,numpy as np
import cadquery as cq
import trimesh
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
R=Path(__file__).resolve().parents[1];S=R/'inspection/v010_development/stacked_preintegration';OLD=R/'releases/LaunchLab_v092_direct_M3';O=R/'releases/LaunchLab_v010_compact_shielded'
assert not (O/'assembly_manifest.json').exists() or '--replace-draft' in sys.argv
for d in ['step','stl','preview','reports','renders','bambu','provenance']:(O/d).mkdir(parents=True,exist_ok=True)
M=json.loads((S/'assembly_manifest.json').read_text());P=json.loads((S/'parameters.json').read_text())
def load(n):return cq.importers.importStep(str(S/'step'/f'{n}.step')).val()
def box(w,l,h,x=0,y=0,z=0):return cq.Workplane('XY').box(w,l,h,centered=(True,True,False)).translate((x,y,z)).val()
def cyl(r,h,x=0,y=0,z=0):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
def bb(s):
 b=Bnd_Box();BRepBndLib.AddOptimal_s(s.wrapped,b,False,False);v=b.Get();return [list(v[:3]),list(v[3:])]
def prism(w,h,z):return cq.Solid.extrudeLinear(w,[],cq.Vector(0,0,h)).translate((0,0,z))
def repair_collinear_boundary(m):
 # STEP triangulation can leave a zero-area triangular T junction after STL
 # float32 welding. Split its long neighboring edge without filling any volume.
 for _ in range(10):
  edges,counts=np.unique(m.edges_sorted,axis=0,return_counts=True);edges=edges[counts==1]
  if not len(edges):break
  fixed=False
  for a,b in edges:
   pa,pb=m.vertices[[a,b]];d=pb-pa;length=np.linalg.norm(d)
   for c in np.unique(edges):
    if c in [a,b]:continue
    t=np.dot(m.vertices[c]-pa,d)/length**2
    if not 1e-5<t<1-1e-5 or np.linalg.norm(m.vertices[c]-(pa+t*d))>1e-5:continue
    if not any(set(e)=={a,c} for e in edges) or not any(set(e)=={b,c} for e in edges):continue
    fi=next(i for i,f in enumerate(m.faces) if a in f and b in f);f=m.faces[fi]
    j=next(j for j in range(3) if set([f[j],f[(j+1)%3]])=={a,b})
    u,v,w=int(f[j]),int(f[(j+1)%3]),int(f[(j+2)%3])
    faces=np.delete(m.faces,fi,axis=0);m.faces=np.vstack([faces,[u,c,w],[c,v,w]])
    fixed=True;break
   if fixed:break
  if not fixed:break
 return m
outline=[(-16,-22),(16,-22),(22,-16),(22,78),(20,84),(16,92),(-16,92),(-20,84),(-22,78),(-22,-16)]
wire=cq.Workplane('XY').polyline(outline).close().wire().val();inside=wire.offset2D(-2.15,kind='intersection')[0]
port=load('01_native_port_UNSCALED');lower=load('03_flat_mount');body=load('05_integrated_body');carrier=load('04_captured_sensor_cradle')
for sign in [-1,1]:body=body.fuse(box(.5,93,3,x=sign*20.05,y=30.5,z=32.9))
body=body.cut(box(6,5.2,2.2,x=20,y=74,z=33.5))
body=body.cut(box(40.6,48,8,y=6.5,z=28.5))
# Two short nose catches replace the front rails and keep the cassette top-loadable.
lid_shape=load('06_slide_lid').cut(box(44,46,6.3,y=7.5,z=30))
for x in [-17,17]:
 body=body.fuse(box(4.8,3.8,1.8,x=x,y=-17.7,z=34.5).intersect(prism(wire,40,0)))
 body=body.cut(box(3.8,4.5,1.6,x=x,y=-16.55,z=34.2))
 sign=1 if x>0 else -1
 tongue=cq.Workplane('XZ').polyline([(sign*15.4,34.5),(sign*18.0,34.5),(sign*16.9,35.6),(sign*15.4,35.6)]).close().extrude(3).translate((0,-14.4,0)).val()
 stem=box(1.0,1.2,1.8,x=sign*15.9,y=-15.0,z=34.5)
 # Forty-five-degree lower lead-in prints from the lid face without a free shelf.
 ramp=cq.Workplane('YZ').polyline([(-17.4,34.5),(-15.6,36.3),(-14.3,36.3),(-14.3,34.5)]).close().extrude(50).translate((-25,0,0)).val()
 lid_shape=lid_shape.fuse(tongue.fuse(stem).intersect(ramp))
# Internal removable cassette combines sensor support, shield, clip keepers and board pads.
# Retain the M3 head seat Z16.8 and sensor optical coordinates.
region=prism(inside,28,0).intersect(box(37,45,28,y=7,z=0))
core=body.intersect(region)
retainer=core.fuse(lower).fuse(carrier).intersect(region)
for sign in [-1,1]:
 for y in [-7.8658,10.1342]:retainer=retainer.cut(box(1.3,3.8,9,x=.1418+sign*8.1,y=y,z=13.3))
for x in [-13.903,13.927]:
 for y in [-9.279,9.461]:retainer=retainer.cut(cyl(3.2,26,x,y,16.8))
clearwire=wire.offset2D(-1.85,kind='intersection')[0]
clearregion=prism(clearwire,42,0).intersect(box(80,45.6,43,y=7,z=0))
clearregion=clearregion.intersect(box(37.6,90,27.7,y=20,z=0).fuse(box(80,90,16,y=20,z=27.7)))
base=body.cut(clearregion).fuse(port)
# Continuous upper port walls connect directly to case foundation, staying
# within donor planform and outside clip swing bays.
for y in [-15.675,15.675]:base=base.fuse(box(39.4,1.6,5.6,y=y,z=10.1))
for x in [-19.6,19.6]:
 for y in [-10.9,10.9]:base=base.fuse(box(1.6,8.4,10.2,x=x,y=y,z=5.5))
walls=base.cut(port).cut(clearregion)
base=port.fuse(walls).clean();retainer=retainer.clean()
shapes={'01_integrated_mount_body':base,'02_latch_RIGHT':load('02_latch_RIGHT'),'02_latch_LEFT':load('02_latch_LEFT'),'03_sensor_clip_retainer':retainer,'06_slide_lid':lid_shape.clean(),'07_battery_deck':load('07_battery_deck')}
M['parts']=[e for e in M['parts'] if e['name'] not in ['01_native_port_UNSCALED','03_flat_mount','04_captured_sensor_cradle','05_integrated_body']]
for n,group,color,rot,desc in [
 ('01_integrated_mount_body','case','#C92E35',[0,-90,0],'Original-scale native port extends directly into compact case base. Two pivot clips, no separate external bracket.'),
 ('03_sensor_clip_retainer','sensor','#252B32',[90,0,0],'Removable internal cassette: clip keepers, sensor cradle, optical shield and four board supports. Four M3x10 direct screws; two M2 board screws.')]:
 M['parts'].append(dict(name=n,filename='preview/'+n+'.stl',group=group,color=color,reference=False,printable=True,print_rotation_deg=rot,source='LaunchLab v0.10 integrated mount',description=desc))
report={'version':'0.10','architecture':'integrated mount/base + internal sensor/clip cassette','cad':{},'nominal_collisions':[],'preserved_clip_exports':{},'limits':['New mount/body print orientation needs slicing; supports may be necessary','No physically registered whole-launcher model','Sensor, plug and wiring clearances still require assembly test','PLA color alone does not establish infrared opacity']}
points=[(.1418,38.1342,20.5),(.1418,40.1342,22.8)]
for deg in range(15,91,15):
 a=math.radians(deg);points.append((.1418-6+6*math.cos(a),40.1342+6*math.sin(a),22.8))
points.append((-10.5,46.1342,22.8))
for deg in range(105,181,15):
 a=math.radians(deg);points.append((-10.5+6*math.cos(a),40.1342+6*math.sin(a),22.8))
points += [(-16.5,30,22.8),(-16.5,-6,22.8)]
sensor_wire=cq.Solid.makeSphere(2,cq.Vector(*points[0]))
for a,b in zip(points,points[1:]):
 va=cq.Vector(*a);vb=cq.Vector(*b);d=vb-va
 sensor_wire=sensor_wire.fuse(cq.Solid.makeCylinder(2,d.Length,va,d.normalized())).fuse(cq.Solid.makeSphere(2,vb))
battery_lead_exit=cq.Workplane('XY').box(12,5,3,centered=(True,True,False)).edges('|Z').fillet(.4).translate((0,32.2,31.8)).val()
batpoints=[(5,32.3,33),(12,31.4,31)]
for deg in range(75,-1,-15):
 a=math.radians(deg);batpoints.append((12+4.5*math.cos(a),26.9+4.5*math.sin(a),31))
batpoints.append((16.5,-7,31))
battery_wires=cq.Solid.makeSphere(1,cq.Vector(*batpoints[0]))
for a,b in zip(batpoints,batpoints[1:]):
 va=cq.Vector(*a);vb=cq.Vector(*b);d=vb-va
 battery_wires=battery_wires.fuse(cq.Solid.makeCylinder(1,d.Length,va,d.normalized())).fuse(cq.Solid.makeSphere(1,vb))
M['parts'].append(dict(name='REF_BATTERY_WIRE_RETURN_ALLOWANCE',filename='preview/REF_BATTERY_WIRE_RETURN_ALLOWANCE.stl',group='clearance',color='#BCA06B',reference=True,printable=False,source='LaunchLab v0.10 provisional routing',description='2mm bundle allowance along positive-X side, screen-facing battery leads, 4.5mm bend. Actual lead length, bundle and terminal approach unmeasured.'))
for e in M['parts']:
 n=e['name']
 if n not in shapes:
  if n in ['REF_BATTERY_LEAD_EXIT_ALLOWANCE','REF_BATTERY_WIRE_RETURN_ALLOWANCE']:
   s=battery_lead_exit if n=='REF_BATTERY_LEAD_EXIT_ALLOWANCE' else battery_wires
   cq.exporters.export(s,str(O/e['filename']),tolerance=.035,angularTolerance=.08)
   e['description']='PROVISIONAL screen-facing battery lead exit and side return; actual cable size, length and final connection not measured.'
   continue
  if n=='REF_SENSOR_WIRE_RETURN_ALLOWANCE':
   cq.exporters.export(sensor_wire,str(O/e['filename']),tolerance=.035,angularTolerance=.08)
   e['description']='PROVISIONAL 4mm bundle,6mm bendradius; return at X=-16.5 clear of screen supports. Physical routing and wire length unmeasured.'
  else:shutil.copy2(S/e['filename'],O/e['filename'])
  continue
 s=shapes[n];assert s.isValid() and len(s.Solids())==1,(n,[(a.Volume(),bb(a)) for a in s.Solids()])
 cq.exporters.export(s,str(O/'step'/f'{n}.step'))
 cq.exporters.export(s,str(O/'preview'/f'{n}.stl'),tolerance=.035,angularTolerance=.08)
 p=s
 for axis,angle in zip([(1,0,0),(0,1,0),(0,0,1)],e['print_rotation_deg']):
  if angle:p=p.rotate((0,0,0),axis,angle)
 b=bb(p);p=p.translate((-(b[0][0]+b[1][0])/2,-(b[0][1]+b[1][1])/2,-b[0][2]))
 cq.exporters.export(p,str(O/'stl'/f'{n}.stl'),tolerance=.035,angularTolerance=.08)
 for d in ['preview','stl']:
  f=O/d/f'{n}.stl';m=trimesh.load(f,force='mesh');m.merge_vertices(digits_vertex=5);m.update_faces(m.unique_faces());m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices()
  if d=='stl':m.apply_translation([0,0,-m.bounds[0,2]])
  v=m.volume;m=repair_collinear_boundary(m);assert abs(m.volume-v)<.001
  m.export(f);assert m.is_watertight and m.is_winding_consistent and len(m.split())==1,(n,d)
 if n.startswith('02_'):
  for d in ['step','stl','preview']:
   f=OLD/d/(n+('.step' if d=='step' else '.stl'));shutil.copy2(f,O/d/f.name);report['preserved_clip_exports'][str((O/d/f.name).relative_to(O))]=hashlib.sha256(f.read_bytes()).hexdigest()
 report['cad'][n]={'bounds_mm':bb(s),'volume_mm3':s.Volume()};print('export',n,flush=True)
for i,(n,a) in enumerate(shapes.items()):
 for m,b in list(shapes.items())[i+1:]:
  v=a.intersect(b).Volume()
  if v>1e-4:report['nominal_collisions'].append([n,m,v])
report['port_material_removed_mm3']=port.cut(base).Volume();assert report['port_material_removed_mm3']<1e-5
report['base_change_below_z5p5_mm3']=base.cut(port).intersect(box(50,34,5.5,z=0)).Volume()
assert report['base_change_below_z5p5_mm3']<1e-5
P['print_optimization'].update(assembly_printed_parts=6,replacement_printed_parts=4,
 body_orientation='Long side down, Y rotation -90; supports required',
 lower_mount_orientation='Internal retainer front edge down, X rotation +90; supports required',
 short_bridges='Lid front catches use 45 degree lead-ins; base and retainer retain supported overhangs',
 servicing='Release lid inward and slide +Y. Remove board using two underside M2 screws, then four M3x10 cassette screws.')
P.update(case_base_z=15.4,case_height=22.5,wall=1.8,case_height_excludes_integral_mount_mm=22.5)
P['mount_status']='v092 original-scale port and both clips preserved; user reports v092 assembly fits. New integrated structure requires fit check; no whole-launcher CAD registration proof.'
P['direct_M3_mount']['clamp_load_path']='head to internal retainer to four preserved port post-top bearing annuli'
P['sensor_connector_allowance']['wire_return_centerline_x_mm']=-16.5
P['sensor_connector_allowance']['wire_loop_max_y_mm']=48.1342
P['battery_deck']['locator_pin_xy_mm']=[[x,y] for x in [-14.7,14.7] for y in [52,80]]
P['battery_deck']['width_mm']=33.8
P['battery_deck']['lead_direction']='-Y screen end, positive-X side return; provisional routing'
P['prior_compatibility']='Reuse both working clips only. New integral mount/body, internal retainer, lid and battery deck replace the old mount stack.'
P['architecture']='Mount is case base; internal removable cassette allows clip installation, sensor service and screen support.'
P['design_intent']='Compact integrated mount/body; head right/string-side, wires and battery left. Six printed parts, no new screws.'
P['fasteners']['mount_thread']='4 M3x10 retain internal cassette directly in preserved port pilots; 2 M2 board screws unchanged.'
M['parts'].sort(key=lambda e:e['name'])
(O/'assembly_manifest.json').write_text(json.dumps(M,indent=2));(O/'parameters.json').write_text(json.dumps(P,indent=2));(O/'reports/cad_validation.json').write_text(json.dumps(report,indent=2))
shutil.copy2(OLD/'LICENSE.txt',O/'LICENSE.txt')
for n in ['build_compact_v010.py','build_compact_modules_v010.py']:shutil.copy2(R/'scripts'/n,O/'provenance'/n)
print('COLLISIONS',report['nominal_collisions']);assert not report['nominal_collisions']
print('INTEGRATED_CAD_COMPLETE',O)
