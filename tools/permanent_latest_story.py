from pathlib import Path
import re

path = Path('nd-shell.js')
text = path.read_text(encoding='utf-8')

# Remove the hardcoded story object. The current archive/homepage source order and dates
# are the source of truth; JavaScript must never re-inject an older story as "latest".
text, latest_count = re.subn(
    r"\n  const LATEST_STORY = \{.*?\n  \};\n",
    "\n",
    text,
    count=1,
    flags=re.S,
)

# Remove the old DOM injector that could recreate and prepend a hardcoded story.
text, function_count = re.subn(
    r"\n  function addLatestStory\(\) \{.*?\n  \}\n\n  function styleBlogArchiveActions",
    "\n  function styleBlogArchiveActions",
    text,
    count=1,
    flags=re.S,
)

# Sorting already uses newest date first, preserving source order for same-day stories.
# The first resulting blog card is then styled as the featured story.
text = text.replace(
    "  function init() {\n    addLatestStory();\n    sortStoryCards();\n    featureNewestBlogStory();",
    "  function init() {\n    sortStoryCards();\n    featureNewestBlogStory();",
    1,
)

if latest_count != 1:
    raise SystemExit(f'Expected one hardcoded LATEST_STORY block, removed {latest_count}')
if function_count != 1:
    raise SystemExit(f'Expected one addLatestStory function, removed {function_count}')
if 'addLatestStory();' in text or 'const LATEST_STORY' in text:
    raise SystemExit('Hardcoded latest-story injector still present')

path.write_text(text, encoding='utf-8')
print('Permanent latest-story rule applied: newest listed story becomes featured; no hardcoded injector remains.')
