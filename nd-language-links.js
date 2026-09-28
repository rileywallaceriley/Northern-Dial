(() => {
  const routePairs = {
    '/': '/fr/',
    '/index.html': '/fr/',
    '/about.html': '/fr/a-propos.html',
    '/archive.html': '/fr/archives.html',
    '/sessions.html': '/fr/seances.html',
    '/accessibility.html': '/fr/accessibilite.html',
    '/rights.html': '/fr/droits.html',
    '/artists.html': '/fr/artists.html',
    '/library.html': '/fr/library.html',
    '/discover.html': '/fr/discover.html',
    '/blog/': '/fr/blog/',
    '/blog/index.html': '/fr/blog/',
    '/blog/rochelle-jordan-disc-2-remix-series.html': '/fr/blog/rochelle-jordan-disc-2-remix-series.html',
    '/blog/if-you-like-kaytranada-canadian-artists.html': '/fr/blog/if-you-like-kaytranada-canadian-artists.html'
  };

  function saveLanguage(value) {
    try { localStorage.setItem('nd-language', value); } catch (_) {}
  }

  function counterpart() {
    const alternate = document.querySelector(
      'link[rel="alternate"][hreflang="fr-CA"],link[rel="alternate"][hreflang="fr"]'
    );
    if (alternate?.href) {
      const paired = new URL(alternate.href, window.location.origin);
      return `${paired.pathname}${paired.search}${paired.hash}`;
    }

    const direct = routePairs[window.location.pathname];
    if (direct) return direct;

    const url = new URL(window.location.href);
    url.searchParams.set('lang', 'fr');
    url.searchParams.delete('page');
    return `${url.pathname}${url.search}${url.hash}`;
  }

  function localizeLanguageControls() {
    const href = counterpart();
    const controls = document.querySelectorAll(
      '.nd-language-link,.language-switch,[data-language-toggle],a.lang'
    );

    controls.forEach((control) => {
      control.setAttribute('href', href);
      control.setAttribute('hreflang', 'fr-CA');
      control.setAttribute('lang', 'fr');
      control.textContent = 'Français';
      control.onclick = () => saveLanguage('fr');
    });
  }

  function addLanguageControlIfMissing() {
    if (document.querySelector('.nd-language-link,.language-switch,[data-language-toggle],a.lang')) return;

    const nav = document.querySelector('.nd-more-menu,.nd-primary-links,.mobile-menu-links,.page-nav');
    if (!nav) return;

    const a = document.createElement('a');
    a.className = 'nd-nav-link nd-language-link';
    a.href = counterpart();
    a.hreflang = 'fr-CA';
    a.lang = 'fr';
    a.textContent = 'Français';
    a.onclick = () => saveLanguage('fr');
    nav.appendChild(a);
  }

  function addHreflang() {
    if (!document.head) return;

    const english = window.location.pathname;
    const french = counterpart();

    [['en-CA', english], ['fr-CA', french], ['x-default', english]].forEach(([hreflang, href]) => {
      if (document.head.querySelector(`link[rel="alternate"][hreflang="${hreflang}"]`)) return;
      const link = document.createElement('link');
      link.rel = 'alternate';
      link.hreflang = hreflang;
      link.href = new URL(href, window.location.origin).href;
      document.head.appendChild(link);
    });
  }

  function apply() {
    document.documentElement.lang = 'en-CA';
    document.documentElement.dataset.ndLanguage = 'en';
    saveLanguage('en');
    addLanguageControlIfMissing();
    localizeLanguageControls();
    addHreflang();
  }

  window.NDI18N = {
    lang: 'en',
    t: (value) => value,
    counterpart: () => counterpart(),
    apply,
    setLanguage: () => {
      saveLanguage('fr');
      window.location.href = counterpart();
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', apply, { once: true });
  } else {
    apply();
  }
})();
