/* Northern Dial author badges: existing stories default to the editorial team.
   Future signed stories can declare <meta name="nd-author" content="riley-wallace">. */
(() => {
  const path = window.location.pathname;
  if (!/^\/blog\/[^/]+\.html$/.test(path) || path === '/blog/index.html') return;
  function render() {
    if (document.getElementById('nd-author-card')) return;
    const host = document.querySelector('main .article-wrapper') || document.querySelector('main .wrap') || document.querySelector('main');
    if (!host || !host.querySelector('h1')) return;
    const specified = document.querySelector('meta[name="nd-author"]')?.getAttribute('content') ||
      document.body.getAttribute('data-nd-author');
    const isRiley = specified === 'riley-wallace';
    const author = isRiley ? {
      name: 'Riley Wallace',
      role: 'Music journalist & editor',
      image: '/images/riley-wallace-avatar.svg',
      url: '/authors/riley-wallace.html',
      bio: 'Veteran Canadian music journalist published in XXL, Exclaim!, HipHopDX and Okayplayer. Current FACTOR juror with more than 15 years covering Canadian music and hip-hop.',
      type: 'Person'
    } : {
      name: 'Northern Dial Staff',
      role: 'Editorial team',
      image: '/images/nd-staff-avatar.svg',
      url: '/authors/northern-dial-staff.html',
      bio: 'Canadian music discoveries, new releases and listening guides curated by the Northern Dial team.',
      type: 'Organization'
    };
    const style = document.createElement('style');
    style.id = 'nd-author-style';
    style.textContent = `
      .nd-author-card{display:flex;align-items:center;gap:14px;max-width:860px;margin:36px 0 8px;padding:15px 16px;border-top:2px solid #C7443E;border-bottom:1px solid #d8d3cb;background:#F6F1E7;color:#111214;font-family:'Roboto Condensed',Arial,sans-serif;text-align:left}
      .nd-author-card img{width:72px;height:72px;flex:0 0 72px;object-fit:cover;border-radius:7px}
      .nd-author-copy{min-width:0}
      .nd-author-card .nd-author-label{font:700 .65rem/1.3 'Oswald',Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:#66635F;margin:0 0 3px}
      .nd-author-card .nd-author-name{font:700 1.08rem/1.3 'Oswald',Arial,sans-serif;margin:0 0 4px}
      .nd-author-card .nd-author-name a{color:#111214;text-decoration:none;border-bottom:1px solid #C7443E}
      .nd-author-card .nd-author-bio{font-size:.93rem;line-height:1.4;color:#3d3c3b;margin:0}
      @media(max-width:480px){.nd-author-card{align-items:flex-start;padding:12px;gap:10px}.nd-author-card img{width:54px;height:54px;flex-basis:54px}.nd-author-card .nd-author-bio{font-size:.87rem}}
    `;
    document.head.appendChild(style);
    const card = document.createElement('section');
    card.id = 'nd-author-card';
    card.className = 'nd-author-card';
    card.setAttribute('aria-label','About the author');
    card.innerHTML = '<img src="' + author.image + '" width="72" height="72" alt="' + author.name + ' avatar" loading="lazy">' +
      '<div class="nd-author-copy"><p class="nd-author-label">About the author · ' + author.role + '</p>' +
      '<p class="nd-author-name"><a href="' + author.url + '" rel="author">' + author.name + '</a></p>' +
      '<p class="nd-author-bio">' + author.bio + '</p></div>';
    host.appendChild(card);
    if (!document.querySelector('meta[name="author"]')) {
      const meta = document.createElement('meta'); meta.name='author';meta.content=author.name;document.head.appendChild(meta);
    }
    if (!document.querySelector('link[rel="author"]')) {
      const link = document.createElement('link');link.rel='author';link.href=author.url;document.head.appendChild(link);
    }
    for (const tag of document.querySelectorAll('script[type="application/ld+json"]')) {
      try {
        const data = JSON.parse(tag.textContent);
        const entries = Array.isArray(data) ? data : [data];
        let changed = false;
        for (const item of entries) {
          if (!item || !['Article','BlogPosting','NewsArticle'].includes(item['@type'])) continue;
          item.author = {'@type':author.type,'name':author.name,'url':'https://www.northerndial.ca'+author.url};
          changed = true;
        }
        if (changed) tag.textContent = JSON.stringify(data);
      } catch (_) { /* Leave unrelated structured data intact. */ }
    }
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',render,{once:true});else render();
})();