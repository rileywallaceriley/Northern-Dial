from pathlib import Path

EMBED_CSS = ".video-embed{position:relative;width:100%;aspect-ratio:16/9;margin:18px 0 6px;background:#111;border-radius:6px;overflow:hidden}.video-embed iframe{position:absolute;inset:0;width:100%;height:100%;border:0}"


def embed(video_id, title):
    return f'<div class="video-embed"><iframe src="https://www.youtube-nocookie.com/embed/{video_id}" title="{title}" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>'


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 match, found {count}')
    return text.replace(old, new, 1)

# Drake discovery piece
path = Path('blog/if-you-like-drake-canadian-artists.html')
text = path.read_text(encoding='utf-8')
text = replace_once(
    text,
    '<div class="video-embed"><iframe src="https://www.youtube-nocookie.com/embed/sa7F1nj_TG4" title="AR Paisley — Walk of Shame" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>',
    embed('G6fJwksq7xU', 'AR Paisley & Manna Music — All Mine'),
    'AR Paisley embed',
)
text = replace_once(
    text,
    '<a class="watch" href="https://www.youtube.com/results?search_query=FRVRFRIDAY+BORN+WINNER+Boi-1da" target="_blank" rel="noopener">Hear “BORN WINNER” on YouTube</a>',
    embed('c_zb6SSQju0', 'AP Dhillon, FRVRFRIDAY, Joe Gez, Canada Soccer & Boi-1da — BORN WINNER'),
    'FRVRFRIDAY button',
)
text = replace_once(
    text,
    '<a class="watch" href="https://www.youtube.com/results?search_query=LOONY+RaGDOLL+2026" target="_blank" rel="noopener">Hear “RaGDOLL” on YouTube</a>',
    embed('Gelox4ZmgM8', 'LOONY — RaGDOLL'),
    'LOONY button',
)
text = replace_once(
    text,
    '<a class="watch" href="https://www.youtube.com/results?search_query=NorthSideBenji+TRYNA+WIN+Boi-1da" target="_blank" rel="noopener">Hear “TRYNA WIN” on YouTube</a>',
    '<p>For a recent visual from Benji, “Harder To Please” shows the quieter, more inward side of the same lane.</p>' + embed('GR__qMs7Tiw', 'NorthSideBenji — Harder To Please'),
    'NorthSideBenji button',
)
path.write_text(text, encoding='utf-8')

# New Canadian releases roundup
path = Path('blog/new-canadian-releases-september-11-2026.html')
text = path.read_text(encoding='utf-8')
text = replace_once(
    text,
    '<a class="watch" href="https://www.youtube.com/watch?v=HVFrIeLh-dQ" target="_blank" rel="noopener">Watch “I\'m Falling Up” on YouTube</a>',
    embed('HVFrIeLh-dQ', "CG Tears — I'm Falling Up"),
    'CG Tears button',
)
text = replace_once(
    text,
    '<a class="watch" href="https://www.youtube.com/results?search_query=Jon+McKiel+Gold+Horatio+For+Shadow" target="_blank" rel="noopener">Hear “For Shadow” on YouTube</a>',
    '<p>For a visual entry point into McKiel’s catalogue, here is “Deeper Shade.”</p>' + embed('n0lqF6HqL7E', 'Jon McKiel — Deeper Shade'),
    'Jon McKiel button',
)
text = replace_once(
    text,
    '<a class="watch" href="https://www.youtube.com/results?search_query=Starpainter+Cayenne+Flowerbed+Rabbits" target="_blank" rel="noopener">Hear Starpainter on YouTube</a>',
    '<p>“I Found a River” was the first preview of <em>Cayenne Flowerbed</em> and gives the album’s fuzzy alt-country side a proper visual.</p>' + embed('H4xQ2xjL3tA', 'Starpainter — I Found a River'),
    'Starpainter button',
)
text = replace_once(
    text,
    '<a class="watch" href="https://www.youtube.com/results?search_query=Hip+Club+Groove+Dead+Words" target="_blank" rel="noopener">Hear “Dead Words” on YouTube</a>',
    '<p>For a look back at the group before the three-decade gap, here is Hip Club Groove in their original era.</p>' + embed('7FSFtkXast0', 'Hip Club Groove — Trailer Park Hip Hop'),
    'Hip Club Groove roundup button',
)
path.write_text(text, encoding='utf-8')

# Mattmac feature
path = Path('blog/mattmac-smoke-signals.html')
text = path.read_text(encoding='utf-8')
if EMBED_CSS not in text:
    text = replace_once(text, '.watch{display:inline-block;background:#c33;color:#fff!important;text-decoration:none;padding:10px 15px;border-radius:4px;font-family:\'Oswald\';text-transform:uppercase;letter-spacing:.08em;margin:16px 0}', '.watch{display:inline-block;background:#c33;color:#fff!important;text-decoration:none;padding:10px 15px;border-radius:4px;font-family:\'Oswald\';text-transform:uppercase;letter-spacing:.08em;margin:16px 0}' + EMBED_CSS, 'Mattmac CSS')
text = replace_once(
    text,
    '<a class="watch" href="https://www.youtube.com/results?search_query=Mattmac+I+Remember+When+QuestionATL" target="_blank" rel="noopener">Watch “I Remember When” on YouTube</a>',
    embed('IifrfX-D4NY', 'Mattmac and QuestionATL — I Remember When'),
    'Mattmac button',
)
path.write_text(text, encoding='utf-8')

# Hip Club Groove feature
path = Path('blog/hip-club-groove-dead-words.html')
text = path.read_text(encoding='utf-8')
if EMBED_CSS not in text:
    text = replace_once(text, '.watch{display:inline-block;background:#c33;color:#fff!important;text-decoration:none;padding:10px 15px;border-radius:4px;font-family:\'Oswald\';text-transform:uppercase;letter-spacing:.08em;margin:16px 0}', '.watch{display:inline-block;background:#c33;color:#fff!important;text-decoration:none;padding:10px 15px;border-radius:4px;font-family:\'Oswald\';text-transform:uppercase;letter-spacing:.08em;margin:16px 0}' + EMBED_CSS, 'HCG CSS')
text = replace_once(
    text,
    '<a class="watch" href="https://www.youtube.com/results?search_query=Hip+Club+Groove+Dead+Words" target="_blank" rel="noopener">Hear “Dead Words” on YouTube</a>',
    '<p>There does not appear to be an embeddable YouTube upload for “Dead Words” yet, so here is a look back at Hip Club Groove before the three-decade gap.</p>' + embed('7FSFtkXast0', 'Hip Club Groove — Trailer Park Hip Hop'),
    'HCG feature button',
)
path.write_text(text, encoding='utf-8')

print('Replaced Sept. 11 YouTube buttons with embeds and replaced the broken AR Paisley video.')
