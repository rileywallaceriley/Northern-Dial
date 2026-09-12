from pathlib import Path
import json

ROOT = Path('.')
REPORT = ROOT / 'data' / 'editorial-internal-links-20260912.json'

changes = []


def replace_once(path_str, old, new, guard=None):
    path = ROOT / path_str
    if not path.exists():
        return False
    text = path.read_text(encoding='utf-8', errors='ignore')
    if guard and guard in text:
        return False
    if old not in text:
        return False
    text = text.replace(old, new, 1)
    path.write_text(text, encoding='utf-8')
    changes.append(path_str)
    return True

# Put high-value artist profile links directly into editorial copy, not only footer boxes.
replace_once(
    'blog/on-repeat-vibi-angeldies.html',
    '<p>VIBI’s 2026 has been busy enough',
    '<p><a href="/artists/vibi.html">VIBI</a>’s 2026 has been busy enough',
    'href="/artists/vibi.html">VIBI</a>’s 2026'
)
replace_once(
    'blog/lolo-the-punisher.html',
    '<p>LØLØ did not have to invent the premise',
    '<p><a href="/artists/ll.html">LØLØ</a> did not have to invent the premise',
    'href="/artists/ll.html">LØLØ</a> did not'
)
replace_once(
    'blog/mattmac-smoke-signals.html',
    '<p>Mattmac has spent the last several years',
    '<p><a href="/artists/mattmac.html">Mattmac</a> has spent the last several years',
    'href="/artists/mattmac.html">Mattmac</a> has spent'
)
replace_once(
    'blog/hip-club-groove-dead-words.html',
    'a situation Hip Club Groove never really got to have',
    'a situation <a href="/artists/hip-club-groove.html">Hip Club Groove</a> never really got to have',
    'href="/artists/hip-club-groove.html">Hip Club Groove</a> never'
)
replace_once(
    'blog/rochelle-jordan-disc-2-remix-series.html',
    '<p class="dek">Rochelle Jordan is pushing',
    '<p class="dek"><a href="/artists/rochelle-jordan.html">Rochelle Jordan</a> is pushing',
    'href="/artists/rochelle-jordan.html">Rochelle Jordan</a> is pushing'
)

# Connect closely related stories inside the actual article flow.
replace_once(
    'blog/on-repeat-vibi-angeldies.html',
    '<p>That balance is becoming easier to hear as the catalogue gets deeper. VIBI is past the “one to watch” stage, and at this point, the question is what she does next.</p>',
    '<p>That balance is becoming easier to hear as the catalogue gets deeper. VIBI is past the “one to watch” stage, and at this point, the question is what she does next.</p><p>For another current Canadian pop songwriter turning personal detail into a bigger hook, read our feature on <a href="/blog/lolo-the-punisher.html">LØLØ and “the punisher”</a>.</p>',
    'LØLØ and “the punisher”</a>'
)
replace_once(
    'blog/lolo-the-punisher.html',
    '<p>That tension is one of LØLØ’s best tricks. She can write like someone reading the group chat out loud, then build the hook so a room full of people can shout it back at her.</p>',
    '<p>That tension is one of LØLØ’s best tricks. She can write like someone reading the group chat out loud, then build the hook so a room full of people can shout it back at her.</p><p>For another current Canadian pop writer having a strong 2026, head to <a href="/blog/on-repeat-vibi-angeldies.html">VIBI’s “angeldies”</a>.</p>',
    'VIBI’s “angeldies”</a>'
)
replace_once(
    'blog/rochelle-jordan-disc-2-remix-series.html',
    '<p>Jordan has spent more than a decade moving between R&amp;B and club music, but this remix run makes that relationship explicit. <em>Disc 2</em> feels less like an appendix to the album than a second life for it.</p>',
    '<p>Jordan has spent more than a decade moving between R&amp;B and club music, but this remix run makes that relationship explicit. <em>Disc 2</em> feels less like an appendix to the album than a second life for it. That dance-floor side also makes her a natural stop in our <a href="/blog/if-you-like-kaytranada-canadian-artists.html">If You Like Kaytranada</a> listening path.</p>',
    'natural stop in our <a href="/blog/if-you-like-kaytranada-canadian-artists.html"'
)
replace_once(
    'blog/if-you-like-kaytranada-canadian-artists.html',
    '<p>Start with the original “All Along,” then move into <em>Play With the Changes</em> and the Kaytranada collaborations.</p>',
    '<p>Start with the original “All Along,” then move into <em>Play With the Changes</em> and the Kaytranada collaborations. For her newest club-facing chapter, read our <a href="/blog/rochelle-jordan-disc-2-remix-series.html">Rochelle Jordan <em>Disc 2</em> feature</a>.</p>',
    'Rochelle Jordan <em>Disc 2</em> feature</a>'
)
replace_once(
    'blog/if-you-like-drake-canadian-artists.html',
    '<p>This isn\'t a list of Drake soundalikes. Start with the part of his catalogue you return to most, then follow that thread somewhere else in Canadian music.</p>',
    '<p>This isn\'t a list of Drake soundalikes. Start with the part of his catalogue you return to most, then follow that thread somewhere else in Canadian music. If the R&amp;B and dance-floor side is more your lane, our <a href="/blog/if-you-like-kaytranada-canadian-artists.html">If You Like Kaytranada</a> guide opens another route.</p>',
    'our <a href="/blog/if-you-like-kaytranada-canadian-artists.html">If You Like Kaytranada</a> guide'
)

# Make the roundup's standalone-feature connections contextual as well as boxed.
replace_once(
    'blog/new-canadian-releases-september-11-2026.html',
    '<section class="entry"><h2>Mattmac — <em>Smoke Signals</em></h2><p>Mattmac\'s third album',
    '<section class="entry"><h2>Mattmac — <em>Smoke Signals</em></h2><p><a href="/blog/mattmac-smoke-signals.html">Mattmac\'s third album</a>',
    'href="/blog/mattmac-smoke-signals.html">Mattmac\'s third album</a>'
)
replace_once(
    'blog/new-canadian-releases-september-11-2026.html',
    '<section class="entry"><h2>Hip Club Groove — “Dead Words”</h2><p>This one needs an asterisk:',
    '<section class="entry"><h2>Hip Club Groove — “Dead Words”</h2><p><a href="/blog/hip-club-groove-dead-words.html">This one needs an asterisk:</a>',
    'href="/blog/hip-club-groove-dead-words.html">This one needs an asterisk:</a>'
)

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    'files_changed': sorted(set(changes)),
    'change_count': len(changes),
    'purpose': 'Contextual in-copy links between artist profiles and closely related Northern Dial stories.'
}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(REPORT.read_text(encoding='utf-8'))
