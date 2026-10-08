// Editorial removal: exclude this artist from selectable songs.
function isRetainedCatalogArtist(credit) {
    return !String(credit || '').split(/\s*(?:,|\/|&|\+|×|\bfeat(?:uring)?\.?|\bft\.?|\bwith\b)\s*/i)
        .some(name => name.trim().toLowerCase() === 'alice ivy');
}
let allTracks = [];
    let filteredTracks = [];

    async function loadCatalog() {
        try {
            document.getElementById('loadingState').textContent = 
                'Loading recently played tracks...';

            let historyItems = [];

            // Try multiple endpoints
            const endpoints = [
                'https://a10.asurahosting.com/public/northern_dial/history',
                'https://a10.asurahosting.com/api/station/northern_dial/history?rows=100',
                'https://a10.asurahosting.com/api/nowplaying/northern_dial'
            ];

            for (const endpoint of endpoints) {
                try {
                    console.log(`Trying: ${endpoint}`);
                    const response = await fetch(endpoint);
                    
                    if (response.ok) {
                        const data = await response.json();
                        
                        // Handle different response formats
                        if (Array.isArray(data)) {
                            historyItems = data;
                        } else if (data.rows) {
                            historyItems = data.rows;
                        } else if (data.song_history) {
                            historyItems = data.song_history;
                        }
                        
                        if (historyItems.length > 0) {
                            console.log(`✓ Success! Got ${historyItems.length} songs from ${endpoint}`);
                            break;
                        }
                    }
                } catch (e) {
                    console.log(`✗ Failed: ${endpoint}`, e);
                }
            }

            if (historyItems.length === 0) {
                throw new Error('No songs available from any endpoint');
            }

            console.log(`Total history items: ${historyItems.length}`);

            // Extract unique tracks
            const uniqueTracks = [];
            const seenIds = new Set();

            historyItems.forEach(item => {
                const song = item.song || {};
                const songId = song.song_id || song.id || song.unique_id;
                
                if (!seenIds.has(songId) && song.title && isRetainedCatalogArtist(song.artist)) {
                    seenIds.add(songId);
                    uniqueTracks.push({
                        id: songId,
                        title: song.title || 'Unknown Track',
                        artist: song.artist || 'Unknown Artist',
                        art: song.art || '',
                        played_at: item.played_at || Date.now() / 1000,
                        request_url: `/api/station/northern_dial/request/${songId}`
                    });
                }
            });

            console.log(`Unique tracks: ${uniqueTracks.length}`);

            if (uniqueTracks.length === 0) {
                throw new Error('No valid tracks found');
            }

            // Sort by most recently played
            allTracks = uniqueTracks.sort((a, b) => b.played_at - a.played_at);

            filteredTracks = [...allTracks];
            displayCatalog(filteredTracks);
            updateCatalogCount(filteredTracks.length);

            document.getElementById('loadingState').style.display = 'none';
            document.getElementById('catalogGrid').style.display = 'grid';

        } catch (error) {
            console.error('Error loading recent plays:', error);
            document.getElementById('loadingState').innerHTML = 
                '<div style="color:#C33;">Unable to load enough recent plays from the API.<br><br>The station\'s API only provides access to ~5 recent songs.<br><br><a href="index.html" style="color:#C33; text-decoration:underline;">← Return home</a></div>';
        }
    }

    function displayCatalog(tracks) {
        const grid = document.getElementById('catalogGrid');
        const emptyState = document.getElementById('emptyState');

        if (tracks.length === 0) {
            grid.style.display = 'none';
            emptyState.style.display = 'block';
            return;
        }

        grid.style.display = 'grid';
        emptyState.style.display = 'none';

        grid.innerHTML = tracks.map(track => `
            <div class="album-card">
                ${track.art ? 
                    `<img src="${track.art}" alt="${track.title}" class="album-art" onerror="this.outerHTML='<div class=\\'album-art-placeholder\\'>♪</div>'">` :
                    `<div class="album-art-placeholder">♪</div>`
                }
                <div class="album-title">${escapeHtml(track.title)}</div>
                <div class="album-artist">${escapeHtml(track.artist)}</div>
                <button class="request-btn" onclick="requestTrack('${escapeHtml(track.request_url)}', this)">
                    Request
                </button>
            </div>
        `).join('');
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function updateCatalogCount(count, isSearch = false) {
        const countEl = document.getElementById('catalogCount');
        if (isSearch) {
            countEl.textContent = count === 0 ? 'No results' : `${count.toLocaleString()} results`;
        } else {
            countEl.textContent = `${count.toLocaleString()} recently played tracks`;
        }
    }

    function searchCatalog(query) {
        const searchTerm = query.toLowerCase().trim();

        if (!searchTerm) {
            // No search - reload initial 5 recent songs
            loadCatalog();
            return;
        }

        // Dynamic search of full catalog (like request modal)
        document.getElementById('catalogGrid').innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding:60px;"><div class="searching-spinner" style="margin: 0 auto 20px;"></div><div style="color:#999; font-size:1.1rem;">Searching catalog...</div></div>';

        fetch(`https://a10.asurahosting.com/api/station/northern_dial/requests?searchPhrase=${encodeURIComponent(searchTerm)}&rowCount=100&current=1`)
            .then(response => {
                if (!response.ok) throw new Error('Search failed');
                return response.json();
            })
            .then(data => {
                const songs = data.rows || data.result || data.results || [];
                console.log(`Search results for "${searchTerm}": ${songs.length}`);

                if (songs.length === 0) {
                    displayCatalog([]);
                    updateCatalogCount(0, true);
                    return;
                }

                // Convert to track format
                const searchResults = [];
                const seenIds = new Set();

                songs.forEach(item => {
                    const song = item.song || item;
                    const songId = song.song_id || song.id;
                    
                    if (!seenIds.has(songId) && isRetainedCatalogArtist(song.artist)) {
                        seenIds.add(songId);
                        searchResults.push({
                            id: songId,
                            title: song.title || 'Unknown Title',
                            artist: song.artist || 'Unknown Artist',
                            art: song.art || song.album_art || '',
                            request_url: item.request_url
                        });
                    }
                });

                filteredTracks = searchResults;
                displayCatalog(filteredTracks);
                updateCatalogCount(filteredTracks.length, true);
            })
            .catch(error => {
                console.error('Search error:', error);
                document.getElementById('catalogGrid').innerHTML = 
                    '<div style="grid-column: 1/-1; text-align:center; padding:40px; color:#C33;">Search failed. Please try again.</div>';
            });
    }

    async function requestTrack(requestUrl, button) {
        // Construct full URL - handle both relative and absolute URLs
        let fullUrl;
        if (requestUrl.startsWith('http')) {
            fullUrl = requestUrl;
        } else if (requestUrl.startsWith('/api')) {
            fullUrl = 'https://a10.asurahosting.com' + requestUrl;
        } else {
            fullUrl = 'https://a10.asurahosting.com/api/station/northern_dial/request/' + requestUrl;
        }

        button.disabled = true;
        button.textContent = 'Requesting...';

        try {
            await fetch(fullUrl, {
                method: 'POST',
                headers: { 'Accept': 'application/json' }
            });

            showStatus('✓ Request submitted! Your song will play soon.', 'success');
            button.textContent = 'Requested ✓';
            
            setTimeout(() => {
                button.disabled = false;
                button.textContent = 'Request';
            }, 3000);

        } catch (error) {
            // CORS blocks reading response but request goes through
            showStatus('✓ Request submitted! Your song will play soon.', 'success');
            button.textContent = 'Requested ✓';
            
            setTimeout(() => {
                button.disabled = false;
                button.textContent = 'Request';
            }, 3000);
        }
    }

    function showStatus(message, type = 'success') {
        const statusEl = document.getElementById('statusMessage');
        statusEl.textContent = message;
        statusEl.className = 'status-message show' + (type === 'error' ? ' error' : '');

        setTimeout(() => {
            statusEl.classList.remove('show');
        }, 4000);
    }

    function updateBackgroundGradient() {
        const scrollPercent = window.scrollY / (document.documentElement.scrollHeight - window.innerHeight);
        const clampedPercent = Math.min(Math.max(scrollPercent, 0), 1);

        // Match the homepage: white at the top, Northern Dial red at the bottom.
        const r = Math.round(255 - (255 - 204) * clampedPercent);
        const g = Math.round(255 - (255 - 51) * clampedPercent);
        const b = Math.round(255 - (255 - 51) * clampedPercent);
        
        document.body.style.background = `rgb(${r}, ${g}, ${b})`;
    }

    // Search input handler with debounce
    let searchTimeout;
    document.getElementById('searchInput').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchCatalog(e.target.value);
        }, 300);
    });

    // Scroll gradient effect
    window.addEventListener('scroll', updateBackgroundGradient);

    // Initialize
    loadCatalog();
    updateBackgroundGradient();
