import {validateCatalog, verifiedDownload, flashVerified} from './flasher.js';

// One attempt owns its connection. Always release it before allowing a retry.
// Callbacks keep this flow testable without opening a browser or a USB port.
export function createInstaller({baseUrl, requestPort, openConnection, md5, fetchFn=fetch, onBusy=()=>{}, onStatus=()=>{}, onLog=()=>{}, onProgress=()=>{}, onInspect=()=>{}}) {
  let busy=false;
  return {
    get busy(){return busy;},
    async run({catalog,mode,recoveryConfirmed=false,installConfirmed=false}) {
      if (busy) return {status:'busy'};
      busy=true;onBusy(true);
      let connection;
      try {
        validateCatalog(catalog);
        if (!['update','install','recovery'].includes(mode)) throw new Error('Unknown install mode.');
        if (mode==='install' && installConfirmed!==true) throw new Error('Confirm first install and backup before continuing.');
        if (mode==='recovery' && recoveryConfirmed!==true) throw new Error('Confirm intentional repair or downgrade and backup before continuing.');
        // The chooser is requested directly during the initiating click.
        const port=await requestPort();
        onStatus('Checking v'+catalog.version+' downloads…');
        const images=await Promise.all(catalog.files.map(file=>verifiedDownload(file,baseUrl,fetchFn)));
        onLog('SHA-256 verified for every firmware file. Selected v'+catalog.version+'.');
        onStatus('Connecting and checking the installed application…');
        connection=await openConnection(port);
        await connection.loader.main('no_reset');
        const totalBytes=mode==='install'?images.reduce((sum,f)=>sum+f.size,0):images[3].size;
        const previous=[];
        const result=await flashVerified({loader:connection.loader,catalog,images,mode,recoveryConfirmed,installConfirmed,md5,onInspect,reportProgress:(index,bytes)=>{
          previous[index]=bytes;
          const percent=Math.min(100,previous.reduce((sum,n)=>sum+(n||0),0)/totalBytes*100);
          onProgress(percent);onStatus('Installing v'+catalog.version+' · '+Math.round(percent)+'%. Keep USB connected.');
        }});
        onProgress(100);
        onLog(result.status==='up-to-date'?'Installed v'+catalog.version+' matches the complete archived application. No write needed.':'Application write completed and device MD5 matched.');
        let restarted=false;
        try {await connection.loader.after('hard_reset');restarted=true;} catch { /* Verified bytes; manual restart is sufficient. */ }
        const message=result.status==='up-to-date'?'Already on verified v'+catalog.version+'. No flash was written.':'v'+catalog.version+' installed and verified.';
        onStatus(message+(restarted?' Restarting.':' Press the side Power/Reset button to restart.'),'success');
        return {...result,restarted};
      } catch(error) {
        if (error.name==='NotFoundError') {onStatus('No device selected. You can try again.');return {status:'cancelled'};}
        onStatus(error.message,'error');onLog(error.stack||error.message);
        return {status:'error',error};
      } finally {
        if (connection) {try {await connection.transport.disconnect();} catch {}}
        busy=false;onBusy(false);
      }
    }
  };
}
