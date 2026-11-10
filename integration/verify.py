"""Checks structural consistency, not legal correctness or external availability."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import hashlib
import runpy
ROOT=Path(__file__).resolve().parents[1]
FILES=[ROOT/'index.html',ROOT/'integration/review.html',ROOT/'integration/evidence.html',ROOT/'integration/evidence.json']
class Page(HTMLParser):
 def __init__(self):
  super().__init__();self.links=[];self.rows=[];self.row=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='tr':self.row=[]
  if tag=='a':
   self.links.append(a.get('href',''))
   if self.row is not None:self.row.append(a.get('href',''))
 def handle_endtag(self,tag):
  if tag=='tr':
   self.rows.append(self.row);self.row=None
before=[hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES]
runpy.run_path(str(ROOT/'integration/build.py'))['build']()
assert before==[hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES], 'nondeterministic build'
allowed={'www.safe.gov.cn','www.irs.gov','www.boc.cn','wise.com','shanghai.chinatax.gov.cn'}
rows=0;links=0
for p in FILES[:3]:
 text=p.read_text();doc=Page();doc.feed(text)
 assert 'name="viewport"' in text
 for row in doc.rows:
  if row:assert any(urlsplit(h).netloc in allowed for h in row), (p,row)
  else:continue # header row
  rows+=1
 for href in doc.links:
  u=urlsplit(href);links+=1
  if u.scheme:assert u.scheme=='https' and u.netloc in allowed,href
  else:
   dest=(p.parent/unquote(u.path)).resolve()
   assert dest.is_relative_to(ROOT) and dest.is_file(),(p,href)
 assert '<script' not in text
root=FILES[0].read_text()
for n in range(10000,400001,10000):assert f'<td>${n:,}</td>' in root
assert root.count('aria-label="Unverified tax"')==40
assert root.count('aria-label="Unverified all-in total"')==40
assert root.count('CNY 200–410</td>')==40
assert 'under 1% at every size' not in root
for edition in 'defgh':assert f'edition-{edition}/' in root
assert rows==61,rows # 6 findings, 40 amounts, 9 flags, 6 evidence rows
print(f'PASS: 3 pages; {rows} primary-source-linked rows; {links} links; 40 targets; 80 blank unknown cells; deterministic rebuild. External live links and personal eligibility not certified.')
