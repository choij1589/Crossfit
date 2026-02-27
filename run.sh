#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

source venv/bin/activate

echo "=== Scraping leaderboard ==="
python scraper.py

echo ""
echo "=== Exporting HTML ==="
python export_html.py

echo ""
echo "Done! Open site/index.html to preview."
