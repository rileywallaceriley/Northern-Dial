from pathlib import Path
import json
import re

BLOG = Path('blog/index.html')
HOME = Path('index.html')
MARKER = '<!-- SEPT11_EDITORIAL_END -->'

blog_card = '''
      <article class="card"><a href="rochelle-jordan-disc-2-remix-series.html"><img src="../images/no-transit-01.png?v=no-transit-01" alt="Rochelle Jordan in a Toronto torn-paper collage" style="width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;display:block;background:#111;" /></a><div class="card-body"><p class="card-date">September 11, 2026 · News Hit</p><h2 class="card-title">Rochelle Jordan Expands <em>Through The Wall</em> With <em>Disc 2</em></h2><div class="card-accent"></div><p class="card-excerpt">The Toronto-raised artist opens her remix series to Chad Hugo, Terry Hunter, Shanti Celeste and Bianca Oblivion.</p><a href="rochelle-jordan-disc-2-remix-series.html" class="card-link">Read More</a></div></article>
'''

home_card = '''
      <a href="/blog/rochelle-jordan-disc-2-remix-series.html" style="text-decoration:none;display:block;border-radius:10px;overflow:hidden;background:white;border:1px solid #e0e0e0;transition:box-shadow .25s,transform .25s;"><img src="images/no-transit-01.png?v=no-transit-01" alt="Rochelle Jordan in a Toronto torn-paper collage" style="width:100%;height:200px;object-fit:cover;object-position:center;display:block;background:#111;"><div style="padding:20px 18px 18px;"><p style="font-family:'Roboto Condensed',sans-serif;font-size:.75rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#CC3333;margin-bottom:8px;">September 11, 2026 · News Hit</p><h3 style="font-family:'Oswald',sans-serif;font-size:1.3rem;color:#1a1a1a;margin-bottom:10px;line-height:1.2;">Rochelle Jordan Expands <em>Through The Wall</em> With <em>Disc 2</em></h3><p style="font-family:'Roboto Condensed',sans-serif;font-size:.92rem;color:#555;line-height:1.6;margin-bottom:14px;">The Toronto-raised artist opens her remix series to Chad Hugo, Terry Hunter, Shanti Celeste and Bianca Oblivion.</p><span style="font-family:'Oswald',sans-serif;font-size:.8rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#CC3333;">Read More →</span></div></a>
'''

blog = BLOG.read_text(encoding='utf-8')
if 'href="rochelle-jordan-disc-2-remix-series.html"' not in blog:
    if MARKER not in blog:
        raise SystemExit('Missing Sept 11 marker in blog index')
    blog = blog.replace(MARKER, MARKER + blog_card, 1)

# Keep CollectionPage ItemList consistent with visible archive if JSON-LD is present.
pattern = re.compile(r'(<script type="application/ld\+json">\s*)(\{.*?\})(\s*</script>)', re.S)
match = pattern.search(blog)
if match:
    data = json.loads(match.group(2))
    items = data.get('mainEntity', {}).get('itemListElement', [])
    url = 'https://www.northerndial.ca/blog/rochelle-jordan-disc-2-remix-series.html'
    if not any(item.get('url') == url for item in items):
        items.append({'@type': 'ListItem', 'position': len(items) + 1, 'url': url})
        data['mainEntity']['itemListElement'] = items
        blog = blog[:match.start(2)] + json.dumps(data, ensure_ascii=False, indent=2) + blog[match.end(2):]
BLOG.write_text(blog, encoding='utf-8')

home = HOME.read_text(encoding='utf-8')
if 'href="/blog/rochelle-jordan-disc-2-remix-series.html"' not in home:
    if MARKER not in home:
        raise SystemExit('Missing Sept 11 marker in homepage')
    home = home.replace(MARKER, MARKER + home_card, 1)
HOME.write_text(home, encoding='utf-8')

print('Rochelle Jordan cards restored below the current Sept 11 editorial package.')
