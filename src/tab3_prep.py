"""
Tab 3 - Electricity Demand: every transformation from the raw files to the files the tab reads.

Commands (run from the repo root):
  python -m src.tab3_prep                 raw files -> samples -> processed files -> checks
  python -m src.tab3_prep --from-sample   samples -> processed files -> checks (no raw files needed)
  python -m src.tab3_prep --validate      checks only, on the current samples and processed files

Raw files (never edited by hand):
  data/raw/tab3/owid_dc_share.csv             data centre share of electricity demand, % (IEA, Ember via OWID)
  data/raw/tab3/owid_electricity_demand.csv   total electricity demand, TWh (Ember via OWID)
  data/raw/tab3/epoch_data_center_timelines.csv   dated power records per AI data centre (Epoch AI)
  data/raw/data_centers.csv                   Epoch AI site list, shared with Tab 2 (used for Country)
  data/monthly-spending-data-center-us.csv    US data centre construction spending, shared with Tabs 1 and 4

The steps:
  1. extract_samples()   keep the rows and columns Tab 3 uses, unchanged -> data/sample/tab3_*.csv
  2. us_demand()         US total demand 2000-2025 with the change since 2021
  3. dc_use()            data centre use in TWh = share x total demand, plus Rest of world
  4. ai_capacity()       month-end US frontier AI power, reported vs planned
  5. scenarios()         growth rates measured from the data
  6. projection()        2025 use grown forward to 2030 under each rate
  7. validate()          checks that can fail; the build stops if any does
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "tab3"
SAMPLE = ROOT / "data" / "sample"
PROCESSED = ROOT / "data" / "processed"

RAW_FILES = {
    "share": RAW / "owid_dc_share.csv",
    "demand": RAW / "owid_electricity_demand.csv",
    "timelines": RAW / "epoch_data_center_timelines.csv",
    "sites": ROOT / "data" / "raw" / "data_centers.csv",
    "construction": ROOT / "data" / "monthly-spending-data-center-us.csv",
}
SAMPLE_FILES = {k: SAMPLE / f"tab3_{k}.csv" for k in RAW_FILES}
SAMPLE_INFO = SAMPLE / "tab3_samples.json"
OUT = {
    "us_demand": PROCESSED / "tab3_us_demand.csv",
    "dc_use": PROCESSED / "tab3_dc_use.csv",
    "ai_capacity": PROCESSED / "tab3_ai_capacity.csv",
    "scenarios": PROCESSED / "tab3_scenarios.csv",
    "projection": PROCESSED / "tab3_projection.csv",
}

# Column names exactly as they appear in the source files.
SHARE_COL = "Share of total electricity demand coming from data centers"
DEMAND_COL = "Electricity demand"
POWER_COL = "Power (MW)"        # whole facility, including cooling: what the grid supplies
IT_POWER_COL = "IT power (MW)"  # servers only; kept in the sample for reference
SPEND_COL = "Data center construction"

REGIONS = ["United States", "China", "World"]
REST = "Rest of world"                                    # World - United States - China
OWID_REST = "World excl. United States and China"         # kept only to check Rest of world
DEMAND_YEARS = (2000, 2025)
BASE, LATEST = 2020, 2025                                 # first and last year with a data centre share
FLAT_PERIOD = (2007, 2021)                                # shaded on the chart: US demand 4,174 vs 4,193 TWh
PROJECT_TO = 2030
CAPACITY_MONTHS = ("2019-01", "2030-01")

# Published reference values used only by validate().
IEA_WORLD_2024_TWH = 415   # IEA, Energy and AI (2025), executive summary
IEA_US_SHARE_2024 = 45     # same source: the US accounts for about 45% of data centre use in 2024


# ---------------------------------------------------------------------------
# Step 1: samples
# ---------------------------------------------------------------------------

def extract_samples() -> None:
    """Keep only the rows and columns Tab 3 uses. Values are not changed."""
    SAMPLE.mkdir(parents=True, exist_ok=True)
    share = pd.read_csv(RAW_FILES["share"])
    share = share[share["Entity"].isin(REGIONS + [OWID_REST])][["Entity", "Year", SHARE_COL]]

    demand = pd.read_csv(RAW_FILES["demand"])
    demand = demand[demand["Entity"].isin(REGIONS) & demand["Year"].between(*DEMAND_YEARS)]
    demand = demand[["Entity", "Year", DEMAND_COL]]

    timelines = pd.read_csv(RAW_FILES["timelines"])[["Data center", "Date", IT_POWER_COL, POWER_COL]]
    sites = pd.read_csv(RAW_FILES["sites"])[["Name", "Country"]]
    construction = pd.read_csv(RAW_FILES["construction"])[["Entity", "Month", SPEND_COL]]

    for key, df in dict(share=share, demand=demand, timelines=timelines, sites=sites,
                        construction=construction).items():
        df.to_csv(SAMPLE_FILES[key], index=False)

    log = json.loads((RAW / "retrieval_log.json").read_text())
    SAMPLE_INFO.write_text(json.dumps({"epoch_snapshot_date": log["retrieved"]}, indent=2) + "\n")


def load_samples() -> dict[str, pd.DataFrame]:
    return {k: pd.read_csv(p) for k, p in SAMPLE_FILES.items()}


# ---------------------------------------------------------------------------
# Steps 2 to 6: processed files
# ---------------------------------------------------------------------------

def us_demand(demand: pd.DataFrame) -> pd.DataFrame:
    """Step 2: US total demand by year, change since 2021 and the flat-period flag."""
    us = (demand[demand["Entity"] == "United States"]
          .rename(columns={"Year": "year", DEMAND_COL: "demand_twh"})[["year", "demand_twh"]]
          .sort_values("year").reset_index(drop=True))
    ref = us.loc[us["year"] == FLAT_PERIOD[1], "demand_twh"].iloc[0]
    us["change_since_2021_pct"] = (us["demand_twh"] / ref - 1) * 100
    us["in_flat_period"] = us["year"].between(*FLAT_PERIOD)
    return us


def dc_use(share: pd.DataFrame, demand: pd.DataFrame) -> pd.DataFrame:
    """Step 3: data centre use (TWh) = share / 100 x total demand.

    Only the United States, China and World have a matching total in both files;
    the IEA regions (Europe, Asia Pacific, ...) are defined differently from Ember's
    and are left out. Rest of world = World - United States - China.
    """
    s = share[share["Entity"].isin(REGIONS)].rename(columns={"Entity": "region", "Year": "year",
                                                             SHARE_COL: "share_pct"})
    d = demand.rename(columns={"Entity": "region", "Year": "year", DEMAND_COL: "demand_twh"})
    df = s.merge(d, on=["region", "year"], how="inner", validate="one_to_one")
    df["dc_twh"] = df["share_pct"] / 100 * df["demand_twh"]

    wide = df.pivot(index="year", columns="region", values=["dc_twh", "demand_twh"])
    rest = pd.DataFrame({
        "region": REST,
        "year": wide.index,
        "dc_twh": (wide["dc_twh"]["World"] - wide["dc_twh"]["United States"] - wide["dc_twh"]["China"]).values,
        "demand_twh": (wide["demand_twh"]["World"] - wide["demand_twh"]["United States"]
                       - wide["demand_twh"]["China"]).values,
    })
    rest["share_pct"] = rest["dc_twh"] / rest["demand_twh"] * 100
    df = pd.concat([df, rest], ignore_index=True)

    df["other_twh"] = df["demand_twh"] - df["dc_twh"]
    first = df[df["year"] == BASE].set_index("region")
    df["dc_change_since_2020_twh"] = df["dc_twh"] - df["region"].map(first["dc_twh"])
    df["demand_change_since_2020_twh"] = df["demand_twh"] - df["region"].map(first["demand_twh"])
    df["dc_share_of_growth_pct"] = (df["dc_change_since_2020_twh"] / df["demand_change_since_2020_twh"] * 100
                                    ).where(df["year"] != BASE)
    world = df[df["region"] == "World"].set_index("year")["dc_twh"]
    df["share_of_world_dc_pct"] = df["dc_twh"] / df["year"].map(world) * 100

    order = {r: i for i, r in enumerate(["United States", "China", REST, "World"])}
    cols = ["region", "year", "share_pct", "demand_twh", "dc_twh", "other_twh", "dc_change_since_2020_twh",
            "demand_change_since_2020_twh", "dc_share_of_growth_pct", "share_of_world_dc_pct"]
    return df.sort_values(["region", "year"], key=lambda c: c.map(order) if c.name == "region" else c)[cols] \
             .reset_index(drop=True)


def ai_capacity(timelines: pd.DataFrame, sites: pd.DataFrame, snapshot: str) -> pd.DataFrame:
    """Step 4: month-end power of US frontier AI data centres.

    Each site keeps its latest reported Power (MW) until its next record. Records with no
    power value are skipped (one in the 25 Oct 2026 file), so the site keeps its previous value.
    Months ending on or before the download date are 'reported'; later months are 'planned'.
    """
    us_sites = set(sites.loc[sites["Country"] == "United States", "Name"])
    t = timelines[timelines["Data center"].isin(us_sites)].dropna(subset=[POWER_COL]).copy()
    t["date"] = pd.to_datetime(t["Date"])
    t = t.sort_values(["Data center", "date"])

    months = pd.period_range(*CAPACITY_MONTHS, freq="M")
    snap = pd.Timestamp(snapshot)
    rows = []
    for m in months:
        end = m.to_timestamp(how="end").normalize()
        latest = t[t["date"] <= end].groupby("Data center").tail(1)
        rows.append({
            "month": str(m),
            "power_mw": latest[POWER_COL].sum(),
            "sites_drawing_power": int((latest[POWER_COL] > 0).sum()),
            "status": "reported" if end <= snap else "planned",
        })
    out = pd.DataFrame(rows)
    out["power_gw"] = out["power_mw"] / 1000
    return out[["month", "power_mw", "power_gw", "sites_drawing_power", "status"]]


def _cagr(end: float, start: float, years: int) -> float:
    return ((end / start) ** (1 / years) - 1) * 100


def scenarios(use: pd.DataFrame, construction: pd.DataFrame) -> pd.DataFrame:
    """Step 5: yearly growth rates (%) measured from the data.

    Other (non data centre) demand grows at its own 2020-2025 rate in every scenario.
    The construction rate uses calendar-year totals of complete years only, so the
    partial 2026 is excluded. Construction spending covers the United States only.
    """
    c = construction[construction["Entity"] == "United States"].copy()
    c["year"] = c["Month"].str[:4].astype(int)
    yearly = c.groupby("year")[SPEND_COL].agg(["sum", "size"])
    yearly = yearly[yearly["size"] == 12]["sum"]
    build_rate = _cagr(yearly[LATEST], yearly[BASE], LATEST - BASE)

    rows = []
    for region, g in use.groupby("region", sort=False):
        g = g.set_index("year")
        other = _cagr(g.loc[LATEST, "other_twh"], g.loc[BASE, "other_twh"], LATEST - BASE)
        rates = [
            ("trend", "Measured trend, 2020 to 2025",
             _cagr(g.loc[LATEST, "dc_twh"], g.loc[BASE, "dc_twh"], LATEST - BASE),
             "Average yearly growth of data centre use, 2020 to 2025"),
            ("latest", "Latest year, 2024 to 2025",
             (g.loc[LATEST, "dc_twh"] / g.loc[LATEST - 1, "dc_twh"] - 1) * 100,
             "Growth of data centre use from 2024 to 2025"),
        ]
        if region == "United States":
            rates.append(("construction", "Construction spending trend, 2020 to 2025", build_rate,
                          "Average yearly growth of US construction spending (constant 2021 US$), "
                          "complete calendar years 2020 to 2025"))
        for key, label, rate, basis in rates:
            rows.append({"region": region, "scenario": key, "scenario_label": label,
                         "dc_growth_pct": rate, "other_growth_pct": other, "basis": basis})
    return pd.DataFrame(rows)


def projection(use: pd.DataFrame, rates: pd.DataFrame) -> pd.DataFrame:
    """Step 6: grow 2025 data centre use and other demand forward each year to 2030."""
    base = use[use["year"] == LATEST].set_index("region")
    rows = []
    for r in rates.itertuples():
        dc0, other0 = base.loc[r.region, "dc_twh"], base.loc[r.region, "other_twh"]
        for year in range(LATEST, PROJECT_TO + 1):
            n = year - LATEST
            dc = dc0 * (1 + r.dc_growth_pct / 100) ** n
            other = other0 * (1 + r.other_growth_pct / 100) ** n
            rows.append({"region": r.region, "scenario": r.scenario, "year": year, "dc_twh": dc,
                         "other_twh": other, "total_twh": dc + other,
                         "dc_share_pct": dc / (dc + other) * 100, "multiple_of_2025": dc / dc0})
    return pd.DataFrame(rows)


def build(samples: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    snapshot = json.loads(SAMPLE_INFO.read_text())["epoch_snapshot_date"]
    use = dc_use(samples["share"], samples["demand"])
    rates = scenarios(use, samples["construction"])
    return {
        "us_demand": us_demand(samples["demand"]),
        "dc_use": use,
        "ai_capacity": ai_capacity(samples["timelines"], samples["sites"], snapshot),
        "scenarios": rates,
        "projection": projection(use, rates),
    }


# ---------------------------------------------------------------------------
# Step 7: checks
# ---------------------------------------------------------------------------

def validate(samples: dict[str, pd.DataFrame], out: dict[str, pd.DataFrame]) -> list[tuple[str, bool, str]]:
    """Each check can fail. Returns (check, passed, detail)."""
    use = out["dc_use"].set_index(["region", "year"])
    share = samples["share"].set_index(["Entity", "Year"])[SHARE_COL]
    checks = []

    world24 = use.loc[("World", 2024), "dc_twh"]
    checks.append(("World data centre use 2024 within 2 TWh of the IEA's 415 TWh",
                   abs(world24 - IEA_WORLD_2024_TWH) <= 2, f"{world24:.1f} TWh"))

    us24 = use.loc[("United States", 2024), "share_of_world_dc_pct"]
    checks.append(("US share of world data centre use 2024 within 5 points of the IEA's 45%",
                   abs(us24 - IEA_US_SHARE_2024) <= 5, f"{us24:.1f}%"))

    gaps = [abs(use.loc[(REST, y), "share_pct"] - share.loc[(OWID_REST, y)]) for y in (2020, 2023, 2024, 2025)]
    checks.append(("Rest of world share matches OWID's 'World excl. United States and China' within 0.01 points",
                   max(gaps) <= 0.01, f"largest gap {max(gaps):.4f} points"))

    d = samples["demand"]
    full = all(set(d.loc[d["Entity"] == r, "Year"]) == set(range(DEMAND_YEARS[0], DEMAND_YEARS[1] + 1))
               for r in REGIONS)
    dups = (samples["share"].duplicated(["Entity", "Year"]).sum() + d.duplicated(["Entity", "Year"]).sum()
            + samples["timelines"].duplicated(["Data center", "Date"]).sum())
    checks.append(("No duplicate keys, and 2000-2025 demand complete for the US, China and World",
                   full and dups == 0, f"{dups} duplicate keys"))

    unmatched = set(samples["timelines"]["Data center"]) - set(samples["sites"]["Name"])
    negative = (samples["timelines"][POWER_COL] < 0).sum()
    checks.append(("Every Epoch timeline site has a country, and no power value is negative",
                   not unmatched and negative == 0, f"{len(unmatched)} unmatched sites, {negative} negative values"))

    c = samples["construction"]
    months = c["Month"].str[:4].astype(int).value_counts()
    checks.append(("Construction spending has 12 months in both 2020 and 2025",
                   months.get(BASE) == 12 and months.get(LATEST) == 12,
                   f"2020: {months.get(BASE)}, 2025: {months.get(LATEST)} months"))
    return checks


def report(checks: list[tuple[str, bool, str]]) -> bool:
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name} ({detail})")
    return all(ok for _, ok, _ in checks)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--from-sample", action="store_true", help="rebuild processed files from the samples")
    mode.add_argument("--validate", action="store_true", help="run the checks only")
    args = parser.parse_args()

    if args.validate:
        samples = load_samples()
        out = {k: pd.read_csv(p) for k, p in OUT.items()}
    else:
        if not args.from_sample:
            extract_samples()
            print(f"Samples written to {SAMPLE.relative_to(ROOT)}/")
        samples = load_samples()
        out = build(samples)
        PROCESSED.mkdir(parents=True, exist_ok=True)
        for key, df in out.items():
            df.to_csv(OUT[key], index=False)
            print(f"  {OUT[key].relative_to(ROOT)} ({len(df)} rows)")

    print("Checks:")
    if not report(validate(samples, out)):
        sys.exit("A check failed: the processed files should not be used until it is resolved.")


if __name__ == "__main__":
    main()
