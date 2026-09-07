#!/usr/bin/env python3
# One-time site-wide Northern Dial Discovery navigation and homepage banner update.

from pathlib import Path
import re

CORE_PAGES = {
    "index.html": "home",
    "library.html": "songs",
    "artists.html": "artists",
    "discover.html": "discover",
}

def root_nav(page, nav_class):
    labels = [
        ("home", "./" if page == "index.html" else "index.html", "Home"),
        ("songs", "library.html", "Songs"),
        ("artists", "artists.html", "Artists"),
        ("discover", "discover.html", "Discover"),
        ("blog", "blog/", "Blog"),
        ("submit", ("./#submit" if page == "index.html" else "index.html#submit"), "Submit"),
    ]
    current = CORE_PAGES[page]
    links = []
    for key, href, label in labels:
        attrs = ""
        if key == current:
            attrs = ' class="active" aria-current="page"'
        links.append(f'    <a href="{href}"{attrs}>{label}</a>')
    return f'<nav class="{nav_class}" aria-label="Main navigation">\n' + "\n".join(links) + "\n</nav>"

def replace_root_nav(path):
    text = path.read_text(encoding="utf-8")
    nav_class = "site-nav" if path.name == "index.html" else "page-nav"
    pattern = re.compile(
        rf'<nav class="{re.escape(nav_class)}" aria-label="Main navigation">.*?</nav>',
        re.S,
    )
    updated, count = pattern.subn(root_nav(path.name, nav_class), text, count=1)
    if count != 1:
        raise RuntimeError(f"Could not replace main nav in {path}")
    path.write_text(updated, encoding="utf-8")

def blog_nav():
    return '''<nav>
    <ul>
      <li><a href="../index.html">Home</a></li>
      <li><a href="../library.html">Songs</a></li>
      <li><a href="../artists.html">Artists</a></li>
      <li><a href="../discover.html">Discover</a></li>
      <li><a href="index.html" class="active">Blog</a></li>
      <li><a href="../index.html#submit">Submit</a></li>
    </ul>
  </nav>'''

def replace_blog_nav(path):
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(r'<nav>\s*<ul>.*?</ul>\s*</nav>', blog_nav(), text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"Could not replace blog nav in {path}")
    updated = updated.replace("flex: 1 1 25%;", "flex: 1 1 33.333%;")
    path.write_text(updated, encoding="utf-8")

def add_home_banner(path):
    text = path.read_text(encoding="utf-8")
    if 'class="discovery-banner"' not in text:
        css = r'''
.discovery-banner {
    align-items: center;
    background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
    border: 4px solid #C33;
    border-radius: 10px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.18);
    color: #fff;
    display: flex;
    gap: 28px;
    justify-content: space-between;
    margin: -22px 0 38px;
    padding: 24px 28px;
}
.discovery-banner-copy {
    min-width: 0;
}
.discovery-banner-kicker {
    color: #C33;
    font-family: 'Oswald', sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    margin-bottom: 5px;
    text-transform: uppercase;
}
.discovery-banner h2 {
    color: #fff;
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(2rem, 4vw, 2.8rem);
    font-weight: 400;
    letter-spacing: 0.04em;
    line-height: 1;
    margin-bottom: 7px;
    text-transform: uppercase;
}
.discovery-banner p {
    color: #d8d8d8;
    font-size: 1rem;
    line-height: 1.5;
    margin: 0;
    max-width: 720px;
}
.discovery-banner-cta {
    background: #C33;
    border: 2px solid #C33;
    border-radius: 7px;
    color: #fff;
    flex: 0 0 auto;
    font-family: 'Oswald', sans-serif;
    font-size: 0.9rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    padding: 12px 20px;
    text-decoration: none;
    text-transform: uppercase;
    transition: background-color 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}
.discovery-banner-cta:hover,
.discovery-banner-cta:focus {
    background: #8B2323;
    border-color: #8B2323;
    transform: translateY(-2px);
}
'''
        marker = "\n.custom-player {"
        if marker not in text:
            raise RuntimeError("Could not find homepage CSS insertion point")
        text = text.replace(marker, css + marker, 1)

        banner = r'''
<section class="discovery-banner" aria-labelledby="discovery-banner-title">
    <div class="discovery-banner-copy">
        <div class="discovery-banner-kicker">Northern Dial Discovery</div>
        <h2 id="discovery-banner-title">Find Your Next Canadian Artist</h2>
        <p>Pick a genre, era or artist you already love and we’ll dial up five Canadian artists worth checking out.</p>
    </div>
    <a class="discovery-banner-cta" href="./discover.html">Start Discovering</a>
</section>
'''
        marker = '\n</div>\n\n<nav class="site-nav" aria-label="Main navigation">'
        if marker not in text:
            raise RuntimeError("Could not find homepage banner insertion point")
        text = text.replace(marker, banner + '\n</div>\n\n<nav class="site-nav" aria-label="Main navigation">', 1)

    text = text.replace("grid-template-columns: repeat(4, minmax(0, 1fr));", "grid-template-columns: repeat(3, minmax(0, 1fr));")
    mobile_css = r'''
    .discovery-banner {
        align-items: flex-start;
        flex-direction: column;
        gap: 16px;
        margin-top: -28px;
        padding: 20px;
    }
    .discovery-banner-cta {
        text-align: center;
        width: 100%;
    }
'''
    media_marker = "@media (max-width: 768px) {"
    if mobile_css.strip() not in text and media_marker in text:
        text = text.replace(media_marker, media_marker + "\n" + mobile_css, 1)

    path.write_text(text, encoding="utf-8")

def patch_discovery(path):
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        'placeholder="e.g. VIBI, Ari Lennox, Drake"',
        'placeholder="e.g. VIBI, Drake, Portishead"',
    )
    text = text.replace('"vibi":["pop","indie-alternative"],"ari lennox":["rnb-soul"],',
                        '"vibi":["pop","indie-alternative"],')
    if 'const DISCOVERY_EXCLUSIONS=' not in text:
        marker = 'const ERA_LABELS={"2020s":"2020s","2010s":"2010s","2000s":"2000s","1990s":"1990s","pre-1990":"1980s and earlier"};'
        if marker not in text:
            raise RuntimeError("Could not find Discovery exclusion insertion point")
        text = text.replace(marker, marker + '\n    const DISCOVERY_EXCLUSIONS=new Set(["ari lennox"]);', 1)
    old = 'if(!name||seen.has(key))return;seen.add(key);'
    new = 'if(!name||seen.has(key)||DISCOVERY_EXCLUSIONS.has(key))return;seen.add(key);'
    if old in text:
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")

def add_ari_removal():
    path = Path("artist_removals.txt")
    lines = path.read_text(encoding="utf-8").splitlines()
    if not any(line.strip().casefold() == "ari lennox" for line in lines):
        if lines and lines[-1].strip():
            lines.append("")
        lines.append("Ari Lennox")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    unresolved = Path("artist_unresolved.txt")
    if unresolved.exists():
        unresolved_lines = [
            line for line in unresolved.read_text(encoding="utf-8").splitlines()
            if line.strip().casefold() != "ari lennox"
        ]
        unresolved.write_text("\n".join(unresolved_lines) + "\n", encoding="utf-8")

def main():
    for filename in CORE_PAGES:
        replace_root_nav(Path(filename))
    add_home_banner(Path("index.html"))
    for path in sorted(Path("blog").glob("*.html")):
        replace_blog_nav(path)
    patch_discovery(Path("discover.html"))
    add_ari_removal()
    print("Discovery navigation, homepage banner, and Ari Lennox exclusion applied.")

if __name__ == "__main__":
    main()
