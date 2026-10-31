#!/usr/bin/env sh
# Build the static HTML site into site/. Local-first: no network needed.
set -e
exec python3 scripts/build.py "$@"
