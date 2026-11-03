#!/bin/sh
exec python3 "$(dirname "$0")/lid-upower.py" "${1:-watch}"
