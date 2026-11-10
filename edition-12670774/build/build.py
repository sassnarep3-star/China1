#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build edition-12670774: data files and the static site.

Deterministic: no clock, no network. Run:  python3 edition-12670774/build/build.py
Inputs: content.py, methods.py, ../data/audit_scan.json (written by audit_repo.py).
Outputs: ../data/*.json, ../data/costs.csv, ../*.html, ../assets/style.css
"""
import csv, html, json, os, sys
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import content as C
import methods as M

SRC = {s[0]: dict(id=s[0], level=s[1], kind=s[2], title=s[3], url=s[4], read=s[5]) for s in C.SOURCES}
FLAG = {f[0]: dict(id=f[0], group=f[1], what=f[2], why=f[3], sources=f[4]) for f in C.FLAGS}
INP = {k: D(v[0]) for k, v in C.INPUTS.items()}
TARGETS = [10000 * i for i in range(1, 41)]

def q(x, places='0.01'):
    return x.quantize(D(places), rounding=ROUND_HALF_UP)
def ceil_div(a, b):
    return int((a / b).to_integral_value(rounding=ROUND_CEILING))

SELL = INP['boc_sell_per_100'] / 100
BUY = INP['boc_buy_per_100'] / 100
MID = (SELL + BUY) / 2
FX_PCT = (SELL - MID) / MID                      # share of the amount lost to the bank's margin
CASH_FX_PCT = (INP['boc_cash_sell_per_100'] / 100 - MID) / MID

def wire(usd):
    """One Bank of China wire of `usd` dollars bought with RMB. Returns (fee_cny, fee_usd, fx_usd, total_usd)."""
    usd = D(usd)
    commission = q(min(max(usd * SELL * INP['boc_fee_rate'], INP['boc_fee_min_cny']), INP['boc_fee_max_cny']))
    fee_cny = commission + INP['boc_cable_cny']
    fee_usd = q(fee_cny / SELL)
    fx_usd = q(usd * FX_PCT)
    return fee_cny, fee_usd, fx_usd, fee_usd + fx_usd

def cost_row(m, usd):
    r = dict(method=m['id'], usd=usd, units=None, unit=None, fee_cny=None, fee_usd=None, fx_usd=None,
             cost_usd=None, pct=None, fine_usd=None, fine_serious_usd=None, sources=[], flags=[])
    mod = m['model']; U = D(usd)
    if mod == 'wire':
        fc, fu, fx, t = wire(usd)
        r.update(units=1, unit='wire', fee_cny=fc, fee_usd=fu, fx_usd=fx, cost_usd=t, sources=['N02', 'N04'], flags=['F04', 'F05', 'F06'])
    elif mod == 'quota':
        n = ceil_div(U, INP['quota_usd_year']); fc = fu = fx = D(0)
        left = U
        for _ in range(n):
            chunk = min(left, INP['quota_usd_year']); a, b, c, _t = wire(chunk)
            fc += a; fu += b; fx += c; left -= chunk
        r.update(units=n, unit='calendar years, one wire each', fee_cny=fc, fee_usd=fu, fx_usd=fx, cost_usd=fu + fx,
                 sources=['N01', 'N02', 'N04'], flags=['F04', 'F05', 'F06'])
    elif mod == 'wise':
        r.update(units=ceil_div(U * SELL, INP['wise_cap_cny']), unit='transfers', sources=['N21', 'N02'], flags=['F07', 'F34'])
    elif mod == 'atm':
        r.update(units=ceil_div(U * SELL, INP['atm_cap_cny_year']), unit='calendar years', sources=['N16', 'N02'], flags=['F08', 'F34'])
    elif mod == 'carry':
        fx = q(U * CASH_FX_PCT)
        r.update(units=ceil_div(U, INP['carry_permit_usd']), unit='trips with a bank permit', fee_cny=D(0), fee_usd=D(0), fx_usd=fx,
                 cost_usd=fx, sources=['N01', 'N02', 'N24'], flags=['F04', 'F32'])
    elif mod == 'none':
        r.update(units=0, unit='conversions', fee_cny=D(0), fee_usd=D(0), fx_usd=D(0), cost_usd=D(0), sources=['N11'], flags=[])
    elif mod == 'blank':
        r.update(sources=m['src'], flags=m['flags'])
    elif mod == 'fine':
        r.update(fine_usd=q(U * INP['fine_ordinary']), fine_serious_usd=q(U * INP['fine_serious']), sources=['N09'], flags=[])
    elif mod == 'fine_carry':
        r.update(fine_usd=q(U * INP['fine_carry']), sources=['N09', 'N24'], flags=[])
    elif mod == 'noamount':
        r.update(sources=m['src'], flags=m['flags'])
    else:
        raise SystemExit('unknown model ' + mod)
    if r['cost_usd'] is not None:
        r['pct'] = q(r['cost_usd'] / U * 100, '0.001')
    return r

COSTS = {m['id']: [cost_row(m, t) for t in TARGETS] for m in M.METHODS}
def at(mid, usd):
    return COSTS[mid][TARGETS.index(usd)]

# ---------- formatting ----------
E = html.escape
def usd(x, dp=2):
    return '—' if x is None else ('$' + format(x, ',.%df' % dp))
def pct(x, dp=3):
    return '—' if x is None else (format(x, '.%df' % dp) + '%')
def src(ids):
    return ' '.join('<a class="s" href="%s" title="%s" rel="noopener">%s</a>' % (E(SRC[i]['url']), E(SRC[i]['title']), i) for i in ids)
def fl(ids):
    return ' '.join('<a class="f" href="flagged.html#%s" title="%s">%s</a>' % (i, E(FLAG[i]['what']), i) for i in ids)
def blank(ids):
    return '<span class="blank">blank</span> ' + fl(ids)
def table(heads, rows, cls='stack', sourced='official', ident=None):
    h = ''.join('<th scope="col">%s</th>' % E(x) for x in heads)
    b = ''
    for row in rows:
        rid = ''
        if isinstance(row, tuple):
            rid, row = ' id="%s"' % row[0], row[1]
        b += '<tr%s>%s</tr>' % (rid, ''.join('<td data-label="%s">%s</td>' % (E(heads[i]), c) for i, c in enumerate(row)))
    return '<div class="tw"><table class="%s" data-sourced="%s"%s><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (
        cls, sourced, (' id="%s"' % ident) if ident else '', h, b)
def badge(cat):
    label, tone = M.CATS[cat]
    return '<span class="b %s">%s</span>' % (tone, E(label))

NAV = [('index.html', 'Overview'), ('summary.html', 'Summary'), ('methods.html', 'Methods'), ('steps.html', 'Steps'),
       ('costs.html', 'Costs'), ('tax.html', 'Tax and penalties'), ('flagged.html', 'Flagged for Review'),
       ('audit.html', 'Repo audit'), ('sources.html', 'Sources'), ('evidence.html', 'Evidence')]
def page(fn, title, lead, body):
    nav = ''.join('<a href="%s"%s>%s</a>' % (f, ' aria-current="page"' if f == fn else '', E(t)) for f, t in NAV)
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>%s — China money, edition 12670774</title>'
            '<meta name="description" content="%s"><link rel="stylesheet" href="assets/style.css"></head><body>'
            '<header><div class="wrap"><a class="brand" href="index.html">China money <span>edition 12670774</span></a>'
            '<nav aria-label="Sections">%s</nav></div></header>'
            '<main class="wrap"><h1>%s</h1><p class="lead">%s</p>%s</main>'
            '<footer><div class="wrap"><p>Rates and rules as read on official pages on %s. Figures are estimates built from published inputs; '
            'the bank\'s actual rate and fees govern. This is not legal or tax advice. '
            '<a href="sources.html">Sources</a> · <a href="flagged.html">Flagged for Review</a> · '
            '<a href="../index.html">Repository portal</a></p></div></footer></body></html>\n') % (
            E(title), E(lead), nav, E(title), lead, body, C.AS_OF)

c10, c100, c400 = at('M01', 10000), at('M01', 100000), at('M01', 400000)
split400 = at('M05', 400000)
FMT = dict(c10=usd(c10['cost_usd']), p10=pct(c10['pct']), c100=usd(c100['cost_usd']), p100=pct(c100['pct']),
           c400=usd(c400['cost_usd']), p400=pct(c400['pct']), fx=pct(q(FX_PCT * 100, '0.0001'), 4), split=usd(split400['cost_usd']))
MBY = {m['id']: m for m in M.METHODS}
LAWFUL = [m for m in M.METHODS if m['cat'] in ('lawful', 'limited', 'noconv')]
PROHIB = [m for m in M.METHODS if m['cat'] == 'prohibited']
def mlink(mid):
    return '<a href="methods.html#%s">%s</a>' % (mid, E(MBY[mid]['name']))

# ---------- pages ----------
def p_index():
    kp = ('<div class="kpis">'
          '<div class="k"><span>Tax on converting or wiring</span><b>None found</b><i>China and US sources opened %s</i></div>'
          '<div class="k"><span>One documented wire, USD 10,000</span><b>%s</b><i>%s of the amount %s</i></div>'
          '<div class="k"><span>One documented wire, USD 400,000</span><b>%s</b><i>%s of the amount %s</i></div>'
          '<div class="k"><span>Yearly cap, documented income</span><b>None in the text</b><i>foreign passport holders %s</i></div>'
          '</div>') % (fl(['F19']), FMT['c10'], FMT['p10'], src(['N02', 'N04']), FMT['c400'], FMT['p400'], src(['N02', 'N04']), src(['N01']))
    rows = []
    for sit, mid, cap, doc, s in M.ROUTES:
        rows.append([E(sit), mlink(mid) if mid else '<span class="blank">no route verified</span> ' + fl(['F01']),
                     E(cap) if cap else blank(['F01']), E(doc), src(s)])
    glance = []
    for t in (10000, 50000, 100000, 200000, 300000, 400000):
        a, b = at('M01', t), at('M05', t)
        glance.append(['<b>%s</b>' % usd(D(t), 0), '<b>%s</b>' % usd(a['cost_usd']), pct(a['pct']),
                       '%s over %d yr' % (usd(b['cost_usd']), b['units']), src(['N02', 'N04', 'N01'])])
    cards = ''.join('<a class="card" href="%s"><b>%s</b><span>%s</span></a>' % x for x in [
        ('summary.html', 'Executive summary', 'Nine findings, each with its official source.'),
        ('methods.html', 'Methods', '%d methods: %d lawful, %d prohibited, 1 not verified. Pros and cons for each.' % (len(M.METHODS), len(LAWFUL), len(PROHIB))),
        ('steps.html', 'Step by step', 'What to bring and what happens, for every lawful method.'),
        ('costs.html', 'Costs', 'Every method at every USD 10,000 step to USD 400,000.'),
        ('tax.html', 'Tax and penalties', 'The conversion penalty taken apart; China and US tax; prohibited channels.'),
        ('flagged.html', 'Flagged for Review', '%d items left blank or uncertain, with where to check.' % len(C.FLAGS)),
        ('audit.html', 'Repo audit', 'Every tracked file scanned line by line; irregularities listed.'),
        ('sources.html', 'Sources', '%d official pages, with what was read on each.' % len(C.SOURCES)),
        ('evidence.html', 'Evidence', 'The passages relied on, quoted as published.')])
    body = (kp + '<h2>Find your route</h2><p>Start with what the money is. The route, the cap and the papers follow from that. '
            'Your own facts were not supplied, so every case is shown.</p>'
            + table(['Your situation', 'Route', 'Cap in the rule', 'Key paper', 'Source'], rows)
            + '<h2>Cost at a glance</h2><p>Bank of China commission and cable fee plus the bank\'s FX margin. '
            'Intermediary and receiving-bank fees are blank and not included %s. The full ladder is on the <a href="costs.html">Costs</a> page.</p>' % fl(['F05', 'F06'])
            + table(['Amount', 'One documented wire', 'Share', 'USD 50,000 a year instead', 'Source'], glance, cls='tight')
            + '<h2>Sections</h2><div class="cards">' + cards + '</div>'
            + '<p class="note"><b>Never use</b> underground banks, borrowed quotas, false documents or virtual currency. '
            'The fines run to 30%% of the amount and to the whole amount in serious cases %s. See <a href="tax.html#prohibited">prohibited channels</a>.</p>' % src(['N09']))
    return page('index.html', 'Getting RMB out of China as a US citizen',
                'No official source read taxes the conversion or the wire itself. The bank wants proof that the income behind the money was taxed, and your papers decide which route is open.', body)

def p_summary():
    rows = [['<b>%s</b>' % E(a), E(b.format(**FMT)), src(s), fl(f) if f else 'none'] for a, b, s, f in M.SUMMARY]
    req = ''.join('<li><a href="%s">%s</a> — %s</li>' % (b, E(a), E(c)) for a, b, c in M.REQUIREMENTS)
    body = (table(['Finding', 'Detail', 'Source', 'Flag'], rows)
            + '<h2>What would change the answer</h2><ul>'
            '<li>What the money is: salary, home sale, inheritance, gift or investment %s.</li>'
            '<li>Whether you were once a Chinese national or hold a Chinese ID %s.</li>'
            '<li>Whether China tax on the income was paid and you hold the vouchers %s.</li>'
            '<li>Which bank holds the money and which US bank receives it %s.</li></ul>'
            % (fl(['F01']), fl(['F02']), src(['N14']), fl(['F03', 'F06']))
            + '<h2>Requirements covered</h2><ul class="req">' + req + '</ul>')
    return page('summary.html', 'Executive summary', 'The important findings first. Each row links to the official page it rests on.', body)

def cost_cell(mid, t):
    r = at(mid, t)
    if r['cost_usd'] is not None: return usd(r['cost_usd'])
    if r['fine_usd'] is not None: return 'fine up to ' + usd(r['fine_usd'], 0)
    return blank(r['flags'][:1] or ['F01'])
def p_methods():
    rows = []
    for m in M.METHODS:
        rows.append((m['id'] + '-row', ['<a href="#%s"><b>%s</b></a>' % (m['id'], E(m['name'])), badge(m['cat']),
                     E(m['who']) if m['who'] else blank(m['flags']), E(m['cap']) if m['cap'] else (E(m['penalty']) if m.get('penalty') else blank(m['flags'])),
                     cost_cell(m['id'], 10000), cost_cell(m['id'], 400000), src(m['src'])]))
    det = ''
    for m in M.METHODS:
        det += '<section class="m" id="%s"><h3>%s %s</h3>' % (m['id'], E(m['name']), badge(m['cat']))
        if m['cat'] == 'prohibited':
            det += '<p><b>Penalty.</b> %s %s</p><p>No steps are published for prohibited channels.</p>' % (E(m['penalty']), src(m['src']))
        elif m['cat'] == 'unverified':
            det += '<p>No official rule for this method was opened in this session, so who qualifies, the cap, the cost and the steps are all blank %s. Official starting point: %s</p>' % (fl(m['flags']), src(m['src']))
        else:
            det += ('<dl><dt>Who it fits</dt><dd>%s</dd><dt>Cap</dt><dd>%s</dd><dt>Papers</dt><dd>%s</dd>'
                    '<dt>For</dt><dd>%s</dd><dt>Against</dt><dd>%s</dd><dt>Sources</dt><dd>%s</dd>%s</dl>'
                    '<p><a href="steps.html#s-%s">Steps</a> · <a href="costs.html">Costs</a></p>') % (
                    E(m['who']), E(m['cap']), E(m['docs']), E(m['pros']), E(m['cons']), src(m['src']),
                    ('<dt>Flags</dt><dd>%s</dd>' % fl(m['flags'])) if m['flags'] else '', m['id'])
        det += '</section>'
    body = (table(['Method', 'Verdict', 'Who it fits', 'Cap or penalty', 'Cost at $10,000', 'Cost at $400,000', 'Source'], rows)
            + '<p class="note">Cost is the sourced part only: Bank of China charges and FX margin. Intermediary and receiving-bank fees are blank %s.</p>' % fl(['F05', 'F06'])
            + '<h2>Each method</h2>' + det)
    return page('methods.html', 'Methods', '%d ways to turn RMB into US dollars: %d lawful, %d prohibited, 1 not verified. Verdict first.'
                % (len(M.METHODS), len(LAWFUL), len(PROHIB)), body)

def p_steps():
    out = ''
    for m in LAWFUL:
        out += ('<section class="m" id="s-%s"><h2>%s %s</h2><p><b>Bring:</b> %s</p><ol>%s</ol><p>Sources: %s%s</p></section>') % (
            m['id'], E(m['name']), badge(m['cat']), E(m['docs']), ''.join('<li>%s</li>' % E(s) for s in m['steps']), src(m['src']),
            (' · Flags: ' + fl(m['flags'])) if m['flags'] else '')
    rows = [[('<b>%s</b>' % E(m['name'])), E(m['penalty']), src(m['src'])] for m in PROHIB]
    out += ('<h2 id="none">Prohibited channels: no steps</h2><p>These are listed so you can recognise and refuse them. How to carry them out is not described.</p>'
            + table(['Channel', 'What the rule says happens', 'Source'], rows))
    return page('steps.html', 'Step by step', 'What to bring and what happens at each stage, for every lawful method. Steps follow the papers the official text asks for.', out)

def p_costs():
    A = lambda t: '<b>%s</b>' % usd(D(t), 0)
    inp = [[E(v[2]), '<b>%s</b>' % E(v[0]), src([v[1]])] for k, v in C.INPUTS.items()]
    inp += [['Mid-point of BOC buy and sell, CNY per USD (computed)', '<b>%s</b>' % format(MID, '.4f'), src(['N02'])],
            ['FX margin: (sell − mid) ÷ mid (computed)', '<b>%s</b>' % FMT['fx'], src(['N02'])]]
    one = [[A(t), '<b>%s</b>' % usd(r['cost_usd']), pct(r['pct']), usd(r['fee_usd']), usd(r['fx_usd']), src(r['sources'])] for t, r in zip(TARGETS, COSTS['M01'])]
    quo = [[A(t), '<b>%s</b>' % usd(r['cost_usd']), pct(r['pct']), str(r['units']), usd(r['fee_usd']), src(r['sources'])] for t, r in zip(TARGETS, COSTS['M05'])]
    car = [[A(t), '<b>%s</b>' % usd(r['cost_usd']), pct(r['pct']), str(r['units']), src(r['sources'])] for t, r in zip(TARGETS, COSTS['M10'])]
    wis = [[A(t), blank(['F07']), str(r['units']), src(r['sources'])] for t, r in zip(TARGETS, COSTS['M08'])]
    atm = [[A(t), blank(['F08']), str(r['units']), src(r['sources'])] for t, r in zip(TARGETS, COSTS['M09'])]
    non = [[A(t), '<b>%s</b>' % usd(r['cost_usd']), src(r['sources'])] for t, r in zip(TARGETS, COSTS['M11'])]
    blk = [[A(t), blank(['F08']), blank(['F10']), src(['N16', 'N18'])] for t in TARGETS]
    fin = [[A(t), '<b>%s</b>' % usd(a['fine_usd'], 0), usd(a['fine_serious_usd'], 0), usd(b['fine_usd'], 0), blank(['F25', 'F26']), src(['N09'])]
           for t, a, b in zip(TARGETS, COSTS['P02'], COSTS['P05'])]
    names = lambda ids: ', '.join(mlink(i) for i in ids)
    sec = lambda sid, title, intro, tbl, op='': '<details id="%s"%s><summary>%s</summary><p>%s</p>%s</details>' % (sid, op, title, intro, tbl)
    body = ('<p>Each figure is arithmetic on inputs read from an official page. A part with no official input is left blank and flagged; it is never guessed. '
            'So every total is a floor: add your own bank\'s incoming-wire fee and anything an intermediary bank deducts %s.</p>' % fl(['F05', 'F06'])
            + '<h2>How the number is built</h2><p class="formula">cost = (commission + cable fee) ÷ selling rate + amount × FX margin<br>'
            'commission = 0.1% of the RMB amount, not less than CNY 50, not more than CNY 260</p>'
            + table(['Input', 'Value', 'Source'], inp)
            + '<h2>Every method, USD 10,000 to USD 400,000</h2>'
            + sec('c-wire', 'One documented wire', 'Applies to %s. Stop at your own cap. Columns: total, share of the amount, bank charges, FX margin.' % names(['M01', 'M02', 'M03', 'M04', 'M06', 'M07']),
                  table(['Amount', 'Sourced cost', 'Share', 'Bank charges', 'FX margin', 'Source'], one, cls='tight'), ' open')
            + sec('c-quota', 'USD 50,000 yearly quota', 'Applies to %s. One wire per calendar year, so large sums take years and each wire pays its own charges.' % names(['M05']),
                  table(['Amount', 'Sourced cost', 'Share', 'Years', 'Bank charges', 'Source'], quo, cls='tight'))
            + sec('c-carry', 'Carrying dollar banknotes', 'Applies to %s. The FX margin when the cash is bought; no wire. Trips are counted at USD 10,000 each, which needs a bank permit. Travel and any cash-handling fee are blank %s.' % (names(['M10']), fl(['F32'])),
                  table(['Amount', 'Sourced cost', 'Share', 'Trips', 'Source'], car, cls='tight'))
            + sec('c-wise', 'Wise, sending from CNY', 'Applies to %s. The fee is not published in the guide, so the cost is blank. Transfers needed at CNY 300,000 each %s.' % (names(['M08']), fl(['F34'])),
                  table(['Amount', 'Cost', 'Transfers', 'Source'], wis, cls='tight'))
            + sec('c-atm', 'ATM cash abroad', 'Applies to %s. Fees are blank. Calendar years needed under the CNY 100,000 yearly cap %s.' % (names(['M09']), fl(['F34'])),
                  table(['Amount', 'Cost', 'Years', 'Source'], atm, cls='tight'))
            + sec('c-none', 'No conversion', 'Applies to %s. Nothing is converted, so there is no conversion cost. US account reporting continues.' % names(['M11']),
                  table(['Amount', 'Conversion cost', 'Source'], non, cls='tight'))
            + sec('c-blank', 'Not priced', 'Applies to %s and %s. No official fee or rule was opened, so every step is blank.' % (names(['M12']), names(['M13'])),
                  table(['Amount', 'Card spending abroad', 'RMB sent abroad', 'Source'], blk, cls='tight'))
            + sec('c-fine', 'Prohibited channels: what the fine can reach', 'Not a cost of doing it: the upper limit of the fine the Regulations set. 30%% and 100%% apply to %s; 20%% applies to %s. No percentage is set in the texts opened for %s.' % (names(['P02', 'P03', 'P06']), names(['P05']), names(['P01', 'P04'])),
                  table(['Amount', 'Fine up to 30%', 'Serious case, up to 100%', 'Undeclared cash, up to 20%', 'Splitting; virtual currency', 'Source'], fin, cls='tight'))
            + '<p>Data: <a href="data/costs.csv">costs.csv</a> · <a href="data/costs.json">costs.json</a> (all %d methods × 40 amounts).</p>' % len(M.METHODS))
    return page('costs.html', 'Costs', 'What each method costs at every USD 10,000 step up to USD 400,000. Total first, then its parts.', body)

def p_tax():
    parts = []
    for name, val, note, s, f in M.PENALTY_PARTS:
        v = FMT['fx'] + ' of the amount' if val == 'fx_pct' else val
        parts.append(['<b>%s</b>' % E(name), ('<b>%s</b>' % E(v)) if v else blank(f), E(note) if note else '', src(s), fl(f) if f else 'none'])
    ex = at('M01', 100000)
    tx = lambda T: [['<b>%s</b>' % E(a), ('<b>%s</b>' % E(b)) if b else blank(f), E(c) if c else '', src(s), fl(f) if f else 'none'] for a, b, c, s, f in T]
    pro = [(m['id'] + '-p', ['<b>%s</b>' % E(m['name']), E(m['penalty']), src(m['src']), fl(m['flags']) if m['flags'] else 'none']) for m in PROHIB]
    body = ('<h2 id="penalty">The conversion penalty, taken apart</h2><p>What you lose between RMB in a China account and dollars in a US account. '
            'Most of it is the bank\'s exchange margin, not tax.</p>'
            + table(['Part', 'Size', 'Note', 'Source', 'Flag'], parts)
            + '<p class="formula">Worked example, USD 100,000 in one Bank of China wire: charges %s + FX margin %s = <b>%s</b>, which is %s of the amount %s.</p>'
            % (usd(ex['fee_usd']), usd(ex['fx_usd']), usd(ex['cost_usd']), pct(ex['pct']), src(['N02', 'N04']))
            + '<h2 id="china">China tax</h2><p>Tax attaches to the income behind the money. If it was withheld when you earned it, the vouchers are your proof.</p>'
            + table(['Item', 'Rate or rule', 'Detail', 'Source', 'Flag'], tx(M.CHINA_TAX))
            + '<h2 id="us">US tax and reporting</h2><p>The forms cost nothing to file. Missing them is where the exposure lies.</p>'
            + table(['Item', 'Rule', 'Detail', 'Source', 'Flag'], tx(M.US_TAX))
            + '<h2 id="prohibited">Prohibited channels and their penalties</h2><p>Listed so they can be recognised and refused. No instructions are given.</p>'
            + table(['Channel', 'What the rule says happens', 'Source', 'Flag'], pro))
    return page('tax.html', 'Tax and penalties', 'The conversion penalty in its parts, then China tax, US tax and reporting, and the penalties for prohibited channels.', body)

def p_flagged():
    rows = [(f[0], ['<b>%s</b>' % f[0], E(f[1]), E(f[2]), E(f[3]), src(f[4])]) for f in C.FLAGS]
    body = ('<p>Everything here is published as it stands and blocks nothing. A blank means no official source opened in this session gave the value; '
            'it was not filled in from memory or from an earlier edition.</p>'
            + table(['ID', 'Group', 'Blank or uncertain', 'Why', 'Check here'], rows))
    return page('flagged.html', 'Flagged for Review', '%d items that are blank, uncertain or irregular, each with the official page to check.' % len(C.FLAGS), body)

def audit_data():
    sc = json.load(open(os.path.join(ROOT, 'data', 'audit_scan.json'), encoding='utf-8'))
    ar = lambda k: sorted({a for v in sc['checks'][k].values() for a in v})
    stale = [a for a in ar('crypto_notice_2021_237') if a not in ar('crypto_notice_2026_42')]
    q_ = sc['checks']['boc_usd_quote']
    where = lambda v: ', '.join(sorted(q_.get(v, {}))) or 'nowhere'
    gh = lambda p: '<a class="s" href="%s/blob/main/%s" rel="noopener">%s</a>' % (C.REPO, p, E(p))
    F = [
     ('A01', 'needs review', 'Edition L stores the central parity as 6.6717 CNY per USD. Its own source value is 671.67 per USD 100, which is 6.7167. edition-l/build/build.py line 35 reads the field.',
      gh('edition-l/data/model.json') + ' ' + gh('edition-l/data/costs.json'), ['N02'], ['F27']),
     ('A02', 'needs review', 'These areas cite Yinfa [2021] No. 237 as the virtual-currency rule and never mention Yinfa [2026] No. 42, which repealed it on 2026-02-06: %s. The prohibition continues, so the conclusion stands.' % ', '.join(stale),
      ' '.join(gh(a) for a in stale if a != '(root)'), ['N19'], ['F28']),
     ('A03', 'needs review', 'Several Bank of China snapshots coexist. Sell 669.03 is used in: %s. Sell 669.29 in: %s. Sell 668.51, the board at 17:39:58 on 2026-11-10, in: %s. Totals across editions are therefore not comparable.' % (where('669.03'), where('669.29'), where('668.51')),
      gh('EXECUTIVE_SUMMARY.md') + ' ' + gh('integration/costs.json'), ['N02'], ['F29']),
     ('A04', 'needs review', 'Links to hosts that are neither government nor the institution concerned: %s.' % ', '.join('%s (%d)' % (h, n) for h, n in sc['hosts_other']),
      gh('edition-b') + ' ' + gh('edition-f') + ' ' + gh('edition-g'), ['N13'], ['F30']),
     ('A05', 'needs review', 'Pull requests #39, #45 and #51 are open; claims by arena-fc438b1a, arena-4207cf2f and arena-8a02a5b6 had no commits for more than 60 minutes when this session started. Not touched.',
      '<a class="s" href="%s/pulls" rel="noopener">open pull requests</a> %s' % (C.REPO, gh('COORDINATION.md')), ['N01'], ['F31']),
     ('A06', 'needs review', 'Official texts disagree on who is a 境内个人: the 2008 Regulations Art. 52 against the 2006 Measures Art. 37. Earlier editions use the Measures\' reading without noting the conflict.',
      'Official texts, not a repository file. Affects every edition that states the quota rule: ' + gh('EXECUTIVE_SUMMARY.md'), ['N09', 'N18'], ['F11']),
     ('A07', 'needs review', 'The 2006 Measures Art. 22 requires SAFE approval to remit home-sale proceeds; the 2025 operating guidelines describe the bank doing it against documents.',
      'Official texts, not a repository file. Affects every edition that describes the home-sale route: ' + gh('README.md'), ['N18', 'N08'], ['F12']),
     ('A08', 'needs review', 'The official inheritance service guide repeats emigrant wording in its conditions block.', 'Official text, not a repository file. Affects every edition that describes the inheritance route: ' + gh('README.md'), ['N06'], ['F13']),
     ('A09', 'confirmed', 'Bank of China wire charge: 0.1%, minimum CNY 50, maximum CNY 260, plus CNY 150 cable. Re-read today on the bank\'s tariff page; matches the root summary and editions K and L.',
      gh('EXECUTIVE_SUMMARY.md') + ' ' + gh('edition-k/data/model.json'), ['N04'], []),
     ('A10', 'confirmed', 'Form 3520 thresholds: USD 100,000 for individuals and estates; USD 20,573 for 2026 and USD 20,116 for 2025 for foreign corporations and partnerships. Re-read today; found in: %s.' % ', '.join(sorted({a for v in sc['checks']['form3520_entity_threshold'].values() for a in v})),
      gh('integration/evidence.json'), ['N03'], []),
     ('A11', 'confirmed', 'Bank of China board 2026-11-10 17:39:58: buy 665.71, sell 668.51, conversion rate 671.67. Re-read today; editions K and L use the same snapshot.',
      gh('edition-k/data/model.json') + ' ' + gh('edition-l/data/model.json'), ['N02'], []),
     ('A12', 'confirmed', 'The USD 50,000 purchase quota is for 境内个人; a foreign individual buys against documented China income. Re-read today in Arts. 54 and 59 and in the Measures Art. 37.',
      gh('EXECUTIVE_SUMMARY.md'), ['N01', 'N18'], []),
     ('A13', 'confirmed at excerpt level', 'Overseas card cash: CNY 100,000 per person per year and CNY 10,000 per card per day. Matches the SAFE Q&A as returned by the official-site search; the page itself was not opened.',
      gh('EXECUTIVE_SUMMARY.md'), ['N16'], ['F08']),
     ('A14', 'confirmed', 'Emigrant transfers: staged remittance abolished; one approval may be remitted once or in parts. Re-read today in Huifa [2014] No. 2 Art. 6.', gh('EXECUTIVE_SUMMARY.md'), ['N23'], []),
     ('A15', 'not re-opened', 'HSBC China tariff, Bank of America incoming-wire fee, the Bank of China PDF price list (ATM and permit fees) and the CFETS central parity, used by editions K and L, were not re-opened in this session. They are neither confirmed nor contradicted here.',
      gh('edition-k/data/sources.json') + ' ' + gh('edition-l/data/sources.json'), ['N04'], ['F03']),
    ]
    areas = [dict(area=k, **v) for k, v in sc['areas'].items()]
    return dict(scanned_commit=sc['scanned_commit'], files_total=sc['files_total'], files_text=sc['files_text'], lines_total=sc['lines_total'],
                findings=[dict(id=a, status=b, finding=c, where_html=d, sources=e, flags=f) for a, b, c, d, e, f in F], areas=areas,
                stale_237_areas=stale, hosts_other=sc['hosts_other'])

def p_audit(AU):
    tone = {'confirmed': 'ok', 'needs review': 'warn', 'not re-opened': 'info', 'confirmed at excerpt level': 'info'}
    rows = [(f['id'], ['<b>%s</b>' % f['id'], '<span class="b %s">%s</span>' % (tone[f['status']], E(f['status'])), E(f['finding']), f['where_html'],
             src(f['sources']), fl(f['flags']) if f['flags'] else 'none']) for f in AU['findings']]
    ar = [['<a class="s" href="%s/tree/main/%s" rel="noopener"><b>%s</b></a>' % (C.REPO, '' if a['area'] == '(root)' else a['area'], E(a['area'])),
           str(a['files']), format(a['lines'], ','), str(a['official']), str(a['institution']), str(a['other'])] for a in AU['areas']]
    body = ('<h2>How the review was done</h2><ul>'
            '<li>Every tracked file outside this edition was read line by line by <a href="build/audit_repo.py">build/audit_repo.py</a> at commit <code>%s</code>: %d files, %d of them text, %s lines.</li>'
            '<li>Each line was checked for links, which were sorted by host into government, the institution itself, and other; and for the figures this session re-read on the official page.</li>'
            '<li>A figure is marked confirmed only when the official page was opened today and shows it. Figures whose source was not re-opened are marked so; they are not called wrong.</li>'
            '<li>No file outside <code>edition-12670774/</code> was changed. Requests to other sessions are logged in COORDINATION.md.</li></ul>'
            % (AU['scanned_commit'], AU['files_total'], AU['files_text'], format(AU['lines_total'], ','))
            + '<h2>Findings</h2>' + table(['ID', 'Status', 'Finding', 'Where in the repository', 'Official source', 'Flag'], rows)
            + '<h2>What was read</h2><p>Lines read and links found, by area. Other = neither government nor the institution concerned.</p>'
            + table(['Area', 'Files', 'Lines read', 'Government links', 'Institution links', 'Other links'], ar, cls='tight', sourced='repo')
            + '<h2 id="process">Process record</h2><p>Session %s worked only on branch <code>arena/12670774-china1</code> and only inside <code>edition-12670774/</code>, its workflow file and its own block of '
            '<a class="s" href="%s/blob/main/COORDINATION.md" rel="noopener">COORDINATION.md</a>. The claim, the sources, the verification performed, the pull request and the Pages result are recorded in that block. '
            'The root landing page and site-wide navigation belong to the final-integration session; a link request is logged there.</p>' % (C.SESSION, C.REPO))
    return page('audit.html', 'Repo audit', 'The repository checked against official pages opened today: what holds, what is out of date, what could not be re-checked.', body)

def p_sources():
    kind = {'gov-cn': 'China government', 'gov-us': 'US government', 'bank': 'Bank\'s own site', 'provider': 'Provider\'s own site'}
    rows = [(s[0], ['<b>%s</b>' % s[0], '<a class="s" href="%s" rel="noopener">%s</a>' % (E(s[4]), E(s[3])), E(s[5]),
             '<span class="b %s">%s</span>' % (('ok', 'opened') if s[1] == 'opened' else ('info', 'excerpt only')), kind[s[2]]]) for s in C.SOURCES]
    n_open = sum(1 for s in C.SOURCES if s[1] == 'opened')
    body = ('<p><b>Opened</b> means the page itself was opened in this session and the passage read. <b>Excerpt only</b> means the official site\'s own text was read in a site-search result and the page was not opened; values from such sources are always flagged. '
            'The verbatim passages are on the <a href="evidence.html">Evidence</a> page.</p>'
            + table(['ID', 'Source', 'What was read', 'Level', 'Type'], rows))
    return page('sources.html', 'Sources', '%d official pages: %d opened, %d read at excerpt level. All read on %s.' % (len(C.SOURCES), n_open, len(C.SOURCES) - n_open, C.AS_OF), body)

def p_evidence():
    import re
    txt = open(os.path.join(ROOT, 'research', 'source-notes.md'), encoding='utf-8').read()
    out = ''; in_ul = False
    link = lambda t: re.sub(r'(https?://[^\s<)]+)', lambda m: '<a class="s" href="%s" rel="noopener">%s</a>' % (m.group(1).rstrip('.,;'), m.group(1).rstrip('.,;')), E(t))
    for ln in txt.splitlines():
        if ln.startswith('## '):
            if in_ul: out += '</ul>'; in_ul = False
            sid = ln[3:6]
            out += '</section>' if out.count('<section') > out.count('</section>') else ''
            out += '<section class="m" id="e-%s"><h2>%s</h2>' % (E(sid), E(ln[3:]))
        elif ln.startswith('# '):
            continue
        elif ln.startswith('- '):
            if not in_ul: out += '<ul>'; in_ul = True
            out += '<li>%s</li>' % link(ln[2:])
        elif ln.strip():
            if in_ul: out += '</ul>'; in_ul = False
            out += '<p>%s</p>' % link(ln)
    if in_ul: out += '</ul>'
    if out.count('<section') > out.count('</section>'): out += '</section>'
    body = ('<p>The working log of this session: every official page consulted, with the passage relied on. Chinese text is quoted as published; '
            'the short English readings on the other pages are this session\'s own. Where a page was not opened, the entry says so.</p>' + out)
    return page('evidence.html', 'Evidence', 'The passages behind every figure, quoted from the official pages read on %s.' % C.AS_OF, body)

CSS = """:root{--bg:#f6f7f9;--card:#fff;--ink:#16202b;--mut:#5b6875;--line:#dde2e8;--acc:#0b5cab;--ok:#0a6b3d;--okb:#e3f4ea;--warn:#8a5300;--warnb:#fdf0d5;--bad:#a1211b;--badb:#fbe4e2;--info:#27507a;--infob:#e4eef8}
@media (prefers-color-scheme:dark){:root{--bg:#10151b;--card:#18202a;--ink:#e8edf2;--mut:#9aa7b4;--line:#2b3644;--acc:#7bb6f2;--ok:#7fd6a4;--okb:#12321f;--warn:#f1c27a;--warnb:#3a2a0c;--bad:#f3a29c;--badb:#3d1614;--info:#a9cdf0;--infob:#15293d}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans","PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:0 16px}a{color:var(--acc)}h1{font-size:1.7rem;line-height:1.2;margin:24px 0 8px}h2{font-size:1.25rem;margin:32px 0 8px}h3{font-size:1.05rem;margin:0 0 8px}
.lead{font-size:1.05rem;color:var(--mut);margin:0 0 20px;max-width:70ch}p,li,dd{max-width:80ch}
header{background:var(--card);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}header .wrap{display:flex;flex-wrap:wrap;align-items:center;gap:4px 16px;padding-top:8px;padding-bottom:8px}
.brand{font-weight:700;text-decoration:none;color:var(--ink)}.brand span{font-weight:400;color:var(--mut);font-size:.85rem}
nav{display:flex;gap:2px;overflow-x:auto;-webkit-overflow-scrolling:touch;max-width:100%}nav a{white-space:nowrap;padding:6px 10px;border-radius:6px;text-decoration:none;font-size:.9rem;color:var(--ink)}nav a[aria-current]{background:var(--infob);color:var(--info);font-weight:600}
footer{margin-top:48px;border-top:1px solid var(--line);color:var(--mut);font-size:.85rem;padding:16px 0 32px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:8px 0 8px}.k{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}.k span{display:block;color:var(--mut);font-size:.85rem}.k b{display:block;font-size:1.45rem;line-height:1.25;margin:2px 0}.k i{font-style:normal;font-size:.8rem;color:var(--mut)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;text-decoration:none;color:var(--ink);display:block}.card b{display:block;color:var(--acc)}.card span{font-size:.9rem;color:var(--mut)}
.tw{overflow-x:auto;-webkit-overflow-scrolling:touch;background:var(--card);border:1px solid var(--line);border-radius:10px;margin:8px 0 16px}table{border-collapse:collapse;width:100%;font-size:.92rem}th,td{text-align:left;vertical-align:top;padding:9px 12px;border-bottom:1px solid var(--line)}th{font-size:.78rem;text-transform:uppercase;letter-spacing:.03em;color:var(--mut);background:var(--bg);position:sticky;top:0}tbody tr:last-child td{border-bottom:0}
table.tight td,table.tight th{white-space:nowrap;padding:7px 10px}table.tight td:first-child{font-variant-numeric:tabular-nums}td{font-variant-numeric:tabular-nums}
.s,.f{display:inline-block;font-size:.75rem;font-weight:600;text-decoration:none;border-radius:4px;padding:0 5px;margin:1px 1px 1px 0;line-height:1.6}.s{background:var(--infob);color:var(--info)}.f{background:var(--warnb);color:var(--warn)}td a.s[href*="github.com"],p a.s{font-weight:500}
.b{display:inline-block;font-size:.75rem;font-weight:600;border-radius:999px;padding:1px 9px;white-space:nowrap}.b.ok{background:var(--okb);color:var(--ok)}.b.info{background:var(--infob);color:var(--info)}.b.warn{background:var(--warnb);color:var(--warn)}.b.bad{background:var(--badb);color:var(--bad)}
.blank{color:var(--mut);font-style:italic}.note,.formula{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--acc);border-radius:8px;padding:10px 14px}.formula{font-variant-numeric:tabular-nums}
.m{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:12px 0;scroll-margin-top:90px}.m h2{margin-top:0;font-size:1.1rem}dl{display:grid;grid-template-columns:minmax(80px,120px) 1fr;gap:6px 12px;margin:0}dt{color:var(--mut);font-size:.85rem}dd{margin:0}
details{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:10px 0;padding:0 14px}summary{cursor:pointer;font-weight:600;padding:12px 0}details .tw{border:0;border-top:1px solid var(--line);border-radius:0;margin:0 -14px}tr[id],section[id],h2[id]{scroll-margin-top:90px}tr:target td{background:var(--warnb)}
code{font-size:.9em;background:var(--bg);padding:1px 4px;border-radius:4px}ul.req li{margin:4px 0}
@media (max-width:640px){h1{font-size:1.4rem}table.stack thead{position:absolute;left:-9999px}table.stack tr{display:block;padding:10px 12px;border-bottom:1px solid var(--line)}table.stack tbody tr:last-child{border-bottom:0}table.stack td{display:block;border:0;padding:3px 0}table.stack td:first-child{font-size:1rem}table.stack td:not(:first-child)::before{content:attr(data-label) ": ";color:var(--mut);font-size:.78rem;text-transform:uppercase;letter-spacing:.03em}table.tight{font-size:.82rem}table.tight td,table.tight th{padding:6px 7px}dl{grid-template-columns:1fr}dt{margin-top:6px}}
"""

def jdefault(o):
    if isinstance(o, D): return format(o, 'f')
    raise TypeError(type(o))
def dump(name, obj):
    with open(os.path.join(ROOT, 'data', name), 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, default=jdefault); f.write('\n')

def main():
    os.makedirs(os.path.join(ROOT, 'assets'), exist_ok=True)
    AU = audit_data()
    dump('sources.json', dict(as_of=C.AS_OF, session=C.SESSION, sources=list(SRC.values())))
    dump('inputs.json', dict(as_of=C.AS_OF, inputs={k: dict(value=v[0], source=v[1], label=v[2]) for k, v in C.INPUTS.items()},
                             derived=dict(sell=SELL, buy=BUY, mid=MID, fx_margin_share=FX_PCT, cash_fx_margin_share=CASH_FX_PCT),
                             formula='cost_usd = (clamp(0.001*usd*sell, 50, 260) + 150)/sell + usd*(sell-mid)/mid'))
    dump('flags.json', dict(as_of=C.AS_OF, flags=list(FLAG.values())))
    dump('methods.json', dict(as_of=C.AS_OF, categories={k: v[0] for k, v in M.CATS.items()}, methods=M.METHODS))
    dump('tax.json', dict(as_of=C.AS_OF,
         china=[dict(item=a, rule=b, detail=c, sources=s, flags=f) for a, b, c, s, f in M.CHINA_TAX],
         us=[dict(item=a, rule=b, detail=c, sources=s, flags=f) for a, b, c, s, f in M.US_TAX],
         conversion_penalty=[dict(part=a, size=(FMT['fx'] if b == 'fx_pct' else b), note=c, sources=s, flags=f) for a, b, c, s, f in M.PENALTY_PARTS],
         routes=[dict(situation=a, method=b, cap=c, key_paper=d, sources=s) for a, b, c, d, s in M.ROUTES],
         summary=[dict(finding=a, detail=b.format(**FMT), sources=s, flags=f) for a, b, s, f in M.SUMMARY]))
    dump('costs.json', dict(as_of=C.AS_OF, targets=TARGETS, note='cost_usd is the sourced part only; null means no official input, see flags.', rows=[r for mid in COSTS for r in COSTS[mid]]))
    dump('audit.json', AU)
    cols = ['method', 'usd', 'units', 'unit', 'fee_cny', 'fee_usd', 'fx_usd', 'cost_usd', 'pct', 'fine_usd', 'fine_serious_usd', 'sources', 'source_urls', 'flags']
    with open(os.path.join(ROOT, 'data', 'costs.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, lineterminator='\n'); w.writerow(cols)
        for mid in COSTS:
            for r in COSTS[mid]:
                w.writerow([('' if r[c] is None else (format(r[c], 'f') if isinstance(r[c], D) else r[c])) for c in cols[:11]]
                           + [' '.join(r['sources']), ' '.join(SRC[i]['url'] for i in r['sources']), ' '.join(r['flags'])])
    pages = {'index.html': p_index(), 'summary.html': p_summary(), 'methods.html': p_methods(), 'steps.html': p_steps(), 'costs.html': p_costs(),
             'tax.html': p_tax(), 'flagged.html': p_flagged(), 'audit.html': p_audit(AU), 'sources.html': p_sources(), 'evidence.html': p_evidence()}
    for fn, txt in pages.items():
        open(os.path.join(ROOT, fn), 'w', encoding='utf-8').write(txt)
    open(os.path.join(ROOT, 'assets', 'style.css'), 'w', encoding='utf-8').write(CSS)
    print('built %d pages, %d methods, %d cost rows, %d sources, %d flags' % (len(pages), len(M.METHODS), sum(len(v) for v in COSTS.values()), len(SRC), len(FLAG)))
    print('one wire: $10k %s (%s) · $100k %s (%s) · $400k %s (%s) · fx margin %s · $400k as 8 quota wires %s' % (
        FMT['c10'], FMT['p10'], FMT['c100'], FMT['p100'], FMT['c400'], FMT['p400'], FMT['fx'], FMT['split']))

if __name__ == '__main__':
    main()
