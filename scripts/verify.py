import json,pathlib,urllib.parse
from html.parser import HTMLParser
root=pathlib.Path('docs')
allowed={'www.pbc.gov.cn','www.hsbc.com.cn','wise.com','www.irs.gov','www.govinfo.gov','english.customs.gov.cn','www.sz.gov.cn'}
class Check(HTMLParser):
 def __init__(self): super().__init__(); self.inrow=False; self.links=[]; self.rows=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='tr': self.inrow=True; self.links=[]; self.data=False
  if tag=='td': self.data=True
  if tag in ('a','link','script'):
   url=a.get('href',a.get('src',''))
   if url.startswith(('https://','http://')):
    assert urllib.parse.urlparse(url).hostname in allowed,url
    if self.inrow:self.links.append(url)
   elif url and not url.startswith('#'): assert (root/url.split('#')[0]).exists(),url
 def handle_endtag(self,tag):
  if tag=='tr':
   if self.data: assert self.links,'Table row without official link'; self.rows+=1
   self.inrow=False
n=0
for f in root.glob('*.html'):
 c=Check(); c.feed(f.read_text()); n+=c.rows
 assert '<html lang="en">' in f.read_text()
d=json.loads((root/'data.json').read_text())
assert len(d['routes'])==18
assert all(r[2]=='' for r in d['costs'])
assert len(d['sources'])==10
print(f'PASS: {len(list(root.glob("*.html")))} pages, {n} sourced table rows, local links, official hosts, blank unknown costs.')
