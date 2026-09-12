#!/usr/bin/env bash
set -euo pipefail
python3 -m pip install --upgrade pip
python3 -m pip install -e '.[local,dev]'
python3 -m PyInstaller --noconfirm --clean infra/FinduptoAI.spec
mkdir -p dist/FinduptoAI/models dist/FinduptoAI/data
echo 'Build complete: dist/FinduptoAI/'
