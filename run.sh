#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

source /afs/cern.ch/user/c/choij/private/crossfit-venv/bin/activate

OUTDIR="site"
if [[ "${1:-}" == "--open26p1" ]]; then
    OUTDIR="Open26p1"
fi

echo "=== Scraping leaderboard ==="
python scraper.py

echo ""
echo "=== Exporting HTML ==="
python export_html.py --outdir "$OUTDIR"

echo ""
echo "Done! Open ${OUTDIR}/index.html to preview."
