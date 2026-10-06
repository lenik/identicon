#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Invoked as:
#   bash scripts/uninstall-symlinks.sh SOURCE_ROOT BUILD_ROOT PREFIX BINDIR DATADIR MANDIR
set -euo pipefail
SOURCE_ROOT="${1:-${MESON_SOURCE_ROOT:-.}}"
BUILD_ROOT="${2:-${MESON_BUILD_ROOT:-.}}"
prefix="${3:-/usr/local}"
bindir="${4:-$prefix/bin}"
datadir="${5:-$prefix/share}"
mandir="${6:-$prefix/share/man}"
for p in "$bindir/identicon" "$mandir/man1/identicon.1" "$datadir/bash-completion/completions/identicon"
do
    if [ -L "$p" ]; then
        sudo rm -f "$p"
        printf "Removed %s\n" "$p"
    else
        printf "Skipped (not a symlink): %s\n" "$p"
    fi
done
