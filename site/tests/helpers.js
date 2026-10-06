import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {APP_OFFSET, APP_IDENTITY_BYTES, verifiedDownload} from '../src/flasher.js';
export const catalog=JSON.parse(await readFile(new URL('../public/firmware/catalog.json',import.meta.url)));
export const oldCatalog=JSON.parse(await readFile(new URL('../public/firmware/0.10.1/catalog.json',import.meta.url)));
export const base=new URL('../public/',import.meta.url);
export const localFetch=async url=>({ok:true,arrayBuffer:async()=>{const b=await readFile(url);return b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);}});
export const images=await Promise.all(catalog.files.map(f=>verifiedDownload(f,base,localFetch)));
export const oldImages=await Promise.all(oldCatalog.files.map(f=>verifiedDownload(f,base,localFetch)));
export const md5=data=>createHash('md5').update(data).digest('hex');
export function fake({app=oldImages[3].data,chip='ESP32-S3',flashSize='8MB',partitions=images[1].data,boot=images[2].data}={}) {
  const l={writes:[],reads:[],capacityChecks:0,chip:{CHIP_NAME:chip},app:app.slice(),partitions:partitions.slice(),boot:boot.slice(),
    async detectFlashSize(){this.capacityChecks++;return flashSize;},
    async readFlash(address,size){
      this.reads.push({address,size});
      if(address===0x8000){assert.equal(size,this.partitions.length);return this.partitions.slice();}
      if(address===0xe000){assert.equal(size,this.boot.length);return this.boot.slice();}
      assert.equal(address,APP_OFFSET);assert.equal(size,APP_IDENTITY_BYTES);
      const data=new Uint8Array(size).fill(255);data.set(this.app.subarray(0,size));return data;
    },
    async flashMd5sum(address,size){assert.equal(address,APP_OFFSET);return md5(this.app.subarray(0,size));},
    async writeFlash(options){
      this.writes.push(options);
      for(const f of options.fileArray){
        if(f.address===APP_OFFSET)this.app=f.data.slice();
        if(f.address===0x8000)this.partitions=f.data.slice();
        if(f.address===0xe000)this.boot=f.data.slice();
      }
    },
    async main(){},async after(){}
  };
  return l;
}
export const opts=loader=>({loader,catalog,images,mode:'update',md5,reportProgress(){}});
