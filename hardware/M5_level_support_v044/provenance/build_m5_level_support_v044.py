"""Add opposite-end supports to the accepted M5 carrier using its factory back datum."""
from pathlib import Path
import ast,hashlib,json,shutil
import cadquery as cq,numpy as np,trimesh
R=Path(__file__).resolve().parents[1];S=R/'releases/LaunchLab_v040_right_block_print';O=R/'inspection/M5_level_support_v044'
assert not (O/'SHA256SUMS.txt').exists(),'Delivered prototype is immutable'
for d in ['preview','stl','step','references','renders','reports','provenance']:(O/d).mkdir(parents=True,exist_ok=True)
source_hashes={}
for line in (S/'SHA256SUMS.txt').read_text().splitlines():
 h,n=line.split('  ',1)
 if n.startswith(('preview/','stl/')) or n=='parameters.json':assert hashlib.sha256((S/n).read_bytes()).hexdigest()==h,n;source_hashes[n]=h
for node in ast.parse((R/'scripts/build_compact_v010.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name=='repair_collinear_boundary':exec(compile(ast.Module(body=[node],type_ignores=[]),'helper','exec'))
def cm(s):
 v,f=s.tessellate(.015,.06);m=repair_collinear_boundary(trimesh.Trimesh([p.toTuple() for p in v],f,process=True));assert m.is_watertight;return m
def box(a,b):return trimesh.creation.box(extents=np.array(b)-a,transform=trimesh.transformations.translation_matrix((np.array(a)+b)/2))
def inter(a,b):return trimesh.boolean.intersection([a,b],engine='manifold')
def diff(a,b):return trimesh.boolean.difference([a,b],engine='manifold')
def vol(m):return abs(float(m.volume)) if m is not None and len(m.faces) else 0
P=json.loads((S/'parameters.json').read_text());M=json.loads((S/'assembly_manifest.json').read_text());old=trimesh.load(S/'preview/01_M5_stepped_platform.stl',force='mesh');factory=trimesh.load(S/'preview/REF_M5Stick_factory_geometry.stl',force='mesh')
DECK=P['platform_top_z_mm'];CONTACT=-5.3;CENTERS=[(4.3,12.5),(16.3,12.5)];pads=[]
for i,(x,y) in enumerate(CENTERS,1):
 s=cq.Workplane('XY').box(6,2.6,CONTACT-DECK+.05,centered=(True,True,False)).translate((x,y,DECK-.05)).edges('|Z').fillet(.5).val()
 cq.exporters.export(s,str(O/'step'/f'Added_support_pad_{i}.step'));m=cm(s);pads.append(m);m.export(O/'references'/f'Added_support_pad_{i}.stl')
new=trimesh.boolean.union([old,*pads],engine='manifold');new.merge_vertices(digits_vertex=7);new.remove_unreferenced_vertices();assert new.is_watertight and new.is_winding_consistent and len(new.split())==1
n='01_M5_level_platform';new.export(O/'preview'/(n+'.stl'));printed=new.copy();printed.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]));shift=np.r_[-printed.bounds[:,:2].mean(0),-printed.bounds[0,2]];printed.apply_translation(shift);printed.export(O/'stl'/(n+'.stl'))
M.update(version='0.44',print_package_created=False,parts=[dict(name=n,filename=f'preview/{n}.stl',color='#357B73',description='v040 carrier plus two integral support pads at the Hat-side back-panel datum',group='M5',reference=False,printable=True,source='Accepted v040 native carrier and factory M5 reference')])
for e in json.loads((S/'assembly_manifest.json').read_text())['parts']:
 if not e['reference'] or e['name'].startswith('REF_soft_liner'):continue
 shutil.copy2(S/e['filename'],O/e['filename']);M['parts'].append(dict(e))
# Sample the actual factory underside across each contact patch.
t=factory.triangles;a=t[:,0];u=t[:,1]-a;v=t[:,2]-a;det=u[:,0]*v[:,1]-u[:,1]*v[:,0];ok=abs(det)>1e-9
samples=[]
for cx,cy in CENTERS:
 for x in np.linspace(cx-2.5,cx+2.5,7):
  for y in np.linspace(cy-.8,cy+.8,5):
   dx=x-a[:,0];dy=y-a[:,1];b=np.divide(dx*v[:,1]-dy*v[:,0],det,out=np.zeros_like(det),where=ok);c=np.divide(u[:,0]*dy-u[:,1]*dx,det,out=np.zeros_like(det),where=ok);hit=ok&(b>=-1e-6)&(c>=-1e-6)&(b+c<=1+1e-6);z=a[:,2]+b*u[:,2]+c*v[:,2];zmin=float(z[hit].min());assert abs(zmin-CONTACT)<.00001,(x,y,zmin);samples.append([float(x),float(y),zmin])
rep=dict(status='PASS',watertight=new.is_watertight,winding_consistent=new.is_winding_consistent,components=len(new.split()),source_sha256=source_hashes,M5_overlap_mm3=vol(inter(new,factory)),old_volume_mm3=vol(old),new_volume_mm3=vol(new),added_material_mm3=vol(new)-vol(old),support_height_above_deck_mm=CONTACT-DECK,support_top_z_mm=CONTACT,support_centers_xy_mm=CENTERS,contact_probe_count=len(samples),underside_samples_mm=samples,preserved={})
assert rep['M5_overlap_mm3']<.002;assert vol(diff(old,new))<.002
# Both supports touch the solid flat back panel; 0.002mm probe enters the factory shell.
contact_areas=[]
for pad in pads:
 probe=pad.copy();probe.apply_translation((0,0,.002));area=vol(inter(probe,factory))/.002;assert area>15.2;contact_areas.append(area)
rep['support_contact_area_mm2']=contact_areas
for name,roi in [('native_head_and_receivers',box([-25,-30,-20],[-1.9999,30,20])),('USB_screw_mounts',box([-2,-26,-10],[24,-17,0])),('trimmed_right_block',box([-25,-30,0],[-2,-14.99,20])),('deck_below_top',box([-2,-30,-10],[24,30,DECK-.0001]))]:
 f=inter(old,roi);g=inter(new,roi);vv=vol(diff(f,g))+vol(diff(g,f));assert vv<.002,(name,vv);rep['preserved'][name+'_symmetric_difference_mm3']=vv
shutil.copy2(S/'LICENSE.txt',O/'LICENSE.txt')
shutil.copy2(R/'inspection/minimal_TCRT_sensor_only_v042/renders/Pasted 2026-10-02 at 12.49.13 PM.png',O/'references/USER_M5_level_markup.png')
P.update(version='0.44',architecture='Accepted trimmed v040 carrier with integral opposite-end back-panel supports',print_package_created=False,fasteners='Reuse 2 x M2x6 from underneath; integral printed pads replace the soft-liner assumption',rear_supports=dict(centers_xy_mm=CENTERS,width_mm=6,depth_mm=2.6,corner_radius_mm=.5,top_z_mm=CONTACT,height_above_deck_mm=CONTACT-DECK,source='Actual downward back-panel face of factory M5 mesh'),print_translation_mm=shift.tolist(),physical_fit='CAD contact verified; physical leveling and retention untested',limits=['The two supports follow the nominal factory back-panel plane, not a physical caliper measurement.','Dry-fit the M5 before tightening; manufacturing tolerances and screw preload require physical inspection.','Unsliced replacement STL, no printer dispatch.'])
(O/'parameters.json').write_text(json.dumps(P,indent=2));(O/'assembly_manifest.json').write_text(json.dumps(M,indent=2));(O/'reports/cad_validation.json').write_text(json.dumps(rep,indent=2))
(O/'README.md').write_text('M5 leveling supports v044\n\nThe accepted v040 trimmed carrier gains two integral 6 x 2.6 mm pads underneath the opposite end of the M5 flat back panel, just inboard of the Hat connector. Pads rise 0.5 mm above the deck to the factory back-plane datum Z -5.3. The front mounting faces are at Z -3.5 because the factory underside is stepped. These unequal pad heights match the different M5 contact surfaces and keep the modeled device level.\n\nExisting two M2x6 underside screws, device pose, USB-C direction, 3 mm right-block trim, matching bevel and launcher receivers remain unchanged. No change to either sensor mount. Replacement: one printed carrier. Physical leveling, preload and fit still need a dry fit. The STL is unsliced.\n')
shutil.copy2(__file__,O/'provenance'/Path(__file__).name)
print('PASS',O,'support height',CONTACT-DECK,'contact areas',contact_areas,flush=True)
