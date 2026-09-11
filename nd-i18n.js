(() => {
  const path = window.location.pathname;
  const params = new URLSearchParams(window.location.search);
  const stored = (() => { try { return localStorage.getItem('nd-language'); } catch (_) { return null; } })();
  const lang = path === '/fr' || path.startsWith('/fr/') || params.get('lang') === 'fr' || (!params.get('lang') && stored === 'fr' && !path.startsWith('/fr/')) ? 'fr' : 'en';

  const routePairs = {
    '/': '/fr/',
    '/index.html': '/fr/',
    '/about.html': '/fr/a-propos.html',
    '/archive.html': '/fr/archives.html',
    '/sessions.html': '/fr/seances.html',
    '/accessibility.html': '/fr/accessibilite.html',
    '/rights.html': '/fr/droits.html',
    '/blog/': '/fr/blog/',
    '/blog/index.html': '/fr/blog/',
    '/blog/rochelle-jordan-disc-2-remix-series.html': '/fr/blog/rochelle-jordan-disc-2-remix-series.html',
    '/blog/if-you-like-kaytranada-canadian-artists.html': '/fr/blog/if-you-like-kaytranada-canadian-artists.html',
    '/fr/': '/',
    '/fr/index.html': '/',
    '/fr/a-propos.html': '/about.html',
    '/fr/archives.html': '/archive.html',
    '/fr/seances.html': '/sessions.html',
    '/fr/accessibilite.html': '/accessibility.html',
    '/fr/droits.html': '/rights.html',
    '/fr/blog/': '/blog/',
    '/fr/blog/index.html': '/blog/',
    '/fr/blog/rochelle-jordan-disc-2-remix-series.html': '/blog/rochelle-jordan-disc-2-remix-series.html',
    '/fr/blog/if-you-like-kaytranada-canadian-artists.html': '/blog/if-you-like-kaytranada-canadian-artists.html'
  };

  const strings = {
    en: {
      'Home':'Home','Songs':'Songs','Artists':'Artists','Discover':'Discover','Blog':'Blog','About':'About','Submit':'Submit','More':'More','English':'English','Français':'Français',
      'Menu':'Menu','Listen Live':'Listen Live','Listen live':'Listen live','Explore Recently Played Songs':'Explore Recently Played Songs','Explore recently played songs':'Explore recently played songs',
      'Now Playing':'Now Playing','Recently Played':'Recently Played','Play':'Play','Pause':'Pause','Volume':'Volume','Close':'Close','Back':'Back','Search':'Search','Clear':'Clear',
      'Submit Your Music':'Submit Your Music','Artist / Band Name':'Artist / Band Name','Your Email':'Your Email','Track Links':'Track Links','Social Media':'Social Media','Tell us about your music, your sound, where you’re from...':'Tell us about your music, your sound, where you’re from...',
      'Read More':'Read More','Previous page':'Previous page','Next page':'Next page','Page':'Page','Explore artist profile':'Explore artist profile','View artist profile':'View artist profile',
      'Artist Features & Stories':'Artist Features & Stories','Digging deeper into the music we play':'Digging deeper into the music we play','Back to the Northern Dial blog':'Back to the Northern Dial blog',
      'Independent Canadian Music Discovery':'Independent Canadian Music Discovery','News Hit':'News Hit','Discovery':'Discovery','Keep Digging':'Keep Digging','Discover Artists':'Discover Artists','Browse the Archive':'Browse the Archive','Sources and Further Listening':'Sources and Further Listening'
    },
    fr: {
      'Home':'Accueil','Songs':'Chansons','Artists':'Artistes','Discover':'Découvrir','Blog':'Blogue','About':'À propos','Submit':'Soumettre','More':'Plus','English':'English','Français':'Français',
      'Menu':'Menu','Listen Live':'Écouter en direct','Listen live':'Écouter en direct','Explore Recently Played Songs':'Voir les chansons récemment diffusées','Explore recently played songs':'Voir les chansons récemment diffusées',
      'Now Playing':'En écoute','Recently Played':'Diffusées récemment','Play':'Lecture','Pause':'Pause','Volume':'Volume','Close':'Fermer','Back':'Retour','Search':'Rechercher','Clear':'Effacer',
      'Submit Your Music':'Soumettre votre musique','Artist / Band Name':'Nom de l’artiste ou du groupe','Your Email':'Votre courriel','Track Links':'Liens vers les morceaux','Social Media':'Réseaux sociaux','Tell us about your music, your sound, where you’re from...':'Parlez-nous de votre musique, de votre son et de votre provenance...',
      'Read More':'Lire la suite','Previous page':'Page précédente','Next page':'Page suivante','Page':'Page','Explore artist profile':'Voir le profil de l’artiste','View artist profile':'Voir le profil de l’artiste',
      'Artist Features & Stories':'Portraits d’artistes et histoires','Digging deeper into the music we play':'Aller plus loin dans la musique que nous diffusons','Back to the Northern Dial blog':'Retour au blogue Northern Dial',
      'Independent Canadian Music Discovery':'Découverte indépendante de la musique canadienne','News Hit':'Brève','Discovery':'Découverte','Keep Digging':'Continuer à découvrir','Discover Artists':'Découvrir des artistes','Browse the Archive':'Parcourir les archives','Sources and Further Listening':'Sources et écoute complémentaire'
    }
  };

  const exact = strings[lang];
  const reversePairs = Object.fromEntries(Object.entries(routePairs).map(([a,b]) => [b,a]));

  function saveLanguage(value) {
    try { localStorage.setItem('nd-language', value); } catch (_) {}
  }

  function counterpart(targetLang) {
    const current = window.location.pathname;
    const direct = routePairs[current] || reversePairs[current];
    if (direct) return direct;

    const url = new URL(window.location.href);
    if (targetLang === 'fr') {
      url.searchParams.set('lang', 'fr');
    } else {
      url.searchParams.delete('lang');
    }
    url.searchParams.delete('page');
    return `${url.pathname}${url.search}${url.hash}`;
  }

  function translateTextNode(node) {
    if (!node || node.nodeType !== Node.TEXT_NODE) return;
    const raw = node.nodeValue;
    const trimmed = raw.trim();
    if (!trimmed || !exact[trimmed]) return;
    node.nodeValue = raw.replace(trimmed, exact[trimmed]);
  }

  function translateElement(el) {
    if (!(el instanceof Element)) return;
    if (el.matches('script,style,code,pre,[data-no-translate]')) return;

    [...el.childNodes].forEach((node) => {
      if (node.nodeType === Node.TEXT_NODE) translateTextNode(node);
    });

    ['aria-label','title','placeholder'].forEach((attr) => {
      const value = el.getAttribute(attr);
      if (value && exact[value]) el.setAttribute(attr, exact[value]);
    });

    if (lang === 'fr') {
      if (el.classList.contains('profile-link') || el.classList.contains('artist-profile-link')) {
        el.innerHTML = el.innerHTML
          .replace(/^Explore /, 'Voir ')
          .replace(/ on Northern Dial/, ' sur Northern Dial')
          .replace(/’s Northern Dial artist profile/, ' sur Northern Dial')
          .replace(/ artist profile/, '');
      }
    }
  }

  function translateTree(root = document.body) {
    if (!root) return;
    translateElement(root);
    root.querySelectorAll('*').forEach(translateElement);
  }

  function localizeLanguageControls() {
    const targetLang = lang === 'fr' ? 'en' : 'fr';
    const targetHref = counterpart(targetLang);
    const controls = document.querySelectorAll('.nd-language-link,.language-switch,[data-language-toggle],a.lang');
    controls.forEach((control) => {
      control.setAttribute('href', targetHref);
      control.setAttribute('hreflang', targetLang === 'fr' ? 'fr-CA' : 'en-CA');
      control.setAttribute('lang', targetLang);
      control.textContent = targetLang === 'fr' ? 'Français' : 'English';
      control.addEventListener('click', () => saveLanguage(targetLang), { once: true });
    });
  }

  function addLanguageControlIfMissing() {
    if (document.querySelector('.nd-language-link,.language-switch,[data-language-toggle],a.lang')) return;
    const nav = document.querySelector('.nd-more-menu,.nd-primary-links,.mobile-menu-links,.page-nav');
    if (!nav) return;
    const a = document.createElement('a');
    a.className = 'nd-nav-link nd-language-link';
    a.href = counterpart(lang === 'fr' ? 'en' : 'fr');
    a.hreflang = lang === 'fr' ? 'en-CA' : 'fr-CA';
    a.lang = lang === 'fr' ? 'en' : 'fr';
    a.textContent = lang === 'fr' ? 'English' : 'Français';
    a.addEventListener('click', () => saveLanguage(lang === 'fr' ? 'en' : 'fr'));
    nav.appendChild(a);
  }

  function addHreflang() {
    const head = document.head;
    if (!head) return;
    const english = lang === 'fr' ? counterpart('en') : window.location.pathname;
    const french = lang === 'fr' ? window.location.pathname : counterpart('fr');
    const links = [
      ['en-CA', english],
      ['fr-CA', french],
      ['x-default', english]
    ];
    links.forEach(([hreflang, href]) => {
      if (head.querySelector(`link[rel="alternate"][hreflang="${hreflang}"]`)) return;
      const link = document.createElement('link');
      link.rel = 'alternate';
      link.hreflang = hreflang;
      link.href = new URL(href, window.location.origin).href;
      head.appendChild(link);
    });
  }

  function apply() {
    document.documentElement.lang = lang === 'fr' ? 'fr-CA' : 'en-CA';
    document.documentElement.dataset.ndLanguage = lang;
    saveLanguage(lang);
    translateTree();
    addLanguageControlIfMissing();
    localizeLanguageControls();
    addHreflang();
  }

  let queued = false;
  const observer = new MutationObserver(() => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      translateTree();
      addLanguageControlIfMissing();
      localizeLanguageControls();
    });
  });

  window.NDI18N = {
    lang,
    t: (value) => exact[value] || value,
    counterpart,
    apply,
    setLanguage: (value) => {
      saveLanguage(value);
      window.location.href = counterpart(value);
    }
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', apply, { once: true });
  else apply();
  observer.observe(document.documentElement, { childList: true, subtree: true });
})();
