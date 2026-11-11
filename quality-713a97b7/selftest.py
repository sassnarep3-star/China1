#!/usr/bin/env python3
"""Mutation-oriented tests for the independent QA checker, using isolated fixtures."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("china_quality_audit", HERE / "audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
SOURCE = "https://www.safe.gov.cn/safe/2006/1225/5319.html"


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = audit.ROOT, audit.GUIDE, audit.DATA
        audit.ROOT = Path(self.temp.name).resolve()
        audit.GUIDE = audit.ROOT / "guide"
        audit.DATA = audit.GUIDE / "data"
        audit.DATA.mkdir(parents=True)
        (audit.ROOT / "quality-713a97b7").mkdir()
        audit.errors.clear()
        audit.warnings.clear()
        self.write_json("guide/data/sources.json", {"sources": [{"url": SOURCE}]})
        self.write_json("guide/data/flagged.json", {"items": [{"id": "F1"}]})
        self.write_json("guide/data/methods.json", {"methods": [{"id": "M01"}]})
        self.write_json("guide/data/prices.json", {})
        self.write_json("quality-713a97b7/findings.json", {"sources": []})
        (audit.ROOT / "index.html").write_text(
            f'<table><tbody><tr><td><a href="{SOURCE}">Source</a></td></tr></tbody></table>'
            '<a href="guide/costs.html#target">Costs</a>', encoding="utf-8")
        (audit.GUIDE / "costs.html").write_text('<h1 id="target">Costs</h1>', encoding="utf-8")
        (audit.ROOT / "quality-713a97b7/index.html").write_text('<h1>Review</h1>', encoding="utf-8")
        self.rows = [{"method_id": "M01", "amount_usd": str(n), "status": "blank",
                      "total_cost_usd": "", "share_of_amount": "", "flags": "F1", "source_urls": SOURCE}
                     for n in audit.EXPECTED_AMOUNTS]
        self.write_csv()

    def tearDown(self):
        audit.ROOT, audit.GUIDE, audit.DATA = self.old
        audit.errors.clear()
        audit.warnings.clear()
        self.temp.cleanup()

    def write_json(self, name, value):
        (audit.ROOT / name).write_text(json.dumps(value), encoding="utf-8")

    def write_csv(self):
        with (audit.DATA / "cost-ladder.csv").open("w", encoding="utf-8", newline="") as out:
            w = csv.DictWriter(out, fieldnames=list(self.rows[0]))
            w.writeheader()
            w.writerows(self.rows)

    def test_valid_fixture(self):
        audit.page_checks()
        audit.cost_checks()
        self.assertEqual(audit.errors, [])

    def test_missing_source_fails(self):
        (audit.ROOT / "index.html").write_text('<table><tbody><tr><td>No source</td></tr></tbody></table>', encoding="utf-8")
        audit.page_checks()
        self.assertTrue(any("no registered" in message for message in audit.errors))

    def test_unknown_cost_cannot_be_filled_or_unflagged(self):
        self.rows[0]["total_cost_usd"] = "123.00"
        self.rows[1]["flags"] = ""
        self.write_csv()
        audit.cost_checks()
        self.assertTrue(any("not blank" in message for message in audit.errors))
        self.assertTrue(any("lacks registered flag" in message for message in audit.errors))

    def test_duplicate_amount_fails(self):
        self.rows[1]["amount_usd"] = self.rows[0]["amount_usd"]
        self.write_csv()
        audit.cost_checks()
        self.assertTrue(any("missing/duplicate" in message for message in audit.errors))

    def test_missing_fragment_fails(self):
        (audit.GUIDE / "costs.html").write_text('<h1 id="other">Costs</h1>', encoding="utf-8")
        audit.page_checks()
        self.assertTrue(any("missing fragment" in message for message in audit.errors))

    def test_archive_fragment_fails(self):
        (audit.ROOT / "archive.html").write_text('<a href="guide/costs.html#not-there">Archive</a>', encoding="utf-8")
        audit.repository_fragment_checks()
        self.assertTrue(any("broken repository anchor" in message for message in audit.errors))

    def test_project_root_links_need_repository_prefix(self):
        self.assertIsNone(audit.local_destination(audit.ROOT / "index.html", "/guide/costs.html"))
        self.assertTrue(any("missing /China1/" in message for message in audit.errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
