export const APP_OFFSET = 0x10000;
const EXPECTED_FILES = [['bootloader.bin', 0], ['partitions.bin', 0x8000], ['boot_app0.bin', 0xe000], ['application.bin', APP_OFFSET]];
export function validateCatalog(catalog) {
  if (catalog.board !== 'M5StickS3 K150' || catalog.chip !== 'ESP32-S3' || catalog.flashBytes !== 0x800000 || catalog.applicationOffset !== APP_OFFSET) throw new Error('Unsupported board or flash layout.');
  if (catalog.files?.length !== 4) throw new Error('Incomplete firmware bundle.');
  catalog.files.forEach((file, i) => {
    const [name, offset] = EXPECTED_FILES[i];
    if (!/^firmware\/[0-9.]+\/[a-z_0-9.]+$/.test(file.path) || !file.path.endsWith('/' + name) || file.offset !== offset || !/^[a-f0-9]{64}$/.test(file.sha256) || !Number.isInteger(file.size) || file.size <= 0) throw new Error('Invalid firmware file or address.');
    const limit = i < 3 ? EXPECTED_FILES[i + 1][1] : APP_OFFSET + 0x330000;
    if (offset + file.size > limit) throw new Error('Firmware exceeds its flash region.');
  });
  return catalog;
}
export async function verifiedDownload(file, baseUrl, fetchFn = fetch) {
  const response = await fetchFn(new URL(file.path, baseUrl), {cache: 'no-store'});
  if (!response.ok) throw new Error(`Download failed (${response.status}): ${file.path}`);
  const data = new Uint8Array(await response.arrayBuffer());
  const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', data)), x => x.toString(16).padStart(2, '0')).join('');
  if (data.length !== file.size || digest !== file.sha256) throw new Error('Firmware checksum mismatch. No flash was written.');
  return {...file, data};
}
export async function flashVerified({loader, catalog, images, mode, md5, reportProgress}) {
  validateCatalog(catalog);
  if (!['update', 'install'].includes(mode)) throw new Error('Unknown install mode.');
  if (loader.chip?.CHIP_NAME !== 'ESP32-S3') throw new Error('This firmware requires an M5StickS3 (ESP32-S3).');
  if (images.length !== catalog.files.length || images.some((image,i) => image.offset !== catalog.files[i].offset || image.data.length !== catalog.files[i].size)) throw new Error('Incomplete verified download.');
  if (mode === 'update') {
    const installed = new Uint8Array(await loader.readFlash(0x8000, images[1].data.length));
    if (installed.length !== images[1].data.length || installed.some((byte,i) => byte !== images[1].data[i])) throw new Error('The device has a different partition layout. Use First install after backing up the device.');
  }
  const selected = mode === 'update' ? [images[3]] : images;
  await loader.writeFlash({fileArray: selected.map(image => ({data:image.data, address:image.offset})), flashSize:'8MB', flashMode:'dio', flashFreq:'80m', eraseAll:false, compress:true, calculateMD5Hash:md5, reportProgress});
}
