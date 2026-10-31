"""Structural and quality tests for the docs/ tree.

Checks the guide actually covers the project goal: every required topic has
a home, internal links resolve, the glossary is substantive, and no
placeholder junk or stray non-content characters slipped in.
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"

CHAPTER_FILES = [
    "00-introduction.md",
    "01-what-to-say-before-you-buy-anything.md",
    "02-bedroom-recording-on-a-budget.md",
    "03-free-editing-and-hosting-compared.md",
    "04-episode-structure-you-can-sustain.md",
    "05-ai-transcripts-and-show-notes-with-verification.md",
    "06-guest-etiquette.md",
    "07-consistency-without-burnout.md",
    "08-quitting-politely.md",
]

WORKSHEET_FILES = [
    "worksheets/show-on-a-page.md",
    "worksheets/episode-planner.md",
    "worksheets/gear-budget.md",
    "worksheets/transcript-verification-checklist.md",
]

# The original goal, mapped to the phrases that prove coverage.
REQUIRED_COVERAGE = {
    "00-introduction.md": [
        "authors", "one-person LLC", "calm", "plain English",
        "audiobook-recording handbook",
    ],
    "01-what-to-say-before-you-buy-anything.md": [
        "one-sentence promise", "ten", "three-episode rule",
        "practice episodes",
        "worksheet",
    ],
    "02-bedroom-recording-on-a-budget.md": [
        "blanket", "room tone", "-12", "-6", "4–8 inches", "dynamic",
        "phone",
    ],
    "03-free-editing-and-hosting-compared.md": [
        "Audacity", "GarageBand", "RSS", "Spotify for Creators",
        "Buzzsprout", "| Tool |", "| Host |",
    ],
    "04-episode-structure-you-can-sustain.md": [
        "cold open", "segments", "takeaway", "outro", "batch",
        "minimum viable episode",
    ],
    "05-ai-transcripts-and-show-notes-with-verification.md": [
        "Whisper", "local", "verif", "show notes", "Names", "quotes",
        "AI drafts",
    ],
    "06-guest-etiquette.md": [
        "invite", "consent", "thank", "clock", "declines",
    ],
    "07-consistency-without-burnout.md": [
        "cadence", "season", "banked", "burnout", "ADHD", "worst",
    ],
    "08-quitting-politely.md": [
        "podfade", "finale", "feed", "break", "announc",
    ],
}


class CoverageTests(unittest.TestCase):
    def test_all_goal_chapters_exist(self):
        for name in CHAPTER_FILES:
            self.assertTrue((DOCS / name).exists(), name)

    def test_required_worksheets_exist(self):
        for name in WORKSHEET_FILES:
            self.assertTrue((DOCS / name).exists(), name)

    def test_each_chapter_covers_its_goal(self):
        for name, phrases in REQUIRED_COVERAGE.items():
            text = (DOCS / name).read_text(encoding="utf-8")
            lower = text.lower()
            for phrase in phrases:
                with self.subTest(phrase=phrase, file=name):
                    self.assertIn(phrase.lower(), lower)


class DocIntegrityTests(unittest.TestCase):
    def _all_md_files(self):
        return sorted(DOCS.rglob("*.md"))

    def test_every_doc_starts_with_h1_title(self):
        for path in self._all_md_files():
            with self.subTest(path=path.name):
                first = path.read_text(encoding="utf-8").lstrip().splitlines()[0]
                self.assertTrue(first.startswith("# "),
                                "%s has no H1 title" % path.name)

    def test_internal_markdown_links_resolve(self):
        for path in self._all_md_files():
            text = path.read_text(encoding="utf-8")
            for label, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text):
                if target.startswith(("http://", "https://", "mailto:", "index.html")):
                    continue
                clean = target.split("#")[0]
                if not clean:
                    continue
                with self.subTest(src=path.name, target=target):
                    dest = (path.parent / clean).resolve()
                    self.assertTrue(dest.exists(),
                                    "%s links to missing %r" % (path.name, target))

    def test_no_placeholder_junk(self):
        bad = re.compile(r"\b(TODO|TBD|FIXME|LOREM|XXX)\b")
        for path in self._all_md_files():
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(bad.search(text), path.name)

    def test_no_stray_cjk_or_replacement_characters(self):
        bad = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af\ufffd]")
        for path in self._all_md_files():
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(bad.search(text), path.name)


class GlossaryTests(unittest.TestCase):
    GLOSSARY = DOCS / "glossary.md"

    def test_glossary_is_substantive(self):
        text = self.GLOSSARY.read_text(encoding="utf-8")
        entries = re.findall(r"^- \*\*(.+?)\*\* — ", text, flags=re.M)
        self.assertGreaterEqual(len(entries), 25)
        self.assertEqual(len(entries), len(set(entries)),
                         "duplicate glossary terms")

    def test_glossary_entries_point_back_to_chapters(self):
        text = self.GLOSSARY.read_text(encoding="utf-8")
        for line in text.splitlines():
            if not line.startswith("- **"):
                continue
            with self.subTest(entry=line[:40]):
                self.assertIsNotNone(
                    re.search(r"\[Chapter \d+\]", line),
                    "glossary entry missing a chapter reference: %s" % line[:60])


class WorksheetUsabilityTests(unittest.TestCase):
    def test_worksheets_have_fillable_fields(self):
        for name in WORKSHEET_FILES:
            text = (DOCS / name).read_text(encoding="utf-8")
            with self.subTest(worksheet=name):
                self.assertRegex(text, r"(_{5,}|\[ \])",
                                 "worksheet has nothing to fill in")


if __name__ == "__main__":
    unittest.main()
