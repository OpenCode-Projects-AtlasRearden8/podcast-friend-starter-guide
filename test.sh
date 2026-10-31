#!/usr/bin/env sh
# Run the full test suite. Local-first: no network needed.
set -e
python3 -m unittest discover -s scripts/tests -v
