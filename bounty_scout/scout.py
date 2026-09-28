"""Weekly scout for paid open-source bounties that match the owner's expertise.

Searches public GitHub issues carrying bounty labels (Algora, IssueHunt, and
generic "bounty" labels), extracts the advertised amount, scores each issue
against the owner's research areas, and writes a ranked Markdown report.

Only the standard library is used so the script runs unchanged on a GitHub
Actions runner or a laptop. Set GITHUB_TOKEN to raise the search rate limit.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

API = "https://api.github.com/search/issues"

# Labels used by the main bounty platforms that pay through GitHub issues.
QUERIES = [
    'label:"💎 Bounty" state:open is:issue no:assignee',
    'label:bounty state:open is:issue no:assignee',
    'label:"Bounty" state:open is:issue no:assignee',
    'label:"issuehunt" state:open is:issue no:assignee',
]

# Keywords weighted by fit with the owner's research areas.
KEYWORDS = {
    "machine learning": 3, "deep learning": 3, "computer vision": 3,
    "opencv": 3, "pytorch": 3, "tensorflow": 3, "yolo": 3, "image": 2,
    "model": 2, "dataset": 2, "gis": 3, "geospatial": 3, "gdal": 3,
    "iot": 3, "mqtt": 2, "sensor": 2, "autonomous": 3, "ros": 2,
    "python": 2, "numpy": 2, "pandas": 2, "jupyter": 2, "data": 1,
    "docs": 1, "documentation": 1, "typo": 1, "test": 1,
}

# Signals that an issue is too large or too contested for a quick win.
PENALTIES = {
    "rewrite": -3, "refactor entire": -3, "architecture": -2,
    "security audit": -2, "kernel": -2, "rust": -1, "blockchain": -2,
}

AMOUNT_RE = re.compile(
    r"(?:\$\s?(\d{1,3}(?:[,.]\d{3})*(?:\.\d+)?)"
    r"|(\d{1,3}(?:[,.]\d{3})*)\s?(?:usd|dollars?))",
    re.IGNORECASE,
)


@dataclass
class Bounty:
    title: str
    url: str
    repo: str
    amount: float | None
    comments: int
    updated_at: str
    labels: list[str] = field(default_factory=list)
    score: float = 0.0


def parse_amount(*texts: str) -> float | None:
    """Return the largest dollar amount mentioned in the given texts."""
    found = []
    for text in texts:
        for match in AMOUNT_RE.finditer(text or ""):
            raw = match.group(1) or match.group(2)
            digits = raw.replace(",", "")
            # "1.500" style thousands separators carry exactly three decimals.
            if re.fullmatch(r"\d{1,3}(\.\d{3})+", digits):
                digits = digits.replace(".", "")
            try:
                found.append(float(digits))
            except ValueError:
                continue
    return max(found) if found else None


def score(bounty: Bounty, text: str, today: dt.date) -> float:
    """Higher is better: fit with expertise, payout, low competition, freshness."""
    lowered = text.lower()
    fit = sum(w for k, w in KEYWORDS.items() if k in lowered)
    fit += sum(w for k, w in PENALTIES.items() if k in lowered)
    payout = min((bounty.amount or 0) / 50, 4)  # cap so huge bounties don't dominate
    competition = -min(bounty.comments / 5, 4)
    updated = dt.date.fromisoformat(bounty.updated_at[:10])
    freshness = max(0, 3 - (today - updated).days / 10)
    return round(fit + payout + competition + freshness, 2)


def search(query: str, token: str | None, per_page: int) -> list[dict]:
    params = urllib.parse.urlencode(
        {"q": query, "sort": "updated", "order": "desc", "per_page": per_page}
    )
    req = urllib.request.Request(f"{API}?{params}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "bounty-scout")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp).get("items", [])


def collect(items: list[dict], min_amount: float, today: dt.date) -> list[Bounty]:
    seen: dict[str, Bounty] = {}
    for item in items:
        url = item["html_url"]
        if url in seen or "pull_request" in item:
            continue
        labels = [lbl["name"] for lbl in item.get("labels", [])]
        body = item.get("body") or ""
        amount = parse_amount(item["title"], " ".join(labels), body)
        if amount is not None and amount < min_amount:
            continue
        bounty = Bounty(
            title=item["title"],
            url=url,
            repo=item["repository_url"].split("/repos/")[-1],
            amount=amount,
            comments=item.get("comments", 0),
            updated_at=item["updated_at"],
            labels=labels,
        )
        bounty.score = score(bounty, f"{item['title']} {' '.join(labels)} {body}", today)
        seen[url] = bounty
    return sorted(seen.values(), key=lambda b: b.score, reverse=True)


def render(bounties: list[Bounty], today: dt.date, top: int) -> str:
    lines = [
        f"# Bounty Scout — week of {today.isoformat()}",
        "",
        "Target: at least US$10/week. One merged bounty of US$50 covers ~5 weeks.",
        "",
        "| # | Score | Amount | Comments | Repository | Issue |",
        "|---|------:|-------:|---------:|------------|-------|",
    ]
    for i, b in enumerate(bounties[:top], 1):
        amount = f"${b.amount:,.0f}" if b.amount else "n/a"
        title = b.title.replace("|", "\\|")[:80]
        lines.append(
            f"| {i} | {b.score} | {amount} | {b.comments} | `{b.repo}` | [{title}]({b.url}) |"
        )
    if not bounties:
        lines.append("| – | – | – | – | – | No matching open bounties this week |")
    lines += [
        "",
        "## Before claiming",
        "- Read the repo's CONTRIBUTING and bounty rules; many ban low-effort or unreviewed AI-generated PRs.",
        "- Check nobody is already assigned or has an open PR (comment count is a proxy only).",
        "- Comment to claim (e.g. `/attempt` on Algora) only when you can deliver within a week.",
        "- Payouts go to your own Algora/IssueHunt/Stripe account; declare the income for tax.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-amount", type=float, default=10)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--per-page", type=int, default=50)
    parser.add_argument("--output", default="-")
    args = parser.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN")
    items: list[dict] = []
    for query in QUERIES:
        try:
            items.extend(search(query, token, args.per_page))
        except Exception as exc:  # one failed query should not sink the report
            print(f"warning: query failed ({query}): {exc}", file=sys.stderr)
        time.sleep(2)  # stay well under the search API rate limit

    today = dt.date.today()
    report = render(collect(items, args.min_amount, today), today, args.top)
    if args.output == "-":
        sys.stdout.write(report)
    else:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
