from pathlib import Path

blog = Path('blog/index.html')
home = Path('index.html')

blog_cards = '''
      <!-- SEP12_VIBI_LOLO_START -->
      <article class="card"><a href="on-repeat-vibi-angeldies.html"><img src="https://i.ytimg.com/vi/muM8YqfCZ54/maxresdefault.jpg" alt="VIBI angeldies" style="width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;display:block;background:#111;" /></a><div class="card-body"><p class="card-date">September 12, 2026 · On Repeat</p><h2 class="card-title">On Repeat: VIBI’s “angeldies”</h2><div class="card-accent"></div><p class="card-excerpt">The Canadian singer-songwriter follows <em>Building the Band</em>, “wildwoman” and “killshot” with another release in a fast-moving 2026 run.</p><a href="on-repeat-vibi-angeldies.html" class="card-link">Read More</a></div></article>
      <article class="card"><a href="lolo-the-punisher.html"><img src="https://i.ytimg.com/vi/5apYyXJ1hNg/maxresdefault.jpg" alt="LØLØ the punisher" style="width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;display:block;background:#111;" /></a><div class="card-body"><p class="card-date">September 12, 2026 · Artist Feature</p><h2 class="card-title">LØLØ Knows Exactly Where the Sore Spot Is</h2><div class="card-accent"></div><p class="card-excerpt">On “the punisher,” the Toronto singer-songwriter turns post-breakup doom-scrolling into one of the sharpest songs on <em>god forbid a girl spits out her feelings!</em></p><a href="lolo-the-punisher.html" class="card-link">Read More</a></div></article>
      <!-- SEP12_VIBI_LOLO_END -->
'''

home_cards = '''
      <!-- SEP12_VIBI_LOLO_HOME_START -->
      <a href="/blog/on-repeat-vibi-angeldies.html" style="text-decoration:none;display:block;border-radius:10px;overflow:hidden;background:white;border:1px solid #e0e0e0;transition:box-shadow .25s,transform .25s;"><img src="https://i.ytimg.com/vi/muM8YqfCZ54/maxresdefault.jpg" alt="VIBI angeldies" style="width:100%;height:200px;object-fit:cover;object-position:center;display:block;background:#111;"><div style="padding:20px 18px 18px;"><p style="font-family:'Roboto Condensed',sans-serif;font-size:.75rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#CC3333;margin-bottom:8px;">September 12, 2026 · On Repeat</p><h3 style="font-family:'Oswald',sans-serif;font-size:1.3rem;color:#1a1a1a;margin-bottom:10px;line-height:1.2;">On Repeat: VIBI’s “angeldies”</h3><p style="font-family:'Roboto Condensed',sans-serif;font-size:.92rem;color:#555;line-height:1.6;margin-bottom:14px;">The Canadian singer-songwriter keeps a fast-moving 2026 run going with “angeldies.”</p><span style="font-family:'Oswald',sans-serif;font-size:.8rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#CC3333;">Read More →</span></div></a>
      <a href="/blog/lolo-the-punisher.html" style="text-decoration:none;display:block;border-radius:10px;overflow:hidden;background:white;border:1px solid #e0e0e0;transition:box-shadow .25s,transform .25s;"><img src="https://i.ytimg.com/vi/5apYyXJ1hNg/maxresdefault.jpg" alt="LØLØ the punisher" style="width:100%;height:200px;object-fit:cover;object-position:center;display:block;background:#111;"><div style="padding:20px 18px 18px;"><p style="font-family:'Roboto Condensed',sans-serif;font-size:.75rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#CC3333;margin-bottom:8px;">September 12, 2026 · Artist Feature</p><h3 style="font-family:'Oswald',sans-serif;font-size:1.3rem;color:#1a1a1a;margin-bottom:10px;line-height:1.2;">LØLØ Knows Exactly Where the Sore Spot Is</h3><p style="font-family:'Roboto Condensed',sans-serif;font-size:.92rem;color:#555;line-height:1.6;margin-bottom:14px;">“the punisher” turns post-breakup doom-scrolling into something painfully catchy.</p><span style="font-family:'Oswald',sans-serif;font-size:.8rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#CC3333;">Read More →</span></div></a>
      <!-- SEP12_VIBI_LOLO_HOME_END -->
'''

text = blog.read_text(encoding='utf-8')
if 'SEP12_VIBI_LOLO_START' not in text:
    marker = '<!-- SEPT11_EDITORIAL_START -->'
    if marker not in text:
        raise SystemExit('Blog insertion marker not found')
    text = text.replace(marker, blog_cards + '\n      ' + marker, 1)
    blog.write_text(text, encoding='utf-8')

text = home.read_text(encoding='utf-8')
if 'SEP12_VIBI_LOLO_HOME_START' not in text:
    marker = '<!-- SEPT11_EDITORIAL_START -->'
    if marker not in text:
        raise SystemExit('Homepage insertion marker not found')
    text = text.replace(marker, home_cards + '\n      ' + marker, 1)
    home.write_text(text, encoding='utf-8')

print('Published VIBI and LØLØ cards to blog and homepage.')