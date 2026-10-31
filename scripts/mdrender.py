"""Tiny dependency-free Markdown renderer for the Podcast Friend Starter Guide.

Local-first on purpose: no third-party packages, no network, no installs.
Supports the constructs used by this project's documentation:

  * ATX headings (# .. ######) with stable slug ids
  * fenced code blocks (```), contents escaped safely
  * blockquotes (may contain other blocks)
  * unordered and ordered lists with 2-space nesting; kind switches at the
    same indent level start a sibling list fragment
  * checkbox items (- [ ] / - [x]) rendered with unicode ballot glyphs
  * pipe tables with :---: alignment
  * horizontal rules (---)
  * inline: **bold**, *italic*, `code`, [links](target), ![images](src)
  * optional href_transform callable to rewrite link targets (used by the
    site builder to turn .md URLs into .html)

The full test suite in scripts/tests/ exercises every feature above.
"""

import html
import re


def slugify(text):
    """Stable, readable URL slug for a heading."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
HR_RE = re.compile(r"^\s{0,3}(?:-{3,}|\*{3,}|_{3,})\s*$")
FENCE_OPEN_RE = re.compile(r"^\s{0,3}(```|~~~)\s*(.*)$")
LIST_RE = re.compile(r"^( {0,6})([-*+]|\d+[.)])\s+(.*)$")
QUOTE_RE = re.compile(r"^\s{0,3}>\s?(.*)$")
TABLE_SEPARATOR_RE = re.compile(
    r"^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)+\|?\s*$")
CODESPAN_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*\s][^*]*?)\*(?!\*)")
CHECKBOX_RE = re.compile(r"^\[( |x|X)\]\s*(.*)$")

BOX_EMPTY = "\u2610"  # ballot box
BOX_DONE = "\u2611"   # ballot box with check


class MarkdownError(Exception):
    pass


class Renderer:
    def __init__(self, href_transform=None):
        self.href_transform = href_transform
        self.heading_ids = []
        self._used_ids = set()

    # ---- public -------------------------------------------------------
    def render(self, text):
        """Render a full markdown document to an HTML body fragment."""
        self.heading_ids = []
        self._used_ids = set()
        return self.render_lines(text.splitlines())

    def render_lines(self, lines):
        out = []
        i = 0
        n = len(lines)
        while i < n:
            line = lines[i]
            if not line.strip():
                i += 1
                continue

            if FENCE_OPEN_RE.match(line):
                i, block = self._code_block(lines, i)
                out.append(block)
                continue

            heading = HEADING_RE.match(line)
            if heading:
                level = len(heading.group(1))
                text_inner = heading.group(2).strip()
                body = self.inline(text_inner)
                slug = self._heading_id(text_inner)
                out.append('<h%d id="%s">%s</h%d>' % (level, slug, body, level))
                i += 1
                continue

            if HR_RE.match(line):
                out.append("<hr>")
                i += 1
                continue

            if QUOTE_RE.match(line):
                i, block = self._blockquote(lines, i)
                out.append(block)
                continue

            if "|" in line and i + 1 < n and TABLE_SEPARATOR_RE.match(lines[i + 1]):
                i, block = self._table(lines, i)
                out.append(block)
                continue

            if LIST_RE.match(line):
                i, block = self._list(lines, i)
                out.append(block)
                continue

            i, block = self._paragraph(lines, i)
            out.append(block)
        return "\n".join(out)

    # ---- blocks -------------------------------------------------------
    def _code_block(self, lines, i):
        fence = FENCE_OPEN_RE.match(lines[i])
        marker = fence.group(1)
        lang = (fence.group(2) or "").strip()
        i += 1
        buf = []
        while i < len(lines) and lines[i].strip() != marker.strip():
            buf.append(lines[i])
            i += 1
        if i >= len(lines):
            raise MarkdownError("unterminated %s code fence" % marker)
        i += 1  # consume the closing fence
        cls = ' class="language-%s"' % html.escape(lang, quote=True) if lang else ""
        inner = html.escape("\n".join(buf), quote=False)
        return i, "<pre><code%s>%s</code></pre>" % (cls, inner)

    def _blockquote(self, lines, i):
        buf = []
        while i < len(lines) and QUOTE_RE.match(lines[i]):
            buf.append(QUOTE_RE.match(lines[i]).group(1))
            i += 1
        body = self.render_lines(buf) if any(b.strip() for b in buf) else "&#8203;"
        return i, "<blockquote>\n%s\n</blockquote>" % body

    def _table(self, lines, i):
        header_cells = self._split_row(lines[i])
        aligns = [self._align(c) for c in self._split_row(lines[i + 1])]
        i += 2
        rows = []
        while i < len(lines) and "|" in lines[i] and lines[i].strip():
            rows.append(self._split_row(lines[i]))
            i += 1
        parts = ["<table>", "<thead>", "<tr>"]
        for idx, cell in enumerate(header_cells):
            parts.append("<th%s>%s</th>" % (
                aligns[idx] if idx < len(aligns) else "", self._td(cell)))
        parts.append("</tr>")
        parts.append("</thead>")
        if rows:
            parts.append("<tbody>")
            for row in rows:
                parts.append("<tr>")
                for idx, cell in enumerate(row):
                    parts.append("<td%s>%s</td>" % (
                        aligns[idx] if idx < len(aligns) else "", self._td(cell)))
                parts.append("</tr>")
            parts.append("</tbody>")
        parts.append("</table>")
        return i, "\n".join(parts)

    @staticmethod
    def _split_row(line):
        line = line.strip()
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]
        return [c.strip() for c in line.split("|")]

    @staticmethod
    def _align(cell):
        left = cell.startswith(":")
        right = cell.endswith(":")
        if left and right:
            return ' style="text-align:center"'
        if right:
            return ' style="text-align:right"'
        if left:
            return ' style="text-align:left"'
        return ""

    def _td(self, cell):
        return self.inline(cell)

    # ---- lists --------------------------------------------------------
    def _list(self, lines, i):
        entries = []
        pending_blank = False
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                # A blank separator between list items keeps the list open
                # (markdown "loose lists") as long as another item follows.
                if pending_blank:
                    break
                lookahead = i + 1
                while lookahead < len(lines) and not lines[lookahead].strip():
                    lookahead += 1
                if lookahead < len(lines) and LIST_RE.match(lines[lookahead]):
                    pending_blank = True
                    i += 1
                    continue
                break
            m = LIST_RE.match(line)
            if m:
                level = len(m.group(1)) // 2
                kind = "ol" if m.group(2)[0].isdigit() else "ul"
                entries.append((level, kind, m.group(3).strip()))
                pending_blank = False
                i += 1
                continue
            break
        fragments = []
        pos = 0
        while pos < len(entries):
            fragment, pos = self._build_list(entries, pos, entries[pos][0])
            fragments.append(fragment)
        return i, "\n".join(fragments)

    def _build_list(self, entries, pos, level):
        """Render one list starting at entries[pos] with the given level.

        Returns the html fragment and the updated position. Nested deeper
        lists are attached inside the previous item; a kind switch at the
        same level closes this fragment so the caller can render the next.
        """
        kind = entries[pos][1]
        items = []
        while pos < len(entries):
            lvl, k, content = entries[pos]
            if lvl < level:
                break
            if lvl > level:
                nested, pos = self._build_list(entries, pos, lvl)
                items[-1] = items[-1][:-len("</li>")] + "\n" + nested + "\n</li>"
                continue
            if k != kind:
                break
            check = CHECKBOX_RE.match(content)
            if check:
                glyph = BOX_DONE if check.group(1).lower() == "x" else BOX_EMPTY
                items.append(
                    '<li class="todo"><span class="box" aria-hidden="true">%s</span> %s</li>'
                    % (glyph, self.inline(check.group(2))))
            else:
                items.append("<li>%s</li>" % self.inline(content))
            pos += 1
        if not items:
            raise MarkdownError("empty list fragment at level %d" % level)
        return "<%s>\n%s\n</%s>" % (kind, "\n".join(items), kind), pos

    def _paragraph(self, lines, i):
        buf = []
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                break
            if (HEADING_RE.match(line) or HR_RE.match(line)
                    or QUOTE_RE.match(line) or LIST_RE.match(line)
                    or FENCE_OPEN_RE.match(line)
                    or ("|" in line and i + 1 < len(lines)
                        and TABLE_SEPARATOR_RE.match(lines[i + 1]))):
                break
            buf.append(line.strip())
            i += 1
        return i, "<p>%s</p>" % self.inline(" ".join(buf))

    def _heading_id(self, text_inner):
        raw = re.sub(r"[`*_\[\]]", "", text_inner)
        slug = slugify(raw) or "heading"
        base = slug
        n = 2
        while slug in self._used_ids:
            slug = "%s-%d" % (base, n)
            n += 1
        self._used_ids.add(slug)
        self.heading_ids.append(slug)
        return html.escape(slug, quote=True)

    # ---- inline -------------------------------------------------------
    def inline(self, text):
        t = html.escape(text, quote=False)

        # Stash code spans first so other rules never touch their contents.
        stash = []

        def sub_code(m):
            stash.append(m.group(1))
            return "\x00%d\x00" % (len(stash) - 1)

        t = re.sub(r"`([^`]+)`", sub_code, t)

        def transform_href(href):
            if self.href_transform:
                return self.href_transform(href)
            return href

        t = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)",
                   lambda m: '<img src="%s" alt="%s">' % (
                       html.escape(transform_href(m.group(2)), quote=True),
                       m.group(1)),
                   t)

        t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                   lambda m: '<a href="%s">%s</a>' % (
                       html.escape(transform_href(m.group(2)), quote=True),
                       m.group(1)),
                   t)

        t = BOLD_RE.sub(lambda m: "<strong>%s</strong>" % m.group(1), t)
        t = ITALIC_RE.sub(lambda m: "<em>%s</em>" % m.group(1), t)

        for idx, content in enumerate(stash):
            marker = "\x00%d\x00" % idx
            if marker not in t:
                raise MarkdownError("lost code span placeholder %d" % idx)
            t = t.replace(marker, "<code>%s</code>" % content)
        if "\x00" in t:
            raise MarkdownError("unresolved code span placeholder in output")
        return t


def render(text, href_transform=None):
    """Convenience function: render markdown text to an HTML body."""
    return Renderer(href_transform=href_transform).render(text)
