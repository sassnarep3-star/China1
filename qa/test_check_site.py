import tempfile
import unittest
from pathlib import Path

from check_site import check_site, official_url


class CheckSiteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'index.html').write_text('''
            <h1>Overview</h1><a href="review.html">Flagged for Review</a>
            <table><thead><tr><th>Claim</th><th>Source</th></tr></thead>
            <tbody><tr><td>Needs evidence</td><td><a href="https://www.irs.gov/">IRS</a></td></tr></tbody></table>
            <a href="#intro">Introduction</a><h2 id="intro">Introduction</h2>
        ''', encoding='utf-8')
        (self.root / 'review.html').write_text('''
            <h1>Flagged for Review</h1><a href="index.html">Home</a>
            <table><tr><td>Unverified amount: blank</td>
            <td><a href="https://www.safe.gov.cn/en/">SAFE</a></td></tr></table>
        ''', encoding='utf-8')
        self.hosts = {'irs.gov', 'safe.gov.cn'}

    def tearDown(self):
        self.temp.cleanup()

    def codes(self):
        issues, rows = check_site(self.root, self.hosts)
        return {issue.code for issue in issues}, rows

    def test_clean_static_site(self):
        self.assertEqual((set(), 2), self.codes())

    def test_deceptive_domain_is_not_accepted(self):
        self.assertFalse(official_url('https://irs.gov.example.net/a', self.hosts))
        self.assertFalse(official_url('http://irs.gov/a', self.hosts))
        self.assertTrue(official_url('https://www.irs.gov/a', self.hosts))
        (self.root / 'index.html').write_text('''<a href="review.html">Review</a>
            <table><tr><td>Claim</td><td><a href="https://irs.gov.example.net/">Source</a></td></tr></table>''', encoding='utf-8')
        self.assertIn('ROW_WITHOUT_OFFICIAL_SOURCE', self.codes()[0])

    def test_broken_link_anchor_resource_and_missing_source(self):
        (self.root / 'index.html').write_text('''
          <a href="missing.html">Missing</a><a href="review.html#no-such-id">Bad anchor</a>
          <img src="bad.png"><table><tr><td>Unverified, no link</td></tr></table>
        ''', encoding='utf-8')
        codes, _ = self.codes()
        self.assertTrue({'BROKEN_LOCAL_LINK', 'BROKEN_ANCHOR', 'BROKEN_RESOURCE',
                         'ROW_WITHOUT_OFFICIAL_SOURCE'}.issubset(codes))

    def test_no_rows_cannot_be_certified(self):
        (self.root / 'index.html').write_text('<a href="review.html">Review</a><script src="app.js"></script>', encoding='utf-8')
        codes, rows = self.codes()
        self.assertEqual(rows, 1)  # review page still has a static row
        (self.root / 'review.html').write_text('<h1>Flagged for Review</h1>', encoding='utf-8')
        self.assertIn('NO_STATIC_ROWS', self.codes()[0])

    def test_missing_flagged_page(self):
        (self.root / 'review.html').write_text('<h1>Other</h1>', encoding='utf-8')
        self.assertIn('NO_FLAGGED_PAGE', self.codes()[0])


if __name__ == '__main__':
    unittest.main()
