"""Offline, repeatable evidence extraction across the complete artist catalogue."""
import re
import unicodedata


def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.lower()) if unicodedata.category(c) != 'Mn').replace('’', "'")


# These describe music, not demographic attributes. Every extraction keeps its sentence.
STYLES = {
    'experimental-electronic': r'experimental electronic(?: music)?',
    'cloud-pop': r'\bcloud[ -]pop\b', 'cloud-rap': r'\bcloud[ -]rap\b',
    'hyperpop': r'\bhyper[ -]?pop\b', 'bedroom-pop': r'\bbedroom[ -]pop\b',
    'lo-fi': r'\blo[ -]?fi\b', 'chillwave': r'\bchillwave\b',
    'alternative-pop': r'\b(?:alternative|alt)[ -]pop\b',
    'emo-rap': r'\bemo[ -]rap\b', 'boom-bap': r'boom[ -]bap', 'trap': r'\btrap\b', 'drill': r'\bdrill\b',
    'conscious-rap': r'conscious (?:rap|hip[ -]hop)',
    'alternative-rap': r'alternative hip[ -]hop|alternative rap',
    'abstract-rap': r'abstract rap|experimental hip[ -]hop',
    'jazz-rap': r'jazz[ -](?:rap|inflected hip[ -]hop)',
    'melodic-rap': r'melodic (?:rap|hip[ -]hop)',
    'wordplay': r'wordplay|witty lyricism|intricate lyricism',
    'neo-soul': r'neo[ -]soul', 'alternative-rnb': r'alternative[ -]r&b|alt[ -]r&b',
    'adult-rnb': r'adult r&b', 'soul-pop': r'soul[ -]pop|soul, pop',
    'funk': r'\bfunk\b|\bfunky\b', 'gospel': r'\bgospel\b',
    'folk-pop': r'folk[ -]pop', 'folk-rock': r'folk[ -]rock',
    'indie-folk': r'indie[ -]folk', 'acoustic': r'\bacoustic\b|finger[ -]pick',
    'indie-rock': r'indie[ -]rock', 'indie-pop': r'indie[ -]pop|guitar pop|jangly',
    'power-pop': r'power[ -]pop', 'dream-pop': r'dream[ -]pop',
    'shoegaze': r'shoegaz', 'post-punk': r'post[ -]punk',
    'post-rock': r'post[ -]rock', 'garage-rock': r'garage[ -]rock',
    'hard-rock': r'hard[ -]rock', 'psychedelic': r'psychedelic',
    'synth-pop': r'synth[ -]?pop|electropop', 'dance-pop': r'dance[ -]pop',
    'art-pop': r'art[ -]pop', 'electro-punk': r'electro[ -]punk|electroclash|electronic.{0,40}\bpunk|\bpunk.{0,40}electronic',
    'pop-punk': r'pop[ -]punk', 'post-hardcore': r'post[ -]hardcore',
    'hardcore': r'\bhardcore\b', 'punk-rock': r'punk[ -]rock',
    'death-metal': r'death[ -]metal', 'black-metal': r'black[ -]metal',
    'doom-metal': r'doom[ -]metal', 'metalcore': r'metalcore',
    'thrash-metal': r'thrash', 'heavy-metal': r'heavy[ -]metal',
    'trip-hop': r'trip[ -]hop', 'downtempo': r'downtempo',
    'ambient': r'\bambient\b', 'house': r'\bhouse music|\bdeep house|\bsoulful house',
    'techno': r'\btechno\b', 'drum-and-bass': r'drum[ -]and[ -]bass|drum & bass',
    'dubstep': r'dubstep', 'disco': r'\bdisco\b', 'dancehall': r'dancehall',
    'reggae': r'\breggae\b', 'roots-country': r'roots[ -]country|alt[ -]country|americana',
    'bluegrass': r'bluegrass', 'traditional-folk': r'traditional folk|traditional songs',
    'jazz-fusion': r'jazz[ -]fusion|jazz, funk', 'improvised': r'improvisation|improvised',
    'vocal-jazz': r'jazz (?:singer|vocalist)|vocal jazz',
    'blues': r'\bblues\b', 'orchestral': r'orchestral|chamber pop',
    'singer-songwriter': r'singer[ -]songwriter',
}
SCENES = ['Toronto','Scarborough','Brampton','Mississauga','Hamilton','Montreal','Vancouver',
          'Halifax','Ottawa','Winnipeg','Edmonton','Calgary','Victoria','Quebec City',
          'Saskatoon','Regina','London, Ontario','Newfoundland','Cape Breton']
RELATION = re.compile(r'collaborat|produc(?:ed|tion) (?:by|for)|records by|work(?:ed|ing)? with|'
                      r'featur(?:es|ed|ing)\b|member(?:s)? of|part of|formed|co-founded|'
                      r'fronted by|alongside|mentorship|mentored|collective|duo', re.I)


def extract_profile(bio, location=''):
    sentences = re.split(r'(?<=[.!?])\s+', bio)
    signals = []
    for key, pattern in STYLES.items():
        sentence = next((s for s in sentences if re.search(pattern, normalize(s))), None)
        if sentence:
            signals.append({'kind':'style','key':key,'label':key.replace('-', ' '),'evidence':sentence})
    for scene in SCENES:
        sentence = next((s for s in sentences if re.search(r'\b'+re.escape(normalize(scene))+r'\b', normalize(s))), None)
        if sentence:
            signals.append({'kind':'scene','key':('greater-toronto' if scene in ['Toronto','Scarborough','Brampton','Mississauga'] else normalize(scene)),'label':('Greater Toronto area' if scene in ['Toronto','Scarborough','Brampton','Mississauga'] else scene),'evidence':sentence})
    # Career references come from the biography, not remaster dates or album metadata.
    for decade in range(1960, 2030, 10):
        pattern = rf'\b{decade//10}\d\b|\b{decade}s\b'
        sentence = next((s for s in sentences if re.search(pattern, re.sub(r'\bborn[^,.]{0,70}\b(?:19|20)\d{2}\b', '', s, flags=re.I))), None)
        if decade in (1990,2000) and not sentence:
            sentence = next((s for s in sentences if 'turn-of-the-century' in s), None)
        if sentence:
            signals.append({'kind':'era','key':f'{decade}s','label':f'{decade}s','evidence':sentence})
    return list({(s['kind'],s['key']):s for s in signals}.values())


def extract_relationships(records):
    """Exact catalogue names in relationship-bearing biography sentences, bidirectionally."""
    patterns = []
    for record in records:
        name = record['name']
        # Very short/common names cannot safely be resolved from free text.
        if len(name) < 4 or name.lower() in {'promise','work','stars','live','baby','love','future','cube'}:
            continue
        names = [name, *record.get('aliases', [])]
        patterns.append((record, re.compile(r'(?<!\w)(?:'+ '|'.join(re.escape(n) for n in names) +r')(?!\w)')))
    edges = {}
    for record in records:
        for sentence in re.split(r'(?<=[.!?])\s+', record.get('fullBio','')):
            if not RELATION.search(sentence):
                continue
            for other, pattern in patterns:
                if other['name']==record['name'] or not pattern.search(sentence):
                    continue
                pair=tuple(sorted([record['name'],other['name']]))
                edges.setdefault(pair, {'artists':list(pair),'reason':f'Connected in {record["name"]}’s artist profile.',
                    'evidence':sentence,'source':record.get('profileHref') or '/artists.html','kind':'profile'})
    return list(edges.values())


def extract_track_relationships(records):
    """Use explicit featured-artist credits, never names elsewhere in a song title."""
    patterns = [(a, re.compile(r'(?<!\w)(?:'+ '|'.join(re.escape(n) for n in [a['name'], *a.get('aliases', [])]) +r')(?!\w)', re.I)) for a in records]
    edges = {}
    for artist in records:
        for title in artist.get('_trackTitles', []):
            match = re.search(r'\b(?:feat\.?|ft\.?|featuring)\s+(.+)', title, re.I)
            if not match:
                continue
            for other, pattern in patterns:
                if other['name'] == artist['name'] or not pattern.search(match[1]):
                    continue
                pair = tuple(sorted([artist['name'], other['name']]))
                edges.setdefault(pair, {'artists': list(pair), 'kind':'track-credit',
                    'reason': f'{artist["name"]} and {other["name"]} are credited together on “{title}” in Northern Dial’s library.',
                    'source': '/artists.html', 'evidence': title})
    return list(edges.values())
