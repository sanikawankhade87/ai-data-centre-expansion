"""Tab 3: Electricity Demand.

Question for Dana: what share of electricity demand do data centres take,
and how fast is that share rising in the United States compared with the
rest of the world?

Data: IEA "Energy and AI" (data centre electricity use) divided by Ember
total electricity demand, processed and published by Our World in Data.
The CSV in data/ is kept exactly as downloaded; every cleaning step is below.

Changes from the first version:
- a second chart ranks every region by the rise in its share since 2020, which
  answers the "compared with the rest of the world" half of the question
- a "yearly rise" card shows whether the US rise is speeding up
- the year picker now drives the cards, the ranking chart and the summary box
- card wording corrected ("3.2x the world share", not "3.2x higher")
- the "no data" note sits beside the dashed segment it explains
- the region selector is capped at six so the end labels cannot collide
- source last-updated and download dates shown on screen
- runs on Streamlit 1.50 (local) as well as the newer version on Streamlit Cloud
- neon hover effect and emoji removed
"""

import inspect
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

DATA_FILE = Path(__file__).parent / "data" / "data-centers-share-electricity-demand.csv"
SOURCE_URL = "https://ourworldindata.org/grapher/data-centers-share-electricity-demand"
SOURCE_TEXT = (
    "International Energy Agency (2025, 2026); Ember (2026), "
    "with major processing by Our World in Data"
)
SOURCE_UPDATED = "30 June 2026"      # "last updated" date in the OWID chart metadata
FILE_DOWNLOADED = "21 October 2026"  # date the CSV was added to data/

FOCUS = "United States"
# Regions shown by default. North America is left out because it mostly
# repeats the United States line.
DEFAULT_REGIONS = [
    "United States",
    "World",
    "Europe (IEA)",
    "China",
    "World excl. United States and China",
]
MAX_REGIONS = 6  # beyond this the end labels start to overlap
HIGHLIGHT = "#C46A10"  # warm amber: the one line Dana should read (matches the app theme)
CONTEXT = "#A79E97"    # soft warm grey: comparison regions
# Darker versions for text, so labels stay readable in a compressed screen recording
# (both pass the 4.5:1 contrast guideline on the page background).
HIGHLIGHT_TEXT = "#A85A0C"
CONTEXT_TEXT = "#766D66"


def fit(fn) -> dict:
    """Keyword that stretches an element to its container on any Streamlit version.

    Streamlit 1.50 has no ``width`` argument on st.altair_chart; newer versions
    have it and warn about the old ``use_container_width`` keyword.
    """
    if "width" in inspect.signature(fn).parameters:
        return {"width": "stretch"}
    return {"use_container_width": True}


@st.cache_data
def load_data(path: Path = DATA_FILE) -> tuple[pd.DataFrame, str]:
    """Read the raw OWID file and return (tidy table, name of the value column).

    OWID files come with either short or long column names depending on the
    download option, so columns are matched by lower-cased name rather than
    by one exact spelling.
    """
    raw = pd.read_csv(path)
    cols = {c.lower(): c for c in raw.columns}
    entity, year = cols["entity"], cols["year"]
    value_col = [c for c in raw.columns if c.lower() not in ("entity", "code", "year")][0]
    df = raw.rename(columns={entity: "region", year: "year", value_col: "share"})
    df = df[["region", "year", "share"]].dropna(subset=["share"])
    df["year"] = df["year"].astype(int)
    return df.sort_values(["region", "year"]).reset_index(drop=True), value_col


def segments(df: pd.DataFrame) -> pd.DataFrame:
    """Split each region's line into segments between consecutive years with data.

    A segment is marked as a gap when it jumps over years with no data
    (2020 to 2023), so the chart can draw it dashed instead of solid.
    """
    rows = []
    for region, g in df.groupby("region"):
        g = g.sort_values("year").reset_index(drop=True)
        for i in range(len(g) - 1):
            y0, y1 = g.loc[i, "year"], g.loc[i + 1, "year"]
            for j in (i, i + 1):
                rows.append({
                    "region": region, "year": g.loc[j, "year"], "share": g.loc[j, "share"],
                    "seg": f"{region}|{y0}", "gap": (y1 - y0) > 1,
                })
    return pd.DataFrame(rows)


def role(d: pd.DataFrame) -> pd.Series:
    return d["region"].eq(FOCUS).map({True: "focus", False: "context"})


def growth_table(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Rise in each region's share between the first year in the file and ``year``, in points."""
    first = int(df["year"].min())
    wide = df.pivot(index="region", columns="year", values="share")
    out = pd.DataFrame({"region": wide.index, "rise": (wide[year] - wide[first]).values})
    # "-0.0" reads as a drop, so a change that rounds to zero is shown as 0.0.
    out["label"] = out["rise"].map(lambda v: f"{v:+.1f}".replace("-0.0", "0.0"))
    return out.sort_values("rise", ascending=False).reset_index(drop=True)


def build_chart(df: pd.DataFrame) -> alt.LayerChart:
    df = df.assign(role=role)
    seg = segments(df).assign(role=role)
    years = sorted(df["year"].unique())
    regions = sorted(df["region"].unique(), key=lambda r: (r != FOCUS, r))

    x = alt.X(
        "year:Q", title=None,
        # Room on the right for the longest end label ("World excl. United States and China").
        scale=alt.Scale(domain=[min(years) - 0.2, max(years) + 3.4]),
        axis=alt.Axis(values=list(range(min(years), max(years) + 1)), format="d",
                      labelFontSize=14, grid=False),
    )
    y = alt.Y(
        "share:Q", title="Share of electricity demand (%)",
        scale=alt.Scale(domain=[0, max(6.0, float(df["share"].max()) * 1.15)]),
        axis=alt.Axis(labelFontSize=14, titleFontSize=14, format="d", tickMinStep=1),
    )
    color = alt.Color("role:N", scale=alt.Scale(domain=["focus", "context"],
                                                range=[HIGHLIGHT, CONTEXT]), legend=None)
    width = alt.Size("role:N", scale=alt.Scale(domain=["focus", "context"], range=[4, 2]),
                     legend=None)

    # Hover anywhere on the chart: the nearest year with data is selected.
    hover = alt.selection_point(nearest=True, on="pointerover", fields=["year"], empty=False)

    base_seg = alt.Chart(seg).encode(x=x, y=y, color=color, size=width, detail="seg:N")
    measured = base_seg.transform_filter("!datum.gap").mark_line(strokeCap="round")
    # Soft halo under the US line only, so Dana's eye goes there first.
    halo = (base_seg.transform_filter("datum.role == 'focus' && !datum.gap")
            .mark_line(strokeCap="round", opacity=0.22)
            .encode(size=alt.value(14), color=alt.value(HIGHLIGHT)))
    missing = base_seg.transform_filter("datum.gap").mark_line(strokeDash=[5, 5], opacity=0.8)

    dots = alt.Chart(df).mark_point(filled=True, opacity=1).encode(
        x=x, y=y, color=color,
        size=alt.condition(hover, alt.value(220), alt.value(90)),
    )

    # Vertical guide line with every region's value for the hovered year.
    # One row per year, one column per region. Columns get simple names (r0, r1, ...)
    # because region names like "World excl." contain characters the chart library
    # misreads; the real names are kept as the tooltip titles.
    safe = {r: f"r{i}" for i, r in enumerate(regions)}
    wide = (df.pivot(index="year", columns="region", values="share")
            .rename(columns=safe).reset_index())
    guide = (
        alt.Chart(wide)
        .mark_rule(color=CONTEXT, strokeWidth=1.5)
        .encode(
            x=x,
            opacity=alt.condition(hover, alt.value(0.7), alt.value(0)),
            tooltip=[alt.Tooltip("year:Q", title="Year", format="d")]
            + [alt.Tooltip(f"{safe[r]}:Q", title=f"{r} (%)", format=".2f") for r in regions],
        )
        .add_params(hover)
    )

    last = df[df["year"] == df["year"].max()]
    end_labels = (
        alt.Chart(last).mark_text(align="left", dx=12, fontSize=14, fontWeight="bold")
        .encode(x=x, y=y, text="endlabel:N",
                color=alt.condition("datum.role == 'focus'",
                                    alt.value(HIGHLIGHT_TEXT), alt.value(CONTEXT_TEXT)))
        .transform_calculate(endlabel="datum.region + ' ' + format(datum.share, '.1f') + '%'")
    )

    layers = [halo, missing, measured, guide, dots, end_labels]

    # The "no data" note sits just above the middle of the US dashed segment.
    focus = df[df["region"] == FOCUS].sort_values("year")
    if len(focus) >= 2 and focus["year"].iloc[1] - focus["year"].iloc[0] > 1:
        y0, y1 = int(focus["year"].iloc[0]), int(focus["year"].iloc[1])
        s0, s1 = float(focus["share"].iloc[0]), float(focus["share"].iloc[1])
        note = pd.DataFrame({"year": [(y0 + y1) / 2], "share": [(s0 + s1) / 2],
                             "txt": [f"no data {y0 + 1}–{y1 - 1}"]})
        layers.append(
            alt.Chart(note).mark_text(fontSize=13, fontStyle="italic", color=HIGHLIGHT_TEXT, dy=-14)
            .encode(x="year:Q", y="share:Q", text="txt:N")
        )

    return (
        alt.layer(*layers)
        .properties(height=440)
        .configure_view(strokeWidth=0)
        .configure(background="transparent")
    )


def build_growth_chart(g: pd.DataFrame, first: int, year: int) -> alt.LayerChart:
    """Horizontal bars: rise in share since ``first``, largest first, US highlighted."""
    g = g.assign(role=role)
    lo, hi = float(g["rise"].min()), float(g["rise"].max())
    y = alt.Y("region:N", sort=list(g["region"]), title=None,
              axis=alt.Axis(labelFontSize=13, labelLimit=260))
    x = alt.X(
        "rise:Q", title=f"Percentage points, {first} to {year}",
        scale=alt.Scale(domain=[min(0.0, lo * 1.2), hi * 1.25]),
        axis=alt.Axis(labelFontSize=13, titleFontSize=13, grid=False, format="+.1f"),
    )
    color = alt.Color("role:N", scale=alt.Scale(domain=["focus", "context"],
                                                range=[HIGHLIGHT, CONTEXT]), legend=None)
    bars = alt.Chart(g).mark_bar(cornerRadiusEnd=3).encode(
        x=x, y=y, color=color,
        tooltip=[alt.Tooltip("region:N", title="Region"),
                 alt.Tooltip("rise:Q", title="Rise (points)", format="+.2f")],
    )
    labels = alt.Chart(g).mark_text(align="left", dx=6, fontSize=13, fontWeight="bold").encode(
        x=x, y=y, text="label:N",
        color=alt.condition("datum.role == 'focus'",
                            alt.value(HIGHLIGHT_TEXT), alt.value(CONTEXT_TEXT)),
    )
    return (
        alt.layer(bars, labels)
        .properties(height=440)
        .configure_view(strokeWidth=0)
        .configure(background="transparent")
    )


def render() -> None:
    st.html('<style>[data-testid="stMetricValue"] { color: #C46A10; }</style>')
    st.header("Electricity Demand")
    st.markdown(
        "**What share of electricity demand do data centres take, and how fast is that "
        "share rising in the United States compared with the rest of the world?**"
    )

    if not DATA_FILE.exists():
        st.error(f"Missing source file: `data/{DATA_FILE.name}`. Download it from {SOURCE_URL}.")
        return

    df, value_col = load_data()
    years = sorted(int(y) for y in df["year"].unique())
    first, latest = years[0], years[-1]

    def val(region: str, year: int) -> float:
        return float(df.loc[(df["region"] == region) & (df["year"] == year), "share"].iloc[0])

    # --- Year picker for the cards, the ranking chart and the summary ----------
    year = st.segmented_control(
        "Show the cards and ranking for", years[1:], default=latest, key="tab3_year",
    ) or latest
    i = years.index(year)
    prev = years[i - 1]  # previous year with data (2023's is 2020)

    us_now, us_prev, us_first = val(FOCUS, year), val(FOCUS, prev), val(FOCUS, first)
    world_now = val("World", year)
    diff = us_now - us_prev
    rate = diff / (year - prev)  # points per year over the latest period, so the 2020 gap compares fairly
    if i >= 2:
        before = years[i - 2]
        rate_before = (us_prev - val(FOCUS, before)) / (prev - before)
        rate_note = f"was {rate_before:+.1f} a year, {before} to {prev}"
    else:
        rate_before, rate_note = None, f"first period in the file"

    g = growth_table(df, year)
    us_rank = int(g.index[g["region"] == FOCUS][0]) + 1

    # --- Summary cards -----------------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"US data centre share, {year}", f"{us_now:.1f}%",
              f"{diff:+.1f} points since {prev}", delta_color="off", border=True)
    c2.metric(f"Growth since {first}", f"{us_now / us_first:.1f}×",
              f"{us_now - us_first:+.1f} points", delta_color="off", border=True)
    c3.metric(f"Yearly rise, {prev} to {year}", f"{rate:+.1f} pts a year",
              rate_note, delta_color="off", border=True)
    c4.metric(f"US share vs world share, {year}", f"{us_now / world_now:.1f}×",
              f"World: {world_now:.1f}%", delta_color="off", border=True)

    # --- Charts ------------------------------------------------------------------
    left, right = st.columns([3, 2])
    with left.container(border=True):
        options = sorted(df["region"].unique(), key=lambda r: (r != FOCUS, r))
        chosen = st.multiselect(
            "Regions to compare (the United States is always highlighted)",
            options, default=[r for r in DEFAULT_REGIONS if r in options],
            max_selections=MAX_REGIONS, key="tab3_regions",
        )
        if FOCUS not in chosen:
            chosen = [FOCUS] + chosen[:MAX_REGIONS - 1]
        st.altair_chart(build_chart(df[df["region"].isin(chosen)]), **fit(st.altair_chart))
        st.caption(
            "Hover over the chart to see every region's value for that year. "
            "Dots mark the years the source has values for. Dashed segments cross years "
            "where the source has no values, so the line does not invent numbers for them."
        )
    with right.container(border=True):
        st.markdown(f"**Rise in share since {first}, every region in the file**")
        st.altair_chart(build_growth_chart(g, first, year), **fit(st.altair_chart))
        st.caption(
            f"Percentage points between {first} and {year}, largest first. "
            f"The United States ranks {us_rank} of {len(g)}."
        )

    # --- Plain-language summary ---------------------------------------------------
    rank_text = ("the largest rise of any region in the file" if us_rank == 1
                 else f"ranked {us_rank} of {len(g)} regions")
    if rate_before is None:
        speed = ""
    elif rate > rate_before:
        speed = " The yearly rise is getting larger, not smaller."
    else:
        speed = " The yearly rise is smaller than in the period before."
    st.info(
        f"**What this means for Dana:** in {year}, data centres used about {us_now:.1f}% of US "
        f"electricity, {us_now / world_now:.1f} times the world share. The US share has risen "
        f"{us_now - us_first:+.1f} points since {first}, {rank_text}.{speed} For the key question, "
        f"this is the load the grid must absorb if construction keeps pace with AI use, and the "
        f"capacity left idle if it does not. The series covers **all** data centres, not only AI "
        f"ones, so it is an upper bound on AI-driven demand."
    )

    # --- Trace: every card back to the raw file ---------------------------------
    with st.expander(f"Trace the headline number ({us_now:.1f}%) to the source file"):
        # Read as text so the table shows every digit exactly as stored in the file.
        raw = pd.read_csv(DATA_FILE, dtype=str, keep_default_na=False)
        ent = [c for c in raw.columns if c.lower() == "entity"][0]
        yr = [c for c in raw.columns if c.lower() == "year"][0]

        def cell(region: str, yr_: int) -> str:
            return raw[(raw[ent] == region) & (raw[yr] == str(yr_))][value_col].iloc[0]

        row = raw[(raw[ent] == FOCUS) & (raw[yr] == str(year))]
        raw_value, prev_value = cell(FOCUS, year), cell(FOCUS, prev)
        first_value, world_value = cell(FOCUS, first), cell("World", year)
        raw_diff = float(raw_value) - float(prev_value)
        st.markdown(f"1. File: `data/{DATA_FILE.name}` (unchanged OWID download)")
        st.markdown(f"2. Filter rows where *{ent}* = `{FOCUS}` and *{yr}* = `{year}`:")
        st.dataframe(row, hide_index=True, **fit(st.dataframe))
        st.markdown(
            f"3. Column *{value_col}* holds `{raw_value}`. The unit is already percent, "
            f"so no conversion is needed."
        )
        st.markdown(f"4. Round to one decimal place: `{raw_value}` → **{float(raw_value):.1f}%**, "
                    f"the figure on the first card.")
        st.markdown(
            f"5. The first card's change figure uses the {prev} row: `{raw_value}` − `{prev_value}` = "
            f"`{raw_diff:.4f}` → **{raw_diff:+.1f} points**."
        )
        st.markdown(
            f"6. Second card uses the United States {first} row (`{first_value}`): "
            f"`{raw_value}` ÷ `{first_value}` = **{float(raw_value) / float(first_value):.1f}×**, "
            f"and `{raw_value}` − `{first_value}` = **{float(raw_value) - float(first_value):+.1f} points**."
        )
        st.markdown(
            f"7. Third card divides step 5 by the years between {prev} and {year}: "
            f"`{raw_diff:.4f}` ÷ {year - prev} = **{rate:+.1f} points a year**."
        )
        st.markdown(
            f"8. Fourth card uses the World {year} row (`{world_value}`): "
            f"`{raw_value}` ÷ `{world_value}` = **{float(raw_value) / float(world_value):.1f}×**, "
            f"and the world value rounds to **{float(world_value):.1f}%**."
        )
        st.markdown(
            f"9. The ranking chart repeats the subtraction in step 6 for every region: "
            f"its {year} value minus its {first} value."
        )

    with st.expander("All data used in this tab"):
        wide = df.pivot(index="region", columns="year", values="share").round(2)
        st.dataframe(wide, **fit(st.dataframe))

    st.caption(
        f"Source: {SOURCE_TEXT}. [{SOURCE_URL}]({SOURCE_URL}). "
        f"Source last updated {SOURCE_UPDATED}; file downloaded {FILE_DOWNLOADED}. "
        "Share = data centre electricity use (IEA) ÷ total electricity demand (Ember). "
        "Includes general-purpose and AI data centres; the source does not separate AI."
    )


if __name__ == "__main__":
    # Lets you preview the tab on its own: streamlit run tab3_electricity.py
    st.set_page_config(page_title="Electricity Demand", layout="wide")
    render()
