"""Tests for the dependency-free markdown renderer (scripts/mdrender.py)."""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import mdrender


class HeadingTests(unittest.TestCase):
    def test_h1_with_slug_id(self):
        html = mdrender.render("# Hello World")
        self.assertEqual(html, '<h1 id="hello-world">Hello World</h1>')

    def test_h2_h3_levels(self):
        html = mdrender.render("## level two\n### level three")
        self.assertIn('<h2 id="level-two">', html)
        self.assertIn('<h3 id="level-three">', html)

    def test_duplicate_headings_get_unique_ids(self):
        html = mdrender.render("## Same\n\n## Same")
        self.assertIn('id="same"', html)
        self.assertIn('id="same-2"', html)

    def test_heading_ids_recorded_for_anchor_validation(self):
        r = mdrender.Renderer()
        r.render("## The room\n## The gear")
        self.assertEqual(r.heading_ids, ["the-room", "the-gear"])


class InlineTests(unittest.TestCase):
    def test_bold_italic_code_link(self):
        html = mdrender.render("a **b** c *d* e `f` [t](u.md)")
        self.assertIn("<strong>b</strong>", html)
        self.assertIn("<em>d</em>", html)
        self.assertIn("<code>f</code>", html)
        self.assertIn('<a href="u.md">t</a>', html)

    def test_link_href_transform(self):
        html = mdrender.render("[x](a.md) [y](b.html#s) [z](https://e.io)",
                               href_transform=lambda h: h[:-3] + ".html"
                               if h.endswith(".md") else h)
        self.assertIn('<a href="a.html">x</a>', html)
        self.assertIn('<a href="b.html#s">y</a>', html)
        self.assertIn('<a href="https://e.io">z</a>', html)

    def test_code_span_contents_untouched_by_emphasis(self):
        html = mdrender.render("`not *real* `code` here`")
        self.assertIn("<code>not *real* ", html)
        self.assertNotIn("<em>", html)

    def test_html_is_escaped(self):
        html = mdrender.render("<script>alert(1)</script>")
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_plosive_style_text_is_safe(self):
        html = mdrender.render("A & B < C > D \" E")
        self.assertIn("A &amp; B &lt; C &gt; D \" E", html)


class BlockTests(unittest.TestCase):
    def test_paragraph_joins_multiple_lines(self):
        html = mdrender.render("first line\nsecond line")
        self.assertEqual(html, "<p>first line second line</p>")

    def test_blockquote_renders_inner_content(self):
        html = mdrender.render("> **Note:** thing")
        self.assertIn("<blockquote>", html)
        self.assertIn("<strong>Note:</strong> thing", html)

    def test_blockquote_with_paragraphs(self):
        html = mdrender.render("> para one\n>\n> para two")
        self.assertEqual(html.count("<p>"), 2)

    def test_code_fence_escapes_content(self):
        html = mdrender.render("```python\nx < y & \"z\"\n```")
        self.assertIn("<pre><code", html)
        self.assertIn("x &lt; y &amp; ", html)

    def test_unterminated_fence_raises(self):
        with self.assertRaises(mdrender.MarkdownError):
            mdrender.render("```python\nno end ever")

    def test_horizontal_rule(self):
        html = mdrender.render("a\n\n---\n\nb")
        self.assertIn("<hr>", html)

    def test_table_with_alignment(self):
        html = mdrender.render("| a | b |\n| --- | :-: |\n| 1 | 2 |")
        self.assertIn("<table>", html)
        self.assertIn('<th>a</th>', html)
        self.assertIn('style="text-align:center"', html)
        self.assertIn("<tbody>", html)


class ListTests(unittest.TestCase):
    def test_ordered_list_numbering_strict(self):
        html = mdrender.render("1. a\n2. b")
        self.assertEqual(html.count("<ol>"), 1)
        self.assertEqual(html.count("<li>"), 2)

    def test_loose_list_survives_blank_lines(self):
        html = mdrender.render("1. a\n\n2. b\n\n3. c")
        self.assertEqual(html.count("<ol>"), 1)
        self.assertEqual(html.count("<li>"), 3)

    def test_unordered_and_checkbox_items(self):
        html = mdrender.render("- [ ] open\n- [x] done")
        self.assertIn('class="todo"', html)
        self.assertIn("\u2610", html)
        self.assertIn("\u2611", html)

    def test_nested_list_inside_item(self):
        html = mdrender.render("- one\n  - one-a")
        self.assertIn("<ul>", html)
        self.assertIn("<li>one\n<ul>", html)
        self.assertIn("<li>one-a</li>", html)

    def test_kind_switch_same_level_makes_sibling_fragment(self):
        html = mdrender.render("- a\n  - b\n  1. c")
        self.assertIn("<ul>", html)
        self.assertIn("<ol>", html)
        self.assertIn("<li>c</li>", html)


class WorksheetIntegrationTests(unittest.TestCase):
    """Every real worksheet/chapter must render without renderer errors."""

    DOCS = pathlib.Path(__file__).resolve().parents[2] / "docs"

    def test_all_docs_render_and_slugs_unique(self):
        md_files = sorted(self.DOCS.rglob("*.md"))
        self.assertGreaterEqual(len(md_files), 14)
        for path in md_files:
            with self.subTest(path=path.name):
                r = mdrender.Renderer()
                body = r.render(path.read_text(encoding="utf-8"))
                self.assertIn("<h1", body)
                self.assertEqual(len(r.heading_ids), len(set(r.heading_ids)),
                                 "duplicate heading slug in %s" % path.name)
                self.assertNotIn("\x00", body)


if __name__ == "__main__":
    unittest.main()
