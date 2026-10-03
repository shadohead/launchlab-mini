"""Lowered M5/QRE stack. Sensor sets the height; original launcher hooks stay at source scale."""
from pathlib import Path
import ast,hashlib,json,shutil
import cadquery as cq,numpy as np,trimesh
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
R=Path(__file__).resolve().parents[1];S=R/'releases/LaunchLab_v016_qre1113';O=R/'releases/LaunchLab_v018_low_stack'
assert not (O/'SHA256SUMS.txt').exists(),'Delivered releases are immutable'
for d in ['step','stl','preview','reports','renders','bambu','provenance','references','extras']:(O/d).mkdir(parents=True,exist_ok=True)
for n in ast.parse((R/'scripts/build_compact_v010.py').read_text()).body:
 if isinstance(n,ast.FunctionDef) and n.name in ['box','bb','prism','repair_collinear_boundary']:exec(compile(ast.Module(body=[n],type_ignores=[]),'geometry_helpers','exec'))
def rect(x0,x1,y0,y1,z0,z1):return box(x1-x0,y1-y0,z1-z0,(x0+x1)/2,(y0+y1)/2,z0)
def cyl(r,x,y,z0,z1):return cq.Solid.makeCylinder(r,z1-z0,cq.Vector(x,y,z0))
def load(p):return cq.importers.importStep(str(p)).val()
X=.1418;Y=-7.8658;CENTERS=json.loads((R/'source/LaunchLab_v02/parameters.json').read_text())['source_screw_centers_mm']
oldport=load(R/'source/LaunchLab_v02/step/01_native_port_UNSCALED.step')
oldret=load(R/'releases/LaunchLab_v015_m5sticks3/step/03_sensor_clip_retainer.step')
# Keep launcher underside/pivot seats. Lower the legacy post crowns and add
# short post feet above the launcher plane so the recessed M3x5 screws retain
# 3.0 mm of thread engagement instead of hanging in the old post-bottom void.
M5BACK=10.3;M5TOP=25.3;DECK_BOTTOM=8.;DECK_TOP=10.;MOUNT_FACE=12.3
rw=cq.Workplane('XY').polyline([(-18.5,16),(-18.5,-13.42229),(-17.46115,-15.5),(17.46115,-15.5),(18.5,-13.42229),(18.5,16)]).close().wire().val()
clear=prism(rw.offset2D(.25,kind='intersection')[0],7,8).cut(rect(-35,-15.2,-6.6,6.6,7.9,16)).cut(rect(15.2,35,-6.6,6.6,7.9,16))
base=oldport.cut(clear).cut(rect(-12.5,12.5,-24,24,8,16))
for x,y in CENTERS:
 base=base.cut(cyl(3.65,x,y,8,14)).fuse(cyl(3.4,x,y,4.7,8)).cut(cyl(1.2,x,y,4.5,8.1))
base=base.cut(rect(X-6.4,X+6.4,Y-9.45,Y+7.75,5,15)).cut(rect(X-3.8,X+3.8,Y+1.4,Y+3.7,4.7,5.11)).clean()
M5SCREWS=[(-9,21),(9,21)]
def sensor_carrier(width):
 bx0,bx1=X-width/2,X+width/2;by0,by1=Y-7.65,Y+6.35
 pocket=(bx0-.3,bx1+.3,by0-.3,by1+.3);outer=(bx0-1.6,bx1+1.6,by0-1.5,by1+1.1)
 side=oldret.cut(rect(-9,9,-40,50,-20,80)).intersect(rect(-60,60,-3.4,3.4,10.8,13.284))
 w=cq.Workplane('XY').polyline([(-18.5,16),(-18.5,-13.42229),(-17.46115,-15.5),(17.46115,-15.5),(18.5,-13.42229),(18.5,16)]).close().wire().val()
 carrier=rect(*outer,5.1,9.6).cut(rect(*pocket,6.1,15.5)).cut(rect(bx0+.6,bx1-.6,outer[2]-.1,outer[3]+.1,3.5,6.11))
 carrier=carrier.cut(rect(*pocket[:2],by1+.3,outer[3]+.1,5,15.5)).cut(rect(bx0+.6,bx1-.6,by1-.8,outer[3]+.1,5,15.5))
 ret=side.fuse(prism(w,2,8)).fuse(carrier).cut(rect(*pocket,6.1,15.5))
 for a,b in [(bx0-.3,bx0+.6),(bx1-.6,bx1+.3)]:ret=ret.fuse(rect(a,b,by0+.2,by1-.9,8.4,9.6))
 for a,b in [(outer[0]-.1,bx0+.1),(bx1-.1,outer[1]+.1)]:ret=ret.cut(rect(a,b,by1-.15,by1+.65,6.35,7.65))
 # Open rear wire bay and a narrow front exit beneath the M5 back support.
 ret=ret.cut(rect(X-4,X+4,by1-.3,2,9.8,14.8)).cut(rect(-6.8,6.8,2,16.1,9.5,14.8))
 ret=ret.cut(rect(-1.4,1.4,outer[2]-.1,by0+.2,8.2,9.7))
 ret=ret.cut(rect(-35,-15.2,-6.6,6.6,7.8,10.1)).cut(rect(15.2,35,-6.6,6.6,7.8,10.1))
 # Original keeper contact geometry is carried by two outboard supports.
 for sx in [-1,1]:
  ret=ret.fuse(rect(*sorted((sx*14.2,sx*14.95)),-3.,3.,9.8,14.4)).fuse(rect(*sorted((sx*14.2,sx*18.5)),-3.4,3.4,13.284,14.4))
 for x,y in CENTERS:
  ret=ret.cut(cyl(1.7,x,y,7.8,10.2)).cut(cq.Solid.makeCone(1.7,3.1,1.4,cq.Vector(x,y,8.7)))
 return ret.clean(),(bx0,bx1,by0,by1,6.1,8.1),outer
def dock(width):
 ret,board,outer=sensor_carrier(width)
 # An open skeleton under the factory back: two beams and three crossbars.
 deck=rect(-12,-7,-23,23,DECK_BOTTOM,DECK_TOP).fuse(rect(7,12,-23,23,DECK_BOTTOM,DECK_TOP))
 for a,b in [(-23,-19),(-1.5,1.5)]:deck=deck.fuse(rect(-12,12,a,b,DECK_BOTTOM,DECK_TOP))
 for x,y in M5SCREWS:deck=deck.fuse(cyl(2.5,x,y,DECK_BOTTOM,MOUNT_FACE)).cut(cyl(1.2,x,y,DECK_BOTTOM-.1,MOUNT_FACE+.1))
 deck=deck.fuse(rect(-7,7,21,23,9.8,12.1))
 ret=ret.fuse(deck).cut(rect(-1.4,1.4,-24,3,8,10.1))
 # Board and short solder tails slide through this channel after the M5 lifts off.
 ret=ret.cut(rect(-6.8,6.8,board[3]-.3,20.99,5,10.1))
 for x,y in CENTERS:
  ret=ret.cut(cyl(1.7,x,y,7.8,10.2)).cut(cq.Solid.makeCone(1.7,3.1,1.4,cq.Vector(x,y,8.7)))
 return ret.clean(),board,outer
stack,BOARD,OUTER=dock(9);native,NATIVEBOARD,_=dock(7.62)
parts={'01_attachment_port':base,'03_sensor_m5_dock':stack}
meta={'01_attachment_port':('#C13C47',[0,-90,0],'Launcher attachment','Source-scale launcher pivots/underside, shorter mount posts with new feet and QRE pocket.'),'03_sensor_m5_dock':('#417767',[0,-90,0],'Open sensor/device dock','Low countersunk plate, original keeper faces on outboard wings, QRE rails and open M5 back support.')}
M=json.loads((S/'assembly_manifest.json').read_text());E={e['name']:e for e in M['parts']};manifest={'version':'0.18','units':'mm','parts':[]};report={'cad':{},'mesh':{},'source_sha256':{},'nominal_collisions':[]}
def export(n,s,color,rot,group,desc,d=''):
 assert s.isValid() and len(s.Solids())==1,(n,s.isValid(),len(s.Solids()))
 if d:
  cq.exporters.export(s,str(O/d/f'{n}.step'))
 else:cq.exporters.export(s,str(O/'step'/f'{n}.step'));cq.exporters.export(s,str(O/'preview'/f'{n}.stl'),tolerance=.025,angularTolerance=.08)
 p=s
 for ax,a in zip([(1,0,0),(0,1,0),(0,0,1)],rot):
  if a:p=p.rotate((0,0,0),ax,a)
 b=bb(p);p=p.translate((-(b[0][0]+b[1][0])/2,-(b[0][1]+b[1][1])/2,-b[0][2]));cq.exporters.export(p,str(O/(d or 'stl')/f'{n}.stl'),tolerance=.025,angularTolerance=.08)
 for folder in ([d] if d else ['preview','stl']):
  f=O/folder/f'{n}.stl';m=trimesh.load(f,force='mesh');m.merge_vertices(digits_vertex=5);m.update_faces(m.unique_faces());m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices();m=repair_collinear_boundary(m);assert m.is_watertight and m.is_winding_consistent and len(m.split())==1,(n,folder);m.export(f);report['mesh'][str(f.relative_to(O))]={'watertight':True,'components':1,'volume_mm3':float(m.volume)}
 report['cad'][n]={'bounds_mm':bb(s),'volume_mm3':s.Volume()}
 if not d:manifest['parts'].append({'name':n,'filename':f'preview/{n}.stl','color':color,'group':group,'reference':False,'printable':True,'print_rotation_deg':rot,'description':desc,'source':'LaunchLab v0.18'})
 print('EXPORTED',n,flush=True)
for n in ['02_latch_LEFT','02_latch_RIGHT']:
 for d,ext in [('step','.step'),('preview','.stl'),('stl','.stl')]:shutil.copy2(S/d/(n+ext),O/d/(n+ext))
 manifest['parts'].append(E[n])
for n,s in parts.items():export(n,s,*meta[n])
export('03_OPEN_DOCK_NATIVE_7p62_OPTION',native,'#417767',[0,-90,0],'Option','Same open dock for 7.62 mm PCB',d='extras')
mountcoupon=stack.intersect(rect(-12,12,12,24,DECK_BOTTOM,MOUNT_FACE)).clean()
export('13_M5_MOUNT_FIT',mountcoupon,'#417767',[0,0,0],'Mount fit coupon','Two M2 pads and short back-support beams',d='extras')
fastfit=cyl(3.4,0,0,0,3.3).fuse(rect(-5,5,-5,5,3.3,5.3)).cut(cyl(1.2,0,0,-.1,3.31)).cut(cyl(1.7,0,0,3.3,5.4)).cut(cq.Solid.makeCone(1.7,3.1,1.4,cq.Vector(0,0,4.0)))
export('14_M3_COUNTERSUNK_FIT',fastfit,'#417767',[180,0,0],'Fastener fit coupon','Exact short post and recessed M3x5 seat; print face down',d='extras')
for n,s in [('11_QRE_FIT_9mm',stack),('12_QRE_FIT_7p62mm',native)]:
 coupon=s.intersect(rect(X-6.25,X+6.25,Y-9.2,Y+7.8,5,10)).clean();export(n,coupon,'#5489B2',[0,0,0],'Fit coupon','Exact lower QRE rails',d='extras')
# Manufacturer STL contains an assembled device and exploded copies. Keep only
# the three assembled pieces at X0..24; rotate so Grove faces free tail +Y.
vendor=trimesh.load(str(R/'releases/LaunchLab_v017_open_stack/references/StickS3_VENDOR_ASSEMBLY_AND_EXPLODED.stl'),force='mesh');vs=[s for s in vendor.split(only_watertight=False) if s.bounds[1,0]<25]
assert len(vs)==3
actual=trimesh.util.concatenate(vs);actual.apply_transform(np.diag([-1,-1,1,1]));actual.apply_translation([12,24.06066132,24.37736397]);assert actual.is_watertight
actual.export(O/'preview/REF_M5_OFFICIAL_GEOMETRY.stl')
def solidmesh(s):
 v,f=s.tessellate(.025,.1);return trimesh.Trimesh(vertices=[p.toTuple() for p in v],faces=f,process=True)
def bm(*a):return solidmesh(rect(*a))
by1=BOARD[3];pcb=rect(*BOARD).cut(cyl(1.651,X,Y+6.35-11.43,5.9,8.3))
liner=cq.Compound.makeCompound([rect(-12,-7,-23,15,10,10.3),rect(7,12,-23,15,10,10.3),rect(-7,-6.8,-1.5,1.5,10,10.3),rect(6.8,7,-1.5,1.5,10,10.3)])
refs={
 'REF_M5_OFFICIAL_GEOMETRY':(actual,'electronics','#858F9E','Manufacturer assembled geometry, Grove +Y, back lowest Z10.3; no factory screws removed.'),
 'REF_M5_BODY_ENVELOPE':(bm(-12.001,12.001,-24,24,10.3,25.3),'fit_envelope','#8B9099','Conservative product envelope only; actual stepped back used for mounting pads.'),
 'REF_M5_SOFT_LINER':(solidmesh(liner),'liner','#59646E','0.3 mm thin liner on the open back beams.'),
 'REF_QRE_PCB_USER_14x9x2':(solidmesh(pcb),'electronics','#365D9D','User-measured PCB, source analog mounting-hole/element positions.'),
 'REF_QRE_SENSOR':(bm(X-1.5,X+1.5,Y-1.8,Y+1.8,4.1,6.1),'electronics','#48525E','2 mm sensor projection, original optical plane retained.'),
 'REF_QRE_UNDERSIDE_ALLOWANCE':(bm(X-3.6,X+3.6,Y+1.6,Y+3.5,4.9,6.1),'clearance','#C68A60','Provisional underside resistor/solder allowance.'),
 'REF_QRE_TOP_SOLDER':(bm(X-3.9,X+3.9,by1-2.2,by1-.3,8.1,9.5),'clearance','#C68A60','Short soldered leads; no tall upright QRE header.'),
 'REF_QRE_REAR_STOP_TIE':(bm(OUTER[0]-.1,OUTER[1]+.1,by1+.3,by1+.6,6.4,7.5),'clearance','#A59173','Thin flexible PCB rear stop through the two cheek tunnels.'),
 'REF_HAT_PLUG':(bm(-7.6,10.2,-32,-24,15.23,17.83),'clearance','#CE8459','Provisional short Hat connections for existing 3.3 V/GND/G1 wiring. Actual plug lengths and bends unmeasured.'),
 'REF_WIRE_ROUTE':(trimesh.util.concatenate([bm(-1.1,1.1,-30.5,3,8.3,9.3),bm(-1.1,1.1,-30.5,-28.3,9.3,15.23)]),'clearance','#D29243','Provisional thin soldered three-wire bundle through the open center slot to Hat. Actual bends/slack unverified.'),
 'REF_M5_SCREEN_VISUAL_ONLY':(bm(-8,8,-19,5,24.32,24.36),'visual','#111B24','Illustrative display face; actual factory controls fully exposed.')}
for i,(x,y) in enumerate(CENTERS,1):refs[f'REF_M3x5_COUNTERSUNK_{i}']=(solidmesh(cyl(1.5,x,y,5,8.5).fuse(cq.Solid.makeCone(1.3,3,1.7,cq.Vector(x,y,8.3)))),'fasteners','#AAB1BA','M3x5 DIN7991, 6 mm head / 90 degrees. Total length includes head; 3 mm engagement, tip Z5.')
for i,(x,y) in enumerate(M5SCREWS,1):refs[f'REF_M2x6_DEVICE_{i}']=(solidmesh(cyl(1,x,y,8,14).fuse(cyl(1.9,x,y,6.6,8))),'fasteners','#AAB1BA','M2x6 from underside; unchanged 1.7 mm nominal insert engagement.')
for n,(m,g,c,d) in refs.items():
 m.export(O/'preview'/f'{n}.stl');manifest['parts'].append({'name':n,'filename':f'preview/{n}.stl','group':g,'color':c,'reference':True,'printable':False,'description':d,'source':'Manufacturer geometry / user measurement / nominal harness'})
for n,a in parts.items():
 for t,b in parts.items():
  if n<t and a.intersect(b).Volume()>.005:report['nominal_collisions'].append([n,t,a.intersect(b).Volume()])
assert not report['nominal_collisions'],report['nominal_collisions']
for p in [R/'source/LaunchLab_v02/step/01_native_port_UNSCALED.step',S/'stl/02_latch_LEFT.stl',S/'stl/02_latch_RIGHT.stl',Path(str(R/'releases/LaunchLab_v017_open_stack/references/StickS3_VENDOR_ASSEMBLY_AND_EXPLODED.stl'))]:report['source_sha256'][str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
params={'version':'0.18','architecture':'Low open stack: shortened screw posts, recessed fasteners and sensor directly under the exposed M5','units':'mm','device':'M5StickS3 K150, intact factory shell','sensor_board_mm':[14,9,2],'sensor_projection_mm':2,'optical_face_z_mm':4.1,'launcher_top_z_mm':3.78,'sensor_center_xy_mm':[X,Y],'PCB_box_mm':BOARD,'PCB_pocket_clearance_mm':.3,'mount_screw_centres_mm':CENTERS,'M5_screw_centres_mm':M5SCREWS,'M5_mount_face_z_mm':MOUNT_FACE,'M5_mount_pad_step_above_back_mm':2.,'M5_back_z_mm':M5BACK,'M5_max_z_mm':M5TOP,'M5_orientation':'Grove/USB +Y, Hat -Y','deck_z_mm':[8,10],'printed_port_mm':[43.146,32.95,13.284],'open_deck_mm':[24,48],'electronics_Y_mm':[-24,24],'provisional_Hat_plug_Y_mm':[-32,-24],'new_printed_parts':list(parts),'reuse':['02_latch_LEFT','02_latch_RIGHT'],'fasteners':{'mount':'4 x M3x5 DIN7991 countersunk, 6 mm head, 90 degree seat','M5':'2 x M2x6 pan head, from underside','M5_nominal_thread_engagement_mm':1.7,'mount_thread_engagement_mm':3.,'mount_tip_z_mm':5.,'mount_tip_above_launcher_plane_mm':1.22},'user_confirmation':'M2 fits the two brass holes beside the Grove connector','attachment':'Two M2 screws in the user-confirmed brass mounts; Grove is unused for mounting and electrical connection','wiring':{'VCC':'Hat 3V3_L2','GND':'Hat GND','OUT':'Hat G1, existing analog input','status':'Existing wiring retained, no ADC or external-power configuration change'},'limits':['Hat plug and wires are provisional allowances, not actual measured harness solids.','M5 inserts are user-confirmed M2; source model gives 18 mm spacing and a 2 mm raised mounting face. Depth must be checked before tightening.','QRE element positions use manufacturer analog PCB drawing; dimensions are user measurements. Print both width coupons first.','No whole-launcher registration, physical fit, strength, retention, actual launch optical response, RPM accuracy or battery runtime is proved.','Shorter printed mount posts require this matching base/dock and new M3x5 countersunk screws. Do not combine with earlier mount parts. No printer dispatch or firmware/device changes performed.']}
old=json.loads((R/'releases/LaunchLab_v017_open_stack/reports/cad_validation.json').read_text());oldvolume=sum(old['cad'][n]['volume_mm3'] for n in ['01_attachment_port','03_sensor_m5_dock']);newvolume=sum(s.Volume() for s in parts.values());params['comparison_v017']={'old_replacement_volume_mm3':oldvolume,'new_replacement_volume_mm3':newvolume,'less_printed_material_percent':100*(1-newvolume/oldvolume),'old_M5_top_z_mm':33.3,'new_M5_top_z_mm':25.3,'lower_mm':8.,'height_above_launcher_before_mm':29.52,'height_above_launcher_now_mm':21.52,'height_above_launcher_reduction_percent':100*8/29.52,'printed_parts_before':2,'printed_parts_now':2}
(O/'parameters.json').write_text(json.dumps(params,indent=2));(O/'assembly_manifest.json').write_text(json.dumps(manifest,indent=2));(O/'reports/cad_validation.json').write_text(json.dumps(report,indent=2));cq.exporters.export(cq.Compound.makeCompound(list(parts.values())),str(O/'LaunchLab_v018_low_stack_assembly.step'))
for p in ['LICENSE.txt','references/K150-sticks3-dimensions.pdf','references/SparkFun_QRE1113_Analog.brd']:shutil.copy2(S/p,O/p)
shutil.copy2(str(R/'releases/LaunchLab_v017_open_stack/references/StickS3_VENDOR_ASSEMBLY_AND_EXPLODED.stl'),O/'references/StickS3_VENDOR_ASSEMBLY_AND_EXPLODED.stl');shutil.copy2(__file__,O/'provenance'/Path(__file__).name)
(O/'references/sources.txt').write_text('M5 official structure: https://github.com/m5stack/M5_Hardware/tree/master/Products/K150_StickS3/Structures\nM5 docs/pin map: https://docs.m5stack.com/en/core/StickS3\nSparkFun analog: https://github.com/sparkfun/QRE1113_Line_Sensor-Analog\nUser measured PCB and confirmed M2 brass mounting holes. Manufacturer geometry is an unmodified reference, not licensed new printed geometry.\n')
print('CAD_COMPLETE',params['comparison_v017'],flush=True)
