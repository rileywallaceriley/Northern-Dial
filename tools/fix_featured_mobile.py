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
