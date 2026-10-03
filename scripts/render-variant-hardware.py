"""Render current M5 v0.50 and old-sensor TCRT5000 v0.43 from frozen STL meshes.
Run Blender -b --python scripts/render-variant-hardware.py. No CAD file is modified.
"""
from pathlib import Path
# Reuse the existing camera/material helpers without executing its frozen v0.40 renders.
helper=Path(__file__).with_name('render-readme-hardware.py')
exec(compile(helper.read_text().split('bpy.ops.wm.read_factory_settings')[0],str(helper),'exec'))
OUT=ROOT/'docs/assets/hardware/variants';OUT.mkdir(parents=True,exist_ok=True)
SOURCES={'m5':ROOT/'hardware/M5_equal_supports_v050','tcrt':ROOT/'hardware/minimal_TCRT_split_keepers_v043'}
PARTS={
 '01_M5_equal_supports_platform':(1,'M5 equal-height carrier','#54b9a3'),
 '01_TCRT_sensor_cradle':(1,'TCRT sensor cradle','#5999b0'),
 '02_TCRT_clip_cap_LEFT':(2,'Left clip cap','#55bda2'),
 '02_TCRT_clip_cap_RIGHT':(3,'Right clip cap','#69c6b0'),
 '03_TCRT_sensor_pressure_keeper':(4,'Sensor pressure keeper','#f0bb66'),
 '08_TCRT_latch_LEFT':(5,'Left launcher latch','#bfa7ef'),
 '09_TCRT_latch_RIGHT':(6,'Right launcher latch','#e299b7')}
REPORT=[]
bpy.ops.wm.read_factory_settings(use_empty=True)
for kind,heading in [('m5','M5STICKS3  /  v0.50 EXPLODED'),('tcrt','OLD TCRT5000 SENSOR  /  v0.43 EXPLODED')]:
 folder=SOURCES[kind];manifest=json.loads((folder/'assembly_manifest.json').read_text());s=scene(kind+' latest exploded');obs=[];numbered=[]
 for item in manifest['parts']:
  if item.get('group')=='clearance':continue
  ob=load(s,folder,item);n=item['name'];shift=Vector((0,0,0))
  if kind=='m5':
   if n.startswith('REF_M2'):shift.z=-.017
   elif n.startswith('REF_'):shift.z=.030
  else:
   if n.startswith('02_TCRT_clip_cap'):
    shift.z=.032;shift.x= -.007 if n.endswith('LEFT') else .007
   elif n.startswith('03_TCRT'):shift.z=.032
   elif n.startswith('REF_M2x5'):shift.z=.043
   elif n.startswith('REF_M2x4'):shift.z=.042
   elif n.startswith('REF_'):shift.z=.015
   elif 'latch_' in n:
    center=sum(v.co.x for v in ob.data.vertices)/len(ob.data.vertices);shift.x=math.copysign(.020,center);shift.z=-.006
  ob.location+=shift;obs.append(ob)
  if n in PARTS:numbered.append((ob,PARTS[n][0]))
 scale=setup(s,obs,(-1,-1,1.0) if kind=='m5' else (-1,1,1.3),1.55)
 subtitle='Sliced prototype  /  stepped device reference lifted; seating on raised pads unverified' if kind=='m5' else 'Unsliced prototype  /  numbered prints; electronics and screws are nominal references'
 title(s,heading,subtitle,scale)
 for ob,n in numbered:number(s,ob,n,scale)
 render(s,kind+'-exploded.png')
for name,(n,label,color) in PARTS.items():
 kind='m5' if name.startswith('01_M5') else 'tcrt';folder=SOURCES[kind];manifest=json.loads((folder/'assembly_manifest.json').read_text());item=next(i for i in manifest['parts'] if i['name']==name)
 s=scene(kind+' piece '+str(n));s.render.resolution_x=850;s.render.resolution_y=620;ob=load(s,folder,item)
 scale=setup(s,[ob],(-1,-1,1.3) if kind=='m5' else (-1,1,1.4),1.55)
 title(s,f'{n:02d}  /  {label.upper()}','v0.50' if kind=='m5' else 'v0.43  /  actual saved STL mesh',scale)
 render(s,f'{kind}-part-{n:02d}.png')
(OUT/'provenance.json').write_text(json.dumps({'description':'Frozen local STL snapshots. Explosion translations are illustrative. M5 v0.50 has nominal reference-pad overlap in its original assembly; lifted reference here is not a fit claim. TCRT v0.43 has provisional electronic envelopes; all physical fit remains unverified.','renders':REPORT},indent=2)+'\n')
print('VARIANT_RENDER_COMPLETE',flush=True)
