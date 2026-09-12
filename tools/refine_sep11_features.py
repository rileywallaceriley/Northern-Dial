from pathlib import Path
import re, subprocess

ROOT=Path('.')

def yt_id(query, fallback=''):
    try:
        out=subprocess.check_output(['yt-dlp','ytsearch1:'+query,'--print','%(id)s','--skip-download','--quiet'], text=True, timeout=60).strip().splitlines()
        if out: return out[0].strip()
    except Exception as e:
        print('yt-dlp lookup failed', query, e)
    return fallback

VIDEOS={
 'Mattmac':'Mattmac QuestionATL I Remember When official music video',
 'CG Tears':'CG Tears I\'m Falling Up official video',
 'Jon McKiel':'Jon McKiel For Shadow official',
 'Starpainter':'Starpainter Cayenne Flowerbed official',
 'Hip Club Groove':'Hip Club Groove Dead Words official',
 'AR Paisley':'AR Paisley Walk of Shame official',
 'FRVRFRIDAY':'FRVRFRIDAY BORN WINNER Boi-1da official',
 'TOBi':'TOBi Hoodwinked Dreamhouse Studios official',
 'LOONY':'LOONY RaGDOLL official',
 'NorthSideBenji':'NorthSideBenji TRYNA WIN Boi-1da official',
}
FALLBACK={'Mattmac':'IifrfX-D4NY','AR Paisley':'sa7F1nj_TG4','TOBi':'t1cb_rCvf4w'}
ids={k:yt_id(q,FALLBACK.get(k,'')) for k,q in VIDEOS.items()}
print('Resolved videos:',ids)

def iframe(vid,title):
    if not vid:
        return ''
    return f'<div class="video-embed"><iframe src="https://www.youtube-nocookie.com/embed/{vid}" title="{title}" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>'

def patch_blog(path, mapping):
    p=ROOT/path
    s=p.read_text()
    if '.video-embed{' not in s:
        s=s.replace('.note{', '.video-embed{position:relative;width:100%;aspect-ratio:16/9;margin:18px 0 6px;background:#111;border-radius:6px;overflow:hidden}.video-embed iframe{position:absolute;inset:0;width:100%;height:100%;border:0}.note{')
    for label,(artist,title) in mapping.items():
        vid=ids.get(artist,'')
        if not vid: continue
        # replace the first watch button associated with this exact visible label
        pat=r'<a class="watch"[^>]*>'+re.escape(label)+r'</a>'
        s,n=re.subn(pat, iframe(vid,title), s, count=1)
        print(path, artist, 'embed replacements', n)
    p.write_text(s)

patch_blog(Path('blog/new-canadian-releases-september-11-2026.html'), {
 'Watch “I Remember When” on YouTube':('Mattmac','Mattmac and QuestionATL — I Remember When'),
 'Watch “I\'m Falling Up” on YouTube':('CG Tears','CG Tears — I’m Falling Up'),
 'Hear “For Shadow” on YouTube':('Jon McKiel','Jon McKiel — For Shadow'),
 'Hear Starpainter on YouTube':('Starpainter','Starpainter — Cayenne Flowerbed'),
 'Hear “Dead Words” on YouTube':('Hip Club Groove','Hip Club Groove — Dead Words'),
})
patch_blog(Path('blog/if-you-like-drake-canadian-artists.html'), {
 'Watch “Walk of Shame” on YouTube':('AR Paisley','AR Paisley — Walk of Shame'),
 'Hear “BORN WINNER” on YouTube':('FRVRFRIDAY','FRVRFRIDAY — BORN WINNER'),
 'Watch “Hoodwinked” on YouTube':('TOBi','TOBi — Hoodwinked at Dreamhouse Studios'),
 'Hear “RaGDOLL” on YouTube':('LOONY','LOONY — RaGDOLL'),
 'Hear “TRYNA WIN” on YouTube':('NorthSideBenji','NorthSideBenji and Boi-1da — TRYNA WIN'),
})

bios={
'cg-tears.html':[
'CG Tears is a Calgary trio made up of Clinton St. John, Morgan Greenwood and Chad VanGaalen. St. John brings the cryptic, folk-leaning songwriting he developed through projects including The Cape May and Pale Air Singers. Greenwood is a producer and multi-instrumentalist with an electronic sensibility, while VanGaalen is a longtime Calgary songwriter, visual artist and restless studio experimenter. What began as a collaboration between St. John and Greenwood expanded when VanGaalen came in to mix the music and started adding parts, backing vocals and arrangement ideas of his own.',
'Their self-titled debut arrived in September 2026 through Victory Pool Records after years of the three musicians circling one another creatively. The record leans on echo-heavy synths, intricate rhythms, off-centre arrangements and melodies that keep pulling the songs back toward pop even when the production gets strange. “I’m Falling Up” is one of the clearest introductions: catchy on the surface, but full of small structural decisions that make the track feel unstable in a good way.',
'CG Tears works because none of the three members disappears into a generic supergroup sound. St. John’s impressionistic writing, Greenwood’s production detail and VanGaalen’s taste for texture remain recognizable, but the project gives those instincts somewhere new to collide. For Northern Dial, they sit in the part of Canadian independent music where electronic production, indie rock and experimental pop stop behaving like separate scenes.'
],
'jon-mckiel.html':[
'Jon McKiel is a New Brunswick songwriter and recording artist whose catalogue has gradually moved from guitar-forward indie rock into something stranger, looser and more interested in the recording process itself. Albums such as <em>Bobby Joe Hope</em> and 2024’s <em>Hex</em> established a version of McKiel’s writing where melody stays approachable even when the textures around it warp, smear or drift out of expected shape.',
'His 2026 album <em>Gold Horatio</em> deepens that approach through a close collaboration with Jay Crocker. The two recorded in Baie Verte and Sackville, New Brunswick, handling arrangements, production and performances together before Crocker mixed the album and Harris Newman mastered it. Songs such as “For Shadow,” “Guru,” “Rosemary” and “Stinging Reflection” feel intimate without sounding small, with home-studio closeness sitting beside unusually detailed production choices.',
'That balance is a big part of McKiel’s appeal. He can write a song that works on acoustic structure alone, then surround it with enough odd detail to make repeat listens feel different. Within Northern Dial’s library, he connects East Coast songwriting to a more exploratory branch of Canadian indie music, where atmosphere and studio experimentation matter as much as the hook.'
],
'starpainter.html':[
'Starpainter is a Lethbridge, Alberta band led by songwriter Joel Stretch. Since forming in 2019, the group has built a sound around the overlap between cinematic folk, fuzzy country rock and richly textured indie pop. The current six-piece also includes Joel Gray, Mickey Hayward, Dylan Wagner, Bailey Kate and Tyler Stewart, giving Stretch’s songs enough room to move between quiet acoustic detail and a fuller band sound.',
'After <em>Rattlesnake Dream</em> in 2023, Starpainter returned in 2026 with <em>Cayenne Flowerbed</em>. Produced and engineered by Chris Dadge at Child Stone Studios in Calgary, the album became the band’s most collaborative record to date. Bright acoustic guitars, slide guitar and idiosyncratic percussion sit underneath songs about distance, routine, family and the ordinary details that start carrying more weight as life changes.',
'The title track turns a memory of Stretch’s grandmother protecting birds from neighbourhood cats into a song about the anger that can live inside love. Elsewhere, tracks such as “I Found a River” and “Rabbits” show how comfortable the band is letting country language and indie-rock instincts share the same space. Starpainter fits Northern Dial as a reminder that some of the most interesting Canadian guitar music is being made well outside the country’s biggest music centres.'
],
'hip-club-groove.html':[
'Hip Club Groove came out of Truro, Nova Scotia in the early 1990s before becoming part of Halifax’s unusually cross-pollinated independent music scene. The core lineup of Cheklove Shakil, MacKenzie and DJ Moves built a rap group in a city better known nationally at the time for guitar bands, but they rarely treated those worlds as separate. They played mixed bills, toured with Sloan and helped make East Coast hip-hop visible to audiences who might not otherwise have encountered it.',
'The group released <em>Cool Beans</em>, <em>Trailer Park Hip Hop</em> and <em>Land of the Lost</em> during its original run, while early connections to artists including Sixtoo and Buck 65 place Hip Club Groove inside a much larger Canadian underground lineage. A later <em>Unreleased &amp; Rare</em> collection preserved material from that period, but for decades the group existed mostly as history rather than an active recording concern.',
'That changed in 2026 with “Dead Words,” recorded for Hand’Solo Records’ <em>Bassments of Badmen 4</em>. Cheklove and MacKenzie return to the mic while Moves handles production and cuts, turning the reunion into more than a nostalgia exercise. The track sounds deliberately rooted in boom-bap, but its real value is connective: it links a formative Halifax rap group back into the current Canadian independent ecosystem three decades later.'
],
'loony.html':[
'LOONY is a Toronto singer and songwriter working in the space between R&amp;B, neo-soul and left-field pop. Her songs tend to avoid oversized drama in favour of close detail: conversational phrasing, awkward emotional turns, warm low-end and melodies that sound lived-in rather than polished into perfect symmetry. That restraint has become one of the clearest signatures in her catalogue.',
'Her earlier releases built momentum through songs and projects that foregrounded voice and groove, leading into the 2024 self-titled album <em>LOONY</em>. In 2026 she followed with <em>JUST HAPPY TO BE HERE!</em> and then the July single “RaGDOLL,” continuing to push her writing toward records that feel intimate without becoming musically slight. The arrangements leave enough air around her vocals for tiny shifts in tone to carry the song.',
'For listeners coming from Toronto’s better-known late-night R&amp;B tradition, LOONY offers a different route through the city. The mood can be familiar, but the perspective is less immaculate and more human-scale. On Northern Dial, she sits comfortably beside artists who treat R&amp;B as a songwriting language rather than a fixed production template.'
],
'northsidebenji.html':[
'NorthSideBenji is a Brampton rapper whose music balances street detail, melody and a delivery that rarely needs to force the point. He emerged as one of the more durable voices in the GTA’s melodic rap lane by keeping the writing specific while letting hooks arrive naturally. Even on harder records, his delivery often stays measured, giving the songs a reflective quality that separates him from artists working with similar production.',
'His catalogue stretches across singles and projects that move between survival writing, ambition and the emotional cost of the environments he describes. Recent releases include 2025 material such as “Latest Trends,” followed in 2026 by “Tired Of Counting,” “Crowd Control” and “TRYNA WIN.” The latter paired him with Boi-1da and Canada Soccer as part of the <em>WHAT IF IT ALL GOES RIGHT?</em> project, putting his voice inside a national music program without sanding down the style that made him recognizable.',
'That Boi-1da connection makes NorthSideBenji an obvious bridge for Drake listeners, but he works best when heard on his own terms. His records are less about copying Toronto’s established rap template than extending one branch of it from Brampton, where melody and street rap have developed their own local grammar. Northern Dial uses him as a link between the GTA’s mainstream rap ecosystem and the deeper regional catalogue around it.'
]}
for fn,paras in bios.items():
    p=ROOT/'artists'/fn
    s=p.read_text()
    block=''.join(f'<p class="bio">{x}</p>' for x in paras)+'\n        '
    s,n=re.subn(r'(\s*<p class="bio">.*?</p>)+\s*(?=<div class="official-links">|<a class="cta")', '\n        '+block, s, flags=re.S)
    print(fn,'bio blocks',n)
    p.write_text(s)

# Make the new-release roundup the visual lead on the blog index.
p=ROOT/'blog/index.html'; s=p.read_text()
if '.card.featured{' not in s:
    s=s.replace('.card:hover {', '.card.featured{grid-column:1/-1;display:grid;grid-template-columns:minmax(0,1.35fr) minmax(320px,.85fr);border:3px solid #CC3333}.card.featured>a{display:block;min-height:100%}.card.featured>a img{height:100%!important;min-height:320px;object-fit:cover!important}.card.featured .card-body{justify-content:center}.card.featured .card-title{font-size:2rem}@media(max-width:760px){.card.featured{display:flex;grid-column:auto}.card.featured>a img{height:auto!important;min-height:0}}\n    .card:hover {')
s=s.replace('<article class="card"><a href="new-canadian-releases-september-11-2026.html">','<article class="card featured"><a href="new-canadian-releases-september-11-2026.html">',1)
p.write_text(s)

# Make the same story the homepage lead card and enlarge it.
p=ROOT/'index.html'; s=p.read_text()
start='<!-- SEPT11_HOME_EDITORIAL_START -->'; end='<!-- SEPT11_HOME_EDITORIAL_END -->'
if start in s and end in s:
    a,b=s.split(start,1); mid,c=b.split(end,1)
    cards=re.findall(r'<a href="/blog/.*?</a>',mid,flags=re.S)
    target=[x for x in cards if 'new-canadian-releases-september-11-2026.html' in x]
    if target:
        t=target[0]
        mid=mid.replace(t,'')
        t=t.replace('style="text-decoration:none;', 'style="grid-column:1/-1;text-decoration:none;',1)
        t=t.replace('height:200px;', 'height:320px;',1)
        mid='\n'+t+'\n'+mid
        s=a+start+mid+end+c
p.write_text(s)
