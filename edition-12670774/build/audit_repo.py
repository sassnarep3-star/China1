#!/usr/bin/env python3
"""Line-by-line scan of every tracked text file outside this edition.

Reads each line once and records: line counts, every URL with its host class, and every
occurrence of a set of figures that this session re-read on the official page itself.
Output: ../data/audit_scan.json. Nothing outside edition-12670774/ is modified.
"""
import json, os, re, subprocess, sys, collections
ROOT = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip()
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'data', 'audit_scan.json')
OWN = 'edition-12670774/'
TEXT_EXT = {'.md', '.html', '.htm', '.json', '.csv', '.py', '.yml', '.yaml', '.js', '.css', '.txt', '.svg', '.xml'}
OFFICIAL = ('gov.cn', 'irs.gov', 'fincen.gov', 'treasury.gov', 'govinfo.gov', 'cbp.gov', 'dhs.gov',
            'federalregister.gov', 'ecfr.gov', 'congress.gov', 'house.gov', 'state.gov', 'ssa.gov', 'supremecourt.gov', 'uscourts.gov',
            'consumerfinance.gov', 'federalreserve.gov', 'fdic.gov', 'sec.gov', 'justice.gov', 'usa.gov',
            'npc.gov.cn', 'court.gov.cn', 'chinamoney.com.cn', 'cfets.com.cn', 'hkma.gov.hk', 'gov.hk', 'oecd.org',
            'imf.org')
INSTITUTION = ('boc.cn', 'bankofchina.com', 'icbc.com.cn', 'icbc-ltd.com', 'ccb.com', 'abchina.com', 'cmbchina.com',
               'bankcomm.com', 'hsbc.com.cn', 'hsbc.com', 'hsbc.com.hk', 'chase.com', 'bankofamerica.com',
               'wellsfargo.com', 'citi.com', 'wise.com', 'unionpayintl.com', 'unionpay.com', 'swift.com',
               'westernunion.com', 'moneygram.com', 'paypal.com', 'alipay.com', 'schwab.com', 'fidelity.com',
               'interactivebrokers.com', 'standardchartered.com.cn', 'bochk.com', 'sc.com', 'dbs.com.cn', 'citibank.com.cn',
               'icbcasia.com', 'skyremit.cn', 'hkex.com.hk')
INFRA = ('github.com', 'github.io', 'githubusercontent.com', 'w3.org', 'schema.org', 'shields.io', 'e2b.app',
         'arena.ai', 'python.org', 'pypi.org', 'npmjs.org', 'jsdelivr.net', 'googleapis.com', 'gstatic.com')
URL_RE = re.compile(r'https?://[^\s"\'<>)\]\\|`,]+')
def host_class(host):
    host = host.lower().split(':')[0]
    for kind, table in (('official', OFFICIAL), ('institution', INSTITUTION), ('infrastructure', INFRA)):
        if any(host == d or host.endswith('.' + d) for d in table):
            return kind
    return 'other'
CHECKS = {
    'boc_usd_quote': re.compile(r'(?<![\d.])6[5-9]\d\.\d{2}(?![\d.])'),
    'cny_per_usd_4dp': re.compile(r'(?<![\d.])6\.[5-9]\d{3}(?![\d])'),
    'form3520_entity_threshold': re.compile(r'20,(?:116|573)'),
    'crypto_notice_2021_237': re.compile(r'(?:2021\]?\s*(?:No\.?\s*)?237(?!\d)|〔2021〕237号|3581332/4348658)'),
    'crypto_notice_2026_42': re.compile(r'(?:2026\]?\s*(?:No\.?\s*)?42(?!\d)|〔2026〕42号|2026020619591971323)'),
}
files = [f for f in subprocess.check_output(['git', 'ls-files'], text=True, cwd=ROOT).splitlines()
         if not f.startswith(OWN)]
per_area = collections.OrderedDict(); per_file = []; hosts = collections.Counter(); host_kind = {}
host_areas = collections.defaultdict(set)
check_hits = {k: collections.defaultdict(lambda: collections.Counter()) for k in CHECKS}
total_lines = 0; binary = 0
for f in files:
    ext = os.path.splitext(f)[1].lower()
    area = f.split('/')[0] if '/' in f else '(root)'
    a = per_area.setdefault(area, {'files': 0, 'text_files': 0, 'lines': 0, 'urls': 0, 'official': 0, 'institution': 0, 'other': 0})
    a['files'] += 1
    if ext not in TEXT_EXT:
        binary += 1; continue
    try:
        lines = open(os.path.join(ROOT, f), encoding='utf-8', errors='replace').read().splitlines()
    except Exception:
        binary += 1; continue
    a['text_files'] += 1; a['lines'] += len(lines); total_lines += len(lines)
    rec = {'file': f, 'lines': len(lines), 'urls': 0, 'official': 0, 'institution': 0, 'other': 0}
    for ln in lines:
        for u in URL_RE.findall(ln):
            h = re.sub(r'^https?://', '', u).split('/')[0]
            if not re.fullmatch(r'[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?::\d+)?', h): continue
            k = host_class(h); hosts[h.lower()] += 1; host_kind[h.lower()] = k
            host_areas[h.lower()].add(area)
            if k == 'infrastructure': continue
            rec['urls'] += 1; a['urls'] += 1
            rec[k] += 1; a[k] += 1
        for name, rx in CHECKS.items():
            for m in rx.findall(ln):
                check_hits[name][m][area] += 1
    per_file.append(rec)
out = {
    'scanned_commit': subprocess.check_output(['git', 'rev-parse', '--short', 'origin/main'], text=True, cwd=ROOT).strip(),
    'files_total': len(files), 'files_text': len(per_file), 'files_binary_or_skipped': binary, 'lines_total': total_lines,
    'areas': per_area,
    'hosts_other': sorted(((h, c, sorted(host_areas[h])) for h, c in hosts.items() if host_kind[h] == 'other'), key=lambda x: (-x[1], x[0])),
    'hosts_official_count': sum(1 for h in hosts if host_kind[h] == 'official'),
    'hosts_institution_count': sum(1 for h in hosts if host_kind[h] == 'institution'),
    'checks': {k: {val: dict(areas) for val, areas in sorted(v.items())} for k, v in check_hits.items()},
    'files': per_file,
}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('files', len(files), 'text', len(per_file), 'lines', total_lines)
