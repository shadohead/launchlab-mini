export const APP_OFFSET = 0x10000;
export const APP_IDENTITY_BYTES = 1024;
const EXPECTED_FILES = [['bootloader.bin', 0], ['partitions.bin', 0x8000], ['boot_app0.bin', 0xe000], ['application.bin', APP_OFFSET]];
const hex = (value, length) => typeof value === 'string' && new RegExp('^[a-f0-9]{' + length + '}$').test(value);
export function compareVersions(a, b) {
  const parts = value => {
    if (typeof value !== 'string' || !/^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/.test(value)) throw new Error('Invalid release version.');
    const p = value.split('.').map(Number);
    if (p.some(n => !Number.isSafeInteger(n))) throw new Error('Invalid release version.');
    return p;
  };
  const x = parts(a), y = parts(b);
  for (let i = 0; i < 3; i++) if (x[i] !== y[i]) return x[i] > y[i] ? 1 : -1;
  return 0;
}
export function validateCatalog(catalog) {
  compareVersions(catalog.version, catalog.version);
  if (catalog.board !== 'M5StickS3 K150' || catalog.chip !== 'ESP32-S3' || catalog.flashBytes !== 0x800000 || catalog.applicationOffset !== APP_OFFSET) throw new Error('Unsupported board or flash layout.');
  if (typeof catalog.release !== 'string' || !catalog.release.startsWith(catalog.version + '-sticks3-qre1113-') || !/^[a-z0-9.-]+$/.test(catalog.release) || typeof catalog.runtime !== 'string' || !catalog.runtime.startsWith(catalog.version + '-')) throw new Error('Release identity mismatch.');
  if (catalog.files?.length !== 4) throw new Error('Incomplete firmware bundle.');
  catalog.files.forEach((file, i) => {
    const [name, offset] = EXPECTED_FILES[i];
    if (file.path !== 'firmware/' + catalog.version + '/' + name || file.offset !== offset || !hex(file.sha256, 64) || !Number.isInteger(file.size) || file.size <= 0) throw new Error('Invalid firmware file or address.');
    const limit = i < 3 ? EXPECTED_FILES[i + 1][1] : APP_OFFSET + 0x330000;
    if (offset + file.size > limit) throw new Error('Firmware exceeds its flash region.');
  });
  if (!Array.isArray(catalog.knownApplications) || !catalog.knownApplications.length || catalog.knownApplications.length > 100) throw new Error('Missing installed-application identities.');
  const versions = new Set(), elves = new Set();
  for (const app of catalog.knownApplications) {
    compareVersions(app.version, app.version);
    if (app.sensor !== 'qre1113' || !hex(app.elfSha256, 64) || !hex(app.sha256, 64) || !hex(app.md5, 32) || !Number.isInteger(app.size) || app.size < APP_IDENTITY_BYTES || app.size > 0x330000 || versions.has(app.version) || elves.has(app.elfSha256)) throw new Error('Invalid installed-application identity.');
    versions.add(app.version); elves.add(app.elfSha256);
  }
  const target = catalog.knownApplications.find(app => app.version === catalog.version);
  if (!target || target.sha256 !== catalog.files[3].sha256 || target.size !== catalog.files[3].size || target.runtime !== catalog.runtime) throw new Error('Target application identity mismatch.');
  return catalog;
}
async function sha256(data) {
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', data)), x => x.toString(16).padStart(2, '0')).join('');
}
export async function verifiedDownload(file, baseUrl, fetchFn = fetch) {
  const response = await fetchFn(new URL(file.path, baseUrl), {cache: 'no-store'});
  if (!response.ok) throw new Error('Download failed (' + response.status + '): ' + file.path);
  const data = new Uint8Array(await response.arrayBuffer());
  if (data.length !== file.size || await sha256(data) !== file.sha256) throw new Error('Firmware checksum mismatch. No flash was written.');
  return {...file, data};
}
export async function inspectInstalledApplication(loader, catalog) {
  const data = new Uint8Array(await loader.readFlash(APP_OFFSET, APP_IDENTITY_BYTES));
  if (data.length !== APP_IDENTITY_BYTES) throw new Error('Incomplete installed-application read. No flash was written.');
  if (data[0] !== 0xe9 || new DataView(data.buffer, data.byteOffset, data.byteLength).getUint32(32, true) !== 0xabcd5432) return {state:'unknown'};
  const elf = Array.from(data.slice(176,208), x => x.toString(16).padStart(2,'0')).join('');
  const app = catalog.knownApplications.find(a => a.elfSha256 === elf);
  if (!app) return {state:'unknown'};
  // Arduino's descriptor version is a build label. Identify the archived ELF,
  // then verify the complete installed image, not just its descriptor.
  const digest = await loader.flashMd5sum(APP_OFFSET, app.size);
  return {state:typeof digest === 'string' && digest.toLowerCase() === app.md5 ? 'verified' : 'damaged', application:app};
}
export async function flashVerified({loader, catalog, images, mode, recoveryConfirmed=false, installConfirmed=false, md5, reportProgress, onInspect=()=>{}}) {
  validateCatalog(catalog);
  if (!['update', 'install', 'recovery'].includes(mode)) throw new Error('Unknown install mode.');
  if (mode === 'install' && installConfirmed !== true) throw new Error('Confirm first install and backup before continuing.');
  if (mode === 'recovery' && recoveryConfirmed !== true) throw new Error('Confirm intentional repair or downgrade and backup before continuing.');
  if (loader.chip?.CHIP_NAME !== 'ESP32-S3') throw new Error('This firmware requires an M5StickS3 (ESP32-S3).');
  if (images.length !== catalog.files.length) throw new Error('Incomplete verified download.');
  for (let i=0; i<images.length; i++) {
    const image=images[i], file=catalog.files[i];
    if (!(image.data instanceof Uint8Array) || image.path !== file.path || image.offset !== file.offset || image.data.length !== file.size || await sha256(image.data) !== file.sha256) throw new Error('Incomplete or changed verified download. No flash was written.');
  }
  let installed;
  if (mode !== 'install') {
    const same = (a,b) => a.length === b.length && a.every((byte,i)=>byte===b[i]);
    const partitions = new Uint8Array(await loader.readFlash(0x8000, images[1].data.length));
    if (!same(partitions, images[1].data)) throw new Error('The device has a different partition layout. Stop and back up before considering First install.');
    // This updater writes app0 only. Do not write an inactive slot when an
    // outside OTA tool has changed boot selection.
    const bootSelection = new Uint8Array(await loader.readFlash(0xe000, images[2].data.length));
    if (!same(bootSelection, images[2].data)) throw new Error('The device has a different boot selection. Stop and back up; app-only update cannot safely continue.');
    installed = await inspectInstalledApplication(loader, catalog);
    onInspect(installed);
    if (mode === 'update') {
      if (installed.state !== 'verified') throw new Error('Installed LaunchLab application is unknown or incomplete. Update stopped. Use Repair / rollback only after backup and an intentional version choice.');
      const comparison = compareVersions(catalog.version, installed.application.version);
      if (comparison < 0) throw new Error('Downgrade blocked: installed v' + installed.application.version + ', selected v' + catalog.version + '. Keep the newer release or deliberately use Repair / rollback.');
      if (comparison === 0) return {status:'up-to-date', installed};
    }
  }
  const selected = mode === 'install' ? images : [images[3]];
  await loader.writeFlash({fileArray: selected.map(image => ({data:image.data, address:image.offset})), flashSize:'8MB', flashMode:'dio', flashFreq:'80m', eraseAll:false, compress:true, calculateMD5Hash:md5, reportProgress});
  return {status:'verified', installed};
}
