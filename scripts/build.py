#!/usr/bin/env python3
"""Build the static HTML site for the Podcast Friend Starter Guide.

Local-first: pure Python standard library, no network access, no installs.

  python3 scripts/build.py            # build into site/
  python3 scripts/build.py --out DIR  # build elsewhere (used by tests)
  python3 scripts/build.py --docs DIR # build from another docs directory

What it does:
  * renders every docs/*.md (chapters, worksheets, glossary) to HTML
  * generates index.html with a calm overview of chapters and worksheets
  * validates every internal link and #anchor in the generated site
  * exits non-zero when anything is broken; prints a summary otherwise
"""

import argparse
import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import mdrender  # noqa: E402

SHOW_NAME = "Podcast Friend Starter Guide"
SHOW_SUBTITLE = "A calm manual for starting a small podcast or audio show"
FOOTER_NOTE = ("Local-first and tested. No network needed to read, build, "
               "or test this guide.")
HUB_URL = "https://dylanasdale.github.io/"

CHAPTERS = [
    ("00-introduction.md",
     "A friendly guide for authors and one-person LLCs: what this manual is, "
     "who it is for, and how the calm method fits together."),
    ("01-what-to-say-before-you-buy-anything.md",
     "Write your one-sentence promise, list ten episodes, and record three "
     "practice takes before spending a dollar."),
    ("02-bedroom-recording-on-a-budget.md",
     "Turn your bedroom into a good-enough studio for free: room, mic "
     "technique, levels, and file habits."),
    ("03-free-editing-and-hosting-compared.md",
     "Audacity vs GarageBand vs the rest; free podcast hosts compared; and "
     "who really owns your RSS feed."),
    ("04-episode-structure-you-can-sustain.md",
     "The five-part skeleton, batch recordings, and the ten-minute planner "
     "that keeps shows alive past month three."),
    ("05-ai-transcripts-and-show-notes-with-verification.md",
     "Local AI transcription, a show-notes template, and the non-negotiable "
     "human verification checklist."),
    ("06-guest-etiquette.md",
     "Invite, prep, consent, record, edit, publish, thank-you: the full "
     "courtesy loop, with email templates."),
    ("07-consistency-without-burnout.md",
     "Cadence you can keep, seasons with endings, banked episodes, and the "
     "edges that actually cause burnout."),
    ("08-quitting-politely.md",
     "Podfade versus a real goodbye: how to end a show deliberately, kindly, "
     "and with your dignity intact."),
]

WORKSHEETS = [
    ("worksheets/show-on-a-page.md",
     "One page with your show's promise, cadence, LLC lines, and spend rule."),
    ("worksheets/episode-planner.md",
     "The ten-minute fill-in sheet used before every single recording."),
    ("worksheets/gear-budget.md",
     "The buy-nothing-first inventory and the earned-purchase ladder."),
    ("worksheets/transcript-verification-checklist.md",
     "Run before every AI-drafted transcript or show note publishes."),
]

GLOSSARY = ("glossary.md",
            "Every piece of jargon in the guide, explained like a friend would.")

PAGE_ORDER = ([name for name, _ in CHAPTERS] + [GLOSSARY[0]]
              + [name for name, _ in WORKSHEETS])


def md_to_href(href):
    """Rewrite .md links to .html; keep http(s)://, mailto:, and # anchors."""
    if href.startswith(("http://", "https://", "mailto:", "#")):
        return href
    if href.endswith(".md"):
        return href[:-3] + ".html"
    return href


def extract_title(text):
    for line in text.splitlines():
        m = re.match(r"^#\s+(.*)$", line)
        if m:
            return m.group(1).strip()
    return None


def nav_label(name):
    if name == "glossary.md":
        return "Glossary"
    if name.startswith("worksheets/"):
        label = name.split("/")[-1].removesuffix(".md").replace("-", " ")
        return "Worksheet: " + label.title()
    stem = name.removesuffix(".md")
    return "Ch. %s" % stem.split("-", 1)[0]


def relative_url(current_page_path, docs_name):
    """URL from the current output page to another rendered docs page."""
    depth = len(current_page_path.replace("\\", "/").split("/")) - 1
    return ("../" * depth) + md_to_href(docs_name)


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="%(description)s">
<title>%(title)s</title>
<link rel="stylesheet" href="%(assets)s">
<link rel="icon" href="data:,">
</head>
<body>
<header class="site-head">
  <p class="site-title"><a href="%(base)s">%(show_name)s</a></p>
  <p class="site-note">%(show_subtitle)s</p>
</header>
<nav class="site-nav" aria-label="Site pages">
  <ul>
%(nav)s
  </ul>
</nav>
<main>
%(body)s
%(pagenav)s
</main>
<footer class="site-foot">
  <p>&copy; 2026 Asdale Dynamics, LLC &middot; MIT license &middot;
  companion to the <strong>audiobook-recording handbook</strong> &middot;
  <a href="%(hub_url)s">dylanasdale.github.io</a></p>
  <p class="small">%(footer_note)s</p>
  <p class="small">Built %(build_date)s</p>
</footer>
</body>
</html>
"""


def render_page(page_rel_path, body, title, description,
                nav_active=None, prev_page=None, next_page=None, build_date=None):
    depth = len(page_rel_path.replace("\\", "/").split("/")) - 1
    base = "./" if depth == 0 else "../" * depth
    assets = base + "assets/style.css"

    nav_items = []
    for name in PAGE_ORDER:
        label = nav_label(name)
        href = relative_url(page_rel_path, name)
        cls = ' class="current"' if nav_active == name else ""
        nav_items.append('<li%s><a href="%s">%s</a></li>'
                         % (cls, href, html.escape(label)))
    nav_html = ("\n".join(nav_items) if depth == 0
                else "\n".join(nav_items))

    links = []
    if prev_page:
        links.append('<a class="prev" href="%s">&larr; %s</a>'
                     % (relative_url(page_rel_path, prev_page[0]),
                        html.escape(prev_page[1])))
    links.append('<a class="up" href="%s">Index</a>' % (base + "index.html",))
    if next_page:
        links.append('<a class="next" href="%s">%s &rarr;</a>'
                     % (relative_url(page_rel_path, next_page[0]),
                        html.escape(next_page[1])))
    pagenav_html = '<nav class="pagenav">%s</nav>' % "\n".join(links)

    return PAGE_TEMPLATE % {
        "title": html.escape(title),
        "description": html.escape(description, quote=True),
        "assets": html.escape(assets, quote=True),
        "base": base,
        "show_name": SHOW_NAME,
        "show_subtitle": SHOW_SUBTITLE,
        "nav": nav_html,
        "body": body,
        "pagenav": pagenav_html,
        "hub_url": HUB_URL,
        "footer_note": FOOTER_NOTE,
        "build_date": build_date or "local build",
    }


def build(docs_dir, out_dir, build_date=None):
    docs_dir = pathlib.Path(docs_dir)
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    page_specs = ([(name, "chapter", desc) for name, desc in CHAPTERS]
                  + [(GLOSSARY[0], "glossary", GLOSSARY[1])]
                  + [(name, "worksheet", desc) for name, desc in WORKSHEETS])

    outputs = {}
    for name, kind, desc in page_specs:
        src = docs_dir / name
        if not src.exists():
            raise SystemExit("missing required doc: %s" % (docs_dir / name))
        text = src.read_text(encoding="utf-8")
        renderer = mdrender.Renderer(href_transform=md_to_href)
        body = renderer.render(text)
        title = extract_title(text) or name
        page_path = name.removesuffix(".md") + ".html"
        outputs[name] = {
            "path": page_path,
            "body": body,
            "title": title,
            "desc": desc,
            "kind": kind,
            "anchors": set(renderer.heading_ids),
        }

    names_ordered = PAGE_ORDER
    for idx, name in enumerate(names_ordered):
        info = outputs[name]
        prev_entry, next_entry = None, None
        if info["kind"] == "chapter":
            if idx > 0 and names_ordered[idx - 1] in outputs:
                p_name = names_ordered[idx - 1]
                prev_entry = (p_name, short_title(docs_dir, p_name))
            if idx + 1 < len(names_ordered) and names_ordered[idx + 1] in outputs:
                n_name = names_ordered[idx + 1]
                next_entry = (n_name, short_title(docs_dir, n_name))
        page = render_page(
            info["path"], info["body"], info["title"], info["desc"],
            nav_active=name, prev_page=prev_entry, next_page=next_entry,
            build_date=build_date)
        target = out_dir / info["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page, encoding="utf-8")

    index_body = build_index_body(docs_dir)
    index_html = render_page(
        "index.html", index_body,
        "%s — %s" % (SHOW_NAME, SHOW_SUBTITLE), SHOW_SUBTITLE,
        build_date=build_date)
    (out_dir / "index.html").write_text(index_html, encoding="utf-8")

    style_src = ROOT / "scripts" / "assets" / "style.css"
    assets_out = out_dir / "assets"
    assets_out.mkdir(exist_ok=True)
    (assets_out / "style.css").write_text(style_src.read_text(encoding="utf-8"),
                                          encoding="utf-8")

    errors = validate_links(out_dir)
    return outputs, errors


def short_title(docs_dir, docs_name):
    if docs_name == "glossary.md":
        return "Glossary"
    text = (docs_dir / docs_name).read_text(encoding="utf-8")
    title = extract_title(text) or docs_name
    for chapter_name, _ in CHAPTERS:
        if docs_name == chapter_name:
            return title
    return "Worksheet: " + title


def build_index_body(docs_dir):
    parts = ['<section class="hero">',
             "<h1>Start a small podcast, calmly.</h1>",
             '<p class="lede">A friend\u2019s manual for authors and one-person '
             "LLCs: what to say before you buy anything, bedroom recording on a "
             "budget, free editing and hosting compared, an episode structure "
             "you can sustain, AI transcripts you actually verify, guest "
             "etiquette, consistency without burnout &mdash; and how to quit "
             "politely if the fun stops.</p>",
             '<p class="small">Published by Asdale Dynamics, LLC &middot; plain '
             'English, never condescending &middot; free tools first</p>',
             "</section>"]

    parts.append('<section class="cards">')
    parts.append("<h2>The nine chapters</h2>")
    for idx, (name, desc) in enumerate(CHAPTERS, start=1):
        title = extract_title((docs_dir / name).read_text(encoding="utf-8"))
        number_label = "Start here" if idx == 1 else "Chapter %d" % (idx - 1)
        parts.append('<a class="card" href="%s"><span class="card-no">%s</span>'
                     '<span class="card-title">%s</span>'
                     '<span class="card-desc">%s</span></a>'
                     % (md_to_href(name), number_label,
                        html.escape(title), html.escape(desc)))
    parts.append('<a class="card card-wide" href="%s"><span class="card-no">Reference</span>'
                 '<span class="card-title">Glossary</span>'
                 '<span class="card-desc">%s</span></a>'
                 % (md_to_href(GLOSSARY[0]), html.escape(GLOSSARY[1])))
    parts.append("</section>")

    parts.append('<section class="cards worksheets">')
    parts.append("<h2>The four worksheets</h2>")
    for name, desc in WORKSHEETS:
        title = extract_title((docs_dir / name).read_text(encoding="utf-8"))
        parts.append('<a class="card" href="%s"><span class="card-no">Worksheet</span>'
                     '<span class="card-title">%s</span>'
                     '<span class="card-desc">%s</span></a>'
                     % (md_to_href(name), html.escape(title), html.escape(desc)))
    parts.append("</section>")

    parts.append('<section class="companion">')
    parts.append("<h2>Companions</h2>")
    parts.append("<p>This guide covers the <em>show</em> around your recording. "
                 "For the recording craft itself &mdash; performance, breath, "
                 "narration &mdash; see its sibling project, the "
                 "<strong>audiobook-recording handbook</strong>, and the whole "
                 "library of plain-English AI manuals at "
                 '<a href="%s">dylanasdale.github.io</a> (the hub for '
                 "<em>The Massive AI Manual</em> and everything published by "
                 "Asdale Dynamics, LLC).</p>" % HUB_URL)
    parts.append("</section>")

    parts.append('<section class="howto">')
    parts.append("<h2>Reading offline</h2>")
    parts.append("<p>This site is a static build: no cookies, no analytics, no "
                 "accounts, no JavaScript. Open <code>site/index.html</code> "
                 "in any browser, or rebuild it any time with "
                 "<code>./build.sh</code>. The README has build and test "
                 "commands.</p>")
    parts.append("</section>")
    return "\n".join(parts)


def validate_links(out_dir):
    """Every relative href and #anchor in the generated site must resolve."""
    errors = []
    for page in sorted(pathlib.Path(out_dir).rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        rel = page.relative_to(out_dir).as_posix()
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith(("http://", "https://", "mailto:", "data:")):
                continue
            anchor = None
            if "#" in href:
                target, href_anchor = href.split("#", 1)
                anchor = href_anchor
            else:
                target = href
            if target:
                target_file = page.parent / target
                if not target_file.exists():
                    errors.append("%s: broken link -> %s" % (rel, href))
                    continue
            else:
                target_file = page
            if anchor:
                doc = target_file.read_text(encoding="utf-8")
                if ('id="%s"' % anchor) not in doc:
                    errors.append("%s: missing anchor -> %s" % (rel, href))
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build the static HTML site.")
    parser.add_argument("--out", default=str(ROOT / "site"),
                        help="output directory (default: site/)")
    parser.add_argument("--docs", default=str(ROOT / "docs"),
                        help="docs directory (default: docs/)")
    parser.add_argument("--date", default=None,
                        help="build date stamp (default: today)")
    args = parser.parse_args(argv)

    import datetime
    build_date = args.date or datetime.date.today().isoformat()
    try:
        _outputs, errors = build(args.docs, args.out, build_date=build_date)
    except SystemExit as exc:
        print("build failed: %s" % exc, file=sys.stderr)
        return 1
    if errors:
        for err in errors:
            print("ERROR: %s" % err, file=sys.stderr)
        print("build failed with %d validation error(s)" % len(errors),
              file=sys.stderr)
        return 1
    pages = len(list(pathlib.Path(args.out).rglob("*.html")))
    print("OK: built %d pages into %s" % (pages, args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
