#!/usr/bin/env python3
"""Build the French directory from the English catalogue and published French bios.

No live API or third-party packages are needed. Catalogue names, track titles and
albums stay unchanged; editorial/UI copy and available profiles are French.
"""
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote
import json
import re
import unicodedata

from build_artist_pages import slugify

BASE = 'https://www.northerndial.ca'
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


class Element:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def text(self):
        return ''.join(child.text() if isinstance(child, Element) else child for child in self.children)

    def find(self, tag=None, cls=None):
        for child in self.children:
            if isinstance(child, Element):
                if (tag is None or child.tag == tag) and (cls is None or cls in child.attrs.get('class', '').split()):
                    yield child
                yield from child.find(tag, cls)


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.root = Element()
        self.stack = [self.root]
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        node = Element(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def plain(node, tag=None, cls=None):
    match = next(node.find(tag, cls), None)
    return ' '.join(match.text().split()) if match else ''


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c))


def catalogue(text):
    entries = {}
    for node in Document(text).root.find('details'):
        summary = next(node.find('summary'), None)
        if summary is None:
            continue
        meta = plain(summary, cls='artist-meta')
        name = ' '.join(summary.text().split())
        if meta and name.endswith(meta):
            name = name[:-len(meta)].strip()
        profile = next(summary.find('a', 'artist-page-link'), None)
        slug = Path(profile.attrs['href']).stem if profile else slugify(name)
        # Some catalogue credits share a profile. Keep one entry and merge songs.
        key = slug if profile else 'credit-' + normalized(name)
        entry = entries.setdefault(key, {'name': name, 'slug': slug, 'tracks': [], 'count': 0})
        count = re.search(r'([\d,]+)\s+track', meta)
        entry['count'] += int(count.group(1).replace(',', '')) if count else 0
        for track in node.find(cls='track'):
            title = plain(track, cls='track-title')
            album = plain(track, cls='track-album')
            if title and (title, album) not in entry['tracks']:
                entry['tracks'].append((title, album))
    return list(entries.values())


def main():
    source = Path('artists.html').read_text(encoding='utf-8')
    entries = catalogue(source)
    french = {}
    for path in sorted(Path('fr/artists').glob('*.html')):
        doc = Document(path.read_text(encoding='utf-8')).root
        name, bio = plain(doc, 'h1'), plain(doc, cls='bio')
        if not name or not bio:
            raise SystemExit(f'Missing French artist name or biography: {path}')
        official = next(doc.find(cls='official-links'), None)
        links = [(a.text().strip(), a.attrs.get('href', '')) for a in official.find('a')] if official else []
        french[path.stem] = {'name': name, 'bio': bio, 'location': plain(doc, cls='location'), 'links': links}
    existing = {entry['slug'] for entry in entries}
    for slug, profile in french.items():
        if slug not in existing:
            entries.append({'name': profile['name'], 'slug': slug, 'tracks': [], 'count': 0})
    entries.sort(key=lambda entry: (normalized(entry['name']), entry['slug']))
    letters, blocks, ids = {}, [], set()
    for entry in entries:
        name, slug = entry['name'], entry['slug']
        anchor = 'artist-' + slug
        if anchor in ids:
            anchor += '-catalogue'
        if anchor in ids:
            raise SystemExit(f'Duplicate directory ID: {anchor}')
        ids.add(anchor)
        first = normalized(name).lstrip()[0].upper()
        letter = first if 'A' <= first <= 'Z' else '#'
        letters.setdefault(letter, anchor)
        profile = french.get(slug)
        en_path = Path('artists') / (slug + '.html')
        profile_url = f'/fr/artists/{slug}.html' if profile else (f'/artists/{slug}.html' if en_path.exists() else '')
        label = 'Voir le profil complet' if profile else 'Voir le profil en anglais'
        name_html = escape(name)
        if profile_url:
            name_html = f'<a class="artist-page-link" href="{escape(profile_url)}" onclick="event.stopPropagation()">{name_html}</a>'
        count = entry['count']
        count_label = f'{count} titre' + ('s' if count != 1 else '') if count else 'Profil d’artiste'
        bio_html = ''
        if profile:
            bio_html = f'<div class="artist-profile"><p class="profile-bio">{escape(profile["bio"])}</p><p class="profile-location">{escape(profile["location"])}</p></div>'
            official_links = ' · '.join(f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(text)}</a>' for text, url in profile['links'] if url)
            if official_links:
                bio_html = bio_html.replace('</div>', f'<p class="profile-links">{official_links}</p></div>')
        actions = f'<a class="profile-page-button" href="{profile_url}">{label}</a>' if profile_url else ''
        request = '/?request=' + quote(name) + '&amp;lang=fr'
        rows = []
        for title, album in entry['tracks'][:3]:
            rows.append(f'<div class="track" data-search="{escape(normalized(name + " " + title + " " + album), quote=True)}"><div><div class="track-title">{escape(title)}</div><div class="track-album">{escape(album)}</div></div><a class="request-link" href="{request}">Demander cet artiste</a></div>')
        more = max(0, count - len(rows))
        note = f'<p class="track-overflow-note">+{more} autres titres en rotation</p>' if more else ''
        blocks.append(f'<details id="{escape(anchor)}" data-search="{escape(normalized(name), quote=True)}"><summary>{name_html} <span class="artist-meta">({count_label})</span></summary>{bio_html}<div class="profile-actions">{actions}</div>{"".join(rows)}{note}<p><a class="request-link" href="{request}">Demander {escape(name)}</a></p></details>')
    nav = ''.join(f'<a href="#{anchor}">{letter}</a>' for letter, anchor in sorted(letters.items()))
    options = ''.join(f'<option value="{anchor}">{letter}</option>' for letter, anchor in sorted(letters.items()))
    # Share the English directory's actual styles, including its curation and bio UI.
    styles = '\n'.join(line.rstrip() for style in re.findall(r'<style>(.*?)</style>', source, re.S) for line in style.splitlines())
    schema = json.dumps({'@context': 'https://schema.org', '@type': 'CollectionPage', 'url': BASE + '/fr/artists.html', 'name': 'Artistes et chansons canadiennes | Northern Dial', 'inLanguage': 'fr-CA'}, ensure_ascii=False)
    page = '''<!doctype html>
<html lang="fr-CA"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#CC3333">
<title>Artistes et chansons canadiennes | Northern Dial</title>
<meta name="description" content="Découvrez les artistes canadiens de Northern Dial : biographies en français, répertoire alphabétique et chansons disponibles sur demande.">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="https://www.northerndial.ca/fr/artists.html">
<meta property="og:type" content="website"><meta property="og:site_name" content="Northern Dial">
<meta property="og:title" content="Artistes et chansons canadiennes | Northern Dial">
<meta property="og:description" content="Explorez les artistes, leurs biographies en français et les chansons de Northern Dial.">
<meta property="og:url" content="https://www.northerndial.ca/fr/artists.html">
<meta property="og:image" content="https://i.imgur.com/XIAPd0N.png">
<meta name="twitter:card" content="summary">
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/nd-shell.css?v=20260927e"><link rel="stylesheet" href="/nd-banner.css?v=20260914a">
<script type="application/ld+json">SCHEMA</script>
<style>STYLES
.letter-nav{position:static;gap:10px}.letter-nav a{padding:8px;color:#8b2323;font-weight:700}.letter-nav select{min-height:44px}
#artistList details{scroll-margin-top:90px}#artistList details[hidden],.track[hidden]{display:none}
.profile-actions:empty{display:none}.request-link{white-space:normal}
a:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid #c33;outline-offset:3px}
</style></head><body id="top">
<header><a href="/fr/" aria-label="Accueil Northern Dial"><img src="https://i.imgur.com/XIAPd0N.png" alt="Northern Dial"></a></header>
<nav class="page-nav" aria-label="Navigation principale"><a href="/fr/">Accueil</a><a href="/fr/library.html">Chansons</a><a href="/fr/artists.html" class="active" aria-current="page">Artistes</a><a href="/fr/discover.html">Découvrir</a><a href="/fr/blog/">Blogue</a><a class="language-switch" href="/artists.html" lang="en">English</a></nav>
<main>
<h1 id="page-title">Artistes et chansons canadiennes du répertoire Northern Dial</h1>
<p class="intro">Explorez les artistes et les chansons du catalogue canadien et indépendant de Northern Dial. Ouvrez une fiche pour découvrir l’artiste, lire sa biographie en français et consulter les titres disponibles sur demande.</p>
<div class="controls"><input id="artistSearch" type="search" placeholder="Rechercher un artiste ou une chanson…" aria-label="Rechercher un artiste ou une chanson"></div>
<div id="status" role="status" aria-live="polite">Parcourez le catalogue ci-dessous.</div>
<section class="curation-panel" aria-labelledby="curation-title">
<div class="curation-kicker">À propos du catalogue</div><h2 id="curation-title">Comment nous construisons le répertoire Northern Dial</h2>
<p>Ce répertoire est une ressource éditoriale vivante. Northern Dial vérifie l’identité des artistes, retire les artistes non canadiens et les crédits qui ne désignent pas des artistes, enrichit les profils à partir de sources fiables et garde les cas ambigus ouverts tant que les preuves ne permettent pas de les trancher.</p>
<div class="curation-points"><div class="curation-point"><strong>Examiner</strong><span>Les crédits d’artistes sont vérifiés plutôt que repris automatiquement.</span></div><div class="curation-point"><strong>Vérifier</strong><span>Les profils s’appuient sur des sources fiables, des liens officiels et des renseignements géographiques.</span></div><div class="curation-point"><strong>Retirer</strong><span>Les artistes clairement non canadiens et les crédits qui ne correspondent pas à des artistes sont exclus.</span></div><div class="curation-point"><strong>Clarifier avec soin</strong><span>Les cas incertains restent ouverts plutôt que de devenir des affirmations sans preuve.</span></div></div>
<div class="curation-links"><a href="/fr/a-propos.html">À propos du projet</a><a href="/fr/archives.html">Archives et atlas</a><a href="/listening-paths.html" lang="en">Parcours d’écoute en anglais</a></div>
</section>
<p>Les biographies françaises disponibles figurent dans les fiches. Les profils non encore traduits sont indiqués comme étant en anglais.</p>
<nav class="letter-nav" aria-label="Navigation alphabétique"><label for="letterJump">Aller à une lettre</label><select id="letterJump"><option value="">Choisir une lettre</option>OPTIONS</select><div>LETTERS</div><a class="top-link" href="#top">Haut de page ↑</a></nav>
<section id="artistList" aria-labelledby="page-title">ENTRIES</section>
</main>
<footer><a href="/fr/">Northern Dial</a> · Radio canadienne indépendante · <a href="/artists.html" lang="en">Répertoire en anglais</a></footer>
<script>
(() => {
const list=document.getElementById('artistList'), filter=document.getElementById('artistSearch'), status=document.getElementById('status');
const normalize=value=>value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('fr-CA');
function updateFilter(){
 const query=normalize(filter.value.trim());let artists=0,songs=0;
 list.querySelectorAll('details').forEach(artist=>{
  const artistMatch=!query||artist.dataset.search.includes(query);let matches=0;
  artist.querySelectorAll('.track').forEach(track=>{const match=artistMatch||track.dataset.search.includes(query);track.hidden=!match;if(match)matches++;});
  artist.hidden=Boolean(query)&&!artistMatch&&matches===0;
  if(!artist.hidden){artists++;songs+=matches;}
 });
 status.textContent=artists.toLocaleString('fr-CA')+(artists===1?' artiste':' artistes')+' · '+songs.toLocaleString('fr-CA')+(songs===1?' titre affiché':' titres affichés');
}
filter.addEventListener('input',updateFilter);
function jump(id){const target=document.getElementById(id);if(!target)return;filter.value='';updateFilter();target.open=true;target.scrollIntoView({behavior:'smooth',block:'start'});history.replaceState(null,'','#'+id);}
document.getElementById('letterJump').addEventListener('change',event=>{jump(event.target.value);event.target.value='';});
document.querySelector('.letter-nav').addEventListener('click',event=>{const a=event.target.closest('a[href^="#artist-"]');if(a){event.preventDefault();jump(a.getAttribute('href').slice(1));}});
const openHash=()=>{const target=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(target?.tagName==='DETAILS'){filter.value='';updateFilter();target.open=true;}};
window.addEventListener('hashchange',openHash);updateFilter();openHash();
})();
</script><script src="/nd-shell.js?v=20260927e" defer></script></body></html>
'''
    for marker, value in [('SCHEMA', schema), ('STYLES', styles), ('OPTIONS', options), ('LETTERS', nav), ('ENTRIES', '\n'.join(blocks))]:
        page = page.replace(marker, value)
    Path('fr/artists.html').write_text(page, encoding='utf-8')
    print(f'Built {len(entries)} French directory entries with {len(french)} published French biographies.')


if __name__ == '__main__':
    main()
