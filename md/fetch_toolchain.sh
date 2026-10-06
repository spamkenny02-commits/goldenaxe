#!/bin/sh
set -eu
DEST=${1:-"$PWD/md/toolchain"}
URL='https://github.com/EythorE/m68k-elf-toolchain/releases/download/toolchain-latest/m68k-elf-toolchain-x86_64-linux.tar.gz'
if [ -x "$DEST/bin/m68k-elf-gcc" ]; then
  "$DEST/bin/m68k-elf-gcc" --version | head -1
  exit 0
fi
mkdir -p "$DEST"
tmp=${TMPDIR:-/tmp}/m68k-elf-toolchain.$$.tar.gz
trap 'rm -f "$tmp"' EXIT INT TERM
curl -fL "$URL" -o "$tmp"
# The upstream toolchain-latest tag is intentionally moving.  Pin a digest in
# CI/release builds by exporting TOOLCHAIN_SHA256; local builds may follow the
# latest verified-by-TLS release asset.
if [ -n "${TOOLCHAIN_SHA256:-}" ]; then
  printf '%s  %s\n' "$TOOLCHAIN_SHA256" "$tmp" | sha256sum -c -
fi
tar xzf "$tmp" --no-same-owner --strip-components=1 -C "$DEST"
test "$("$DEST/bin/m68k-elf-gcc" -dumpmachine)" = m68k-elf
"$DEST/bin/m68k-elf-gcc" --version | head -1
