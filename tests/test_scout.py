import datetime as dt
import unittest
from collections import Counter

from bounty_scout.scout import collect, fit, parse_amount, render

TODAY = dt.date(2026, 9, 27)

ORG = {"owner": {"type": "Organization"}, "stargazers_count": 5000}
REPOS = {
    "org/vision": ORG,
    "org/web": ORG,
    "org/small": {"owner": {"type": "Organization"}, "stargazers_count": 50},
    "someone/tool": {"owner": {"type": "User"}, "stargazers_count": 9000},
}


def item(title, repo="org/vision", body="", labels=(), comments=0,
         updated="2026-09-25T00:00:00Z", n=1):
    return {
        "title": title,
        "body": body,
        "html_url": f"https://github.com/{repo}/issues/{n}",
        "repository_url": f"https://api.github.com/repos/{repo}",
        "labels": [{"name": name} for name in labels],
        "comments": comments,
        "updated_at": updated,
    }


def run(items, min_amount=10, min_stars=500):
    return collect(items, min_amount, min_stars, TODAY, REPOS.get)


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


class FitTest(unittest.TestCase):
    def test_whole_words_only(self):
        # "gis" inside "registration" and "ros" inside "across" must not match.
        self.assertEqual(fit("Fix registration across pages")[0], 0)

    def test_domain_match_and_penalty(self):
        matches, score = fit("Add YOLO object detection for a Laravel app")
        self.assertEqual(matches, 2)
        self.assertEqual(score, 3 + 3 - 2)


class CollectTest(unittest.TestCase):
    def test_keeps_only_trusted_domain_bounties(self):
        items = [
            item("Add YOLO export", labels=["$100"], n=1),                      # kept
            item("Add YOLO export", labels=["💎 Bounty"], n=2),                  # no amount
            item("Add YOLO export", labels=["$5"], n=3),                         # too small
            item("Fix CSS button", repo="org/web", labels=["$100"], n=4),        # off-domain
            item("Add YOLO export", repo="org/small", labels=["$100"], n=5),     # few stars
            item("Add YOLO export", repo="someone/tool", labels=["$100"], n=6),  # user repo
            item("Add YOLO export", repo="x/bug-bounty", labels=["$100"], n=7),  # farm
        ]
        bounties, dropped = run(items)
        self.assertEqual([b.url for b in bounties],
                         ["https://github.com/org/vision/issues/1"])
        self.assertEqual(sum(dropped.values()), 6)
        self.assertEqual(dropped["no stated amount"], 1)
        self.assertEqual(dropped["not an organisation repo"], 1)

    def test_algora_bounty_ranks_higher(self):
        items = [
            item("PyTorch inference fix", labels=["$100"], n=1),
            item("PyTorch inference fix", labels=["$100", "💎 Bounty"], n=2),
        ]
        bounties, _ = run(items)
        self.assertEqual(bounties[0].url[-1], "2")

    def test_skips_pull_requests_and_duplicates(self):
        pr = item("Python PR", labels=["$50"], n=4)
        pr["pull_request"] = {}
        dup = item("Python dup", labels=["$50"], n=5)
        bounties, _ = run([pr, dup, dup])
        self.assertEqual(len(bounties), 1)

    def test_render_empty_and_dropped(self):
        report = render([], TODAY, 10, Counter({"no stated amount": 3}), failed_queries=1)
        self.assertIn("No bounty passed the filters", report)
        self.assertIn("no stated amount: 3", report)
        self.assertIn("search queries that failed: 1", report)


if __name__ == "__main__":
    unittest.main()
