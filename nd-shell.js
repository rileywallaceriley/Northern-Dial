(() => {
  const LOGO = 'https://i.imgur.com/XIAPd0N.png';
  const path = window.location.pathname;
  const isHomepage = path === '/' || path === '/index.html';
  const isFrench = path === '/fr' || path.startsWith('/fr/');


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

  function styleBlogArchiveActions() {
    if (path !== '/blog/' && path !== '/blog/index.html') return;

    const header = document.querySelector('.page-header');
    if (!header) return;

    const actionLine = [...header.querySelectorAll('p.subheading')].find((p) => p.querySelectorAll('a').length >= 2);
    if (!actionLine) return;

    actionLine.classList.add('nd-blog-actions');
    actionLine.style.cssText = 'display:flex;justify-content:center;gap:12px;flex-wrap:wrap;margin-top:18px;letter-spacing:0;';

    const actionLinks = [...actionLine.querySelectorAll('a')];
    actionLinks.forEach((link, index) => {
      link.style.cssText = `display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:12px 18px;border-radius:7px;font-family:'Oswald',sans-serif;font-size:.9rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;text-decoration:none;transition:transform .2s,background .2s,color .2s,border-color .2s;${index === 0 ? 'background:#CC3333;color:#fff;border:2px solid #CC3333;' : 'background:#fff;color:#1a1a1a;border:2px solid #1a1a1a;'}`;

      link.addEventListener('mouseenter', () => {
        link.style.transform = 'translateY(-2px)';
        if (index === 0) link.style.background = '#8B2323';
        else {
          link.style.background = '#1a1a1a';
          link.style.color = '#fff';
        }
      });

      link.addEventListener('mouseleave', () => {
        link.style.transform = 'translateY(0)';
        if (index === 0) link.style.background = '#CC3333';
        else {
          link.style.background = '#fff';
          link.style.color = '#1a1a1a';
        }
      });
    });

    actionLine.childNodes.forEach((node) => {
      if (node.nodeType === Node.TEXT_NODE && node.textContent.includes('·')) node.textContent = ' ';
    });

    const mobile = window.matchMedia('(max-width: 640px)');
    const applyMobile = () => {
      actionLinks.forEach((link) => {
        link.style.width = mobile.matches ? '100%' : 'auto';
        link.style.maxWidth = mobile.matches ? '320px' : 'none';
      });
    };
    applyMobile();
    mobile.addEventListener?.('change', applyMobile);
  }

  function sortStoryCards() {
    const datePattern = /(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}/i;
    const parseDate = (text) => {
      const match = String(text || '').match(datePattern);
      if (!match) return 0;
      const time = Date.parse(match[0]);
      return Number.isNaN(time) ? 0 : time;
    };

    if (path === '/blog/' || path === '/blog/index.html') {
      const grid = document.querySelector('.card-grid');
      if (grid) {
        const cards = [...grid.children].filter((el) => el.matches('article.card'));
        cards
          .map((card, index) => ({
            card,
            index,
            featured: card.classList.contains('featured'),
            date: parseDate(card.querySelector('.card-date')?.textContent)
          }))
          .sort((a, b) => (Number(b.featured) - Number(a.featured)) || (b.date - a.date) || (a.index - b.index))
          .forEach(({ card }) => grid.appendChild(card));
      }
    }

    if (isHomepage) {
      const stories = document.querySelector('#stories');
      if (!stories) return;
      const grid = [...stories.querySelectorAll('div')].find((el) => window.getComputedStyle(el).display === 'grid');
      if (!grid) return;

      const cards = [...grid.children].filter((el) => el.tagName === 'A' && /\/blog\//.test(el.getAttribute('href') || ''));
      cards
        .map((card, index) => ({
          card,
          index,
          date: parseDate([...card.querySelectorAll('p')].map((p) => p.textContent).join(' '))
        }))
        .sort((a, b) => (b.date - a.date) || (a.index - b.index))
        .forEach(({ card }) => grid.appendChild(card));
    }
  }

  function featureNewestBlogStory() {
    if (path !== '/blog/' && path !== '/blog/index.html') return;
    const grid = document.querySelector('.card-grid');
    const featured = grid?.querySelector('article.card');
    if (!grid || !featured) return;

    featured.classList.add('nd-featured-story');
    const image = featured.querySelector('img');
    const title = featured.querySelector('.card-title');
    const excerpt = featured.querySelector('.card-excerpt');

    const applyLayout = () => {
      const desktop = window.innerWidth > 900;
      grid.style.gridAutoFlow = desktop ? 'dense' : '';
      featured.style.gridColumn = desktop ? 'span 2' : '';
      featured.style.gridRow = desktop ? 'span 2' : '';

      if (image) {
        image.style.width = '100%';
        image.style.height = desktop ? '360px' : '';
        image.style.aspectRatio = desktop ? 'auto' : '16 / 9';
        image.style.objectFit = 'cover';
        image.style.objectPosition = 'center center';
      }
      if (title) title.style.fontSize = desktop ? '1.9rem' : '';
      if (excerpt) excerpt.style.fontSize = desktop ? '1.05rem' : '';
    };

    applyLayout();
    window.addEventListener('resize', applyLayout, { passive: true });
  }

  function limitHomepageStories() {
    if (!isHomepage) return;
    const stories = document.querySelector('#stories');
    if (!stories) return;
    const grid = [...stories.querySelectorAll('div')].find((el) => window.getComputedStyle(el).display === 'grid');
    if (!grid) return;

    const applyLimit = () => {
      const width = window.innerWidth;
      const limit = width <= 640 ? 4 : width <= 900 ? 6 : 8;
      const cards = [...grid.children].filter((el) => el.tagName === 'A' && /\/blog\//.test(el.getAttribute('href') || ''));
      cards.forEach((card, index) => {
        card.style.display = index < limit ? 'block' : 'none';
      });
    };

    applyLimit();
    window.addEventListener('resize', applyLimit, { passive: true });
  }

  function paginateBlogArchive() {
    if (path !== '/blog/' && path !== '/blog/index.html') return;
    const grid = document.querySelector('.card-grid');
    if (!grid) return;

    const cards = [...grid.children].filter((el) => el.matches('article.card'));
    const pageSize = 9;
    const totalPages = Math.max(1, Math.ceil(cards.length / pageSize));
    if (totalPages <= 1) return;

    const controls = document.createElement('nav');
    controls.className = 'nd-blog-pagination';
    controls.setAttribute('aria-label', 'Blog pagination');
    controls.style.cssText = 'display:flex;justify-content:center;align-items:center;gap:8px;flex-wrap:wrap;margin:42px 0 0;background:transparent;border:0;position:static;';
    grid.insertAdjacentElement('afterend', controls);

    const makeButton = (label, page, ariaLabel = '') => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = label;
      button.dataset.page = String(page);
      if (ariaLabel) button.setAttribute('aria-label', ariaLabel);
      button.style.cssText = "min-width:42px;height:42px;padding:0 13px;border:2px solid #1a1a1a;border-radius:6px;background:#fff;color:#1a1a1a;font-family:'Oswald',sans-serif;font-size:.88rem;font-weight:700;cursor:pointer;";
      return button;
    };

    const render = (requestedPage, updateHistory = true) => {
      const currentPage = Math.min(Math.max(Number(requestedPage) || 1, 1), totalPages);
      const start = (currentPage - 1) * pageSize;
      const end = start + pageSize;

      cards.forEach((card, index) => {
        card.style.display = index >= start && index < end ? 'flex' : 'none';
      });

      controls.innerHTML = '';
      const prev = makeButton('←', currentPage - 1, 'Previous page');
      prev.disabled = currentPage === 1;
      prev.style.opacity = prev.disabled ? '.35' : '1';
      controls.appendChild(prev);

      for (let page = 1; page <= totalPages; page += 1) {
        const button = makeButton(String(page), page, `Page ${page}`);
        if (page === currentPage) {
          button.setAttribute('aria-current', 'page');
          button.style.background = '#CC3333';
          button.style.borderColor = '#CC3333';
          button.style.color = '#fff';
        }
        controls.appendChild(button);
      }

      const next = makeButton('→', currentPage + 1, 'Next page');
      next.disabled = currentPage === totalPages;
      next.style.opacity = next.disabled ? '.35' : '1';
      controls.appendChild(next);

      controls.querySelectorAll('button:not(:disabled)').forEach((button) => {
        button.addEventListener('click', () => {
          render(Number(button.dataset.page));
          grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
      });

      if (updateHistory) {
        const url = new URL(window.location.href);
        if (currentPage === 1) url.searchParams.delete('page');
        else url.searchParams.set('page', String(currentPage));
        history.replaceState({ page: currentPage }, '', `${url.pathname}${url.search}${url.hash}`);
      }
    };

    const initialPage = Number(new URLSearchParams(window.location.search).get('page')) || 1;
    render(initialPage, false);
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

  function enhanceArtistFeatures() {
    const features = {
      '/blog/enola-bedard.html': {
        slug: 'enola-bedard',
        name: 'Enola Bédard',
        video: { id: 'd5valSPWtaU', title: 'Enola Bédard — Unavez official music video' }
      },
      '/blog/ghostboyrj.html': {
        slug: 'ghostboyrj',
        name: 'Ghostboyrj',
        video: { id: 'IXHMbu_G3so', title: 'Ghostboyrj — Cartoons & Cereal Intro (Official Video)' }
      },
      '/blog/haley-smalls.html': {
        slug: 'haley-smalls',
        name: 'Haley Smalls',
        video: { id: 'OJlFbow63fY', title: 'Haley Smalls — Matches' }
      },
      '/blog/koko-love.html': {
        slug: 'koko-love',
        name: 'Koko Love',
        video: { id: 'sjOAyC2JZ2Y', title: 'Koko Love — The Cost of Freedom (Live)' }
      },
      '/blog/lia-pappas-kemps.html': {
        slug: 'lia-pappas-kemps',
        name: 'Lia Pappas-Kemps',
        video: { id: '3DMSt6uTwVs', title: 'Lia Pappas-Kemps — Towers (Official Video)' }
      },
      '/blog/livingthing.html': {
        slug: 'livingthing',
        name: 'livingthing',
        video: { id: 'EBt8k2ZUYgg', title: 'livingthing — auburn (Official Lyric Video)' }
      },
      '/blog/lov.html': {
        slug: 'lov',
        name: 'LÖV',
        video: { id: 'AEKT4RYj9_w', title: 'LÖV — Mama (Official Music Video)' }
      },
      '/blog/puma-june.html': {
        slug: 'puma-june',
        name: 'Puma June',
        video: { id: 'Vk0KPDApOQk', title: 'Puma June — Bad Habits (Official Video)' }
      },
      '/blog/tauro.html': {
        slug: 'tauro',
        name: 'TAURO',
        video: { id: '01iUyzfWkqQ', title: 'TAURO — Great Minds (Official Video)' }
      }
    };

    const feature = features[path];
    if (!feature) return;

    const body = document.querySelector('.article-body');
    if (!body) return;

    const hasYouTube = [...body.querySelectorAll('iframe')].some((iframe) => {
      const src = iframe.getAttribute('src') || '';
      return src.includes('youtube.com/embed/');
    });

    if (!hasYouTube) {
      const firstParagraph = body.querySelector('p');
      if (firstParagraph) {
        const video = document.createElement('div');
        video.className = 'nd-feature-video';
        video.style.cssText = 'position:relative;padding-bottom:56.25%;height:0;overflow:hidden;margin:28px 0;border-radius:8px;background:#111;';

        const iframe = document.createElement('iframe');
        iframe.src = `https://www.youtube.com/embed/${feature.video.id}`;
        iframe.title = feature.video.title;
        iframe.loading = 'lazy';
        iframe.referrerPolicy = 'strict-origin-when-cross-origin';
        iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
        iframe.allowFullscreen = true;
        iframe.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;border:0;';

        video.appendChild(iframe);
        firstParagraph.insertAdjacentElement('afterend', video);
      }
    }

    const profileHref = `/artists/${feature.slug}.html`;
    const existingProfileLink = [...body.querySelectorAll('a')].some((link) => {
      try {
        return new URL(link.href, window.location.origin).pathname === profileHref;
      } catch (_) {
        return false;
      }
    });

    if (!existingProfileLink) {
      const profileLine = document.createElement('p');
      profileLine.className = 'artist-profile-link';
      profileLine.style.marginTop = '24px';

      const profileLink = document.createElement('a');
      profileLink.href = profileHref;
      profileLink.textContent = `Explore ${feature.name}’s Northern Dial artist profile →`;
      profileLink.style.cssText = 'color:#CC3333;text-decoration:underline;font-weight:700;';

      profileLine.appendChild(profileLink);
      body.appendChild(profileLine);
    }
  }

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

  function updateHomepageListeningPromos() {
    if (!isHomepage) return;

    document.querySelectorAll('a[href="new-canadian-artists.html"],a[href="/new-canadian-artists.html"]').forEach((link) => {
      if (link.closest('.site-nav,.nd-site-nav')) link.remove();
    });

    const player = document.querySelector('.custom-player');
    if (!player) return;
    const walker = document.createTreeWalker(player, NodeFilter.SHOW_TEXT);
    const textNodes = [];
    while (walker.nextNode()) textNodes.push(walker.currentNode);
    textNodes.forEach((node) => {
      node.textContent = node.textContent
        .replace('Alexa, play Northern Dial.', 'Alexa, play Northern Dial Radio.')
        .replace('Alexa, play Northern Dial', 'Alexa, play Northern Dial Radio');
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

  function loadI18n() {
    if (document.querySelector('script[data-nd-i18n]')) return;
    const script = document.createElement('script');
    script.src = '/nd-i18n.js?v=20260911a';
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
        '<button class="nd-mini-play" type="button" aria-label="Play Northern Dial"><span aria-hidden="true">▶</span></button>',
        '<div class="nd-mini-copy">',
          '<div class="nd-mini-status"><span class="nd-mini-live-dot" aria-hidden="true"></span><span class="nd-mini-status-text">Northern Dial · Ready</span></div>',
          '<div class="nd-mini-track">Northern Dial Radio</div>',
          '<div class="nd-mini-artist">All Killer, All CanCon</div>',
        '</div>',
        '<a class="nd-mini-profile" href="/artists.html" hidden>Meet the Artist</a>',
      '</div>'
    ].join('');

    let audio = document.getElementById('radioStream');
    if (!audio) {
      audio = document.createElement('audio');
      audio.id = 'ndPersistentAudio';
      audio.preload = 'none';
      audio.src = streamUrl;
      audio.volume = 0.7;
    }
    audio.classList.add('nd-persistent-audio');
    player.appendChild(audio);
    document.body.appendChild(player);

    const playButton = player.querySelector('.nd-mini-play');
    const playIcon = playButton.querySelector('span');
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

    function renderPlaybackState() {
      const playing = !audio.paused && !audio.ended;
      playButton.classList.toggle('playing', playing);
      playButton.setAttribute('aria-label', playing ? 'Pause Northern Dial' : 'Play Northern Dial');
      playIcon.textContent = playing ? '❚❚' : '▶';
      statusText.textContent = playing ? 'Northern Dial · Live' : 'Northern Dial · Paused';
      player.classList.toggle('is-playing', playing);
    }

    async function resumeIfWanted() {
      if (!userWantsPlayback || !audio.paused) return;
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
          audio.play();
        });
        navigator.mediaSession.setActionHandler('pause', () => {
          userWantsPlayback = false;
          audio.pause();
        });
      } catch (_) {}
    }

    async function refreshNowPlaying() {
      try {
        const response = await fetch(nowPlayingUrl, { cache: 'no-store' });
        if (!response.ok) return;
        const data = await response.json();
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
      try {
        if (audio.paused) {
          userWantsPlayback = true;
          await audio.play();
        } else {
          userWantsPlayback = false;
          audio.pause();
        }
      } catch (_) {
        statusText.textContent = 'Northern Dial · Tap again to play';
      }
      renderPlaybackState();
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

    renderPlaybackState();
    refreshNowPlaying();
    window.setInterval(refreshNowPlaying, 10000);

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

      if (childWindow.location.pathname === '/' || childWindow.location.pathname === '/index.html') {
        const style = childDocument.createElement('style');
        style.dataset.ndFramedHome = 'true';
        style.textContent = '.player-section{display:none!important}.home-top-grid{display:block!important}.home-top-grid .discovery-banner{margin:0 0 38px!important}';
        childDocument.head.appendChild(style);
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

  function init() {
    sortStoryCards();
    featureNewestBlogStory();
    limitHomepageStories();
    paginateBlogArchive();
    styleBlogArchiveActions();
    fixKaytranadaVideos();
    enhanceArtistFeatures();
    enhanceArtistsDirectory();
    updateHomepageListeningPromos();
    if (!isHomepage) buildShell();
    loadI18n();
    initPersistentPlayer();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();