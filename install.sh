#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if ! command -v python3 >/dev/null; then
    echo 'Python 3 is required: sudo pacman -S python OR sudo dnf install python3' >&2
    exit 1
fi
exec python3 scripts/install.py "$@"
