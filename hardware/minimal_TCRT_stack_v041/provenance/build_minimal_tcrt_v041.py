"""Separate TCRT5000 stacked CAD prototype, measured old board; no firmware changes."""
from pathlib import Path
import ast,json,shutil,hashlib
import cadquery as cq
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];O=R/'inspection/minimal_TCRT_stack_v041';Q=R/'releases/LaunchLab_v033_flush_QRE';T=R/'releases/LaunchLab_v019_tcrt5000_open_stack'
for d in ['step','preview','stl','renders','reports','references']:(O/d).mkdir(parents=True,exist_ok=True)
for node in ast.parse((R/'scripts/build_compact_v010.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name=='repair_collinear_boundary':exec(compile(ast.Module(body=[node],type_ignores=[]),'helpers','exec'))
def box(a,b,c,d,e,f):return cq.Solid.makeBox(b-a,d-c,f-e,cq.Vector(a,c,e))
def cyl(r,x,y,a,b):return cq.Solid.makeCylinder(r,b-a,cq.Vector(x,y,a))
def load(p):return cq.importers.importStep(str(p)).val()
def mesh(s):
 v,f=s.tessellate(.025,.08);m=trimesh.Trimesh([p.toTuple() for p in v],f,process=True);m.merge_vertices(digits_vertex=5);m.update_faces(m.unique_faces());m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices();m=repair_collinear_boundary(m)
 assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
 return m
X=.1418;Y=-7.8658;x0,x1=X-6.5,X+6.5;y0,y1=Y-4,Y+27
PCB=15.1;TOP=16.1;AXES=[(X-9.8,3.6),(X+9.8,3.6)];DECK=20.6;DECKTOP=22.6
base=load(Q/'step/01_QRE_minimal_port.step').cut(box(-11,11,-18,22,5.4,35))
# Only optical relief changes below the central floor. Native latch beds remain intact.
base=base.cut(box(X-3.9,X+3.9,Y-3.4,Y+3.4,3.1,PCB))
# Thin open side rails, four bare edge seats and end stops. No assumed PCB holes.
for a,b in [(x0-1.8,x0-.2),(x1+.2,x1+1.8)]:
 base=base.fuse(box(a,b,y0-.8,y1+.8,5.35,TOP+.2))
for a,b in [(x0-1.8,x0+.6),(x1-.6,x1+1.8)]:
 for c,d in [(y0+.6,y0+2.1),(y1-2.1,y1-.6)]:base=base.fuse(box(a,b,c,d,PCB-1.6,PCB))
for c,d in [(y0-.8,y0-.2),(y1+.2,y1+.8)]:
 for a,b in [(x0-1.8,x0+1),(x1-1,x1+1.8)]:base=base.fuse(box(a,b,c,d,5.35,TOP-.2))
for x,y in AXES:
 base=base.fuse(cyl(2.3,x,y,5.35,TOP-.4)).cut(cyl(.85,x,y,TOP-3.4,TOP))
 # Connection to side rail.
 a,b=sorted((x,x0-.4 if x<X else x1+.4));base=base.fuse(box(a,b,y-1.3,y+1.3,5.35,TOP-.4))
# Existing clip crossbar passes through the side rails with 0.3 mm clearance.
base=base.cut(box(-14.3,14.3,2.1,4.5,11.8,14.184)).clean()
# Removable M5 support presses on four edge lands; screw ears sit 0.4mm above bosses.
cap=None
for a,b,pa,pb in [(x0-.6,x0-.05,x0-.6,x0+.6),(x1+.05,x1+.6,x1-.6,x1+.6)]:
 s=box(a,b,y0+.6,y1-.6,TOP+.3,TOP+1.4)
 for c,d in [(y0+.6,y0+2.1),(y1-2.1,y1-.6)]:s=s.fuse(box(pa,pb,c,d,TOP,TOP+.5))
 s=s.fuse(box(a,b,y0-.8,y0+.7,TOP+.3,TOP+3.4))
 cap=s if cap is None else cap.fuse(s)
cap=cap.fuse(box(x0-.6,x1+.6,y0-.8,y0+.7,TOP+2.2,TOP+3.4))
for x,y in AXES:
 cap=cap.fuse(cyl(2.3,x,y,TOP,TOP+1.6))
 a,b=sorted((x,x0 if x<X else x1));cap=cap.fuse(box(a,b,y-1.2,y+1.2,TOP,TOP+1.6))
 cap=cap.cut(cyl(1.1,x,y,TOP-.1,TOP+1.7))
 # Small risers behind the screw head, not around the device.
 cap=cap.fuse(box(a,b,y+3,y+5,TOP+.3,TOP+1.4))
 cap=cap.fuse(box(x-1.3,x+1.3,y+3,y+5,TOP+.3,DECKTOP))
for a,b in [(-12,-7.5),(7.5,12)]:cap=cap.fuse(box(a,b,-21,25,DECK,DECKTOP))
cap=cap.fuse(box(-12,12,-21,-17,DECK,DECKTOP))
for x in [-9,9]:cap=cap.fuse(cyl(2.5,x,-19,DECK,24.9)).cut(cyl(1.2,x,-19,DECK-.1,25))
# Vertical driver windows for the sensor screws, reinforced by 1mm rings.
for x,y in AXES:cap=cap.fuse(cyl(3.2,x,y,DECK,DECKTOP)).cut(cyl(2.2,x,y,TOP+1.61,DECKTOP+.1))
cap=cap.clean();keeper=load(Q/'step/02_QRE_clip_keeper.step')
# Move the crossbar in front of the larger PCB to keep its underside solder clear.
keeper=keeper.cut(box(-12,12,2.3,4.3,10,15))
for a,b in [(-14.4,-12),(12,14.4)]:keeper=keeper.fuse(box(a,b,-14.4,3.4,12.1,13.884))
keeper=keeper.fuse(box(-14.4,14.4,-14.4,-12.6,12.1,13.884)).clean()
base=base.cut(keeper).cut(cap).clean()
solids={'01_TCRT_minimal_cradle':base,'02_TCRT_clip_keeper':keeper,'03_TCRT_M5_clamp_dock':cap}
M={'version':'0.41','units':'mm','parts':[]};report={'status':'BUILDING','mesh':{},'collisions':{},'source_sha256':{}}
for n,s in solids.items():
 assert s.isValid() and len(s.Solids())==1,(n,s.isValid(),len(s.Solids()))
 cq.exporters.export(s,str(O/'step'/(n+'.step')));m=mesh(s);m.export(O/'preview'/(n+'.stl'))
 p=m.copy();rot=[0,-90,0] if n.startswith('01') else [180,0,0] if n.startswith('03') else [0,0,0]
 for ax,angle in zip([(1,0,0),(0,1,0),(0,0,1)],rot):
  if angle:p.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(angle),ax))
 p.apply_translation(np.r_[-p.bounds[:,:2].mean(axis=0),-p.bounds[0,2]]);p.export(O/'stl'/(n+'.stl'))
 report['mesh'][n]={'watertight':m.is_watertight,'components':len(m.split()),'volume_mm3':m.volume,'bounds_mm':m.bounds.tolist()}
 M['parts'].append(dict(name=n,filename=f'preview/{n}.stl',color='#48545D' if n.startswith('01') else '#D0A96A' if n.startswith('03') else '#398B83',reference=False,printable=True,group='printed',source='v041 measured TCRT alternate',description=n,print_rotation_deg=rot))
E={e['name']:e for e in json.loads((Q/'assembly_manifest.json').read_text())['parts']}
for n in ['08_QRE_latch_LEFT','09_QRE_latch_RIGHT']:
 e=dict(E[n]);nn=n.replace('QRE','TCRT');e.update(name=nn,filename=f'preview/{nn}.stl',description='Original launcher latch, unchanged')
 for d in ['preview','stl']:shutil.copy2(Q/d/(n+'.stl'),O/d/(nn+'.stl'))
 M['parts'].append(e)
# Old measured components and intact factory M5 move together 1mm down.
TE={e['name']:e for e in json.loads((T/'assembly_manifest.json').read_text())['parts']}
for n in ['REF_M5_OFFICIAL_GEOMETRY','REF_M5_SOFT_LINER','REF_TCRT_PCB_MEASURED','REF_TCRT_HEAD_AND_LEGS','REF_TCRT_LENS_PAIR','REF_TCRT_POT','REF_TCRT_HEADER','REF_TCRT_UNDERSIDE_SOLDER','REF_TCRT_TOP_SOLDER','REF_SENSOR_SOCKET_ALLOWANCE','REF_HAT_PLUG_ALLOWANCE','REF_WIRE_ROUTE_ALLOWANCE']:
 e=dict(TE[n]);m=trimesh.load(T/e['filename'],force='mesh');m.apply_translation((0,-4 if n.startswith('REF_M5') or n=='REF_HAT_PLUG_ALLOWANCE' else 0,-1));m.export(O/e['filename']);M['parts'].append(e)
for n,s in solids.items():
 for nn,ss in solids.items():
  if n<nn:
   v=s.intersect(ss).Volume();report['collisions'][n+' / '+nn]=v;assert v<.002,(n,nn,v)
# CAD envelopes independent from imported mesh references.
refsolids={'PCB':box(x0,x1,y0,y1,PCB,TOP),'head':box(X-5,X+5,Y-3,Y+3,5.6,PCB),'lens':box(X-3.5,X+3.5,Y-3,Y+3,3.1,5.6),'pot':box(X-.8,X+6.2,y1-19,y1-12,TOP,TOP+6),'header':box(X-5,X+5,y1-2,y1+6,TOP,TOP+4)}
for n,s in solids.items():
 for rn,rs in refsolids.items():
  v=s.intersect(rs).Volume();report['collisions'][n+' / '+rn]=v;assert v<.002,(n,rn,v)
# Preserve conservative solder clearance except the four recorded bare corner lands.
for rn in ['REF_TCRT_UNDERSIDE_SOLDER','REF_TCRT_TOP_SOLDER','REF_SENSOR_SOCKET_ALLOWANCE']:
 rm=trimesh.load(O/'preview'/(rn+'.stl'),force='mesh')
 for n in solids:
  inter=trimesh.boolean.intersection([trimesh.load(O/'preview'/(n+'.stl'),force='mesh'),rm],engine='manifold');v=abs(inter.volume) if inter is not None else 0
  report['collisions'][n+' / '+rn]=v;assert v<.002,(n,rn,v)
# Factory M5 intersection via manifold Boolean, allowing numerical face-contact noise.
m5=trimesh.load(O/'preview/REF_M5_OFFICIAL_GEOMETRY.stl',force='mesh')
for n in solids:
 inter=trimesh.boolean.intersection([trimesh.load(O/'preview'/(n+'.stl'),force='mesh'),m5],engine='manifold');v=abs(inter.volume) if inter is not None else 0
 report['collisions'][n+' / factory M5']=v;assert v<.002,(n,v)
for p in [Q/'step/01_QRE_minimal_port.step',Q/'step/02_QRE_clip_keeper.step',R/'reference files/TCRT5000_user_measurements_2026-09-21.md']:
 report['source_sha256'][str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
shutil.copy2(R/'reference files/TCRT5000_user_measurements_2026-09-21.md',O/'references/TCRT5000_measurements.md')
shutil.copy2(Q/'LICENSE.txt',O/'LICENSE.txt')
params=dict(sensor='OLD TCRT5000/LM393',PCB_mm=[31,13,1],optical_projection_mm=12,pot_mm=[7,7,6],sensor_seat_z_mm=PCB,optics_z_mm=3.1,M5_back_z_mm=22.9,M5_top_z_mm=37.9,clamp_screw_axes_mm=AXES,clamp_screws='2 x M2x4 pan head',M5_screws='2 x M2x6 underside',M5_screw_axes_mm=[[-9,-19],[9,-19]],assembly_order='Tighten sensor keeper first through driver windows, then mount M5 from underneath via the front overhang',wall_mm=1.6,deck_mm=2,xy_play_per_side_mm=.2,preload_ear_gap_mm=.4,limits=['Component positions and bare corner lands follow earlier TCRT CAD assumptions; physically check contact lands.','Plug and wire bends are provisional; header end remains open.','Launcher optical aperture alignment and lens-to-ring spacing need bench verification.','Prototype CAD/STL only; not sliced or sent to printer.'])
report['status']='PASS';(O/'reports/cad_validation.json').write_text(json.dumps(report,indent=2));(O/'parameters.json').write_text(json.dumps(params,indent=2));(O/'assembly_manifest.json').write_text(json.dumps(M,indent=2))
cq.exporters.export(cq.Compound.makeCompound(list(solids.values())),str(O/'TCRT_minimal_stack_v041.step'))
(O/'README.md').write_text('TCRT5000 minimal stacked alternate v041\n\nOpen measured 31x13x1mm board cradle on the v033 launcher base. Two centered M2x4 screws secure a removable keeper/M5 dock, pressing on four bare PCB edge lands. Existing launcher latches are reused; the crossbar moves ahead of the larger board to clear solder. Tighten the sensor keeper through its reinforced driver windows first. Then attach the M5 underneath with two M2x6 screws at the accessible front overhang.\n\nThis is a design prototype, not a sliced print package. Electronics are references, never print them. Physical contact lands, wire envelope and optical alignment require fit checking. The TCRT and QRE versions remain separate.\n')
print('PASS',O,flush=True)
