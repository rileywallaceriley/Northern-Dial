import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import {parseDirectory,parseProfile,resolveArtist,safeURL} from '../src/content.js';
globalThis.DOMParser = new JSDOM('').window.DOMParser;
test('parses the actual published directory and preserves artist identity',()=>{
  const records=parseDirectory(readFileSync('../artists.html','utf8'));
  assert.ok(records.length>100);
  const artist=resolveArtist('k-os',records);
  assert.ok(artist);assert.equal(artist.url,'https://www.northerndial.ca/artists/k-os.html');
  assert.equal(resolveArtist('k-os feat. Another Artist',records),artist);
});
test('reads real profile paragraphs without executing fetched markup',()=>{
  const profile=parseProfile(readFileSync('../artists/k-os.html','utf8'));
  assert.equal(profile.name,'k-os');assert.ok(profile.paragraphs.length>=2);
  assert.ok(profile.paragraphs[0].includes('Exit'));assert.ok(!profile.paragraphs[0].includes('<em>'));
});
test('does not guess ambiguous or compound artist credits',()=>{
  const a={name:'Earth, Wind & Fire'};assert.equal(resolveArtist(a.name,[a]),a);
  assert.equal(resolveArtist('Same',[{name:'Same'},{name:'same'}]),null);
  assert.equal(resolveArtist('One & Two',[{name:'One'},{name:'Two'}]),null);
});
test('rejects unsafe URLs and wrong page templates',()=>{
  for(const url of ['javascript:alert(1)','http://example.com','https://user:pass@example.com'])assert.equal(safeURL(url),null);
  assert.throws(()=>parseProfile('<h1>Not an artist</h1>'));
  assert.throws(()=>parseDirectory('<html>Unavailable</html>'));
});
