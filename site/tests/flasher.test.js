import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {validateCatalog, verifiedDownload, flashVerified} from '../src/flasher.js';
const catalog = JSON.parse(await readFile(new URL('../public/firmware/catalog.json', import.meta.url)));
const base = new URL('../public/', import.meta.url);
const localFetch = async url => ({ok:true,arrayBuffer:async()=>{const b=await readFile(url);return b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);}});
const images = await Promise.all(catalog.files.map(file=>verifiedDownload(file,base,localFetch)));
function fake(chip='ESP32-S3', partitions=images[1].data) {
 const writes=[];return {writes,chip:{CHIP_NAME:chip},async readFlash(address,size){assert.equal(address,0x8000);assert.equal(size,partitions.length);return partitions;},async writeFlash(options){writes.push(options);}};
}
const opts=loader=>({loader,catalog,images,mode:'update',md5:()=>'',reportProgress(){}});
test('release downloads have exact sizes and SHA-256',()=>assert.equal(images.length,4));
test('update writes only application and never erases all',async()=>{const l=fake();await flashVerified(opts(l));assert.deepEqual(l.writes[0].fileArray.map(f=>f.address),[0x10000]);assert.equal(l.writes[0].eraseAll,false);assert.equal(typeof l.writes[0].calculateMD5Hash,'function');});
test('first install uses exact offsets',async()=>{const l=fake();await flashVerified({...opts(l),mode:'install'});assert.deepEqual(l.writes[0].fileArray.map(f=>f.address),[0,0x8000,0xe000,0x10000]);assert.equal(l.writes[0].eraseAll,false);});
test('wrong chip refused without writes',async()=>{const l=fake('ESP32');await assert.rejects(flashVerified(opts(l)),/M5StickS3/);assert.equal(l.writes.length,0);});
test('partition mismatch refused without writes',async()=>{const p=images[1].data.slice();p[0]^=1;const l=fake('ESP32-S3',p);await assert.rejects(flashVerified(opts(l)),/partition layout/);assert.equal(l.writes.length,0);});
test('tampered download refused',async()=>{await assert.rejects(verifiedDownload(catalog.files[3],base,async()=>({ok:true,arrayBuffer:async()=>new Uint8Array([1,2]).buffer})),/checksum mismatch/);});
test('HTTP failure reported',async()=>{await assert.rejects(verifiedDownload(catalog.files[3],base,async()=>({ok:false,status:404})),/404/);});
test('catalog cannot write into NVS or inject external URLs',()=>{for(const mutate of [c=>c.files[3].offset=0x9000,c=>c.files[3].path='https://bad.example/app.bin',c=>c.files[0].size=0x9000,c=>c.files[3].sha256='bad']){const c=structuredClone(catalog);mutate(c);assert.throws(()=>validateCatalog(c));}});
test('missing images or invalid mode cannot flash',async()=>{const l=fake();await assert.rejects(flashVerified({...opts(l),images:[]}),/Incomplete/);await assert.rejects(flashVerified({...opts(l),mode:'erase'}),/Unknown/);assert.equal(l.writes.length,0);});
test('write verification failure is propagated',async()=>{const l=fake();l.writeFlash=async()=>{throw new Error('MD5 mismatch');};await assert.rejects(flashVerified(opts(l)),/MD5 mismatch/);});

test('fresh device first install does not require LaunchLab partition table',async()=>{
 const l=fake();l.readFlash=async()=>{throw new Error('Factory device must not be treated as an update');};
 await flashVerified({...opts(l),mode:'install'});
 assert.deepEqual(l.writes[0].fileArray.map(f=>f.address),[0,0x8000,0xe000,0x10000]);
 assert.equal(l.writes[0].flashMode,'dio');assert.equal(l.writes[0].flashSize,'8MB');
 for(const file of l.writes[0].fileArray)assert.ok(file.address+file.data.length<=0x9000 || file.address>=0xe000,'NVS must not be overwritten');
});
test('first install also refuses wrong-chip factory devices before any writes',async()=>{
 const l=fake('ESP32-S2');await assert.rejects(flashVerified({...opts(l),mode:'install'}),/M5StickS3/);assert.equal(l.writes.length,0);
});
