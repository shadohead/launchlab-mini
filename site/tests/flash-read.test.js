import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {useVerifiedFlashReads} from '../src/flash-read.js';
const md5=data=>createHash('md5').update(data).digest('hex');
function stub(data){
  let queue=[],acked=0;
  const requests=[];
  const loader={IS_STUB:true,ESP_READ_FLASH:0xd2,requests,
    async checkCommand(description,command,bytes){
      assert.equal(queue.length,0,'previous digest must be consumed');
      assert.equal(command,0xd2);
      const view=new DataView(bytes.buffer);const words=Array.from({length:4},(_,i)=>view.getUint32(i*4,true));
      requests.push(words);assert.equal(words[1],data.length);assert.equal(words[2],256);assert.equal(words[3],1);
      acked=0;queue.push(data.slice(0,256));
    },
    transport:{async read(){assert.ok(queue.length);return queue.shift();},async write(bytes){
      const count=new DataView(bytes.buffer).getUint32(0,true);
      assert.equal(count,Math.min(acked+256,data.length));acked=count;
      queue.push(acked<data.length?data.slice(acked,acked+256):new Uint8Array(Buffer.from(md5(data),'hex')));
    }}
  };
  return useVerifiedFlashReads(loader,md5);
}
test('USB preflight reads small acknowledged packets, verifies and drains digest before next command',async()=>{
  for(const size of [1024,3072,8192,513]){
    const data=Uint8Array.from({length:size},(_,i)=>i%251),loader=stub(data);
    assert.deepEqual(await loader.readFlash(0x8000,size),data);
    assert.deepEqual(await loader.readFlash(0xe000,size),data);
    assert.equal(loader.requests.length,2);
  }
});
test('truncated, oversized, missing and corrupted read replies refuse inspection',async()=>{
  for(const packet of [new Uint8Array(0),new Uint8Array(255),new Uint8Array(257)]){
    const loader=stub(new Uint8Array(256));loader.transport.read=async()=>packet;
    await assert.rejects(loader.readFlash(0x8000,256),/packet/);
  }
  for(const digest of [new Uint8Array(0),new Uint8Array(16)]){
    const loader=stub(new Uint8Array(256));let count=0;
    loader.transport.read=async()=>++count===1?new Uint8Array(256):digest;
    await assert.rejects(loader.readFlash(0x8000,256),/checksum/);
  }
});
test('read timeout propagates and invalid range or missing stub sends no command',async()=>{
  const loader=stub(new Uint8Array(256));loader.transport.read=async()=>{throw new Error('USB read timed out');};
  await assert.rejects(loader.readFlash(0x8000,256),/timed out/);
  const guarded=stub(new Uint8Array(256));
  for(const [address,size] of [[-1,256],[0,0],[0,1.5],[8388600,256]])await assert.rejects(guarded.readFlash(address,size),/range/);
  guarded.IS_STUB=false;await assert.rejects(guarded.readFlash(0x8000,256),/stub/);assert.equal(guarded.requests.length,0);
});
