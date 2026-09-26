#!/usr/bin/env bash
# Installs a local k6 binary into loadtest/bin/k6 (idempotent). No sudo/system
# install required -- add loadtest/bin to PATH, or invoke ./bin/k6 directly.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$SCRIPT_DIR/bin"
K6_VERSION="v2.3.0"

if [ -x "$BIN_DIR/k6" ]; then
  echo "k6 already installed at $BIN_DIR/k6 ($("$BIN_DIR/k6" version))"
  exit 0
fi

ARCH="$(uname -m)"
case "$ARCH" in
  x86_64) K6_ARCH="amd64" ;;
  aarch64|arm64) K6_ARCH="arm64" ;;
  *) echo "Unsupported architecture: $ARCH" >&2; exit 1 ;;
esac

TARBALL="k6-${K6_VERSION}-linux-${K6_ARCH}.tar.gz"
URL="https://github.com/grafana/k6/releases/download/${K6_VERSION}/${TARBALL}"

mkdir -p "$BIN_DIR"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "Downloading $URL ..."
curl -fsSL "$URL" -o "$TMP_DIR/$TARBALL"
tar -xzf "$TMP_DIR/$TARBALL" -C "$TMP_DIR"
cp "$TMP_DIR/k6-${K6_VERSION}-linux-${K6_ARCH}/k6" "$BIN_DIR/k6"
chmod +x "$BIN_DIR/k6"

echo "Installed k6 $("$BIN_DIR/k6" version) to $BIN_DIR/k6"
