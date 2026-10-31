# STATUS — Podcast Friend Starter Guide

Last updated: 2026-10-31

## What was built

A complete, calm, beginner-facing manual for starting a small podcast or audio show, aimed at authors and one-person LLCs — plus the local-first static site that presents it, the scripts that generate and verify it, and a tested build around all of it.

**Deliverables**

1. **Nine docs chapters** (`docs/*.md`), covering the full original goal:
   - 00 — Start a small podcast, calmly (who it's for, how to use the guide, companions incl. the audiobook-recording handbook)
   - 01 — What to say before you buy anything (one-sentence promise, ten-episode test, three-episode rule, LLC housekeeping)
   - 02 — Bedroom recording on a budget (room treatment for free, mic technique, levels, file habits, the one earned mic purchase)
   - 03 — Free editing and hosting, compared (tool table: Audacity/GarageBand/ocenaudio/Reaper/others; host table: Spotify for Creators/Buzzsprout/Podbean/etc.; feed-ownership rules)
   - 04 — Episode structure you can sustain (five-part skeleton, batch rhythm, minimum viable episode)
   - 05 — AI transcripts and show notes, with verification (local Whisper first; template; names/numbers/quotes/timestamps/links verification pass)
   - 06 — Guest etiquette (invite + prep email templates, consent, the courtesy loop, declines, corrections)
   - 07 — Consistency without burnout (cadence, seasons, banked episodes, the five real burnout edges, low-energy/ADHD adaptations)
   - 08 — Quitting politely (podfade vs real ending; tired-or-done diagnosis; step-by-step exit)
2. **Glossary** (`docs/glossary.md`): 30 entries, alphabetical, each linking back to the chapter that uses it.
3. **Four worksheets** (`docs/worksheets/*.md`): show-on-a-page, episode planner, gear budget, transcript-verification checklist.
4. **Static HTML site** (`site/`, built and committed): 15 pages — index with chapter/worksheet cards, all chapters, glossary, worksheets — warm calm CSS, no JavaScript, print-friendly, cross-linked with prev/next navigation. Megabytes of "no" instead of megabytes of JS.
5. **Build system** (stdlib-only Python, local-first):
   - `scripts/mdrender.py` — small dependency-free Markdown renderer (headings with stable slugs, nested lists, loose lists, checkbox glyphs, tables with alignment, blockquotes, code fences, inline markup, href rewriting).
   - `scripts/build.py` — renders all docs, builds the index, validates every internal link and #anchor, exits non-zero on any broken link.
   - `scripts/new_episode.py` — generates an episode planner draft from `templates/episode-template.md` into `episodes/` (git-ignored). Refuses to overwrite.
   - `build.sh` / `test.sh` — thin wrappers.
6. **Test suite** (`scripts/tests/`, 52 tests): renderer behavior, docs coverage of every goal topic (phrase-level checks per chapter), internal-link resolution, glossary completeness, build-in-a-temp-dir checks, end-to-end `main()` runs (success and failure paths), repo hygiene (secrets scan, no personal contact data, LICENSE/README checks), and `new_episode.py` behavior.

## How to run it

```sh
./build.sh        # rebuild site/ (self-validating; exits non-zero on broken links)
./test.sh         # run all 52 tests
open site/index.html   # read the built site (any browser, fully offline)
```

Helper utility:

```sh
python3 scripts/new_episode.py --title "Some episode" --number 4
```

Requirements: Python 3.9+ (tested on 3.13). No pip installs, no network. Anything else (Node, pandoc, etc.) is deliberately not needed.

## Verification results (actual run, this session)

- `./test.sh` → **Ran 52 tests — OK** (0 failures, 0 errors)
- `./build.sh` → **OK: built 15 pages into .../site** (link + anchor validation passed)
- Spot checks of built HTML: tables render (editing/hosting comparisons), checkbox glyphs render in worksheets, guest email template blockquotes render, prev/next/index navigation correct from all depths, footer credits Asdale Dynamics, LLC with MIT license.
- Renderer edge cases pinned by tests: duplicate heading slugs deduplicated (same / same-2), unterminated code fence raises, HTML injection escaped, missing/broken links fail the build (unit-tested), loose ordered lists keep numbering.

## Known gaps

- **Host comparisons are a snapshot.** Free tiers change their numbers yearly; the guide says so plainly and tells readers to re-check the two things that matter (storage/expiry limits, feed portability). A small refresh cadence (e.g., before each season) is a future improvement, documented in the guide itself (Chapter 3).
- **No RSS-feed generator script.** The guide teaches hosting on free tiers (hosts generate the feed). A tiny offline "preview your own feed" script would be a natural follow-up if someone wants to self-validate before upload.
- **No additional-language versions.** English-only for now.
- **Companion repo not bundled.** The audiobook-recording handbook is referenced by name and via dylanasdale.github.io; fetching it requires visiting that site (deliberate — this repo stays local-first and self-contained).
- **Worksheets are print-oriented.** They're designed as fill-in Markdown/print pages; an interactive web worksheet (with localStorage) would degrade the no-JS guarantee, so it wasn't done.
- The committed `site/` is rebuilt by `./build.sh`; a stale copy (e.g., after editing docs without rebuilding) is made visually obvious by the build date in the footer.

## Content guardrails honored

- No secrets, API keys, or personal contact details anywhere in the repo (enforced by tests, not just intent).
- LICENSE is MIT with the exact line "Copyright (c) 2026 Asdale Dynamics, LLC"; README credits Asdale Dynamics, LLC.
- Educational boundary kept in-guide: medical/legal/financial disclaimers point to professionals; the guide stays a friend, not a lawyer.
