"""Separate minimal QRE holder. Preserves source launcher contact and optical datum."""
from pathlib import Path
import ast, hashlib, json, shutil
from zipfile import ZipFile
import cadquery as cq
import numpy as np
import trimesh
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib

R=Path(__file__).resolve().parents[1]
S=R/'releases/LaunchLab_v021_native_grip_M5'
O=R/'releases/LaunchLab_v032_balanced_QRE'
assert not (O/'SHA256SUMS.txt').exists(), 'Frozen release cannot be changed'
for d in ['step','preview','stl','extras','reports','renders','references','provenance','bambu']:
    (O/d).mkdir(parents=True,exist_ok=True)
for node in ast.parse((R/'scripts/build_compact_v010.py').read_text()).body:
    if isinstance(node,ast.FunctionDef) and node.name in ['bb','repair_collinear_boundary']:
        exec(compile(ast.Module(body=[node],type_ignores=[]),'helpers','exec'))
def box(x0,x1,y0,y1,z0,z1): return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,cq.Vector(x0,y0,z0))
def cyl(r,x,y,z0,z1): return cq.Solid.makeCylinder(r,z1-z0,cq.Vector(x,y,z0))
def load(p): return cq.importers.importStep(str(p)).val()
def mesh(s):
    v,f=s.tessellate(.025,.08)
    m=trimesh.Trimesh([p.toTuple() for p in v],f,process=True)
    m.merge_vertices(digits_vertex=5);m.update_faces(m.unique_faces());m.update_faces(m.nondegenerate_faces())
    m.remove_unreferenced_vertices();m=repair_collinear_boundary(m)
    assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
    return m

X=.1418;Y=-7.8658;ZSEAT=6.4;ZPCB=8.1
x0,x1=X-4.5,X+4.5;y0,y1=Y-6.35,Y+7.65
CLAMPY=y1-.45;SENSOR_AXES=[(x0-2.2,CLAMPY),(x1+2.2,CLAMPY)]
CLIP_AXES=[(-13.2,0),(13.2,0)];CAP_BOTTOM=11.484;CAP_TOP=13.284
source_checks={}
for dirname in ['LaunchLab_v025_minimal_QRE','LaunchLab_v031_vertical_QRE']:
    src=R/'releases'/dirname
    differences=[]
    for line in (src/'SHA256SUMS.txt').read_text().splitlines():
        h,n=line.split('  ',1)
        actual=hashlib.sha256((src/n).read_bytes()).hexdigest()
        if actual!=h:
            assert dirname=='LaunchLab_v031_vertical_QRE' and n=='bambu/LaunchLab_v031_P1S_PLA_QRE_NO_SUPPORT.3mf',(dirname,n)
            with ZipFile(R/'releases/LaunchLab_v031_VERTICAL_QRE_package.zip') as z:
                assert hashlib.sha256(z.read(dirname+'/'+n)).hexdigest()==h
            differences.append(dict(file=n,archived_sha256=h,current_sha256=actual,reason='Slicer project resaved; all CAD, STL and parameters still match frozen source'))
    source_checks[dirname]=dict(CAD_and_parameters_match_frozen=True,resaved_slicer_projects=differences)
previous=R/'releases/LaunchLab_v031_vertical_QRE'
oldP=json.loads((previous/'parameters.json').read_text())
CONTACT=oldP['keeper_flat_contact_box_mm'];CLAMPY=(CONTACT[2]+CONTACT[3])/2
SENSOR_AXES=[(x0-2.2,CLAMPY),(x1+2.2,CLAMPY)]
old=load(S/'step/05_QRE_attachment_port.step')
native=load(R/'source/LaunchLab_v02/step/01_native_port_UNSCALED.step')
# The exact entire native underside is kept, not a guessed launcher proxy.
# Keep the hinge beds at full native height; delete electronics frame/posts above the low floor.
mask=box(-40,40,-25,25,-20,6.4)
for lo,hi in [(-35,-16),(16,35)]: mask=mask.fuse(box(lo,hi,-6,6,-20,13.284))
base=old.intersect(mask)
# Cap the central nonfunctional openings and shallow grooves at the existing
# Z6.4 main floor. Capture the actual source section outline, without its inner
# openings; all additions begin at Z4.2 so the launcher contacts remain intact.
floor_source=load(R/'releases/LaunchLab_v025_minimal_QRE/step/01_QRE_minimal_port.step')
section=floor_source.intersect(cq.Face.makePlane(100,100,cq.Vector(0,0,4.2),cq.Vector(0,0,1)))
section_face=max(section.Faces(),key=lambda f:f.Area())
floor_fill=cq.Solid.extrudeLinear(section_face.outerWire(),[],cq.Vector(0,0,2.2))
base=base.fuse(floor_fill)
# Sensor component relief is the only remaining central recess.
base=base.cut(box(x0+.65,x1-.65,y0-.1,y1+.7,4.5,ZSEAT+.01))
base=base.cut(box(X-1.5,X+1.5,Y-1.85,Y+1.85,4.2,ZSEAT+.01))
# Rebuild only the shallow board edge seat; lens, resistors and pin tails have open relief.
seat=box(x0-1.1,x1+1.1,y0-.8,y1+.6,5,8.4)
seat=seat.cut(box(x0-.12,x1+.12,y0-.12,y1+.12,ZSEAT,10))
seat=seat.cut(box(x0+.65,x1-.65,y0-.1,y1+.7,4.5,ZSEAT+.01))
seat=seat.cut(box(x0-.13,x1+.13,y0-.9,y0+2.5,5,10))
for a,b in [(x0-.30,x0+.65),(x1-.65,x1+.30)]:
    for c,d in [(Y-.7,Y+.7),(y1-1.25,y1+.12)]: seat=seat.fuse(box(a,b,c,d,5,ZSEAT))
# Raised transverse ties are replaced by the flat floor below the new bosses.
base=base.fuse(seat)
base=base.cut(box(X-3.95,X+3.95,Y-5.08-1.45,Y-5.08+1.45,4.2,ZSEAT))
for a,b in [(x0-1.1,x0+.55),(x1-.55,x1+1.1)]:
    base=base.fuse(box(a,b,y0-.8,y0-.12,ZSEAT,8.4))
for x,y in SENSOR_AXES:
    base=base.fuse(cyl(2,x,y,5,7.9)).cut(cyl(.85,x,y,5,8))
    # A 0.2mm gap under the keeper ears permits clamp preload before the hard stop.
    base=base.cut(cyl(2.15,x,y,7.9,11))
base=base.cut(box(x0-.85,x1+.85,CLAMPY-.7,CLAMPY+.7,8.1,11))
# Only two inward bosses hold the slim clip retainer. No changes inside hinge beds.
for x,y in CLIP_AXES:
    base=base.fuse(cyl(2.4,x,y,5.6,CAP_BOTTOM))
    base=base.cut(cyl(.85,x,y,8,CAP_BOTTOM+.1))
base=base.clean()

# A small U instead of the previous four-post rectangular M5 support frame.
# Preserve both old hinge keeper solids exactly in their functional region.
oldcap=load(S/'step/07_QRE_clip_retainer.step')
caps=[]
for side,(x,y) in zip([-1,1],CLIP_AXES):
    lo,hi=sorted([side*15,side*35])
    cap=oldcap.intersect(box(lo,hi,-3.4,3.4,10.8,CAP_TOP))
    cap=cap.fuse(cyl(2.7,x,y,CAP_BOTTOM,CAP_TOP))
    lo,hi=sorted([side*13.2,side*16.3])
    cap=cap.fuse(box(lo,hi,-2.4,3.4,12.1,CAP_TOP))
    caps.append(cap)
retainer=caps[0].fuse(caps[1]).fuse(box(-14.2,14.2,2.4,4.2,12.1,CAP_TOP))
for x,y in CLIP_AXES:
    retainer=retainer.cut(cyl(1.15,x,y,10,CAP_TOP+.1))
    retainer=retainer.cut(cq.Solid.makeCone(1.15,2.25,1.1,cq.Vector(x,y,CAP_TOP-1.1)))
# Thicken the joining crossbar by 0.6mm on top; the source latch keeper
# undersides and countersunk screw seats stay at their original heights.
retainer=retainer.fuse(box(-14.2,14.2,2.4,4.2,CAP_TOP,CAP_TOP+.6)).clean()

# Central screw rings balance the pressure along the exposed board. Their
# forward wings meet the same straight bed edge as v031, so the plate still
# prints upright with supports disabled.
contact=CONTACT
keeper=box(*contact);ramp_end=contact[3]+.8;bed_y=oldP['keeper_flat_bed_edge_y_mm']
points=[cq.Vector(contact[0],contact[3],8.1),cq.Vector(contact[0],ramp_end,8.9),
        cq.Vector(contact[0],ramp_end,9.7),cq.Vector(contact[0],contact[3],9.3)]
keeper=keeper.fuse(cq.Solid.extrudeLinear(cq.Wire.makePolygon(points,close=True),[],cq.Vector(contact[1]-contact[0],0,0)))
keeper=keeper.fuse(box(SENSOR_AXES[0][0],SENSOR_AXES[1][0],ramp_end-.01,bed_y,8.9,9.7))
for a,b in [(SENSOR_AXES[0][0],contact[0]+.4),(contact[1]-.4,SENSOR_AXES[1][0])]:
    keeper=keeper.fuse(box(a,b,CLAMPY-.6,CLAMPY+.6,8.5,10.1))
for x,y in SENSOR_AXES:
    keeper=keeper.fuse(cyl(2,x,y,8.5,10.1)).fuse(box(x-2,x+2,y,bed_y,8.9,10.1))
    keeper=keeper.cut(cyl(1.1,x,y,8.0,10.2))
keeper=keeper.clean()
# Keep the board seat fixed while providing clearance below the center rings.
base=base.cut(retainer).cut(keeper.translate((0,0,-.4))).clean()
parts={'01_QRE_minimal_port':base,'02_QRE_clip_keeper':retainer,'03_QRE_pressure_bar':keeper}
metadata={
 '01_QRE_minimal_port':('#48545D',[0,-90,0],'Flat main floor, sensor-only component recess and centered clamp screw bosses; native underside and hinge beds unchanged.'),
 '02_QRE_clip_keeper':('#398B83',[0,0,0],'U retains both original launcher latches; crossbar thickened upward by 0.6mm, original hinge keeper faces and screw seats retained.'),
 '03_QRE_pressure_bar':('#E5AB62',[-90,0,0],'Center-positioned M2x4 screws press the broad flat face onto the PCB; straight edge for upright printing.')}
manifest={'version':'0.32','units':'mm','assemblies':'Sensor independent of unchanged v0.24 M5 platform','parts':[]}
report={'status':'BUILDING','cad':{},'mesh':{},'sources':{},'source_release_checks':source_checks}
def export(n,s,color,rot,description,extra=False):
    assert s.isValid() and len(s.Solids())==1,(n,s.isValid(),len(s.Solids()))
    cq.exporters.export(s,str(O/('extras' if extra else 'step')/(n+'.step')))
    s.exportBrep(str(O/('extras' if extra else 'step')/(n+'.brep')))
    m=mesh(s)
    if not extra:m.export(O/'preview'/(n+'.stl'))
    pm=m.copy()
    for ax,a in zip([(1,0,0),(0,1,0),(0,0,1)],rot):
        if a:pm.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(a),ax))
    shift=np.r_[-pm.bounds[:,:2].mean(axis=0),-pm.bounds[0,2]];pm.apply_translation(shift)
    pm.export(O/('extras' if extra else 'stl')/(n+'.stl'))
    report['cad'][n]={'volume_mm3':s.Volume(),'bounds_mm':bb(s),'solids':1}
    report['mesh'][n]={'volume_mm3':m.volume,'watertight':True,'components':1,'bed_min_z_mm':pm.bounds[0,2]}
    if not extra:manifest['parts'].append(dict(name=n,filename=f'preview/{n}.stl',color=color,group='QRE',reference=False,printable=True,print_rotation_deg=rot,print_translation_mm=shift.tolist(),description=description,source='v0.32 minimal QRE'))
    print('EXPORTED',n,round(s.Volume(),2),flush=True)
for n,s in parts.items():export(n,s,*metadata[n])
E={e['name']:e for e in json.loads((S/'assembly_manifest.json').read_text())['parts']}
for n in ['08_QRE_latch_LEFT','09_QRE_latch_RIGHT']:
    for d,ext in [('preview','.stl'),('stl','.stl'),('step','.step')]:shutil.copy2(S/d/(n+ext),O/d/(n+ext))
    e=dict(E[n],description='Existing latch, byte identical; reuse the printed latch.',source='v0.21 unchanged launcher latch')
    manifest['parts'].append(e)
for n in ['REF_QRE_red_PCB','REF_QRE_downward_optics','REF_Underside_resistor_-1.524','REF_Underside_resistor_1.524']+[f'REF_QRE_existing_upright_plug_{i}' for i in range(3)]:
    shutil.copy2(S/E[n]['filename'],O/'preview'/(n+'.stl'))
    manifest['parts'].append(dict(E[n],filename=f'preview/{n}.stl'))
def reference(n,s,desc):
    mesh(s).export(O/'preview'/(n+'.stl'))
    manifest['parts'].append(dict(name=n,filename=f'preview/{n}.stl',color='#B2BBC6',group='hardware',reference=True,printable=False,description=desc,source='Nominal screw envelope; verify purchased head dimensions'))
for i,(x,y) in enumerate(CLIP_AXES,1):
    top=CAP_TOP-.1
    s=cyl(1,x,y,top-5,top-1).fuse(cq.Solid.makeCone(1,2,1,cq.Vector(x,y,top-1)))
    reference(f'REF_M2x5_CLIP_{i}',s,'M2x5 countersunk: modeled 4mm head; 3.3mm nominal pilot engagement.')
for i,(x,y) in enumerate(SENSOR_AXES,1):
    reference(f'REF_M2x4_SENSOR_{i}',cyl(1,x,y,6.1,10.1).fuse(cyl(1.9,x,y,10.1,11.5)),'M2x4 pan head: nominal 1.8mm pilot engagement, centered pressure on the PCB; actual grip untested.')
coupon=base.intersect(box(x0-4.4,x1+4.4,y0-.8,y1+2.6,4.2,9.4)).clean()
export('11_QRE_POCKET_FIT',coupon,'#48545D',[0,0,0],'Exact pocket/lands/header relief, cropped from the new port.',True)
for n,s in parts.items():
    if n!='01_QRE_minimal_port':continue
    for label,roi in [('underside',box(-35,35,-20,20,-20,4.1999)),('hinge_LEFT',box(-35,-16,-6,6,-20,13.284)),('hinge_RIGHT',box(16,35,-6,6,-20,13.284))]:
        a=native.intersect(roi);b=s.intersect(roi)
        d=a.cut(b).Volume()+b.cut(a).Volume();assert d<.001,(label,d)
        report[label+'_symmetric_difference_mm3']=d
oldvol=sum(load(previous/'step'/(n+'.step')).Volume() for n in ['01_QRE_minimal_port','02_QRE_clip_keeper','03_QRE_pressure_bar'])
newvol=sum(s.Volume() for s in parts.values())
params=dict(version='0.32',units='mm',architecture='Balanced mid-plane PCB pressure plate, flattened base and thicker latch crossbar; separate unchanged M5 mount',
    optical_center_xy_mm=[X,Y],optical_face_z_mm=4.1,launcher_top_z_mm=3.78,
    PCB_box_mm=[x0,x1,y0,y1,ZSEAT,ZPCB],PCB_nominal_mm=[14,9,1.7],PCB_side_clearance_mm=.12,
    PCB_thickness_range_for_keeper_mm=[1.7,2.0],PCB_reference='Current v0.20/v0.21 measured-photo envelope: 1.7mm PCB plus 2.3mm sensor. Keeper can rise 0.3mm for the earlier 2mm PCB measurement; actual optical projection requires physical verification.',
    keeper_preload_gap_mm=.6,keeper_edge_overlap_mm=None,header_tail_relief_floor_z_mm=4.2,
    clip_screw_axes_xy_mm=CLIP_AXES,sensor_screw_axes_xy_mm=SENSOR_AXES,
    fasteners={'clip_keeper':'2 x M2x5 countersunk (nominal 4mm head, 90deg)','sensor_keeper':'2 x M2x4 pan head','clip_engagement_mm':3.3,'sensor_engagement_mm':1.8},
    replacement_parts=list(parts),reuse=['08_QRE_latch_LEFT','09_QRE_latch_RIGHT','existing v0.24 M5 stepped platform'],
    comparison={'old_new_parts_volume_mm3':oldvol,'new_parts_volume_mm3':newvol,'material_reduction_percent':100*(1-newvol/oldvol),'old_keeper_top_z_mm':13.284,'new_keeper_top_z_mm':CAP_TOP+.6,'sensor_pocket_height_above_launcher_mm':9.3-3.78},
    limits=['Digital fit prototype. Printed fit, clamping force, latch retention, material strength and actual launch optical response remain unverified.','The native launcher underside, two hinge beds, latch meshes and optical datum are preserved at original scale.','Do not overtighten the PCB keeper; preload is a geometric allowance, not a tested spring or fatigue model.','Connector width, solder tails, flexible wire routing and purchased screw dimensions are provisional.','Separate QRE and M5 assemblies have no measured relative transform; side-by-side layout is not an installed pose.','No print dispatch.'])
params.update(keeper_flat_contact_box_mm=CONTACT,keeper_contact_step_down_mm=.4,keeper_tab_bottom_z_mm=8.5,
    keeper_tab_top_z_mm=10.1,keeper_body_thickness_mm=1.2,keeper_tab_thickness_mm=1.6,
    keeper_nominal_contact_z_mm=8.1,keeper_contact_footprint_mm2=(CONTACT[1]-CONTACT[0])*(CONTACT[3]-CONTACT[2]),
    dupont_clearance_mm=.3,keeper_bare_end_bevel_trim_mm=.4,keeper_underside_ramp_rise_mm=.8,keeper_underside_ramp_run_mm=.8,
    keeper_flat_bed_edge_y_mm=bed_y,keeper_front_bridge_bottom_z_mm=8.9,keeper_front_bridge_top_z_mm=9.7,
    keeper_print_orientation='Upright on straight bare-end edge; centered screw wings extend to the bed edge',
    keeper_print_height_mm=bed_y-CONTACT[2],keeper_print_layer_height_mm=.2,
    sensor_screw_position='Midpoint of flat exposed-PCB contact rectangle',sensor_screw_shift_y_mm=CLAMPY-oldP['sensor_screw_axes_xy_mm'][0][1],
    main_flat_floor_z_mm=6.4,flattening_patch_bottom_z_mm=4.2,clip_crossbar_added_thickness_mm=.6,
    clip_crossbar_thickness_mm=CAP_TOP+.6-12.1,clip_screw_seats_z_mm=CAP_TOP,
    positive_header_end_stops_mm=.55,
    physical_feedback='End-loaded pressure allowed PCB sliding; user requests centered screws, redesigned base, thicker latch crossbar and filled/smoothed extra openings',
    limits=['Digital checks do not establish physical retention, clamp force, print strength or optical sensing.',
            'Sensor seat, native launcher contacts and hinge beds remain unchanged; main floor above Z4.2 is intentionally filled and smoothed.',
            'Use all three v032 replacement parts together; centered screw positions do not match the old base.',
            'M2x4 nominal pilot engagement is 1.8mm for a 1.7mm PCB or 1.5mm for a 2mm PCB; actual printed grip needs inspection.',
            'The upright pressure plate has a narrow bed footprint and small horizontal hole bridges; adhesion/hole quality untested.',
            'No print dispatch.'])
pm=trimesh.load(O/'stl/03_QRE_pressure_bar.stl',force='mesh')
bed_faces=np.all(abs(pm.vertices[pm.faces][:,:,2])<.00001,axis=1)
params['keeper_bed_contact_area_mm2']=float(pm.area_faces[bed_faces].sum())
params['keeper_screw_front_hole_wall_mm']=bed_y-CLAMPY-1.1
floor_fill.exportStep(str(O/'references/REF_main_floor_fill.step'))
extra_opening=max(section_face.innerWires(),key=lambda w:w.Center().y)
extra_plug=cq.Solid.extrudeLinear(extra_opening,[],cq.Vector(0,0,2.2))
assert extra_plug.cut(base).Volume()<.00001
report['extra_trapezoid_closed_above_Z4p2_mm3']=extra_plug.Volume()
report['main_floor_patch_mm3']=floor_fill.Volume()
# The functional keeper regions at the two hinges are source-identical too.
for label,roi in [('clip_keeper_LEFT',box(-35,-15,-3.4,3.4,10.8,13.284)),('clip_keeper_RIGHT',box(15,35,-3.4,3.4,10.8,13.284))]:
    before=load(R/'releases/LaunchLab_v025_minimal_QRE/step/02_QRE_clip_keeper.step').intersect(roi)
    after=retainer.intersect(roi);d=before.cut(after).Volume()+after.cut(before).Volume();assert d<.001,(label,d)
    report[label+'_symmetric_difference_mm3']=d
(O/'parameters.json').write_text(json.dumps(params,indent=2))
(O/'assembly_manifest.json').write_text(json.dumps(manifest,indent=2))
report['status']='CAD_EXPORT_PASS'
for p in [S/'step/05_QRE_attachment_port.step',S/'step/07_QRE_clip_retainer.step',R/'source/LaunchLab_v02/step/01_native_port_UNSCALED.step',R/'releases/LaunchLab_v024_stepped_platform/SHA256SUMS.txt']:
    report['sources'][str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
(O/'reports/cad_validation.json').write_text(json.dumps(report,indent=2))
cq.exporters.export(cq.Compound.makeCompound([*parts.values(),*[load(O/'step'/(n+'.step')) for n in ['08_QRE_latch_LEFT','09_QRE_latch_RIGHT']]]),str(O/'LaunchLab_v032_balanced_QRE_assembly.step'))
shutil.copy2(R/'releases/LaunchLab_v020_crosswise_QRE/LICENSE.txt',O/'LICENSE.txt')
shutil.copy2(R/'releases/LaunchLab_v024_stepped_platform/references/QRE_BP_port_LICENSE.txt',O/'references/QRE_BP_port_LICENSE.txt')
shutil.copy2(__file__,O/'provenance'/Path(__file__).name)
print('V032_CAD_READY',params['comparison'],flush=True)
