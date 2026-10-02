import {ESPLoader, Transport} from 'esptool-js';
import SparkMD5 from 'spark-md5';
import {validateCatalog, verifiedDownload, flashVerified} from './flasher.js';
import './style.css';
const $ = id => document.getElementById(id);
let catalog, busy = false;
const supported = isSecureContext && 'serial' in navigator;
function log(message) { $('log').textContent += message + '\n'; $('log').scrollTop = $('log').scrollHeight; }
function status(message, state = '') { $('status').textContent = message; $('status').dataset.state = state; }
function updateControls() {
  $('flash').disabled = busy || !supported || !catalog || !$('board-confirm').checked || ($('mode').value === 'install' && !$('install-confirm').checked);
  $('install-warning').hidden = $('mode').value !== 'install';
  $('mode').disabled = busy;
  $('board-confirm').disabled = busy;
  $('install-confirm').disabled = busy;
  $('flash').textContent = busy ? 'Installing…' : ($('mode').value === 'install' ? 'Connect & install' : 'Connect & update');
}
if (!supported) { $('browser-note').hidden = false; status('Open this page in desktop Chrome or Edge to install over USB.'); }
for (const id of ['mode', 'board-confirm', 'install-confirm']) $(id).addEventListener('change', updateControls);
updateControls();
fetch(new URL('firmware/catalog.json', document.baseURI), {cache:'no-store'}).then(response => {
  if (!response.ok) throw new Error('Firmware catalog unavailable.');
  return response.json();
}).then(data => {
  catalog = validateCatalog(data);
  $('version').textContent = 'v' + catalog.version;
  $('checksum').textContent = catalog.files[3].sha256;
  if (supported) status('Ready when you are.');
  updateControls();
}).catch(error => status(error.message, 'error'));
let activeTransport;
window.addEventListener('beforeunload', event => { if (busy) {event.preventDefault(); event.returnValue = '';} });
$('flash').addEventListener('click', async () => {
  if ($('flash').disabled || busy) return;
  const mode = $('mode').value;
  busy = true; updateControls(); $('log').textContent = ''; $('details').open = true; $('progress').value = 0;
  let written = false;
  try {
    // Request the port while this click still supplies browser user activation.
    const port = await navigator.serial.requestPort({filters:[{usbVendorId:0x303a}]});
    status('Checking firmware downloads…');
    const images = await Promise.all(catalog.files.map(file => verifiedDownload(file, document.baseURI)));
    log('SHA-256 verified for every firmware file.');
    status('Connecting to your M5StickS3…');
    activeTransport = new Transport(port, true);
    const loader = new ESPLoader({transport:activeTransport, baudrate:115200, romBaudrate:115200, terminal:{clean(){}, writeLine:log, write:log}});
    await loader.main('no_reset');
    status('Installing firmware. Keep the USB cable connected.');
    const totalBytes = mode === 'update' ? images[3].size : images.reduce((sum,f)=>sum+f.size,0);
    const previous = [];
    await flashVerified({loader, catalog, images, mode, md5:data => SparkMD5.ArrayBuffer.hash(data.buffer.slice(data.byteOffset, data.byteOffset+data.byteLength)), reportProgress:(index, bytes, total) => {
      previous[index] = bytes;
      $('progress').value = Math.min(100, previous.reduce((sum,n)=>sum+(n||0),0)/totalBytes*100);
      status(`Installing firmware · ${Math.round($('progress').value)}%`);
    }});
    written = true; $('progress').value = 100;
    log('Flash completed and the device MD5 matched.');
    try { await loader.after('hard_reset'); status('Firmware installed. Your M5StickS3 is restarting.', 'success'); }
    catch { status('Firmware installed and verified. Press the side Power/Reset button to restart.', 'success'); }
  } catch (error) {
    if (error.name === 'NotFoundError') status('No device selected. You can try again.');
    else { status(written ? 'Firmware verified; restart the device manually.' : error.message, written ? 'success' : 'error'); log(error.stack || error.message); }
  } finally {
    if (activeTransport) { try {await activeTransport.disconnect();} catch {} activeTransport = null; }
    busy = false; updateControls();
  }
});
