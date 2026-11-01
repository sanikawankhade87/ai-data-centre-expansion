"""
Tab 2 - Builders and Locations: every transformation applied to the Epoch AI file.

Commands (run from the repo root):
  python -m src.tab2_prep                raw file -> sample -> processed files -> checks
  python -m src.tab2_prep --from-sample  sample -> processed files -> checks (no raw file needed)
  python -m src.tab2_prep --validate     checks only, on the current sample and processed files

Source file : data/raw/data_centers.csv  (downloaded unedited from
              https://epoch.ai/data/data_centers/data_centers.csv)
Licence     : CC BY, Epoch AI, 'AI data centers', epoch.ai

The raw file has one row per AI data centre site. This module does only these things,
so any number on the page can be traced back in two steps:

  0. extract_sample()  keep the five columns the tab uses, values unchanged -> data/sample/tab2_sites.csv
  1. load()            read the CSV and keep the columns the tab uses
  2. clean()           strip Epoch's confidence tags (#confident / #likely /
                       #speculative) from Owner, and fill blank owners -> data/processed/tab2_sites_clean.csv
  3. share_table()     group by Owner or Country and sum power (MW)
                       -> data/processed/tab2_owner_share.csv and tab2_country_share.csv
  4. top_n_share()     add up the largest N groups as a % of the total (done live in the tab, for the slider)

Nothing else is changed: no rows are dropped, no values are imputed.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import pandas as pd
from urllib.request import urlretrieve

RAW_URL = "https://epoch.ai/data/data_centers/data_centers.csv"
ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "data_centers.csv"
SAMPLE_FILE = ROOT / "data" / "sample" / "tab2_sites.csv"
PROCESSED = {
    "sites": ROOT / "data" / "processed" / "tab2_sites_clean.csv",
    "Owner": ROOT / "data" / "processed" / "tab2_owner_share.csv",
    "Country": ROOT / "data" / "processed" / "tab2_country_share.csv",
}
RELEASE = "2026-10-19"     # Epoch AI release date of the downloaded file (95 sites)
DOWNLOADED = "2026-10-24"  # date the file was downloaded into data/raw/

# Column names exactly as they appear in the Epoch header row.
COL_NAME = "Name"
COL_OWNER = "Owner"
COL_COUNTRY = "Country"
COL_POWER = "Current power (MW)"  # latest IT power, MW (Epoch looks this up from Timelines)
COL_COST = "Current total capital cost (2025 USD billions)"

UNATTRIBUTED = "Owner not disclosed"
TAG_PATTERN = re.compile(r"\s*#(confident|likely|speculative)\b", flags=re.IGNORECASE)


def load(path: str | Path = RAW_PATH) -> pd.DataFrame:
    """Step 1: read the raw Epoch file. If it is missing, download it once and save it
    to data/raw/ unedited, so the repository always holds the exact file used."""
    path = Path(os.environ.get("TAB2_DATA_PATH", path))  # override used only by tests
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        urlretrieve(RAW_URL, path)  # byte-for-byte copy of Epoch's file
    df = pd.read_csv(path)
    return df[[COL_NAME, COL_OWNER, COL_COUNTRY, COL_POWER, COL_COST]].copy()


def clean_owner(value) -> str:
    """'Meta #confident' -> 'Meta'.  Blank -> 'Owner not disclosed'."""
    if pd.isna(value) or str(value).strip() == "":
        return UNATTRIBUTED
    return TAG_PATTERN.sub("", str(value)).strip()


def owner_confidence(value) -> str:
    """Keep Epoch's tag in its own column so the page can disclose it."""
    if pd.isna(value):
        return "none"
    match = TAG_PATTERN.search(str(value))
    return match.group(1).lower() if match else "untagged"


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Step 2: tidy text fields and flag sites that are not yet drawing power."""
    out = df.copy()
    out["owner_confidence"] = out[COL_OWNER].map(owner_confidence)
    out[COL_OWNER] = out[COL_OWNER].map(clean_owner)
    out[COL_POWER] = pd.to_numeric(out[COL_POWER], errors="coerce").fillna(0)
    out[COL_COST] = pd.to_numeric(out[COL_COST], errors="coerce").fillna(0)
    out["operational"] = out[COL_POWER] > 0  # Epoch records 0 MW for sites not yet running
    return out


def share_table(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """Step 3: total current power and site count per Owner or Country, largest first.
    share_pct = group MW / all MW * 100."""
    table = (
        df.groupby(by, as_index=False)
        .agg(power_mw=(COL_POWER, "sum"), sites=(COL_NAME, "count"))
        .sort_values("power_mw", ascending=False, ignore_index=True)
    )
    table["share_pct"] = table["power_mw"] / table["power_mw"].sum() * 100
    table["cumulative_pct"] = table["share_pct"].cumsum()
    return table


def top_n_share(table: pd.DataFrame, n: int, by: str) -> float:
    """Step 4: % of all current power held by the n largest groups.
    'Owner not disclosed' is not a single organisation, so it never counts toward the top n."""
    named = table[table[by] != UNATTRIBUTED]
    return named.head(n)["power_mw"].sum() / table["power_mw"].sum() * 100



# ---------------------------------------------------------------------------
# Sample and processed files
# ---------------------------------------------------------------------------

def extract_sample() -> pd.DataFrame:
    """Step 0: keep the five columns the tab uses. Values are not changed."""
    raw = pd.read_csv(RAW_PATH, dtype=str, keep_default_na=False)  # read as text so values stay identical
    sample = raw[[COL_NAME, COL_OWNER, COL_COUNTRY, COL_POWER, COL_COST]]
    SAMPLE_FILE.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(SAMPLE_FILE, index=False)
    return sample


def build() -> dict[Path, pd.DataFrame]:
    """Steps 2 and 3 on the sample. Returns processed files keyed by where they are saved."""
    sites = clean(pd.read_csv(SAMPLE_FILE))
    return {
        PROCESSED["sites"]: sites,
        PROCESSED["Owner"]: share_table(sites, by=COL_OWNER),
        PROCESSED["Country"]: share_table(sites, by=COL_COUNTRY),
    }


def load_sites() -> pd.DataFrame:
    """The cleaned site list the tab reads."""
    return pd.read_csv(PROCESSED["sites"])


def load_share(by: str) -> pd.DataFrame:
    """The Owner or Country share table the tab reads."""
    return pd.read_csv(PROCESSED[by])


def validate(sample: pd.DataFrame, out: dict[str, pd.DataFrame]) -> list[tuple[str, bool, str]]:
    """Each check can fail. Returns (check, passed, detail)."""
    sites, owners, countries = out["sites"], out["Owner"], out["Country"]
    checks = []
    checks.append(("No site dropped between sample and processed file",
                   len(sites) == len(sample), f"{len(sample)} sample rows, {len(sites)} processed rows"))
    checks.append(("Site names are unique (primary key)", sites[COL_NAME].is_unique,
                   f"{sites[COL_NAME].duplicated().sum()} duplicates"))
    checks.append(("No confidence tag left in Owner", not sites[COL_OWNER].str.contains("#").any(),
                   f"{sites[COL_OWNER].str.contains('#').sum()} owners still tagged"))
    checks.append(("No negative power values", (sites[COL_POWER] >= 0).all(),
                   f"min {sites[COL_POWER].min():.1f} MW"))
    for name, table in (("Owner", owners), ("Country", countries)):
        checks.append((f"{name} shares add up to 100% and to the total MW",
                       abs(table["share_pct"].sum() - 100) < 1e-6
                       and abs(table["power_mw"].sum() - sites[COL_POWER].sum()) < 1e-6,
                       f"{table['share_pct'].sum():.4f}%, {table['power_mw'].sum():,.1f} MW"))
    return checks


def report(checks: list[tuple[str, bool, str]]) -> bool:
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name} ({detail})")
    return all(ok for _, ok, _ in checks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tab 2 data preparation")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--from-sample", action="store_true", help="rebuild processed files from the sample")
    mode.add_argument("--validate", action="store_true", help="run the checks only")
    args = parser.parse_args()

    if not args.validate:
        if not args.from_sample:
            extract_sample()
            print(f"Sample written to {SAMPLE_FILE.relative_to(ROOT)}")
        for path, df in build().items():
            path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(path, index=False)
            print(f"  {path.relative_to(ROOT)} ({len(df)} rows)")
    out = {"sites": load_sites(), "Owner": load_share("Owner"), "Country": load_share("Country")}
    print("Checks:")
    if not report(validate(pd.read_csv(SAMPLE_FILE), out)):
        sys.exit("A check failed: the processed files should not be used until it is resolved.")


if __name__ == "__main__":
    main()
