#!/usr/bin/env python3
from pathlib import Path
import re, sys

FILES=[Path('index.html'),Path('library.html'),Path('artists.html'),Path('discover.html'),Path('about.html'),Path('sessions.html'),Path('archive.html'),Path('accessibility.html'),Path('rights.html'),Path('survey.html')]
FILES += sorted(Path('fr').glob('*.html'))
issues=[]
for p in FILES:
    if not p.exists():
        issues.append(f'{p}: missing file'); continue
    t=p.read_text(encoding='utf-8',errors='ignore')
    if not re.search(r'<html[^>]+lang=["\'][^"\']+["\']',t,re.I): issues.append(f'{p}: missing html lang')
    if not re.search(r'<title>[^<]+</title>',t,re.I): issues.append(f'{p}: missing title')
    h1=len(re.findall(r'<h1\b',t,re.I))
    if h1!=1: issues.append(f'{p}: expected 1 h1, found {h1}')
    for tag in re.findall(r'<img\b[^>]*>',t,re.I):
        if not re.search(r'\balt=',tag,re.I): issues.append(f'{p}: image missing alt')
    for tag in re.findall(r'<button\b[^>]*>(.*?)</button>',t,re.I|re.S):
        if not re.sub(r'<[^>]+>','',tag).strip() and 'aria-label=' not in tag.lower(): issues.append(f'{p}: button may lack accessible name')
print(f'Checked {len(FILES)} public HTML files.')
if issues:
    print('Accessibility guardrail findings:')
    for i in issues: print('-',i)
    sys.exit(1)
print('Automated guardrails passed. This is not WCAG certification; manual keyboard, screen-reader and contrast testing remains required.')
