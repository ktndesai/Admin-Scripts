#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ $EUID -ne 0 ]]; then
  echo "Run this script with sudo: sudo ./build.sh" >&2
  exit 1
fi
command -v lb >/dev/null || { echo "live-build is not installed. Run: sudo apt install live-build" >&2; exit 1; }

lb clean --purge || true
lb config
lb build

mkdir -p build
if [[ -f live-image-amd64.hybrid.iso ]]; then
  cp -f live-image-amd64.hybrid.iso build/IT-Preboot-v1.iso
  echo "Built: $(pwd)/build/IT-Preboot-v1.iso"
else
  echo "Build completed but expected ISO was not found." >&2
  exit 1
fi
