from pathlib import Path

old = '@media(max-width:760px){.card.featured{display:flex;grid-column:auto}.card.featured>a img{height:auto!important;min-height:0}}'
new = '@media(max-width:760px){.card.featured{display:flex;grid-column:auto;grid-template-columns:none}.card.featured>a{min-height:0;height:auto;width:100%}.card.featured>a img{height:auto!important;min-height:0;width:100%!important;display:block}.card.featured .card-body{width:100%}}'

for path in [Path('blog/index.html'), Path('tools/refine_sep11_features.py')]:
    text = path.read_text()
    if old not in text:
        print(f'Pattern not found in {path}')
        continue
    path.write_text(text.replace(old, new))
    print(f'Fixed {path}')

shell = Path('nd-shell.js')
text = shell.read_text(encoding='utf-8')
replacements = {
    "href: '/blog/rochelle-jordan-disc-2-remix-series.html'": "href: '/blog/new-canadian-releases-september-11-2026.html'",
    "localHref: 'rochelle-jordan-disc-2-remix-series.html'": "localHref: 'new-canadian-releases-september-11-2026.html'",
    "image: '/images/rochelle-jordan-disc-2-2026.jpg'": "image: '/images/new-canadian-releases-sept-11-2026-collage-v2.jpg'",
    "category: 'News Hit'": "category: 'New Canadian Music'",
    "title: 'Rochelle Jordan Expands Through The Wall With Disc 2'": "title: '5 New Canadian Releases to Bump This Weekend'",
    "excerpt: 'Chad Hugo, Terry Hunter, Shanti Celeste and Bianca Oblivion reshape Rochelle Jordan’s 2025 album for the dancefloor.'": "excerpt: 'Mattmac, CG Tears, Jon McKiel, Starpainter and Hip Club Groove lead this weekend’s picks.'",
}
for old_text, new_text in replacements.items():
    if old_text not in text:
        print(f'Latest-story pattern not found: {old_text}')
    text = text.replace(old_text, new_text, 1)
shell.write_text(text, encoding='utf-8')
print('Updated nd-shell.js latest story source')
print('Featured mobile patch complete')
