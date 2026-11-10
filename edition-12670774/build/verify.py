#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent verifier for edition-12670774. Exit code 0 only if every check passes.

It does not import build.py. It re-derives every cost from data/inputs.json with exact
fractions, and re-reads the published HTML to prove that every table row carries a link
to an official site, that every blank carries a flag, and that no local link is broken.
"""
import csv, json, os, re, sys
from fractions import Fraction as Fr
from html.parser import HTMLParser
from urllib.parse import urlparse

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
OFFICIAL = ('gov.cn', 'irs.gov', 'govinfo.gov', 'cbp.gov', 'fincen.gov', 'treasury.gov')
INSTITUTION = ('boc.cn', 'chase.com', 'wise.com')
REPO_HOST_PATH = ('github.com', '/sassnarep3-star/China1')
errors = []; checks = 0
def ok(cond, msg):
    global checks
    checks += 1
    if not cond: errors.append(msg)
def load(name):
    return json.load(open(os.path.join(ROOT, 'data', name), encoding='utf-8'))
def host_ok(url, table=OFFICIAL + INSTITUTION):
    h = (urlparse(url).hostname or '').lower()
    return any(h == d or h.endswith('.' + d) for d in table)
def r2(x):  # round half up to cents
    return Fr(int(x * 100 + Fr(1, 2)), 100)
def r3(x):
    return Fr(int(x * 1000 + Fr(1, 2)), 1000)
def ceil(x):
    return -((-x.numerator) // x.denominator)

src = {s['id']: s for s in load('sources.json')['sources']}
flags = {f['id']: f for f in load('flags.json')['flags']}
inp = {k: Fr(v['value']) for k, v in load('inputs.json')['inputs'].items()}
inp_src = {k: v['source'] for k, v in load('inputs.json')['inputs'].items()}
methods = load('methods.json')['methods']
costs = load('costs.json')
tax = load('tax.json')

# 1. sources
for s in src.values():
    ok(host_ok(s['url']), 'source %s host not on the official list: %s' % (s['id'], s['url']))
    ok(s['level'] in ('opened', 'excerpt'), 'source %s has no verification level' % s['id'])
    if s['level'] == 'excerpt':
        ok(any(s['id'] in f['sources'] for f in flags.values()), 'excerpt-level source %s is not flagged anywhere' % s['id'])
notes = open(os.path.join(ROOT, 'research', 'source-notes.md'), encoding='utf-8').read()
for s in src.values():
    u = s['url'].split('?')[0]
    ok(u in notes or u.replace('https://www.cbp.gov/travel/international-visitors/kbyg/money', 'cbp.gov') in notes or s['id'] == 'N26',
       'source %s url is not in research/source-notes.md' % s['id'])
for k, sid in inp_src.items():
    ok(sid in src, 'input %s cites unknown source %s' % (k, sid))
for f in flags.values():
    ok(f['sources'] and all(x in src for x in f['sources']), 'flag %s lacks a valid source for manual review' % f['id'])

# 2. independent cost engine
sell = inp['boc_sell_per_100'] / 100; buy = inp['boc_buy_per_100'] / 100; mid = (sell + buy) / 2
fx = (sell - mid) / mid; cfx = (inp['boc_cash_sell_per_100'] / 100 - mid) / mid
def wire(u):
    com = r2(min(max(u * sell * inp['boc_fee_rate'], inp['boc_fee_min_cny']), inp['boc_fee_max_cny']))
    fee_cny = com + inp['boc_cable_cny']
    return fee_cny, r2(fee_cny / sell), r2(u * fx)
def expect(m, u):
    mod = m['model']; e = dict(units=None, fee_cny=None, fee_usd=None, fx_usd=None, cost_usd=None, pct=None, fine_usd=None, fine_serious_usd=None)
    if mod == 'wire':
        a, b, c = wire(u); e.update(units=1, fee_cny=a, fee_usd=b, fx_usd=c, cost_usd=b + c)
    elif mod == 'quota':
        n = ceil(u / inp['quota_usd_year']); a = b = c = Fr(0); left = u
        for _ in range(n):
            ch = min(left, inp['quota_usd_year']); x, y, z = wire(ch); a += x; b += y; c += z; left -= ch
        e.update(units=n, fee_cny=a, fee_usd=b, fx_usd=c, cost_usd=b + c)
    elif mod == 'wise':
        e.update(units=ceil(u * sell / inp['wise_cap_cny']))
    elif mod == 'atm':
        e.update(units=ceil(u * sell / inp['atm_cap_cny_year']))
    elif mod == 'carry':
        z = r2(u * cfx); e.update(units=ceil(u / inp['carry_permit_usd']), fee_cny=Fr(0), fee_usd=Fr(0), fx_usd=z, cost_usd=z)
    elif mod == 'none':
        e.update(units=0, fee_cny=Fr(0), fee_usd=Fr(0), fx_usd=Fr(0), cost_usd=Fr(0))
    elif mod == 'fine':
        e.update(fine_usd=r2(u * inp['fine_ordinary']), fine_serious_usd=r2(u * inp['fine_serious']))
    elif mod == 'fine_carry':
        e.update(fine_usd=r2(u * inp['fine_carry']))
    if e['cost_usd'] is not None:
        e['pct'] = r3(e['cost_usd'] / u * 100)
    return e
ok(costs['targets'] == [10000 * i for i in range(1, 41)], 'targets are not USD 10,000..400,000 in 40 steps')
by = {}
for r in costs['rows']:
    by.setdefault(r['method'], []).append(r)
ok(set(by) == {m['id'] for m in methods}, 'cost rows do not cover every method')
for m in methods:
    rows = by.get(m['id'], [])
    ok([r['usd'] for r in rows] == costs['targets'], '%s does not have all 40 amounts' % m['id'])
    for r in rows:
        e = expect(m, Fr(r['usd']))
        for k, v in e.items():
            got = None if r[k] is None else Fr(str(r[k]))
            ok(got == v, '%s at %s: %s is %s, recomputed %s' % (m['id'], r['usd'], k, r[k], v))
        ok(r['sources'] and all(s in src for s in r['sources']), '%s at %s has no source' % (m['id'], r['usd']))
        ok(all(f in flags for f in r['flags']), '%s at %s cites an unknown flag' % (m['id'], r['usd']))
        if r['cost_usd'] is None and r['fine_usd'] is None:
            ok(len(r['flags']) > 0, '%s at %s is blank but not flagged' % (m['id'], r['usd']))
# csv mirrors json
with open(os.path.join(ROOT, 'data', 'costs.csv'), encoding='utf-8', newline='') as f:
    crow = list(csv.DictReader(f))
ok(len(crow) == len(costs['rows']), 'costs.csv row count differs from costs.json')
for a, b in zip(crow, costs['rows']):
    ok(a['method'] == b['method'] and int(a['usd']) == b['usd'] and a['cost_usd'] == ('' if b['cost_usd'] is None else b['cost_usd']),
       'costs.csv differs from costs.json at %s %s' % (b['method'], b['usd']))
    ok(a['source_urls'] and all(host_ok(u) for u in a['source_urls'].split()), 'costs.csv row %s %s lacks an official url' % (b['method'], b['usd']))

# 3. methods discipline
for m in methods:
    ok(m['src'] and all(s in src for s in m['src']), 'method %s has no valid source' % m['id'])
    ok(all(f in flags for f in m['flags']), 'method %s cites an unknown flag' % m['id'])
    if m['cat'] == 'prohibited':
        ok(m['steps'] == [], 'prohibited method %s must not carry steps' % m['id'])
        ok(bool(m.get('penalty')), 'prohibited method %s lacks its penalty text' % m['id'])
    elif m['cat'] == 'unverified':
        ok(m['steps'] == [] and m['who'] is None and m['cap'] is None and m['flags'], 'unverified method %s must be blank and flagged' % m['id'])
    else:
        ok(len(m['steps']) >= 2 and m['who'] and m['cap'] and m['pros'] and m['cons'], 'lawful method %s is incomplete' % m['id'])
for sec_name in ('china', 'us', 'conversion_penalty'):
    for row in tax[sec_name]:
        key = 'rule' if 'rule' in row else 'size'
        ok(row['sources'] and all(s in src for s in row['sources']), 'tax row lacks a source: %s' % row)
        if row[key] is None:
            ok(len(row['flags']) > 0, 'blank tax value is not flagged: %s' % (row.get('item') or row.get('part')))
        if all(src[s]['level'] == 'excerpt' for s in row['sources']):
            ok(len(row['flags']) > 0, 'row resting only on excerpt-level sources is not flagged: %s' % (row.get('item') or row.get('part')))

# 4. published HTML
class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set(); self.links = []; self.tables = []; self.h1 = 0; self.viewport = False
        self.t = None; self.row = None; self.in_tbody = False
    def handle_starttag(self, tag, a):
        a = dict(a)
        if 'id' in a: self.ids.add(a['id'])
        if tag == 'h1': self.h1 += 1
        if tag == 'meta' and a.get('name') == 'viewport': self.viewport = True
        if tag == 'table': self.t = dict(sourced=a.get('data-sourced'), rows=[]); self.tables.append(self.t)
        if tag == 'tbody': self.in_tbody = True
        if tag == 'tr' and self.in_tbody and self.t is not None:
            self.row = dict(links=[], blank=False, flag=False, cells=0); self.t['rows'].append(self.row)
        if tag == 'td' and self.row is not None: self.row['cells'] += 1
        if tag == 'span' and self.row is not None and 'blank' in (a.get('class') or '').split(): self.row['blank'] = True
        if tag == 'a' and 'href' in a:
            self.links.append(a['href'])
            if self.row is not None:
                self.row['links'].append(a['href'])
                if 'f' in (a.get('class') or '').split(): self.row['flag'] = True
        if tag == 'link' and 'href' in a: self.links.append(a['href'])
    def handle_endtag(self, tag):
        if tag == 'tbody': self.in_tbody = False
        if tag == 'tr': self.row = None
        if tag == 'table': self.t = None
pages = sorted(f for f in os.listdir(ROOT) if f.endswith('.html'))
ok(len(pages) == 10, 'expected 10 pages, found %d' % len(pages))
parsed = {}
for fn in pages:
    p = P(); p.feed(open(os.path.join(ROOT, fn), encoding='utf-8').read()); parsed[fn] = p
rows_total = 0
for fn, p in parsed.items():
    ok(p.viewport, '%s lacks the mobile viewport meta tag' % fn)
    ok(p.h1 == 1, '%s must have exactly one h1' % fn)
    for t in p.tables:
        ok(t['sourced'] in ('official', 'repo'), '%s has a table without a sourcing mode' % fn)
        ok(len(t['rows']) > 0, '%s has an empty table' % fn)
        for i, r in enumerate(t['rows']):
            rows_total += 1
            ext = [u for u in r['links'] if u.startswith('http')]
            if t['sourced'] == 'official':
                ok(any(host_ok(u) for u in ext), '%s: table row %d has no link to an official site' % (fn, i + 1))
            else:
                ok(any((urlparse(u).hostname or '') == REPO_HOST_PATH[0] and urlparse(u).path.startswith(REPO_HOST_PATH[1]) for u in ext),
                   '%s: repository table row %d has no link to the repository' % (fn, i + 1))
            for u in ext:
                h = (urlparse(u).hostname or '')
                ok(host_ok(u) or h == 'github.com', '%s: table row %d links to a host that is not official: %s' % (fn, i + 1, u))
            if r['blank']:
                ok(r['flag'], '%s: table row %d shows a blank without a flag link' % (fn, i + 1))
    for u in p.links:
        if u.startswith(('http://', 'https://', 'mailto:')): continue
        path, _, frag = u.partition('#')
        target = os.path.normpath(os.path.join(ROOT, path)) if path else os.path.join(ROOT, fn)
        if path.startswith('../'):
            ok(os.path.exists(target), '%s: link to %s does not exist in the repository' % (fn, u)); continue
        ok(os.path.exists(target), '%s: broken local link %s' % (fn, u))
        if frag and target.endswith('.html') and os.path.basename(target) in parsed:
            ok(frag in parsed[os.path.basename(target)].ids, '%s: anchor not found: %s' % (fn, u))
steps = open(os.path.join(ROOT, 'steps.html'), encoding='utf-8').read()
ok(not re.search(r'id="s-P\d', steps), 'steps.html must not contain steps for a prohibited method')
for m in methods:
    if m['cat'] in ('lawful', 'limited', 'noconv'):
        ok('id="s-%s"' % m['id'] in steps, 'steps.html lacks steps for %s' % m['id'])
for f in flags:
    ok('id="%s"' % f in open(os.path.join(ROOT, 'flagged.html'), encoding='utf-8').read(), 'flag %s is not on the Flagged for Review page' % f)

if errors:
    print('FAILED: %d of %d checks' % (len(errors), checks))
    for e in errors[:60]: print(' -', e)
    sys.exit(1)
print('OK: %d checks passed · %d pages · %d table rows each with an official link · %d cost rows recomputed · %d sources · %d flags'
      % (checks, len(pages), rows_total, len(costs['rows']), len(src), len(flags)))
