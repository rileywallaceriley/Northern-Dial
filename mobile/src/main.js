import './style.css';
import { App } from '@capacitor/app';
import { Browser } from '@capacitor/browser';
import { Capacitor } from '@capacitor/core';
import {getArtists,getPaths,getProfile,resolveArtist,request,NOW,key} from './content.js';
import {Radio} from './player.js';
const $ = s => document.querySelector(s);
function el(tag,text,cls) {const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
const radio=new Radio(); let artists=[],paths=[],history=[],song={},tab='listen',view=0,profileRequest=0,polling=false;
const screen=$('#screen'), dialog=$('#overlay');
function row(title,subtitle,action) {const n=el('button',undefined,'row');n.append(el('strong',title),el('span',subtitle));n.onclick=action;return n;}
function error(container,message,retry) {container.replaceChildren(el('p',message,'error'));if(retry){const b=el('button','Try again','quiet');b.onclick=retry;container.append(b);}}
async function directory(force=false) {if(!artists.length||force)artists=await getArtists();return artists;}
async function artistOverlay(artist) {
  const token=++profileRequest;const body=$('#overlay-body');body.replaceChildren(el('h2',artist.name));body.firstChild.id='overlay-title';body.append(el('p','Loading artist profile…','loading'));
  if(!dialog.open)dialog.showModal();
  try {const p=await getProfile(artist);if(token!==profileRequest||!dialog.open)return;body.replaceChildren(el('h2',p.name));body.firstChild.id='overlay-title';if(p.location)body.append(el('p',p.location,'location'));p.paragraphs.forEach(t=>body.append(el('p',t)));for(const l of p.links){const a=el('a',l.label);a.href=l.url;a.rel='noopener noreferrer';a.target='_blank';if(Capacitor.isNativePlatform())a.onclick=e=>{e.preventDefault();Browser.open({url:l.url});};body.append(a);}}
  catch(e){if(token===profileRequest&&dialog.open){body.replaceChildren(el('h2',artist.name));body.firstChild.id='overlay-title';const msg=el('div');body.append(msg);error(msg,e.message,()=>artistOverlay(artist));}}
}
$('#close').onclick=()=>dialog.close();dialog.addEventListener('close',()=>profileRequest++);
$('#now-artist').onclick=async()=>{try{await directory();const a=resolveArtist(song.artist,artists);await artistOverlay(a||{name:song.artist||'Northern Dial',summary:'We haven’t matched this broadcast credit to an artist profile yet. The music keeps playing.'});}catch{await artistOverlay({name:song.artist||'Northern Dial',summary:'Artist information is temporarily unavailable. Please try again shortly.'});}};
function historyRows(container) {container.replaceChildren();if(!history.length)container.append(el('p','Recent songs will appear when broadcast information is available.'));history.slice(0,5).forEach(h=>container.append(row(h.song?.title||'Unknown track',h.song?.artist||'Northern Dial',async()=>{try{await directory();const a=resolveArtist(h.song?.artist,artists);artistOverlay(a||{name:h.song?.artist||'Northern Dial'});}catch{artistOverlay({name:h.song?.artist||'Northern Dial'});}})));}
async function render(next=tab) {
  tab=next;const token=++view;screen.replaceChildren();document.querySelectorAll('[data-tab]').forEach(n=>{if(n.dataset.tab===tab)n.setAttribute('aria-current','page');else n.removeAttribute('aria-current');});
  if(tab==='listen') {
    screen.append(el('div','ALL KILLER. ALL CANCON.','eyebrow'));
    const h=el('h1');h.append(document.createTextNode('Stay curious.'));h.append(el('br'),el('em','Keep listening.'));screen.append(h,el('p','Independent Canadian radio. Familiar favourites, unexpected finds and the stories behind the music.','hero-copy'));
    const art=el('div',undefined,'dial-art');art.setAttribute('aria-hidden','true');art.append(el('div',undefined,'record'),el('span','TUNED TO THE NORTH / 24–7','dial-caption'));screen.append(art);
    const heading=el('div',undefined,'section-title');heading.append(el('h2','Fresh off the air'));screen.append(heading);const recent=el('div');recent.id='recent';screen.append(recent);historyRows(recent);
  } else if(tab==='artists') {
    screen.append(el('div','MEET YOUR NEXT FAVOURITE','eyebrow'),el('h1','The artists.'));
    const input=el('input',undefined,'search');input.type='search';input.placeholder='Find an artist';input.setAttribute('aria-label','Find an artist');const list=el('div');screen.append(input,list);list.append(el('p','Loading the Northern Dial directory…','loading'));
    try{await directory();if(token!==view)return;const paint=()=>{const filtered=artists.filter(a=>key(a.name).includes(key(input.value)));list.replaceChildren(el('p',`${filtered.length.toLocaleString()} artists`));filtered.slice(0,100).forEach(a=>list.append(row(a.name,a.summary? 'Read the story →':`${a.songs.length} songs in the library`,()=>artistOverlay(a))));if(filtered.length>100)list.append(el('p','Type a name to narrow these results.'));};input.oninput=paint;paint();}catch(e){if(token===view)error(list,e.message,()=>render());}
  } else {
    screen.append(el('div','FOLLOW THE CONNECTIONS','eyebrow'),el('h1','Listening paths.'),el('p','Follow the scenes, sounds and stories connecting Canadian artists. Your radio stays on.'));
    const list=el('div');screen.append(list);list.append(el('p','Loading listening paths…','loading'));
    try{paths=await getPaths();if(token!==view)return;list.replaceChildren();paths.forEach((p,i)=>{const b=el('button',undefined,'path-card');b.append(el('span',`PATH ${String(i+1).padStart(2,'0')} / ${p.artists.length} ARTISTS`,'number'),el('h2',p.title),el('p',p.dek),el('span','Explore this path ↗','quiet'));b.onclick=()=>pathView(p);list.append(b);});}catch(e){if(token===view)error(list,e.message,()=>render());}
  }
}
function pathView(path) {
  ++view;screen.replaceChildren();const back=el('button','← All listening paths','back');back.onclick=()=>render('paths');screen.append(back,el('h1',path.title),el('p',path.intro));
  path.artists.forEach((a,i)=>{const section=el('section',undefined,'path-step');section.append(el('p',String(i+1).padStart(2,'0'),'eyebrow'));const b=el('button',a.name+' ↗');b.onclick=async()=>{try{await directory();const match=resolveArtist(a.name,artists);artistOverlay(match||{name:a.name});}catch{artistOverlay({name:a.name});}};section.append(b,el('p',a.why_here));if(a.leads_to_next)section.append(el('p',a.leads_to_next,'connection'));screen.append(section);});window.scrollTo(0,0);
}
function paintPlayer(){const s=radio.state;$('#play').textContent=['playing','buffering'].includes(s)?'Ⅱ':'▶';$('#play').setAttribute('aria-label',['playing','buffering'].includes(s)?'Pause live radio':'Play live radio');$('#status').textContent=({playing:'LIVE FROM NORTHERN DIAL',buffering:'CONNECTING…',paused:'READY WHEN YOU ARE',error:'CONNECTION LOST · TAP PLAY TO RETRY'})[s]||s;document.body.classList.toggle('playing',s==='playing');}
radio.addEventListener('change',paintPlayer);$('#play').onclick=()=>['playing','buffering'].includes(radio.state)?radio.pause():radio.play();
async function poll(){if(polling)return;polling=true;try{const data=await request(NOW);song=data.now_playing?.song||{};history=Array.isArray(data.song_history)?data.song_history:[];$('#track').textContent=song.title||'Northern Dial';$('#artist').textContent=(song.artist||'Live Canadian radio')+' · About the artist ↗';await radio.metadata(song);if($('#recent'))historyRows($('#recent'));}catch{$('#artist').textContent=(song.artist||'Live Canadian radio')+' · Broadcast details temporarily unavailable';}finally{polling=false;}}
function resumeSync(){artists=[];poll();radio.refreshState();}
document.querySelectorAll('[data-tab]').forEach(n=>n.onclick=()=>{render(n.dataset.tab);window.scrollTo(0,0);});
window.addEventListener('hashchange',()=>{if(location.hash==='#listen')render('listen');});
document.addEventListener('visibilitychange',()=>{if(!document.hidden)resumeSync();});
App.addListener('appStateChange',({isActive})=>{if(isActive)resumeSync();});
App.addListener('backButton',()=>{if(dialog.open)dialog.close();else if(tab!=='listen')render('listen');else App.minimizeApp();});
radio.init().catch(()=>{radio.setState('error');$('#status').textContent='AUDIO SERVICE UNAVAILABLE';});
render();paintPlayer();poll();setInterval(()=>{if(!document.hidden)poll();},10000);
