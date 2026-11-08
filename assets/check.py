#!/usr/bin/env python3
"""Check static navigation, generated files, and official citations in each table row."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import re
import subprocess

root = Path(__file__).resolve().parent.parent
pages = [root / 'overview.html', *sorted((root / 'pages').glob('*.html'))]
assert len(pages) == 6, 'expected the overview and five subpages'
class Checker(HTMLParser):
 def __init__(self, path):
  super().__init__(); self.path = path; self.row = None; self.rows = 0
 def handle_starttag(self, tag, attrs):
  attrs = dict(attrs)
  if tag == 'tr': self.row = {'td': 0, 'source': False}
  if self.row is not None and tag == 'td': self.row['td'] += 1
  if tag in ('a', 'link') and attrs.get('href'):
   href = attrs['href']; url = urlparse(href)
   if url.scheme:
    assert url.scheme == 'https', (self.path, href)
    if self.row is not None and attrs.get('class') == 'source':
     assert url.hostname and (url.hostname.endswith('.gov.cn') or url.hostname.endswith('.gov') or url.hostname.endswith('.irs.gov') or url.hostname.endswith('.boc.cn') or url.hostname == 'wise.com' or url.hostname.endswith('.wise.com')), href
     self.row['source'] = True
   elif not href.startswith('#'):
    assert (self.path.parent / url.path).resolve().is_file(), (self.path, href)
 def handle_endtag(self, tag):
  if tag == 'tr' and self.row is not None:
   if self.row['td']:
    assert self.row['source'], f'missing official source in {self.path}'
    self.rows += 1
   self.row = None
before = {p: p.read_bytes() for p in pages}
subprocess.run(['python3', str(root / 'assets/build.py')], check=True)
assert all(p.read_bytes() == before[p] for p in pages), 'generated pages out of date'
rows = 0
for path in pages:
 c=Checker(path); c.feed(path.read_text()); rows += c.rows
estimate_html = (root / 'pages/estimates.html').read_text()
targets = [int(value.replace(',', '')) for value in re.findall(r'<th scope="row">\$([\d,]+)</th>', estimate_html)]
assert targets == list(range(10_000, 400_001, 10_000)), 'scenario table must cover USD 10,000–400,000 by 10,000'
assert '2026/11/09' in estimate_html and 'later-dated' in estimate_html, 'rate-date mismatch must remain visible'
print(f'OK: {len(pages)} pages, {rows} cited rows, 40 amount scenarios, local links and deterministic build')
