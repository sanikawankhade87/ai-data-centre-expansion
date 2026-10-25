"""Download the Tab 3 source files into data/raw/tab3/ exactly as published.

Run once from the repo root:  python scripts/download_tab3.py
Never edit the saved files by hand; every change happens in src/tab3_prep.py.

Saves:
  owid_dc_share.csv (+ .metadata.json)        IEA and Ember via Our World in Data
  owid_electricity_demand.csv (+ .metadata.json)  Ember via Our World in Data
  epoch_data_center_timelines.csv             Epoch AI, AI data centers (timelines)
  retrieval_log.json                          download date, URL, size and MD5 of each file

Tab 3 also reads two files that other tabs already keep in data/ (not downloaded here):
  data/raw/data_centers.csv                   Epoch AI site list (Tab 2), used for each site's country
  data/monthly-spending-data-center-us.csv    US Census Bureau via OWID (Tabs 1 and 4)
"""

import hashlib
import json
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen

OWID = "https://ourworldindata.org/grapher/{}.{}?v=1&csvType=full&useColumnShortNames=false"
FILES = {
    "owid_dc_share.csv": OWID.format("data-centers-share-electricity-demand", "csv"),
    "owid_dc_share.metadata.json": OWID.format("data-centers-share-electricity-demand", "metadata.json"),
    "owid_electricity_demand.csv": OWID.format("electricity-demand", "csv"),
    "owid_electricity_demand.metadata.json": OWID.format("electricity-demand", "metadata.json"),
    "epoch_data_center_timelines.csv": "https://epoch.ai/data/data_centers/data_center_timelines.csv",
}
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "tab3"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    log = {"retrieved": date.today().isoformat(), "files": {}}
    for name, url in FILES.items():
        body = urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
        (OUT / name).write_bytes(body)  # byte-for-byte copy of the published file
        log["files"][name] = {"url": url, "bytes": len(body), "md5": hashlib.md5(body).hexdigest()}
        print(f"Saved data/raw/tab3/{name} ({len(body):,} bytes)")
    (OUT / "retrieval_log.json").write_text(json.dumps(log, indent=2) + "\n")
    print(f"Retrieval date {log['retrieved']} recorded in data/raw/tab3/retrieval_log.json")


if __name__ == "__main__":
    main()
