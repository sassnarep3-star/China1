#!/usr/bin/env python3
"""Offline, conservative QA for a built static GitHub Pages site.

This checks syntax/attribution structure, NOT whether a source supports a claim.
An allowed hostname is only a routing heuristic, not evidence of verification.
"""

import argparse
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit


@dataclass
class Issue:
    code: str
    page: str
    detail: str


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.duplicate_ids = set()
        self.links = []
        self.resources = []
        self.rows = []
        self.current_row = None
        self.cell_depth = 0
        self.headings = []
        self.current_heading = None
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            if attrs['id'] in self.ids:
                self.duplicate_ids.add(attrs['id'])
            self.ids.add(attrs['id'])
        if tag == 'a' and attrs.get('href') is not None:
            self.links.append((attrs['href'], attrs))
            if self.current_row is not None:
                self.current_row['links'].append(attrs['href'])
        if tag in ('img', 'script', 'link') and attrs.get('src' if tag != 'link' else 'href'):
            self.resources.append(attrs['src' if tag != 'link' else 'href'])
        if tag == 'script' and (attrs.get('src') or attrs.get('type') == 'module'):
            self.scripts.append(attrs.get('src', '<inline module>'))
        if tag == 'tr':
            self.current_row = {'links': [], 'text': '', 'has_td': False}
        if tag == 'td' and self.current_row is not None:
            self.cell_depth += 1
            self.current_row['has_td'] = True
        if tag in ('h1', 'h2'):
            self.current_heading = ''

    def handle_data(self, data):
        if self.current_row is not None:
            self.current_row['text'] += data
        if self.current_heading is not None:
            self.current_heading += data

    def handle_endtag(self, tag):
        if tag == 'td':
            self.cell_depth = max(0, self.cell_depth - 1)
        if tag == 'tr' and self.current_row is not None:
            if self.current_row['has_td']:
                self.rows.append(self.current_row)
            self.current_row = None
        if tag in ('h1', 'h2') and self.current_heading is not None:
            self.headings.append(' '.join(self.current_heading.split()))
            self.current_heading = None


def official_url(url, hosts):
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or '').rstrip('.').lower()
        # Accept only HTTPS and a hostname exactly on or below an allowlisted host.
        # Prevent deceptive matches such as irs.gov.example.com.
        return parsed.scheme.lower() == 'https' and any(
            host == allowed or host.endswith('.' + allowed) for allowed in hosts
        )
    except ValueError:
        return False


def resolve_local(root, current, href):
    """Return (target, fragment) or None for a non-local URL."""
    parts = urlsplit(href)
    if parts.scheme or parts.netloc or href.startswith('//'):
        return None
    path = unquote(parts.path)
    if path.startswith('/'):
        target = root / path.lstrip('/')
    else:
        target = current.parent / path if path else current
    if target.is_dir() or not path or path.endswith('/'):
        target /= 'index.html' if path else ''
    # GitHub Pages project sites may use /repo-name/ as a base URL. Supply the
    # built site's root as the base, then use relative URLs where possible.
    target = target.resolve()
    if not target.is_relative_to(root):
        return ('<escapes-root>', parts.fragment)
    return (target, unquote(parts.fragment))


def check_site(root, hosts, require_flagged=True):
    root = root.resolve()
    pages = {}
    issues = []
    for page in sorted(root.rglob('*.html')):
        parser = PageParser()
        parser.feed(page.read_text(encoding='utf-8'))
        parser.close()
        pages[page.resolve()] = parser
    if not pages:
        return [Issue('NO_HTML', '.', 'No built HTML pages found')], 0
    home = root / 'index.html'
    if home not in pages:
        issues.append(Issue('NO_HOME', '.', 'Missing index.html'))

    flagged_pages = {page for page, parser in pages.items()
                     if any('flagged for review' in h.lower() for h in parser.headings)}
    if require_flagged and not flagged_pages:
        issues.append(Issue('NO_FLAGGED_PAGE', '.', 'No HTML page has a Flagged for Review heading'))

    row_count = 0
    flagged_links = 0
    for page, parser in pages.items():
        name = str(page.relative_to(root))
        for ident in parser.duplicate_ids:
            issues.append(Issue('DUPLICATE_ID', name, ident))
        for index, row in enumerate(parser.rows, start=1):
            row_count += 1
            if not any(official_url(link, hosts) for link in row['links']):
                excerpt = ' '.join(row['text'].split())[:100]
                issues.append(Issue('ROW_WITHOUT_OFFICIAL_SOURCE', name,
                                    f'row {index}: {excerpt}'))
        for href, attrs in parser.links:
            if not href.strip():
                issues.append(Issue('EMPTY_LINK', name, 'Anchor with empty href'))
                continue
            if href.startswith(('mailto:', 'tel:')):
                continue
            parsed = urlsplit(href)
            if parsed.scheme in ('http', 'https') or href.startswith('//'):
                if not parsed.netloc and parsed.scheme:
                    issues.append(Issue('MALFORMED_URL', name, href))
                continue
            if parsed.scheme:
                issues.append(Issue('UNSUPPORTED_LINK', name, href))
                continue
            result = resolve_local(root, page, href)
            if result is None:
                continue
            target, anchor = result
            if target == '<escapes-root>' or not target.is_file():
                issues.append(Issue('BROKEN_LOCAL_LINK', name, href))
                continue
            if anchor and target in pages and anchor not in pages[target].ids:
                issues.append(Issue('BROKEN_ANCHOR', name, href))
            if target in flagged_pages:
                flagged_links += 1
        for resource in parser.resources:
            if resource.startswith(('data:', 'https:', 'http:', '//')):
                continue
            result = resolve_local(root, page, resource)
            if result is not None and (result[0] == '<escapes-root>' or not result[0].is_file()):
                issues.append(Issue('BROKEN_RESOURCE', name, resource))
    if require_flagged and flagged_pages and not flagged_links:
        issues.append(Issue('FLAGGED_PAGE_NOT_LINKED', '.', 'No internal link to the Flagged for Review page'))
    if row_count == 0:
        issues.append(Issue('NO_STATIC_ROWS', '.',
                            'No HTML table data rows were found; dynamic/JSON content was NOT checked'))
    return issues, row_count


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('site', type=Path, help='Built static site directory, not its source directory')
    ap.add_argument('--hosts', type=Path, default=Path(__file__).with_name('official-hosts.json'))
    ap.add_argument('--no-require-flagged', action='store_true')
    ap.add_argument('--json', action='store_true', help='Print machine-readable report')
    args = ap.parse_args()
    if not args.site.is_dir():
        ap.error(f'not a directory: {args.site}')
    hosts = json.loads(args.hosts.read_text(encoding='utf-8'))
    if not isinstance(hosts, list) or not all(isinstance(h, str) for h in hosts):
        ap.error('hosts file must be a JSON array of hostnames')
    issues, rows = check_site(args.site, {h.lower() for h in hosts}, not args.no_require_flagged)
    if args.json:
        print(json.dumps({'rows_checked': rows, 'issues': [asdict(i) for i in issues]}, indent=2))
    else:
        print(f'{rows} static table data rows checked; {len(issues)} issues')
        for issue in issues:
            print(f'{issue.code}: {issue.page}: {issue.detail}')
    return 1 if issues else 0


if __name__ == '__main__':
    sys.exit(main())
