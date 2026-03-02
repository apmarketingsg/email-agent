#!/bin/bash
# Cron entry point for Namecheap shared hosting.
# Called by cPanel cron 3× daily; activates the virtualenv and runs one digest.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR" || exit 1

mkdir -p "$SCRIPT_DIR/data/logs"

LOG="$SCRIPT_DIR/data/logs/cron.log"

{
    echo "--- $(date '+%Y-%m-%d %H:%M:%S %Z') ---"
    "$SCRIPT_DIR/.venv/bin/python" main.py --once
} >> "$LOG" 2>&1
