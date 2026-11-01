"""
Tab 1 - Pace of Construction: every transformation from the raw file to the file the tab reads.

Commands (run from the repo root):
  python -m src.tab1_prep                raw file -> sample -> processed file -> checks
  python -m src.tab1_prep --from-sample  sample -> processed file -> checks (no raw file needed)
  python -m src.tab1_prep --validate     checks only, on the current sample and processed file

Raw file (never edited by hand; shared with Tabs 3 and 4 so every tab shows the same numbers):
  data/monthly-spending-data-center-us.csv
    US Census Bureau, Value of Construction Put in Place (private data centre construction),
    in constant 2021 US$ using BLS producer price indexes, processed by Our World in Data.
    https://ourworldindata.org/grapher/monthly-spending-data-center-us

The steps:
  1. extract_sample()  keep the rows and columns Tab 1 uses, values unchanged -> data/sample/tab1_construction.csv
  2. monthly()         one row per month: spending in US$ billions and the 12-month average
                       -> data/processed/tab1_monthly.csv (also read by Tab 4)
  3. cards()           the five figures on the summary cards
  4. validate()        checks that can fail; the build stops if any does

No rows are dropped and no values are imputed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "monthly-spending-data-center-us.csv"
SAMPLE_FILE = ROOT / "data" / "sample" / "tab1_construction.csv"
PROCESSED_FILE = ROOT / "data" / "processed" / "tab1_monthly.csv"
SOURCE_URL = "https://ourworldindata.org/grapher/monthly-spending-data-center-us"
RETRIEVED = "2026-10-23"   # date the group downloaded the raw file from Our World in Data

# Column names exactly as they appear in the source file.
ENTITY_COL = "Entity"
CODE_COL = "Code"
MONTH_COL = "Month"
VALUE_COL = "Data center construction"   # constant 2021 US$, monthly, not seasonally adjusted

CHATGPT = pd.Timestamp("2022-11-01")     # ChatGPT was released on 30 Nov 2022


# ---------------------------------------------------------------------------
# Step 1: sample
# ---------------------------------------------------------------------------

def extract_sample() -> pd.DataFrame:
    """Keep the United States rows and the four source columns. Values are not changed."""
    raw = pd.read_csv(RAW_FILE, dtype=str, keep_default_na=False)
    sample = raw[raw[ENTITY_COL] == "United States"][[ENTITY_COL, CODE_COL, MONTH_COL, VALUE_COL]]
    SAMPLE_FILE.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(SAMPLE_FILE, index=False)
    return sample


def load_sample() -> pd.DataFrame:
    return pd.read_csv(SAMPLE_FILE)


# ---------------------------------------------------------------------------
# Step 2: processed file
# ---------------------------------------------------------------------------

def monthly(sample: pd.DataFrame) -> pd.DataFrame:
    """One row per month.

    month     YYYY-MM
    csv_line  line of this month in the raw and sample files (line 1 is the header)
    spend     spending in US$ at 2021 prices, exactly as in the source
    spend_b   spend / 1,000,000,000
    avg12_b   mean of spend_b for this month and the 11 before it (empty for the first 11 months)
    """
    df = sample.reset_index(drop=True).copy()
    df["csv_line"] = df.index + 2
    df = df.rename(columns={MONTH_COL: "month", VALUE_COL: "spend"})[["month", "csv_line", "spend"]]
    df = df.sort_values("month").reset_index(drop=True)
    df["spend_b"] = df["spend"] / 1e9
    df["avg12_b"] = df["spend_b"].rolling(12).mean()
    return df


def load_processed() -> pd.DataFrame:
    """The file the app reads, with month turned into a date."""
    df = pd.read_csv(PROCESSED_FILE)
    df["month"] = pd.to_datetime(df["month"], format="%Y-%m")
    return df


# ---------------------------------------------------------------------------
# Step 3: card figures
# ---------------------------------------------------------------------------

def _at(df: pd.DataFrame, month: pd.Timestamp) -> pd.Series:
    return df[df["month"] == month].iloc[0]


def cards(df: pd.DataFrame) -> dict:
    """The summary-card figures, all computed from the processed file.

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


# ---------------------------------------------------------------------------
# Step 4: checks
# ---------------------------------------------------------------------------

def validate(sample: pd.DataFrame, out: pd.DataFrame) -> list[tuple[str, bool, str]]:
    """Each check can fail. Returns (check, passed, detail)."""
    results = []

    def check(name: str, ok: bool, detail: str) -> None:
        results.append((name, bool(ok), detail))

    months = pd.to_datetime(out["month"], format="%Y-%m")
    check("Sample keeps the four source columns",
          list(sample.columns) == [ENTITY_COL, CODE_COL, MONTH_COL, VALUE_COL], ", ".join(sample.columns))
    check("Only United States rows", set(sample[ENTITY_COL]) == {"United States"},
          ", ".join(sorted(set(sample[ENTITY_COL]))))
    expected = pd.date_range(months.min(), months.max(), freq="MS")
    check("Every month present once, no gaps",
          len(months) == len(expected) and months.is_unique and (months.values == expected.values).all(),
          f"{len(out)} rows, {months.min():%b %Y} to {months.max():%b %Y}")
    check("No missing or negative values",
          out["spend"].notna().all() and (out["spend"] >= 0).all(), f"min {out['spend'].min():,.0f}")
    last12 = out["spend_b"].tail(12).mean()
    check("12-month average matches a manual mean of the last 12 rows",
          abs(last12 - out["avg12_b"].iloc[-1]) < 1e-9, f"{last12:.6f} bn")
    latest_raw = float(sample.loc[sample[MONTH_COL] == out["month"].iloc[-1], VALUE_COL].iloc[0])
    check("Latest card value traces to the source cell",
          abs(latest_raw / 1e9 - out["spend_b"].iloc[-1]) < 1e-12,
          f"{latest_raw:,.0f} / 1e9 = {latest_raw / 1e9:.2f} bn")
    check("Nov 2022 (ChatGPT) and the month two years before the latest both exist",
          CHATGPT in set(months) and (months.iloc[-1] - pd.DateOffset(years=2)) in set(months),
          "needed for the cards")
    return results


def report(checks: list[tuple[str, bool, str]]) -> bool:
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name} ({detail})")
    return all(ok for _, ok, _ in checks)


def build() -> dict[Path, pd.DataFrame]:
    """Processed files built from the sample, keyed by where they are saved."""
    return {PROCESSED_FILE: monthly(load_sample())}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--from-sample", action="store_true", help="rebuild the processed file from the sample")
    mode.add_argument("--validate", action="store_true", help="run the checks only")
    args = parser.parse_args()

    if args.validate:
        out = pd.read_csv(PROCESSED_FILE)
    else:
        if not args.from_sample:
            extract_sample()
            print(f"Sample written to {SAMPLE_FILE.relative_to(ROOT)}")
        for path, df in build().items():
            path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(path, index=False)
            print(f"  {path.relative_to(ROOT)} ({len(df)} rows)")
        out = pd.read_csv(PROCESSED_FILE)

    print("Checks:")
    if not report(validate(load_sample(), out)):
        sys.exit("A check failed: the processed file should not be used until it is resolved.")


if __name__ == "__main__":
    main()
