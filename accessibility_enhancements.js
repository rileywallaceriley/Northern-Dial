(() => {
  const focusableSelector = [
    'a[href]', 'button:not([disabled])', 'input:not([disabled])',
    'select:not([disabled])', 'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])'
  ].join(',');

  let lastOpener = null;

  function labelControl(id, text) {
    const control = document.getElementById(id);
    if (!control) return;
    if (control.getAttribute('aria-label') || control.getAttribute('aria-labelledby')) return;
    const existing = document.querySelector(`label[for="${id}"]`);
    if (existing) return;
    const label = document.createElement('label');
    label.className = 'visually-hidden';
    label.htmlFor = id;
    label.textContent = text;
    control.parentNode.insertBefore(label, control);
  }

  function setLabel(selector, text) {
    const el = document.querySelector(selector);
    if (el && !el.getAttribute('aria-label')) el.setAttribute('aria-label', text);
  }

  function makeKeyboardActivatable(el) {
    if (!el || ['A', 'BUTTON', 'INPUT'].includes(el.tagName)) return;
    if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '0');
    if (!el.hasAttribute('role')) el.setAttribute('role', 'button');
    el.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        el.click();
      }
    });
  }

  function modalHeading(modal) {
    const heading = modal.querySelector('h1,h2,h3');
    if (!heading) return null;
    if (!heading.id) heading.id = `${modal.id || 'dialog'}-title`;
    return heading;
  }

  function prepareModal(modal) {
    if (!modal) return;
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    const heading = modalHeading(modal);
    if (heading) modal.setAttribute('aria-labelledby', heading.id);
    modal.querySelectorAll('.close-modal-btn,.visualizer-close').forEach((button) => {
      if (!button.getAttribute('aria-label')) button.setAttribute('aria-label', 'Close dialog');
    });
  }

  function isOpen(modal) {
    return modal.classList.contains('show') || modal.getAttribute('aria-hidden') === 'false';
  }

  function focusDialog(modal) {
    const focusable = [...modal.querySelectorAll(focusableSelector)].filter((el) => {
      return !el.hidden && el.offsetParent !== null;
    });
    const target = focusable[0] || modalHeading(modal) || modal;
    if (!target.hasAttribute('tabindex') && !target.matches(focusableSelector)) target.setAttribute('tabindex', '-1');
    target.focus({ preventScroll: true });
  }

  function closeDialog(modal) {
    if (!modal) return;
    modal.classList.remove('show');
    modal.setAttribute('aria-hidden', 'true');
    if (lastOpener && document.contains(lastOpener)) lastOpener.focus();
  }

  function trapFocus(event, modal) {
    if (event.key !== 'Tab' || !isOpen(modal)) return;
    const focusable = [...modal.querySelectorAll(focusableSelector)].filter((el) => el.offsetParent !== null);
    if (!focusable.length) {
      event.preventDefault();
      modal.focus();
      return;
    }
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  function init() {
    setLabel('#playPauseBtn', 'Play or pause Northern Dial radio');
    setLabel('#visualizerBtn', 'Open audio visualizer');
    setLabel('#volumeSlider', 'Radio volume');
    setLabel('#visualizerClose', 'Close visualizer');

    labelControl('requestSearch', 'Search for a song or artist');
    labelControl('artistName', 'Artist or band name');
    labelControl('artistEmail', 'Email address');
    labelControl('trackLinks', 'Track links');
    labelControl('socialLinks', 'Social media or website links');
    labelControl('artistMessage', 'Tell us about your music');
    labelControl('involvedName', 'Your name');
    labelControl('involvedEmail', 'Your email');
    labelControl('involvedInterest', 'How you want to contribute');
    labelControl('involvedMessage', 'Tell us how you would like to contribute');

    const dialogs = [...document.querySelectorAll('.install-modal')];
    const visualizer = document.getElementById('visualizerOverlay');
    if (visualizer) dialogs.push(visualizer);
    dialogs.forEach((modal) => {
      prepareModal(modal);
      if (!isOpen(modal)) modal.setAttribute('aria-hidden', 'true');
      const observer = new MutationObserver(() => {
        const open = isOpen(modal);
        modal.setAttribute('aria-hidden', open ? 'false' : 'true');
        if (open) requestAnimationFrame(() => focusDialog(modal));
      });
      observer.observe(modal, { attributes: true, attributeFilter: ['class'] });
    });

    document.querySelectorAll('[onclick*="classList.add(\'show\')"]').forEach(makeKeyboardActivatable);

    document.addEventListener('click', (event) => {
      const opener = event.target.closest('[onclick*="classList.add(\'show\')"],#visualizerBtn');
      if (opener) lastOpener = opener;
    }, true);

    document.addEventListener('keydown', (event) => {
      const openModal = dialogs.find(isOpen);
      if (!openModal) return;
      if (event.key === 'Escape') {
        event.preventDefault();
        closeDialog(openModal);
        return;
      }
      trapFocus(event, openModal);
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
