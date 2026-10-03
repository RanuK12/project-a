# Verified Skills: Business and Release Plan

Target: **≥ US$10 net per week** (≈ US$43/month) from paid, verified AI skills
for SMA students and teachers, university academics, and programmers.

## 1. Value proposition (why people pay for something they could find free)

Thousands of free skills and prompt packs exist. Price alone does not stop a
malicious one; **verifiable provenance** does. The product is therefore not
"a prompt", but a prompt the buyer can trust:

| Buyer risk | Store control | Where it is implemented |
|---|---|---|
| Hidden code runs on my machine | Instruction-only policy: Markdown/data files only, no scripts | `skill_store/scan.py` (file-type rule) |
| Hidden instructions turn the AI against me | Scan for prompt injection, concealment, invisible Unicode, encoded blobs | `skill_store/scan.py` |
| My files or keys are sent somewhere | Scan for exfiltration endpoints, credential paths, network calls | `skill_store/scan.py` |
| The copy I received was altered | SHA-256 manifest of every file + checksum of the archive | `skill_store/release.py build` |
| Someone impersonates the author | SSH signature verifiable with the public key published in this repo | `release.py verify --allowed-signers` |
| A zip overwrites files outside the folder | Zip-slip check before extraction | `release.py verify` |
| Quality is unknown | Free sample skill + documented evaluation prompts | `skills/skill-safety-check` |

Honest limit: no scanner proves a skill is safe. The guarantee is that the
store sells only short, human-readable, instruction-only skills that the
buyer can read in full and verify came unaltered from a named author.

## 2. Product line (v1)

| Skill | Segment | Main job | Price (Lemon Squeezy / Gumroad) | Local price (Lynk.id / Karyakarsa) |
|---|---|---|---|---|
| `skill-safety-check` | Everyone | Audit any third-party skill before installing | Free (lead magnet, public repo) | Free |
| `tutor-coding-sma` | SMA/SMK students, informatics teachers | Socratic Python/algorithm tutor aligned to Kurikulum Merdeka, OSN roadmap | US$4 | Rp29.000 |
| `secure-code-review` | Programmers, CS students, startups | OWASP/CWE-mapped review incl. LLM-app security | US$7 | Rp59.000 |
| `scopus-manuscript-reviewer` | Lecturers, PhD/master's students | Pre-submission review, AI/ML pitfalls, reporting guidelines, response to reviewers | US$9 | Rp79.000 |
| Bundle (all three) | | | US$15 | Rp129.000 |
| Institutional license (one faculty or school) | Universities, schools | Same, multi-user | US$49/year | Rp690.000/tahun |

### Unit economics

Lemon Squeezy fee ≈ 5% + US$0.50 per order; Gumroad ≈ 10% + US$0.50 (verify current fees before pricing).
Net per sale on Lemon Squeezy: US$4 → 3.30, US$7 → 6.15, US$9 → 8.05, US$15 → 13.75.

Any one of these weekly mixes reaches US$10 net:
- 1 manuscript reviewer + 1 SMA tutor (≈ US$11.35), or
- 1 bundle (≈ US$13.75), or
- 1 institutional license every 5 weeks (≈ US$46 ÷ 5 ≈ US$9.30) plus occasional singles.

Expect zero sales during the first weeks; the target is realistic from
roughly month 2 onward if the marketing cadence in section 5 is kept. These
are planning assumptions, not forecasts.

## 3. Compatibility with AI tools

| Tool | How the buyer installs | Notes |
|---|---|---|
| Claude (claude.ai, desktop, Claude Code) | Upload the `.skill` file in the Skills section of claude.ai settings, or unzip into `~/.claude/skills/` for Claude Code | Native format |
| Other agents that read the Agent Skills `SKILL.md` format | Unzip into the tool's skills folder | Check each tool's current docs |
| ChatGPT (Custom GPT / Projects) | Paste SKILL.md body into Instructions; upload `references/*.md` as Knowledge | Instruction limit applies; keep body concise |
| Gemini (Gems) | Paste SKILL.md body into Gem instructions; attach references | |

Ship a one-page `INSTALL.md` per platform with each purchase (to be written
in the sales listing; not part of the signed archive).

## 4. Release procedure (PPEPP applied to each version)

| Stage | Action | Command / artefact |
|---|---|---|
| Penetapan | Define skill purpose, segment, 3 test prompts | `evals/evals.json` inside the skill folder |
| Pelaksanaan | Write/revise SKILL.md and references in the **private** repo | |
| Evaluasi | Run test prompts with and without the skill; scan | `python -m skill_store.scan <dir> --strict` |
| Pengendalian | Build, sign, verify; publish checksum and public key | see below |
| Peningkatan | Read buyer feedback and refund reasons monthly; bump version | CHANGELOG in listing |

One-time key setup (on your own laptop, never in a cloud session):

```bash
ssh-keygen -t ed25519 -C "aria@verified-skills" -f ~/.ssh/skill_signing
echo "aria@verified-skills $(cat ~/.ssh/skill_signing.pub)" > allowed_signers
# commit allowed_signers (public key only) to this public repo
```

Each release:

```bash
python -m skill_store.release build ../private-skills/tutor-coding-sma \
    --version 1.0.0 --license docs/EULA.md --key ~/.ssh/skill_signing
python -m skill_store.release verify dist/tutor-coding-sma-1.0.0.skill \
    --allowed-signers allowed_signers --identity aria@verified-skills
# upload .skill + .skill.sig + .skill.sha256 to the sales platform
```

Buyer verification (shown on every product page):

```bash
python -m skill_store.release verify tutor-coding-sma-1.0.0.skill \
    --allowed-signers allowed_signers --identity aria@verified-skills
```

## 5. Go-to-market (≤ 3 hours/week)

| Week | Action | Channel |
|---|---|---|
| 1 | Create Lemon Squeezy (or Gumroad) store; connect payout to bank/PayPal/Wise; create Lynk.id page for Rupiah buyers via QRIS | Platforms |
| 1 | Make paid skills repo **private**; keep this repo public for tooling, free skill, public key | GitHub |
| 2 | Publish free `skill-safety-check` with a short article: "How to check an AI skill before installing it" | LinkedIn, Medium, Kompasiana, dev.to |
| 2 | Demo video (2 min) of the SMA tutor refusing to dump homework and guiding instead | TikTok, YouTube Shorts, Instagram Reels |
| 3 | Offer the manuscript reviewer at faculty writing clinics and journal-writing workshops (with institutional approval) | Faculty network, APTIKOM/RJI groups |
| 4 | Pitch institutional license to 3 schools (MGMP Informatika) and 1 faculty | Email, WhatsApp |
| Monthly | Review sales, conversion, refunds; adjust price or listing; add one new skill per quarter | Dashboard |

Indicators: listing visits, free-skill downloads, conversion rate (aim
≥ 2%), net revenue per week, refund rate (< 5%).

## 6. Legal and ethical checklist

- **Repository visibility**: this repository is public and GPL-2.0. Never
  commit paid skill content here; keep it in a private repository. Anything
  pushed to a public repo should be treated as permanently public.
- **Minors**: SMA students are usually under 18. Use payment channels that
  parents can operate, collect no personal data beyond what the platform
  requires, and keep the tutor's safety section intact.
- **Academic integrity**: the reviewer and tutor are designed to coach, not
  ghost-write. Market them that way; this is also a selling point to
  institutions.
- **Tax**: report income in the annual SPT (PPh orang pribadi). Platforms such
  as Lemon Squeezy act as merchant of record and handle VAT/sales tax for
  foreign buyers.
- **Employment rules**: as a civil servant or permanent lecturer, check
  institutional rules on outside commercial activity and conflicts of
  interest, especially when selling to your own students.
- **Trademarks**: do not use "Claude", "Anthropic", "OpenAI", or "ChatGPT" in
  the store name or imply endorsement; "compatible with Claude" is factual.
