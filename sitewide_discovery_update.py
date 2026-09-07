#!/usr/bin/env python3
# Site-wide Northern Dial navigation, Discovery and mobile menu updater.

from pathlib import Path
import re

CORE_PAGES = {
    "index.html": "home",
    "library.html": "songs",
    "artists.html": "artists",
    "discover.html": "discover",
}

MOBILE_MENU_CSS = r'''

/* ND_MOBILE_MENU_CSS_START */
.mobile-menu-toggle {
    display: none;
}

.mobile-menu-links {
    align-items: stretch;
    display: flex;
    gap: inherit;
    justify-content: center;
    width: 100%;
}

.mobile-menu-links > li {
    list-style: none;
}

@media (max-width: 768px) {
    .mobile-menu-nav {
        display: block !important;
        padding: 0 !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 1000 !important;
    }

    .mobile-menu-toggle {
        align-items: center;
        background: #1a1a1a !important;
        border: 0 !important;
        border-radius: 0 !important;
        color: #ffffff !important;
        cursor: pointer;
        display: flex !important;
        font-family: 'Oswald', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        justify-content: space-between;
        letter-spacing: 0.14em !important;
        line-height: 1 !important;
        margin: 0 !important;
        min-height: 48px;
        padding: 13px 18px !important;
        text-transform: uppercase;
        width: 100% !important;
    }

    .mobile-menu-toggle:hover,
    .mobile-menu-toggle:focus {
        background: #262626 !important;
        color: #ffffff !important;
    }

    .mobile-menu-toggle:focus-visible {
        outline: 3px solid #CC3333 !important;
        outline-offset: -3px;
    }

    .mobile-menu-icon {
        color: #CC3333;
        font-family: Arial, sans-serif;
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: 0;
        line-height: 1;
    }

    .mobile-menu-links {
        background: #1a1a1a;
        display: none !important;
        flex-direction: column !important;
        gap: 0 !important;
        margin: 0 !important;
        max-width: none !important;
        padding: 0 !important;
        width: 100% !important;
    }

    .mobile-menu-nav.menu-open .mobile-menu-links {
        display: flex !important;
    }

    .mobile-menu-links > li {
        margin: 0 !important;
        padding: 0 !important;
        width: 100% !important;
    }

    .mobile-menu-links a,
    .mobile-menu-links li a {
        background: #1a1a1a !important;
        border: 0 !important;
        border-bottom: 1px solid #343434 !important;
        border-radius: 0 !important;
        color: #ffffff !important;
        display: block !important;
        flex: none !important;
        font-family: 'Oswald', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.11em !important;
        margin: 0 !important;
        padding: 14px 18px !important;
        text-align: left !important;
        text-decoration: none !important;
        text-transform: uppercase !important;
        width: 100% !important;
    }

    .mobile-menu-links a:hover,
    .mobile-menu-links a:focus,
    .mobile-menu-links a.active,
    .mobile-menu-links li a:hover,
    .mobile-menu-links li a:focus,
    .mobile-menu-links li a.active {
        background: #262626 !important;
        color: #CC3333 !important;
    }

    .mobile-menu-links a.active,
    .mobile-menu-links li a.active {
        border-left: 4px solid #CC3333 !important;
        padding-left: 14px !important;
    }

    .mobile-menu-links .submit-link,
    .mobile-menu-links li .submit-link {
        background: #CC3333 !important;
        border-bottom-color: #CC3333 !important;
        color: #ffffff !important;
    }

    .mobile-menu-links .submit-link:hover,
    .mobile-menu-links .submit-link:focus,
    .mobile-menu-links li .submit-link:hover,
    .mobile-menu-links li .submit-link:focus {
        background: #8B2323 !important;
        color: #ffffff !important;
    }
}
/* ND_MOBILE_MENU_CSS_END */
'''

MOBILE_MENU_JS = r'''
<script>
/* ND_MOBILE_MENU_JS_START */
(function () {
    const menus = document.querySelectorAll('.mobile-menu-nav');
    menus.forEach((nav, index) => {
        const toggle = nav.querySelector('.mobile-menu-toggle');
        const links = nav.querySelector('.mobile-menu-links');
        if (!toggle || !links) return;

        if (!links.id) links.id = `nd-mobile-menu-${index + 1}`;
        toggle.setAttribute('aria-controls', links.id);

        const icon = toggle.querySelector('.mobile-menu-icon');
        const closeMenu = () => {
            nav.classList.remove('menu-open');
            toggle.setAttribute('aria-expanded', 'false');
            toggle.setAttribute('aria-label', 'Open navigation menu');
            if (icon) icon.textContent = '☰';
        };

        const openMenu = () => {
            nav.classList.add('menu-open');
            toggle.setAttribute('aria-expanded', 'true');
            toggle.setAttribute('aria-label', 'Close navigation menu');
            if (icon) icon.textContent = '✕';
        };

        toggle.addEventListener('click', () => {
            if (nav.classList.contains('menu-open')) closeMenu();
            else openMenu();
        });

        links.addEventListener('click', event => {
            if (event.target.closest('a')) closeMenu();
        });

        document.addEventListener('keydown', event => {
            if (event.key === 'Escape') closeMenu();
        });

        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) closeMenu();
        });
    });
})();
/* ND_MOBILE_MENU_JS_END */
</script>
'''


def menu_button():
    return '''    <button class="mobile-menu-toggle" type="button" aria-expanded="false" aria-label="Open navigation menu">
        <span>Menu</span>
        <span class="mobile-menu-icon" aria-hidden="true">☰</span>
    </button>'''


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
        classes = []
        attrs = ""
        if key == current:
            classes.append("active")
            attrs += ' aria-current="page"'
        if key == "submit":
            classes.append("submit-link")
        if classes:
            attrs = f' class="{" ".join(classes)}"' + attrs
        links.append(f'        <a href="{href}"{attrs}>{label}</a>')
    return (
        f'<nav class="{nav_class} mobile-menu-nav" aria-label="Main navigation">\n'
        + menu_button() + "\n"
        + '    <div class="mobile-menu-links">\n'
        + "\n".join(links)
        + "\n    </div>\n</nav>"
    )


def replace_root_nav(path):
    text = path.read_text(encoding="utf-8")
    nav_class = "site-nav" if path.name == "index.html" else "page-nav"
    pattern = re.compile(
        rf'<nav class="{re.escape(nav_class)}(?: mobile-menu-nav)?" aria-label="Main navigation">.*?</nav>',
        re.S,
    )
    updated, count = pattern.subn(root_nav(path.name, nav_class), text, count=1)
    if count != 1:
        raise RuntimeError(f"Could not replace main nav in {path}")
    path.write_text(updated, encoding="utf-8")


def blog_nav():
    return '''<nav class="mobile-menu-nav" aria-label="Main navigation">
''' + menu_button() + '''
    <ul class="mobile-menu-links">
      <li><a href="../index.html">Home</a></li>
      <li><a href="../library.html">Songs</a></li>
      <li><a href="../artists.html">Artists</a></li>
      <li><a href="../discover.html">Discover</a></li>
      <li><a href="index.html" class="active">Blog</a></li>
      <li><a href="../index.html#submit" class="submit-link">Submit</a></li>
    </ul>
  </nav>'''


def replace_blog_nav(path):
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'<nav(?: class="mobile-menu-nav" aria-label="Main navigation")?>\s*(?:<button.*?</button>\s*)?<ul(?: class="mobile-menu-links")?>.*?</ul>\s*</nav>',
        re.S,
    )
    updated, count = pattern.subn(blog_nav(), text, count=1)
    if count != 1:
        raise RuntimeError(f"Could not replace blog nav in {path}")
    path.write_text(updated, encoding="utf-8")


def request_nav():
    links = [
        ("./", "Home", ""),
        ("./library.html", "Songs", ""),
        ("./artists.html", "Artists", ""),
        ("./discover.html", "Discover", ""),
        ("./blog/", "Blog", ""),
        ("./#submit", "Submit", "submit-link"),
    ]
    anchors = []
    for href, label, css_class in links:
        class_attr = f' class="{css_class}"' if css_class else ""
        anchors.append(f'        <a href="{href}"{class_attr}>{label}</a>')
    return (
        '<nav class="nav mobile-menu-nav" aria-label="Main navigation">\n'
        + menu_button() + "\n"
        + '    <div class="mobile-menu-links">\n'
        + "\n".join(anchors)
        + "\n    </div>\n</nav>"
    )


def replace_request_nav(path):
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'<nav class="nav(?: mobile-menu-nav)?" aria-label="Main navigation">.*?</nav>',
        re.S,
    )
    updated, count = pattern.subn(request_nav(), text, count=1)
    if count != 1:
        raise RuntimeError(f"Could not replace request nav in {path}")
    path.write_text(updated, encoding="utf-8")


def inject_mobile_menu_assets(path):
    text = path.read_text(encoding="utf-8")
    if "ND_MOBILE_MENU_CSS_START" not in text:
        if "</style>" not in text:
            raise RuntimeError(f"Could not find style block in {path}")
        text = text.replace("</style>", MOBILE_MENU_CSS + "\n</style>", 1)
    if "ND_MOBILE_MENU_JS_START" not in text:
        if "</body>" not in text:
            raise RuntimeError(f"Could not find body end in {path}")
        text = text.replace("</body>", MOBILE_MENU_JS + "\n</body>", 1)
    path.write_text(text, encoding="utf-8")


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
.discovery-banner-copy { min-width: 0; }
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
        marker = '\n</div>\n\n<nav class="site-nav'
        if marker not in text:
            raise RuntimeError("Could not find homepage banner insertion point")
        text = text.replace(marker, banner + '\n</div>\n\n<nav class="site-nav', 1)

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
        path = Path(filename)
        replace_root_nav(path)
        inject_mobile_menu_assets(path)

    add_home_banner(Path("index.html"))

    for path in sorted(Path("blog").glob("*.html")):
        replace_blog_nav(path)
        inject_mobile_menu_assets(path)

    request_path = Path("requests.html")
    if request_path.exists():
        replace_request_nav(request_path)
        inject_mobile_menu_assets(request_path)

    patch_discovery(Path("discover.html"))
    add_ari_removal()
    print("Responsive mobile hamburger navigation applied site-wide.")


if __name__ == "__main__":
    main()
