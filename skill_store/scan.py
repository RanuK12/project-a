"""Static safety scanner for AI agent skills (SKILL.md folders).

The store sells instruction-only skills: Markdown and data files, no executable
code. This scanner enforces that policy and flags the patterns most often used
to smuggle malicious behaviour into a skill: hidden Unicode, encoded payloads,
pipe-to-shell installers, exfiltration endpoints, credential paths, and prompt
injection aimed at the model reading the skill.

Usage:
    python -m skill_store.scan path/to/skill [more/skills ...] [--strict]

Exit code 1 when any HIGH finding exists (or MEDIUM, with --strict).
"""

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ALLOWED_EXTENSIONS = {".md", ".txt", ".json", ".csv", ".yaml", ".yml"}
MAX_FILE_BYTES = 200_000

HIGH, MEDIUM, LOW = "HIGH", "MEDIUM", "LOW"
SEVERITY_ORDER = {HIGH: 0, MEDIUM: 1, LOW: 2}

# Zero-width, bidirectional-override and Unicode "tag" characters can hide
# instructions that a human reviewer never sees but the model still reads.
HIDDEN_CHARS = re.compile(
    "[​-‏‪-‮⁠-⁤⁦-⁩﻿\U000e0000-\U000e007f]"
)

TEXT_RULES = [
    (HIGH, "pipe-to-shell",
     re.compile(r"\b(curl|wget|iwr|Invoke-WebRequest)\b[^\n|]*\|\s*(sudo\s+)?(ba|z)?sh\b|\|\s*iex\b", re.I),
     "downloads and executes remote code"),
    (HIGH, "destructive-command",
     re.compile(r"\brm\s+-[a-z]*r[a-z]*f?[a-z]*\s+(/|~|\$HOME)(\s|$)|\bmkfs\.|\bdd\s+if=.*of=/dev/", re.I),
     "destructive filesystem command"),
    (HIGH, "encoded-payload",
     re.compile(r"[A-Za-z0-9+/]{200,}={0,2}"),
     "long base64-like blob (possible hidden payload)"),
    (HIGH, "exfiltration-endpoint",
     re.compile(r"(discord(app)?\.com/api/webhooks|hooks\.slack\.com|webhook\.site|requestbin|"
                r"pipedream\.net|ngrok(-free)?\.(io|app)|pastebin\.com|transfer\.sh|"
                r"api\.telegram\.org/bot)", re.I),
     "known data-exfiltration or anonymous upload endpoint"),
    (HIGH, "prompt-injection",
     re.compile(r"\b(ignore|disregard|forget|override)\b[^.\n]{0,40}\b(previous|prior|above|earlier|"
                r"system|safety)\b[^.\n]{0,20}\b(instructions?|prompts?|rules?|guidelines?)\b", re.I),
     "tells the model to discard its other instructions"),
    (HIGH, "concealment",
     re.compile(r"\b(do not|don't|never|without)\s+(tell|telling|inform|informing|reveal|revealing|"
                r"mention|mentioning|ask|asking|notify|notifying|show|showing)\b[^.\n]{0,20}\b(the\s+)?user\b", re.I),
     "instructs the model to hide actions from the user"),
    (MEDIUM, "credential-path",
     re.compile(r"(~|\$HOME)?/?\.(ssh|aws|gnupg|kube|docker)\b(?!-)|\bid_(rsa|ed25519)\b|\.env\b|"
                r"\.netrc\b|\.git-credentials\b|Login Data|keychain", re.I),
     "references credential or secret storage"),
    (MEDIUM, "network-call",
     re.compile(r"\b(requests\.(get|post|put)|urllib\.request|http\.client|fetch\(|XMLHttpRequest|"
                r"socket\.socket|curl\s+-[a-zA-Z]*\s*(-d|--data|-F|-T)|Invoke-RestMethod)", re.I),
     "network request inside the skill text"),
    (MEDIUM, "privilege-escalation",
     re.compile(r"\bsudo\b|\bchmod\s+(\+s|[0-7]*7[0-7]{2})\b|\bSet-ExecutionPolicy\b", re.I),
     "privilege escalation or permission loosening"),
    (LOW, "external-url",
     re.compile(r"https?://[^\s)\]>\"']+", re.I),
     "external URL (review destination)"),
]


@dataclass(frozen=True)
class Finding:
    severity: str
    rule: str
    path: str
    line: int
    detail: str

    def __str__(self):
        loc = f"{self.path}:{self.line}" if self.line else self.path
        return f"[{self.severity}] {self.rule} {loc} - {self.detail}"


def _check_frontmatter(skill_dir: Path):
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [Finding(HIGH, "missing-skill-md", "SKILL.md", 0, "skill folder has no SKILL.md")]
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    match = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not match:
        return [Finding(HIGH, "frontmatter", "SKILL.md", 1, "missing YAML frontmatter")]
    keys = {line.split(":", 1)[0].strip() for line in match.group(1).splitlines()
            if line and not line[0].isspace() and ":" in line}
    return [Finding(HIGH, "frontmatter", "SKILL.md", 1, f"frontmatter lacks '{key}'")
            for key in ("name", "description") if key not in keys]


def scan_text(text: str, rel: str):
    findings = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for ch in set(HIDDEN_CHARS.findall(line)):
            if ch == "﻿" and lineno == 1 and line.startswith(ch):
                continue  # a leading byte-order mark is harmless
            findings.append(Finding(HIGH, "hidden-unicode", rel, lineno,
                                    f"invisible/bidi character U+{ord(ch):04X}"))
        for severity, rule, pattern, detail in TEXT_RULES:
            match = pattern.search(line)
            if match:
                shown = match.group(0)
                shown = shown if len(shown) <= 60 else shown[:57] + "..."
                findings.append(Finding(severity, rule, rel, lineno, f"{detail}: {shown!r}"))
    return findings


def scan_skill(skill_dir, allow_scripts=False):
    skill_dir = Path(skill_dir)
    findings = _check_frontmatter(skill_dir)
    for path in sorted(skill_dir.rglob("*")):
        rel = path.relative_to(skill_dir).as_posix()
        if any(part in {"__pycache__", ".git"} for part in path.parts):
            continue
        if path.is_symlink():
            findings.append(Finding(HIGH, "symlink", rel, 0, "symlinks can point outside the skill"))
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            severity = MEDIUM if allow_scripts else HIGH
            findings.append(Finding(severity, "file-type", rel, 0,
                                    f"'{path.suffix or path.name}' is not an instruction-only file type"))
            continue
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            findings.append(Finding(MEDIUM, "large-file", rel, 0, f"{size} bytes; review manually"))
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            findings.append(Finding(HIGH, "binary-content", rel, 0, "not valid UTF-8 text"))
            continue
        findings.extend(scan_text(text, rel))
    return sorted(findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.path, f.line))


def is_blocking(findings, strict=False):
    blocking = {HIGH, MEDIUM} if strict else {HIGH}
    return any(f.severity in blocking for f in findings)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("skills", nargs="+", help="skill folders to scan")
    parser.add_argument("--strict", action="store_true", help="also fail on MEDIUM findings")
    parser.add_argument("--allow-scripts", action="store_true",
                        help="downgrade non-text files from HIGH to MEDIUM")
    args = parser.parse_args(argv)

    failed = False
    for skill in args.skills:
        findings = scan_skill(skill, allow_scripts=args.allow_scripts)
        blocked = is_blocking(findings, args.strict)
        failed |= blocked
        print(f"== {skill}: {'FAIL' if blocked else 'PASS'} ({len(findings)} finding(s))")
        for finding in findings:
            print(f"   {finding}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
