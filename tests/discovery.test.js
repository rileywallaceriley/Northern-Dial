const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const engine = require('../discover-engine.js');
const library = JSON.parse(fs.readFileSync('discovery-data.json')).artists.map(engine.prepare);
const taste = engine.resolve(library, 'Wordburglar');
assert(taste.traits.includes('backburner'));
const picks = engine.rank(library, {taste});
assert.equal(picks.length, 5);
assert(!picks.some(a => a.name === 'The New Pornographers'));
assert(picks.slice(0,4).every(a => a.traits.includes('backburner')));
assert.deepEqual(engine.rank(library, {taste}), picks, 'Results must be stable');
assert.equal(engine.resolve(library, 'a').matched, false, 'Do not guess short artist names');
const constrained=engine.rank(library, {genre:'metal', taste});
assert(constrained.every(a => a.genres.includes('metal') && a.primaryGenre === 'hip-hop'), 'Honour both filters');
assert.equal(engine.rank(library.filter(a=>a.primaryGenre==='rock'), {taste}).length, 0, 'Do not backfill unrelated genres');
assert(!library.find(a => a.name === 'The New Pornographers').genres.includes('hip-hop'));
assert(!library.find(a => a.name === 'Wordburglar').genres.includes('pop'));
const choclair = engine.rank(library, {taste:engine.resolve(library,'Choclair')});
const daneo = engine.rank(library, {taste:engine.resolve(library,'Dan-e-o')});
assert.deepEqual(choclair.map(a=>a.name), ['Checkmate','Kardinal Offishall','Rascalz','Saukrates','Thrust']);
assert.deepEqual(daneo.map(a=>a.name), ['Grimace Love','Maestro Fresh Wes','Moka Only','Promise','Rich Kidd']);
assert(choclair.concat(daneo).every(a=>a.track));
assert(!library.some(a=>['Alice Ivy','6ix'].includes(a.name)));
assert.equal(engine.rank(library,{taste:{matched:true,primaryGenre:'hip-hop',genres:['hip-hop'],traits:[]}}).length,0);
assert.equal(engine.rank(library,{genre:'hip-hop'}).length,5,'Genre browsing remains available');
assert(choclair.every(a=>engine.connection(a,engine.resolve(library,'Choclair'))?.source));
console.log('Wordburglar picks:', picks.map(a => a.name).join(', '));

// Exercise the actual Discover renderer and click handler with a small DOM stub.
const elements = {};
function element(id) {
  return elements[id] ||= {value:'', textContent:'', innerHTML:'', disabled:false,
    classList:{add(){},remove(){}}, handlers:{},
    addEventListener(type,fn){this.handlers[type]=fn;}, scrollIntoView(){}};
}
let saved=[];
const document = {getElementById:element,querySelectorAll:()=>[],addEventListener(){},
  createElement:()=>({set textContent(value){this.innerHTML=String(value).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}})};
const context = {document, window:{NDDiscoveryEngine:engine,NorthernDialMix:{snapshot:()=>saved,add:t=>saved.push(t)}},
  fetch:async()=>({ok:true,json:async()=>({artists:library})}),console,setTimeout:()=>{}};
vm.createContext(context);
vm.runInContext(fs.readFileSync('discover.js','utf8'),context);
setImmediate(()=>{
  element('tasteInput').value='Wordburglar';
  element('discoverBtn').handlers.click();
  assert(element('resultsGrid').innerHTML.includes('Add song to mix'));
  assert(element('resultsGrid').innerHTML.includes('Backburner collective'));
  assert(!element('resultsGrid').innerHTML.includes('shares a hip-hop lane'));
  element('resultsGrid').handlers.click({target:{closest:()=>({dataset:{discoveryIndex:'0'}})}});
  assert.equal(saved[0].artist,picks[0].name);
  assert.equal(saved[0].title,picks[0].track);
  console.log('Ranking, filtering, explanation and Discover-to-mix checks passed.');
});
