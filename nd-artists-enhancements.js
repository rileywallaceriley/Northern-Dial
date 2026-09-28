(() => {
  const path = window.location.pathname;
  if (path !== '/artists.html') return;

  function enhanceArtistsDirectory() {
    if (path !== '/artists.html') return;
    if (document.querySelector('.nd-new-artists-cta')) return;

    const filter = [...document.querySelectorAll('input')].find((input) => {
      const placeholder = input.getAttribute('placeholder') || '';
      return /filter artists|filter.*songs|search artists/i.test(placeholder);
    });

    const cta = document.createElement('div');
    cta.className = 'nd-new-artists-cta';
    cta.style.cssText = 'display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;margin:24px 0 34px;padding:20px 22px;background:#1a1a1a;border:3px solid #CC3333;border-radius:8px;color:#fff;';

    const copy = document.createElement('div');
    copy.style.cssText = 'min-width:0;flex:1 1 320px;';
    copy.innerHTML = `<div style="font-family:'Oswald',sans-serif;font-size:.78rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#CC3333;margin-bottom:4px;">Northern Dial Discovery</div><div style="font-family:'Oswald',sans-serif;font-size:1.18rem;font-weight:700;line-height:1.25;">Looking for what’s next?</div><div style="font-family:'Roboto Condensed',sans-serif;font-size:.98rem;line-height:1.45;color:#ddd;margin-top:4px;">Meet emerging Canadian artists currently on our radar.</div>`;

    const button = document.createElement('a');
    button.href = '/new-canadian-artists.html';
    button.textContent = 'Discover New Canadian Artists';
    button.style.cssText = "display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:12px 18px;background:#CC3333;border:2px solid #CC3333;border-radius:6px;color:#fff;font-family:'Oswald',sans-serif;font-size:.88rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;text-decoration:none;white-space:nowrap;";

    cta.appendChild(copy);
    cta.appendChild(button);

    if (filter) {
      const wrapper = filter.parentElement || filter;
      wrapper.insertAdjacentElement('afterend', cta);
    } else {
      const main = document.querySelector('main') || document.body;
      main.insertBefore(cta, main.firstChild);
    }
  }

  enhanceArtistsDirectory();
})();
