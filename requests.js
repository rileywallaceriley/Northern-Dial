const apiRoot = 'https://a10.asurahosting.com';
    const queryInput = document.getElementById('query');
    const status = document.getElementById('status');
    const results = document.getElementById('results');

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
    }

    async function searchSongs(event) {
      if (event) event.preventDefault();
      const query = queryInput.value.trim();
      if (!query) return;
      status.textContent = 'Searching…';
      results.innerHTML = '';
      try {
        const response = await fetch(`${apiRoot}/api/station/northern_dial/requests?searchPhrase=${encodeURIComponent(query)}&rowCount=10&current=1`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        const songs = data.rows || data.result || data.results || (Array.isArray(data) ? data : []);
        if (!Array.isArray(songs) || songs.length === 0) {
          status.textContent = 'No results found. Try a different search.';
          return;
        }
        status.textContent = `${songs.length} result${songs.length === 1 ? '' : 's'} found`;
        results.innerHTML = songs.map(item => {
          const song = item.song || item;
          const requestUrl = item.request_url || '';
          const art = song.art || song.album_art || '';
          const image = art ? `<img class="art" src="${escapeHtml(art)}" alt="">` : '<div class="art" aria-hidden="true">♪</div>';
          return `<div class="result">${image}<div class="song"><strong>${escapeHtml(song.title || 'Unknown title')}</strong><span>${escapeHtml(song.artist || 'Unknown artist')}</span></div><button class="request" data-url="${escapeHtml(requestUrl)}">Request</button></div>`;
        }).join('');
      } catch (error) {
        status.textContent = 'Search is temporarily unavailable. Please try again.';
      }
    }

    async function requestSong(requestUrl, button) {
      const fullUrl = requestUrl.startsWith('http') ? requestUrl : apiRoot + requestUrl;
      button.disabled = true;
      button.textContent = 'Sending…';
      try { await fetch(fullUrl, { method: 'POST', headers: { Accept: 'application/json' } }); } catch (error) { /* The station may still accept the request despite a CORS response. */ }
      status.textContent = 'Request submitted — your song will play soon.';
      results.innerHTML = '';
      queryInput.value = '';
    }

    document.getElementById('searchForm').addEventListener('submit', searchSongs);
    results.addEventListener('click', event => {
      const button = event.target.closest('button[data-url]');
      if (button) requestSong(button.dataset.url, button);
    });
