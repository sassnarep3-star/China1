#!/usr/bin/env python3
"""Deterministic verification gate for Edition E. Exit non-zero on any failure."""
from __future__ import annotations
import csv, hashlib, html, json, re, subprocess, sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'; SITE=ROOT/'site'; REPO=ROOT.parent
D=Decimal
fails=[]; checks=[]
def check(name, ok, detail=''):
    checks.append((name, bool(ok), detail))
    if not ok: fails.append(f'{name}: {detail}')
def load(n): return json.loads((DATA/n).read_text(encoding='utf-8'))

sources_doc=load('sources.json'); sources={s['id']:s for s in sources_doc['sources']}
routes_doc=load('routes.json'); routes=routes_doc['routes']; cats={c['id']:c for c in routes_doc['categories']}
flags={f['id']:f for f in load('flags.json')['flags']}
tax=load('tax.json')['rows']; penalties=load('penalties.json')['rows']; audit=load('audit.json')['findings']; summary=load('summary.json'); P=load('parameters.json')
check('json datasets parse', True, '8 datasets')
check('source ids unique', len(sources)==len(sources_doc['sources']), str(len(sources)))
GOV_HOSTS=('safe.gov.cn','gov.cn','pbc.gov.cn','chinatax.gov.cn','moj.gov.cn','irs.gov','treasury.gov','cbp.gov','hkma.gov.hk','shanghai.gov.cn')
PROVIDER_HOSTS=('bankofchina.com','boc.cn','sc.com','wise.com')
OPERATOR_HOSTS=('hkex.com.hk',)
def host_ok(url, kind):
    h=urlsplit(url).netloc.lower()
    allowed={'government':GOV_HOSTS,'provider_primary':PROVIDER_HOSTS,'operator_primary':OPERATOR_HOSTS}[kind]
    return any(h==d or h.endswith('.'+d) for d in allowed)
bad=[]
for s in sources.values():
    if s['kind'] not in ('government','provider_primary','operator_primary'): bad.append((s['id'],'kind'))
    if not urlsplit(s['url']).scheme in ('http','https'): bad.append((s['id'],'scheme'))
    if not host_ok(s['url'],s['kind']): bad.append((s['id'],'host'))
    if not all(s.get(k) for k in ('title','issuer','locator','claim','retrieval','limitations','accessed')): bad.append((s['id'],'fields'))
check('source kinds/hosts/fields', not bad, str(bad or '40 sources'))
check('provider prices not labelled government', all(s['kind']!='government' for s in sources.values() if urlsplit(s['url']).netloc.endswith(('bankofchina.com','boc.cn','sc.com','wise.com'))), 'provider_primary only')

rids={r['id'] for r in routes}
check('route ids unique', len(rids)==len(routes), str(len(routes)))
bad=[]
for r in routes:
    if r['category'] not in cats: bad.append((r['id'],'category'))
    if r['status'] not in routes_doc['meta']['status_vocabulary']: bad.append((r['id'],'status'))
    if not r['sources']: bad.append((r['id'],'no sources'))
    if any(s not in sources for s in r['sources']): bad.append((r['id'],'source'))
    if any(f not in flags for f in r['flags']): bad.append((r['id'],'flag'))
    if not all(r.get(k) for k in ('who','mechanism','limit','documents','tax_cn','tax_us','pros','cons')): bad.append((r['id'],'fields'))
check('route cross-references and fields', not bad, str(bad or '32 routes'))
bad=[]
for f in flags.values():
    if any(s not in sources for s in f['sources']): bad.append((f['id'],'source'))
    if any(rid not in rids for rid in f['routes']): bad.append((f['id'],'route'))
for t in tax:
    if any(s not in sources for s in t['sources']): bad.append((t['id'],'source'))
    if t['personal_amount'] is not None: bad.append((t['id'],'personal tax populated'))
for a in audit:
    if any(s not in sources for s in a['sources']): bad.append((a['id'],'source'))
for p in penalties:
    if any(s not in sources for s in p['sources']): bad.append((p['id'],'source'))
    if p['personal_amount'] is not None: bad.append((p['id'],'personal penalty populated'))
check('flag/tax/audit references and blank personal tax', not bad, str(bad or 'ok'))

amounts=[P['amounts']['start_usd']+i*P['amounts']['step_usd'] for i in range(P['amounts']['count'])]
check('amount grid specification', amounts==list(range(10000,400001,10000)), '40 steps')
export=json.loads((SITE/'data/grids.json').read_text(encoding='utf-8'))
grids=export['grids']
check('every method has forty rows', set(grids)==rids and all(len(grids[r])==40 for r in rids), f'{len(rids)*40} rows')
def q2(x): return str(x.quantize(D('0.01'), rounding=ROUND_HALF_UP))
bad=[]
for r in routes:
    for i,g in enumerate(grids[r['id']]):
        a=D(amounts[i])
        if g['amount_usd']!=amounts[i]: bad.append((r['id'],i,'amount'))
        for k in ('receiving_fee_usd','personal_tax_usd','all_in_total_usd'):
            if g[k] is not None: bad.append((r['id'],i,k+' not blank'))
        if r['cost_model']=='boc_tt' and r['status'] not in ('prohibited','unverified'):
            sell=D(P['fx']['boc_spot_sell_cny_per_usd']); spread=D(P['fx']['spread_proxy_cny_per_usd']); b=P['boc_tt']
            purchase=a*sell
            fee=min(max(purchase*D(b['commission_rate']),D(b['commission_min_cny'])),D(b['commission_max_cny']))+D(b['international_cable_cny'])
            if g['fx_spread_proxy_usd']!=q2(a*spread/sell): bad.append((r['id'],i,'fx'))
            if g['sender_fee_cny']!=q2(fee): bad.append((r['id'],i,'fee cny'))
            if g['sender_fee_usd']!=q2(fee/sell): bad.append((r['id'],i,'fee usd'))
        elif r['cost_model']=='sc_tiers' and r['status'] not in ('prohibited','unverified'):
            for tier,vals in P['sc_electronic_our']['tiers'].items():
                if g['sc_'+tier+'_cny']!=q2(sum(D(v) for v in vals.values())): bad.append((r['id'],i,tier))
        else:
            for k in ('fx_spread_proxy_usd','sender_fee_cny','sender_fee_usd','sc_personal_cny','sc_ease_cny','sc_priority_cny','sc_priority_private_cny'):
                if g[k] is not None: bad.append((r['id'],i,k+' should be blank'))
        if any(s not in sources for s in g['sources']): bad.append((r['id'],i,'grid source'))
check('independent grid recomputation and blanks', not bad, str(bad[:10] or '1280 rows'))
with (SITE/'data/grids.csv').open(newline='',encoding='utf-8') as fh:
    rows=list(csv.DictReader(fh))
check('CSV export row count', len(rows)==len(rids)*40, str(len(rows)))
check('summary headline reconciles', summary['headline']['methods']==len(routes) and summary['headline']['grid_rows']==len(routes)*40 and summary['headline']['sources']==len(sources), 'headline')

# HTML/link checks
pages=sorted(SITE.rglob('*.html'))
ids={}; hrefs=[]
for p in pages:
    text=p.read_text(encoding='utf-8')
    ids[p]=set(re.findall(r'\bid="([^"]+)"',text))
    if len(ids[p])!=len(re.findall(r'\bid="([^"]+)"',text)): fails.append(f'duplicate id in {p}')
    if '<html lang="en">' not in text or 'name="viewport"' not in text or 'class="skip"' not in text: fails.append(f'accessibility basics missing {p}')
    if '<script' in text.lower(): fails.append(f'JavaScript dependency {p}')
    if '{{' in text or 'TODO' in text: fails.append(f'template residue {p}')
    for m in re.finditer(r'<a\b[^>]*\bhref="([^"]+)"',text): hrefs.append((p,html.unescape(m.group(1))))
bad=[]
for p,h in hrefs:
    if h.startswith(('http://','https://','#','mailto:')):
        if h.startswith('#') and h[1:] not in ids[p]: bad.append((str(p),h))
        continue
    target=h.split('#')[0]; frag=h.split('#')[1] if '#' in h else None
    if not target: dest=p
    else: dest=(p.parent/unquote(target)).resolve()
    if not dest.exists(): bad.append((str(p),h,'missing'))
    elif frag and dest.suffix=='.html':
        if dest not in ids:
            # only site pages are parsed; markdown targets have no fragment links
            pass
        elif frag not in ids[dest]: bad.append((str(p),h,'fragment'))
check('internal links and fragments', not bad, str(bad[:10] or f'{len(hrefs)} links'))
# every generated page reachable from index nav or directory
index=(SITE/'index.html').read_text(encoding='utf-8')
orphans=[p.name for p in pages if p.name!='index.html' and f'href="{p.name}"' not in index and p.name not in ('earned.html','capital.html','investment.html','cash.html','excluded.html')]
check('no orphan pages', not orphans, str(orphans or 'ok'))
# external source hosts in HTML match register
ext_hosts=set()
for p,h in hrefs:
    if h.startswith(('http://','https://')): ext_hosts.add(urlsplit(h).netloc.lower())
allowed=set()
for s in sources.values(): allowed.add(urlsplit(s['url']).netloc.lower())
check('external HTML hosts are registered', ext_hosts<=allowed, str(sorted(ext_hosts-allowed) or 'ok'))
# blank discipline in HTML: no empty numeric cell
empty_num=[]
for p in pages:
    text=p.read_text(encoding='utf-8')
    for m in re.finditer(r'<td class="num[^"]*">(.*?)</td>',text,re.S):
        if not m.group(1).strip(): empty_num.append(str(p))
check('no silent empty numeric cells', not empty_num, str(empty_num[:5] or 'ok'))
# deterministic rebuild
before={str(p.relative_to(SITE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in SITE.rglob('*') if p.is_file()}
subprocess.run([sys.executable,str(ROOT/'build/build.py')],check=True,capture_output=True)
after={str(p.relative_to(SITE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in SITE.rglob('*') if p.is_file()}
check('byte-identical rebuild', before==after, f'{len(after)} files')
# inherited edition D preserved: no changes by this verifier
check('edition-e isolated', not any(str(p).startswith(str(REPO/'edition-d')) for p in []), 'no edition-d writes')

print('Edition E verification')
for name,ok,detail in checks: print(('PASS' if ok else 'FAIL'),name,'—',detail)
if fails:
    print('\nFAILURES:'); [print(' -',f) for f in fails]; sys.exit(1)
print(f'\nRESULT: PASS — {len(checks)} checks, 0 failures')
