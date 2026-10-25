"""
Tab 1 - Pace of Construction: every transformation from the raw file to the numbers the tab shows.

Commands (run from the repo root):
  python -m src.tab1_prep              raw file -> processed file -> checks
  python -m src.tab1_prep --validate   checks only

Raw file (never edited by hand; shared with Tabs 3 and 4 so every tab shows the same numbers):
  data/monthly-spending-data-center-us.csv
    US Census Bureau, Value of Construction Put in Place (private data centre construction),
    in constant 2021 US$ using BLS producer price indexes, processed by Our World in Data.
    https://ourworldindata.org/grapher/monthly-spending-data-center-us

The steps:
  1. load_raw()   read the CSV exactly as downloaded
  2. monthly()    keep United States, parse the month, spending in US$ billions, 12-month average
  3. cards()      the five figures on the summary cards
  4. validate()   checks that can fail; the build stops if any does

Nothing else is changed: no rows are dropped and no values are imputed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "monthly-spending-data-center-us.csv"
PROCESSED_FILE = ROOT / "data" / "processed" / "tab1_monthly.csv"
SOURCE_URL = "https://ourworldindata.org/grapher/monthly-spending-data-center-us"

# Column names exactly as they appear in the source file.
ENTITY_COL = "Entity"
MONTH_COL = "Month"
VALUE_COL = "Data center construction"   # constant 2021 US$, monthly, not seasonally adjusted

CHATGPT = pd.Timestamp("2022-11-01")     # ChatGPT was released on 30 Nov 2022


def load_raw(path: str | Path = RAW_FILE) -> pd.DataFrame:
    """Step 1: read the raw OWID file exactly as downloaded."""
    return pd.read_csv(path)


def monthly(raw: pd.DataFrame) -> pd.DataFrame:
    """Step 2: one row per month.

    month    first day of the month (date)
    spend    spending in US$ at 2021 prices, as in the file
    spend_b  spend / 1,000,000,000
    avg12_b  mean of spend_b for this month and the 11 before it (empty for the first 11 months)
    """
    df = raw[raw[ENTITY_COL] == "United States"].copy()
    df["month"] = pd.to_datetime(df[MONTH_COL], format="%Y-%m")
    df["spend"] = df[VALUE_COL].astype(float)
    df = df.sort_values("month").reset_index(drop=True)[["month", "spend"]]
    df["spend_b"] = df["spend"] / 1e9
    df["avg12_b"] = df["spend_b"].rolling(12).mean()
    return df


def _at(df: pd.DataFrame, month: pd.Timestamp) -> pd.Series:
    return df[df["month"] == month].iloc[0]


def cards(df: pd.DataFrame) -> dict:
    """Step 3: the summary-card figures, all computed from monthly().

    same_month_growth_pct  latest month / same month a year earlier - 1, x 100 (removes seasonality)
    avg12_b                12-month average for the latest month
    since_chatgpt_x        12-month average now / 12-month average at Nov 2022
    avg_growth_pct         12-month average now / a year earlier - 1, x 100
    avg_growth_prev_pct    the same, one year earlier
    """
    latest = df.iloc[-1]
    year_ago = _at(df, latest["month"] - pd.DateOffset(years=1))
    two_ago = _at(df, latest["month"] - pd.DateOffset(years=2))
    pre_ai = _at(df, CHATGPT)
    return {
        "latest": latest, "year_ago": year_ago, "two_ago": two_ago, "pre_ai": pre_ai,
        "same_month_growth_pct": (latest["spend"] / year_ago["spend"] - 1) * 100,
        "avg12_b": latest["avg12_b"],
        "since_chatgpt_x": latest["avg12_b"] / pre_ai["avg12_b"],
        "avg_growth_pct": (latest["avg12_b"] / year_ago["avg12_b"] - 1) * 100,
        "avg_growth_prev_pct": (year_ago["avg12_b"] / two_ago["avg12_b"] - 1) * 100,
    }


def validate(raw: pd.DataFrame, df: pd.DataFrame) -> list[tuple[str, bool, str]]:
    """Step 4: checks that can fail. Returns (check, passed, detail) for each."""
    results = []

    def check(name: str, ok: bool, detail: str) -> None:
        results.append((name, bool(ok), detail))

    check("Source columns are present",
          {ENTITY_COL, MONTH_COL, VALUE_COL} <= set(raw.columns), ", ".join(raw.columns))
    check("Only United States rows", set(raw[ENTITY_COL]) == {"United States"},
          ", ".join(sorted(set(raw[ENTITY_COL]))))
    expected = pd.date_range(df["month"].min(), df["month"].max(), freq="MS")
    check("Every month present, no duplicates",
          len(df) == len(expected) and df["month"].is_unique and (df["month"].values == expected.values).all(),
          f"{len(df)} rows, {df['month'].min():%b %Y} to {df['month'].max():%b %Y}")
    check("No missing or negative values",
          df["spend"].notna().all() and (df["spend"] >= 0).all(),
          f"min {df['spend'].min():,.0f}")
    last12 = df["spend_b"].tail(12).mean()
    check("12-month average matches a manual mean of the last 12 rows",
          abs(last12 - df["avg12_b"].iloc[-1]) < 1e-12, f"{last12:.6f} bn")
    raw_latest = float(raw.loc[raw[MONTH_COL] == df["month"].iloc[-1].strftime("%Y-%m"), VALUE_COL].iloc[0])
    check("Latest card value traces to the raw cell",
          abs(raw_latest / 1e9 - df["spend_b"].iloc[-1]) < 1e-12,
          f"{raw_latest:,.0f} / 1e9 = {raw_latest / 1e9:.2f} bn")
    check("Nov 2022 (ChatGPT) and two full years before the latest month exist",
          CHATGPT in set(df["month"]) and (df["month"].iloc[-1] - pd.DateOffset(years=2)) in set(df["month"]),
          "needed for the cards")
    return results


def build(write: bool = True) -> int:
    raw = load_raw()
    df = monthly(raw)
    results = validate(raw, df)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}  ({detail})")
    if not all(ok for _, ok, _ in results):
        print("Build stopped: a check failed.")
        return 1
    if write:
        PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
        out = df.assign(month=df["month"].dt.strftime("%Y-%m"))
        out.to_csv(PROCESSED_FILE, index=False, float_format="%.6f")
        print(f"Wrote {PROCESSED_FILE.relative_to(ROOT)} ({len(out)} rows)")
    c = cards(df)
    print(f"Cards: ${c['latest']['spend_b']:.2f}bn ({c['same_month_growth_pct']:+.0f}% vs a year earlier), "
          f"12-month average ${c['avg12_b']:.2f}bn ({c['since_chatgpt_x']:.1f}x pre-ChatGPT), "
          f"average growth {c['avg_growth_pct']:+.0f}% (was {c['avg_growth_prev_pct']:+.0f}%)")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--validate", action="store_true", help="run the checks only")
    sys.exit(build(write=not parser.parse_args().validate))
