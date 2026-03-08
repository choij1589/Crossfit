"""
CrossFit Open 2026 – 26.2 Leaderboard Dashboard
Run: streamlit run dashboard.py
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="CrossFit Open 26.2", layout="centered", initial_sidebar_state="collapsed")

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

DATA_PATH = "data/26.2_scores.csv"

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
    # TODO 26.2: Add workout-specific column parsing here
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
    f'<h1 style="margin:0; font-size:1.8rem; color:{TEXT_COLOR};">CROSSFIT OPEN 26.2</h1>'
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

# TODO 26.2: Replace score_col with the correct column for 26.2 workout
# score_col = filtered["<score_column>"].dropna()

st.markdown(
    f'<p style="text-align:center; margin:0.3rem 0 0 0; font-size:0.95rem; color:{SUBTITLE_COLOR};">'
    f'{gender} Rx\'d &middot; {len(filtered):,} athletes'
    f'</p>',
    unsafe_allow_html=True,
)

# --- Athlete lookup ---
if athlete_name:
    matches = filtered[filtered["name"].str.contains(athlete_name, case=False, na=False)]
    if len(matches) > 0:
        st.dataframe(
            matches[["name", "rank", "score_display", "country", "age"]].head(5),
            hide_index=True, use_container_width=True,
        )
    else:
        st.caption("No athlete found.")

# TODO 26.2: Add histogram once score column is known

st.markdown(
    f'<p style="text-align:center; color:{SUBTITLE_COLOR}; font-size:0.75rem;">'
    f'Data from c3po.crossfit.com &middot; {len(df):,} total athletes</p>',
    unsafe_allow_html=True,
)
