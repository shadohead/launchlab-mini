"""Separate compact OLD TCRT5000 + exposed M5StickS3 variant. Do not modify v0.17."""
from pathlib import Path
import ast,hashlib,json,shutil
import cadquery as cq,numpy as np,trimesh
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
R=Path(__file__).resolve().parents[1];S=R/'releases/LaunchLab_v017_open_stack';O=R/'releases/LaunchLab_v019_tcrt5000_open_stack'
assert not (O/'SHA256SUMS.txt').exists(),'Delivered releases are immutable'
for d in ['step','stl','preview','reports','renders','bambu','provenance','references','extras']:(O/d).mkdir(parents=True,exist_ok=True)
for n in ast.parse((R/'scripts/build_compact_v010.py').read_text()).body:
 if isinstance(n,ast.FunctionDef) and n.name in ['box','bb','prism','repair_collinear_boundary']:exec(compile(ast.Module(body=[n],type_ignores=[]),'geometry_helpers','exec'))
def rect(x0,x1,y0,y1,z0,z1):return box(x1-x0,y1-y0,z1-z0,(x0+x1)/2,(y0+y1)/2,z0)
def cyl(r,x,y,z0,z1):return cq.Solid.makeCylinder(r,z1-z0,cq.Vector(x,y,z0))
def load(p):return cq.importers.importStep(str(p)).val()
def solidmesh(s):
 vs,fs=s.tessellate(.025,.1);return trimesh.Trimesh([v.toTuple() for v in vs],fs,process=True)
def bm(*a):return solidmesh(rect(*a))
X=.1418;Y=-7.8658;CENTERS=json.loads((R/'source/LaunchLab_v02/parameters.json').read_text())['source_screw_centers_mm']
# Explicit measurement reconciliation: 12 mm from PCB lower face to lens tips.
PCB_BOTTOM=16.1;PCB_TOP=17.1;POT_TOP=23.1;M5BACK=23.9;M5TOP=38.9
DECK_BOTTOM=21.6;DECK_TOP=23.6;MOUNT_FACE=25.9;M5SCREWS=[(-9,-15),(9,-15)]
BX0,BX1=X-6.5,X+6.5;BY0,BY1=Y-4,Y+27;BOARD=(BX0,BX1,BY0,BY1,PCB_BOTTOM,PCB_TOP)
POCKET=(BX0-.3,BX1+.3,BY0-.3,BY1+.3);OUTER=(BX0-1.6,BX1+1.6,BY0-1.3,BY1+1.3)
base=load(S/'step/01_attachment_port.step')
# Recess for the OLD 7x6 lens-pair envelope. No actual launcher alteration.
base=base.cut(rect(X-3.9,X+3.9,Y-3.4,Y+3.4,3.79,15.)).clean()
oldret=load(R/'releases/LaunchLab_v015_m5sticks3/step/03_sensor_clip_retainer.step')
side=oldret.cut(rect(-9,9,-40,50,-20,80)).intersect(rect(-60,60,-40,50,-20,13.284))
w=cq.Workplane('XY').polyline([(-18.5,16),(-18.5,-13.42229),(-17.46115,-15.5),(17.46115,-15.5),(18.5,-13.42229),(18.5,16)]).close().wire().val()
dock=side.fuse(prism(w,1.4,13.284)).cut(rect(*POCKET,13.2,20))
# Two thin cheeks, four underside corner lands, and low PCB end stops.
for a,b in [(OUTER[0],POCKET[0]),(POCKET[1],OUTER[1])]:dock=dock.fuse(rect(a,b,OUTER[2],OUTER[3],13.284,17.3))
for ya,yb in [(OUTER[2],POCKET[2]),(POCKET[3],OUTER[3])]:dock=dock.fuse(rect(OUTER[0],OUTER[1],ya,yb,13.284,16.9))
cornerY=[(BY0+.6,BY0+2.1),(BY1-2.1,BY1-.6)]
for xa,xb in [(POCKET[0],BX0+.6),(BX1-.6,POCKET[1])]:
 for ya,yb in cornerY:dock=dock.fuse(rect(xa,xb,ya,yb,14.684,PCB_BOTTOM))
# Removable sensor corner keeper. No sensor PCB holes or solder pads are assumed.
keeper=rect(OUTER[0],OUTER[1],OUTER[2],OUTER[3],17.3,18.7).cut(rect(*POCKET,17.2,18.8))
# Open both ends across the central width for the optical head and bare header.
keeper=keeper.cut(rect(BX0+.6,BX1-.6,BY1-.3,OUTER[3]+.1,17.2,18.8))
for xa,xb in [(POCKET[0],BX0+.6),(BX1-.6,POCKET[1])]:
 for ya,yb in cornerY:keeper=keeper.fuse(rect(xa,xb,ya,yb,17.3,18.7))
SENSOR_SCREWS=[(-17,-14),(17,-14),(-14.2,17),(14.2,17)]
for x,y in SENSOR_SCREWS:
 ya,yb=(-14.8,-11.4) if y<0 else (15.8,18.2)
 dock=dock.fuse(cyl(2.4,x,y,13.284,17.3)).cut(cyl(.85,x,y,14.4,17.4))
 keeper=keeper.fuse(cyl(2.4,x,y,17.3,18.7)).fuse(rect(*sorted((x,OUTER[0] if x<0 else OUTER[1])),ya,yb,17.3,18.7)).cut(cyl(1.2,x,y,17.2,18.8))
# Open M5 support beams; front/back crossbars avoid the adjustment block.
deck=rect(-12,-7.5,-17,29,DECK_BOTTOM,DECK_TOP).fuse(rect(7.5,12,-17,29,DECK_BOTTOM,DECK_TOP))
for ya,yb in [(-17,-13)]:deck=deck.fuse(rect(-12,12,ya,yb,DECK_BOTTOM,DECK_TOP))
for x,y in M5SCREWS:deck=deck.fuse(cyl(2.5,x,y,DECK_BOTTOM,MOUNT_FACE)).cut(cyl(1.2,x,y,DECK_BOTTOM-.1,MOUNT_FACE+.1))
for x in [-8.8,8.8]:
 for y in [-3.5,13.5]:keeper=keeper.fuse(cyl(1.7,x,y,18.7,DECK_TOP))
keeper=keeper.fuse(deck)
# M2 heads/tools pass through the lower plate while this top module is off the base.
for x,y in M5SCREWS:keeper=keeper.cut(cyl(2.2,x,y,17.2,DECK_BOTTOM-.01))
for x,y in CENTERS:
 dock=dock.cut(cyl(1.7,x,y,13.1,15.1)).cut(cyl(3.2,x,y,14.684,20))
 keeper=keeper.cut(cyl(3.2,x,y,17.2,20))
dock=dock.clean();keeper=keeper.clean()
parts={'01_TCRT_attachment_port':base,'03_TCRT_sensor_cradle':dock,'04_TCRT_M5_top_dock':keeper}
meta={'01_TCRT_attachment_port':('#C13C47',[0,-90,0],'Launcher attachment','Original-scale launcher attachment; upper lens recess fits old TCRT pair.'),'03_TCRT_sensor_cradle':('#417767',[0,-90,0],'Sensor/device dock','Measured old-sensor corner seats and original clip keepers; open service from above.'),'04_TCRT_M5_top_dock':('#D0A96A',[180,0,0],'Sensor keeper','Removable M5 support and four-corner PCB keeper with four M2x4 screws; 0.2 mm PCB vertical play.')}
M=json.loads((S/'assembly_manifest.json').read_text());E={e['name']:e for e in M['parts']};manifest={'version':'0.19','variant':'OLD TCRT5000 + top-mounted M5StickS3','units':'mm','parts':[]};report={'cad':{},'mesh':{},'source_sha256':{},'nominal_collisions':[],'protected_v017_packages_sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [R/'releases/LaunchLab_v017_OPEN_STACK_package.zip',R/'releases/LaunchLab_v017_COMPLETE_FIRST_BUILD_package.zip']}}
# Reuse the validated single-solid/export routine, without executing older builders.
for n in ast.parse((R/'scripts/build_low_stack_v018.py').read_text()).body:
 if isinstance(n,ast.FunctionDef) and n.name=='export':exec(ast.unparse(n).replace('LaunchLab v0.18','LaunchLab v0.19'))
for n in ['02_latch_LEFT','02_latch_RIGHT']:
 for d,ext in [('step','.step'),('preview','.stl'),('stl','.stl')]:shutil.copy2(S/d/(n+ext),O/d/(n+ext))
 manifest['parts'].append({**E[n],'quantity':1})
for n,s in parts.items():export(n,s,*meta[n]);manifest['parts'][-1]['quantity']=1
seatfit=dock.intersect(rect(-19.5,19.5,-16.5,OUTER[3]+.1,13.284,17.3)).clean()
export('11_TCRT_SEAT_FIT',seatfit,'#417767',[0,0,0],'Fit coupon','Actual PCB seat/pilots; use with 12 keeper coupon',d='extras')
keeperfit=keeper.intersect(rect(-25,25,-20,25,17.3,18.7)).clean()
export('12_TCRT_KEEPER_FIT',keeperfit,'#D0A96A',[180,0,0],'Fit coupon','Exact lower keeper frame, without elevated M5 beams',d='extras')
mountfit=keeper.intersect(rect(-12,12,-18,-11,DECK_BOTTOM,MOUNT_FACE)).clean()
export('13_M5_MOUNT_FIT',mountfit,'#417767',[0,0,0],'Fit coupon','M5 front brass mounts and stepped face',d='extras')
vendor=trimesh.load(S/'references/StickS3_VENDOR_ASSEMBLY_AND_EXPLODED.stl',force='mesh');vs=[s for s in vendor.split(only_watertight=False) if s.bounds[1,0]<25];assert len(vs)==3
actual=trimesh.util.concatenate(vs);actual.apply_translation([-12,-18.05879,37.97736397]);assert actual.is_watertight
# Four bare corner contact lands are the only exclusions from the broad top solder allowance.
topsolder=rect(BX0,BX1,BY0,BY1,PCB_TOP,PCB_TOP+2)
for xa,xb in [(BX0,BX0+.65),(BX1-.65,BX1)]:
 for ya,yb in cornerY:topsolder=topsolder.cut(rect(xa,xb,ya-.05,yb+.05,17,19.2))
liner=cq.Compound.makeCompound([rect(-12,-7.5,-11,29,DECK_TOP,M5BACK),rect(7.5,12,-11,29,DECK_TOP,M5BACK)])
refs={
 'REF_M5_OFFICIAL_GEOMETRY':(actual,'electronics','#858F9E','Manufacturer assembled shell, Grove/USB -Y, Hat +Y; lowest back Z23.9, top38.9.'),
 'REF_M5_SOFT_LINER':(solidmesh(liner),'liner','#59646E','0.3 mm soft liner on the long back beams.'),
 'REF_TCRT_PCB_MEASURED':(bm(*BOARD),'electronics','#365D9D','OLD TCRT5000/LM393 blue module. User PCB31x13x1, not QRE1113.'),
 'REF_TCRT_HEAD_AND_LEGS':(bm(X-5,X+5,Y-3,Y+3,6.6,PCB_BOTTOM),'electronics','#48525E','10x6 envelope, 9.5 mm PCB-face to housing lens-side datum; lateral registration provisional.'),
 'REF_TCRT_LENS_PAIR':(bm(X-3.5,X+3.5,Y-3,Y+3,4.1,6.6),'electronics','#344B6A','7x6 lens-pair envelope,2.5 projection included in total12 from PCB face.'),
 'REF_TCRT_POT':(bm(X-.8,X+6.2,BY1-19,BY1-12,PCB_TOP,POT_TOP),'electronics','#457EC0','7x7x6 adjustment block on opposite PCB face;0.3 long-edge inset and12mm from header edge interpreted as in priorCAD.'),
 'REF_TCRT_HEADER':(bm(X-5,X+5,BY1-2,BY1+6,PCB_TOP,PCB_TOP+4),'electronics','#AAB1BA','User bare right-angle header:6 past edge,4 high.10x8 lateral footprint is a priorCAD assumption.'),
 'REF_TCRT_UNDERSIDE_SOLDER':(bm(X-5.6,X+5.6,BY0,BY1,PCB_BOTTOM-2,PCB_BOTTOM),'clearance','#C68A60','Conservative2mm underside allowance except outer edge seats.'),
 'REF_TCRT_TOP_SOLDER':(solidmesh(topsolder),'clearance','#C68A60','Conservative2mm top allowance except four corner lands visible in photos; actual copper/solder contact must be checked.'),
 'REF_SENSOR_SOCKET_ALLOWANCE':(bm(X-5.2,X+5.2,BY1+.5,BY1+19,PCB_TOP,PCB_TOP+6),'clearance','#CE8459','Same conservative18.5mm socket allowance as earlierM5/TCRT design; actual housing unmeasured. Rear stays open.'),
 'REF_HAT_PLUG_ALLOWANCE':(bm(-10.2,7.6,30,38,28.83,31.43),'clearance','#CE8459','Provisional8mm Hat connection at same end as sensor pins; actual plug/bends unmeasured.'),
 'REF_WIRE_ROUTE_ALLOWANCE':(trimesh.util.concatenate([bm(X-1.5,X+1.5,32,38.2,18.1,21.1),bm(X-1.5,X+1.5,36.5,38.2,21.1,31.43)]),'clearance','#D29243','Provisional short rear loop;3-wire analog harness, both connectors at+Y. No firmware change.'),
 'REF_M5_SCREEN_VISUAL_ONLY':(bm(-8,8,1,25,37.92,37.96),'visual','#111B24','Illustrative display face, not fit geometry.')}
for i,(x,y) in enumerate(CENTERS,1):refs[f'REF_M3x8_MOUNT_{i}']=(solidmesh(cyl(1.5,x,y,6.684,14.684).fuse(cyl(2.84,x,y,14.684,17.684))),'fasteners','#AAB1BA','M3x8DIN912 mount screws;6.6mm nominal engagement in original posts.')
for i,(x,y) in enumerate(M5SCREWS,1):refs[f'REF_M2x6_DEVICE_{i}']=(solidmesh(cyl(1,x,y,DECK_BOTTOM,DECK_BOTTOM+6).fuse(cyl(1.9,x,y,DECK_BOTTOM-1.4,DECK_BOTTOM))),'fasteners','#AAB1BA','M2x6 underside device mount;1.7mm nominal insertion. Attach before lowering dock onto base.')
for i,(x,y) in enumerate(SENSOR_SCREWS,1):refs[f'REF_M2x4_SENSOR_{i}']=(solidmesh(cyl(1,x,y,14.7,18.7).fuse(cyl(1.9,x,y,18.7,20.1))),'fasteners','#AAB1BA','M2x4 top-dock screws, 2.6 mm printed pilot engagement; top module lifts for sensor service.')
for n,(m,g,c,d) in refs.items():
 m.export(O/'preview'/f'{n}.stl');manifest['parts'].append({'name':n,'filename':f'preview/{n}.stl','group':g,'color':c,'reference':True,'printable':False,'description':d,'source':'User measurement / intact vendor M5 reference / explicit provisional allowance'})
for n,a in parts.items():
 for t,b in parts.items():
  if n<t and a.intersect(b).Volume()>.005:report['nominal_collisions'].append([n,t,a.intersect(b).Volume()])
assert not report['nominal_collisions'],report['nominal_collisions']
for p in [R/'reference files/TCRT5000_user_measurements_2026-09-21.md',S/'step/01_attachment_port.step',S/'references/StickS3_VENDOR_ASSEMBLY_AND_EXPLODED.stl',S/'stl/02_latch_LEFT.stl',S/'stl/02_latch_RIGHT.stl']:report['source_sha256'][str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
params={'version':'0.19','variant':'OLD TCRT5000/LM393, exposed M5StickS3 on top','architecture':'Original-scale launcher port, open measured-sensor cradle and removable top M5 dock with integrated corner keeper','sensor_identity':'Blue TCRT5000/LM393 module in IMG_7445–7448; OLD sensor, not QRE1113','measurement_source':'references/TCRT5000_user_measurements_2026-09-21.md','PCB_box_mm':BOARD,'sensor_PCB_mm':[31,13,1],'head_total_projection_from_PCB_mm':12,'lens_pair_mm':[7,6],'lens_projection_from_housing_mm':2.5,'pot_mm':[7,7,6],'sensor_total_component_thickness_mm':19,'PCB_xy_clearance_mm':.3,'PCB_vertical_capture_play_mm':.2,'minimum_cheek_wall_mm':1.3,'M5_back_z_mm':M5BACK,'M5_max_z_mm':M5TOP,'M5_mount_face_z_mm':MOUNT_FACE,'M5_screw_centres_mm':M5SCREWS,'sensor_keeper_screw_centres_mm':SENSOR_SCREWS,'mount_screw_centres_mm':CENTERS,'deck_z_mm':[DECK_BOTTOM,DECK_TOP],'device_Y_mm':[-18,30],'M5_orientation':'Grove/USB -Y, Hat +Y; sensor header+Y','core_footprint_mm':[43.146,48.],'launcher_top_z_mm':3.78,'optical_face_z_mm':4.1,'sensor_center_xy_mm':[X,Y],'height_above_launcher_mm':35.12,'pot_to_M5_gap_mm':.8,'mount_screw_head_to_deck_gap_mm':3.916,'sensor_keeper_screw_head_to_deck_gap_mm':1.5,'provisional_connector_extent_Y_mm':[-18,38.2],'core_with_provisional_harness_footprint_mm':[43.146,56.2],'clip_span_mm':59.777393,'assembly_printed_pieces':5,'replacement_printed_pieces':3,'fasteners':{'mount':'4 x M3x8 DIN912','device':'2 x M2x6 pan head','top_dock':'4 x M2x4 pan head','mount_thread_engagement_mm':6.6,'device_nominal_insert_engagement_mm':1.7,'sensor_keeper_thread_engagement_mm':2.6},'wiring':{'VCC':'Hat3V3_L2','GND':'HatGND','AO':'HatG1, analog input','DO':'Unused','Grove':'Unused electrically and mechanically'},'comparison_v015':{'old_case_length_mm':72.5,'new_core_length_mm':48,'shorter_mm':24.5,'length_reduction_percent':100*24.5/72.5,'old_frame_top_z_mm':41.6,'new_device_top_z_mm':38.9,'lower_mm':2.7,'note':'New sensor mount honors recorded12mm projection; older v0.15 CAD used10.5mm between PCB face and lens tips.'},'limits':['Actual sensor housing lateral registration, module component positions,4bare PCB corner lands,plug envelope and wire bends require fit check.','No whole-launcher registration or physical strength/retention/optical/RPM proof.','The7x6lens-pair envelope may be partially obscured by the real launcher aperture; no actual launcher modification or optical success is claimed.','M5 brass thread is user-confirmedM2;1.7mm insert depth and factory mount-face contact are nominal until dry fit.','The sensor 12 mm projection is taken from the measurement record; prior10.5mm CAD pose is corrected rather than silently reused.','v0.17 complete first-build package remains unchanged. This is a separateOLD-sensor prototype; no printer dispatch,purchase or firmware change.']}
for n in ['parameters','assembly_manifest']:(O/(n+'.json')).write_text(json.dumps(params if n=='parameters' else manifest,indent=2))
(O/'reports/cad_validation.json').write_text(json.dumps(report,indent=2));cq.exporters.export(cq.Compound.makeCompound(list(parts.values())),str(O/'LaunchLab_v019_TCRT_open_stack_assembly.step'))
for p in ['LICENSE.txt','references/K150-sticks3-dimensions.pdf','references/StickS3_VENDOR_ASSEMBLY_AND_EXPLODED.stl']:shutil.copy2(S/p,O/p)
shutil.copy2(R/'reference files/TCRT5000_user_measurements_2026-09-21.md',O/'references/TCRT5000_user_measurements_2026-09-21.md')
for n in ['IMG_7445.jpeg','IMG_7447.jpeg','IMG_7448.jpeg']:shutil.copy2(Path('/Users/mingj/Downloads')/n,O/'references'/n)
shutil.copy2(__file__,O/'provenance'/Path(__file__).name)
print('CAD_COMPLETE',params['core_footprint_mm'],params['M5_max_z_mm'],'OLD TCRT5000',flush=True)
