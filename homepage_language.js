(() => {
  const FRENCH_HOME = '/fr/';

  function rememberFrench() {
    try {
      localStorage.setItem('nd-language', 'fr');
      localStorage.setItem('northernDialLanguage', 'fr');
    } catch (_) {}
  }

  function init() {
    const params = new URLSearchParams(window.location.search);

    // Retire the old ?lang=fr homepage mode in favour of the real French URL.
    if (params.get('lang') === 'fr') {
      rememberFrench();
      window.location.replace(FRENCH_HOME);
      return;
    }

    const toggle = document.querySelector('[data-language-toggle]');
    if (!toggle) return;

    toggle.textContent = 'Français';
    toggle.setAttribute('lang', 'fr');
    toggle.setAttribute('hreflang', 'fr-CA');
    toggle.setAttribute('aria-label', 'Afficher Northern Dial en français');

    if (toggle.tagName === 'A') toggle.setAttribute('href', FRENCH_HOME);

    toggle.addEventListener('click', (event) => {
      if (toggle.tagName !== 'A') event.preventDefault();
      rememberFrench();
      window.location.href = FRENCH_HOME;
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
