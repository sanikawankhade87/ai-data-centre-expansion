# Data Dictionary: Tab 3 (Electricity Demand)

Every dataset Tab 3 reads, from the raw download to the processed file. All transforms are in `src/tab3_prep.py`.

| Command | Reads | Writes |
|---|---|---|
| `python scripts/download_tab3.py` | Published URLs | `data/raw/tab3/` and `retrieval_log.json` |
| `python -m src.tab3_prep` | Raw files | `data/sample/tab3_*.csv`, `data/processed/tab3_*.csv` |
| `python -m src.tab3_prep --from-sample` | Samples only | `data/processed/tab3_*.csv` (byte-identical to the full build) |
| `python -m src.tab3_prep --validate` | Samples and processed files | Six checks, printed as PASS or FAIL |

Raw files were retrieved on 25 Oct 2026. Each sample keeps the source column names and values unchanged; only the rows and columns Tab 3 uses are kept.

## Source datasets

| Sample | Source and URL | Licence | Columns and units | Primary key | Time coverage | Latest observation |
|---|---|---|---|---|---|---|
| `tab3_share.csv` (16 rows) | IEA, *Energy and AI* (2025, 2026), and Ember, *Yearly Electricity Data* (2026), processed by Our World in Data. https://ourworldindata.org/grapher/data-centers-share-electricity-demand | IEA terms of use (© OECD/IEA, attribution required); Ember CC BY 4.0 | `Entity` (text); `Year` (integer); `Share of total electricity demand coming from data centers` (%) | Entity, Year | 2020, 2023, 2024, 2025 (no values for 2021 and 2022) | 2025 (OWID update 30 Jun 2026) |
| `tab3_demand.csv` (78 rows) | Ember, *Yearly Electricity Data* (2026), processed by Our World in Data. https://ourworldindata.org/grapher/electricity-demand | CC BY 4.0 | `Entity` (text); `Year` (integer); `Electricity demand` (TWh) | Entity, Year | 2000–2025, every year | 2025 (OWID update 30 Jun 2026) |
| `tab3_timelines.csv` (567 rows) | Epoch AI, *AI data centers*, timelines table. https://epoch.ai/data/data_centers/data_center_timelines.csv | CC BY 4.0 | `Data center` (text); `Date` (YYYY-MM-DD); `IT power (MW)` (servers only, MW); `Power (MW)` (whole facility including cooling, MW) | Data center, Date | 2018-12-18 to 2030-01-01; dates after the retrieval date are planned | Reported: 2026-10-19; planned: 2030-01-01 |
| `tab3_sites.csv` (95 rows) | Epoch AI, *AI data centers*, site list (same file as Tab 2). https://epoch.ai/data/data_centers/data_centers.csv | CC BY 4.0 | `Name` (text); `Country` (text) | Name | Snapshot | Release used by Tab 2 (19 Oct 2026) |
| `tab3_construction.csv` (152 rows) | US Census Bureau, *Value of Construction Put in Place*, and US Bureau of Labor Statistics price indexes, processed by Our World in Data (same file as Tabs 1 and 4). https://ourworldindata.org/grapher/monthly-spending-data-center-us | CC BY 4.0 (OWID); US government data | `Entity` (text); `Month` (YYYY-MM); `Data center construction` (constant 2021 US$) | Month | Jan 2014 to Aug 2026, every month | Aug 2026 (OWID update 2 Oct 2026); recent months are preliminary |

Rows kept: `tab3_share.csv` keeps United States, China, World and World excl. United States and China (the last is used only for a check). `tab3_demand.csv` keeps United States, China and World for 2000–2025.

## Processed datasets

| File | Primary key | Columns and units | Time coverage | Transform |
|---|---|---|---|---|
| `tab3_us_demand.csv` | year | `year`; `demand_twh` (TWh); `change_since_2021_pct` (% change from 2021); `in_flat_period` (true for 2007–2021) | 2000–2025 | United States rows of `tab3_demand.csv`. Change = demand ÷ 2021 demand − 1, × 100. The flat period is 2007 (4,174 TWh) to 2021 (4,193 TWh) |
| `tab3_dc_use.csv` | region, year | `share_pct` (%); `demand_twh`, `dc_twh`, `other_twh`, `dc_change_since_2020_twh`, `demand_change_since_2020_twh` (TWh); `dc_share_of_growth_pct` (%; empty in 2020); `share_of_world_dc_pct` (%) | 2020, 2023, 2024, 2025 | Join share and demand on region and year. `dc_twh` = share ÷ 100 × demand. Rest of world = World − United States − China, for TWh and demand, and its share is recalculated. `other_twh` = demand − `dc_twh`. Share of growth = change in `dc_twh` since 2020 ÷ change in demand since 2020 × 100 |
| `tab3_ai_capacity.csv` | month | `month` (YYYY-MM); `power_mw` (MW); `power_gw` (GW); `sites_drawing_power` (count); `status` (reported or planned) | Jan 2019 to Jan 2030 | US sites only (country from `tab3_sites.csv`). At each month end, each site keeps its latest `Power (MW)` record on or before that date; values are summed. One record with no power value (QTS Cedar Rapids, 16 Apr 2026) is skipped. Two decreases for Colossus 1 are kept as reported. Months ending on or before the retrieval date are reported; later months are planned |
| `tab3_scenarios.csv` | region, scenario | `scenario` (trend, latest, construction); `scenario_label`; `dc_growth_pct`, `other_growth_pct` (% per year); `basis` | Rates measured over 2020–2025 | Trend = (2025 ÷ 2020 data centre use)^(1/5) − 1. Latest = 2025 ÷ 2024 − 1. Construction (United States only) = the same formula on calendar-year totals of spending, complete years only. Other demand grows at its own 2020–2025 rate |
| `tab3_projection.csv` | region, scenario, year | `dc_twh`, `other_twh`, `total_twh` (TWh); `dc_share_pct` (%); `multiple_of_2025` (ratio) | 2025–2030 | 2025 data centre use and other demand grown each year at the scenario rates. An arithmetic projection, not a forecast |

## Checks (run on every build)

1. World data centre use in 2024 is within 2 TWh of the IEA's published 415 TWh (result: 416.0 TWh).
2. The US share of world data centre use in 2024 is within 5 points of the IEA's stated 45% (result: 44.0%).
3. The recalculated Rest of world share matches OWID's "World excl. United States and China" row within 0.01 points (result: exact match).
4. No duplicate keys in any sample, and demand is complete for 2000–2025 for the United States, China and World.
5. Every Epoch timeline site has a country, and no power value is negative.
6. Construction spending has 12 months in both 2020 and 2025, the years used for the construction rate.

## What the data cannot show

- The data centre share covers all data centres; no public source separates AI data centres, so the measured values are an upper limit on AI-driven use.
- No data centre share is published for 2021 and 2022.
- Epoch AI covers 95 frontier AI sites, not every data centre, and planned capacity reflects announcements that may be delayed or cancelled. Announcements beyond 2028 are limited, so planned capacity levels off after 2028.
- Tab 3 uses `Power (MW)` (whole facility), while Tab 2 uses `IT power (MW)` (servers only), so the two tabs show different MW for the same site.
