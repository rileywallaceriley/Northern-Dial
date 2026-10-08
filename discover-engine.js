/* Evidence-based ranking. No demographic features or random similarity claims. */
(() => {
  const normalize = value => String(value || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[’‘]/g, "'").trim();
  const traits = {
    backburner: 'the Backburner collective', wordplay: 'wordplay-focused lyricism',
    humour: 'humour in the writing', 'underground-rap': 'underground hip-hop',
    'boom-bap': 'boom-bap production', storytelling: 'personal storytelling',
    turntablism: 'turntablism', 'abstract-rap': 'abstract or experimental rap',
    'neo-soul': 'neo-soul', 'trip-hop': 'trip-hop', downtempo: 'downtempo textures',
    shoegaze: 'shoegaze', 'dream-pop': 'dream pop', 'power-pop': 'power pop',
    'post-punk': 'post-punk', 'synth-pop': 'synth-pop', house: 'house music',
    techno: 'techno', 'pop-punk': 'pop-punk', 'post-hardcore': 'post-hardcore',
    'folk-rock': 'folk rock'
  };
  const nameIdentity = name => normalize(name).replace(/[^a-z0-9]/g,'');
  const profileIdentity = href => String(href||'').replace(/^https?:\/\/[^/]+/,'').replace(/^\.\//,'/').split(/[?#]/)[0].replace(/\/$/,'');
  function sameArtist(a,b) {
    if(a.artistId && b.artistId && a.artistId===b.artistId)return true;
    const names = x => x._identityNames || [x.name,x.key,x.excludedKey,...(x.aliases||[])].filter(Boolean).map(nameIdentity);
    const profiles = x => x._identityProfiles || [x.profileHref,...(x.profileAliases||[])].filter(Boolean).map(profileIdentity);
    return names(a).some(n=>names(b).includes(n)) || profiles(a).some(p=>profiles(b).includes(p));
  }
  function prepare(artist) {
    return {...artist, _identityNames:[artist.name,...(artist.aliases||[])].filter(Boolean).map(nameIdentity),
      _identityProfiles:[artist.profileHref,...(artist.profileAliases||[])].filter(Boolean).map(profileIdentity),
      key: normalize(artist.name), genres: artist.genres || [],
      eras: artist.eras || [], traits: artist.traits || [],
      primaryGenre: artist.primaryGenre || artist.genres?.[0] || ''};
  }
  function resolve(library, input, references = {}) {
    const key = normalize(input);
    if (!key) return {matched:false, genres:[], traits:[], excludedKey:'', source:''};
    const exact = library.find(a => a.key === key || (a.aliases||[]).some(n=>normalize(n)===key));
    const compact = key.replace(/([a-z])[-\s]\1/g,'$1').replace(/[^a-z0-9]/g,'');
    const aliases = compact.length>=4 ? library.filter(a=>a.key.replace(/[^a-z0-9]/g,'')===compact) : [];
    const credits = key.split(/\s*(?:,|\/|&|\bfeat\.?|\bft\.?)\s*/);
    const credited = credits.length>1 ? credits.map(c=>library.find(a=>a.key===c || a.key.replace(/[^a-z0-9]/g,'')===c.replace(/[^a-z0-9]/g,''))).find(Boolean) : null;
    const prefix = key.length >= 4 ? library.filter(a => a.key.startsWith(key)) : [];
    const artist = exact || (aliases.length===1?aliases[0]:null) || credited || (prefix.length === 1 ? prefix[0] : null);
    if (artist) return {...artist, matched:true, excludedKey:artist.key, source:artist.name};
    if (references[key]) return {matched:true, genres:references[key], primaryGenre:references[key][0], traits:[], excludedKey:key, source:input.trim()};
    return {matched:false, genres:[], traits:[], excludedKey:key, source:''};
  }
  function sharedTraits(artist, taste) {
    return artist.traits.filter(t => taste.traits?.includes(t));
  }
  function connection(artist,taste){if(sameArtist(artist,taste))return undefined;return (taste.connections||[]).find(c=>normalize(c.artist)===artist.key);}
  function evidence(artist,taste) {
    const shared=(artist.signals||[]).filter(a=>(taste.signals||[]).some(t=>a.kind===t.kind && a.key===t.key));
    const styles=shared.filter(s=>s.kind==='style');
    const scenes=shared.filter(s=>s.kind==='scene');
    const eras=shared.filter(s=>s.kind==='era');
    const genres=artist.genres.filter(g=>taste.genres?.includes(g));
    const sharedTrait=sharedTraits(artist,taste);
    const link=connection(artist,taste);
    const specificStyles=styles.filter(s=>!['singer-songwriter','soul-pop'].includes(s.key));
    const soulPop=styles.some(s=>s.key==='soul-pop') && artist.primaryGenre===taste.primaryGenre;
    const seedSpecific=(taste.signals||[]).some(s=>s.kind==='style' && !['singer-songwriter','soul-pop','adult-rnb'].includes(s.key));
    // A documented specific style is enough, even across broad genre buckets.
    const supported=Boolean(link) || specificStyles.length>0 || (genres.length>0 && (soulPop || sharedTrait.some(t=>t!=='underground-rap')))
      || (!seedSpecific && artist.primaryGenre===taste.primaryGenre && genres.length>0 && scenes.length>0 && eras.length>0)
      || (taste.genres?.length===2 && genres.length===2 && artist.primaryGenre===taste.primaryGenre);
    return {link,styles,specificStyles,scenes,eras,genres,sharedTrait,supported};
  }
  function rank(library, {genre='', era='', taste={}, surprise=false} = {}) {
    const seen = [];
    const candidates = library.filter(a => !sameArtist(a,taste) && a.track &&
      (!genre || a.genres.includes(genre)) && (!era || a.eras.includes(era)));
    return candidates.map(artist => {
      const match=evidence(artist,taste);
      const production = match.link && /produced|producer.*records by|records by/.test((match.link.reason||'')+' '+(match.link.evidence||''));
      const score=(match.link?(production?1350:match.link.kind==='profile'?1050:1200):0)+match.styles.reduce((n,s)=>n+(s.key==='singer-songwriter'?5:s.key==='soul-pop'?8:25),0)
        +match.scenes.length*3+match.eras.length*20+match.genres.length*3
        +match.sharedTrait.reduce((n,t)=>n+(t==='backburner'?100:t==='underground-rap'?1:20),0);
      const tier=match.link?3:match.specificStyles.length || match.sharedTrait.some(t=>!['underground-rap'].includes(t))?2:1;
      return {artist, score, tier, supported:match.supported, random:surprise ? Math.random() : 0};
    }).filter(x => !taste.matched || x.supported).sort((a,b) => surprise ? b.random-a.random : b.tier-a.tier || b.score-a.score || a.artist.name.localeCompare(b.artist.name))
      .filter(x => {if(seen.some(a=>sameArtist(a,x.artist)))return false;seen.push(x.artist);return true;})
      .slice(0,5).map(x => x.artist);
  }
  const api = {normalize, sameArtist, prepare, resolve, rank, evidence, connection, sharedTraits, traitLabels:traits};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof window !== 'undefined') window.NDDiscoveryEngine = api;
})();
