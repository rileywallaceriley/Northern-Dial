/* Northern Dial Mix beta: browser-local discovery collection. */
(() => {
  'use strict';
  if (window.NorthernDialMix) return;
  const KEY = 'nd.discovery.mix.v1';
  const LIMIT = 5;
  const french = location.pathname.startsWith('/fr/');
  const label = (en, fr) => french ? fr : en;
  const identity = track => `${track.artist.trim().toLowerCase()}\u0000${track.title.trim().toLowerCase()}`;
  const valid = t => t && typeof t.title === 'string' && typeof t.artist === 'string' && t.title.trim() && t.artist.trim();
  let tracks = [];
  try {
    const stored = JSON.parse(localStorage.getItem(KEY) || '[]');
    if (Array.isArray(stored)) tracks = stored.filter(valid).filter((t, i, a) => a.findIndex(x => identity(x) === identity(t)) === i).slice(0, LIMIT).map(t => ({title:t.title.slice(0,300),artist:t.artist.slice(0,300)}));
  } catch (_) { /* Storage is optional. */ }
  let tab, dialog, list, status, actions, opener, messageTimer, playerAdd;
  const button = (text, fn) => { const b = document.createElement('button'); b.type = 'button'; b.textContent = text; b.addEventListener('click', fn); return b; };
  function persist() {
    try { localStorage.setItem(KEY, JSON.stringify(tracks)); }
    catch (_) { announce(label('Saved for this page only. Browser storage is unavailable.', 'Enregistré pour cette page seulement. Le stockage est indisponible.')); }
  }
  function announce(message) { (dialog.open ? dialog : document.body).append(status); status.textContent = message; clearTimeout(messageTimer); messageTimer = setTimeout(() => { status.textContent = ''; }, 5000); }
  function searchUrl(t, service) {
    const query = encodeURIComponent(`${t.artist} ${t.title}`);
    return service === 'youtube' ? `https://www.youtube.com/results?search_query=${query}` : `https://open.spotify.com/search/${query}`;
  }
  function mixText() {
    return `${label('My Northern Dial Mix', 'Mon mix Northern Dial')}\n\n` + tracks.map((t, i) => `${i+1}. ${t.artist} - ${t.title}\n${label('Find on YouTube', 'Chercher sur YouTube')}: ${searchUrl(t, 'youtube')}\n${label('Find on Spotify', 'Chercher sur Spotify')}: ${searchUrl(t, 'spotify')}`).join('\n\n') + '\n\nhttps://www.northerndial.ca';
  }
  function sync() {
    if (!tab) return;
    tab.textContent = `${label('Your mix', 'Votre mix')} · ${tracks.length}/${LIMIT}`;
    list.replaceChildren();
    if (!tracks.length) {
      const p = document.createElement('p'); p.textContent = label('Your mix is empty. Tap + beside a song in Recently Played or the song library.', 'Votre mix est vide. Appuyez sur + à côté d’une chanson récemment jouée ou dans la bibliothèque.'); list.append(p);
    }
    tracks.forEach(t => {
      const row = document.createElement('li');
      const title = document.createElement('strong'); title.textContent = t.title;
      const artist = document.createElement('span'); artist.textContent = t.artist;
      const remove = button('×', () => { tracks = tracks.filter(x => identity(x) !== identity(t)); persist(); sync(); announce(label('Song removed.', 'Chanson retirée.')); });
      remove.setAttribute('aria-label', `${label('Remove', 'Retirer')} ${t.title}`); remove.className = 'nd-mix-remove';
      const links = document.createElement('div'); links.className = 'nd-mix-links';
      ['youtube', 'spotify'].forEach(service => { const a = document.createElement('a'); a.href = searchUrl(t,service); a.textContent = service === 'youtube' ? label('Find on YouTube', 'Chercher sur YouTube') : label('Find on Spotify', 'Chercher sur Spotify'); a.target = '_blank'; a.rel = 'noopener noreferrer'; links.append(a); });
      row.append(title, artist, remove, links); list.append(row);
    });
    actions.querySelectorAll('button').forEach(b => b.disabled = tracks.length === 0);
    document.querySelectorAll('.nd-mix-add').forEach(b => {
      const saved = tracks.some(t => identity(t) === b.dataset.mixKey);
      b.textContent = saved ? '✓' : '+';
      b.disabled = saved;
      b.setAttribute('aria-label', `${saved ? label('Saved to mix', 'Enregistré dans le mix') : label('Add to mix', 'Ajouter au mix')}: ${b.dataset.mixTitle}`);
      b.title = saved ? label('Saved to your mix', 'Enregistré dans votre mix') : label('Add to your mix', 'Ajouter à votre mix');
    });
    updatePlayerAdd();
    document.dispatchEvent(new CustomEvent('nd:mixchange'));
  }
  function add(track) {
    if (!valid(track)) return;
    if (tracks.some(t => identity(t) === identity(track))) return;
    if (tracks.length === LIMIT) { open(); announce(label('Your mix has five songs. Remove one to add another.', 'Votre mix contient cinq chansons. Retirez-en une pour en ajouter une autre.')); return; }
    tracks.push({title:track.title.slice(0,300), artist:track.artist.slice(0,300)});
    persist(); sync(); announce(label(`${track.title} added to your mix.`, `${track.title} ajouté à votre mix.`));
  }
  function open() { opener = document.activeElement; if (!dialog.open) dialog.showModal(); tab.setAttribute('aria-expanded', 'true'); }
  function attach(container, track) {
    if (!valid(track) || container.querySelector('.nd-mix-add')) return;
    const b = button('+', () => add(track)); b.className = 'nd-mix-add'; b.dataset.mixKey = identity(track); b.dataset.mixTitle = track.title;
    container.append(b);
  }
  function currentPlayerTrack() {
    const title = document.getElementById('songTitle')?.textContent.trim() || '';
    const artist = document.getElementById('artistName')?.textContent.trim() || '';
    if (!title || !artist || title === 'Northern Dial Radio' ||
        title === 'Unknown Track' || artist === 'All Killer, All CanCon' ||
        artist === 'Unknown Artist') return null;
    return { title, artist };
  }
  function updatePlayerAdd() {
    if (!playerAdd) return;
    const track = currentPlayerTrack();
    const saved = track && tracks.some(t => identity(t) === identity(track));
    playerAdd.textContent = saved ? '✓' : '+';
    playerAdd.disabled = !track || Boolean(saved);
    const description = !track
      ? label('Waiting for the current song', 'En attente de la chanson en cours')
      : saved
        ? label('Saved to your mix', 'Enregistré dans votre mix')
        : label('Add current song to your mix', 'Ajouter la chanson en cours à votre mix');
    playerAdd.title = description;
    playerAdd.setAttribute('aria-label', description + (track ? ': ' + track.artist + ' - ' + track.title : ''));
  }
  function initPlayerAdd() {
    const info = document.querySelector('.player-section .player-info');
    if (!info || document.getElementById('nd-player-mix-add')) return;
    playerAdd = button('+', () => {
      const track = currentPlayerTrack();
      if (track) add(track);
    });
    playerAdd.id = 'nd-player-mix-add';
    playerAdd.className = 'nd-mix-add nd-player-mix-add';
    info.insertAdjacentElement('afterend', playerAdd);
    const observer = new MutationObserver(updatePlayerAdd);
    ['songTitle', 'artistName'].forEach(id => {
      const el = document.getElementById(id);
      if (el) observer.observe(el, { childList: true, characterData: true, subtree: true });
    });
    updatePlayerAdd();
  }
  function scan() {
    document.querySelectorAll('#catalogGrid .album-card').forEach(card => attach(card, { title:card.querySelector('.album-title')?.textContent || '', artist:card.querySelector('.album-artist')?.textContent || '' }));
    document.querySelectorAll('#recentlyPlayed > div').forEach(row => {
      const info = Array.from(row.children).find(el => el.style.flex === '1 1 0%' || el.style.flex === '1' || (el.style.minWidth === '0px' && el.children.length >= 2));
      if (info) attach(row, {title:info.children[0]?.textContent || '', artist:info.children[1]?.textContent || ''});
    });
    sync();
  }
  function init() {
    const style = document.createElement('style');
    style.textContent = `
      #nd-mix-tab{position:fixed;right:14px;bottom:calc(96px + env(safe-area-inset-bottom));z-index:1100;border:2px solid #C33;border-radius:22px;background:#1a1a1a;color:white;padding:10px 15px;font:700 14px "Roboto Condensed",sans-serif;cursor:pointer;box-shadow:0 3px 14px #0003}
      .nd-mix-add{flex-shrink:0!important;min-width:36px;min-height:36px;width:36px;border:1px solid #C33;border-radius:50%;background:white;color:#8b2323;font:700 23px Arial;cursor:pointer;margin:8px 0 0 8px;vertical-align:middle}
      .player-controls .nd-player-mix-add{width:40px;min-width:40px;min-height:40px;height:40px;margin:0;align-self:center;background:transparent;color:#fff;border-color:#fff8;line-height:1;padding:0}.player-controls .nd-player-mix-add:hover:not(:disabled){background:#C33;border-color:#C33}.player-controls .nd-player-mix-add:disabled{color:#bbb;border-color:#777}
      #recentlyPlayed .nd-mix-add{margin:0}.nd-mix-add:disabled{color:#555;border-color:#777;cursor:default}
      #nd-mix-dialog{box-sizing:border-box;position:fixed;inset:0 0 0 auto;margin:0;width:min(420px,100vw);height:100dvh;max-height:100dvh;max-width:100vw;border:0;border-left:4px solid #C33;background:#F6F1E7;color:#1a1a1a;padding:24px;overflow:auto;font:16px/1.5 "Roboto Condensed",sans-serif}
      #nd-mix-dialog::backdrop{background:#0006}#nd-mix-dialog h2{margin:0;color:#8b2323;font-size:28px}#nd-mix-dialog .nd-mix-top{display:flex;justify-content:space-between;align-items:center;gap:12px}
      #nd-mix-dialog button{cursor:pointer;font:inherit;border:1px solid #1a1a1a;border-radius:6px;background:white;color:#1a1a1a;padding:8px 12px}#nd-mix-dialog button:disabled{opacity:.5;cursor:default}
      #nd-mix-dialog ol{padding:0;list-style:none}#nd-mix-dialog li{position:relative;padding:14px 42px 14px 0;border-bottom:1px solid #bbb}#nd-mix-dialog li strong,#nd-mix-dialog li span{display:block;overflow-wrap:anywhere}#nd-mix-dialog li span{color:#555}
      #nd-mix-dialog .nd-mix-remove{position:absolute;right:0;top:14px}.nd-mix-links{display:flex;gap:12px;flex-wrap:wrap;font-size:13px;margin-top:8px}.nd-mix-links a{color:#8b2323}
      #nd-mix-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:20px}#nd-mix-dialog .nd-mix-note{font-size:13px;color:#555}#nd-mix-status{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(145px + env(safe-area-inset-bottom));z-index:1200;background:#1a1a1a;color:white;border-radius:7px;padding:8px 12px;max-width:85vw;font:14px/1.4 Arial;pointer-events:none}#nd-mix-status:empty{display:none}
      #nd-mix-tab:focus-visible,.nd-mix-add:focus-visible,#nd-mix-dialog button:focus-visible,#nd-mix-dialog a:focus-visible{outline:3px solid #C33;outline-offset:3px}
      @media(max-width:600px){#nd-mix-dialog{inset:auto 0 0;height:auto;max-height:80dvh;width:100%;border-left:0;border-top:4px solid #C33;border-radius:16px 16px 0 0;padding:20px 18px calc(20px + env(safe-area-inset-bottom))}#nd-mix-tab{font-size:13px;padding:8px 12px}}
    `;
    document.head.append(style);
    tab = button('', open); tab.id = 'nd-mix-tab'; tab.setAttribute('aria-haspopup','dialog'); tab.setAttribute('aria-controls','nd-mix-dialog'); tab.setAttribute('aria-expanded','false');
    dialog = document.createElement('dialog'); dialog.id = 'nd-mix-dialog'; dialog.setAttribute('aria-labelledby','nd-mix-heading');
    const top = document.createElement('div'); top.className = 'nd-mix-top';
    const heading = document.createElement('h2'); heading.id = 'nd-mix-heading'; heading.textContent = label('Your mix · Beta', 'Votre mix · Bêta');
    const close = button('×', () => dialog.close()); close.setAttribute('aria-label',label('Close mix','Fermer le mix')); top.append(heading,close);
    const intro = document.createElement('p'); intro.textContent = label('Keep up to five discoveries and take your song list with you.', 'Gardez jusqu’à cinq découvertes et emportez votre liste de chansons.');
    list = document.createElement('ol');
    actions = document.createElement('div'); actions.id = 'nd-mix-actions';
    actions.append(button(label('Copy song list','Copier la liste'),async () => {
      try { await navigator.clipboard.writeText(mixText()); announce(label('Song list copied.','Liste copiée.')); }
      catch (_) { announce(label('Copy is unavailable. Download your list instead.','La copie est indisponible. Téléchargez votre liste.')); }
    }), button(label('Download list','Télécharger la liste'), () => { const url = URL.createObjectURL(new Blob([mixText()],{type:'text/plain;charset=utf-8'})); const a = document.createElement('a'); a.href=url; a.download='northern-dial-mix.txt'; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000); }), button(label('Email song list','Envoyer la liste par courriel'), () => { location.href = `mailto:?subject=${encodeURIComponent(label('My Northern Dial Mix','Mon mix Northern Dial'))}&body=${encodeURIComponent(mixText())}`; }));
    const note = document.createElement('p'); note.className = 'nd-mix-note'; note.textContent = label('Saved in this browser. Email opens your email app. Listening links search YouTube and Spotify; automatic YouTube playlist creation is not available in this beta yet.', 'Enregistré dans ce navigateur. Le courriel s’ouvre dans votre application de messagerie. Les liens recherchent sur YouTube et Spotify; la création automatique de playlists YouTube n’est pas encore disponible dans cette bêta.');
    dialog.append(top,intro,list,actions,note);
    status = document.createElement('div'); status.id='nd-mix-status'; status.setAttribute('role','status'); status.setAttribute('aria-live','polite');
    document.body.append(tab,dialog,status);
    dialog.addEventListener('close',()=>{tab.setAttribute('aria-expanded','false');if(opener?.isConnected)opener.focus();else tab.focus();});
    dialog.addEventListener('click',e=>{const r=dialog.getBoundingClientRect();if(e.target===dialog&&(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom))dialog.close();});
    let scheduled = false;
    const observer = new MutationObserver(records => { if (!records.some(r=>r.addedNodes.length && Array.from(r.addedNodes).some(n=>n.nodeType===1 && !n.classList?.contains('nd-mix-add')))) return; if(!scheduled){scheduled=true;queueMicrotask(()=>{scheduled=false;scan();});} });
    ['recentlyPlayed','catalogGrid'].forEach(id=>{const el=document.getElementById(id);if(el)observer.observe(el,{childList:true,subtree:true});});
    window.addEventListener('storage',e=>{if(e.key!==KEY)return;try{const value=JSON.parse(e.newValue||'[]');tracks=Array.isArray(value)?value.filter(valid).slice(0,LIMIT):[];sync();}catch(_){}});
    initPlayerAdd();
    scan();
    const deliveryScript = document.createElement('script');
    deliveryScript.src = '/nd-mix-email.js?v=20261008a';
    document.head.append(deliveryScript);
  }
  window.NorthernDialMix = {
    add,
    snapshot: () => tracks.map(t => ({...t})),
    complete: sent => {
      const keys = new Set(sent.map(identity));
      tracks = tracks.filter(t => !keys.has(identity(t)));
      persist(); sync();
    }
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
