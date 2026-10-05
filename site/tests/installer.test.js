import test from 'node:test';
import assert from 'node:assert/strict';
import {createInstaller} from '../src/installer.js';
import {catalog,oldCatalog,base,localFetch,fake,md5,images} from './helpers.js';
function setup({loader=fake(),requestPort=async()=>({}),fetchFn=localFetch,disconnect=async()=>{}}={}) {
  const state={choosers:0,opens:0,closes:0,busy:[],statuses:[]};
  const installer=createInstaller({baseUrl:base,md5,fetchFn,
    requestPort:async()=>{state.choosers++;return requestPort();},
    openConnection:async()=>{state.opens++;return {loader,transport:{disconnect:async()=>{state.closes++;await disconnect();}}};},
    onBusy:b=>state.busy.push(b),onStatus:(message,result)=>state.statuses.push({message,result})});
  return {installer,state,loader};
}
test('cancelled chooser resets busy and does not open a device',async()=>{
  const s=setup({requestPort:async()=>{throw Object.assign(new Error('cancelled'),{name:'NotFoundError'});}});
  assert.equal((await s.installer.run({catalog,mode:'update'})).status,'cancelled');
  assert.equal(s.state.opens,0);assert.equal(s.installer.busy,false);assert.deepEqual(s.state.busy,[true,false]);
});
test('download failure does not open USB and a subsequent attempt starts cleanly',async()=>{
  let fail=true;const s=setup({fetchFn:async url=>fail?{ok:false,status:503}:localFetch(url)});
  assert.equal((await s.installer.run({catalog,mode:'update'})).status,'error');assert.equal(s.state.opens,0);
  fail=false;assert.equal((await s.installer.run({catalog,mode:'update'})).status,'verified');assert.equal(s.state.closes,1);
});
test('double clicks cannot start another chooser or overlapping write',async()=>{
  let choose;const s=setup({requestPort:()=>new Promise(resolve=>{choose=resolve;})});
  const first=s.installer.run({catalog,mode:'update'});assert.equal(s.installer.busy,true);
  assert.equal((await s.installer.run({catalog,mode:'update'})).status,'busy');assert.equal(s.state.choosers,1);
  choose({});assert.equal((await first).status,'verified');assert.equal(s.loader.writes.length,1);assert.equal(s.installer.busy,false);
});
test('connection failure closes transport and allows a fresh retry',async()=>{
  const l=fake();let fail=true;l.main=async()=>{if(fail)throw new Error('connection lost');};const s=setup({loader:l});
  assert.equal((await s.installer.run({catalog,mode:'update'})).status,'error');assert.equal(s.state.closes,1);assert.equal(l.writes.length,0);
  fail=false;assert.equal((await s.installer.run({catalog,mode:'update'})).status,'verified');assert.equal(s.state.closes,2);
});
test('write interruption is never reported as success; repair retry closes each connection',async()=>{
  const l=fake();const write=l.writeFlash;let fail=true;
  l.writeFlash=async function(o){await write.call(this,o);if(fail){this.app[10000]^=1;throw new Error('USB disconnected mid-write');}};
  const s=setup({loader:l});const interrupted=await s.installer.run({catalog,mode:'update'});
  assert.equal(interrupted.status,'error');assert.equal(s.state.closes,1);assert.equal(s.installer.busy,false);
  fail=false;assert.equal((await s.installer.run({catalog,mode:'update'})).status,'error');
  assert.equal((await s.installer.run({catalog,mode:'recovery',recoveryConfirmed:true})).status,'verified');
  assert.equal((await s.installer.run({catalog,mode:'update'})).status,'up-to-date');assert.equal(l.writes.length,2);assert.equal(s.state.closes,4);
});
test('reset failure after verified write requests manual restart and keeps success evidence',async()=>{
  const l=fake();l.after=async()=>{throw new Error('reset unavailable');};const s=setup({loader:l});
  const result=await s.installer.run({catalog,mode:'update'});assert.equal(result.status,'verified');assert.equal(result.restarted,false);
  assert.match(s.state.statuses.at(-1).message,/Power\/Reset/);assert.equal(s.state.statuses.at(-1).result,'success');assert.equal(s.state.closes,1);
});
test('older selected release is blocked end-to-end before write',async()=>{
  const s=setup({loader:fake({app:images[3].data})});const result=await s.installer.run({catalog:oldCatalog,mode:'update'});
  assert.equal(result.status,'error');assert.match(result.error.message,/Downgrade blocked/);assert.equal(s.loader.writes.length,0);assert.equal(s.state.closes,1);
});
test('missing explicit repair or first-install consent stops before chooser',async()=>{
  for(const mode of ['install','recovery']){const s=setup();assert.equal((await s.installer.run({catalog,mode})).status,'error');assert.equal(s.state.choosers,0);}
});
test('disconnect failure cannot retain busy state or trigger another write',async()=>{
  const s=setup({disconnect:async()=>{throw new Error('already unplugged');}});
  assert.equal((await s.installer.run({catalog,mode:'update'})).status,'verified');assert.equal(s.installer.busy,false);
  assert.equal((await s.installer.run({catalog,mode:'update'})).status,'up-to-date');assert.equal(s.loader.writes.length,1);
});
