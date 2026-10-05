import {compareVersions, validateCatalog} from './flasher.js';

export function validateReleaseIndex(index) {
  if (!Array.isArray(index.releases) || !index.releases.length || index.releases.length > 20) throw new Error('Firmware release list unavailable.');
  const seen = new Set();
  for (const release of index.releases) {
    compareVersions(release.version, release.version);
    if (seen.has(release.version) || release.catalog !== 'firmware/' + release.version + '/catalog.json') throw new Error('Invalid release selection.');
    seen.add(release.version);
  }
  if (!seen.has(index.latest) || index.releases.some(release=>compareVersions(release.version,index.latest)>0)) throw new Error('Recommended release mismatch.');
  return index;
}

export async function loadReleaseIndex(baseUrl, fetchFn=fetch) {
  const response=await fetchFn(new URL('firmware/versions.json',baseUrl),{cache:'no-store'});
  if (!response.ok) throw new Error('Firmware release list unavailable.');
  return validateReleaseIndex(await response.json());
}

// Invalidate the old catalog immediately. A slow response from an earlier
// selection must never enable a flash using the wrong release.
export function createReleaseSelection({index, baseUrl, fetchFn=fetch, onChange=()=>{}}) {
  validateReleaseIndex(index);
  let generation=0, state={loading:false,catalog:null,version:null,error:null};
  const set=next=>{state=next;onChange(state);};
  return {
    get state(){return state;},
    async select(version) {
      const request=++generation;
      set({loading:true,catalog:null,version,error:null});
      try {
        const release=index.releases.find(r=>r.version===version);
        if (!release) throw new Error('Unknown firmware release.');
        const response=await fetchFn(new URL(release.catalog,baseUrl),{cache:'no-store'});
        if (!response.ok) throw new Error('Selected firmware catalog unavailable.');
        const catalog=validateCatalog(await response.json());
        if (catalog.version!==version) throw new Error('Selected firmware version does not match its catalog.');
        if (request===generation) set({loading:false,catalog,version,error:null});
      } catch(error) {
        if (request===generation) set({loading:false,catalog:null,version,error});
      }
      return state;
    }
  };
}
