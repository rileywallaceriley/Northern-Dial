const $=id=>document.getElementById(id);
    const normalize=value=>String(value||"").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[’‘]/g,"'").trim();
    const GENRES={
      "hip-hop":{label:"Hip-Hop",terms:["hip-hop","hip hop","rapper"," rap ","rap.","rap,","boom bap","trap","drill","emcee"]},
      "rnb-soul":{label:"R&B / Soul",terms:["r&b","rnb","rhythm and blues","neo-soul","neo soul","soul","soulful"]},
      "pop":{label:"Pop",terms:[" pop ","synth-pop","synthpop","dance-pop","art-pop","electropop","dream pop","indie-pop","indie pop","scandi-pop"]},
      "rock":{label:"Rock",terms:[" rock ","garage rock","hard rock","classic rock","post-rock","rockabilly"]},
      "indie-alternative":{label:"Indie / Alternative",terms:["indie","alternative","alt-","shoegaze","post-punk","new wave","dream pop","art rock","experimental"]},
      "electronic-dance":{label:"Electronic / Dance",terms:["electronic","electronica","house","techno"," dance ","club","edm","ambient","trip-hop","trip hop","downtempo","synth"]},
      "folk-songwriter":{label:"Folk / Singer-Songwriter",terms:["folk","singer-songwriter","singer songwriter","acoustic","roots music"]},
      "country-americana":{label:"Country / Americana",terms:["country","americana","alt-country","bluegrass","honky tonk"]},
      "jazz":{label:"Jazz",terms:["jazz","bebop","improvisation","improvised music"]},
      "punk-hardcore":{label:"Punk / Hardcore",terms:["punk","hardcore","post-hardcore","emo","ska punk"]},
      "metal":{label:"Metal",terms:["metal","doom","black metal","death metal","thrash","sludge","metalcore"]},
      "reggae-dancehall":{label:"Reggae / Dancehall",terms:["reggae","dancehall","dub","soca","caribbean"]}
    };
    const ERA_LABELS={"2020s":"2020s","2010s":"2010s","2000s":"2000s","1990s":"1990s","pre-1990":"1980s and earlier"};
    const REFERENCE_TASTES={"vibi":["pop","indie-alternative"],"sza":["rnb-soul","pop"],"erykah badu":["rnb-soul"],"d'angelo":["rnb-soul"],"anderson .paak":["rnb-soul","hip-hop"],"kendrick lamar":["hip-hop"],"j. cole":["hip-hop"],"de la soul":["hip-hop"],"a tribe called quest":["hip-hop"],"outkast":["hip-hop"],"nas":["hip-hop"],"radiohead":["indie-alternative","rock","electronic-dance"],"portishead":["electronic-dance","indie-alternative"],"massive attack":["electronic-dance","indie-alternative"],"nirvana":["rock","indie-alternative"],"the cure":["indie-alternative","rock"],"phoebe bridgers":["indie-alternative","folk-songwriter"],"boygenius":["indie-alternative","folk-songwriter"],"taylor swift":["pop","folk-songwriter"],"beyonce":["pop","rnb-soul"],"charli xcx":["pop","electronic-dance"],"dua lipa":["pop","electronic-dance"],"daft punk":["electronic-dance"],"fred again..":["electronic-dance"]};
    let library=[],ready=false,currentPicks=[];
    function escapeHtml(value){const div=document.createElement("div");div.textContent=String(value||"");return div.innerHTML;}
    function escapeAttr(value){return escapeHtml(value).replace(/"/g,"&quot;");}
    function populateSuggestions(){const names=[...library.map(a=>a.name),...Object.keys(REFERENCE_TASTES)],unique=[...new Set(names)].sort((a,b)=>a.localeCompare(b));$("artistSuggestions").innerHTML=unique.map(name=>`<option value="${escapeAttr(name)}"></option>`).join("");}
    function resolveTaste(input){return window.NDDiscoveryEngine.resolve(library,input,REFERENCE_TASTES);}
    function scoreArtist(){ /* Ranking lives in discover-engine.js. */ }
    function makeRecommendations({surprise=false}={}) {
      if(!ready)return;
      let genre=$("genreSelect").value,era=$("eraSelect").value,tasteInput=$("tasteInput").value.trim();
      if(surprise){genre="";era="";tasteInput="";$("genreSelect").value="";$("eraSelect").value="";$("tasteInput").value="";}
      const taste=resolveTaste(tasteInput);
      if(tasteInput&&!taste.matched&&!genre&&!era){showStatus(`We don’t have a reliable profile for “${tasteInput}” yet. Pick a genre or era, or choose a recognised artist.`);$("resultsSection").classList.remove("show");return;}
      const picks=window.NDDiscoveryEngine.rank(library,{genre,era,taste,surprise});
      if(!picks.length){showStatus("No documented matches for this selection yet. Browse by genre or try another artist.");$("resultsSection").classList.remove("show");return;}
      if(tasteInput&&!taste.matched)showStatus(`We don’t have a reliable profile for “${tasteInput}” yet. These picks use your genre and era filters only.`);
      else if(picks.length<5)showStatus(`We found ${picks.length} supported matches. We haven’t filled the list with unrelated artists.`);
      else hideStatus();
      renderResults(picks,genre,era,taste,surprise);
    }
    function whyLine(artist,genre,era,taste) {
      const link=window.NDDiscoveryEngine.connection(artist,taste);
      if(link)return link.reason;
      const shared=window.NDDiscoveryEngine.sharedTraits(artist,taste);
      if(taste.source&&shared.length) {
        const labels=shared.slice(0,3).map(t=>window.NDDiscoveryEngine.traitLabels[t]);
        return `Musical overlap with ${taste.source}: ${labels.join(", ")}. These connections come from the artist profiles.`;
      }
      const broad=genre||taste.primaryGenre||artist.primaryGenre;
      const category=GENRES[broad]?.label||"Canadian music";
      return taste.source
        ? `A broader ${category} pick. We don’t yet have a specific musical connection to ${taste.source}.`
        : `${category}${era ? " with "+ERA_LABELS[era]+" catalogue references" : " from Northern Dial’s catalogue"}.`;
    }
    function truncate(text,len=170){const value=String(text||"").trim();if(value.length<=len)return value;return value.slice(0,len).replace(/\s+\S*$/,"")+"…";}
    function renderResults(picks,genre,era,taste,surprise){currentPicks=picks;const summary=[];if(genre)summary.push(GENRES[genre].label);if(era)summary.push(ERA_LABELS[era]);if(taste.matched&&taste.source)summary.push(`starting from ${taste.source}`);$("resultsSummary").textContent=surprise?`${picks.length} picks from Northern Dial’s Canadian artist library.`:summary.length?`Discoveries ${summary.join(" · ")}.`:"Five picks from Northern Dial’s Canadian artist library.";$("resultsGrid").innerHTML=picks.map((artist,index)=>{const requestUrl=artist.requestHref||`./index.html?request=${encodeURIComponent(artist.name)}`,profileUrl=artist.profileHref||"",primaryUrl=profileUrl||artist.feature||requestUrl,tags=[...artist.genres.slice(0,3).map(g=>GENRES[g]?.label).filter(Boolean),...artist.eras.slice(0,1).map(e=>ERA_LABELS[e]).filter(Boolean)],image=artist.image?`<img class="artist-image" src="${escapeAttr(artist.image)}" alt="${escapeAttr(artist.name)}" loading="lazy" decoding="async" onerror="this.outerHTML='<div class=&quot;image-fallback&quot;>ND</div>'">`:`<div class="image-fallback">ND</div>`,track=artist.track,profile=profileUrl?`<a class="feature-link" href="${escapeAttr(profileUrl)}">Artist Profile</a>`:"",feature=artist.feature?`<a class="feature-link" href="${escapeAttr(artist.feature)}">Read Feature</a>`:"",link=window.NDDiscoveryEngine.connection(artist,taste),evidence=link?`<a class="connection-source" href="${escapeAttr(link.source)}" target="_blank" rel="noopener noreferrer">Connection source</a>`:"",bio=artist.bio||"Explore this Canadian artist in the Northern Dial catalogue.";return`<article class="artist-card"><div class="card-top"><a class="artist-image-link" href="${escapeAttr(primaryUrl)}" aria-label="${escapeAttr(artist.feature?`Read about ${artist.name}`:`Request ${artist.name}`)}">${image}<span class="rank">Pick ${index+1}</span></a><div><h3 class="artist-name"><a href="${escapeAttr(primaryUrl)}">${escapeHtml(artist.name)}</a></h3><div class="location">${escapeHtml(artist.location||"Canada")}</div><div class="tags">${tags.map(tag=>`<span class="tag">${escapeHtml(tag)}</span>`).join("")}</div><p class="why">${escapeHtml(whyLine(artist,genre,era,taste))}</p>${evidence}</div></div><div class="card-lower"><p class="bio">${escapeHtml(truncate(bio))}</p>${track?`<div class="start-track"><strong>On Northern Dial:</strong> ${escapeHtml(track)}</div>`:""}<div class="card-actions">${track?`<button class="feature-link discovery-mix-add" type="button" data-discovery-index="${index}" aria-label="${escapeAttr(`Add ${artist.name} - ${track} to your mix`)}" disabled>Add song to mix</button>`:""}<a class="request-link" href="${escapeAttr(requestUrl)}">Request ${escapeHtml(artist.name)}</a>${profile}${feature}</div></div></article>`;}).join("");updateMixButtons();$("resultsSection").classList.add("show");$("resultsSection").scrollIntoView({behavior:"smooth",block:"start"});}
    function showStatus(message){$("status").textContent=message;$("status").classList.add("show");}
    function hideStatus(){$("status").textContent="";$("status").classList.remove("show");}
    async function loadDiscoveryData(){try{const response=await fetch("/discovery-data.json?v=20261008d");if(!response.ok)throw new Error(`Discovery data returned ${response.status}`);const payload=await response.json();library=Array.isArray(payload?.artists)?payload.artists.map(artist=>window.NDDiscoveryEngine.prepare(artist)):[];if(library.length<5)throw new Error("Not enough artist records");populateSuggestions();ready=true;$("discoverBtn").disabled=false;$("discoverBtn").textContent="Find Me 5 Artists";$("surpriseBtn").disabled=false;const tagged=library.filter(a=>a.genres?.length).length;showStatus(`${library.length.toLocaleString()} Canadian artist profiles loaded. ${tagged.toLocaleString()} currently have discovery genre signals.`);setTimeout(hideStatus,3500);}catch(error){console.error("Discovery load failed:",error);$("discoverBtn").textContent="Discovery unavailable";showStatus("The artist library couldn’t load right now. Try again shortly or browse the full artist index.");}}
    function updateMixButtons(){
      const mix=window.NorthernDialMix,saved=mix?.snapshot()||[];
      document.querySelectorAll('.discovery-mix-add').forEach(button=>{
        const artist=currentPicks[Number(button.dataset.discoveryIndex)];
        const exists=saved.some(t=>t.artist.trim().toLowerCase()===artist.name.trim().toLowerCase()&&t.title.trim().toLowerCase()===artist.track.trim().toLowerCase());
        button.disabled=!mix||exists||saved.length>=5;
        button.textContent=exists?"✓ Added to mix":saved.length>=5?"Mix full":"Add song to mix";
        button.title=saved.length>=5&&!exists?"Remove a song from Your mix to make room":`Save ${artist.track}`;
      });
    }
    $("resultsGrid").addEventListener("click",event=>{
      const button=event.target.closest('.discovery-mix-add');if(!button)return;
      const artist=currentPicks[Number(button.dataset.discoveryIndex)];
      if(artist?.track)window.NorthernDialMix?.add({artist:artist.name,title:artist.track});
      updateMixButtons();
    });
    document.addEventListener('nd:mixchange',updateMixButtons);
    $("discoverBtn").addEventListener("click",()=>makeRecommendations());
    $("surpriseBtn").addEventListener("click",()=>makeRecommendations({surprise:true}));
    $("tasteInput").addEventListener("keydown",event=>{if(event.key==="Enter"&&ready)makeRecommendations();});
    const playerArtist = new URLSearchParams(window.location.search).get('artist');
    if (playerArtist) $("tasteInput").value = playerArtist.slice(0,300);
    loadDiscoveryData().then(() => {
      if (ready && playerArtist) makeRecommendations();
    });

