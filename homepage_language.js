(() => {
  const STORAGE_KEY = 'northernDialLanguage';

  const EN_TO_FR = {
    'Independent Canadian Music Radio': 'Radio musicale canadienne indépendante',
    'NOW PLAYING': 'EN CE MOMENT',
    'LIVE NOW': 'EN DIRECT',
    'PAUSED': 'EN PAUSE',
    'All Killer, All CanCon': 'Que du bon, que du CanCon',
    'Visualizer': 'Visualiseur',
    'Find Your Next Canadian Artist': 'Découvrez votre prochain artiste canadien',
    'Pick a genre, era or artist you already love and we’ll dial up five Canadian artists worth checking out.': 'Choisissez un genre, une époque ou un artiste que vous aimez déjà et nous vous proposerons cinq artistes canadiens à découvrir.',
    'Start Discovering': 'Commencer la découverte',
    'Home': 'Accueil',
    'Songs': 'Chansons',
    'Artists': 'Artistes',
    'Discover': 'Découvrir',
    'About': 'À propos',
    'Submit': 'Soumettre',
    'Northern Dial is an independent Canadian radio station built for people who actually care about music.': 'Northern Dial est une station de radio canadienne indépendante conçue pour les gens qui aiment vraiment la musique.',
    'This station exists because Canadian music deserves space not just in quotas, but in context. We believe the best songs hit differently depending on the hour, the season, and where you are. So we built a station that moves with you.': 'Cette station existe parce que la musique canadienne mérite une place qui va au-delà des quotas et qui lui donne du contexte. Nous croyons que les meilleures chansons résonnent différemment selon l’heure, la saison et l’endroit où l’on se trouve. Nous avons donc créé une station qui évolue avec vous.',
    'We stream 24/7 and add new music into rotation constantly. Interested in having your music  or podcast played? Scroll down and click our submission box.': 'Nous diffusons 24 heures sur 24, 7 jours sur 7 et ajoutons constamment de nouvelles musiques à la rotation. Vous souhaitez faire diffuser votre musique ou votre balado? Faites défiler la page et utilisez notre formulaire de soumission.',
    'About the Northern Dial project →': 'À propos du projet Northern Dial →',
    'Recently Played': 'Récemment diffusé',
    'Loading...': 'Chargement…',
    'Explore Recent Songs': 'Explorer les chansons récentes',
    'Browse recently played tracks and search our catalog': 'Parcourez les titres récemment diffusés et recherchez dans notre catalogue',
    'Browse Now →': 'Parcourir →',
    'On Air Daily': 'À l’antenne chaque jour',
    'A playlist that feels like sunrise and highways - pop, indie, rock, R&B that moves with the morning.': 'Une sélection qui évoque les levers de soleil et la route : pop, indie, rock et R&B pour accompagner la matinée.',
    'A hip-hop forward block rooted in Canadian voices - from golden era hits to new rap chemistry.': 'Un bloc axé sur le hip-hop et ancré dans les voix canadiennes, des classiques de l’âge d’or aux nouvelles sonorités rap.',
    'Late night vibes for deeper listening - mellow beats, smooth grooves, edge-of-town energy.': 'Une ambiance de fin de soirée pour une écoute plus profonde : rythmes feutrés, grooves souples et énergie nocturne.',
    'Request A Song': 'Demander une chanson',
    "Got a track in mind? Submit a request and we'll add it to the rotation.": 'Une chanson en tête? Faites une demande et nous l’ajouterons à la rotation.',
    'Submit A Request': 'Faire une demande',
    'Submit Your Music': 'Soumettez votre musique',
    'Canadian artist or podcaster? Share your tracks with us for airplay on Northern Dial.': 'Artiste canadien ou créateur de balado? Faites-nous parvenir vos titres pour une diffusion sur Northern Dial.',
    'Submit Now': 'Soumettre maintenant',
    'Open-Source Community Project': 'Projet open source',
    'Explore our bigger picture and discover how you can get involved in building the future of Canadian independent radio.': 'Découvrez notre vision et voyez comment vous pouvez contribuer à bâtir l’avenir de la radio indépendante canadienne.',
    'Learn More': 'En savoir plus',
    'Latest Stories': 'Derniers articles',
    'Artist features and deep dives from the Northern Dial blog': 'Portraits d’artistes et articles de fond du blogue Northern Dial',
    'View All Stories': 'Voir tous les articles',
    'Read More →': 'Lire la suite →',
    'Search': 'Rechercher',
    'Submit Music': 'Soumettre de la musique',
    'The Northern Dial Project': 'Le projet Northern Dial',
    'Northern Dial Project': 'Projet Northern Dial',
    'Sessions': 'Séances',
    'Archive & Atlas': 'Archives et atlas',
    'Accessibility': 'Accessibilité',
    'Our Mantra': 'Notre raison d’être',
    'Where We Are Now': 'Où nous en sommes',
    'The Vision': 'La vision',
    'How You Can Contribute': 'Comment contribuer',
    'Get Involved': 'Participer',
    'Install Northern Dial': 'Installer Northern Dial',
    'Add to your home screen for quick access': 'Ajoutez Northern Dial à votre écran d’accueil pour un accès rapide',
    'Install': 'Installer',
    'Later': 'Plus tard',
    'Install App': 'Installer l’application',
    'Wave': 'Vague',
    'Circle': 'Cercle',
    'Dots': 'Points',
    'Search for a song or artist...': 'Rechercher une chanson ou un artiste…',
    'Artist/Band Name *': 'Nom de l’artiste ou du groupe *',
    'Your Email *': 'Votre courriel *',
    'Track Links (SoundCloud, Spotify, YouTube, etc.) *': 'Liens vers les titres (SoundCloud, Spotify, YouTube, etc.) *',
    'Social Media (Instagram, Twitter, Website, etc.)': 'Réseaux sociaux (Instagram, X, site Web, etc.)',
    "Tell us about your music, your sound, where you're from...": 'Parlez-nous de votre musique, de votre son et de votre région…',
    'Your Name *': 'Votre nom *',
    "I'm interested in... *": 'Je souhaite contribuer à… *',
    "Tell us about your interest and how you'd like to contribute...": 'Parlez-nous de votre intérêt et de la façon dont vous aimeriez contribuer…',
    'Sponsorship and Funding': 'Commandites et financement',
    'Grassroots Promotion': 'Promotion communautaire',
    'Content Submission': 'Soumission de contenu',
    'Development and Design': 'Développement et design',
    'Hosting and Production': 'Animation et production',
    'Writing and Journalism': 'Rédaction et journalisme',
    'Other': 'Autre'
  };

  const FR_TO_EN = Object.fromEntries(Object.entries(EN_TO_FR).map(([en, fr]) => [fr, en]));

  const EN_TO_FR_ROUTES = {
    '/': '/?lang=fr',
    '/index.html': '/?lang=fr',
    '/library.html': '/fr/library.html',
    '/artists.html': '/fr/artists.html',
    '/discover.html': '/fr/discover.html',
    '/blog/': '/fr/blog/',
    '/blog/index.html': '/fr/blog/',
    '/about.html': '/fr/a-propos.html',
    '/sessions.html': '/fr/seances.html',
    '/archive.html': '/fr/archives.html',
    '/accessibility.html': '/fr/accessibilite.html',
    '/rights.html': '/fr/droits.html'
  };
  const FR_TO_EN_ROUTES = Object.fromEntries(Object.entries(EN_TO_FR_ROUTES).map(([en, fr]) => [fr, en]));

  function preserveWhitespace(value, replacement) {
    const leading = value.match(/^\s*/)?.[0] || '';
    const trailing = value.match(/\s*$/)?.[0] || '';
    return `${leading}${replacement}${trailing}`;
  }

  function translateTextNodes(root, dictionary) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    let node;
    while ((node = walker.nextNode())) nodes.push(node);

    for (const textNode of nodes) {
      const parent = textNode.parentElement;
      if (!parent || ['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEXTAREA'].includes(parent.tagName)) continue;
      const raw = textNode.nodeValue || '';
      const key = raw.trim();
      if (dictionary[key]) textNode.nodeValue = preserveWhitespace(raw, dictionary[key]);
    }
  }

  function translateAttributes(dictionary) {
    document.querySelectorAll('[placeholder], [aria-label], [title]').forEach((el) => {
      ['placeholder', 'aria-label', 'title'].forEach((attr) => {
        const value = el.getAttribute(attr);
        if (value && dictionary[value]) el.setAttribute(attr, dictionary[value]);
      });
    });
  }

  function updateInternalLinks(lang) {
    const map = lang === 'fr' ? EN_TO_FR_ROUTES : FR_TO_EN_ROUTES;
    document.querySelectorAll('a[href]').forEach((a) => {
      if (a.hasAttribute('data-language-toggle')) return;
      let url;
      try { url = new URL(a.getAttribute('href'), window.location.origin); } catch (_) { return; }
      if (url.origin !== window.location.origin) return;
      const key = `${url.pathname}${url.search}`;
      const target = map[key] || map[url.pathname];
      if (target) a.setAttribute('href', target + (url.hash || ''));
    });
  }

  function updateLanguageToggle(lang) {
    const toggle = document.querySelector('[data-language-toggle]');
    if (!toggle) return;
    if (lang === 'fr') {
      toggle.textContent = 'English';
      toggle.setAttribute('lang', 'en');
      toggle.setAttribute('aria-label', 'Switch homepage to English');
    } else {
      toggle.textContent = 'Français';
      toggle.setAttribute('lang', 'fr');
      toggle.setAttribute('aria-label', 'Afficher la page d’accueil en français');
    }
  }

  function updateUrlForLanguage(lang) {
    const url = new URL(window.location.href);
    if (lang === 'fr') url.searchParams.set('lang', 'fr');
    else url.searchParams.delete('lang');
    const next = `${url.pathname}${url.search}${url.hash}`;
    window.history.replaceState({}, '', next);
  }

  function updateMetadata(lang) {
    const description = document.querySelector('meta[name="description"]');
    const canonical = document.querySelector('link[rel="canonical"]');
    if (lang === 'fr') {
      document.title = 'Radio musicale canadienne indépendante | Northern Dial';
      if (description) description.setAttribute('content', 'Northern Dial est une radio canadienne indépendante diffusée 24 heures sur 24 pour découvrir des artistes, des chansons et des émissions d’ici.');
      if (canonical) canonical.setAttribute('href', 'https://www.northerndial.ca/?lang=fr');
    } else {
      document.title = 'Independent Canadian Music Radio | Northern Dial';
      if (description) description.setAttribute('content', 'Northern Dial is independent 24/7 Canadian music radio: discover emerging artists, Canadian songs, and curated shows from coast to coast.');
      if (canonical) canonical.setAttribute('href', 'https://www.northerndial.ca/');
    }
  }

  function applyLanguage(lang, persist = true) {
    const current = document.documentElement.dataset.ndLanguage || 'en';
    const dictionary = lang === 'fr' ? EN_TO_FR : FR_TO_EN;

    if (current !== lang) {
      translateTextNodes(document.body, dictionary);
      translateAttributes(dictionary);
    }

    document.documentElement.lang = lang === 'fr' ? 'fr-CA' : 'en-CA';
    document.documentElement.dataset.ndLanguage = lang;
    updateLanguageToggle(lang);
    updateInternalLinks(lang);
    updateMetadata(lang);
    if (persist) updateUrlForLanguage(lang);
    if (persist) {
      try { localStorage.setItem(STORAGE_KEY, lang); } catch (_) {}
    }
  }

  function closeMobileMenu() {
    const nav = document.querySelector('.mobile-menu-nav');
    const menuToggle = nav?.querySelector('.mobile-menu-toggle');
    const icon = menuToggle?.querySelector('.mobile-menu-icon');
    if (!nav || !menuToggle) return;
    nav.classList.remove('menu-open');
    menuToggle.setAttribute('aria-expanded', 'false');
    menuToggle.setAttribute('aria-label', 'Open navigation menu');
    if (icon) icon.textContent = '☰';
  }

  function installMutationTranslation() {
    let queued = false;
    const observer = new MutationObserver(() => {
      if ((document.documentElement.dataset.ndLanguage || 'en') !== 'fr' || queued) return;
      queued = true;
      requestAnimationFrame(() => {
        queued = false;
        translateTextNodes(document.body, EN_TO_FR);
        translateAttributes(EN_TO_FR);
        updateLanguageToggle('fr');
        updateInternalLinks('fr');
      });
    });
    observer.observe(document.body, { childList: true, subtree: true, characterData: true });
  }

  function init() {
    const toggle = document.querySelector('[data-language-toggle]');
    if (!toggle) return;

    toggle.addEventListener('click', (event) => {
      event.preventDefault();
      const current = document.documentElement.dataset.ndLanguage || 'en';
      applyLanguage(current === 'fr' ? 'en' : 'fr');
      closeMobileMenu();
    });

    // URL state is authoritative so a saved preference can never trap the homepage.
    const requested = new URLSearchParams(window.location.search).get('lang');
    const initial = requested === 'fr' ? 'fr' : 'en';
    applyLanguage(initial, false);
    installMutationTranslation();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
