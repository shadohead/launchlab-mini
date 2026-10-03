"""Raise both opposite-end pads to the existing screw standoff plane."""
from pathlib import Path
import ast, hashlib, json, shutil
import cadquery as cq
import numpy as np
import trimesh
from scipy.spatial import cKDTree

R=Path(__file__).resolve().parents[1]
S=R/'inspection/M5_soft_ramp_v049'
O=R/'inspection/M5_equal_supports_v050'
assert not (O/'SHA256SUMS.txt').exists(), 'Delivered revision is immutable'
for d in ['preview','stl','step','references','renders','reports','provenance']:
    (O/d).mkdir(parents=True,exist_ok=True)
hashes={}
for line in (S/'SHA256SUMS.txt').read_text().splitlines():
    h,n=line.split('  ',1)
    if n.startswith(('preview/','stl/')) or n in ['parameters.json','assembly_manifest.json','LICENSE.txt']:
        assert hashlib.sha256((S/n).read_bytes()).hexdigest()==h,n
        hashes[n]=h
for node in ast.parse((R/'scripts/build_compact_v010.py').read_text()).body:
    if isinstance(node,ast.FunctionDef) and node.name=='repair_collinear_boundary':
        exec(compile(ast.Module(body=[node],type_ignores=[]),'helper','exec'))
def box(a,b):
    return trimesh.creation.box(extents=np.array(b)-a,transform=trimesh.transformations.translation_matrix((np.array(a)+b)/2))
def inter(a,b):
    return trimesh.boolean.intersection([a,b],engine='manifold')
def diff(a,b):
    if not len(a.faces):return trimesh.Trimesh()
    if not len(b.faces):return a.copy()
    return trimesh.boolean.difference([a,b],engine='manifold')
def vol(a):return abs(float(a.volume)) if a is not None and len(a.faces) else 0
P=json.loads((S/'parameters.json').read_text())
M=json.loads((S/'assembly_manifest.json').read_text())
old=trimesh.load(S/M['parts'][0]['filename'],force='mesh')
deck=P['platform_top_z_mm']; top=P['M5_mount_face_z_mm']
centers=P['rear_supports']['centers_xy_mm']; old_top=P['rear_supports']['top_z_mm']
height=top-deck
assert abs(height-2.3)<1e-6 and abs(top-old_top-1.8)<1e-6
post_tops=[]
for x,y in P['M5_axes_xy_mm']:
    post=inter(old,box([x-2.6,y-2.6,deck+.001],[x+2.6,y+2.6,0]))
    post_tops.append(float(post.bounds[1,2]));assert abs(post.bounds[1,2]-top)<.0001
pads=[]
for i,(x,y) in enumerate(centers,1):
    s=cq.Workplane('XY').box(6,2.6,height+.05,centered=(True,True,False)).translate((x,y,deck-.05)).edges('|Z').fillet(.5).val()
    assert s.isValid()
    cq.exporters.export(s,str(O/'step'/f'Equal_height_support_{i}_ONLY.step'))
    v,f=s.tessellate(.015,.06)
    m=repair_collinear_boundary(trimesh.Trimesh([p.toTuple() for p in v],f,process=True))
    assert m.is_watertight and m.is_winding_consistent
    pads.append(m);m.export(O/'references'/f'Equal_height_support_{i}.stl')
new=trimesh.boolean.union([old,*pads],engine='manifold')
new.merge_vertices(digits_vertex=7);new.remove_unreferenced_vertices()
assert new.is_watertight and new.is_winding_consistent and len(new.split())==1
NAME='01_M5_equal_supports_platform'
new.export(O/'preview'/(NAME+'.stl'))
printed=new.copy();printed.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]))
shift=np.r_[-printed.bounds[:,:2].mean(0),-printed.bounds[0,2]]
assert np.max(np.abs(shift-np.array(P['print_translation_mm'])))<.0001
printed.apply_translation(shift);printed.export(O/'stl'/(NAME+'.stl'))
readback=trimesh.load(O/'stl'/(NAME+'.stl'),force='mesh')
delta=float(max(cKDTree(printed.vertices).query(readback.vertices)[0].max(),cKDTree(readback.vertices).query(printed.vertices)[0].max()))
assert delta<.0001 and readback.is_watertight and len(readback.split())==1
removed=vol(diff(old,new));assert removed<.002
added=diff(new,old)
allowed=trimesh.boolean.union([box([x-3.01,y-1.31,old_top-.001],[x+3.01,y+1.31,top+.001]) for x,y in centers],engine='manifold')
outside=vol(diff(added,allowed));assert outside<.002
pad_tops=[]
for x,y in centers:
    m=inter(new,box([x-3.01,y-1.31,deck+.001],[x+3.01,y+1.31,0]))
    pad_tops.append(float(m.bounds[1,2]));assert abs(m.bounds[1,2]-top)<.0001
factory=trimesh.load(S/'preview/REF_M5Stick_factory_geometry.stl',force='mesh')
rep=dict(status='PASS',units='mm',watertight=new.is_watertight,winding_consistent=new.is_winding_consistent,components=len(new.split()),source_sha256=hashes,old_support_height_mm=old_top-deck,new_support_height_mm=height,added_support_height_mm=top-old_top,support_top_z_mm=pad_tops,screw_standoff_top_z_mm=post_tops,support_centers_xy_mm=centers,removed_material_mm3=removed,added_material_mm3=vol(added),changed_material_outside_support_extensions_mm3=outside,STL_export_delta_mm=delta,preserved='All prior geometry outside the two support extensions, including softened center ramp and screw-head recesses',fixed_nominal_M5_reference_overlap_mm3=vol(inter(new,factory)),reference_pose='Frozen manufacturer reference is unchanged; equal-height supports are a user-requested physical-fit iteration rather than a verified assembly fit',physical_fit='UNVERIFIED',print_bounds_mm=printed.bounds.tolist())
parts=[dict(name=NAME,filename=f'preview/{NAME}.stl',color='#357B73',description='v049 carrier with both opposite-end supports raised to the screw standoff height',group='M5',reference=False,printable=True,source='Frozen v049 carrier plus analytic support extensions')]
for e in M['parts']:
    if e['reference']:
        shutil.copy2(S/e['filename'],O/e['filename']);parts.append(dict(e))
M.update(version='0.50',parts=parts,print_package_created=False)
P.update(version='0.50',architecture='Soft-ramp M5 carrier with equal-height screw posts and opposite-end supports',print_translation_mm=shift.tolist(),physical_fit='User-requested equal support heights; actual M5 seating and leveling unverified')
P['rear_supports'].update(top_z_mm=top,height_above_deck_mm=height,added_height_mm=top-old_top,source='User-requested match to existing screw standoff plane')
P['limits']=[x for x in P['limits'] if 'Opposite-end supports retain' not in x]+['Both opposite-end supports are now 2.3 mm high, matching the screw posts; the unchanged nominal M5 reference has a stepped underside, so this revision does not claim CAD-level assembly fit.']
for name in ['LICENSE.txt','references/USER_center_rectangle.png']:
    shutil.copy2(S/name,O/name)
(O/'parameters.json').write_text(json.dumps(P,indent=2))
(O/'assembly_manifest.json').write_text(json.dumps(M,indent=2))
(O/'reports/cad_validation.json').write_text(json.dumps(rep,indent=2))
(O/'README.md').write_text('M5 equal-height supports v050\n\nThe two existing 6 x 2.6 mm support pads are raised from 0.5 to 2.3 mm above the deck, matching the existing screw standoffs at Z -3.5. Each gains 1.8 mm. Footprint, location and 0.5 mm corner radii are unchanged. All other v049 carrier geometry is preserved, including the softened center ramp, underside screw-head recesses and launcher receivers.\n\nThe nominal manufacturer M5 reference remains at its old pose for provenance. It has a stepped underside and overlaps the taller pads; it is not presented as a verified assembly. The requested equal-height support configuration requires physical seating and leveling inspection. The printable carrier is one watertight solid. STEP files contain only the added support geometry; the complete carrier is mesh geometry.\n\nPrint orientation: existing +90-degree Y side orientation. One replacement carrier, sensor mount separate.\n')
shutil.copy2(__file__,O/'provenance'/Path(__file__).name)
print('PASS',O,'both supports = screw standoffs =',height,'mm; added',top-old_top,'mm',flush=True)
