"""Build-output tests: generate the site into a temp dir and check it."""

import pathlib
import shutil
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import build  # noqa: E402
import mdrender  # noqa: E402


class BuildToTemp(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="pfsg-build-"))
        self.addCleanup(shutil.rmtree, self.tmp)
        self.out = self.tmp / "site"
        self.outputs, self.errors = build.build(ROOT / "docs", self.out,
                                                build_date="2026-10-30")

    def test_build_validates_clean(self):
        self.assertEqual(self.errors, [])

    def test_exactly_fifteen_pages_plus_assets(self):
        pages = sorted(p.relative_to(self.out).as_posix()
                       for p in self.out.rglob("*.html"))
        self.assertEqual(len(pages), 15)
        self.assertIn("index.html", pages)
        self.assertTrue((self.out / "assets" / "style.css").exists())

    def test_every_page_is_valid_looking_html(self):
        for name in self.outputs:
            page = (self.out / self.outputs[name]["path"])
            with self.subTest(page=page.name):
                text = page.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("<!DOCTYPE html>"))
                self.assertIn('<meta charset="utf-8">', text)
                self.assertIn('lang="en"', text)
                self.assertIn("</html>", text)

    def test_index_cards_list_all_chapters_and_worksheets(self):
        index = (self.out / "index.html").read_text(encoding="utf-8")
        for name in build.CHAPTERS + build.WORKSHEETS:
            href = name[0].replace(".md", ".html")
            with self.subTest(href=href):
                self.assertIn('href="%s"' % href, index)

    def test_chapter_pages_have_prev_next_nav(self):
        page = (self.out / "03-free-editing-and-hosting-compared.html")
        text = page.read_text(encoding="utf-8")
        self.assertIn('class="pagenav"', text)
        self.assertIn("Index", text)

    def test_worksheets_link_back_to_index(self):
        page = self.out / "worksheets" / "episode-planner.html"
        text = page.read_text(encoding="utf-8")
        self.assertIn("../index.html", text)

    def test_footer_has_license_and_llc_credit(self):
        page = (self.out / "glossary.html").read_text(encoding="utf-8")
        self.assertIn("Asdale Dynamics, LLC", page)
        self.assertIn("MIT license", page)

    def test_nav_links_resolve_independently_from_worksheets(self):
        page = (self.out / "worksheets" / "gear-budget.html").read_text(encoding="utf-8")
        self.assertIn('href="../00-introduction.html"', page)
        self.assertIn('href="../glossary.html"', page)


class InternalLinkUnitTests(unittest.TestCase):
    """Feed validate_links a deliberately broken site; it must report it."""

    def test_broken_anchor_and_missing_page_are_caught(self):
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="pfsg-linkcheck-"))
        try:
            (tmp / "a.html").write_text(
                '<!DOCTYPE html><a href="b.html">b</a>'
                '<a href="#missing">x</a><p id="anchor"></p>', encoding="utf-8")
            errors = build.validate_links(tmp)
            self.assertTrue(any("broken link -> b.html" in e for e in errors), errors)
            self.assertTrue(any("missing anchor -> #missing" in e for e in errors),
                            errors)
        finally:
            shutil.rmtree(tmp)


class WorkbookHeadingAnchors(unittest.TestCase):
    """In-doc anchors (e.g. chapter links like c4.md#section) must exist.

    The real docs mostly link whole pages, but if any page link includes a
    fragment, the build's own validator would catch it. This test pins the
    anchor-generation contract for heading consistency.
    """

    def test_anchor_contract(self):
        r = mdrender.Renderer()
        body = r.render("## Two Word Heading")
        self.assertIn('id="two-word-heading"', body)


class E2EMainTests(unittest.TestCase):
    def test_main_success_exit_code(self):
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="pfsg-e2e-"))
        try:
            code = build.main(["--out", str(tmp / "site"),
                               "--docs", str(ROOT / "docs"),
                               "--date", "2026-10-30"])
            self.assertEqual(code, 0)
            self.assertTrue((tmp / "site" / "index.html").exists())
        finally:
            shutil.rmtree(tmp)

    def test_main_fails_on_missing_docs(self):
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="pfsg-e2e-"))
        try:
            empty = tmp / "docs"
            empty.mkdir()
            code = build.main(["--out", str(tmp / "site"),
                               "--docs", str(empty),
                               "--date", "2026-10-30"])
            self.assertEqual(code, 1)
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
