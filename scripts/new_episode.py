#!/usr/bin/env python3
"""Create a new episode planner draft from templates/episode-template.md.

Local-first and offline. Example:

  python3 scripts/new_episode.py --title "My bedroom studio" --number 4

Writes episodes/ep04_my-bedroom-studio.md (created if missing) and prints
the path. No network access, no external dependencies.
"""

import argparse
import datetime
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "templates" / "episode-template.md"


def slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Create a new episode planner draft.")
    parser.add_argument("--title", required=True,
                        help="working episode title")
    parser.add_argument("--number", required=True, type=int,
                        help="episode number (1, 2, 3, ...)")
    parser.add_argument("--date", default=None,
                        help="recording date YYYY-MM-DD (default: today)")
    parser.add_argument("--outdir", default="episodes",
                        help="output directory (default: episodes/)")
    args = parser.parse_args(argv)

    if args.number < 1:
        parser.error("--number must be 1 or greater")
    if args.number > 9999:
        parser.error("--number is implausibly large")

    if not TEMPLATE_PATH.exists():
        print("error: missing template %s" % TEMPLATE_PATH, file=sys.stderr)
        return 1

    date_str = args.date or datetime.date.today().isoformat()
    try:
        datetime.date.fromisoformat(date_str)
    except ValueError:
        parser.error("--date must be YYYY-MM-DD")

    slug = slugify(args.title) or "episode"
    filename = "ep%02d-%s.md" % (args.number, slug)
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    out_path = outdir / filename

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    filled = (template
              .replace("{{NUMBER}}", "%02d" % args.number)
              .replace("{{TITLE}}", args.title)
              .replace("{{DATE}}", date_str)
              .replace("{{SLUG}}", slug)
              .replace("[tmp: exactly one thing listeners should do]",
                       "The one thing listeners should do:")
              .replace("---\n---\n\n", ""))

    if out_path.exists():
        print("error: %s already exists (refusing to overwrite)" % out_path,
              file=sys.stderr)
        return 1

    out_path.write_text(filled, encoding="utf-8")
    print("created %s" % out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
