"""Tab 4: Demand Comparison.

Question for Dana: is actual AI use growing at the same pace as data centre
construction?

Supply: US Census Bureau monthly construction spending on data centres
(constant 2021 US$), published by Our World in Data. Same file as Tab 1.
Demand: US Census Bureau Business Trends and Outlook Survey (BTOS), share of
US employer businesses that used AI in the last two weeks.

The two series have different units (dollars and % of firms), so each is
indexed to 100 in the first month both have data. A steeper line means
faster growth, whatever the unit.

BTOS changed its AI question on 17 Nov 2025, and no data was collected during
the Oct to Nov 2025 federal shutdown. The two wordings are kept apart as two
comparison windows and are never joined into one line, because the jump
between them comes from the new definition, not from new users.

All source files in data/ are kept exactly as downloaded. Every step from raw
cell to displayed number is in this file, and the trace expander repeats it
on screen.
"""

from __future__ import annotations

import datetime as dt
import inspect
import math
import re
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

DATA = Path(__file__).parent / "data"
CONSTRUCTION_FILE = DATA / "monthly-spending-data-center-us.csv"
BTOS_NOW_FILE = DATA / "National.xlsx"             # revised AI question, Nov 2025 onward
BTOS_OLD_FILE = DATA / "AI Core Questions.xlsx"    # original AI question, Sep 2023 to Sep 2025

CONSTRUCTION_URL = "https://ourworldindata.org/grapher/monthly-spending-data-center-us"
BTOS_URL = "https://www.census.gov/hfp/btos/data_downloads"

# Sheet names as published by the Census Bureau.
NOW_SHEET, NOW_SE_SHEET = "Response Estimates", "Response Standard Errors"
OLD_SHEET, OLD_SE_SHEET = "National Estimates", "National SE"
DATES_SHEET = "Collection and Reference Dates"

# Decision rule. The group proposal says: if AI use grows at least as fast as
# construction, the expansion keeps pace; if construction grows clearly faster,
# it is running ahead; if the two are close, the data cannot settle it.
# This tab makes "clearly" measurable: AI use index more than 10% below the
# construction index at the end of a window. The 10% band is several times
# wider than the BTOS sampling error on the index (shown in the trace).
PACE_BAND = 0.10

SUPPLY, DEMAND = "Construction spending", "Firms using AI"
SUPPLY_COLOR, DEMAND_COLOR = "#C46A10", "#2B6CB0"       # amber = supply (app theme), blue = demand
SUPPLY_TEXT, DEMAND_TEXT = "#A85A0C", "#245C96"         # darker versions for text labels
MUTED = "#766D66"

# The cards carry no up/down meaning, so hide the delta arrow where Streamlit supports it.
NO_ARROW = {"delta_arrow": "off"} if "delta_arrow" in inspect.signature(st.metric).parameters else {}

WINDOWS = {
    "old": {"short": "Original question",
            "wording": "AI used “in producing goods or services”",
            "file": BTOS_OLD_FILE, "sheet": OLD_SHEET, "se_sheet": OLD_SE_SHEET},
    "now": {"short": "Revised question",
            "wording": "AI used “in any of its business functions”",
            "file": BTOS_NOW_FILE, "sheet": NOW_SHEET, "se_sheet": NOW_SE_SHEET},
}


# ---------------------------------------------------------------------------
# Loading the raw files
# ---------------------------------------------------------------------------

def _period_code(v) -> str | None:
    """Turn a BTOS period header ('202618', 202618 or 202618.0) into '202618'."""
    if v is None:
        return None
    s = str(v).strip()
    if re.fullmatch(r"\d{6}(\.0)?", s):
        return s[:6]
    return None


def _pct(cell) -> float:
    """'23.2%' -> 23.2. '.' (no estimate) -> NaN."""
    if cell is None:
        return math.nan
    if isinstance(cell, (int, float)):
        return float(cell) * 100 if cell <= 1 else float(cell)
    s = str(cell).strip().rstrip("%")
    try:
        return float(s)
    except ValueError:
        return math.nan


def _excel_date(v) -> pd.Timestamp:
    if isinstance(v, (dt.datetime, dt.date)):
        return pd.Timestamp(v)
    if isinstance(v, (int, float)):
        return pd.Timestamp("1899-12-30") + pd.Timedelta(days=float(v))
    return pd.to_datetime(str(v), format="%m/%d/%Y")


def _ai_use_row(ws) -> tuple[dict, int, dict]:
    """Find the 'used AI in the last two weeks: Yes' row in a BTOS sheet.

    Matched on the question text rather than a fixed row number, so a new
    question added above it in a later release does not break the tab.
    Returns (period -> raw cell text, Excel row number, period -> column letter).
    """
    rows = ws.iter_rows(values_only=True)
    header = next(rows)
    cols = {i: _period_code(h) for i, h in enumerate(header) if _period_code(h)}
    for r_num, row in enumerate(rows, start=2):
        question = str(row[1] or "")
        answer = str(row[3] or "").strip()
        if (answer == "Yes" and "last two weeks" in question
                and re.search(r"Artificial Intelligence|\bAI\b", question)):
            raw = {code: ("" if row[i] is None else str(row[i])) for i, code in cols.items()}
            letters = {code: get_column_letter(i + 1) for i, code in cols.items()}
            return raw, r_num, letters
    raise ValueError(f"No AI-use row found in sheet '{ws.title}'")


@st.cache_data
def load_btos(key: str) -> dict:
    """Raw AI-use estimates and standard errors for one question wording."""
    w = WINDOWS[key]
    wb = load_workbook(w["file"], read_only=True, data_only=True)
    raw, row_num, letters = _ai_use_row(wb[w["sheet"]])
    se_raw, _, _ = _ai_use_row(wb[w["se_sheet"]])
    wb.close()
    return {"raw": raw, "row": row_num, "letters": letters, "se_raw": se_raw}


@st.cache_data
def load_dates() -> pd.DataFrame:
    """Reference period of every BTOS sample period (Smpdt), from National.xlsx.

    The same period codes are used in both BTOS files, so one lookup serves both.
    """
    wb = load_workbook(BTOS_NOW_FILE, read_only=True, data_only=True)
    rows = list(wb[DATES_SHEET].iter_rows(values_only=True))
    wb.close()
    header = [str(h or "").strip().lower() for h in rows[0]]
    i_code = header.index("smpdt")
    i_start = next(i for i, h in enumerate(header) if h.startswith("reference period start") or h == "ref start")
    i_end = next(i for i, h in enumerate(header) if h.startswith("ref end"))
    out = []
    for r_num, row in enumerate(rows[1:], start=2):
        code = _period_code(row[i_code]) if i_code < len(row) else None
        if code and row[i_end] is not None:
            out.append({"period": code, "ref_start": _excel_date(row[i_start]),
                        "ref_end": _excel_date(row[i_end]), "dates_row": r_num})
    return pd.DataFrame(out)


@st.cache_data
def load_construction() -> pd.DataFrame:
    raw = pd.read_csv(CONSTRUCTION_FILE)
    cols = {c.lower(): c for c in raw.columns}
    value_col = [c for c in raw.columns if c.lower() not in ("entity", "code", "month", "year", "day")][0]
    df = raw[raw[cols["entity"]] == "United States"].copy()
    df["month"] = pd.to_datetime(df[cols["month"]], format="%Y-%m")
    df["csv_line"] = df.index + 2          # line 1 is the header
    return df.rename(columns={value_col: "spend"})[["month", "spend", "csv_line"]].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Turning raw values into the comparison
# ---------------------------------------------------------------------------

def monthly_ai(key: str, dates: pd.DataFrame) -> pd.DataFrame:
    """Average the two-week BTOS estimates into calendar months.

    Each estimate is placed in the month its reference period ends, then the
    estimates in a month are averaged (usually two, sometimes three).
    """
    b = load_btos(key)
    d = dates.copy()
    d["pct"] = d["period"].map(lambda p: _pct(b["raw"].get(p)))
    d["se"] = d["period"].map(lambda p: _pct(b["se_raw"].get(p)))
    d = d.dropna(subset=["pct"])
    d["month"] = d["ref_end"].dt.to_period("M").dt.to_timestamp()
    g = d.groupby("month")
    out = g.agg(ai=("pct", "mean"), periods=("period", list), n=("pct", "size")).reset_index()
    # Standard error of a mean of independent estimates: sqrt(sum se^2) / n.
    out["ai_se"] = g["se"].apply(lambda s: math.sqrt((s ** 2).sum()) / len(s)).values
    return out


def window_months(key: str, dates: pd.DataFrame, spend: pd.DataFrame) -> list[pd.Timestamp]:
    """Months where both the AI-use series and construction spending have a value."""
    ai = monthly_ai(key, dates)
    return sorted(set(ai["month"]) & set(spend["month"]))


def build_window(key: str, dates: pd.DataFrame, spend: pd.DataFrame,
                 start: pd.Timestamp | None = None, stop: pd.Timestamp | None = None) -> dict:
    """Index both series to 100 in the first month of the window (start to stop, inclusive)."""
    ai = monthly_ai(key, dates)
    both = ai.merge(spend, on="month", how="inner").sort_values("month").reset_index(drop=True)
    if start is not None:
        both = both[(both["month"] >= start) & (both["month"] <= stop)].reset_index(drop=True)
    base, end = both.iloc[0], both.iloc[-1]
    both["idx_supply"] = both["spend"] / base["spend"] * 100
    both["idx_demand"] = both["ai"] / base["ai"] * 100
    months = (end["month"].year - base["month"].year) * 12 + end["month"].month - base["month"].month
    ratio = both["idx_demand"].iloc[-1] / both["idx_supply"].iloc[-1]
    return {"key": key, "df": both, "base": base, "end": end, "months": months, "ratio": ratio,
            "supply_end": both["idx_supply"].iloc[-1], "demand_end": both["idx_demand"].iloc[-1]}


def verdict(ratio: float) -> tuple[str, str]:
    if ratio >= 1:
        return "AI use kept pace", "AI use grew at least as fast as construction spending."
    if ratio >= 1 - PACE_BAND:
        return "Too close to call", "The gap is less than 10%, too small to call either way."
    return "Building ran ahead", "Construction spending grew clearly faster than AI use."


DANA_NOTE = {
    "AI use kept pace": "On this window, the new data centre load is tracking real use.",
    "Too close to call": "The data cannot separate the two, so the answer rests on whether Dana trusts pre-leasing.",
    "Building ran ahead": "The latest building wave is outpacing measured use, so part of the new data centre load "
                          "may not be permanent.",
}


def annualised(index_end: float, months: int) -> float:
    return ((index_end / 100) ** (12 / months) - 1) * 100


def mlabel(ts: pd.Timestamp) -> str:
    return ts.strftime("%b %Y")


def window_title(w: dict) -> str:
    meta = WINDOWS[w["key"]]
    return f"{meta['short']}: {mlabel(w['base']['month'])} to {mlabel(w['end']['month'])}"


# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------

def panel(w: dict, y_max: float, show_legend: bool) -> alt.LayerChart:
    df = w["df"]
    long = pd.concat([
        pd.DataFrame({"month": df["month"], "series": SUPPLY, "index": df["idx_supply"]}),
        pd.DataFrame({"month": df["month"], "series": DEMAND, "index": df["idx_demand"]}),
    ])
    wide = df.assign(
        spend_b=df["spend"] / 1e9,
    )[["month", "idx_supply", "idx_demand", "spend_b", "ai"]]

    x = alt.X("month:T", title=None,
              axis=alt.Axis(format="%b %y", labelFontSize=13, grid=False, labelAngle=0, tickCount=6))
    y = alt.Y("index:Q", title="Index (first month of window = 100)",
              scale=alt.Scale(domain=[0, y_max]),
              axis=alt.Axis(labelFontSize=13, titleFontSize=13, tickCount=6))
    color = alt.Color("series:N",
                      scale=alt.Scale(domain=[SUPPLY, DEMAND], range=[SUPPLY_COLOR, DEMAND_COLOR]),
                      legend=alt.Legend(orient="top", title=None, labelFontSize=13, symbolStrokeWidth=3)
                      if show_legend else None)

    hover = alt.selection_point(nearest=True, on="pointerover", fields=["month"], empty=False,
                                name=f"hover_{w['key']}")

    baseline = alt.Chart(pd.DataFrame({"index": [100]})).mark_rule(
        color=MUTED, strokeDash=[4, 4], strokeWidth=1).encode(y="index:Q")
    lines = alt.Chart(long).mark_line(strokeWidth=2.5, strokeCap="round").encode(x=x, y=y, color=color)
    points = alt.Chart(long).mark_point(filled=True, opacity=1).encode(
        x=x, y=y, color=color,
        size=alt.condition(hover, alt.value(140), alt.value(36)),
    )
    guide = alt.Chart(wide).mark_rule(color=MUTED, strokeWidth=1.2).encode(
        x="month:T",
        opacity=alt.condition(hover, alt.value(0.6), alt.value(0)),
        tooltip=[
            alt.Tooltip("month:T", title="Month", format="%B %Y"),
            alt.Tooltip("idx_supply:Q", title=f"{SUPPLY} (index)", format=".1f"),
            alt.Tooltip("spend_b:Q", title="Spending (US$ bn, 2021 prices)", format=".2f"),
            alt.Tooltip("idx_demand:Q", title=f"{DEMAND} (index)", format=".1f"),
            alt.Tooltip("ai:Q", title="Firms using AI (%)", format=".2f"),
        ],
    ).add_params(hover)

    last = long[long["month"] == long["month"].max()].copy()
    last["label"] = last.apply(lambda r: f"{'Build' if r['series'] == SUPPLY else 'AI use'} {r['index']:.0f}",
                               axis=1)
    labels = alt.Chart(last).mark_text(align="left", dx=8, fontSize=13, fontWeight="bold").encode(
        x="month:T", y="index:Q", text="label:N",
        color=alt.Color("series:N", scale=alt.Scale(domain=[SUPPLY, DEMAND], range=[SUPPLY_TEXT, DEMAND_TEXT]),
                        legend=None),
    )

    return alt.layer(baseline, lines, guide, points, labels).properties(
        title=alt.Title(window_title(w), subtitle=WINDOWS[w["key"]]["wording"],
                        fontSize=14, subtitleFontSize=12, subtitleColor=MUTED, anchor="start"),
        height=380,
    )


def build_chart(windows: list[dict]) -> alt.HConcatChart:
    top = max(max(w["df"]["idx_supply"].max(), w["df"]["idx_demand"].max()) for w in windows)
    y_max = math.ceil(top * 1.08 / 25) * 25
    # Wider panel for the longer window so a month takes the same width in both.
    total = sum(w["months"] for w in windows)
    panels = [panel(w, y_max, show_legend=(i == 0)).properties(width=max(220, int(820 * w["months"] / total)))
              for i, w in enumerate(windows)]
    return (alt.hconcat(*panels, spacing=36)
            .resolve_scale(y="shared", color="shared")
            .configure_view(strokeWidth=0)
            .configure(background="transparent")
            .configure_title(color="#2E2622"))


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

CSS = """
<style>
[data-testid="stMetric"] { transition: box-shadow .25s ease, transform .25s ease, border-color .25s ease; }
[data-testid="stMetric"]:hover { transform: translateY(-3px); border-color: #5CF2FF !important;
  box-shadow: 0 0 0 1px #5CF2FF, 0 0 16px rgba(92,242,255,.5), 0 0 30px rgba(255,92,214,.2); }
[data-testid="stMetricValue"] { color: #C46A10; }
</style>
"""


def render() -> None:
    st.html(CSS)
    st.header("📈 Demand Comparison")
    st.markdown("**Is actual AI use growing at the same pace as data centre construction?**")
    st.markdown(
        "Tabs 1 to 3 show how much is being built. This tab checks it against how many US businesses "
        "actually use AI. Both series are set to **100** in the first month they share, so the steeper "
        "line is the one growing faster."
    )

    missing = [p.name for p in (CONSTRUCTION_FILE, BTOS_NOW_FILE, BTOS_OLD_FILE) if not p.exists()]
    if missing:
        st.error("Missing source file(s) in `data/`: " + ", ".join(f"`{m}`" for m in missing)
                 + f". Construction CSV: {CONSTRUCTION_URL}. BTOS workbooks: {BTOS_URL} "
                   "(National, and Historical Data → AI Core Questions (Original)).")
        return

    dates = load_dates()
    spend = load_construction()
    full = {k: window_months(k, dates, spend) for k in ("old", "now")}
    latest_ai = monthly_ai("now", dates).iloc[-1]
    btos_now = load_btos("now")
    latest_period = max(p for p, v in btos_now["raw"].items() if not math.isnan(_pct(v)))

    # --- Month-range sliders ---------------------------------------------------
    # Dana can move the start and end month of each window. Everything below
    # (cards, chart, verdict, trace) is recalculated from the months she picks.
    # The defaults are the full windows.
    cards_box = st.container()
    st.markdown("**Choose the months to compare.** The first month picked becomes 100 for both lines.")
    chart_box = st.container(border=True)
    spans = {}
    with chart_box:
        s_old, s_now = st.columns([max(len(full["old"]), 1), max(len(full["now"]), 1) + 4], gap="large")
        for col, key in ((s_old, "old"), (s_now, "now")):
            months = full[key]
            pick = col.select_slider(
                f"{WINDOWS[key]['short']} ({WINDOWS[key]['wording']})",
                options=months, value=(months[0], months[-1]),
                format_func=lambda m: m.strftime("%b %Y"), key=f"tab4_range_{key}",
            )
            if pick[0] == pick[1]:
                col.warning("Pick two different months to compare growth. Showing the full window for now.",
                            icon="↔️")
                pick = (months[0], months[-1])
            spans[key] = pick
    windows = [build_window(k, dates, spend, *spans[k]) for k in ("old", "now")]
    old, now = windows

    # --- Summary cards ------------------------------------------------------
    c1, c2, c3 = cards_box.columns(3)
    for col, w in ((c1, old), (c2, now)):
        head, _ = verdict(w["ratio"])
        col.metric(
            f"{window_title(w)}", head,
            f"AI use {w['demand_end']:.0f} vs build {w['supply_end']:.0f} (start = 100)",
            delta_color="off", border=True, **NO_ARROW,
            help=f"{WINDOWS[w['key']]['wording']}. Index values in {mlabel(w['end']['month'])}.",
        )
    c3.metric(
        "Latest share of US firms using AI", f"{_pct(btos_now['raw'][latest_period]):.1f}%",
        f"Period {latest_period} · build data ends {mlabel(spend['month'].max())}",
        delta_color="off", border=True, **NO_ARROW,
    )

    # --- Main chart ---------------------------------------------------------
    with chart_box:
        st.altair_chart(build_chart(windows), width="stretch")
        st.caption(
            "Hover over either panel to see both index values and the raw numbers for that month. "
            "The panels are separate because the Census Bureau changed its AI question in November 2025 "
            "and collected no data during the October to November 2025 shutdown. The jump from about 10% "
            "to 17% of firms between the two wordings comes from the new definition, so the two AI lines "
            "are never joined."
        )

    # --- What it means --------------------------------------------------------
    o_head, _ = verdict(old["ratio"])
    n_head, n_text = verdict(now["ratio"])
    st.info(
        f"**What this means for Dana:** from {mlabel(old['base']['month'])} to {mlabel(old['end']['month'])}, "
        f"the share of US firms using AI went from {old['base']['ai']:.2f}% to {old['end']['ai']:.2f}% "
        f"(index {old['demand_end']:.0f}) while construction spending reached index {old['supply_end']:.0f} "
        f"({o_head.lower().replace("ai use", "AI use")}). Under the revised question, from {mlabel(now['base']['month'])} "
        f"to {mlabel(now['end']['month'])}, AI use reached index {now['demand_end']:.0f} and construction "
        f"spending reached {now['supply_end']:.0f}. "
        f"In yearly terms that is {annualised(now['demand_end'], now['months']):.0f}% growth in AI use "
        f"against {annualised(now['supply_end'], now['months']):.0f}% in construction. "
        f"**{n_head}:** {n_text} {DANA_NOTE[n_head]} The recent window is only {now['months']} months long, "
        f"so this is an early signal, not a settled trend.",
        icon="💡",
    )

    # --- Trace ----------------------------------------------------------------
    trace(now, dates)

    # --- Robustness -------------------------------------------------------------
    with st.expander("🧪 Does the answer depend on which months are picked?"):
        rows = []
        for w in windows:
            df = w["df"]
            k = min(3, len(df) // 2)
            sup = df["spend"].tail(k).mean() / df["spend"].head(k).mean() * 100
            dem = df["ai"].tail(k).mean() / df["ai"].head(k).mean() * 100
            rows.append({
                "Window": window_title(w),
                "Single months: AI use": round(w["demand_end"], 1),
                "Single months: build": round(w["supply_end"], 1),
                "Single months: verdict": verdict(w["ratio"])[0],
                f"{k}-month averages: AI use": round(dem, 1),
                f"{k}-month averages: build": round(sup, 1),
                f"{k}-month averages: verdict": verdict(dem / sup)[0],
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.markdown(
            "The second set compares the average of the first three months with the average of the last "
            "three, so one unusual month at either end cannot decide the answer. Construction spending is "
            "not seasonally adjusted, which is another reason to check this."
        )
        g = pd.DataFrame([{
            "Window": window_title(w), "Months": w["months"],
            "AI use, % per year": round(annualised(w["demand_end"], w["months"]), 1),
            "Construction, % per year": round(annualised(w["supply_end"], w["months"]), 1),
        } for w in windows])
        st.markdown("The two windows have different lengths, so here is the same growth in yearly terms:")
        st.dataframe(g, hide_index=True, width="stretch")

    # --- Limits -----------------------------------------------------------------
    with st.expander("⚠️ What this comparison can and cannot tell Dana"):
        st.markdown(
            "- **Construction covers all data centres**, not only AI ones. No public source separates them, "
            "so the build line is an upper bound on AI-driven building.\n"
            "- **Spending is in constant 2021 US dollars** (Our World in Data adjusts the Census figures with "
            "construction price indexes), so the build line is not inflated by rising prices. Recent months "
            "are preliminary and get revised.\n"
            "- **BTOS measures how many firms use AI, not how much.** A firm running one chatbot and a firm "
            "training models both count once. Heavy users could be growing faster than the share of users. "
            "The share also cannot pass 100%, so it will slow down at some point whatever happens to demand.\n"
            "- **BTOS covers US employer businesses.** It leaves out households and government, and AI use "
            "served from US data centres to users abroad.\n"
            "- **Two windows, two definitions.** The original and revised AI questions measure different "
            "things, so each window is compared only with itself.\n"
            "- **Why no training compute line.** The proposal listed Epoch AI training compute as a possible "
            "second series. It was left out because it measures how much compute frontier labs spend training "
            "models, which is itself a form of building rather than use, and its growth (several times per "
            "year) would squash the other two lines flat unless the axis were made logarithmic."
        )

    with st.expander("📋 All data used in this tab"):
        for w in windows:
            df = w["df"]
            st.markdown(f"**{window_title(w)}** ({WINDOWS[w['key']]['wording']})")
            show = pd.DataFrame({
                "Month": df["month"].dt.strftime("%Y-%m"),
                "Construction (US$, 2021 prices)": df["spend"].map("{:,.0f}".format),
                "Construction index": df["idx_supply"].round(1),
                "BTOS periods averaged": df["periods"].map(", ".join),
                "Firms using AI (%)": df["ai"].round(2),
                "AI use index": df["idx_demand"].round(1),
            })
            st.dataframe(show, hide_index=True, width="stretch")

    st.caption(
        f"Sources: U.S. Census Bureau, Value of Construction Put in Place; U.S. Bureau of Labor Statistics; "
        f"processed by Our World in Data ([{CONSTRUCTION_URL}]({CONSTRUCTION_URL})). "
        f"U.S. Census Bureau, Business Trends and Outlook Survey, National.xlsx and AI Core Questions.xlsx "
        f"([{BTOS_URL}]({BTOS_URL})). AI use = estimated share of employer businesses answering “Yes” to "
        f"using AI in the last two weeks."
    )


def trace(w: dict, dates: pd.DataFrame) -> None:
    """Walk one displayed number back to the raw cells, using the raw text from the files."""
    b = load_btos(w["key"])
    base, end = w["base"], w["end"]
    with st.expander(f"🔍 Trace the AI use index ({w['demand_end']:.1f}) and build index "
                     f"({w['supply_end']:.1f}) for {mlabel(end['month'])} back to the source files"):
        st.markdown(f"**A. AI use index: file `data/{BTOS_NOW_FILE.name}`, sheet *{NOW_SHEET}*, "
                    f"row {b['row']} (question 7, answer “Yes”).**")
        drows = dates[dates["period"].isin(list(base["periods"]) + list(end["periods"]))]
        st.markdown(
            f"1. Each column is a two-week survey period. Sheet *{DATES_SHEET}* gives the reference period "
            f"of each code, which decides its month:"
        )
        st.dataframe(pd.DataFrame({
            "Period (Smpdt)": drows["period"],
            "Reference period": drows["ref_start"].dt.strftime("%d %b %Y") + " to "
                                + drows["ref_end"].dt.strftime("%d %b %Y"),
            "Counted in month": drows["ref_end"].dt.strftime("%b %Y"),
        }), hide_index=True, width="stretch")

        def cells(periods):
            return [(p, f"{b['letters'][p]}{b['row']}", b["raw"][p]) for p in periods]

        def avg_line(name, periods):
            c = cells(periods)
            parts = " + ".join(f"`{v}` (cell {ref})" for _, ref, v in c)
            vals = [_pct(v) for _, _, v in c]
            return f"{name}: ({parts}) ÷ {len(vals)} = **{sum(vals) / len(vals):.2f}%**", sum(vals) / len(vals)

        line_b, b_val = avg_line(f"Base month, {mlabel(base['month'])}", base["periods"])
        line_e, e_val = avg_line(f"End month, {mlabel(end['month'])}", end["periods"])
        st.markdown(f"2. {line_b}")
        st.markdown(f"3. {line_e}")
        st.markdown(f"4. Index = {e_val:.2f} ÷ {b_val:.2f} × 100 = **{e_val / b_val * 100:.1f}**, "
                    f"shown on the chart and card as **{e_val / b_val * 100:.0f}**.")
        rel = math.sqrt((end["ai_se"] / e_val) ** 2 + (base["ai_se"] / b_val) ** 2)
        st.markdown(
            f"5. Sampling error check: sheet *{NOW_SE_SHEET}* gives a standard error for every cell. "
            f"Combined, the 95% range on this index is about **±{1.96 * rel * e_val / b_val * 100:.1f} points**, "
            f"compared with a gap of {abs(w['supply_end'] - w['demand_end']):.0f} points to the build line."
        )

        st.markdown(f"**B. Build index: file `data/{CONSTRUCTION_FILE.name}`, column "
                    f"*Data center construction* (constant 2021 US$).**")
        raw = pd.read_csv(CONSTRUCTION_FILE, dtype=str, keep_default_na=False)
        mcol = [c for c in raw.columns if c.lower() == "month"][0]
        vcol = raw.columns[-1]
        keys = [base["month"].strftime("%Y-%m"), end["month"].strftime("%Y-%m")]
        rows = raw[raw[mcol].isin(keys)].copy()
        rows.insert(0, "CSV line", rows.index + 2)
        st.dataframe(rows, hide_index=True, width="stretch")
        b_raw, e_raw = rows[vcol].iloc[0], rows[vcol].iloc[1]
        st.markdown(f"6. Index = `{e_raw}` ÷ `{b_raw}` × 100 = **{float(e_raw) / float(b_raw) * 100:.1f}**, "
                    f"shown as **{float(e_raw) / float(b_raw) * 100:.0f}**.")
        st.markdown(
            f"7. Verdict (proposal's rule, with 'clearly faster' set at a 10% gap): {e_val / b_val * 100:.1f} ÷ {float(e_raw) / float(b_raw) * 100:.1f} "
            f"= **{w['ratio']:.2f}**. At least 1.00 means AI use kept pace; below {1 - PACE_BAND:.2f} means "
            f"building ran ahead. Result: **{verdict(w['ratio'])[0]}**."
        )


if __name__ == "__main__":
    # Preview this tab on its own: streamlit run tab4_demand.py
    st.set_page_config(page_title="Demand Comparison", page_icon="📈", layout="wide")
    # When run on its own, show the group question and persona above the tab.
    st.markdown(
        "**Group question:** Is the rapid expansion of AI data centres justified by the actual demand for AI?  \n"
        "**Persona:** Dana Reyes, an energy policy analyst deciding whether her state should build grid "
        "capacity for data centres as permanent demand."
    )
    st.caption("Tab 4 of the group app: https://ai-data-centre-expansion.streamlit.app/")
    st.divider()
    render()
