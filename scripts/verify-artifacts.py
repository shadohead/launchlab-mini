from pathlib import Path
import hashlib, json, zipfile
root = Path(__file__).resolve().parents[1]
catalog = json.loads((root/'site/public/firmware/catalog.json').read_text())
count=0
for file in catalog['files']:
    data=(root/'site/public'/file['path']).read_bytes()
    assert len(data)==file['size'] and hashlib.sha256(data).hexdigest()==file['sha256'], file['path']
    count+=1
for manifest in (root/'firmware/releases').glob('*/manifest.json'):
    m=json.loads(manifest.read_text()); data=(manifest.parent/m.get('binary','LaunchLabMini.ino.bin')).read_bytes()
    assert hashlib.sha256(data).hexdigest()==m['sha256'],manifest
    count+=1
for directory in (root/'hardware').iterdir():
    if directory.is_dir() and (directory/'SHA256SUMS.txt').exists():
        for line in (directory/'SHA256SUMS.txt').read_text().splitlines():
            digest, name=line.split(maxsplit=1); p=directory/name
            assert p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==digest,p
            count+=1
for version in json.loads((root/'hardware/versions.json').read_text())['versions']:
    for file in version['files']:
        data=(root/file['path']).read_bytes()
        assert len(data)==file['size'] and hashlib.sha256(data).hexdigest()==file['sha256'],file['path']
        count+=1
for p in root.rglob('*.3mf'):
    if 'node_modules' in p.parts or 'dist' in p.parts: continue
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None,p
        assert '[Content_Types].xml' in z.namelist(),p
current = root/'firmware/releases/0.10.1-sticks3-qre1113-tiltreplay'
assert (root/'site/public'/catalog['files'][3]['path']).read_bytes()==(current/'LaunchLabMini.ino.bin').read_bytes()
assert catalog['runtime']==json.loads((current/'manifest.json').read_text())['runtime_version']
for path in (root/'firmware/LaunchLabMini').rglob('*'):
    if path.is_file() and path.suffix in ['.h','.ino','.cpp','.c']:
        assert path.read_bytes()==(current/'source'/path.relative_to(root/'firmware/LaunchLabMini')).read_bytes(),path
print(f'PASS: {count} checksums; all 3MF archives intact; site app matches frozen firmware')
