export const SITE = 'https://www.northerndial.ca';
export const STREAM = 'https://a10.asurahosting.com:7220/radio.mp3';
export const NOW = 'https://a10.asurahosting.com/api/nowplaying/northern_dial';
export const key = value => String(value || '').normalize('NFKC').toLocaleLowerCase('en-CA').replace(/\s+/g, ' ').trim();
export function safeURL(value, base = SITE) {
  try { const u = new URL(value, base); return u.protocol === 'https:' && !u.username && !u.password ? u.href : null; } catch { return null; }
}
export function parseDirectory(html) {
  const doc = new DOMParser().parseFromString(html, 'text/html');
  const records = [];
  for (const details of doc.querySelectorAll('details')) {
    const summary = details.querySelector('summary');
    if (!summary?.querySelector('.artist-meta')) continue;
    const clone = summary.cloneNode(true);
    clone.querySelectorAll('.artist-meta').forEach(n => n.remove());
    const name = clone.textContent.trim();
    const link = summary.querySelector('a.artist-page-link');
    const url = link ? safeURL(link.getAttribute('href')) : null;
    records.push({name, url: url?.startsWith(SITE + '/artists/') ? url : null,
      summary: details.querySelector('.profile-bio')?.textContent.trim() || '',
      songs: [...details.querySelectorAll('.track-title')].map(n => n.textContent.trim())});
  }
  if (!records.length) throw new Error('Artist directory is temporarily unavailable.');
  return records;
}
export function parseProfile(html) {
  const doc = new DOMParser().parseFromString(html, 'text/html');
  const name = doc.querySelector('main article h1')?.textContent.trim();
  const paragraphs = [...doc.querySelectorAll('main article .bio')].map(n => n.textContent.trim());
  if (!name || !paragraphs.length) throw new Error('This artist profile is still being prepared.');
  const links = [...doc.querySelectorAll('.official-links a, .sources a')].map(a => ({label:a.textContent.trim(),url:safeURL(a.getAttribute('href'))})).filter(a => a.url);
  return {name, paragraphs, location:doc.querySelector('main article .location')?.textContent.trim(), links};
}
export function resolveArtist(credit, artists) {
  // Exact full-credit match first: never split names such as Earth, Wind & Fire.
  const exact = artists.filter(a => key(a.name) === key(credit));
  if (exact.length === 1) return exact[0];
  if (exact.length > 1) return null;
  const lead = String(credit).split(/\s+(?:feat\.?|ft\.?|featuring)\s+/i)[0];
  const matches = artists.filter(a => key(a.name) === key(lead));
  return matches.length === 1 ? matches[0] : null;
}
export async function request(url, type = 'json') {
  const r = await fetch(url, {signal:AbortSignal.timeout(12000), cache:'no-cache'});
  if (!r.ok) throw new Error(`Unable to load content (${r.status}).`);
  return type === 'text' ? r.text() : r.json();
}
export async function getArtists() { return parseDirectory(await request(SITE + '/artists.html','text')); }
export async function getProfile(artist) {
  if (!artist.url) return {name:artist.name,paragraphs:[artist.summary || 'A full profile is being prepared. Keep exploring while you listen.'],links:[]};
  return parseProfile(await request(artist.url,'text'));
}
export async function getPaths() {
  const data = await request(SITE + '/listening_paths.json');
  return Object.entries(data).filter(([,p]) => p && typeof p.title === 'string' && Array.isArray(p.artists)).map(([id,p]) => ({...p,id}));
}
