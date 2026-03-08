"""
Export a self-contained static HTML dashboard from 26.2 CSV data.
Output: Open26p2/index.html
"""

import argparse
import os
import json
from datetime import datetime
import numpy as np
import pandas as pd

DATA_PATH = "data/26.2_scores.csv"
DEFAULT_OUT_DIR = "Open26p2"

# Colors (match dashboard.py)
BG_COLOR = "#ffffff"
PLOT_BG = "#f5f5f5"
BAR_COLOR_MEN = "#4a9eff"
BAR_COLOR_WOMEN = "#ff4b4b"
MEDIAN_COLOR = "#222222"
QF_COLOR = "#444444"
P90_COLOR = "#666666"
TEXT_COLOR = "#1a1a1a"
SUBTITLE_COLOR = "#555555"
GRID_COLOR = "#ddd"


def load_data():
    df = pd.read_csv(DATA_PATH)
    # TODO 26.2: Add workout-specific column parsing here
    if "scaled" not in df.columns:
        df["scaled"] = False
    else:
        df["scaled"] = df["scaled"].fillna(False).astype(bool)
    return df


def render_html(total, total_registered, collected_at):
    # TODO 26.2: Build histograms and stats based on 26.2 workout format
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CrossFit Open 26.2</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: {BG_COLOR}; color: {TEXT_COLOR}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
  .wrap {{ max-width: 1400px; margin: 0 auto; padding: 1.5rem 1rem; }}
  h1 {{ text-align: center; font-size: 1.8rem; margin-bottom: 0.8rem; }}
  .footer {{ text-align: center; color: {SUBTITLE_COLOR}; font-size: 0.75rem; margin-top: 1rem; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>CROSSFIT OPEN 26.2</h1>
  <!-- TODO 26.2: Add summary stats table -->
  <!-- TODO 26.2: Add distribution charts -->
  <p class="footer">{total:,} submitted / {total_registered:,} registered &middot; Data from c3po.crossfit.com &middot; Collected {collected_at}</p>
</div>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default=DEFAULT_OUT_DIR, help="Output directory")
    args = parser.parse_args()

    out_dir = args.outdir
    out_file = os.path.join(out_dir, "index.html")

    df = load_data()

    collected_at = datetime.fromtimestamp(
        os.path.getmtime(DATA_PATH)
    ).strftime("%Y-%m-%d %H:%M")

    total_registered = 0
    # TODO 26.2: Load registration metadata from data/*_meta.json

    os.makedirs(out_dir, exist_ok=True)
    html = render_html(len(df), total_registered, collected_at)
    with open(out_file, "w") as f:
        f.write(html)
    print(f"Wrote {out_file} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
