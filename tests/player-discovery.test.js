const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const calls = [];
function el() { return {textContent:'',style:{},children:[],handlers:{},attrs:{},dataset:{},addEventListener(t,f){this.handlers[t]=f;},setAttribute(k,v){this.attrs[k]=v;},append(b){this.children.push(b);},insertAdjacentElement(_,b){this.children.push(b);},querySelector(selector){return this.children.find(b=>b.className?.split(' ').includes(selector.slice(1))) || null;}}; }
const info=el(),row=el(),title=el(),artist=el();title.textContent='First song';artist.textContent='Dan-e-o';
const document={readyState:'loading',addEventListener(){},createElement:el,getElementById(id){return {songTitle:title,artistName:artist}[id]||null;},querySelector(){return info;}};
const context={window:{NDPlayer:{discoverArtist:a=>calls.push(a)}},location:{pathname:'/',assign:u=>calls.push(u)},localStorage:{getItem:()=>null},document,MutationObserver:class {observe(){}}};
vm.createContext(context);
const mix=fs.readFileSync('nd-mix.js','utf8').replace("if(document.readyState==='loading')", "window.test={attachDiscover,initPlayerAdd,updatePlayerAdd}; if(document.readyState==='loading')");
vm.runInContext(mix,context);
context.window.test.initPlayerAdd();
const brain=info.children[0].children[0]; // inserted after the + button
assert.equal(brain.textContent,'🧠');assert(!brain.className.split(' ').includes('nd-mix-add'));
brain.handlers.click({stopPropagation(){}});assert.equal(calls.pop(),'Dan-e-o');
artist.textContent='Choclair';context.window.test.updatePlayerAdd();brain.handlers.click({stopPropagation(){}});assert.equal(calls.pop(),'Choclair');
context.window.test.attachDiscover(row,{title:'Earlier song',artist:'Wordburglar'});
context.window.test.attachDiscover(row,{title:'Earlier song',artist:'Wordburglar'});
assert.equal(row.children.length,1);row.children[0].handlers.click({stopPropagation(){}});assert.equal(calls.pop(),'Wordburglar');
artist.textContent='Unknown Artist';context.window.test.updatePlayerAdd();assert.equal(brain.disabled,true);
// Discover must prefill and rank once after its asynchronous catalogue load.
const elements={};const get=id=>elements[id] ||= {...el(),value:'',disabled:true,classList:{add(){},remove(){}},scrollIntoView(){}};
let ranks=0;
const discoverContext={window:{location:{search:'?artist=Dan-e-o'},NDDiscoveryEngine:{prepare:a=>a,resolve:(_,name)=>({matched:true,source:name}),rank:()=>{ranks++;return [];}}},URLSearchParams,document:{getElementById:get,addEventListener(){},querySelectorAll:()=>[],createElement:()=>({set textContent(v){this.innerHTML=String(v);}})},fetch:async()=>({ok:true,json:async()=>({artists:Array.from({length:5},(_,i)=>({name:'Artist '+i,genres:[]}))})}),console,setTimeout(){}};
vm.createContext(discoverContext);vm.runInContext(fs.readFileSync('discover.js','utf8'),discoverContext);
setImmediate(()=>{assert.equal(get('tasteInput').value,'Dan-e-o');assert.equal(ranks,1);assert.match(get('status').textContent,/No documented matches/);console.log('Player, recent-row identity, unknown metadata, duplicate prevention and automatic Discover search checks passed.');});
