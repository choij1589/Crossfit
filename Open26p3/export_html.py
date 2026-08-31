"""
Export a self-contained static HTML dashboard from 26.3 CSV data.
Output: site/index.html
"""

import argparse
import os
import json
from datetime import datetime
import numpy as np
import pandas as pd

DATA_PATH = "data/26.3_scores.csv"
DEFAULT_OUT_DIR = "."

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
    if "scaled" not in df.columns:
        df["scaled"] = False
    else:
        df["scaled"] = df["scaled"].fillna(False).astype(bool)
    return df


def compute_stats(reps):
    return {
        "count": len(reps),
        "median": float(reps.median()),
        "p75": float(reps.quantile(0.75)),
        "p90": float(reps.quantile(0.90)),
        "finished": 0,  # filled in separately
    }


def bootstrap_quantiles(reps, quantiles=(0.50, 0.75, 0.90), n_boot=2000, ci=95, seed=42, n_scaled=0):
    """Estimate quantiles with bootstrap 95% confidence intervals.

    When n_scaled > 0, quantiles are computed over the total population
    (Rx'd + Scaled), treating all Scaled athletes as below all Rx'd.
    The adjusted Rx'd quantile is: q_adj = (q * (n_rx + n_scaled) - n_scaled) / n_rx
    """
    rng = np.random.default_rng(seed)
    n = len(reps)
    total = n + n_scaled

    # Map each overall quantile to its equivalent within the Rx'd distribution
    adj = {}
    for q in quantiles:
        if n_scaled > 0 and total > 0:
            q_adj = (q * total - n_scaled) / n
            q_adj = max(0.0, min(1.0, q_adj))
        else:
            q_adj = q
        adj[q] = q_adj

    boot_qs = {q: [] for q in quantiles}
    for _ in range(n_boot):
        sample = rng.choice(reps, size=n, replace=True)
        for q in quantiles:
            boot_qs[q].append(np.quantile(sample, adj[q]))
    alpha = (100 - ci) / 2
    result = {}
    for q in quantiles:
        dist = np.array(boot_qs[q])
        result[q] = {
            "point": float(np.quantile(reps, adj[q])),
            "lo": float(np.percentile(dist, alpha)),
            "hi": float(np.percentile(dist, 100 - alpha)),
        }
    return result


def ci_table(men_ci, women_ci, men_stats, women_stats, men_reg, women_reg,
             men_scaled_reg, women_scaled_reg, men_scaled_stats=None, women_scaled_stats=None):
    """Build an HTML quantile table with bootstrap CIs and participation context."""
    rows_data = [
        ("Top 10%", 0.90),
        ("Top 25%", 0.75),
        ("Median", 0.50),
    ]

    def fmt_ci(ci_dict):
        return (
            f'<span class="ci-point">{ci_dict["point"]:.0f}</span>'
            f'<span class="ci-range"> [{ci_dict["lo"]:.0f}, {ci_dict["hi"]:.0f}]</span>'
        )

    def fmt_reg(submitted, registered):
        pct = submitted / registered * 100 if registered else 0
        return f'{submitted:,} <span class="ci-pct">({pct:.0f}%)</span>'

    table_rows = ""
    for label, q in rows_data:
        table_rows += (
            f'<tr><td class="ci-label">{label}</td>'
            f'<td class="ci-men">{fmt_ci(men_ci[q])}</td>'
            f'<td class="ci-women">{fmt_ci(women_ci[q])}</td></tr>\n'
        )

    total_men_reg = men_reg + men_scaled_reg
    total_women_reg = women_reg + women_scaled_reg

    table_rows += (
        f'<tr class="ctx-row"><td class="ci-label">Rx\'d</td>'
        f'<td class="ci-men">{fmt_reg(men_stats["count"], total_men_reg)}</td>'
        f'<td class="ci-women">{fmt_reg(women_stats["count"], total_women_reg)}</td></tr>\n'
    )

    men_sc_count = men_scaled_stats["count"] if men_scaled_stats else 0
    women_sc_count = women_scaled_stats["count"] if women_scaled_stats else 0
    table_rows += (
        f'<tr class="ctx-row"><td class="ci-label">Scaled</td>'
        f'<td class="ci-men">{fmt_reg(men_sc_count, total_men_reg)}</td>'
        f'<td class="ci-women">{fmt_reg(women_sc_count, total_women_reg)}</td></tr>\n'
    )

    table_rows += (
        f'<tr class="ctx-row"><td class="ci-label">Registered</td>'
        f'<td class="ci-men">{total_men_reg:,}</td>'
        f'<td class="ci-women">{total_women_reg:,}</td></tr>\n'
    )

    return f"""<div class="ci-table-wrap"><table class="ci-table">
<thead><tr><th></th><th class="ci-men">Men</th><th class="ci-women">Women</th></tr></thead>
<tbody>
{table_rows}</tbody>
</table></div>
<p class="ci-footnote">All divisions combined. Brackets denote 95% CL (bootstrap).</p>"""


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


def render_html(men_reps, women_reps, men_finished, women_finished,
                total, total_registered, collected_at, ci_table_html="",
                men_sc_reps=None, women_sc_reps=None,
                men_sc_finished=0, women_sc_finished=0):
    men_trace, men_layout, men_stats = build_trace(men_reps, "chart-men", "Men Rx'd", BAR_COLOR_MEN)
    women_trace, women_layout, women_stats = build_trace(women_reps, "chart-women", "Women Rx'd", BAR_COLOR_WOMEN)
    men_stats["finished"] = men_finished
    women_stats["finished"] = women_finished

    # Build Scaled histograms
    has_scaled = men_sc_reps is not None and len(men_sc_reps) > 0
    sc_html = ""
    sc_script = ""
    if has_scaled:
        men_sc_trace, men_sc_layout, men_sc_stats = build_trace(men_sc_reps, "chart-men-sc", "Men Scaled", BAR_COLOR_MEN)
        women_sc_trace, women_sc_layout, women_sc_stats = build_trace(women_sc_reps, "chart-women-sc", "Women Scaled", BAR_COLOR_WOMEN)
        men_sc_stats["finished"] = men_sc_finished
        women_sc_stats["finished"] = women_sc_finished

    def stats_line(label, s):
        return (
            f'{label} &middot; {s["count"]:,} athletes &middot; '
            f'Median <b style="color:{MEDIAN_COLOR}">{s["median"]:.0f}</b> &middot; '
            f'Top 25% <b style="color:{QF_COLOR}">{s["p75"]:.0f}+</b> &middot; '
            f'Top 10% <b style="color:{P90_COLOR}">{s["p90"]:.0f}+</b> &middot; '
            f'Finished <b>{s["finished"]}</b>'
        )

    if has_scaled:
        sc_html = f"""
  <h2 class="section-title">Scaled Distribution</h2>
  <div class="row">
    <div class="col">
      <p class="stats">{stats_line("Men Scaled", men_sc_stats)}</p>
      <div id="chart-men-sc" class="chart"></div>
    </div>
    <div class="col">
      <p class="stats">{stats_line("Women Scaled", women_sc_stats)}</p>
      <div id="chart-women-sc" class="chart"></div>
    </div>
  </div>"""
        sc_script = f"""
Plotly.newPlot("chart-men-sc",  [{json.dumps(men_sc_trace)}],  {json.dumps(men_sc_layout)},  cfg);
Plotly.newPlot("chart-women-sc",[{json.dumps(women_sc_trace)}], {json.dumps(women_sc_layout)}, cfg);"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CrossFit Open 26.3</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: {BG_COLOR}; color: {TEXT_COLOR}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
  .wrap {{ max-width: 1400px; margin: 0 auto; padding: 1.5rem 1rem; }}
  h1 {{ text-align: center; font-size: 1.8rem; margin-bottom: 0.8rem; }}
  .section-title {{ text-align: center; font-size: 1rem; color: #888; text-transform: uppercase; letter-spacing: 0.05em; margin: 1.5rem 0 0.5rem; }}
  .row {{ display: flex; gap: 1.5rem; }}
  .col {{ flex: 1; min-width: 0; }}
  .stats {{ text-align: center; color: {SUBTITLE_COLOR}; font-size: 0.95rem; margin-bottom: 0.4rem; }}
  .chart {{ width: 100%; }}
  .footer {{ text-align: center; color: {SUBTITLE_COLOR}; font-size: 0.75rem; margin-top: 1rem; }}
  .ci-table-wrap {{ overflow-x: auto; margin: 1.2rem auto 0; max-width: 700px; }}
  .ci-table {{ border-collapse: collapse; width: 100%; font-size: 0.85rem; }}
  .ci-table th, .ci-table td {{ padding: 0.35rem 0.6rem; border-bottom: 1px solid #e0e0e0; text-align: center; white-space: nowrap; }}
  .ci-table th {{ font-weight: 600; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.03em; }}
  .ci-table td.ci-label {{ text-align: left; font-weight: 600; white-space: nowrap; }}
  .ci-table th.ci-men, .ci-table td.ci-men {{ color: {BAR_COLOR_MEN}; font-weight: 600; }}
  .ci-table th.ci-women, .ci-table td.ci-women {{ color: {BAR_COLOR_WOMEN}; font-weight: 600; }}
  .ci-point {{ font-size: 0.85rem; }}
  .ci-range {{ font-size: 0.8rem; }}
  .ctx-row td.ci-label {{ color: {TEXT_COLOR}; font-weight: 500; }}
  .ci-pct {{ font-size: 0.8rem; }}
  .ci-footnote {{ text-align: center; color: #999; font-size: 0.75rem; margin-top: 0.3rem; }}
  @media (max-width: 800px) {{
    .row {{ flex-direction: column; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <h1>CROSSFIT OPEN 26.3</h1>
  <h2 class="section-title">Summary Statistics</h2>
  {ci_table_html}
  <h2 class="section-title">Rx'd Distribution</h2>
  <div class="row">
    <div class="col">
      <p class="stats">{stats_line("Men Rx'd", men_stats)}</p>
      <div id="chart-men" class="chart"></div>
    </div>
    <div class="col">
      <p class="stats">{stats_line("Women Rx'd", women_stats)}</p>
      <div id="chart-women" class="chart"></div>
    </div>
  </div>
  {sc_html}
  <p class="footer">{total + (len(men_sc_reps) + len(women_sc_reps) if men_sc_reps is not None else 0):,} submitted / {total_registered:,} registered &middot; Data from c3po.crossfit.com &middot; Collected {collected_at}</p>
</div>
<script>
var cfg = {{responsive:true, displayModeBar:false, staticPlot: window.innerWidth < 800}};
Plotly.newPlot("chart-men",  [{json.dumps(men_trace)}],  {json.dumps(men_layout)},  cfg);
Plotly.newPlot("chart-women",[{json.dumps(women_trace)}], {json.dumps(women_layout)}, cfg);
{sc_script}
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default=DEFAULT_OUT_DIR, help="Output directory")
    args = parser.parse_args()

    out_dir = args.outdir
    out_file = os.path.join(out_dir, "index.html")

    df = load_data()
    rx = df[~df["scaled"]]
    men = rx[rx["gender"] == "M"]
    women = rx[rx["gender"] == "F"]
    men_reps = men["reps"].dropna()
    women_reps = women["reps"].dropna()

    collected_at = datetime.fromtimestamp(
        os.path.getmtime(DATA_PATH)
    ).strftime("%Y-%m-%d %H:%M")

    # Load Rx'd registration metadata
    men_reg = women_reg = 0
    for label, var in [("men_rx", "men_reg"), ("women_rx", "women_reg")]:
        meta_file = f"data/{label}_meta.json"
        if os.path.exists(meta_file):
            with open(meta_file) as f:
                val = json.load(f)["total_competitors"]
            if var == "men_reg":
                men_reg = val
            else:
                women_reg = val
    total_registered = men_reg + women_reg

    # Load Scaled registration metadata
    men_scaled_reg = women_scaled_reg = 0
    for label, var in [("men_scaled", "men_scaled_reg"), ("women_scaled", "women_scaled_reg")]:
        meta_file = f"data/{label}_meta.json"
        if os.path.exists(meta_file):
            with open(meta_file) as f:
                val = json.load(f)["total_competitors"]
            if var == "men_scaled_reg":
                men_scaled_reg = val
            else:
                women_scaled_reg = val

    # Extract Scaled reps
    sc = df[df["scaled"]]
    men_sc = sc[sc["gender"] == "M"]
    women_sc = sc[sc["gender"] == "F"]
    men_sc_reps = men_sc["reps"].dropna()
    women_sc_reps = women_sc["reps"].dropna()

    # Count scored scaled athletes for total-population quantiles
    men_scaled_scored = len(men_sc_reps)
    women_scaled_scored = len(women_sc_reps)

    # Bootstrap quantile CIs (over Rx'd + Scaled total population)
    men_ci = bootstrap_quantiles(men_reps.values, n_scaled=men_scaled_scored)
    women_ci = bootstrap_quantiles(women_reps.values, n_scaled=women_scaled_scored)
    men_stats_for_table = compute_stats(men_reps)
    women_stats_for_table = compute_stats(women_reps)
    men_scaled_stats = compute_stats(men_sc_reps) if len(men_sc_reps) > 0 else {"count": 0}
    women_scaled_stats = compute_stats(women_sc_reps) if len(women_sc_reps) > 0 else {"count": 0}
    table_html = ci_table(men_ci, women_ci, men_stats_for_table, women_stats_for_table,
                          men_reg, women_reg, men_scaled_reg, women_scaled_reg,
                          men_scaled_stats=men_scaled_stats,
                          women_scaled_stats=women_scaled_stats)

    os.makedirs(out_dir, exist_ok=True)
    html = render_html(
        men_reps, women_reps,
        int(men["finished"].sum()), int(women["finished"].sum()),
        len(rx), total_registered, collected_at,
        ci_table_html=table_html,
        men_sc_reps=men_sc_reps, women_sc_reps=women_sc_reps,
        men_sc_finished=int(men_sc["finished"].sum()),
        women_sc_finished=int(women_sc["finished"].sum()),
    )
    with open(out_file, "w") as f:
        f.write(html)
    print(f"Wrote {out_file} ({len(html):,} bytes)")
    print(f"  Men:   {len(men_reps):,} athletes, median {men_reps.median():.0f} reps")
    print(f"  Women: {len(women_reps):,} athletes, median {women_reps.median():.0f} reps")


if __name__ == "__main__":
    main()
