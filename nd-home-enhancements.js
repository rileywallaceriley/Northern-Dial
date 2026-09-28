(() => {
  const path = window.location.pathname;
  const isHomepage = path === '/' || path === '/index.html';
  if (!isHomepage) return;

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

  sortStoryCards();
  limitHomepageStories();
  updateHomepageListeningPromos();
})();
