const localAudio = document.getElementById('radioStream');

    let persistentController = null;
    try {
        if (window.self !== window.top && window.top.NDPlayer?.audio) {
            persistentController = window.top.NDPlayer;
        }
    } catch (_) {}

    const audio = persistentController?.audio || localAudio;

    if (!persistentController && localAudio) {
        window.ND_SHARED_AUDIO = localAudio;
    }

    // A framed homepage must never own a second live stream. Safari begins
    // resolving <source> elements before scripts run, so explicitly neutralize
    // the local audio element as soon as we attach to the parent's player.
    if (persistentController && localAudio && localAudio !== audio) {
        try {
            localAudio.pause();
            localAudio.removeAttribute('src');
            localAudio.querySelectorAll('source').forEach(source => source.removeAttribute('src'));
            localAudio.load();
            localAudio.dataset.ndSuppressedAudio = 'true';
        } catch (_) {}
    }

    const playPauseBtn = document.getElementById('playPauseBtn');
    const volumeSlider = document.getElementById('volumeSlider');
    const statusText = document.getElementById('statusText');
    const songTitle = document.getElementById('songTitle');
    const artistName = document.getElementById('artistName');
    const artistProfileBtn = document.getElementById('artistProfileBtn');

    let artistProfileLookupPromise = null;
    let artistProfileRequestId = 0;
    let homepagePlayPending = false;

    function normalizeArtistLookupName(value) {
        return String(value || '')
            .normalize('NFKD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/[’‘]/g, "'")
            .replace(/\s+/g, ' ')
            .trim()
            .toLocaleLowerCase('en-CA');
    }

    function getPrimaryArtist(value) {
        const artist = String(value || '').trim();
        if (!artist) return '';
        return artist
            .split(/\s+(?:feat\.?|ft\.?|featuring|with|x)\s+|,\s*|\s+&\s+/i)[0]
            .trim();
    }

    async function loadArtistProfileLookup() {
        if (!artistProfileLookupPromise) {
            artistProfileLookupPromise = fetch('/artist-profile-index.json', { cache: 'no-cache' })
                .then(response => {
                    if (!response.ok) throw new Error('Artist profile index unavailable');
                    return response.json();
                })
                .then(index => {
                    const lookup = new Map();
                    Object.entries(index || {}).forEach(([name, url]) => {
                        lookup.set(normalizeArtistLookupName(name), url);
                    });
                    return lookup;
                })
                .catch(error => {
                    console.log('Error loading artist profile index:', error);
                    artistProfileLookupPromise = null;
                    return new Map();
                });
        }
        return artistProfileLookupPromise;
    }

    async function updateArtistProfileLink(artist) {
        if (!artistProfileBtn) return;

        const requestId = ++artistProfileRequestId;
        artistProfileBtn.hidden = true;
        artistProfileBtn.removeAttribute('aria-label');

        const lookup = await loadArtistProfileLookup();
        if (requestId !== artistProfileRequestId) return;

        const fullArtist = String(artist || '').trim();
        const primaryArtist = getPrimaryArtist(fullArtist);
        const profileUrl =
            lookup.get(normalizeArtistLookupName(fullArtist)) ||
            lookup.get(normalizeArtistLookupName(primaryArtist));

        if (!profileUrl) return;

        artistProfileBtn.href = profileUrl;
        artistProfileBtn.setAttribute('aria-label', `Meet ${primaryArtist || fullArtist} on Northern Dial`);
        artistProfileBtn.hidden = false;
    }

    if (!persistentController) audio.volume = 0.7;
    if (persistentController && volumeSlider) {
        volumeSlider.value = Math.round(audio.volume * 100);
    }

    function updateMediaSession(title, artist) {
        // The parent persistent player owns lock-screen/media-session controls
        // while Home is displayed inside the listening shell.
        if (persistentController) return;
        if ('mediaSession' in navigator) {
            navigator.mediaSession.metadata = new MediaMetadata({
                title: title,
                artist: artist,
                album: 'Northern Dial Radio',
                artwork: [{ src: 'https://i.imgur.com/XIAPd0N.png', sizes: '512x512', type: 'image/png' }]
            });
            navigator.mediaSession.setActionHandler('play', () => audio.play());
            navigator.mediaSession.setActionHandler('pause', () => audio.pause());
        }
    }

    playPauseBtn.addEventListener('click', async function() {
        if (homepagePlayPending) return;

        try {
            if (audio.paused || audio.ended) {
                homepagePlayPending = true;

                // Make the first tap feel immediate while iOS opens the live stream.
                playPauseBtn.classList.add('playing');
                playPauseBtn.setAttribute('aria-busy', 'true');
                statusText.textContent = 'CONNECTING…';

                if (persistentController) await persistentController.play();
                else await audio.play();
            } else {
                if (persistentController) persistentController.pause();
                else audio.pause();
            }
        } catch (_) {
            statusText.textContent = 'TAP TO RETRY';
            playPauseBtn.classList.remove('playing');
        } finally {
            homepagePlayPending = false;
            playPauseBtn.removeAttribute('aria-busy');
            syncPlaybackUi();
        }
    });

    volumeSlider.addEventListener('input', function() {
        const value = this.value / 100;
        if (persistentController) persistentController.setVolume(value);
        else audio.volume = value;
    });


    function getTimeAgo(date) {
        const seconds = Math.floor((new Date() - date) / 1000);
        if (seconds < 60) return 'Just now';
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        return `${days}d ago`;
    }

    function applySharedStationData(data) {
        if (!data) return;

        if (data.now_playing && data.now_playing.song) {
            const song = data.now_playing.song;
            const title = song.title || 'Unknown Track';
            const artist = song.artist || 'Unknown Artist';
            songTitle.textContent = title;
            artistName.textContent = artist;
            updateArtistProfileLink(artist);
            updateMediaSession(title, artist);
        }

        const recentlyPlayed = document.getElementById('recentlyPlayed');
        if (!recentlyPlayed) return;

        if (Array.isArray(data.song_history)) {
            recentlyPlayed.innerHTML = data.song_history.map(item => {
                const song = item.song || {};
                const title = song.title || 'Unknown Track';
                const artist = song.artist || 'Unknown Artist';
                const art = song.art || '';
                const playedAt = new Date(item.played_at * 1000);
                const timeAgo = getTimeAgo(playedAt);

                return `
                <div style="display:flex; align-items:center; gap:12px; padding:12px; border-bottom:2px solid #e0e0e0; transition:background 0.2s;" onmouseover="this.style.background='#f8f8f8'" onmouseout="this.style.background='transparent'">
                    ${art ? `<img loading="lazy" decoding="async" src="${art}" alt="" width="50" height="50" style="width:50px; height:50px; border-radius:6px; object-fit:cover; flex-shrink:0; border:2px solid #ddd;">` :
                    '<div style="width:50px; height:50px; background:#e0e0e0; border-radius:6px; flex-shrink:0; display:flex; align-items:center; justify-content:center; color:#999; font-size:1.3rem; border:2px solid #ddd;">♪</div>'}
                    <div style="flex:1; min-width:0;">
                        <div style="color:#1a1a1a; font-weight:700; font-size:0.95rem; margin-bottom:2px;">${title}</div>
                        <div style="color:#666; font-size:0.85rem;">${artist}</div>
                    </div>
                    <div style="color:#C33; font-size:0.8rem; font-weight:700; white-space:nowrap; text-transform:uppercase; letter-spacing:0.5px;">${timeAgo}</div>
                </div>`;
            }).join('');
        } else {
            recentlyPlayed.innerHTML = '<div style="color:#999; text-align:center; padding:20px;">No history available</div>';
        }
    }

    document.addEventListener('nd:nowplaying', event => {
        applySharedStationData(event.detail);
    });

    function syncPlaybackUi() {
        const playing = !audio.paused && !audio.ended;
        playPauseBtn.classList.toggle('playing', playing);
        if (!homepagePlayPending) {
            statusText.textContent = playing ? 'LIVE NOW' : 'PAUSED';
        }
    }

    audio.addEventListener('playing', function() {
        syncPlaybackUi();
        updateMediaSession(songTitle.textContent, artistName.textContent);
    });

    audio.addEventListener('pause', function() {
        if (!audio.ended) syncPlaybackUi();
    });

    audio.addEventListener('error', function() {
        statusText.textContent = 'CONNECTION ERROR';
        playPauseBtn.classList.remove('playing');
    });

    syncPlaybackUi();

    let deferredPrompt;
    const installBanner = document.getElementById('installBanner');
    const installModal = document.getElementById('installModal');
    const installBtn = document.getElementById('installBtn');
    const dismissBtn = document.getElementById('dismissBtn');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const installSteps = document.getElementById('installSteps');

    const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;
    const bannerDismissed = localStorage.getItem('installBannerDismissed');

    if (!isStandalone && !bannerDismissed) {
        setTimeout(() => installBanner.classList.add('show'), 3000);
    }

    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
    });

    function getInstallInstructions() {
        const userAgent = navigator.userAgent.toLowerCase();
        const isIOS = /iphone|ipad|ipod/.test(userAgent);
        const isSafari = /safari/.test(userAgent) && !/chrome/.test(userAgent);
        const isAndroid = /android/.test(userAgent);

        if (isIOS || isSafari) {
            return `
                <div class="install-step"><div class="install-step-number">Step 1</div><div>Tap the Share button <strong>⎘</strong> in Safari</div></div>
                <div class="install-step"><div class="install-step-number">Step 2</div><div>Scroll down and tap <strong>"Add to Home Screen"</strong></div></div>
                <div class="install-step"><div class="install-step-number">Step 3</div><div>Tap <strong>"Add"</strong> in the top right</div></div>
                <div class="install-step"><div class="install-step-number">Step 4</div><div>Find Northern Dial on your home screen!</div></div>
            `;
        } else if (isAndroid) {
            return `
                <div class="install-step"><div class="install-step-number">Step 1</div><div>Tap the menu button <strong>⋮</strong> in Chrome</div></div>
                <div class="install-step"><div class="install-step-number">Step 2</div><div>Tap <strong>"Install app"</strong> or <strong>"Add to Home screen"</strong></div></div>
                <div class="install-step"><div class="install-step-number">Step 3</div><div>Tap <strong>"Install"</strong></div></div>
                <div class="install-step"><div class="install-step-number">Step 4</div><div>Northern Dial will appear on your home screen!</div></div>
            `;
        } else {
            return `<div class="install-step"><div class="install-step-number">Desktop</div><div>Look for an install icon <strong>⊕</strong> in your browser's address bar.</div></div>`;
        }
    }

    installBtn.addEventListener('click', async () => {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            deferredPrompt = null;
            installBanner.classList.remove('show');
        } else {
            installSteps.innerHTML = getInstallInstructions();
            installModal.classList.add('show');
            installBanner.classList.remove('show');
        }
    });

    dismissBtn.addEventListener('click', () => {
        installBanner.classList.remove('show');
        localStorage.setItem('installBannerDismissed', 'true');
    });

    closeModalBtn.addEventListener('click', () => installModal.classList.remove('show'));

    installModal.addEventListener('click', (e) => {
        if (e.target === installModal) installModal.classList.remove('show');
    });

    document.getElementById('requestModal').addEventListener('click', (e) => {
        if (e.target === document.getElementById('requestModal')) {
            document.getElementById('requestModal').classList.remove('show');
        }
    });

    document.getElementById('submitModal').addEventListener('click', (e) => {
        if (e.target === document.getElementById('submitModal')) {
            document.getElementById('submitModal').classList.remove('show');
        }
    });

    document.getElementById('involvedModal').addEventListener('click', (e) => {
        if (e.target === document.getElementById('involvedModal')) {
            document.getElementById('involvedModal').classList.remove('show');
        }
    });

    function handleSubmitMusic(event) {
        event.preventDefault();

        const artistName = document.getElementById('artistName').value;
        const artistEmail = document.getElementById('artistEmail').value;
        const trackLinks = document.getElementById('trackLinks').value;
        const socialLinks = document.getElementById('socialLinks').value;
        const artistMessage = document.getElementById('artistMessage').value;

        const formData = {
            formType: 'Music Submission',
            artistName: artistName,
            email: artistEmail,
            trackLinks: trackLinks,
            socialLinks: socialLinks,
            message: artistMessage
        };

        fetch('https://submit-form.com/xNHkj978w', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(response => {
            if (response.ok) {
                alert('✓ Submission received! We\'ll be in touch soon.');
                document.getElementById('submitModal').classList.remove('show');
                document.getElementById('submitForm').reset();
            } else {
                alert('Something went wrong. Please try again or email us directly at rileywallace@gmail.com');
            }
        })
        .catch(error => {
            alert('Something went wrong. Please try again or email us directly at rileywallace@gmail.com');
        });
    }

    function handleInvolvedForm(event) {
        event.preventDefault();

        const name = document.getElementById('involvedName').value;
        const email = document.getElementById('involvedEmail').value;
        const interest = document.getElementById('involvedInterest').value;
        const message = document.getElementById('involvedMessage').value;

        const formData = {
            formType: 'Get Involved',
            name: name,
            email: email,
            interest: interest,
            message: message
        };

        fetch('https://submit-form.com/xNHkj978w', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(response => {
            if (response.ok) {
                alert('✓ Thanks for your interest! We\'ll be in touch soon.');
                document.getElementById('involvedModal').classList.remove('show');
                document.getElementById('involvedForm').reset();
            } else {
                alert('Something went wrong. Please try again or email us directly at rileywallace@gmail.com');
            }
        })
        .catch(error => {
            alert('Something went wrong. Please try again or email us directly at rileywallace@gmail.com');
        });
    }

    async function searchSongs() {
        const query = document.getElementById('requestSearch').value.trim();
        const results = document.getElementById('requestResults');
        const status = document.getElementById('requestStatus');

        if (!query) return;

        results.innerHTML = '<div style="color:#ccc; text-align:center; padding:20px;">Searching...</div>';
        status.style.display = 'none';
        status.textContent = '';

        try {
            const response = await fetch(`https://a10.asurahosting.com/api/station/northern_dial/requests?searchPhrase=${encodeURIComponent(query)}&rowCount=10&current=1`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            const songs = data.rows || data.result || data.results || (Array.isArray(data) ? data : []);

            if (!Array.isArray(songs) || songs.length === 0) {
                results.innerHTML = '<div style="color:#ccc; text-align:center; padding:20px;">No results found. Try a different search.</div>';
                return;
            }

            results.innerHTML = songs.map(item => {
                const song = item.song || item;
                const requestUrl = item.request_url;
                const art = song.art || song.album_art || '';
                const title = song.title || 'Unknown Title';
                const artist = song.artist || 'Unknown Artist';

                return `
                <div style="display:flex; align-items:center; gap:15px; background:#2a2a2a; border:2px solid #444; border-radius:8px; padding:15px;"
                    onmouseover="this.style.borderColor='#C33'" onmouseout="this.style.borderColor='#444'">
                    ${art ? `<img loading="lazy" decoding="async" src="${art}" alt="" style="width:55px; height:55px; border-radius:6px; object-fit:cover; flex-shrink:0;">` :
                    '<div style="width:55px; height:55px; background:#333; border-radius:6px; flex-shrink:0; display:flex; align-items:center; justify-content:center; color:#666; font-size:1.5rem;">♪</div>'}
                    <div style="flex:1; min-width:0;">
                        <div style="color:#ffffff; font-weight:700; font-size:1rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${title}</div>
                        <div style="color:#aaa; font-size:0.9rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${artist}</div>
                    </div>
                    <button onclick="requestSong('${requestUrl}')"
                        style="background:linear-gradient(135deg,#C33,#8B2323); color:white; border:none; padding:10px 18px; border-radius:6px; font-weight:700; font-size:0.85rem; text-transform:uppercase; letter-spacing:1px; cursor:pointer; flex-shrink:0;">
                        Request
                    </button>
                </div>`;
            }).join('');

        } catch (error) {
            results.innerHTML = `<div style="color:#C33; text-align:center; padding:20px;">Search error: ${error.message}</div>`;
        }
    }

    async function requestSong(requestUrl) {
        const status = document.getElementById('requestStatus');

        const fullUrl = requestUrl.startsWith('http')
            ? requestUrl
            : 'https://a10.asurahosting.com' + requestUrl;

        try {
            const response = await fetch(fullUrl, {
                method: 'POST',
                headers: { 'Accept': 'application/json' }
            });

            status.style.display = 'block';
            status.style.background = 'rgba(0, 180, 0, 0.2)';
            status.style.color = '#00cc00';
            status.style.border = '2px solid #00cc00';
            status.textContent = '✓ Request submitted! Your song will play soon.';
            document.getElementById('requestResults').innerHTML = '';
            document.getElementById('requestSearch').value = '';

        } catch (error) {
            status.style.display = 'block';
            status.style.background = 'rgba(0, 180, 0, 0.2)';
            status.style.color = '#00cc00';
            status.style.border = '2px solid #00cc00';
            status.textContent = '✓ Request submitted! Your song will play soon.';
            document.getElementById('requestResults').innerHTML = '';
            document.getElementById('requestSearch').value = '';
        }
    }


    // Simple Animated Visualizer (no real audio analysis - avoids CORS issues)
    let animationId;
    let currentStyle = 'wave';
    let particles = [];
    let animationTime = 0;

    const visualizerBtn = document.getElementById('visualizerBtn');
    const visualizerOverlay = document.getElementById('visualizerOverlay');
    const visualizerClose = document.getElementById('visualizerClose');
    const visualizerCanvas = document.getElementById('visualizerCanvas');
    const visualizerSong = document.getElementById('visualizerSong');
    const visualizerArtist = document.getElementById('visualizerArtist');
    const visualizerStatus = document.getElementById('visualizerStatus');

    let ctx;
    try {
        ctx = visualizerCanvas.getContext('2d');
    } catch (e) {
        // Canvas context failed
    }

    class Particle {
        constructor(x, y) {
            this.x = x;
            this.y = y;
            this.size = Math.random() * 3 + 1;
            this.speedX = Math.random() * 3 - 1.5;
            this.speedY = Math.random() * 3 - 1.5;
            this.life = 1;
        }
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            this.life -= 0.01;
        }
        draw() {
            ctx.fillStyle = `rgba(195, 51, 51, ${this.life})`;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    function resizeCanvas() {
        const container = visualizerCanvas.parentElement;
        visualizerCanvas.width = container.clientWidth;
        visualizerCanvas.height = container.clientHeight;
    }

    function drawBars() {
        if (!ctx || !visualizerCanvas.width || !visualizerCanvas.height) {
            return;
        }

        // Always draw gradient background first
        const gradient = ctx.createLinearGradient(0, 0, 0, visualizerCanvas.height);
        gradient.addColorStop(0, '#1a1a1a');
        gradient.addColorStop(1, '#000000');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, visualizerCanvas.width, visualizerCanvas.height);

        const numBars = 64;
        const barWidth = Math.max(visualizerCanvas.width / numBars - 2, 5);

        for (let i = 0; i < numBars; i++) {
            // Fast and smooth - matches music energy!
            const barHeight = (Math.sin(animationTime / 150 + i / 10) * 0.3 +
                              Math.sin(animationTime / 110 + i / 7) * 0.3 +
                              Math.sin(animationTime / 200 + i / 12) * 0.15 +
                              0.55) * visualizerCanvas.height * 0.75;

            const barGradient = ctx.createLinearGradient(0, visualizerCanvas.height - barHeight, 0, visualizerCanvas.height);
            barGradient.addColorStop(0, '#ff6666');
            barGradient.addColorStop(0.5, '#C33');
            barGradient.addColorStop(1, '#8B2323');

            ctx.fillStyle = barGradient;
            ctx.shadowBlur = 15;
            ctx.shadowColor = '#C33';
            ctx.fillRect(i * (barWidth + 2), visualizerCanvas.height - barHeight, barWidth, barHeight);
        }
        ctx.shadowBlur = 0;
    }

    function drawWaveform() {
        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, visualizerCanvas.width, visualizerCanvas.height);

        ctx.lineWidth = 3;
        ctx.strokeStyle = '#C33';
        ctx.shadowBlur = 10;
        ctx.shadowColor = '#C33';
        ctx.beginPath();

        const points = 200;
        for (let i = 0; i < points; i++) {
            const x = (i / points) * visualizerCanvas.width;

            // Faster waves with variation - matches music energy!
            const y = visualizerCanvas.height / 2 +
                     Math.sin(animationTime / 40 + i / 15) * 60 +
                     Math.sin(animationTime / 25 + i / 8) * 40 +
                     Math.sin(animationTime / 60 + i / 25) * 30 +
                     Math.cos(animationTime / 45 + i / 12) * 25;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.stroke();
        ctx.shadowBlur = 0;
    }

    function drawCircular() {
        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, visualizerCanvas.width, visualizerCanvas.height);

        const centerX = visualizerCanvas.width / 2;
        const centerY = visualizerCanvas.height / 2;
        const radius = Math.min(centerX, centerY) - 50;
        const numBars = 128;

        for (let i = 0; i < numBars; i++) {
            // Faster circular animation - matches music energy!
            const barHeight = (Math.sin(animationTime / 80 + i / 8) * 0.4 +
                              Math.sin(animationTime / 50 + i / 4) * 0.4 +
                              0.5) * 100;
            const angle = (i / numBars) * Math.PI * 2;

            const x1 = centerX + Math.cos(angle) * radius;
            const y1 = centerY + Math.sin(angle) * radius;
            const x2 = centerX + Math.cos(angle) * (radius + barHeight);
            const y2 = centerY + Math.sin(angle) * (radius + barHeight);

            const gradient = ctx.createLinearGradient(x1, y1, x2, y2);
            gradient.addColorStop(0, '#8B2323');
            gradient.addColorStop(0.5, '#C33');
            gradient.addColorStop(1, '#ff6666');

            ctx.strokeStyle = gradient;
            ctx.lineWidth = 2;
            ctx.shadowBlur = 10;
            ctx.shadowColor = '#C33';
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
        }
        ctx.shadowBlur = 0;
    }

    function drawParticles() {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
        ctx.fillRect(0, 0, visualizerCanvas.width, visualizerCanvas.height);

        if (animationTime % 5 === 0 && particles.length < 200) {
            for (let i = 0; i < 3; i++) {
                particles.push(new Particle(
                    Math.random() * visualizerCanvas.width,
                    Math.random() * visualizerCanvas.height
                ));
            }
        }

        particles = particles.filter(particle => particle.life > 0);
        particles.forEach(particle => {
            particle.update();
            particle.draw();
        });
    }

    function drawVisualizer() {
        animationId = requestAnimationFrame(drawVisualizer);
        animationTime++;

        switch(currentStyle) {
            case 'wave': drawWaveform(); break;
            case 'circular': drawCircular(); break;
            case 'particles': drawParticles(); break;
            default: drawWaveform();
        }
    }

    function updateVisualizerInfo() {
        visualizerSong.textContent = songTitle.textContent;
        visualizerArtist.textContent = artistName.textContent;
        visualizerStatus.textContent = statusText.textContent;
    }

    visualizerBtn.addEventListener('click', function() {
        if (!audio.paused) {
            visualizerOverlay.classList.add('show');

            setTimeout(() => {
                resizeCanvas();

                if (!ctx) {
                    alert('Visualizer failed to initialize. Please refresh the page.');
                    return;
                }

                updateVisualizerInfo();
                animationTime = 0;

                if (animationId) {
                    cancelAnimationFrame(animationId);
                }
                drawVisualizer();
            }, 100);
        } else {
            alert('Please start playing the radio first!');
        }
    });

    visualizerClose.addEventListener('click', function() {
        visualizerOverlay.classList.remove('show');
        if (animationId) {
            cancelAnimationFrame(animationId);
            animationId = null;
        }
        particles = [];
    });

    visualizerOverlay.addEventListener('click', function(e) {
        if (e.target === visualizerOverlay) {
            visualizerOverlay.classList.remove('show');
            if (animationId) {
                cancelAnimationFrame(animationId);
                animationId = null;
            }
            particles = [];
        }
    });

    document.querySelectorAll('.visualizer-style-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.visualizer-style-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentStyle = this.dataset.style;
            particles = [];
        });
    });

    setInterval(function() {
        if (visualizerOverlay.classList.contains('show')) {
            updateVisualizerInfo();
        }
    }, 5000);

    audio.addEventListener('playing', function() {
        visualizerBtn.classList.add('playing');
    });

    audio.addEventListener('pause', function() {
        visualizerBtn.classList.remove('playing');
    });

    window.addEventListener('resize', function() {
        if (visualizerOverlay.classList.contains('show')) {
            resizeCanvas();
        }
    });

    // Keep the navigation out of the opening hero view, then make it sticky
    // once the player/hero has scrolled away.
    const siteNav = document.querySelector('.site-nav');
    const heroSection = document.querySelector('.player-section');
    if (siteNav && heroSection && 'IntersectionObserver' in window) {
        const navVisibilityObserver = new IntersectionObserver(([entry]) => {
            siteNav.classList.toggle('is-visible', !entry.isIntersecting);
        }, { threshold: 0 });
        navVisibilityObserver.observe(heroSection);
    }

    // Artist-directory links can open this modal with the artist already searched.
    (() => {
        const artist = new URLSearchParams(window.location.search).get('request');
        if (!artist) return;
        const modal = document.getElementById('requestModal');
        const input = document.getElementById('requestSearch');
        if (!modal || !input) return;
        modal.classList.add('show');
        input.value = artist;
        searchSongs();
    })();
