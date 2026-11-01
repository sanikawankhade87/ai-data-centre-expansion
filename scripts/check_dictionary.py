"""Check that data/DATA_DICTIONARY.md documents every data file and every column the app reads.

Run from the repo root: python scripts/check_dictionary.py
Fails (exit code 1) if a file in data/ is not named in the dictionary, or if a column of a sample
or processed file is not listed in backticks.
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
text = (DATA / "DATA_DICTIONARY.md").read_text(encoding="utf-8")

problems = []
files = [p for p in DATA.rglob("*") if p.is_file() and p.suffix != ".md"]
for p in sorted(files):
    if p.name not in text:
        problems.append(f"file not documented: {p.relative_to(ROOT)}")
for folder in ("sample", "processed"):
    for p in sorted((DATA / folder).glob("*.csv")):
        for col in pd.read_csv(p, nrows=0).columns:
            if f"`{col}`" not in text:
                problems.append(f"column not documented: {p.relative_to(ROOT)} -> {col}")

print(f"Checked {len(files)} data files and the columns of every sample and processed file.")
for line in problems:
    print("  FAIL ", line)
if problems:
    sys.exit(1)
print("  PASS  Every data file and every column is documented in data/DATA_DICTIONARY.md")
