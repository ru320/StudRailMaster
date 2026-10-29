#!/bin/sh
# macOS: per Doppelklick im Finder startbar, macht dasselbe wie start.sh.
exec "$(dirname "$0")/start.sh" "$@"
