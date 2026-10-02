"""Render README assembly illustrations from frozen mesh files, without altering CAD.
Run: blender -b --python scripts/render-readme-hardware.py
All explosion translations are illustrative; nominal assembly geometry is retained.
"""
from pathlib import Path
import hashlib,json,math
import bpy
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/assets/hardware';OUT.mkdir(parents=True,exist_ok=True)
SOURCES={'m5':ROOT/'hardware/LaunchLab_v040_right_block_print','qre':ROOT/'hardware/LaunchLab_v033_flush_QRE'}
PARTS={
 '01_M5_stepped_platform':(1,'M5 platform','#54b9a3'),
 '01_QRE_minimal_port':(2,'QRE sensor base','#5999b0'),
 '02_QRE_clip_keeper':(3,'Latch crossbar','#55bda2'),
 '03_QRE_pressure_bar':(4,'Sensor pressure plate','#f0bb66'),
 '08_QRE_latch_LEFT':(5,'Left launcher latch','#bfa7ef'),
 '09_QRE_latch_RIGHT':(6,'Right launcher latch','#e299b7')}
REPORT=[]
def mat(color):
 if color in bpy.data.materials:return bpy.data.materials[color]
 rgb=[int(color[i:i+2],16)/255 for i in (1,3,5)]
 m=bpy.data.materials.new(color);m.diffuse_color=(*[v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in rgb],1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Roughness'].default_value=.47
 return m
def scene(name):
 s=bpy.data.scenes.new(name);bpy.context.window.scene=s;s.world=bpy.data.worlds.new(name+' world');s.world.use_nodes=True
 s.world.node_tree.nodes['Background'].inputs[0].default_value=(.026,.040,.047,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.65
 s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True;s.render.resolution_x=1400;s.render.resolution_y=1000;s.render.resolution_percentage=100
 s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';return s
def load(s,folder,item):
 path=folder/item['filename'];bpy.context.window.scene=s;bpy.ops.wm.stl_import(filepath=str(path),global_scale=.001,use_scene_unit=False)
 ob=bpy.context.object;ob.name=item['name'];ob.data.transform(ob.matrix_basis);ob.matrix_basis=Matrix.Identity(4)
 ob.data.materials.append(mat(PARTS[item['name']][2] if item['name'] in PARTS else item['color']))
 REPORT.append({'scene':s.name,'part':item['name'],'source':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 return ob
def setup(s,obs,direction=(-1,1,1.3),margin=1.32):
 bpy.context.view_layer.update();points=[ob.matrix_world@Vector(v) for ob in obs for v in ob.bound_box]
 target=Vector([(min(p[i] for p in points)+max(p[i] for p in points))/2 for i in range(3)])
 cd=bpy.data.cameras.new(s.name+' camera');cam=bpy.data.objects.new(cd.name,cd);s.collection.objects.link(cam);cam.location=target+Vector(direction).normalized()*.35
 cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.clip_start=.0001;cd.clip_end=10;s.camera=cam;bpy.context.view_layer.update()
 proj=[cam.matrix_world.inverted()@p for p in points];w=max(p.x for p in proj)-min(p.x for p in proj);h=max(p.y for p in proj)-min(p.y for p in proj)
 cd.ortho_scale=max(w,h*s.render.resolution_x/s.render.resolution_y)*margin
 for name,delta,power,size in [('Key',(.10,.0,.16),1.2,.15),('Fill',(-.10,-.12,.08),.7,.15),('Rim',(.03,.12,.12),1.1,.10)]:
  ld=bpy.data.lights.new(s.name+name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size
  light=bpy.data.objects.new(ld.name,ld);s.collection.objects.link(light);light.location=target+Vector(delta);light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
 return cd.ortho_scale

def text(s,value,x,y,size,color='#d9e6ec'):
 d=bpy.data.curves.new(value,'FONT');d.body=value;d.size=size
 ob=bpy.data.objects.new(value,d);s.collection.objects.link(ob);ob.parent=s.camera;ob.location=(x,y,-.10)
 m=bpy.data.materials.get('text'+color)
 if not m:
  m=bpy.data.materials.new('text'+color);m.use_nodes=True;n=m.node_tree.nodes;n.clear();em=n.new('ShaderNodeEmission');em.inputs[0].default_value=mat(color).diffuse_color;out=n.new('ShaderNodeOutputMaterial');m.node_tree.links.new(em.outputs[0],out.inputs[0])
 d.materials.append(m);return ob

def title(s,heading,sub,scale):
 height=scale*s.render.resolution_y/s.render.resolution_x
 text(s,heading,-scale*.455,height*.43,scale*.026)
 text(s,sub,-scale*.455,-height*.46,scale*.014,'#9faeb9')

def number(s,ob,n,scale):
 height=scale*s.render.resolution_y/s.render.resolution_x
 slots={1:(.30,-.10),2:(-.23,-.25),3:(.055,.29),4:(.25,.09),5:(.31,-.34),6:(-.28,.04)}
 x,y=slots[n];x*=scale;y*=height;r=scale*.018
 center=sum((ob.matrix_world@Vector(v) for v in ob.bound_box),Vector())/8
 pt=world_to_camera_view(s,s.camera,center);px=(pt.x-.5)*scale;py=(pt.y-.5)*height
 # Camera-facing callouts; annotation geometry is not part of the delivered mesh.
 dark=mat('#101b20');white=mat('#d9e6ec')
 for m in [dark,white]:
  if not m.get('annotation'):
   m['annotation']=True;nodelist=m.node_tree.nodes;nodelist.clear();em=nodelist.new('ShaderNodeEmission');em.inputs[0].default_value=m.diffuse_color;out=nodelist.new('ShaderNodeOutputMaterial');m.node_tree.links.new(em.outputs[0],out.inputs[0])
 verts=[(0,0,0)]+[(r*math.cos(i*math.tau/40),r*math.sin(i*math.tau/40),0) for i in range(40)]
 mesh=bpy.data.meshes.new('Callout '+str(n));mesh.from_pydata(verts,[],[(0,i+1,(i+1)%40+1) for i in range(40)])
 badge=bpy.data.objects.new(mesh.name,mesh);s.collection.objects.link(badge);badge.parent=s.camera;badge.location=(x,y,-.098);mesh.materials.append(dark)
 curve=bpy.data.curves.new('Leader '+str(n),'CURVE');curve.dimensions='3D';curve.bevel_depth=scale*.00045
 spline=curve.splines.new('POLY');spline.points.add(1);spline.points[0].co=(x,y,0,1);spline.points[1].co=(px,py,0,1)
 line=bpy.data.objects.new(curve.name,curve);s.collection.objects.link(line);line.parent=s.camera;line.location=(0,0,-.099);curve.materials.append(white)
 label=text(s,str(n),x-r*.42,y-r*.60,scale*.029,'#ffffff');label.location.z=-.097

def render(s,filename):
 s.render.filepath=str(OUT/filename);bpy.ops.render.render(write_still=True,scene=s.name)

bpy.ops.wm.read_factory_settings(use_empty=True)
for kind,heading in [('qre','QRE SENSOR ATTACHMENT  /  EXPLODED'),('m5','M5STICKS3 MOUNT  /  EXPLODED')]:
 folder=SOURCES[kind];manifest=json.loads((folder/'assembly_manifest.json').read_text());s=scene(kind+' exploded');obs=[];numbered=[]
 for item in manifest['parts']:
  ob=load(s,folder,item);n=item['name'];shift=Vector((0,0,0))
  if kind=='qre':
   if n=='02_QRE_clip_keeper':shift.z=.030
   elif n=='03_QRE_pressure_bar':shift.z=.021
   elif n.startswith('REF_M2x5_CLIP'):shift.z=.038
   elif n.startswith('REF_M2x4_SENSOR'):shift.z=.029
   elif n.startswith('REF_'):shift.z=.010
   elif 'latch_' in n:
    center=sum((v.co.x for v in ob.data.vertices))/len(ob.data.vertices);shift.x=math.copysign(.020,center);shift.z=.004
  else:
   if n.startswith('REF_M2'):shift.z=-.017
   elif n.startswith('REF_'):shift.z=.022
  ob.location+=shift;obs.append(ob)
  if n in PARTS:numbered.append((ob,PARTS[n][0]))
 scale=setup(s,obs,(-1,1,1.3) if kind=='qre' else (-1,-1,1.0),1.45)
 title(s,heading,'Numbered pieces are printed  /  electronics and screws are reference envelopes',scale)
 for ob,n in numbered:number(s,ob,n,scale)
 render(s,kind+'-exploded.png')
for name,(n,label,color) in PARTS.items():
 kind='m5' if n==1 else 'qre';folder=SOURCES[kind];manifest=json.loads((folder/'assembly_manifest.json').read_text());item=next(i for i in manifest['parts'] if i['name']==name)
 s=scene(f'part {n}');s.render.resolution_x=850;s.render.resolution_y=620;ob=load(s,folder,item)
 scale=setup(s,[ob],(-1,1,1.4) if kind=='qre' else (-1,-1,1.3),1.55)
 title(s,f'{n:02d}  /  {label.upper()}','Actual delivered mesh  /  one required per build',scale)
 render(s,f'part-{n:02d}.png')
(OUT/'provenance.json').write_text(json.dumps({'description':'Exploded translations are illustrative; all meshes are frozen release STL data. Independent M5 and QRE assemblies, not an inferred complete launcher pose.','renders':REPORT},indent=2)+'\n')
print('README_RENDER_COMPLETE',flush=True)
