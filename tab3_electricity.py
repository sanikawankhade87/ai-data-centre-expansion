"""Tab 3: Electricity Demand.

Question for Dana: what does the data centre expansion cost the US electricity
grid, and how large could this load become?

The page reads one story from top to bottom:
  1. US electricity demand is rising again after years of no growth
  2. how much of that rise comes from data centres
  3. how the United States compares with China and the rest of the world
  4. how much frontier AI capacity is already announced
  5. how large data centre use could become by 2030 at measured growth rates

Every number comes from the processed files in data/processed/, built by
src/tab3_prep.py from the unedited sources in data/raw/. The tab only reads,
filters and formats them, so each figure can be traced back in the data package.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
PROCESSED = ROOT / "data" / "processed"
FILES = {
    "us_demand": PROCESSED / "tab3_us_demand.csv",
    "dc_use": PROCESSED / "tab3_dc_use.csv",
    "ai_capacity": PROCESSED / "tab3_ai_capacity.csv",
    "scenarios": PROCESSED / "tab3_scenarios.csv",
    "projection": PROCESSED / "tab3_projection.csv",
}
RAW = ROOT / "data" / "raw" / "tab3"
RAW_SHARE, RAW_DEMAND = RAW / "owid_dc_share.csv", RAW / "owid_electricity_demand.csv"

US = "United States"
REGIONS = [US, "China", "Rest of world", "World"]
FOCUS = "#C46A10"        # amber: the United States (matches the app theme)
CONTEXT = "#A79E97"      # warm grey: everything else
FOCUS_TEXT = "#A85A0C"   # darker shades for text, readable in a screen recording
CONTEXT_TEXT = "#766D66"
FLAT_FILL = "#EFE6DD"


def fit(fn) -> dict:
    """Stretch an element to its container on any Streamlit version (1.50 has no width=)."""
    if "width" in inspect.signature(fn).parameters:
        return {"width": "stretch"}
    return {"use_container_width": True}


@st.cache_data
def load() -> dict[str, pd.DataFrame]:
    return {k: pd.read_csv(p) for k, p in FILES.items()}


@st.cache_data
def refresh_info() -> dict:
    log = json.loads((RAW / "retrieval_log.json").read_text())
    meta = json.loads((RAW / "owid_dc_share.metadata.json").read_text())
    updated = list(meta["columns"].values())[0]["lastUpdated"]
    return {"retrieved": pd.Timestamp(log["retrieved"]), "owid_updated": pd.Timestamp(updated)}


def card(col, label: str, value: str, note: str) -> None:
    """A bordered card: label, value and one line of context, with no up or down arrow."""
    with col.container(border=True):
        st.metric(label, value)
        st.caption(note)


def style(chart: alt.TopLevelMixin) -> alt.TopLevelMixin:
    return (chart.configure_view(strokeWidth=0)
            .configure(background="transparent")
            .configure_axis(labelFontSize=13, titleFontSize=13, labelColor=CONTEXT_TEXT,
                            titleColor=CONTEXT_TEXT, gridColor="#EDE7E1")
            .configure_title(fontSize=15, anchor="start", color="#2E2622", subtitleColor=CONTEXT_TEXT,
                             subtitleFontSize=12))


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def demand_chart(us: pd.DataFrame) -> alt.LayerChart:
    """Section 1: US total demand, 2000-2025, with the flat period shaded."""
    flat = us[us["in_flat_period"]]
    y0, y1 = int(flat["year"].min()), int(flat["year"].max())
    years = alt.Scale(domain=[1999.5, 2025.8], zero=False)
    x = alt.X("year:Q", title="Year", scale=years,
              axis=alt.Axis(format="d", values=list(range(2000, 2026, 5)), grid=False))
    y = alt.Y("demand_twh:Q", title="US electricity demand (TWh)", scale=alt.Scale(domain=[3500, 4700]),
              axis=alt.Axis(format=",d", tickCount=6))
    # The band shares the year scale; on its own a rect would pull the axis back to zero.
    band = alt.Chart(pd.DataFrame({"a": [y0], "b": [y1]})).mark_rect(color=FLAT_FILL).encode(
        x=alt.X("a:Q", scale=years), x2="b:Q")
    band_label = alt.Chart(pd.DataFrame({"year": [(y0 + y1) / 2], "t": [f"Almost no growth, {y0} to {y1}"]})) \
        .mark_text(fontSize=12, fontStyle="italic", color=CONTEXT_TEXT, dy=-8).encode(
            x="year:Q", y=alt.value(14), text="t:N")
    line = alt.Chart(us).mark_line(color=FOCUS, strokeWidth=3).encode(x=x, y=y)
    dots = alt.Chart(us).mark_point(color=FOCUS, filled=True, size=40, opacity=1).encode(
        x=x, y=y, tooltip=[alt.Tooltip("year:Q", title="Year", format="d"),
                           alt.Tooltip("demand_twh:Q", title="Demand (TWh)", format=",.0f")])
    keys = us[us["year"].isin([2000, y0, y1, int(us["year"].max())])].assign(
        label=lambda d: d["demand_twh"].map("{:,.0f}".format))
    labels = alt.Chart(keys).mark_text(fontSize=13, fontWeight="bold", color=FOCUS_TEXT, dy=-14).encode(
        x=x, y=y, text="label:N")
    return alt.layer(band, band_label, line, dots, labels).properties(
        height=300, title=alt.Title("US electricity demand, 2000 to 2025 (TWh)",
                                    subtitle="Labelled values mark the start, the flat period and the latest year"))


def dc_bar_chart(us: pd.DataFrame) -> alt.LayerChart:
    """Section 2: US data centre use for the four years with data, as bars."""
    d = us.assign(year_label=us["year"].astype(str),
                  label=us.apply(lambda r: f"{r['dc_twh']:.0f} TWh ({r['share_pct']:.1f}%)", axis=1))
    x = alt.X("year_label:N", title="Year (no data for 2021 and 2022)", axis=alt.Axis(labelAngle=0))
    y = alt.Y("dc_twh:Q", title="Data centre electricity use (TWh)",
              scale=alt.Scale(domain=[0, float(d["dc_twh"].max()) * 1.2]))
    bars = alt.Chart(d).mark_bar(color=FOCUS, size=56, cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(x=x, y=y)
    text = alt.Chart(d).mark_text(dy=-10, fontSize=13, fontWeight="bold", color=FOCUS_TEXT).encode(
        x=x, y=y, text="label:N")
    return alt.layer(bars, text).properties(
        height=300, title=alt.Title("US data centre electricity use (TWh) and share of US demand (%)"))


def region_chart(latest: pd.DataFrame, year: int) -> alt.LayerChart:
    """Section 3: data centre use by region in the latest year, largest first."""
    d = latest[latest["region"] != "World"].sort_values("dc_twh", ascending=False).assign(
        label=lambda x: x.apply(lambda r: f"{r['dc_twh']:.0f} TWh ({r['share_of_world_dc_pct']:.0f}% of world)",
                                axis=1),
        colour=lambda x: x["region"].eq(US).map({True: FOCUS, False: CONTEXT}))
    y = alt.Y("region:N", title="Region", sort=list(d["region"]), axis=alt.Axis(labelFontSize=13))
    x = alt.X("dc_twh:Q", title=f"Data centre electricity use, {year} (TWh)",
              scale=alt.Scale(domain=[0, float(d["dc_twh"].max()) * 1.55]), axis=alt.Axis(grid=False))
    bars = alt.Chart(d).mark_bar(size=34, cornerRadiusEnd=3).encode(
        x=x, y=y, color=alt.Color("colour:N", scale=None))
    text = alt.Chart(d).mark_text(align="left", dx=6, fontSize=13, fontWeight="bold").encode(
        x=x, y=y, text="label:N",
        color=alt.condition(alt.datum.region == US, alt.value(FOCUS_TEXT), alt.value(CONTEXT_TEXT)))
    return alt.layer(bars, text).properties(
        height=200, title=alt.Title(f"Data centre electricity use by region, {year} (TWh)"))


def capacity_chart(cap: pd.DataFrame, retrieved: pd.Timestamp) -> alt.LayerChart:
    """Section 4: month-end power of US frontier AI sites, reported against planned."""
    d = cap.assign(date=pd.to_datetime(cap["month"]) + pd.offsets.MonthEnd(0),
                   status=cap["status"].map({"reported": "Reported", "planned": "Planned"}))
    # Repeat the last reported month in the planned series so the two lines join.
    last = d[d["status"] == "Reported"].tail(1).assign(status="Planned")
    d = pd.concat([d, last]).sort_values(["status", "date"])
    x = alt.X("date:T", title="Month", axis=alt.Axis(format="%Y", tickCount="year", grid=False))
    # Headroom above the highest value so its label stays inside the chart area.
    y = alt.Y("power_gw:Q", title="Power (GW)",
              scale=alt.Scale(domain=[0, float(d["power_gw"].max()) * 1.2]))
    colour = alt.Color("status:N", title="Status", scale=alt.Scale(domain=["Reported", "Planned"],
                                                                  range=[FOCUS, FOCUS]),
                       legend=alt.Legend(orient="top-left", symbolType="stroke", symbolStrokeWidth=3))
    dash = alt.StrokeDash("status:N", scale=alt.Scale(domain=["Reported", "Planned"], range=[[1, 0], [6, 4]]),
                          legend=None)
    line = alt.Chart(d).mark_line(strokeWidth=3).encode(x=x, y=y, color=colour, strokeDash=dash)

    # Label each year end up to 2028, the latest reported month and the final month.
    year_ends = d[d["date"].dt.month.eq(12) & d["date"].dt.year.le(2028)]
    marks = pd.concat([year_ends, d[d["status"] == "Reported"].tail(1), d[d["date"] == d["date"].max()]])
    marks = marks.drop_duplicates("date")
    marks = marks[marks["power_gw"] >= 1].assign(label=lambda m: m["power_gw"].map("{:.1f}".format))
    dots = alt.Chart(marks).mark_point(filled=True, size=50, color=FOCUS, opacity=1).encode(x=x, y=y)
    text = alt.Chart(marks).mark_text(dy=-12, fontSize=12, fontWeight="bold", color=FOCUS_TEXT).encode(
        x=x, y=y, text="label:N")
    rule = alt.Chart(pd.DataFrame({"date": [retrieved]})).mark_rule(color=CONTEXT_TEXT, strokeDash=[3, 3]) \
        .encode(x="date:T")
    rule_text = alt.Chart(pd.DataFrame({"date": [retrieved], "t": [f"Data retrieved {retrieved:%d %b %Y}"]})) \
        .mark_text(align="right", dx=-6, dy=4, fontSize=12, color=CONTEXT_TEXT).encode(
            x="date:T", y=alt.value(10), text="t:N")
    return alt.layer(line, rule, rule_text, dots, text).properties(
        height=300, title=alt.Title("Power of US frontier AI data centres, reported and planned (GW)",
                                    subtitle="Labels show the end of each year to 2028, the latest reported month "
                                             "and January 2030"))


def projection_chart(measured: pd.DataFrame, proj: pd.DataFrame, region: str) -> alt.LayerChart:
    """Section 5: measured use (solid) and the projection at one rate (dashed)."""
    m = measured.assign(kind="Measured")
    p = proj.assign(kind="Projected")
    x = alt.X("year:Q", title="Year", scale=alt.Scale(domain=[2019.5, 2030.5]),
              axis=alt.Axis(format="d", values=list(range(2020, 2031)), grid=False))
    top = float(max(m["dc_twh"].max(), p["dc_twh"].max())) * 1.15
    y = alt.Y("dc_twh:Q", title="Data centre electricity use (TWh)", scale=alt.Scale(domain=[0, top]))
    gap = alt.Chart(m[m["year"].isin([2020, 2023])]).mark_line(color=CONTEXT, strokeDash=[2, 4], strokeWidth=2) \
        .encode(x=x, y=y)
    solid = alt.Chart(m[m["year"] >= 2023]).mark_line(color=FOCUS, strokeWidth=3).encode(x=x, y=y)
    dashed = alt.Chart(p).mark_line(color=FOCUS, strokeWidth=3, strokeDash=[6, 4]).encode(x=x, y=y)
    pts = pd.concat([m, p[p["year"] > 2025]]).assign(label=lambda d: d["dc_twh"].map("{:.0f}".format))
    dots = alt.Chart(pts).mark_point(filled=True, size=50, color=FOCUS, opacity=1).encode(
        x=x, y=y, shape=alt.Shape("kind:N", title=None, scale=alt.Scale(domain=["Measured", "Projected"],
                                                                         range=["circle", "diamond"]),
                                  legend=alt.Legend(orient="top-left")))
    text = alt.Chart(pts).mark_text(dy=-12, fontSize=12, fontWeight="bold", color=FOCUS_TEXT).encode(
        x=x, y=y, text="label:N")
    return alt.layer(gap, solid, dashed, dots, text).properties(
        height=320, title=alt.Title(f"{region}: data centre electricity use, measured 2020 to 2025 and "
                                    f"projected to 2030 (TWh)",
                                    subtitle="Solid = measured. Dashed = projection at the chosen rate. "
                                             "Dotted = no data for 2021 and 2022"))


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

def render() -> None:
    st.header("Electricity Demand")
    st.markdown("**What does the data centre expansion cost the US electricity grid, "
                "and how large could this load become?**")

    missing = [p.name for p in FILES.values() if not p.exists()]
    if missing:
        st.error("Missing processed file(s): " + ", ".join(f"`{m}`" for m in missing)
                 + ". Run `python -m src.tab3_prep` from the repository root to rebuild them.")
        return

    data = load()
    info = refresh_info()
    us_d = data["us_demand"]
    use = data["dc_use"]
    cap = data["ai_capacity"]
    latest_year = int(use["year"].max())
    first_year = int(use["year"].min())
    us_use = use[use["region"] == US].sort_values("year")
    us_now = us_use.iloc[-1]
    us_first = us_use.iloc[0]

    # --- 1. Grid demand -----------------------------------------------------------
    flat = us_d[us_d["in_flat_period"]]
    f0, f1 = flat.iloc[0], flat.iloc[-1]
    d_now = us_d.iloc[-1]
    st.subheader("1. US electricity demand is rising again")
    st.markdown(
        f"US demand barely changed between {int(f0['year'])} ({f0['demand_twh']:,.0f} TWh) and "
        f"{int(f1['year'])} ({f1['demand_twh']:,.0f} TWh), then rose by {d_now['change_since_2021_pct']:.0f}% "
        f"in four years.")
    c1, c2 = st.columns(2)
    card(c1, f"US electricity demand, {int(d_now['year'])}", f"{d_now['demand_twh']:,.0f} TWh",
         f"Total demand across all users in {int(d_now['year'])}")
    card(c2, f"Change since {int(f1['year'])}", f"+{d_now['change_since_2021_pct']:.1f}%",
         f"{f1['demand_twh']:,.0f} TWh in {int(f1['year'])} to {d_now['demand_twh']:,.0f} TWh "
         f"in {int(d_now['year'])}")
    with st.container(border=True):
        st.altair_chart(style(demand_chart(us_d)), **fit(st.altair_chart))

    # --- 2. Data centre contribution ---------------------------------------------
    st.subheader("2. Data centres are a large part of the new demand")
    st.markdown(
        f"Data centres used {us_now['dc_twh']:.0f} TWh in {latest_year}, about "
        f"{us_now['dc_twh'] / us_first['dc_twh']:.0f} times the {first_year} level, and account for "
        f"{us_now['dc_share_of_growth_pct']:.0f}% of the rise in US demand since {first_year}.")
    c1, c2, c3 = st.columns(3)
    card(c1, f"Data centre use, {latest_year}", f"{us_now['dc_twh']:.0f} TWh",
         f"{us_first['dc_twh']:.0f} TWh in {first_year}")
    card(c2, f"Share of US demand, {latest_year}", f"{us_now['share_pct']:.1f}%",
         f"{us_first['share_pct']:.1f}% in {first_year}")
    card(c3, f"Share of US demand growth, {first_year} to {latest_year}", f"{us_now['dc_share_of_growth_pct']:.0f}%",
         f"{us_now['dc_change_since_2020_twh']:.0f} of {us_now['demand_change_since_2020_twh']:.0f} TWh "
         f"added came from data centres")
    with st.container(border=True):
        st.altair_chart(style(dc_bar_chart(us_use)), **fit(st.altair_chart))

    # --- 3. Global context ---------------------------------------------------------
    now = use[use["year"] == latest_year].set_index("region")
    then = use[use["year"] == first_year].set_index("region")
    rest_rise = now.loc["Rest of world", "share_pct"] - then.loc["Rest of world", "share_pct"]
    us_rise = now.loc[US, "share_pct"] - then.loc[US, "share_pct"]
    st.subheader("3. The United States carries the largest data centre load")
    st.markdown(
        f"The United States accounts for {now.loc[US, 'share_of_world_dc_pct']:.0f}% of world data centre "
        f"electricity use, up from {then.loc[US, 'share_of_world_dc_pct']:.0f}% in {first_year}.")
    c1, c2 = st.columns(2)
    card(c1, f"US share of world data centre use, {latest_year}", f"{now.loc[US, 'share_of_world_dc_pct']:.0f}%",
         f"{then.loc[US, 'share_of_world_dc_pct']:.0f}% in {first_year}")
    card(c2, f"Rise in data centre share of demand, {first_year} to {latest_year}", f"+{us_rise:.1f} pts in the US",
         f"+{rest_rise:.1f} pts in the rest of world, where data centres use "
         f"{now.loc['Rest of world', 'share_pct']:.1f}% of demand")
    with st.container(border=True):
        st.altair_chart(style(region_chart(now.reset_index(), latest_year)), **fit(st.altair_chart))
        st.caption("Rest of world = World minus the United States and China. "
                   "Percentages show each region's share of world data centre electricity use.")

    # --- 4. Announced AI capacity --------------------------------------------------
    reported = cap[cap["status"] == "reported"].iloc[-1]
    end_2028 = cap[cap["month"] == "2028-12"].iloc[0]
    rep_label = pd.Period(reported["month"]).strftime("%b %Y")
    st.subheader("4. Announced AI data centres would add much more")
    st.markdown(
        f"Frontier AI data centres in the United States drew {reported['power_gw']:.1f} GW in {rep_label}, "
        f"and announced projects would raise this to {end_2028['power_gw']:.1f} GW by the end of 2028.")
    c1, c2 = st.columns(2)
    card(c1, f"Reported power, {rep_label}", f"{reported['power_gw']:.1f} GW",
         f"{int(reported['sites_drawing_power'])} US sites drawing power")
    card(c2, "Planned power, end of 2028", f"{end_2028['power_gw']:.1f} GW",
         f"{end_2028['power_gw'] / reported['power_gw']:.1f} times the power reported in {rep_label}")
    with st.container(border=True):
        st.altair_chart(style(capacity_chart(cap, info["retrieved"])), **fit(st.altair_chart))
        st.caption("Power of the whole facility, including cooling, for the frontier AI sites Epoch AI tracks. "
                   "Planned months follow announced dates, which may change. Few projects are announced "
                   "beyond 2028, so the planned line levels off there.")

    # --- 5. Projection -----------------------------------------------------------
    st.subheader("5. How large could data centre use become by 2030?")
    st.markdown("Choose a region and a growth rate. The projection grows the 2025 value at that rate each year, "
                "so it shows a possible size of the load, not a forecast.")
    rates = data["scenarios"]
    labels = {"trend": "Measured trend, 2020 to 2025", "latest": "Latest year, 2024 to 2025",
              "construction": "Construction spending trend, 2020 to 2025 (US only)"}
    with st.container(border=True):
        k1, k2 = st.columns([1, 2])
        region = k1.selectbox("Region", REGIONS, key="tab3_region")
        scenario = k2.radio("Growth rate", list(labels), format_func=labels.get, horizontal=True,
                            key="tab3_scenario")
        row = rates[(rates["region"] == region) & (rates["scenario"] == scenario)]
        if row.empty:
            st.info(f"Construction spending is only published for the United States, so this growth rate "
                    f"cannot be applied to {region}. Choose another growth rate, or select the United States.")
        else:
            r = row.iloc[0]
            proj = data["projection"]
            p = proj[(proj["region"] == region) & (proj["scenario"] == scenario)]
            p30 = p[p["year"] == p["year"].max()].iloc[0]
            c1, c2, c3 = st.columns(3)
            card(c1, "Growth rate used", f"{r['dc_growth_pct']:.1f}% a year", r["basis"])
            card(c2, "Data centre use, 2030", f"{p30['dc_twh']:.0f} TWh",
                 f"{p30['multiple_of_2025']:.1f} times the 2025 level")
            card(c3, "Share of demand, 2030", f"{p30['dc_share_pct']:.1f}%",
                 f"{now.loc[region, 'share_pct']:.1f}% in 2025; other demand grows "
                 f"{r['other_growth_pct']:.1f}% a year")
            measured = use[use["region"] == region][["year", "dc_twh"]]
            st.altair_chart(style(projection_chart(measured, p[["year", "dc_twh"]], region)),
                            **fit(st.altair_chart))

    # --- What this means ----------------------------------------------------------
    us_p = data["projection"][(data["projection"]["region"] == US) & (data["projection"]["year"] == 2030)]
    lo, hi = us_p.loc[us_p["dc_twh"].idxmin()], us_p.loc[us_p["dc_twh"].idxmax()]
    st.subheader("What this means for Dana")
    st.markdown(
        f"Data centres used {us_now['share_pct']:.1f}% of US electricity in {latest_year} and account for "
        f"{us_now['dc_share_of_growth_pct']:.0f}% of the growth in demand since {first_year}. Depending on the "
        f"growth rate, US data centre use would reach between {lo['dc_twh']:.0f} and {hi['dc_twh']:.0f} TWh by "
        f"2030 ({lo['dc_share_pct']:.1f}% to {hi['dc_share_pct']:.1f}% of demand). This range is the load the grid "
        f"may need to absorb if the expansion continues, while the width of the range shows how uncertain "
        f"permanent demand remains.")
    st.markdown(
        "**What the data cannot show**\n"
        "- The data centre share covers all data centres, as no public source separates AI data centres, "
        "so the measured values are an upper limit on AI-driven use.\n"
        "- No data centre share is published for 2021 and 2022.\n"
        "- Announced AI projects may be delayed or cancelled, and the projection assumes a constant growth rate.")

    with st.expander(f"Trace {us_now['dc_twh']:.0f} TWh (US data centre use, {latest_year}) to the source files"):
        raw_s = pd.read_csv(RAW_SHARE, dtype=str, keep_default_na=False)
        raw_d = pd.read_csv(RAW_DEMAND, dtype=str, keep_default_na=False)
        s_val = raw_s[(raw_s["Entity"] == US) & (raw_s["Year"] == str(latest_year))].iloc[0]
        d_val = raw_d[(raw_d["Entity"] == US) & (raw_d["Year"] == str(latest_year))].iloc[0]
        share_v, demand_v = s_val.iloc[-1], d_val.iloc[-1]
        result = float(share_v) / 100 * float(demand_v)
        st.markdown(
            f"1. `data/raw/tab3/{RAW_SHARE.name}`, row *Entity* = `{US}`, *Year* = `{latest_year}`: "
            f"data centre share = `{share_v}` (%), line {s_val.name + 2} of the file.\n"
            f"2. `data/raw/tab3/{RAW_DEMAND.name}`, row *Entity* = `{US}`, *Year* = `{latest_year}`: "
            f"electricity demand = `{demand_v}` (TWh), line {d_val.name + 2} of the file.\n"
            f"3. `{share_v}` ÷ 100 × `{demand_v}` = `{result:.4f}` TWh, rounded to **{result:.0f} TWh**.\n"
            f"4. The same calculation is step 3 in `src/tab3_prep.py`, and the result is the "
            f"`dc_twh` column of `data/processed/tab3_dc_use.csv`.")

    st.caption(
        f"Sources: IEA, Energy and AI (2025, 2026), and Ember, Yearly Electricity Data (2026), processed by "
        f"Our World in Data; Epoch AI, AI data centers (CC BY); US Census Bureau construction spending, processed "
        f"by Our World in Data. **Last data refresh:** files retrieved {info['retrieved']:%d %b %Y}; electricity "
        f"data updated by Our World in Data on {info['owid_updated']:%d %b %Y}; Epoch AI records up to "
        f"{rep_label} are reported.")


if __name__ == "__main__":
    # Preview this tab on its own: streamlit run tab3_electricity.py
    st.set_page_config(page_title="Electricity Demand", layout="wide")
    render()
