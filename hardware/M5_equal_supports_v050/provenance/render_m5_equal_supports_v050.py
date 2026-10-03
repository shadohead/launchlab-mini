"""Render the actual revised carrier and compare the four support heights."""
from pathlib import Path
import ast,json,sys,bpy
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'inspection/M5_equal_supports_v050'
sys.path.insert(0,str(R/'scripts'))
from blender_helpers_v09 import import_mesh,collection,configure,audit,material,write_3mf
for node in ast.parse((R/'scripts/render_minimal_qre_v025.py').read_text()).body:
    if isinstance(node,ast.FunctionDef) and node.name=='label':exec(compile(ast.Module(body=[node],type_ignores=[]),'label','exec'))
assert not (O/'SHA256SUMS.txt').exists()
assert json.loads((O/'reports/cad_validation.json').read_text())['status']=='PASS'
M=json.loads((O/'assembly_manifest.json').read_text());P=json.loads((O/'parameters.json').read_text());NAME=M['parts'][0]['name']
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.name='01 EQUAL HEIGHT SUPPORTS'
ob=import_mesh(O/'preview'/(NAME+'.stl'),s,NAME,collection(s,'Actual printable carrier'),M['parts'][0])
ob['geometry_revision']='v050 two rear pads raised to 2.3 mm, matching screw posts'
ob.data.materials.append(material('#D7AB61'))
for f in ob.data.polygons:
    p=f.center*1000
    if 11.19<p.y<13.81 and p.z>-5.801 and (1.29<p.x<7.31 or 13.29<p.x<19.31):f.material_index=1
def setup(sc,d,target,scale):
    configure(sc,target,Vector(target)+Vector(d).normalized()*.35,scale)
    sc.render.resolution_x=1400;sc.render.resolution_y=1100;sc.cycles.samples=20
    sc['electronics']='M5StickS3 on separate carrier; device excluded from support inspection'
    sc['battery_allowance']='Factory integrated battery'
    sc['architecture']='v049 carrier with two support pads raised to screw post plane'
    sc['status']='Carrier geometry verified; physical M5 seating untested'
setup(s,(1,1,1.5),(.007,0,-.003),.085)
label(s,'Gold: support pads raised to match screw standoffs',-.035,.027,.0019)
label(s,'Both support pads: 2.3 mm / increase: 1.8 mm',-.035,-.027,.0019)
side=bpy.data.scenes.new('02 SAME HEIGHT PLANE');c=collection(side,'Actual carrier side view');a=ob.copy();c.objects.link(a)
setup(side,(1,0,.14),(.0103,0,-.0035),.070)
label(side,'Support pads and screw posts share the same top plane',-.029,.022,.0015)
label(side,'2.3 mm above deck / screw recesses retained',-.029,-.022,.0017)
close=bpy.data.scenes.new('03 SUPPORT CLOSEUP');c=collection(close,'Actual raised supports');a=ob.copy();c.objects.link(a)
setup(close,(1,1,1.2),(.0103,.0125,-.0045),.033)
label(close,'Two raised pads / same rounded footprint',-.013,.010,.0008)
label(close,'6 x 2.6 mm pads / height: 2.3 mm',-.013,-.010,.0008)
check=audit(ob);assert check['components']==1 and check['nonmanifold_edges']==check['inconsistent_winding_edges']==0
(O/'reports/blender_audit.json').write_text(json.dumps(check,indent=2))
pr=bpy.data.scenes.new('04 PRINT POSE');po=import_mesh(O/'stl'/(NAME+'.stl'),pr,NAME+'_PRINT',collection(pr,'Only printable mesh'),M['parts'][0])
setup(pr,(1,1,1.5),(0,0,.0175),.084)
write_3mf(O/'M5_equal_supports_v050_UNSLICED.3mf',[po],description='One M5 carrier, two opposite-end support pads raised to 2.3 mm matching screw standoffs. v049 center ramp and recessed screw heads retained. Unsliced side print orientation. Physical fit unverified. Migbello / Thingiverse 6856080 / CC BY-SA (version unspecified).')
bpy.data.texts.new('README - equal-height supports').write((O/'README.md').read_text())
bpy.context.window.scene=s;bpy.context.preferences.filepaths.save_version=0
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.clip_start=.0001;sp.overlay.show_floor=False;sp.overlay.show_extras=False;sp.shading.color_type='MATERIAL'
            sp.region_3d.view_location=(.007,0,-.003);sp.region_3d.view_distance=.10;sp.region_3d.view_rotation=s.camera.rotation_euler.to_quaternion();sp.region_3d.view_perspective='ORTHO'
p=O/'M5_equal_supports_v050.blend';bpy.ops.wm.save_as_mainfile(filepath=str(p));bpy.ops.wm.open_mainfile(filepath=str(p))
b=audit(bpy.data.scenes['01 EQUAL HEIGHT SUPPORTS'].objects[NAME]);assert b['vertices']==check['vertices'] and b['nonmanifold_edges']==0
(O/'reports/blender_saved_readback.json').write_text(json.dumps(dict(status='PASS',mesh=b),indent=2))
for name,stem in [('01 EQUAL HEIGHT SUPPORTS','01_raised_supports'),('02 SAME HEIGHT PLANE','02_height_alignment'),('03 SUPPORT CLOSEUP','03_support_closeup')]:
    sc=bpy.data.scenes[name];sc.render.filepath=str(O/'renders'/(stem+'.png'));bpy.ops.render.render(write_still=True,scene=name)
print('RENDER_COMPLETE',p,flush=True)
