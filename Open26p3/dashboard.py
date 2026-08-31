"""
CrossFit Open 2026 – 26.3 Leaderboard Dashboard
Run: streamlit run dashboard.py
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="CrossFit Open 26.3", layout="centered", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
    .block-container { max-width: 600px !important; padding-top: 0.5rem !important; padding-bottom: 0 !important; }
    [data-testid="stSidebar"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    #MainMenu { display: none !important; }
    footer { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

DATA_PATH = "data/26.3_scores.csv"

BG_COLOR = "#0e1117"
BAR_COLOR = "#4a9eff"
MEDIAN_COLOR = "#ff4b4b"
QF_COLOR = "#00d47e"
ATHLETE_COLOR = "#ff6ec7"
TEXT_COLOR = "#fafafa"
SUBTITLE_COLOR = "#888888"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df["time_seconds"] = pd.to_numeric(df["time_seconds"], errors="coerce")
    df["reps"] = pd.to_numeric(df["reps"], errors="coerce")
    df["finished"] = df["time_seconds"].notna()
    if "scaled" not in df.columns:
        df["scaled"] = False
    else:
        df["scaled"] = df["scaled"].fillna(False).astype(bool)
    df = df[~df["scaled"]]
    return df


df = load_data()

# --- Header ---
st.markdown(
    f'<div style="text-align:center; padding:0 0 0.3rem 0;">'
    f'<h1 style="margin:0; font-size:1.8rem; color:{TEXT_COLOR};">CROSSFIT OPEN 26.3</h1>'
    f'</div>',
    unsafe_allow_html=True,
)

# --- Inline filters ---
with st.expander("Filters & Athlete Lookup", expanded=False):
    f1, f2, f3, f4 = st.columns([1.2, 1.5, 1.5, 2])
    gender = f1.radio("Gender", ["Men", "Women"], index=0, horizontal=True)
    age_min, age_max = int(df["age"].min()), int(df["age"].max())
    age_range = f2.slider("Age", age_min, age_max, (age_min, age_max))
    countries = sorted(df["country"].dropna().unique())
    selected_countries = f3.multiselect("Country", countries)
    athlete_name = f4.text_input("Athlete lookup")

# Apply filters
mask = df["gender"] == ("M" if gender == "Men" else "F")
if selected_countries:
    mask &= df["country"].isin(selected_countries)
mask &= df["age"].between(age_range[0], age_range[1])
filtered = df[mask]
reps = filtered["reps"].dropna()

# --- Stats ---
median_r = reps.median() if len(reps) > 0 else 0
p25 = reps.quantile(0.75) if len(reps) > 0 else 0
finisher_count = int(filtered["finished"].sum())

st.markdown(
    f'<p style="text-align:center; margin:0.3rem 0 0 0; font-size:0.95rem; color:{SUBTITLE_COLOR};">'
    f'{gender} Rx\'d &middot; {len(reps):,} athletes &middot; '
    f'Median <b style="color:{MEDIAN_COLOR}">{median_r:.0f}</b> &middot; '
    f'Top 25% <b style="color:{QF_COLOR}">{p25:.0f}+</b> &middot; '
    f'Finished <b>{finisher_count}</b>'
    f'</p>',
    unsafe_allow_html=True,
)

# --- Athlete lookup ---
athlete_reps_val = None
athlete_info = None
if athlete_name:
    matches = filtered[filtered["name"].str.contains(athlete_name, case=False, na=False)]
    if len(matches) > 0:
        top = matches.iloc[0]
        if pd.notna(top["reps"]):
            athlete_reps_val = top["reps"]
            athlete_info = top
        st.dataframe(
            matches[["name", "rank", "score_display", "country", "age"]].head(5),
            hide_index=True, use_container_width=True,
        )
    else:
        st.caption("No athlete found.")


# --- Histogram ---
def make_histogram(reps_series, athlete_reps=None, athlete_row=None):
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=reps_series, nbinsx=60,
        marker_color=BAR_COLOR, opacity=0.85,
        hovertemplate="Reps: %{x}<br>Athletes: %{y}<extra></extra>",
    ))

    y_max = len(reps_series) * 0.06

    med = reps_series.median()
    fig.add_vline(x=med, line_dash="dash", line_color=MEDIAN_COLOR, line_width=2)
    fig.add_annotation(
        x=med, y=y_max, text=f"Median: {med:.0f}",
        showarrow=False, font=dict(color=MEDIAN_COLOR, size=13, family="Arial Black"), yshift=10,
    )

    qf = reps_series.quantile(0.75)
    fig.add_vline(x=qf, line_dash="dash", line_color=QF_COLOR, line_width=2)
    fig.add_annotation(
        x=qf, y=y_max * 0.85, text=f"25%: {qf:.0f} reps",
        showarrow=False, font=dict(color=QF_COLOR, size=13, family="Arial Black"), yshift=10,
    )

    if athlete_reps is not None:
        pct_above = (reps_series >= athlete_reps).mean() * 100
        name = athlete_row["name"] if athlete_row is not None else ""
        fig.add_vline(x=athlete_reps, line_dash="solid", line_color=ATHLETE_COLOR, line_width=3)
        fig.add_annotation(
            x=athlete_reps, y=y_max * 0.7,
            text=f"{name}: {athlete_reps:.0f} (top {pct_above:.0f}%)",
            showarrow=True, arrowhead=2, arrowcolor=ATHLETE_COLOR,
            font=dict(color=ATHLETE_COLOR, size=12, family="Arial Black"), ax=0, ay=-40,
        )

    fig.update_layout(
        xaxis_title="Total Reps", yaxis_title="Athletes",
        bargap=0.03, height=400,
        margin=dict(l=40, r=15, t=10, b=45),
        plot_bgcolor=BG_COLOR, paper_bgcolor=BG_COLOR,
        font=dict(color=TEXT_COLOR, size=12),
        xaxis=dict(gridcolor="#222", zerolinecolor="#333"),
        yaxis=dict(gridcolor="#222", zerolinecolor="#333"),
    )
    return fig


if len(reps) > 0:
    st.plotly_chart(make_histogram(reps, athlete_reps_val, athlete_info), use_container_width=True)
else:
    st.info("No data for current filters.")

st.markdown(
    f'<p style="text-align:center; color:{SUBTITLE_COLOR}; font-size:0.75rem;">'
    f'Data from c3po.crossfit.com &middot; {len(df):,} total athletes</p>',
    unsafe_allow_html=True,
)
