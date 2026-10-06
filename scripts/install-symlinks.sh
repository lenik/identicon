#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Invoked as:
#   bash scripts/install-symlinks.sh SOURCE_ROOT BUILD_ROOT PREFIX BINDIR DATADIR MANDIR
set -euo pipefail
SOURCE_ROOT="${1:-${MESON_SOURCE_ROOT:-.}}"
BUILD_ROOT="${2:-${MESON_BUILD_ROOT:-.}}"
prefix="${3:-/usr/local}"
bindir="${4:-$prefix/bin}"
datadir="${5:-$prefix/share}"
mandir="${6:-$prefix/share/man}"
mkdir -p "$bindir" "$datadir/bash-completion/completions" "$mandir/man1" \
    "$datadir/identicon"
sudo ln -sfn "${BUILD_ROOT}/identicon" "$bindir/identicon"
sudo ln -sfn "${SOURCE_ROOT}/third_party/robohash" "$datadir/identicon/robohash"
sudo ln -sfn "${BUILD_ROOT}/identicon.1" "$mandir/man1/identicon.1"
sudo ln -sfn "${SOURCE_ROOT}/identicon.bash" "$datadir/bash-completion/completions/identicon"
printf "Symlinks installed under %s\n" "$prefix"
