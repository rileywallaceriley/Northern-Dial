from pathlib import Path
from html import unescape
import json
import re

ROOT = Path('.')
BLOG_DIR = ROOT / 'blog'
ARTIST_DIR = ROOT / 'artists'
REPORT = ROOT / 'data' / 'internal-link-report-20260912.json'

BLOG_START = '<!-- ND_INTERNAL_LINKS_START -->'
BLOG_END = '<!-- ND_INTERNAL_LINKS_END -->'
ARTIST_START = '<!-- ND_ARTIST_BLOG_LINKS_START -->'
ARTIST_END = '<!-- ND_ARTIST_BLOG_LINKS_END -->'

TAG_RE = re.compile(r'<[^>]+>')
SPACE_RE = re.compile(r'\s+')


def clean_text(value: str) -> str:
    value = TAG_RE.sub(' ', value or '')
    return SPACE_RE.sub(' ', unescape(value)).strip()


def extract_first(pattern: str, text: str, flags=re.I | re.S) -> str:
    m = re.search(pattern, text, flags)
    return clean_text(m.group(1)) if m else ''


def remove_block(text: str, start: str, end: str) -> str:
    return re.sub(re.escape(start) + r'.*?' + re.escape(end), '', text, flags=re.S)


def norm(value: str) -> str:
    value = unescape(value).casefold()
    value = value.replace('ø', 'o')
    value = re.sub(r'[^a-z0-9]+', ' ', value)
    return SPACE_RE.sub(' ', value).strip()


def blog_category(text: str) -> str:
    kicker = extract_first(r'<p[^>]*class=["\'][^"\']*kicker[^"\']*["\'][^>]*>(.*?)</p>', text)
    if '·' in kicker:
        return kicker.split('·', 1)[0].strip()
    # Older features often use metadata/card labels rather than a kicker.
    title = extract_first(r'<title>(.*?)</title>', text)
    if 'If You Like' in title:
        return 'If You Like...'
    return ''


def choose_candidates(blog_text: str, artist_names: dict[str, str]) -> list[str]:
    candidates = set()

    # Existing profile links are authoritative.
    for slug in re.findall(r'href=["\'](?:\.\./|/)?artists/([^"\']+)\.html["\']', blog_text, re.I):
        if slug in artist_names:
            candidates.add(slug)

    # H1/H2 headings are strong signals and avoid matching thousands of names in generic prose.
    headings = [clean_text(x) for x in re.findall(r'<h[12][^>]*>(.*?)</h[12]>', blog_text, re.I | re.S)]
    heading_norms = [norm(h) for h in headings]
    for slug, name in artist_names.items():
        n = norm(name)
        if not n:
            continue
        # Require exact heading, heading prefix like "1. Name", or artist name in the main headline.
        for h in heading_norms:
            if h == n or h.endswith(' ' + n) or h.startswith(n + ' ') or (' ' + n + ' ') in (' ' + h + ' '):
                candidates.add(slug)
                break

    # Filename/title match catches single-artist features whose body has no profile link yet.
    title = extract_first(r'<h1[^>]*>(.*?)</h1>', blog_text)
    title_n = norm(title)
    for slug, name in artist_names.items():
        n = norm(name)
        if len(n) < 4:
            continue
        if n and re.search(r'(^| )' + re.escape(n) + r'( |$)', title_n):
            candidates.add(slug)

    return sorted(candidates)


def make_blog_block(profile_slugs, artist_names, related):
    parts = [BLOG_START]
    parts.append('<aside class="nd-internal-links" aria-label="Explore more on Northern Dial" style="margin:42px 0 0;padding:24px;border-top:3px solid #c33;background:#f7f7f7;border-radius:8px;">')
    parts.append('<p style="margin:0 0 12px;font-family:\'Oswald\',sans-serif;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#c33;">Explore more on Northern Dial</p>')
    if profile_slugs:
        links = []
        for slug in profile_slugs[:6]:
            name = artist_names[slug]
            links.append(f'<a href="/artists/{slug}.html">{name} artist profile</a>')
        parts.append('<p style="margin:0 0 10px;"><strong>Artist profiles:</strong> ' + ' · '.join(links) + '</p>')
    if related:
        links = [f'<a href="/blog/{item["file"]}">{item["title"]}</a>' for item in related[:3]]
        parts.append('<p style="margin:0;"><strong>Related reading:</strong> ' + ' · '.join(links) + '</p>')
    parts.append('</aside>')
    parts.append(BLOG_END)
    return ''.join(parts)


def make_artist_block(items):
    links = ''.join(
        f'<li style="margin:0 0 10px;"><a href="../blog/{item["file"]}">{item["title"]}</a></li>'
        for item in items[:5]
    )
    return (
        ARTIST_START
        + '<section class="card" aria-label="Northern Dial stories">'
        + '<p class="eyebrow">Northern Dial stories</p><h2>Featured on Northern Dial</h2>'
        + f'<ul style="margin:0;padding-left:20px;">{links}</ul>'
        + '</section>'
        + ARTIST_END
    )


artist_files = sorted(p for p in ARTIST_DIR.glob('*.html') if p.name != 'index.html')
artist_names = {}
artist_paths = {}
for path in artist_files:
    text = path.read_text(encoding='utf-8', errors='ignore')
    name = extract_first(r'<h1[^>]*>(.*?)</h1>', text) or extract_first(r'<title>(.*?)\|', text)
    if not name:
        continue
    slug = path.stem
    artist_names[slug] = name
    artist_paths[slug] = path

blog_files = sorted(p for p in BLOG_DIR.glob('*.html') if p.name != 'index.html')
blogs = []
for path in blog_files:
    text = path.read_text(encoding='utf-8', errors='ignore')
    title = extract_first(r'<h1[^>]*>(.*?)</h1>', text) or extract_first(r'<title>(.*?)</title>', text)
    candidates = choose_candidates(text, artist_names)
    blogs.append({
        'path': path,
        'file': path.name,
        'title': title or path.stem.replace('-', ' ').title(),
        'category': blog_category(text),
        'artists': candidates,
        'text': text,
    })

# Build reverse map artist -> blog stories.
artist_to_blogs = {slug: [] for slug in artist_names}
for blog in blogs:
    for slug in blog['artists']:
        artist_to_blogs.setdefault(slug, []).append(blog)

# Update blogs with profile links and related reading based primarily on shared artists,
# secondarily on the same recurring editorial category.
blogs_changed = 0
related_links_added = 0
profile_links_added = 0
for blog in blogs:
    text = remove_block(blog['text'], BLOG_START, BLOG_END)
    scored = []
    current_artists = set(blog['artists'])
    for other in blogs:
        if other['file'] == blog['file']:
            continue
        shared = current_artists.intersection(other['artists'])
        score = len(shared) * 10
        if blog['category'] and other['category'] == blog['category']:
            score += 2
        if score:
            scored.append((score, other['file'], other))
    scored.sort(key=lambda row: (-row[0], row[1]))
    related = [row[2] for row in scored[:3]]

    if not blog['artists'] and not related:
        continue

    block = make_blog_block(blog['artists'], artist_names, related)
    if '</main>' in text:
        text = text.replace('</main>', block + '</main>', 1)
    elif '</article>' in text:
        text = text.replace('</article>', block + '</article>', 1)
    else:
        continue

    blog['path'].write_text(text, encoding='utf-8')
    blogs_changed += 1
    profile_links_added += min(len(blog['artists']), 6)
    related_links_added += min(len(related), 3)

# Update only artist profiles that actually have blog coverage.
artist_profiles_changed = 0
artist_story_links_added = 0
for slug, items in artist_to_blogs.items():
    if not items:
        continue
    path = artist_paths.get(slug)
    if not path:
        continue
    text = path.read_text(encoding='utf-8', errors='ignore')
    text = remove_block(text, ARTIST_START, ARTIST_END)
    items = sorted(items, key=lambda item: item['file'])
    block = make_artist_block(items)

    # Put the story card inside the existing content grid when possible.
    marker = '</div>\n      <a class="back-link"'
    if marker in text:
        text = text.replace(marker, block + '\n      </div>\n      <a class="back-link"', 1)
    else:
        marker = '<a class="back-link"'
        if marker in text:
            text = text.replace(marker, block + '\n      <a class="back-link"', 1)
        elif '</article>' in text:
            text = text.replace('</article>', block + '</article>', 1)
        else:
            continue

    path.write_text(text, encoding='utf-8')
    artist_profiles_changed += 1
    artist_story_links_added += min(len(items), 5)

REPORT.parent.mkdir(parents=True, exist_ok=True)
report = {
    'blogs_scanned': len(blogs),
    'artist_profiles_scanned': len(artist_names),
    'blogs_changed': blogs_changed,
    'artist_profiles_changed': artist_profiles_changed,
    'profile_links_added_to_blogs': profile_links_added,
    'related_blog_links_added': related_links_added,
    'blog_links_added_to_artist_profiles': artist_story_links_added,
    'artists_with_blog_coverage': sorted([
        {'slug': slug, 'name': artist_names[slug], 'stories': len(items)}
        for slug, items in artist_to_blogs.items() if items
    ], key=lambda x: (-x['stories'], x['name'].casefold())),
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
