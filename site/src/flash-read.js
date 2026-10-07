// Stub READ_FLASH protocol: small packets, one outstanding ACK, then a raw MD5.
// https://docs.espressif.com/projects/esptool/en/latest/esp32s3/advanced-topics/serial-protocol.html#read-flash
// esptool-js 0.7.0 requests 4096-byte packets/1024 in flight and leaves the
// trailing digest unread. Bound USB bursts and consume/verify the entire reply.
export function useVerifiedFlashReads(loader, md5) {
  loader.readFlash=async(address,size)=>{
    if (!loader.IS_STUB) throw new Error('Flash inspection requires the connected stub loader.');
    if (!Number.isInteger(address)||address<0||!Number.isInteger(size)||size<=0||address+size>8388608) throw new Error('Invalid flash read range.');
    loader.info?.('Reading '+size+' bytes at 0x'+address.toString(16)+' for preflight…');
    const packetSize=256, timeout=5000;
    const words=(...values)=>{
      const bytes=new Uint8Array(values.length*4), view=new DataView(bytes.buffer);
      values.forEach((value,index)=>view.setUint32(index*4,value,true));return bytes;
    };
    await loader.checkCommand('read flash',loader.ESP_READ_FLASH,words(address,size,packetSize,1));
    const data=new Uint8Array(size);
    let received=0;
    while(received<size){
      const packet=await loader.transport.read(timeout);
      if (!(packet instanceof Uint8Array)||packet.length!==Math.min(packetSize,size-received)) throw new Error('Incomplete or oversized flash-read packet. No flash was written.');
      data.set(packet,received);received+=packet.length;
      await loader.transport.write(words(received));
    }
    const digest=await loader.transport.read(timeout);
    if (!(digest instanceof Uint8Array)||digest.length!==16) throw new Error('Missing flash-read checksum. No flash was written.');
    const hex=Array.from(digest,byte=>byte.toString(16).padStart(2,'0')).join('');
    if (md5(data)!==hex) throw new Error('Flash-read checksum mismatch. No flash was written.');
    loader.info?.('Flash read complete; checksum verified.');
    return data;
  };
  return loader;
}
