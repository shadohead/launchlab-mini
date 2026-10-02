"""Independent exported-mesh clearance, capture, service and source preservation checks."""
from pathlib import Path
import itertools,json,hashlib
import cadquery as cq
import numpy as np
import trimesh
R=Path(__file__).resolve().parents[1];O=R/'releases/LaunchLab_v033_flush_QRE'
P=json.loads((O/'parameters.json').read_text());M=json.loads((O/'assembly_manifest.json').read_text())
E={e['name']:e for e in M['parts']};ms={n:trimesh.load(O/e['filename'],force='mesh') for n,e in E.items()}
B='01_QRE_minimal_port';C='02_QRE_clip_keeper';K='03_QRE_pressure_bar';PCB='REF_QRE_red_PCB'
rep={'status':'CHECKING','collisions':[],'checks':{},'limits':P['limits']}
def vol(a,b):
    if np.any(a.bounds[1]<=b.bounds[0]+1e-5) or np.any(b.bounds[1]<=a.bounds[0]+1e-5):return 0.
    r=trimesh.boolean.intersection([a,b],engine='manifold',check_volume=False)
    return abs(float(r.volume)) if len(r.faces) else 0.
def mv(m,d):o=m.copy();o.apply_translation(d);return o
def check(a,b,stage,**details):
    v=vol(a,b)
    if v>.015:rep['collisions'].append(dict(stage=stage,volume_mm3=v,**details))
    return v
def box(x0,x1,y0,y1,z0,z1):
    m=trimesh.creation.box([x1-x0,y1-y0,z1-z0]);m.apply_translation([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2]);return m
printed=[n for n,e in E.items() if e['printable']]
for n in printed:
    m=ms[n];p=trimesh.load(O/'stl'/(n+'.stl'),force='mesh')
    assert m.is_watertight and m.is_winding_consistent and len(m.split())==1,n
    assert p.is_watertight and p.is_winding_consistent and len(p.split())==1,n
    assert abs(p.bounds[0,2])<.001 and abs(p.volume-m.volume)<.005,n
    s=cq.importers.importStep(str(O/'step'/(n+'.step'))).val()
    assert s.isValid() and len(s.Solids())==1 and abs(s.Volume()-m.volume)/s.Volume()<.01,n
for a,b in itertools.combinations(printed,2):check(ms[a],ms[b],'assembled prints',part=a,target=b)
for a in printed:
    for b,e in E.items():
        if e['reference'] and e['group']!='hardware':check(ms[a],ms[b],'electronics clearance',part=a,target=b)
rep['checks']['all_printed_meshes']='Valid single CAD solids; watertight, consistent, single component meshes, scale and volumes preserved, on bed.'
for side,x,sign in [('RIGHT',17.628,-1),('LEFT',-17.6,1)]:
    n='09_QRE_latch_RIGHT' if side=='RIGHT' else '08_QRE_latch_LEFT'
    for deg in range(0,91,5):
        a=ms[n].copy();a.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(sign*deg),[0,1,0],point=[x,0,9.1]))
        for t in [B,C,K]+[k for k,e in E.items() if e['reference']]:check(a,ms[t],'latch rotation',side=side,degrees=deg,target=t)
    lift=vol(mv(ms[n],[0,0,.5]),ms[C]);assert lift>.1,(side,lift)
    rep['checks'][side+'_clip_lift_0p5mm_stop_volume_mm3']=lift
rep['checks']['latch_motion']='0..90 degrees in 5-degree steps; original source pivots. Rigid samples, no physical load proof.'
assert vol(mv(ms[PCB],[0,0,-.05]),ms[B])>.05
assert vol(mv(ms[PCB],[0,0,.05]),ms[K])>.05
rep['checks']['PCB_capture_probe_mm3']={
    'seat_down_0p05':vol(mv(ms[PCB],[0,0,-.05]),ms[B]),
    'keeper_up_0p05':vol(mv(ms[PCB],[0,0,.05]),ms[K])}
for name,d in [('left',[-.2,0,0]),('right',[.2,0,0]),('plug_end',[0,-.2,0]),('bare_end',[0,.2,0])]:
    v=vol(mv(ms[PCB],d),ms[B]);assert v>.01,(name,v)
    rep['checks']['PCB_capture_probe_mm3'][name+'_0p2']=v
rep['checks']['PCB_capture']='Original pocket stops and lower lands; continuous flat central pressure face up to Dupont housings, with a small bare-end bevel for the upright print; central face is 0.4mm below the screw-tab undersides.'
for n in [C,K]:
    for dz in [0,.1,.25,.5,1,2,4,8,16]:
        for t in [B]+[k for k,e in E.items() if e['reference'] and e['group']!='hardware']:
            check(mv(ms[n],[0,0,dz]),ms[t],'keeper top removal',part=n,target=t,dz=dz)
for n,e in E.items():
    if not e['reference'] or e['group']=='hardware':continue
    for dz in [0,.1,.25,.5,1,2,4,8,16]:check(mv(ms[n],[0,0,dz]),ms[B],'sensor top insertion after keeper removal',part=n,dz=dz)
rep['checks']['service']='Clip keeper and pressure bar can lift straight up; sensor/rigid plugs load vertically after pressure bar removal. M5 remains separate.'
thick=ms[PCB].copy();v=thick.vertices.copy();v[:,2]=5.4+(v[:,2]-5.4)*(2/1.7);thick.vertices=v
check(thick,ms[B],'2mm PCB width/thickness option')
check(thick,mv(ms[K],[0,0,.3]),'2mm PCB raised keeper')
rep['checks']['2mm_PCB_option']='Same lower seat, keeper lifted 0.3mm; nominal 1.5mm remaining M2x4 pilot engagement. Actual lens projection not inferred.'
x,y=P['optical_center_xy_mm'];beam=box(x-1.35,x+1.35,y-1.7,y+1.7,2.79,3.09)
for t in [B,C,K]:check(beam,ms[t],'clear optical window',target=t)
for dx in [-2.54,0,2.54]:
    t=trimesh.creation.cylinder(radius=.8,height=2,sections=48);t.apply_translation([x+dx,y-5.08,4.4])
    check(t,ms[B],'2mm provisional header solder tail',dx=dx)
for n,e in E.items():
    if e['group']!='hardware':continue
    for t in [C,K]:check(ms[n],ms[t],'screw head/shaft clears keeper',screw=n,target=t)
    if 'CLIP' in n:head=box(ms[n].bounds[0,0]-1,ms[n].bounds[1,0]+1,-3,3,11.484,14)
    else:head=box(ms[n].bounds[0,0]-1,ms[n].bounds[1,0]+1,ms[n].bounds[0,1]-1,ms[n].bounds[1,1]+1,6.9,11)
    actual_head=trimesh.boolean.intersection([ms[n],head],engine='manifold',check_volume=False)
    check(actual_head,ms[B],'screw upper region clears base',screw=n)
    center=ms[n].bounds.mean(axis=0)
    tool_bottom=float(ms[n].bounds[1,2])+.01;tool_top=40.
    tool=trimesh.creation.cylinder(radius=1.3,height=tool_top-tool_bottom,sections=48);tool.apply_translation([center[0],center[1],(tool_top+tool_bottom)/2])
    for t in printed+[k for k,e in E.items() if e['reference'] and e['group']!='hardware']:
        check(tool,ms[t],'top screwdriver access',screw=n,target=t)
rep['checks']['fasteners']='2 x M2x5 countersunk clip screws and 2 x M2x4 pan-head sensor screws; head clearance and top driver corridors pass. Pilot bite is intentional.'
for n in ['08_QRE_latch_LEFT','09_QRE_latch_RIGHT']:
    for d,ext in [('step','.step'),('stl','.stl'),('preview','.stl')]:assert (O/d/(n+ext)).read_bytes()==(R/'releases/LaunchLab_v021_native_grip_M5'/d/(n+ext)).read_bytes()
rep['checks']['original_latches_byte_identical']=True
from scipy.spatial import cKDTree
source=R/'releases/LaunchLab_v032_balanced_QRE'
for n,e in E.items():
    if not e['reference'] or e['group']=='hardware':continue
    before=trimesh.load(source/e['filename'],force='mesh');before.apply_translation((0,0,-1))
    assert max(cKDTree(before.vertices).query(ms[n].vertices)[0].max(),cKDTree(ms[n].vertices).query(before.vertices)[0].max())<.00001,n
rep['checks']['all_sensor_component_envelopes_shifted_down_exactly_1mm']=True
assert abs(ms[PCB].bounds[0,2]-5.4)<.00001
assert abs(ms['REF_QRE_downward_optics'].bounds[0,2]-3.1)<.00001
for n in [C,K,'08_QRE_latch_LEFT','09_QRE_latch_RIGHT']:
    assert (O/'stl'/(n+'.stl')).read_bytes()==(source/'stl'/(n+'.stl')).read_bytes(),n
rep['checks']['only_new_base_needs_printing']=True
rep['checks']['native_launcher_and_functional_hinge_regions']=json.loads((O/'reports/cad_validation.json').read_text())
assert abs(P['keeper_body_thickness_mm']-1.2)<1e-6 and abs(P['keeper_tab_thickness_mm']-1.6)<1e-6
assert P['keeper_contact_footprint_mm2']>90
assert vol(mv(ms[K],[0,0,-.2]),ms[B])<.015
contact=P['keeper_flat_contact_box_mm'];x0,x1,y0,y1,z0,z1=contact
k=cq.importers.importStep(str(O/'step'/(K+'.step'))).val()
slab=cq.Solid.makeBox(x1-x0,y1-y0,.01,cq.Vector(x0,y0,z0))
assert slab.cut(k).Volume()<.0001
area=vol(mv(ms[PCB],[0,0,.01]),ms[K])/.01
assert area>.8*P['keeper_contact_footprint_mm2'],area
plug_end=max(ms[n].bounds[1,1] for n in ms if n.startswith('REF_QRE_existing_upright_plug'))
assert abs(y0-plug_end-.3)<.00001
rep['checks']['flat_contact_area_mm2']=area
rep['checks']['flat_pressure_face']='Continuous rectangular underside up to modeled plugs; only 0.4mm of the bare end is beveled. Exact CAD slab coverage verified; PCB through-hole excluded from contact area.'
rep['checks']['Dupont_gap_mm']=y0-plug_end
rep['checks']['screw_tab_thickness_mm']=P['keeper_tab_thickness_mm']
assert abs(P['keeper_tab_bottom_z_mm']-P['keeper_nominal_contact_z_mm']-.4)<1e-6
assert abs(P['keeper_tab_bottom_z_mm']-6.9-.6)<1e-6
assert vol(mv(ms[K],[0,0,-.4]),ms[B])<.015
rep['checks']['central_step_down_mm']=.4
rep['checks']['tab_to_boss_gap_at_PCB_contact_mm']=.6
rep['checks']['preload_clearance_probe']='At 0.4mm additional downward rigid travel, the keeper remains clear of the base; board deformation and screw preload are untested.'
assert abs(P['keeper_underside_ramp_rise_mm']-P['keeper_underside_ramp_run_mm'])<1e-6
assert P['keeper_screw_front_hole_wall_mm']>=.7999
entry=E[K];assert entry['print_rotation_deg']==[-90,0,0]
p=trimesh.load(O/'stl'/(K+'.stl'),force='mesh')
expected=ms[K].copy();expected.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0]));expected.apply_translation(entry['print_translation_mm'])
from scipy.spatial import cKDTree
assert max(cKDTree(p.vertices).query(expected.vertices)[0].max(),cKDTree(expected.vertices).query(p.vertices)[0].max())<.0001
bed_faces=np.all(abs(p.vertices[p.faces][:,:,2])<.00001,axis=1)
area=float(p.area_faces[bed_faces].sum());assert area>17 and abs(area-P['keeper_bed_contact_area_mm2'])<.001
front=P['keeper_flat_bed_edge_y_mm'];ax=P['sensor_screw_axes_xy_mm']
bed_probe=cq.Solid.makeBox(ax[1][0]-ax[0][0]+4,.001,2.1,cq.Vector(ax[0][0]-2,front-.001,7.05)).intersect(k)
assert bed_probe.isValid() and len(bed_probe.Solids())==1
rep['checks']['upright_print_orientation']='Actual manufacturing STL rotated -90 degrees about X and placed on straight screw-end edge; all vertices independently matched to assembly STL.'
rep['checks']['continuous_flat_bed_edge']=dict(area_mm2=area,connected=True,height_mm=float(p.extents[2]),screw_hole_front_wall_mm=P['keeper_screw_front_hole_wall_mm'])
rep['checks']['underside_print_bevel']='45-degree ramp; central flat bearing face and screw-ring height difference retained.'
base=cq.importers.importStep(str(O/'step/01_QRE_minimal_port.step')).val()
cad=json.loads((O/'reports/cad_validation.json').read_text())
assert all(v<.001 for v in cad['preserved'].values())
oldcenter=cq.importers.importStep(str(O/'references/REF_OLD_center.step')).val().translate((0,0,-1))
newcenter=cq.importers.importStep(str(O/'references/REF_NEW_center.step')).val()
assert oldcenter.cut(newcenter).Volume()+newcenter.cut(oldcenter).Volume()<.001
assert newcenter.cut(base).Volume()<.001
assert abs(P['new_center_step_width_at_y0_mm']-(P['old_center_step_width_at_y0_mm']-1))<.00001
assert abs(P['central_platform_drop_mm']-1)<.00001
assert abs(P['central_step_trim_per_side_mm']-.5)<.00001
# Independent STEP readback of the new lower face and two trimmed side planes.
f=max((f for f in base.Faces() if abs(f.BoundingBox().zmin-2.78)<1e-5 and abs(f.BoundingBox().zmax-2.78)<1e-5),key=lambda f:f.Area())
xy=np.array([v.toTuple()[:2] for v in f.outerWire().Vertices()]);left=xy[xy[:,0]<-8]
b=P['central_left_boundary']
assert max(abs(left[:,0]-(b['slope_dx_dy']*left[:,1]+b['new_intercept_mm'])))<.00001
assert abs(xy[:,0].max()-P['central_right_boundary_mm'][1])<.00001
assert abs(P['sensor_screw_axes_xy_mm'][0][1]-(contact[2]+contact[3])/2)<1e-6
assert abs(P['clip_crossbar_thickness_mm']-1.784)<.00001
rep['checks']['center_step_dimension_readback']=dict(trim_each_side_mm=.5,platform_drop_mm=1,underside_z_mm=2.78,PCB_seat_z_mm=5.4,optical_face_z_mm=3.1,new_width_at_Y0_mm=P['new_center_step_width_at_y0_mm'],old_width_at_Y0_mm=P['old_center_step_width_at_y0_mm'])
rep['checks']['preserved_outer_mount_and_hinges']=cad['preserved']
rep['checks']['sensor_slot_width_mm']=9.24
rep['checks']['minimum_center_to_side_join_height_mm']=P['minimum_center_to_side_join_height_mm']
rep['checks']['launcher_fit_boundary']='No full measured launcher collision model; photo supports requested geometry change, installed clearance requires physical trial.'
rep['status']='PASS' if not rep['collisions'] else 'FAIL'
(O/'reports/fit_and_motion.json').write_text(json.dumps(rep,indent=2))
print('V033_CHECKS',rep['status'],'COLLISIONS',rep['collisions'][:12],flush=True)
assert not rep['collisions']
