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
  function prepare(artist) {
    return {...artist, key: normalize(artist.name), genres: artist.genres || [],
      eras: artist.eras || [], traits: artist.traits || [],
      primaryGenre: artist.primaryGenre || artist.genres?.[0] || ''};
  }
  function resolve(library, input, references = {}) {
    const key = normalize(input);
    if (!key) return {matched:false, genres:[], traits:[], excludedKey:'', source:''};
    const exact = library.find(a => a.key === key);
    const prefix = key.length >= 4 ? library.filter(a => a.key.startsWith(key)) : [];
    const artist = exact || (prefix.length === 1 ? prefix[0] : null);
    if (artist?.genres.length) return {...artist, matched:true, excludedKey:artist.key, source:artist.name};
    if (references[key]) return {matched:true, genres:references[key], primaryGenre:references[key][0], traits:[], excludedKey:key, source:input.trim()};
    return {matched:false, genres:[], traits:[], excludedKey:key, source:''};
  }
  function sharedTraits(artist, taste) {
    return artist.traits.filter(t => taste.traits?.includes(t));
  }
  function rank(library, {genre='', era='', taste={}, surprise=false} = {}) {
    const anchor = taste.matched ? taste.primaryGenre : '';
    const candidates = library.filter(a => a.key !== taste.excludedKey && a.track &&
      (!genre || a.genres.includes(genre)) && (!era || a.eras.includes(era)) &&
      (!anchor || a.primaryGenre === anchor));
    return candidates.map(artist => {
      const shared = sharedTraits(artist, taste);
      const score = shared.reduce((sum, t) => sum + (t === 'backburner' ? 40 : t === 'underground-rap' ? 4 : 12), 0)
        + (artist.bio ? 1 : 0);
      return {artist, score, random:surprise ? Math.random() : 0};
    }).sort((a,b) => surprise ? b.random-a.random : b.score-a.score || a.artist.name.localeCompare(b.artist.name))
      .slice(0,5).map(x => x.artist);
  }
  const api = {normalize, prepare, resolve, rank, sharedTraits, traitLabels:traits};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof window !== 'undefined') window.NDDiscoveryEngine = api;
})();
