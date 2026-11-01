"""
Tab 4 - Demand Comparison: every transformation from the raw files to the files the tab reads.

Commands (run from the repo root):
  python -m src.tab4_prep                raw files -> samples -> processed file -> checks
  python -m src.tab4_prep --from-sample  samples -> processed file -> checks (no raw files needed)
  python -m src.tab4_prep --validate     checks only, on the current samples and processed file

Raw files (never edited by hand), US Census Bureau, Business Trends and Outlook Survey (BTOS):
  data/AI Core Questions.xlsx   original AI question, "in producing goods or services", Sep 2023 to Sep 2025
  data/National.xlsx            revised AI question, "in any of its business functions", Nov 2025 onward,
                                plus the sheet of reference dates for every survey period
Construction spending comes from Tab 1's processed file (data/processed/tab1_monthly.csv), so
Tabs 1 and 4 always show the same spending.

The steps:
  1. extract_samples()  the "used AI in the last two weeks: Yes" row and its standard errors, cell text
                        unchanged, with sheet, Excel row and column for each cell
                        -> data/sample/tab4_btos_ai_use.csv
                        the reference period of every survey period -> data/sample/tab4_btos_dates.csv
  2. ai_monthly()       each two-week estimate goes in the month its reference period ends; estimates in the
                        same month are averaged -> data/processed/tab4_ai_monthly.csv
  3. validate()         checks that can fail; the build stops if any does
The tab then indexes both series to 100 in the first month of the window the user picks.
"""

from __future__ import annotations

import argparse
import datetime as dt
import math
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BTOS_NOW_FILE = DATA / "National.xlsx"
BTOS_OLD_FILE = DATA / "AI Core Questions.xlsx"
SAMPLE_AI = DATA / "sample" / "tab4_btos_ai_use.csv"
SAMPLE_DATES = DATA / "sample" / "tab4_btos_dates.csv"
PROCESSED_AI = DATA / "processed" / "tab4_ai_monthly.csv"
BTOS_URL = "https://www.census.gov/hfp/btos/data_downloads"
RETRIEVED = "2026-10-23"   # date the group downloaded the BTOS files and the construction file

# Sheet names as published by the Census Bureau.
NOW_SHEET, NOW_SE_SHEET = "Response Estimates", "Response Standard Errors"
OLD_SHEET, OLD_SE_SHEET = "National Estimates", "National SE"
DATES_SHEET = "Collection and Reference Dates"

SOURCES = {
    "old": (BTOS_OLD_FILE, OLD_SHEET, OLD_SE_SHEET),
    "now": (BTOS_NOW_FILE, NOW_SHEET, NOW_SE_SHEET),
}


# ---------------------------------------------------------------------------
# Reading cells
# ---------------------------------------------------------------------------

def period_code(v) -> str | None:
    """Turn a BTOS period header ('202618', 202618 or 202618.0) into '202618'."""
    if v is None:
        return None
    s = str(v).strip()
    if re.fullmatch(r"\d{6}(\.0)?", s):
        return s[:6]
    return None


def pct(cell) -> float:
    """'23.2%' -> 23.2. '.' (no estimate) -> NaN."""
    if cell is None or (isinstance(cell, float) and math.isnan(cell)):
        return math.nan
    if isinstance(cell, (int, float)):
        return float(cell) * 100 if cell <= 1 else float(cell)
    s = str(cell).strip().rstrip("%")
    try:
        return float(s)
    except ValueError:
        return math.nan


def excel_date(v) -> pd.Timestamp:
    if isinstance(v, (dt.datetime, dt.date)):
        return pd.Timestamp(v)
    if isinstance(v, (int, float)):
        return pd.Timestamp("1899-12-30") + pd.Timedelta(days=float(v))
    return pd.to_datetime(str(v), format="%m/%d/%Y")


def ai_use_row(ws) -> tuple[dict, int, dict]:
    """Find the 'used AI in the last two weeks: Yes' row in a BTOS sheet.

    Matched on the question text rather than a fixed row number, so a new
    question added above it in a later release does not break the tab.
    Returns (period -> raw cell text, Excel row number, period -> column letter).
    """
    from openpyxl.utils import get_column_letter

    rows = ws.iter_rows(values_only=True)
    header = next(rows)
    cols = {i: period_code(h) for i, h in enumerate(header) if period_code(h)}
    for r_num, row in enumerate(rows, start=2):
        question = str(row[1] or "")
        answer = str(row[3] or "").strip()
        if (answer == "Yes" and "last two weeks" in question
                and re.search(r"Artificial Intelligence|\bAI\b", question)):
            raw = {code: ("" if row[i] is None else str(row[i])) for i, code in cols.items()}
            letters = {code: get_column_letter(i + 1) for i, code in cols.items()}
            return raw, r_num, letters
    raise ValueError(f"No AI-use row found in sheet '{ws.title}'")


# ---------------------------------------------------------------------------
# Step 1: samples
# ---------------------------------------------------------------------------

def extract_samples() -> None:
    """Copy the cells Tab 4 uses out of the two workbooks. Cell text is not changed."""
    from openpyxl import load_workbook

    rows = []
    for key, (path, sheet, se_sheet) in SOURCES.items():
        wb = load_workbook(path, read_only=True, data_only=True)
        raw, row_num, letters = ai_use_row(wb[sheet])
        se_raw, se_row, _ = ai_use_row(wb[se_sheet])
        wb.close()
        for code in raw:
            rows.append({"window": key, "file": path.name, "sheet": sheet, "excel_row": row_num,
                         "column": letters[code], "period": code, "estimate": raw[code],
                         "se_sheet": se_sheet, "se_excel_row": se_row, "standard_error": se_raw.get(code, "")})
    SAMPLE_AI.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(SAMPLE_AI, index=False)

    wb = load_workbook(BTOS_NOW_FILE, read_only=True, data_only=True)
    sheet = list(wb[DATES_SHEET].iter_rows(values_only=True))
    wb.close()
    header = [str(h or "").strip().lower() for h in sheet[0]]
    i_code = header.index("smpdt")
    i_start = next(i for i, h in enumerate(header) if h.startswith("reference period start") or h == "ref start")
    i_end = next(i for i, h in enumerate(header) if h.startswith("ref end"))
    i_pub = next((i for i, h in enumerate(header) if h.startswith("publication")), None)
    out = []
    for r_num, row in enumerate(sheet[1:], start=2):
        code = period_code(row[i_code]) if i_code < len(row) else None
        if code and row[i_end] is not None:
            pub = (excel_date(row[i_pub]) if i_pub is not None and i_pub < len(row)
                   and row[i_pub] not in (None, "") else pd.NaT)
            out.append({"period": code, "ref_start": excel_date(row[i_start]).date().isoformat(),
                        "ref_end": excel_date(row[i_end]).date().isoformat(), "dates_row": r_num,
                        "published": "" if pd.isna(pub) else pub.date().isoformat()})
    pd.DataFrame(out).to_csv(SAMPLE_DATES, index=False)


def load_ai_sample() -> pd.DataFrame:
    return pd.read_csv(SAMPLE_AI, dtype={"period": str, "estimate": str, "standard_error": str},
                       keep_default_na=False)


def load_dates() -> pd.DataFrame:
    d = pd.read_csv(SAMPLE_DATES, dtype={"period": str}, keep_default_na=False)
    for c in ("ref_start", "ref_end"):
        d[c] = pd.to_datetime(d[c])
    d["published"] = pd.to_datetime(d["published"].replace("", None))
    return d


# ---------------------------------------------------------------------------
# Step 2: processed file
# ---------------------------------------------------------------------------

def ai_monthly(sample: pd.DataFrame, dates: pd.DataFrame) -> pd.DataFrame:
    """Average the two-week estimates into calendar months, for each question wording.

    window   old (original question) or now (revised question)
    month    YYYY-MM, the month the reference period ends
    ai       mean share of firms using AI in that month (%)
    ai_se    standard error of that mean: sqrt(sum of se^2) / n (% points)
    n        number of two-week estimates averaged
    periods  survey period codes averaged, separated by ';'
    """
    out = []
    for key in ("old", "now"):
        s = sample[sample["window"] == key]
        d = dates.copy()
        est = dict(zip(s["period"], s["estimate"]))
        se = dict(zip(s["period"], s["standard_error"]))
        d["pct"] = d["period"].map(lambda p: pct(est.get(p)))
        d["se"] = d["period"].map(lambda p: pct(se.get(p)))
        d = d.dropna(subset=["pct"])
        d["month"] = d["ref_end"].dt.to_period("M").dt.to_timestamp()
        g = d.groupby("month")
        m = g.agg(ai=("pct", "mean"), n=("pct", "size"), periods=("period", ";".join)).reset_index()
        m["ai_se"] = g["se"].apply(lambda v: math.sqrt((v ** 2).sum()) / len(v)).values
        m.insert(0, "window", key)
        m["month"] = m["month"].dt.strftime("%Y-%m")
        out.append(m[["window", "month", "ai", "ai_se", "n", "periods"]])
    return pd.concat(out, ignore_index=True)


def load_processed() -> pd.DataFrame:
    """The file the tab reads, with month as a date and periods as a list."""
    df = pd.read_csv(PROCESSED_AI, dtype={"periods": str})
    df["month"] = pd.to_datetime(df["month"], format="%Y-%m")
    df["periods"] = df["periods"].str.split(";")
    return df


def build() -> dict[Path, pd.DataFrame]:
    return {PROCESSED_AI: ai_monthly(load_ai_sample(), load_dates())}


# ---------------------------------------------------------------------------
# Step 3: checks
# ---------------------------------------------------------------------------

def validate(sample: pd.DataFrame, dates: pd.DataFrame, out: pd.DataFrame) -> list[tuple[str, bool, str]]:
    checks = []
    for key in ("old", "now"):
        s = sample[sample["window"] == key]
        n_est = s["estimate"].map(pct).notna().sum()
        used = out.loc[out["window"] == key, "n"].sum()
        checks.append((f"Every '{key}' estimate with a value is used exactly once", n_est == used,
                       f"{n_est} estimates, {used} averaged"))
    with_value = set(sample.loc[sample["estimate"].map(pct).notna(), "period"])
    missing = with_value - set(dates["period"])
    checks.append(("Every survey period with an estimate has reference dates", not missing,
                   f"{len(missing)} periods without dates"))
    checks.append(("Shares are between 0 and 100%", out["ai"].between(0, 100).all(),
                   f"{out['ai'].min():.2f}% to {out['ai'].max():.2f}%"))
    checks.append(("One row per window and month (primary key)",
                   not out.duplicated(["window", "month"]).any(), f"{len(out)} rows"))
    checks.append(("Reference periods end after they start", (dates["ref_end"] >= dates["ref_start"]).all(),
                   f"{len(dates)} periods"))
    return checks


def report(checks: list[tuple[str, bool, str]]) -> bool:
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name} ({detail})")
    return all(ok for _, ok, _ in checks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tab 4 data preparation")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--from-sample", action="store_true", help="rebuild the processed file from the samples")
    mode.add_argument("--validate", action="store_true", help="run the checks only")
    args = parser.parse_args()

    if not args.validate:
        if not args.from_sample:
            extract_samples()
            print(f"Samples written to {SAMPLE_AI.relative_to(ROOT)} and {SAMPLE_DATES.relative_to(ROOT)}")
        for path, df in build().items():
            path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(path, index=False)
            print(f"  {path.relative_to(ROOT)} ({len(df)} rows)")
    print("Checks:")
    if not report(validate(load_ai_sample(), load_dates(), pd.read_csv(PROCESSED_AI))):
        sys.exit("A check failed: the processed file should not be used until it is resolved.")


if __name__ == "__main__":
    main()
