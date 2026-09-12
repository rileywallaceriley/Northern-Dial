from pathlib import Path

path = Path('nd-shell.js')
text = path.read_text(encoding='utf-8')
old = """          .map((card, index) => ({\n            card,\n            index,\n            date: parseDate(card.querySelector('.card-date')?.textContent)\n          }))\n          .sort((a, b) => (b.date - a.date) || (a.index - b.index))\n"""
new = """          .map((card, index) => ({\n            card,\n            index,\n            featured: card.classList.contains('featured'),\n            date: parseDate(card.querySelector('.card-date')?.textContent)\n          }))\n          .sort((a, b) => (Number(b.featured) - Number(a.featured)) || (b.date - a.date) || (a.index - b.index))\n"""
if old not in text:
    raise SystemExit('Blog sort block not found')
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
print('Pinned explicit featured card ahead of date sorting on the blog archive.')
