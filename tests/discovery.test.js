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
assert(constrained.every(a => a.genres.includes('metal')), 'Honour both filters');
assert.equal(engine.rank(library.filter(a=>a.primaryGenre==='rock'), {taste}).length, 0, 'Do not backfill unrelated genres');
assert(!library.find(a => a.name === 'The New Pornographers').genres.includes('hip-hop'));
assert(!library.find(a => a.name === 'Wordburglar').genres.includes('pop'));
const choclair = engine.rank(library, {taste:engine.resolve(library,'Choclair')});
const daneo = engine.rank(library, {taste:engine.resolve(library,'Dan-e-o')});
assert(choclair.some(a=>a.name==='Saukrates'));
assert(choclair.some(a=>a.name==='Solitair'));
assert(!choclair.some(a=>['3MFrench','6ix'].includes(a.name)));
assert.notDeepEqual(choclair.map(a=>a.name),daneo.map(a=>a.name));
assert(daneo.some(a=>a.name==='Grimace Love'));
assert(daneo.some(a=>a.name==='Promise'));
assert(choclair.concat(daneo).every(a=>a.track));
assert(!library.some(a=>['Alice Ivy','6ix'].includes(a.name)));
assert.equal(engine.rank(library,{taste:{matched:true,primaryGenre:'hip-hop',genres:['hip-hop'],traits:[]}}).length,0);
assert.equal(engine.rank(library,{genre:'hip-hop'}).length,5,'Genre browsing remains available');
assert(choclair.every(a=>engine.connection(a,engine.resolve(library,'Choclair'))?.source));
for(const name of ['jacksoul','Lia Pappas-Kemps','Alvvays','Peaches','Charlotte Day Wilson']) {
  const anchor=engine.resolve(library,name), results=engine.rank(library,{taste:anchor});
  assert.equal(results.length,5,`${name} needs useful results`);
  assert(results.every(a=>engine.evidence(a,anchor).supported));
  assert(results.every(a=>a.track));
  assert(!results.some(a=>a.name===name));
}
assert.equal(engine.resolve(library,'Choc-Clair').name,'Choclair');
assert.equal(engine.resolve(library,'DillanPonders/ BVB').name,'DillanPonders');
assert.equal(engine.resolve(library,'Not in catalogue/ Jazz Cartier').name,'Jazz Cartier');
assert(engine.rank(library,{taste:engine.resolve(library,'Lia Pappas-Kemps'),genre:'pop'}).length>=3);
const cdw=engine.resolve(library,'Charlotte Day Wilson');
assert(engine.connection(library.find(a=>a.name==='Daniel Caesar'),cdw).evidence.includes('collaborations'));
assert.equal(engine.rank(library,{taste:{...cdw,signals:[],connections:[],traits:[]}}).length,0,'No generic genre fallback');
console.log('Wordburglar picks:', picks.map(a => a.name).join(', '));

// Exercise the actual Discover renderer and click handler with a small DOM stub.
const elements = {};
function element(id) {
  return elements[id] ||= {value:'', textContent:'', innerHTML:'', disabled:false,
    classList:{add(){},remove(){}}, handlers:{},
    addEventListener(type,fn){this.handlers[type]=fn;}, scrollIntoView(options){this.scrollOptions=options;}};
}
let saved=[];
const document = {getElementById:element,querySelectorAll:()=>[],addEventListener(){},
  createElement:()=>({set textContent(value){this.innerHTML=String(value).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}})};
const context = {document, URLSearchParams,window:{location:{search:''},NDDiscoveryEngine:engine,NorthernDialMix:{snapshot:()=>saved,add:t=>saved.push(t)}},
  fetch:async()=>({ok:true,json:async()=>({artists:library})}),console,setTimeout:()=>{}};
vm.createContext(context);
vm.runInContext(fs.readFileSync('discover.js','utf8'),context);
setImmediate(()=>{
  element('tasteInput').value='Wordburglar';
  element('discoverBtn').handlers.click();
  assert(element('resultsGrid').innerHTML.includes('Add song to mix'));
  assert(element('resultsSummary').textContent.includes('starting from Wordburglar'));
  assert(element('resultsSummary').textContent.includes('Each card explains its link'));
  assert.equal(element('resultsSection').scrollOptions.block,'start');
  assert.equal(element('resultsSection').scrollOptions.behavior,'auto');
  assert(element('resultsGrid').innerHTML.includes('Backburner collective'));
  assert(!element('resultsGrid').innerHTML.includes('shares a hip-hop lane'));
  element('resultsGrid').handlers.click({target:{closest:()=>({dataset:{discoveryIndex:'0'}})}});
  assert.equal(saved[0].artist,picks[0].name);
  assert.equal(saved[0].title,picks[0].track);
  console.log('Ranking, filtering, explanation and Discover-to-mix checks passed.');
});

// Specific styles work across broad genres; stronger connections stay first.
const styleSignal={kind:'style',key:'cloud-pop',label:'cloud pop',evidence:'Makes cloud pop music.'};
const styleSeed=engine.prepare({name:'Seed',genres:['pop'],signals:[styleSignal],connections:[{artist:'Collaborator',kind:'profile'}],track:'Seed song'});
const styleCandidates=[
 engine.prepare({name:'Style neighbour',genres:['electronic-dance'],signals:[styleSignal],track:'Cloud song'}),
 engine.prepare({name:'Collaborator',genres:['pop'],track:'Collab song'}),
 engine.prepare({name:'Unrelated pop',genres:['pop'],track:'Other song'})
];
const stylePicks=engine.rank(styleCandidates,{taste:{...styleSeed,matched:true,excludedKey:styleSeed.key}});
assert.deepEqual(stylePicks.map(a=>a.name),['Collaborator','Style neighbour']);
assert.equal(engine.rank(styleCandidates,{genre:'pop',taste:{...styleSeed,matched:true,excludedKey:styleSeed.key}}).length,1);

// Canonical artist profiles prevent alias duplicates and recommending the seed itself.
const identities=library.map(a=>a.profileHref||a.key);
assert.equal(new Set(identities).size,library.length);
assert.equal(engine.resolve(library,'P. Reign').name,'P Reign');
const legacy=engine.prepare({...library.find(a=>a.name==='P Reign'),name:'P. Reign'});
const drake=engine.resolve(library,'Drake');
const aliasPicks=engine.rank([...library,legacy],{taste:drake});
assert.equal(aliasPicks.filter(a=>a.profileHref==='./artists/p-reign.html').length,1);
assert(!engine.rank([...library,legacy],{taste:engine.resolve(library,'P Reign')}).some(a=>a.profileHref===legacy.profileHref));
for(const artist of library){
 assert(!(artist.connections||[]).some(c=>c.artist===artist.name));
 const results=engine.rank(library,{taste:engine.resolve(library,artist.name)});
 assert.equal(new Set(results.map(a=>a.profileHref||a.key)).size,results.length);
}

// Different profile paths, alternate credits and URL formats still identify the same artist.
for(const alias of ['Nish','Nish Rawks','Nish Rawwks'])assert.equal(engine.resolve(library,alias).name,'Nish Raawks');
assert.equal(engine.resolve(library,'Mayhem Moreaty').name,'Mayhem Morearty');
const nish=engine.resolve(library,'Nish');
const alternate=engine.prepare({...nish,name:'Nish Rawwks',profileHref:'/artists/nish-rawwks.html',aliases:[],connections:[]});
assert(engine.sameArtist(nish,alternate));
assert.equal(engine.connection(alternate,{...nish,connections:[{artist:alternate.name}]}),undefined);
assert(!engine.rank([...library,alternate],{taste:nish}).some(a=>engine.sameArtist(a,nish)));
assert(engine.sameArtist({name:'A',profileHref:'./artists/test.html'},{name:'B',profileHref:'https://www.northerndial.ca/artists/test.html?x=1'}));
for(const artist of library){
 const results=engine.rank(library,{taste:engine.resolve(library,artist.name)});
 assert(!results.some(a=>engine.sameArtist(a,artist)),`Self recommendation: ${artist.name}`);
 for(let i=0;i<results.length;i++)assert(!results.slice(i+1).some(a=>engine.sameArtist(a,results[i])));
}
