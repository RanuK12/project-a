import datetime as dt
import unittest

from bounty_scout.scout import collect, parse_amount, render

TODAY = dt.date(2026, 9, 27)


def item(title, body="", labels=(), comments=0, updated="2026-09-25T00:00:00Z", n=1):
    return {
        "title": title,
        "body": body,
        "html_url": f"https://github.com/o/r/issues/{n}",
        "repository_url": "https://api.github.com/repos/o/r",
        "labels": [{"name": name} for name in labels],
        "comments": comments,
        "updated_at": updated,
    }


class ParseAmountTest(unittest.TestCase):
    def test_dollar_sign(self):
        self.assertEqual(parse_amount("Fix bug ($150)"), 150)

    def test_thousands_separators(self):
        self.assertEqual(parse_amount("$1,500 bounty"), 1500)
        self.assertEqual(parse_amount("$1.500 bounty"), 1500)

    def test_usd_suffix_and_max(self):
        self.assertEqual(parse_amount("50 USD", "or $20"), 50)

    def test_none(self):
        self.assertIsNone(parse_amount("no money here"))


class CollectTest(unittest.TestCase):
    def test_filters_below_minimum_and_ranks_by_fit(self):
        items = [
            item("Typo fix", labels=["💎 Bounty", "$5"], n=1),
            item("Add YOLO computer vision example in Python", labels=["$100"], n=2),
            item("Rewrite blockchain kernel", labels=["$100"], comments=30, n=3),
        ]
        result = collect(items, min_amount=10, today=TODAY)
        self.assertEqual([b.url[-1] for b in result], ["2", "3"])

    def test_skips_pull_requests_and_duplicates(self):
        pr = item("PR", labels=["$50"], n=4)
        pr["pull_request"] = {}
        dup = item("Dup", labels=["$50"], n=5)
        self.assertEqual(len(collect([pr, dup, dup], 10, TODAY)), 1)

    def test_render_empty(self):
        self.assertIn("No matching open bounties", render([], TODAY, 10))


if __name__ == "__main__":
    unittest.main()
