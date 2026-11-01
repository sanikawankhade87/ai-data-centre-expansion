"""
Rebuild every processed file in data/processed/ from the source samples in data/sample/.

Commands (run from the repo root):
  python -m src.build_data           rebuild all processed files from the samples, then run every check
  python -m src.build_data --check   rebuild in memory and confirm each committed processed file is
                                     byte-for-byte identical to the rebuild; changes nothing on disk

Each tab's transforms live in its own module and are documented in data/DATA_DICTIONARY.md:
  src/tab1_prep.py  Tab 1, Pace of Construction
  src/tab2_prep.py  Tab 2, Builders and Locations
  src/tab3_prep.py  Tab 3, Electricity Demand
  src/tab4_prep.py  Tab 4, Demand Comparison (reads Tab 1's processed file, so Tab 1 is built first)

To refresh the samples from the raw downloads first, run each module on its own without flags,
for example: python -m src.tab1_prep
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from src import tab1_prep, tab2_prep, tab3_prep, tab4_prep

ROOT = Path(__file__).resolve().parents[1]


def rebuilt() -> list[tuple[str, Path, pd.DataFrame]]:
    """(tab, path, rebuilt data) for every processed file, in build order."""
    out = [("Tab 1", p, df) for p, df in tab1_prep.build().items()]
    out += [("Tab 2", p, df) for p, df in tab2_prep.build().items()]
    t3 = tab3_prep.build(tab3_prep.load_samples())
    out += [("Tab 3", tab3_prep.OUT[k], df) for k, df in t3.items()]
    out += [("Tab 4", p, df) for p, df in tab4_prep.build().items()]
    return out


def checks() -> bool:
    """Run each module's own checks on the samples and the processed files on disk."""
    ok = True
    print("Tab 1 checks:")
    ok &= tab1_prep.report(tab1_prep.validate(tab1_prep.load_sample(), pd.read_csv(tab1_prep.PROCESSED_FILE)))
    print("Tab 2 checks:")
    ok &= tab2_prep.report(tab2_prep.validate(
        pd.read_csv(tab2_prep.SAMPLE_FILE),
        {"sites": tab2_prep.load_sites(), "Owner": tab2_prep.load_share("Owner"),
         "Country": tab2_prep.load_share("Country")}))
    print("Tab 3 checks:")
    samples = tab3_prep.load_samples()
    ok &= tab3_prep.report(tab3_prep.validate(samples, {k: pd.read_csv(p) for k, p in tab3_prep.OUT.items()}))
    print("Tab 4 checks:")
    ok &= tab4_prep.report(tab4_prep.validate(tab4_prep.load_ai_sample(), tab4_prep.load_dates(),
                                              pd.read_csv(tab4_prep.PROCESSED_AI)))
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild all processed files from the samples")
    parser.add_argument("--check", action="store_true",
                        help="compare a fresh rebuild with the committed files; change nothing")
    args = parser.parse_args()

    if args.check:
        same = True
        print("Rebuilding every processed file from the samples and comparing with the committed file:")
        for tab, path, df in rebuilt():
            fresh = df.to_csv(index=False).encode()
            committed = path.read_bytes() if path.exists() else b""
            match = fresh == committed
            same &= match
            print(f"  {'IDENTICAL' if match else 'DIFFERENT'}  {tab}  {path.relative_to(ROOT)} ({len(df)} rows)")
        ok = checks()
        if not (same and ok):
            sys.exit("Not reproducible: a processed file differs from its rebuild, or a check failed.")
        print("All processed files regenerate exactly from the samples, and every check passes.")
        return

    # Tab 4 reads Tab 1's processed file, so write in build order.
    for tab, path, df in rebuilt():
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        print(f"  {tab}  {path.relative_to(ROOT)} ({len(df)} rows)")
    if not checks():
        sys.exit("A check failed: the processed files should not be used until it is resolved.")


if __name__ == "__main__":
    main()
