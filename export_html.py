"""
Export a self-contained static HTML dashboard from 26.1 CSV data.
Output: site/index.html
"""

import os
import json
from datetime import datetime
import pandas as pd

DATA_PATH = "data/26.1_scores.csv"
OUT_DIR = "site"
OUT_FILE = os.path.join(OUT_DIR, "index.html")

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
    df["reps"] = pd.to_numeric(df["reps"], errors="coerce")
    df["time_seconds"] = pd.to_numeric(df["time_seconds"], errors="coerce")
    df["finished"] = df["time_seconds"].notna()
    return df


def compute_stats(reps):
    return {
        "count": len(reps),
        "median": float(reps.median()),
        "p75": float(reps.quantile(0.75)),
        "p90": float(reps.quantile(0.90)),
        "finished": 0,  # filled in separately
    }


def build_trace(reps, div_id, label, bar_color):
    """Return a Plotly JSON config dict for one histogram."""
    stats = compute_stats(reps)
    y_max = len(reps) * 0.06

    trace = {
        "x": reps.tolist(),
        "type": "histogram",
        "nbinsx": 60,
        "marker": {"color": bar_color, "opacity": 0.85},
        "hovertemplate": "Reps: %{x}<br>Athletes: %{y}<extra></extra>",
    }

    layout = {
        "xaxis": {"title": "Total Reps", "gridcolor": GRID_COLOR, "zerolinecolor": GRID_COLOR},
        "yaxis": {"title": "Athletes", "gridcolor": GRID_COLOR, "zerolinecolor": GRID_COLOR},
        "bargap": 0.03,
        "height": 420,
        "margin": {"l": 50, "r": 20, "t": 15, "b": 50},
        "plot_bgcolor": PLOT_BG,
        "paper_bgcolor": BG_COLOR,
        "font": {"color": TEXT_COLOR, "size": 12},
        "shapes": [
            {
                "type": "line", "x0": stats["median"], "x1": stats["median"],
                "y0": 0, "y1": 1, "yref": "paper",
                "line": {"color": MEDIAN_COLOR, "width": 2, "dash": "dash"},
            },
            {
                "type": "line", "x0": stats["p75"], "x1": stats["p75"],
                "y0": 0, "y1": 1, "yref": "paper",
                "line": {"color": QF_COLOR, "width": 2, "dash": "dash"},
            },
            {
                "type": "line", "x0": stats["p90"], "x1": stats["p90"],
                "y0": 0, "y1": 1, "yref": "paper",
                "line": {"color": P90_COLOR, "width": 2, "dash": "dash"},
            },
        ],
        "annotations": [
            {
                "x": stats["median"], "y": y_max, "text": f"Median: {stats['median']:.0f}",
                "showarrow": False, "yshift": 10,
                "font": {"color": MEDIAN_COLOR, "size": 13, "family": "Arial Black"},
            },
            {
                "x": stats["p75"], "y": y_max * 0.85, "text": f"Top 25%: {stats['p75']:.0f}",
                "showarrow": False, "yshift": 10,
                "font": {"color": QF_COLOR, "size": 13, "family": "Arial Black"},
            },
            {
                "x": stats["p90"], "y": y_max * 0.7, "text": f"Top 10%: {stats['p90']:.0f}",
                "showarrow": False, "yshift": 10,
                "font": {"color": P90_COLOR, "size": 13, "family": "Arial Black"},
            },
        ],
    }

    return trace, layout, stats


def render_html(men_reps, women_reps, men_finished, women_finished, total, total_registered, collected_at):
    men_trace, men_layout, men_stats = build_trace(men_reps, "chart-men", "Men", BAR_COLOR_MEN)
    women_trace, women_layout, women_stats = build_trace(women_reps, "chart-women", "Women", BAR_COLOR_WOMEN)
    men_stats["finished"] = men_finished
    women_stats["finished"] = women_finished

    def stats_line(label, s):
        return (
            f'{label} Rx\'d &middot; {s["count"]:,} athletes &middot; '
            f'Median <b style="color:{MEDIAN_COLOR}">{s["median"]:.0f}</b> &middot; '
            f'Top 25% <b style="color:{QF_COLOR}">{s["p75"]:.0f}+</b> &middot; '
            f'Top 10% <b style="color:{P90_COLOR}">{s["p90"]:.0f}+</b> &middot; '
            f'Finished <b>{s["finished"]}</b>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CrossFit Open 26.1</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: {BG_COLOR}; color: {TEXT_COLOR}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
  .wrap {{ max-width: 1400px; margin: 0 auto; padding: 1.5rem 1rem; }}
  h1 {{ text-align: center; font-size: 1.8rem; margin-bottom: 0.8rem; }}
  .row {{ display: flex; gap: 1.5rem; }}
  .col {{ flex: 1; min-width: 0; }}
  .stats {{ text-align: center; color: {SUBTITLE_COLOR}; font-size: 0.95rem; margin-bottom: 0.4rem; }}
  .chart {{ width: 100%; }}
  .footer {{ text-align: center; color: {SUBTITLE_COLOR}; font-size: 0.75rem; margin-top: 1rem; }}
  @media (max-width: 800px) {{
    .row {{ flex-direction: column; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <h1>CROSSFIT OPEN 26.1</h1>
  <div class="row">
    <div class="col">
      <p class="stats">{stats_line("Men", men_stats)}</p>
      <div id="chart-men" class="chart"></div>
    </div>
    <div class="col">
      <p class="stats">{stats_line("Women", women_stats)}</p>
      <div id="chart-women" class="chart"></div>
    </div>
  </div>
  <p class="footer">{total:,} Rx'd scores / {total_registered:,} registered athletes &middot; Data from c3po.crossfit.com &middot; Collected {collected_at}</p>
</div>
<script>
Plotly.newPlot("chart-men",  [{json.dumps(men_trace)}],  {json.dumps(men_layout)},  {{responsive:true, displayModeBar:false}});
Plotly.newPlot("chart-women",[{json.dumps(women_trace)}], {json.dumps(women_layout)}, {{responsive:true, displayModeBar:false}});
</script>
</body>
</html>"""


def main():
    df = load_data()
    men = df[df["gender"] == "M"]
    women = df[df["gender"] == "F"]
    men_reps = men["reps"].dropna()
    women_reps = women["reps"].dropna()

    collected_at = datetime.fromtimestamp(
        os.path.getmtime(DATA_PATH)
    ).strftime("%Y-%m-%d %H:%M")

    total_registered = 0
    for meta_file in ["data/men_rx_meta.json", "data/women_rx_meta.json"]:
        if os.path.exists(meta_file):
            with open(meta_file) as f:
                total_registered += json.load(f)["total_competitors"]

    os.makedirs(OUT_DIR, exist_ok=True)
    html = render_html(
        men_reps, women_reps,
        int(men["finished"].sum()), int(women["finished"].sum()),
        len(df), total_registered, collected_at,
    )
    with open(OUT_FILE, "w") as f:
        f.write(html)
    print(f"Wrote {OUT_FILE} ({len(html):,} bytes)")
    print(f"  Men:   {len(men_reps):,} athletes, median {men_reps.median():.0f} reps")
    print(f"  Women: {len(women_reps):,} athletes, median {women_reps.median():.0f} reps")


if __name__ == "__main__":
    main()
