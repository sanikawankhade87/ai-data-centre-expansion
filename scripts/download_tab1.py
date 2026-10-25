"""Download the Tab 1 source file from Our World in Data, unedited.

Run from the repo root:
  python scripts/download_tab1.py            save a fresh copy to data/raw/tab1/ and compare it
  python scripts/download_tab1.py --replace  also replace the shared file data/monthly-spending-data-center-us.csv

The shared file is also read by Tabs 3 and 4, so only use --replace when the group agrees to
update to a newer release: the Census Bureau revises recent months, so the numbers will change.
Never edit either file by hand; every change happens in src/tab1_prep.py.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

BASE = os.environ.get("TAB1_SOURCE_BASE", "https://ourworldindata.org/grapher/monthly-spending-data-center-us")
CSV_URL = f"{BASE}.csv?v=1&csvType=full&useColumnShortNames=false"
META_URL = f"{BASE}.metadata.json?v=1&csvType=full&useColumnShortNames=false"

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "tab1"
SHARED = ROOT / "data" / "monthly-spending-data-center-us.csv"


def fetch(url: str, out: Path) -> None:
    req = Request(url, headers={"User-Agent": "Our World In Data data fetch/1.0"})
    with urlopen(req, timeout=60) as resp, out.open("wb") as f:
        f.write(resp.read())  # byte-for-byte copy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="store_true", help="also replace the shared data file")
    args = parser.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    csv_out = RAW / "monthly-spending-data-center-us.csv"
    meta_out = RAW / "monthly-spending-data-center-us.metadata.json"
    fetch(CSV_URL, csv_out)
    fetch(META_URL, meta_out)

    rows = sum(1 for _ in csv_out.open(encoding="utf-8")) - 1
    same = SHARED.exists() and filecmp.cmp(csv_out, SHARED, shallow=False)
    log = {
        "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "csv_url": CSV_URL,
        "metadata_url": META_URL,
        "rows": rows,
        "identical_to_shared_file": same,
    }
    (RAW / "retrieval_log.json").write_text(json.dumps(log, indent=2))
    print(f"Saved {csv_out.relative_to(ROOT)} ({rows} rows).")
    print("Identical to the shared file." if same else "Differs from the shared file (newer or revised release).")

    if args.replace and not same:
        shutil.copyfile(csv_out, SHARED)
        print(f"Replaced {SHARED.relative_to(ROOT)}. Tell the group: Tabs 1, 3 and 4 will show the new numbers.")


if __name__ == "__main__":
    main()
