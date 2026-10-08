/* Google Analytics 4 - site-wide tag (G-G24PFXRPMW) */
(function () {
  if (window.__ndGaInstalled) return;
  window.__ndGaInstalled = true;
  var s = document.createElement('script');
  s.async = true;
  s.src = 'https://www.googletagmanager.com/gtag/js?id=G-G24PFXRPMW';
  document.head.appendChild(s);
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  window.gtag = gtag;
  gtag('js', new Date());
  gtag('config', 'G-G24PFXRPMW');
})();
(() => {
  const LOGO = 'https://i.imgur.com/XIAPd0N.png';
  const path = window.location.pathname;
  const isHomepage = path === '/' || path === '/index.html';
  const isFrench = path === '/fr' || path.startsWith('/fr/') || new URLSearchParams(window.location.search).get('lang') === 'fr';


  const root = isFrench ? '/fr/' : '/';
  const links = isFrench
    ? [
        ['Accueil', '/fr/'],
        ['Chansons', '/fr/library.html'],
        ['Artistes', '/fr/artists.html'],
        ['Découvrir', '/fr/discover.html'],
        ['Blog', '/fr/blog/']
      ]
    : [
        ['Home', '/'],
        ['Songs', '/library.html'],
        ['Artists', '/artists.html'],
        ['Discover', '/discover.html'],
        ['New Releases', '/new-releases.html'],
        ['TV', '/tv.html'],
        ['Blog', '/blog/']
      ];

  const secondary = isFrench
    ? [
        ['À propos', '/fr/a-propos.html', ''],
        ['Soumettre', '/fr/#submit', 'submit'],
        ['English', '/', 'language']
      ]
    : [
        ['About', '/about.html', ''],
        ['Submit', '/#submit', 'submit'],
        ['Français', '/fr/', 'language']
      ];

  function loadPageEnhancements() {
    let src = '';

    if (isHomepage) {
      src = '/nd-home-enhancements.js?v=20260927b';
    } else if (path === '/artists.html') {
      src = '/nd-artists-enhancements.js?v=20260927a';
    } else if (path === '/blog/' || path === '/blog/index.html' || path.startsWith('/blog/')) {
      src = '/nd-blog-enhancements.js?v=20260927a';
    }

    if (!src || document.querySelector('script[data-nd-page-enhancements]')) return;

    const script = document.createElement('script');
    script.src = src;
    script.defer = true;
    script.dataset.ndPageEnhancements = 'true';
    document.head.appendChild(script);
  }

  function normalized(value) {
    if (!value) return '/';
    const url = new URL(value, window.location.origin);
    let p = url.pathname.replace(/\/index\.html$/, '/');
    if (p.length > 1 && p.endsWith('/')) return p;
    return p;
  }

  function isActive(href) {
    const current = normalized(path);
    const target = normalized(href);
    if (target === '/' || target === '/fr/') return current === target;
    if (target === '/blog/' || target === '/fr/blog/') return current.startsWith(target);
    return current === target;
  }

  function makeLink(label, href, extra = '') {
    const a = document.createElement('a');
    a.className = 'nd-nav-link';
    if (extra === 'submit') a.classList.add('nd-submit-link');
    if (extra === 'language') a.classList.add('nd-language-link');
    a.href = href;
    a.textContent = label;
    if (isActive(href)) {
      a.classList.add('active');
      a.setAttribute('aria-current', 'page');
    }
    return a;
  }

  function removeExistingShell() {
    const directHeader = document.querySelector('body > header');
    let nav = null;
    if (directHeader) nav = directHeader.querySelector('nav');
    if (!nav) nav = document.querySelector('body > nav');
    if (nav && nav.parentElement !== directHeader) nav.remove();
    if (directHeader) directHeader.remove();
  }

  function buildShell() {
    removeExistingShell();

    const header = document.createElement('header');
    header.className = 'nd-site-header';
    header.setAttribute('data-nd-shell', 'header');
    const logoLink = document.createElement('a');
    logoLink.className = 'nd-site-logo';
    logoLink.href = root;
    logoLink.setAttribute('aria-label', isFrench ? 'Accueil Northern Dial' : 'Northern Dial home');
    const img = document.createElement('img');
    img.src = LOGO;
    img.alt = 'Northern Dial';
    logoLink.appendChild(img);
    header.appendChild(logoLink);

    const nav = document.createElement('nav');
    nav.className = 'nd-site-nav';
    nav.setAttribute('aria-label', isFrench ? 'Navigation principale' : 'Main navigation');
    nav.setAttribute('data-nd-shell', 'nav');

    const inner = document.createElement('div');
    inner.className = 'nd-nav-inner';

    const mobileToggle = document.createElement('button');
    mobileToggle.className = 'nd-mobile-toggle';
    mobileToggle.type = 'button';
    mobileToggle.setAttribute('aria-expanded', 'false');
    mobileToggle.innerHTML = `<span>Menu</span><span class="nd-menu-icon" aria-hidden="true">☰</span>`;
    inner.appendChild(mobileToggle);

    const primary = document.createElement('div');
    primary.className = 'nd-primary-links';
    primary.style.display = 'flex';
    links.forEach(([label, href]) => primary.appendChild(makeLink(label, href)));

    const more = document.createElement('div');
    more.className = 'nd-more';
    const moreButton = document.createElement('button');
    moreButton.className = 'nd-more-button';
    moreButton.type = 'button';
    moreButton.setAttribute('aria-expanded', 'false');
    moreButton.textContent = isFrench ? 'Plus' : 'More';
    const moreMenu = document.createElement('div');
    moreMenu.className = 'nd-more-menu';
    secondary.forEach(([label, href, extra]) => moreMenu.appendChild(makeLink(label, href, extra)));
    more.appendChild(moreButton);
    more.appendChild(moreMenu);
    primary.appendChild(more);
    inner.appendChild(primary);
    nav.appendChild(inner);

    document.body.insertBefore(nav, document.body.firstChild);
    document.body.insertBefore(header, nav);

    mobileToggle.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      mobileToggle.setAttribute('aria-expanded', String(open));
      mobileToggle.querySelector('.nd-menu-icon').textContent = open ? '✕' : '☰';
    });

    moreButton.addEventListener('click', (event) => {
      event.stopPropagation();
      const open = more.classList.toggle('open');
      moreButton.setAttribute('aria-expanded', String(open));
    });

    document.addEventListener('click', (event) => {
      if (!more.contains(event.target)) {
        more.classList.remove('open');
        moreButton.setAttribute('aria-expanded', 'false');
      }
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        more.classList.remove('open');
        moreButton.setAttribute('aria-expanded', 'false');
        nav.classList.remove('open');
        mobileToggle.setAttribute('aria-expanded', 'false');
        mobileToggle.querySelector('.nd-menu-icon').textContent = '☰';
      }
    });
  }

  function registerServiceWorker() {
    if (!('serviceWorker' in navigator) || window.self !== window.top) return;
    navigator.serviceWorker.register('/service-worker.js').catch(() => {});
  }

  function loadI18n() {
    // The homepage already ships its purpose-built language engine.
    if (isHomepage && document.querySelector('script[src*="homepage_language.js"]')) return;
    if (document.querySelector('script[data-nd-i18n]')) return;

    const script = document.createElement('script');
    script.src = isFrench
      ? '/nd-i18n.js?v=20260927b'
      : '/nd-language-links.js?v=20260927a';
    script.defer = true;
    script.dataset.ndI18n = 'true';
    document.head.appendChild(script);
  }


  /* ND_PERSISTENT_PLAYER_START */
  function initPersistentPlayer() {
    // The parent document owns the live stream. Framed pages keep their normal
    // page scripts and styling, but never create a second persistent player.
    if (window.self !== window.top) return;
    if (document.querySelector('[data-nd-persistent-player]')) return;

    const streamUrl = 'https://a10.asurahosting.com:7220/radio.mp3';
    const nowPlayingUrl = 'https://a10.asurahosting.com/api/nowplaying/northern_dial';
    const initialUrl = window.location.href;
    const initialTitle = document.title;
    const hadHomepagePlayer = Boolean(document.getElementById('radioStream'));

    const player = document.createElement('div');
    player.className = 'nd-mini-player';
    player.dataset.ndPersistentPlayer = 'true';
    player.setAttribute('role', 'region');
    player.setAttribute('aria-label', isFrench ? 'Lecteur radio Northern Dial' : 'Northern Dial radio player');
    player.innerHTML = [
      '<div class="nd-mini-player-inner">',
        '<button class="nd-mini-play" type="button" aria-label="Play Northern Dial"><span class="nd-mini-play-glyph" aria-hidden="true"></span><span class="nd-mini-pause-glyph" aria-hidden="true"><i></i><i></i></span></button>',
        '<div class="nd-mini-copy">',
          '<div class="nd-mini-status"><span class="nd-mini-live-dot" aria-hidden="true"></span><span class="nd-mini-status-text">Northern Dial · Ready</span></div>',
          '<div class="nd-mini-track">Northern Dial Radio</div>',
          '<div class="nd-mini-artist">All Killer, All CanCon</div>',
        '</div>',
        '<a class="nd-mini-profile" href="/artists.html" hidden>Meet the Artist</a>',
      '</div>'
    ].join('');

    let audio = window.ND_SHARED_AUDIO || document.getElementById('radioStream');
    if (!audio) {
      audio = document.createElement('audio');
      audio.id = 'ndPersistentAudio';
      audio.preload = 'none';
      audio.src = streamUrl;
      audio.volume = 0.7;
    }
    window.ND_SHARED_AUDIO = audio;
    audio.classList.add('nd-persistent-audio');
    player.appendChild(audio);
    document.body.appendChild(player);

    const playButton = player.querySelector('.nd-mini-play');
    const statusText = player.querySelector('.nd-mini-status-text');
    const trackText = player.querySelector('.nd-mini-track');
    const artistText = player.querySelector('.nd-mini-artist');
    const profileLink = player.querySelector('.nd-mini-profile');

    let artistLookupPromise = null;
    let currentArtistKey = '';
    let initialPage = null;
    let frame = null;
    let pendingFrame = null;
    let navigationToken = 0;
    let homeObserver = null;
    let shellMode = false;
    let expectedFrameUrl = '';
    let userWantsPlayback = !audio.paused && !audio.ended;
    let resumeTimer = null;
    let latestNowPlayingData = null;
    let playRequestPending = false;

    // One stream per top-level Northern Dial session. Framed pages can use
    // this API instead of creating/controlling their own audio element.
    window.NDPlayer = {
      audio,
      play: async () => {
        userWantsPlayback = true;
        enforceSingleAudio();
        await audio.play();
        renderPlaybackState();
      },
      pause: () => {
        userWantsPlayback = false;
        audio.pause();
        renderPlaybackState();
      },
      setVolume: (value) => {
        audio.volume = Math.max(0, Math.min(1, Number(value) || 0));
      },
      isPlaying: () => !audio.paused && !audio.ended
    };

    function setPlayerHeight() {
      const height = Math.ceil(player.getBoundingClientRect().height || 76);
      document.documentElement.style.setProperty('--nd-player-height', height + 'px');
    }
    setPlayerHeight();
    if ('ResizeObserver' in window) {
      const observer = new ResizeObserver(setPlayerHeight);
      observer.observe(player);
    } else {
      window.addEventListener('resize', setPlayerHeight, { passive: true });
    }

    function setMiniVisible(visible) {
      player.classList.toggle('nd-mini-visible', Boolean(visible));
      if (!isHomepage) document.body.classList.add('nd-has-mini-player');
    }

    if (isHomepage && hadHomepagePlayer) {
      const homepagePlayer = document.querySelector('.player-section');
      if (homepagePlayer && 'IntersectionObserver' in window) {
        homeObserver = new IntersectionObserver(([entry]) => {
          if (!shellMode) setMiniVisible(!entry.isIntersecting);
        }, { threshold: 0 });
        homeObserver.observe(homepagePlayer);
      }
    } else {
      setMiniVisible(true);
    }

    function neutralizeDuplicateAudio(rootDocument) {
      const doc = rootDocument || document;
      try {
        doc.querySelectorAll('audio').forEach((candidate) => {
          if (candidate === audio) return;
          try {
            candidate.pause();
            candidate.removeAttribute('src');
            candidate.querySelectorAll('source').forEach((source) => source.removeAttribute('src'));
            candidate.load();
            candidate.dataset.ndSuppressedAudio = 'true';
          } catch (_) {}
        });
      } catch (_) {}
    }

    function enforceSingleAudio() {
      neutralizeDuplicateAudio(document);
      if (frame?.contentDocument) neutralizeDuplicateAudio(frame.contentDocument);
      if (pendingFrame?.contentDocument) neutralizeDuplicateAudio(pendingFrame.contentDocument);
    }

    function renderPlaybackState() {
      const playing = !audio.paused && !audio.ended;
      playButton.classList.toggle('playing', playing);
      playButton.setAttribute('aria-label', playing ? 'Pause Northern Dial' : 'Play Northern Dial');
      playButton.setAttribute('aria-busy', playRequestPending ? 'true' : 'false');
      if (!playRequestPending) {
        statusText.textContent = playing ? 'Northern Dial · Live' : 'Northern Dial · Paused';
      }
      player.classList.toggle('is-playing', playing);
    }

    async function resumeIfWanted() {
      if (!userWantsPlayback || !audio.paused) return;
      enforceSingleAudio();
      if (resumeTimer) {
        window.clearTimeout(resumeTimer);
        resumeTimer = null;
      }
      try {
        await audio.play();
        renderPlaybackState();
      } catch (_) {
        statusText.textContent = 'Northern Dial · Tap play to resume';
      }
    }

    function scheduleResume() {
      if (!shellMode || !userWantsPlayback) return;
      if (resumeTimer) window.clearTimeout(resumeTimer);
      resumeTimer = window.setTimeout(() => {
        resumeTimer = null;
        resumeIfWanted();
      }, 80);
    }

    async function loadArtistLookup() {
      if (!artistLookupPromise) {
        artistLookupPromise = fetch('/artist-profile-index.json', { cache: 'no-cache' })
          .then((response) => response.ok ? response.json() : {})
          .catch(() => ({}));
      }
      return artistLookupPromise;
    }

    function normalizeArtist(value) {
      return String(value || '')
        .normalize('NFKD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[’‘]/g, "'")
        .replace(/\s+/g, ' ')
        .trim()
        .toLocaleLowerCase('en-CA');
    }

    function primaryArtist(value) {
      return String(value || '')
        .split(/\s+(?:feat\.?|ft\.?|featuring|with|x)\s+|,\s*|\s+&\s+/i)[0]
        .trim();
    }

    async function updateProfileLink(artist) {
      const key = normalizeArtist(artist);
      if (!key || key === currentArtistKey) return;
      currentArtistKey = key;
      profileLink.hidden = true;

      const lookup = await loadArtistLookup();
      const primary = primaryArtist(artist);
      const href = lookup[artist] ||
        lookup[primary] ||
        Object.entries(lookup).find(([name]) => normalizeArtist(name) === key)?.[1] ||
        Object.entries(lookup).find(([name]) => normalizeArtist(name) === normalizeArtist(primary))?.[1];

      if (!href) return;
      profileLink.href = href;
      profileLink.textContent = isFrench ? "Voir l'artiste" : 'Meet the Artist';
      profileLink.setAttribute('aria-label', 'Meet ' + (primary || artist) + ' on Northern Dial');
      profileLink.hidden = false;
    }

    function updateMediaSession(title, artist) {
      if (!('mediaSession' in navigator) || typeof MediaMetadata === 'undefined') return;
      try {
        navigator.mediaSession.metadata = new MediaMetadata({
          title: title || 'Northern Dial Radio',
          artist: artist || 'All Killer, All CanCon',
          album: 'Northern Dial Radio',
          artwork: [{ src: LOGO, sizes: '512x512', type: 'image/png' }]
        });
        navigator.mediaSession.setActionHandler('play', () => {
          userWantsPlayback = true;
          enforceSingleAudio();
          audio.play();
        });
        navigator.mediaSession.setActionHandler('pause', () => {
          userWantsPlayback = false;
          audio.pause();
        });
      } catch (_) {}
    }


    function broadcastStationData(data) {
      latestNowPlayingData = data;
      try {
        document.dispatchEvent(new CustomEvent('nd:nowplaying', { detail: data }));
      } catch (_) {}

      if (frame && frame.contentWindow && frame.contentDocument) {
        try {
          frame.contentDocument.dispatchEvent(
            new frame.contentWindow.CustomEvent('nd:nowplaying', { detail: data })
          );
        } catch (_) {}
      }
    }

    async function refreshNowPlaying() {
      if (document.hidden && (audio.paused || audio.ended)) return;
      try {
        const response = await fetch(nowPlayingUrl, { cache: 'no-store' });
        if (!response.ok) return;
        const data = await response.json();
        broadcastStationData(data);
        const song = data && data.now_playing && data.now_playing.song;
        if (!song) return;
        const title = song.title || 'Unknown Track';
        const artist = song.artist || 'Unknown Artist';
        trackText.textContent = title;
        artistText.textContent = artist;
        updateProfileLink(artist);
        updateMediaSession(title, artist);
      } catch (_) {}
    }

    playButton.addEventListener('click', async () => {
      if (playRequestPending) return;

      try {
        if (audio.paused || audio.ended) {
          playRequestPending = true;
          userWantsPlayback = true;
          enforceSingleAudio();

          // Acknowledge the tap immediately so iOS stream startup never feels dead.
          playButton.classList.add('playing');
          playButton.setAttribute('aria-busy', 'true');
          statusText.textContent = 'Northern Dial · Connecting';

          await audio.play();
        } else {
          userWantsPlayback = false;
          audio.pause();
        }
      } catch (_) {
        userWantsPlayback = false;
        statusText.textContent = 'Northern Dial · Tap to retry';
      } finally {
        playRequestPending = false;
        renderPlaybackState();
      }
    });

    audio.addEventListener('playing', () => {
      userWantsPlayback = true;
      renderPlaybackState();
    });

    audio.addEventListener('pause', () => {
      renderPlaybackState();
      if (shellMode && userWantsPlayback) scheduleResume();
      else if (!shellMode) userWantsPlayback = false;
    });

    audio.addEventListener('ended', () => {
      renderPlaybackState();
      if (shellMode && userWantsPlayback) scheduleResume();
    });
    audio.addEventListener('error', () => {
      statusText.textContent = 'Northern Dial · Connection error';
      renderPlaybackState();
    });

    document.addEventListener('play', (event) => {
      const candidate = event.target;
      if (candidate instanceof HTMLMediaElement && candidate !== audio) {
        try {
          candidate.pause();
          candidate.removeAttribute('src');
          candidate.querySelectorAll?.('source').forEach((source) => source.removeAttribute('src'));
          candidate.load();
        } catch (_) {}
      }
    }, true);

    renderPlaybackState();
    refreshNowPlaying();
    window.setInterval(refreshNowPlaying, 10000);
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) refreshNowPlaying();
    });

    function isModifiedClick(event) {
      return event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey;
    }

    function linkUrl(anchor, baseHref) {
      if (!anchor || !anchor.getAttribute('href')) return null;
      if (anchor.hasAttribute('download')) return null;
      const target = (anchor.getAttribute('target') || '').toLowerCase();
      if (target && target !== '_self') return null;

      let url;
      try {
        url = new URL(anchor.getAttribute('href'), baseHref || window.location.href);
      } catch (_) {
        return null;
      }

      if (url.origin !== window.location.origin) return null;
      if (!/^https?:$/.test(url.protocol)) return null;
      if (/\.(?:pdf|zip|mp3|m4a|wav|flac|jpg|jpeg|png|gif|webp|svg|json|xml)$/i.test(url.pathname)) return null;
      return url;
    }

    function wrapInitialPage() {
      if (initialPage) return;
      initialPage = document.createElement('div');
      initialPage.id = 'nd-initial-document';

      const nodes = [...document.body.childNodes].filter((node) => node !== player && node !== frame);
      nodes.forEach((node) => initialPage.appendChild(node));
      document.body.insertBefore(initialPage, player);
    }

    function wireFrameDocument(activeFrame, destination) {
      const childWindow = activeFrame.contentWindow;
      const childDocument = activeFrame.contentDocument;
      if (!childWindow || !childDocument || childWindow.location.origin !== window.location.origin) {
        return false;
      }

      const loadedUrl = childWindow.location.href;
      if (!loadedUrl || loadedUrl === 'about:blank') return false;

      const targetUrl = new URL(destination, initialUrl);
      const actualUrl = new URL(loadedUrl);
      const targetPath = targetUrl.pathname.replace(/\/index\.html$/, '/');
      const actualPath = actualUrl.pathname.replace(/\/index\.html$/, '/');

      if (actualUrl.origin !== targetUrl.origin ||
          actualPath !== targetPath ||
          actualUrl.search !== targetUrl.search) {
        return false;
      }

      const canonical = childDocument.querySelector('link[rel="canonical"]');
      if (canonical) {
        try {
          const canonicalUrl = new URL(canonical.href, loadedUrl);
          const canonicalPath = canonicalUrl.pathname.replace(/\/index\.html$/, '/');
          if (canonicalUrl.origin === targetUrl.origin &&
              canonicalPath !== targetPath &&
              targetPath !== '/') {
            return false;
          }
        } catch (_) {}
      }

      if (latestNowPlayingData) {
        try {
          childDocument.dispatchEvent(
            new childWindow.CustomEvent('nd:nowplaying', { detail: latestNowPlayingData })
          );
        } catch (_) {}
      }

      if (childWindow.location.pathname === '/' || childWindow.location.pathname === '/index.html') {
        const style = childDocument.createElement('style');
        style.dataset.ndFramedHome = 'true';
        style.textContent = '.player-section{display:none!important}.home-top-grid{display:block!important}.home-top-grid .discovery-banner{margin:0 0 38px!important}';
        childDocument.head.appendChild(style);

        neutralizeDuplicateAudio(childDocument);

        // Safari can execute framed Home scripts before they see the parent
        // controller. Capture the controls here so they always operate the
        // single parent stream, regardless of child-script timing.
        childDocument.addEventListener('click', async (event) => {
          const control = event.target.closest && event.target.closest('#playPauseBtn');
          if (!control) return;
          event.preventDefault();
          event.stopImmediatePropagation();

          try {
            if (audio.paused || audio.ended) {
              userWantsPlayback = true;
              enforceSingleAudio();
              await audio.play();
            } else {
              userWantsPlayback = false;
              audio.pause();
            }
          } catch (_) {}
          renderPlaybackState();
        }, true);

        childDocument.addEventListener('input', (event) => {
          const control = event.target.closest && event.target.closest('#volumeSlider');
          if (!control) return;
          event.stopImmediatePropagation();
          audio.volume = Math.max(0, Math.min(1, Number(control.value) / 100));
        }, true);

        const childVolume = childDocument.getElementById('volumeSlider');
        if (childVolume) childVolume.value = Math.round(audio.volume * 100);
      }

      childDocument.addEventListener('click', (event) => {
        if (event.defaultPrevented || isModifiedClick(event)) return;
        const anchor = event.target.closest && event.target.closest('a');
        if (!anchor) return;

        const href = anchor.getAttribute('href');
        if (!href) return;

        let candidate;
        try {
          candidate = new URL(href, childWindow.location.href);
        } catch (_) {
          return;
        }

        if (candidate.origin !== window.location.origin) {
          if (!anchor.getAttribute('target')) {
            anchor.setAttribute('target', '_blank');
            anchor.setAttribute('rel', 'noopener');
          }
          return;
        }

        if (candidate.pathname === childWindow.location.pathname &&
            candidate.search === childWindow.location.search &&
            candidate.hash) {
          return;
        }

        const internal = linkUrl(anchor, childWindow.location.href);
        if (!internal) return;
        event.preventDefault();
        openPersistentPage(internal.href, true);
      }, true);

      return true;
    }

    function loadDestinationFrame(destination, pushHistory) {
      const token = ++navigationToken;

      if (pendingFrame) {
        pendingFrame.remove();
        pendingFrame = null;
      }

      const nextFrame = document.createElement('iframe');
      pendingFrame = nextFrame;
      nextFrame.className = 'nd-persistent-frame nd-persistent-frame-loading';
      nextFrame.title = isFrench ? 'Contenu Northern Dial' : 'Northern Dial page content';
      nextFrame.setAttribute('loading', 'eager');
      nextFrame.setAttribute('aria-hidden', 'true');

      // Set src before insertion. This matters on iOS Safari: a blank same-origin
      // frame can inherit/resolve against the changing parent URL and render empty.
      nextFrame.src = destination;

      let retried = false;
      nextFrame.addEventListener('load', () => {
        if (token !== navigationToken) {
          nextFrame.remove();
          return;
        }

        let ready = false;
        try {
          ready = wireFrameDocument(nextFrame, destination);
        } catch (_) {
          ready = false;
        }

        if (!ready) {
          if (!retried) {
            retried = true;
            try {
              const retryUrl = new URL(destination, initialUrl);
              retryUrl.searchParams.set('_ndnav', String(Date.now()));
              nextFrame.contentWindow.location.replace(retryUrl.href);
            } catch (_) {}
          }
          return;
        }

        if (frame && frame !== nextFrame) frame.remove();
        frame = nextFrame;
        pendingFrame = null;

        nextFrame.classList.remove('nd-persistent-frame-loading');
        nextFrame.removeAttribute('aria-hidden');

        document.body.classList.add('nd-persistent-browsing', 'nd-has-mini-player');
        if (initialPage) initialPage.hidden = true;

        try {
          const loadedTitle = nextFrame.contentDocument && nextFrame.contentDocument.title;
          if (loadedTitle) document.title = loadedTitle;
        } catch (_) {}

        expectedFrameUrl = destination;
        if (pushHistory) {
          history.pushState(
            Object.assign({}, history.state, { ndPersistentUrl: destination }),
            '',
            destination
          );
        }

        updateMediaSession(trackText.textContent, artistText.textContent);
        resumeIfWanted();
        window.scrollTo(0, 0);
      });

      document.body.insertBefore(nextFrame, player);
    }

    function openPersistentPage(url, pushHistory) {
      const wasPlaying = !audio.paused && !audio.ended;
      if (wasPlaying) userWantsPlayback = true;

      const destination = new URL(url, initialUrl).href;
      wrapInitialPage();
      shellMode = true;
      setMiniVisible(true);

      // Keep the current page visible until the destination has verifiably
      // loaded. This prevents Safari from ever exposing a blank content frame.
      loadDestinationFrame(destination, pushHistory);
      resumeIfWanted();
    }

    function restoreInitialPage() {
      if (!initialPage) return;
      shellMode = false;
      document.body.classList.remove('nd-persistent-browsing');
      frame.hidden = true;
      initialPage.hidden = false;
      document.title = initialTitle;

      if (isHomepage && hadHomepagePlayer) {
        const homepagePlayer = initialPage.querySelector('.player-section');
        if (homepagePlayer) {
          const rect = homepagePlayer.getBoundingClientRect();
          setMiniVisible(rect.bottom <= 0 || rect.top >= window.innerHeight);
        } else {
          setMiniVisible(false);
        }
      } else {
        setMiniVisible(true);
      }
    }

    document.addEventListener('click', (event) => {
      if (event.defaultPrevented || isModifiedClick(event)) return;
      if (event.target.closest && event.target.closest('[data-nd-persistent-player]')) return;

      const anchor = event.target.closest && event.target.closest('a');
      if (!anchor) return;
      const url = linkUrl(anchor, window.location.href);
      if (!url) return;

      if (url.pathname === window.location.pathname &&
          url.search === window.location.search &&
          url.hash) {
        return;
      }

      // Preserve normal navigation until the listener has actively started audio.
      // Once playing, internal navigation becomes app-like and the stream survives.
      if (audio.paused || audio.ended) return;

      event.preventDefault();
      openPersistentPage(url.href, true);
    }, true);

    window.addEventListener('popstate', () => {
      if (window.location.href === initialUrl) {
        restoreInitialPage();
        return;
      }
      if (!audio.paused && !audio.ended) {
        openPersistentPage(window.location.href, false);
      }
    });

    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && shellMode && userWantsPlayback) resumeIfWanted();
    });

    profileLink.addEventListener('click', (event) => {
      if (audio.paused || audio.ended) return;
      const url = linkUrl(profileLink, window.location.href);
      if (!url) return;
      event.preventDefault();
      openPersistentPage(url.href, true);
    });
  }
  /* ND_PERSISTENT_PLAYER_END */


  function initArtistBackToTop() {
    if (path !== '/artists.html' && path !== '/fr/artists.html') return;
    const list = document.getElementById('artistList');
    if (!list || document.querySelector('.nd-artist-back-to-top')) return;

    const rows = [...list.querySelectorAll(':scope > details')];
    const firstB = rows.find(row => /^B/i.test(row.querySelector('summary')?.textContent.trim() || ''));
    if (!firstB) return;

    const style = document.createElement('style');
    style.textContent = `
      .nd-artist-back-to-top {
        position: fixed; right: max(16px, env(safe-area-inset-right));
        bottom: ${window.self !== window.top ? '16px' : 'calc(var(--nd-player-height, 76px) + 20px + env(safe-area-inset-bottom))'};
        z-index: 2147482500; min-height: 44px; padding: 12px 16px;
        border: 2px solid #fff; border-radius: 6px; background: #a82424;
        color: #fff; box-shadow: 0 3px 14px rgba(0,0,0,.25);
        font: 700 1rem 'Roboto Condensed', sans-serif; cursor: pointer;
      }
      .nd-artist-back-to-top[hidden],
      body.nd-persistent-browsing > .nd-artist-back-to-top { display: none !important; }
      .nd-artist-back-to-top:hover { background: #861b1b; }
      .nd-artist-back-to-top:focus-visible { outline: 3px solid #1a1a1a; outline-offset: 3px; }
    `;
    document.head.appendChild(style);

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'nd-artist-back-to-top';
    button.setAttribute('data-no-translate', '');
    button.textContent = isFrench ? 'Haut de page' : 'Back to top';
    button.hidden = true;
    document.body.appendChild(button);

    function update() {
      // The first B marks the end of the A section. Filtering can hide it.
      const boundary = firstB.getClientRects().length ? firstB
        : rows.find(row => row.getClientRects().length &&
          /^[B-Z]/i.test(row.querySelector('summary')?.textContent.trim() || ''));
      button.hidden = !boundary || boundary.getBoundingClientRect().top > 0;
    }

    let queued = false;
    function scheduleUpdate() {
      if (queued) return;
      queued = true;
      requestAnimationFrame(() => { queued = false; update(); });
    }
    window.addEventListener('scroll', scheduleUpdate, { passive: true });
    window.addEventListener('resize', scheduleUpdate);
    list.addEventListener('toggle', scheduleUpdate, true);
    document.addEventListener('input', scheduleUpdate);
    if ('ResizeObserver' in window) new ResizeObserver(scheduleUpdate).observe(list);

    button.addEventListener('click', () => {
      window.scrollTo({
        top: 0,
        behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'
      });
      const heading = document.getElementById('page-title');
      if (heading) {
        if (!heading.hasAttribute('tabindex')) heading.setAttribute('tabindex', '-1');
        heading.focus({ preventScroll: true });
      }
    });
    update();
  }

  function init() {
    registerServiceWorker();
    if (!isHomepage) buildShell();
    loadI18n();
    loadPageEnhancements();
    initArtistBackToTop();
    initPersistentPlayer();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
// Load the browser-local discovery mix on every page.
(() => {
  if (document.getElementById('nd-mix-script')) return;
  const script = document.createElement('script');
  script.id = 'nd-mix-script';
  script.src = '/nd-mix.js?v=20261008c';
  script.defer = true;
  document.head.appendChild(script);
})();
