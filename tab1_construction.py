"""Tab 1: Pace of Construction.

Question for Dana: how fast is US data centre construction spending growing,
and is the growth accelerating?

Data: US Census Bureau Value of Construction Put in Place (private data centre
construction), adjusted to constant 2021 US$ with BLS producer price indexes,
processed and published by Our World in Data. The CSV in data/ is kept exactly
as downloaded; every transformation is in src/tab1_prep.py.
"""

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src import tab1_prep as prep  # noqa: E402  (every transformation lives in src/tab1_prep.py)

DATA_FILE = prep.RAW_FILE
SOURCE_URL = prep.SOURCE_URL
SOURCE_TEXT = (
    "US Census Bureau (2026); US Bureau of Labor Statistics (2026), "
    "with major processing by Our World in Data"
)

CHATGPT = prep.CHATGPT
HIGHLIGHT = "#C46A10"       # warm amber: the 12-month average Dana should read
CONTEXT = "#A79E97"         # soft warm grey: raw monthly values
HIGHLIGHT_TEXT = "#A85A0C"  # darker versions for text, readable in a screen recording
CONTEXT_TEXT = "#766D66"

NEON_CSS = """
<style>
[data-testid="stMetric"] { transition: box-shadow .25s ease, transform .25s ease, border-color .25s ease; }
[data-testid="stMetric"]:hover { transform: translateY(-3px); border-color: #5CF2FF !important;
  box-shadow: 0 0 0 1px #5CF2FF, 0 0 16px rgba(92,242,255,.5), 0 0 30px rgba(255,92,214,.2); }
[data-testid="stMetricValue"] { color: #C46A10; }
</style>
"""


@st.cache_data
def load_data() -> pd.DataFrame:
    """Steps 1 and 2 from src/tab1_prep.py: read the raw file, one row per month."""
    return prep.monthly(prep.load_raw())


def build_chart(df: pd.DataFrame, show_avg: bool) -> alt.LayerChart:
    long = df.melt(id_vars="month", value_vars=["spend_b", "avg12_b"], var_name="series", value_name="b")
    long["series"] = long["series"].map({"spend_b": "Monthly spending", "avg12_b": "12-month average"})
    long = long.dropna()
    if not show_avg:
        long = long[long["series"] == "Monthly spending"]

    x = alt.X("month:T", title=None, axis=alt.Axis(format="%Y", labelFontSize=14, grid=False,
                                                   tickCount="year"))
    y = alt.Y("b:Q", title="Spending per month (billion US$, 2021 prices)",
              scale=alt.Scale(domain=[0, float(df["spend_b"].max()) * 1.12]),
              axis=alt.Axis(labelFontSize=14, titleFontSize=14))
    color = alt.Color("series:N", legend=None, scale=alt.Scale(
        domain=["12-month average", "Monthly spending"], range=[HIGHLIGHT, CONTEXT]))
    width = alt.Size("series:N", legend=None, scale=alt.Scale(
        domain=["12-month average", "Monthly spending"], range=[4, 1.6]))

    lines = alt.Chart(long).mark_line(strokeCap="round").encode(x=x, y=y, color=color, size=width,
                                                                 detail="series:N")
    halo = (alt.Chart(long[long["series"] == "12-month average"])
            .mark_line(strokeCap="round", opacity=0.22)
            .encode(x=x, y=y, size=alt.value(14), color=alt.value(HIGHLIGHT)))

    # Hover anywhere: the nearest month is selected and both values appear.
    hover = alt.selection_point(nearest=True, on="pointerover", fields=["month"], empty=False)
    guide = (
        alt.Chart(df.dropna(subset=["spend_b"]))
        .mark_rule(color=CONTEXT, strokeWidth=1.5)
        .encode(
            x="month:T",
            opacity=alt.condition(hover, alt.value(0.7), alt.value(0)),
            tooltip=[alt.Tooltip("month:T", title="Month", format="%b %Y"),
                     alt.Tooltip("spend_b:Q", title="Monthly spending ($bn)", format=".2f"),
                     alt.Tooltip("avg12_b:Q", title="12-month average ($bn)", format=".2f")],
        )
        .add_params(hover)
    )
    dots = alt.Chart(long).mark_point(filled=True, size=70, opacity=1).encode(
        x=x, y=y, color=color, opacity=alt.condition(hover, alt.value(1), alt.value(0)))

    marker = pd.DataFrame({"month": [CHATGPT], "txt": ["ChatGPT released (Nov 2022)"]})
    rule = alt.Chart(marker).mark_rule(strokeDash=[4, 4], color=CONTEXT_TEXT).encode(x="month:T")
    rule_txt = alt.Chart(marker).mark_text(align="left", dx=6, dy=10, fontSize=13, fontStyle="italic",
                                           color=CONTEXT_TEXT).encode(x="month:T", y=alt.value(0),
                                                                      text="txt:N")

    last = long[long["month"] == long["month"].max()].copy()
    last["label"] = last.apply(lambda r: f"{r['series']} ${r['b']:.2f}bn", axis=1)
    end_labels = alt.Chart(last).mark_text(align="right", dx=-8, dy=-12, fontSize=14, fontWeight="bold").encode(
        x="month:T", y="b:Q", text="label:N",
        color=alt.condition("datum.series == '12-month average'",
                            alt.value(HIGHLIGHT_TEXT), alt.value(CONTEXT_TEXT)))

    return (
        alt.layer(halo, lines, rule, rule_txt, guide, dots, end_labels)
        .properties(height=440)
        .configure_view(strokeWidth=0)
        .configure(background="transparent")
    )


def render() -> None:
    st.html(NEON_CSS)
    st.header("🏗️ Pace of Construction")
    st.markdown(
        "**How fast is US data centre construction spending growing, and is the growth accelerating?**"
    )

    if not DATA_FILE.exists():
        st.error(f"Missing source file: `data/{DATA_FILE.name}`. Download it from {SOURCE_URL}.")
        return

    df = load_data()
    month_col, value_col = prep.MONTH_COL, prep.VALUE_COL
    c = prep.cards(df)  # step 3 in src/tab1_prep.py
    latest, year_ago, two_ago, pre_ai = c["latest"], c["year_ago"], c["two_ago"], c["pre_ai"]
    same_month_growth = c["same_month_growth_pct"]
    avg_growth_now = c["avg_growth_pct"]
    avg_growth_before = c["avg_growth_prev_pct"]
    since_ai = c["since_chatgpt_x"]
    m = lambda d: d.strftime("%b %Y")

    # --- Summary cards -------------------------------------------------------
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Spending in {m(latest['month'])}", f"${latest['spend_b']:.2f}bn",
              f"{same_month_growth:+.0f}% vs {m(year_ago['month'])}", delta_color="off", border=True)
    c2.metric("12-month average per month", f"${latest['avg12_b']:.2f}bn",
              f"{since_ai:.1f}× the level before ChatGPT", delta_color="off", border=True)
    c3.metric("Growth of the 12-month average, past year", f"{avg_growth_now:+.0f}%",
              f"was {avg_growth_before:+.0f}% the year before", delta_color="off", border=True)

    # --- Main chart ----------------------------------------------------------
    with st.container(border=True):
        years = sorted(df["month"].dt.year.unique())
        a, b = st.columns([3, 1], vertical_alignment="bottom")
        start = a.select_slider("Show from", options=years, value=years[0], key="tab1_start")
        show_avg = b.toggle("12-month average", value=True, key="tab1_avg")
        view = df[df["month"].dt.year >= start]
        st.altair_chart(build_chart(view, show_avg), width="stretch")
        st.caption(
            "Hover over the chart to see the values for any month. The grey line is the raw monthly "
            "figure, which is not seasonally adjusted, so it wobbles with the construction season. "
            "The amber line is the 12-month average, which smooths that out. Recent months are "
            "preliminary and the Census Bureau revises them."
        )

    st.info(
        f"**What this means for Dana:** construction spending is still rising fast. "
        f"{m(latest['month'])} was {same_month_growth:.0f}% above the same month a year earlier, and the "
        f"12-month average is {since_ai:.1f} times its level before ChatGPT. But the growth *rate* has "
        f"slowed: the 12-month average grew {avg_growth_now:.0f}% in the past year, down from "
        f"{avg_growth_before:.0f}% the year before. More is being built every month, just not at an "
        f"ever-faster rate. This covers buildings only (not servers) for all data centres, not only AI.",
        icon="💡",
    )

    # --- Trace: the headline numbers back to the raw file -------------------
    with st.expander(f"🔍 Trace the headline number (\\${latest['spend_b']:.2f}bn) to the source file"):
        # Read as text so the table shows every digit exactly as stored in the file.
        raw = pd.read_csv(DATA_FILE, dtype=str, keep_default_na=False)
        ent = [c for c in raw.columns if c.lower() == "entity"][0]

        def row(month: pd.Timestamp) -> pd.DataFrame:
            return raw[(raw[ent] == "United States") & (raw[month_col] == month.strftime("%Y-%m"))]

        r_now, r_ago = row(latest["month"]), row(year_ago["month"])
        v_now, v_ago = r_now[value_col].iloc[0], r_ago[value_col].iloc[0]
        st.markdown(f"1. File: `data/{DATA_FILE.name}` (unchanged OWID download)")
        st.markdown(f"2. Filter rows where *{ent}* = `United States` and *{month_col}* = "
                    f"`{latest['month'].strftime('%Y-%m')}`:")
        st.dataframe(r_now, hide_index=True, width="stretch")
        st.markdown(f"3. Column *{value_col}* holds `{v_now}`, in US dollars at 2021 prices.")
        st.markdown(f"4. Divide by 1,000,000,000 and round to two decimals: `{v_now}` ÷ 10⁹ = "
                    f"**\\${float(v_now) / 1e9:.2f}bn**, the figure on the first card.")
        st.markdown(
            f"5. First card's change uses the `{year_ago['month'].strftime('%Y-%m')}` row (`{v_ago}`): "
            f"`{v_now}` ÷ `{v_ago}` − 1 = **{(float(v_now) / float(v_ago) - 1) * 100:+.0f}%**. "
            f"Comparing the same month a year apart avoids the seasonal wobble."
        )
        last12 = df.tail(12)
        st.markdown(
            f"6. Second card: the mean of the 12 monthly values from "
            f"{m(last12['month'].iloc[0])} to {m(last12['month'].iloc[-1])} = "
            f"**\\${latest['avg12_b']:.2f}bn**. Before ChatGPT ({m(CHATGPT)}) the same average was "
            f"\\${pre_ai['avg12_b']:.2f}bn, so {latest['avg12_b']:.2f} ÷ {pre_ai['avg12_b']:.2f} = "
            f"**{since_ai:.1f}×**."
        )
        st.markdown(
            f"7. Third card: 12-month average now ÷ 12-month average a year earlier − 1 = "
            f"{latest['avg12_b']:.2f} ÷ {year_ago['avg12_b']:.2f} − 1 = **{avg_growth_now:+.0f}%**. "
            f"The year before: {year_ago['avg12_b']:.2f} ÷ {two_ago['avg12_b']:.2f} − 1 = "
            f"**{avg_growth_before:+.0f}%**."
        )

    with st.expander("📋 All data used in this tab"):
        table = df.assign(Month=df["month"].dt.strftime("%Y-%m"))[["Month", "spend_b", "avg12_b"]]
        st.dataframe(
            table.rename(columns={"spend_b": "Monthly spending ($bn)", "avg12_b": "12-month average ($bn)"})
            .iloc[::-1].round(2),
            hide_index=True, width="stretch",
        )

    st.caption(
        f"Source: {SOURCE_TEXT}. [{SOURCE_URL}]({SOURCE_URL}). Private construction of data centre "
        "buildings only, in constant 2021 US$; excludes servers and other IT equipment, land and "
        "maintenance. Not seasonally adjusted. Covers all data centres; the source does not separate AI."
    )


if __name__ == "__main__":
    # Lets you preview the tab on its own: streamlit run tab1_construction.py
    st.set_page_config(page_title="Pace of Construction", page_icon="🏗️", layout="wide")
    render()
