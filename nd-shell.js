(() => {
  const LOGO = 'https://i.imgur.com/XIAPd0N.png';
  const path = window.location.pathname;
  const isHomepage = path === '/' || path === '/index.html';
  const isFrench = path === '/fr' || path.startsWith('/fr/');

  const LATEST_STORY = {
    href: '/blog/rochelle-jordan-disc-2-remix-series.html',
    localHref: 'rochelle-jordan-disc-2-remix-series.html',
    image: '/images/rochelle-jordan-disc-2-2026.jpg',
    date: 'September 11, 2026',
    category: 'News Hit',
    title: 'Rochelle Jordan Expands Through The Wall With Disc 2',
    excerpt: 'Chad Hugo, Terry Hunter, Shanti Celeste and Bianca Oblivion reshape Rochelle Jordan’s 2025 album for the dancefloor.'
  };

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

  function addLatestStory() {
    if (isFrench) return;

    if (path === '/blog/' || path === '/blog/index.html') {
      const grid = document.querySelector('.card-grid');
      if (grid) {
        let cardLink = grid.querySelector(`a[href="${LATEST_STORY.localHref}"]`);
        let article = cardLink ? cardLink.closest('article.card') : null;

        if (!article) {
          article = document.createElement('article');
          article.className = 'card';
          article.setAttribute('data-nd-latest-story', 'true');
          article.innerHTML = `
            <a href="${LATEST_STORY.localHref}">
              <img src="${LATEST_STORY.image}" alt="${LATEST_STORY.title}" style="width:100%; aspect-ratio:16/9; object-fit:cover; display:block; background:#171717;" />
            </a>
            <div class="card-body">
              <p class="card-date">${LATEST_STORY.date} · ${LATEST_STORY.category}</p>
              <h2 class="card-title">${LATEST_STORY.title}</h2>
              <div class="card-accent"></div>
              <p class="card-excerpt">${LATEST_STORY.excerpt}</p>
              <a href="${LATEST_STORY.localHref}" class="card-link">Read More</a>
            </div>`;
        }

        if (grid.firstElementChild !== article) grid.prepend(article);
      }
    }

    if (isHomepage) {
      const stories = document.querySelector('#stories');
      if (!stories) return;

      const grid = [...stories.querySelectorAll('div')].find((el) => window.getComputedStyle(el).display === 'grid');
      if (!grid) return;

      let card = grid.querySelector(`a[href="${LATEST_STORY.href}"]`);

      if (!card) {
        card = document.createElement('a');
        card.href = LATEST_STORY.href;
        card.setAttribute('data-nd-latest-story', 'true');
        card.style.cssText = 'text-decoration:none;display:block;border-radius:10px;overflow:hidden;background:white;border:1px solid #e0e0e0;transition:box-shadow .25s,transform .25s;';
        card.innerHTML = `
          <img src="${LATEST_STORY.image}" alt="${LATEST_STORY.title}" style="width:100%;height:200px;object-fit:cover;display:block;background:#171717;" />
          <div style="padding:20px 18px 18px;">
            <p style="font-family:'Roboto Condensed',sans-serif;font-size:.76rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#C33;margin:0 0 8px;">${LATEST_STORY.date} · ${LATEST_STORY.category}</p>
            <h3 style="font-family:'Oswald',sans-serif;font-size:1.22rem;line-height:1.25;color:#1a1a1a;margin:0 0 10px;">${LATEST_STORY.title}</h3>
            <p style="font-family:'Roboto Condensed',sans-serif;font-size:.94rem;line-height:1.55;color:#444;margin:0;">${LATEST_STORY.excerpt}</p>
          </div>`;
        card.addEventListener('mouseenter', () => {
          card.style.boxShadow = '0 8px 30px rgba(195,51,51,.3)';
          card.style.transform = 'translateY(-3px)';
        });
        card.addEventListener('mouseleave', () => {
          card.style.boxShadow = 'none';
          card.style.transform = 'translateY(0)';
        });
      }

      if (grid.firstElementChild !== card) grid.prepend(card);
    }
  }

  function fixKaytranadaVideos() {
    if (path !== '/blog/if-you-like-kaytranada-canadian-artists.html') return;

    const body = document.querySelector('.article-body');
    if (!body) return;

    const replacements = {
      '2. BAMBII': {
        id: 'RGOJ8bEoY-0',
        title: 'BAMBII — One Touch'
      },
      '3. Rochelle Jordan': {
        id: 'JyqCj8D2Wzw',
        title: 'Rochelle Jordan — Lowkey',
        note: 'Watch next: “Lowkey”'
      },
      '4. Planet Giza': {
        id: 'Qd2LW7zYyPY',
        title: 'Planet Giza — Nights Like This',
        note: 'Watch next: “Nights Like This”'
      },
      '5. KALLITECHNIS': {
        id: '2oX4Vlvof58',
        title: 'KALLITECHNIS — Hold Me Down featuring Kofi',
        note: 'Watch next: “Hold Me Down” featuring Kofi'
      }
    };

    const headings = [...body.querySelectorAll('h2')];

    Object.entries(replacements).forEach(([label, data]) => {
      const heading = headings.find((h2) => h2.textContent.trim() === label);
      if (!heading) return;

      let node = heading.nextElementSibling;
      let startLine = null;
      let video = null;

      while (node && node.tagName !== 'H2') {
        if (node.matches('p.start')) startLine = node;
        if (node.matches('.video')) {
          video = node;
          break;
        }
        node = node.nextElementSibling;
      }

      const iframeMarkup = `<iframe src="https://www.youtube.com/embed/${data.id}" title="${data.title}" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>`;

      if (video) {
        video.innerHTML = iframeMarkup;
        if (data.note && startLine) {
          let note = startLine.nextElementSibling;
          if (!note || !note.classList.contains('video-note')) {
            note = document.createElement('p');
            note.className = 'video-note';
            note.style.cssText = 'margin:-4px 0 10px;color:#666;font-size:.95rem;';
            startLine.insertAdjacentElement('afterend', note);
          }
          note.innerHTML = `<strong>${data.note}</strong>`;
        }
      } else if (startLine) {
        if (data.note && !startLine.nextElementSibling?.classList.contains('video-note')) {
          const note = document.createElement('p');
          note.className = 'video-note';
          note.style.cssText = 'margin:-4px 0 10px;color:#666;font-size:.95rem;';
          note.innerHTML = `<strong>${data.note}</strong>`;
          startLine.insertAdjacentElement('afterend', note);
          video = document.createElement('div');
          video.className = 'video';
          video.innerHTML = iframeMarkup;
          note.insertAdjacentElement('afterend', video);
        } else {
          video = document.createElement('div');
          video.className = 'video';
          video.innerHTML = iframeMarkup;
          startLine.insertAdjacentElement('afterend', video);
        }
      }
    });
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

  function init() {
    addLatestStory();
    fixKaytranadaVideos();
    if (!isHomepage) buildShell();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
