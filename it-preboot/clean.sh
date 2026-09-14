#!/bin/bash
set -e
cd "$(dirname "$0")"
sudo lb clean --purge
rm -rf build
