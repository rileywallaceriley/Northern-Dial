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
            date: parseDate(card.querySelector('.card-date')?.textContent)
          }))
          .sort((a, b) => (b.date - a.date) || (a.index - b.index))
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

  function init() {
    addLatestStory();
    sortStoryCards();
    featureNewestBlogStory();
    limitHomepageStories();
    paginateBlogArchive();
    styleBlogArchiveActions();
    fixKaytranadaVideos();
    enhanceArtistFeatures();
    if (!isHomepage) buildShell();
    loadI18n();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();