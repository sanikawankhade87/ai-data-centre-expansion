# Tab 3 · Electricity Demand

| | |
|---|---|
| **Owner** | Szexuan Yap |
| **Sub-question** | What does the data centre expansion cost the US electricity grid, and how large could this load become? |
| **Persona** | Dana Reyes, energy policy analyst advising a US state public utilities commission (the group persona, see [README.md](README.md)) |
| **Short answer for Dana** | US data centres used 224 TWh in 2025 (4.9% of US demand) and account for 26% of the rise in US demand since 2020. At measured growth rates they would use 465 to 848 TWh by 2030 |
| **Charts** | Line chart (change over time); column chart (magnitude); ranked bar chart (ranking); reported vs planned line chart (change over time); projection line chart (change over time) |

## 1. Files

| File | Purpose |
|---|---|
| `tab3_electricity.py` | The tab. `app.py` imports it and calls `render()` inside the third tab |
| `src/tab3_prep.py` | Every transformation, in commented steps, plus six checks that can fail |
| `scripts/download_tab3.py` | Downloads the Tab 3 source files into `data/raw/tab3/` exactly as published, with a retrieval log |
| `data/raw/tab3/` | Raw downloads, never edited, plus `retrieval_log.json` (date, URL, size and MD5 of each file) |
| `data/sample/tab3_*.csv` | Source samples: the rows and columns Tab 3 uses, values unchanged |
| `data/processed/tab3_*.csv` | The five files the tab reads |

Tab 3 also reads two files shared with other tabs: `data/raw/data_centers.csv` (Tab 2, for each site's country) and `data/monthly-spending-data-center-us.csv` (Tabs 1 and 4, for the construction growth rate).

## 2. Run it

```bash
pip install -r requirements.txt
python scripts/download_tab3.py       # saves data/raw/tab3/, unedited
python -m src.tab3_prep               # raw files -> samples -> processed files, then the checks
python -m src.tab3_prep --from-sample # rebuild the processed files from the samples only
python -m src.tab3_prep --validate    # checks only
streamlit run app.py                  # Tab 3 is the third tab
```

## 3. Data

Raw files were retrieved on 25 Oct 2026. Each sample keeps the source column names and values unchanged; only the rows and columns Tab 3 uses are kept.

| Sample | Source and URL | Licence | Columns and units | Primary key | Time coverage | Latest observation |
|---|---|---|---|---|---|---|
| `tab3_share.csv` (16 rows) | IEA, *Energy and AI* (2025, 2026), and Ember, *Yearly Electricity Data* (2026), processed by Our World in Data. https://ourworldindata.org/grapher/data-centers-share-electricity-demand | IEA terms of use (© OECD/IEA, attribution required); Ember CC BY 4.0 | `Entity`; `Year`; `Share of total electricity demand coming from data centers` (%) | Entity, Year | 2020, 2023, 2024, 2025 (no values for 2021 and 2022) | 2025 (OWID update 30 Jun 2026) |
| `tab3_demand.csv` (78 rows) | Ember, *Yearly Electricity Data* (2026), processed by Our World in Data. https://ourworldindata.org/grapher/electricity-demand | CC BY 4.0 | `Entity`; `Year`; `Electricity demand` (TWh) | Entity, Year | 2000–2025, every year | 2025 (OWID update 30 Jun 2026) |
| `tab3_timelines.csv` (567 rows) | Epoch AI, *AI data centers*, timelines table. https://epoch.ai/data/data_centers/data_center_timelines.csv | CC BY 4.0 | `Data center`; `Date` (YYYY-MM-DD); `IT power (MW)` (servers only); `Power (MW)` (whole facility including cooling) | Data center, Date | 2018-12-18 to 2030-01-01; dates after retrieval are planned | Reported: 2026-10-19; planned: 2030-01-01 |
| `tab3_sites.csv` (95 rows) | Epoch AI, *AI data centers*, site list (same file as Tab 2). https://epoch.ai/data/data_centers/data_centers.csv | CC BY 4.0 | `Name`; `Country` | Name | Snapshot | Release of 19 Oct 2026 |
| `tab3_construction.csv` (152 rows) | US Census Bureau and US Bureau of Labor Statistics, processed by Our World in Data (same file as Tabs 1 and 4). https://ourworldindata.org/grapher/monthly-spending-data-center-us | CC BY 4.0 (OWID); US government data | `Entity`; `Month` (YYYY-MM); `Data center construction` (constant 2021 US$) | Month | Jan 2014 to Aug 2026 | Aug 2026 (recent months preliminary) |

Rows kept: `tab3_share.csv` keeps United States, China, World and World excl. United States and China (the last is used only for a check). `tab3_demand.csv` keeps United States, China and World for 2000–2025.

| Processed file | Primary key | Columns and units |
|---|---|---|
| `tab3_us_demand.csv` | year | `demand_twh` (TWh); `change_since_2021_pct` (%); `in_flat_period` (true for 2007–2021) |
| `tab3_dc_use.csv` | region, year | `share_pct` (%); `demand_twh`, `dc_twh`, `other_twh`, change-since-2020 columns (TWh); `dc_share_of_growth_pct` (%); `share_of_world_dc_pct` (%) |
| `tab3_ai_capacity.csv` | month | `power_mw` (MW); `power_gw` (GW); `sites_drawing_power` (count); `status` (reported or planned) |
| `tab3_scenarios.csv` | region, scenario | `dc_growth_pct`, `other_growth_pct` (% per year); `basis` |
| `tab3_projection.csv` | region, scenario, year | `dc_twh`, `other_twh`, `total_twh` (TWh); `dc_share_pct` (%); `multiple_of_2025` (ratio) |

Full column detail for every file is in [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md).

## 4. Transformations

All steps are in `src/tab3_prep.py`. No values are imputed.

| Step | What it does |
|---|---|
| 1 | Keep the rows and columns Tab 3 uses, values unchanged → samples |
| 2 | US total demand 2000–2025; change = demand ÷ 2021 demand − 1, × 100; flat period 2007 (4,174 TWh) to 2021 (4,193 TWh) → `tab3_us_demand.csv` |
| 3 | Data centre use (TWh) = share ÷ 100 × total demand. Rest of world = World − United States − China. Share of growth = change in data centre use since 2020 ÷ change in demand since 2020 × 100 → `tab3_dc_use.csv` |
| 4 | US frontier AI power: at each month end, each US site keeps its latest `Power (MW)` record on or before that date, and values are summed. Months after the retrieval date are planned → `tab3_ai_capacity.csv` |
| 5 | Growth rates from the data: trend = (2025 ÷ 2020)^(1/5) − 1; latest = 2025 ÷ 2024 − 1; construction (US only) = the same formula on yearly construction spending → `tab3_scenarios.csv` |
| 6 | Projection: 2025 data centre use and other demand grown each year to 2030 at the chosen rates → `tab3_projection.csv` |
| 7 | Checks (section 9) |

## 5. Charts and design decisions

The page reads as one story from top to bottom, one chart per step.

| Section and chart | Visual task | Why this form |
|---|---|---|
| 1. Line chart of US electricity demand, 2000–2025 (TWh), with the flat 2007–2021 period shaded | See that demand is rising again after years of no growth | A line shows the long flat period and the recent rise in one view |
| 2. Column chart of US data centre use (TWh) by year, with the share of US demand | Compare the size of data centre use across years | Columns on a zero baseline compare amounts directly; the x-axis says "no data for 2021 and 2022" instead of filling the gap |
| 3. Ranked bar chart of data centre use by region (United States, China, rest of world) | Compare the United States with the rest of the world | Sorted horizontal bars rank regions and fit their names |
| 4. Line chart of the power capacity of US frontier AI data centres, reported (solid) and planned (dashed), in GW | See how much announced capacity would add | One line split at the retrieval date keeps measured and announced capacity visibly apart |
| 5. Projection to 2030 (TWh): measured 2020–2025 solid, projection dashed | See how large the load could become | Solid vs dashed separates measurement from projection; a dotted line bridges the missing 2021–2022 years rather than inventing values |

Every chart has a title, axis titles with units, and value labels at the key points, so it can be read without hovering.

## 6. Interaction

- **Region** selector (section 5): United States, China, Rest of world or World.
- **Growth rate** choice (section 5): the measured trend 2020 to 2025, the latest year 2024 to 2025, or (United States only) the construction spending trend 2020 to 2025. The cards, chart and summary update together.
- **Hover:** shows the exact demand for any year on the section 1 chart. All other values are labelled on the charts.

## 7. What it shows for Dana

US demand barely changed between 2007 and 2021, then rose 8% in four years. Data centres used 224 TWh in 2025, about twice the 2020 level, and account for 26% of the rise in US demand since 2020. The United States carries 46% of the world's data centre electricity use. Frontier AI sites had 15.2 GW of power capacity operating in Sep 2026, and announced projects would raise this to 43.0 GW by the end of 2028. Depending on the growth rate, US data centre use would reach 465 to 848 TWh by 2030 (9.1% to 15.4% of demand). The width of that range shows how uncertain permanent demand remains.

## 8. Trace a number

1. `data/raw/tab3/owid_dc_share.csv`, row United States, 2025: data centre share = **4.9384785** (%), line 33.
2. `data/raw/tab3/owid_electricity_demand.csv`, row United States, 2025: demand = **4535.81** (TWh), line 6092.
3. 4.9384785 ÷ 100 × 4535.81 = 224.0000 TWh, rounded to **224 TWh**.
4. The same calculation is step 3 in `src/tab3_prep.py`, and the result is the `dc_twh` column of `data/processed/tab3_dc_use.csv`. The **Trace 224 TWh** section in the tab shows it on screen.

## 9. Checks

`python -m src.tab3_prep --validate` runs six checks; the build stops if any fails.

1. World data centre use in 2024 is within 2 TWh of the IEA's published 415 TWh (result: 416.0 TWh).
2. The US share of world data centre use in 2024 is within 5 points of the IEA's stated 45% (result: 44.0%).
3. The recalculated rest-of-world share matches OWID's "World excl. United States and China" row within 0.01 points (result: exact match).
4. No duplicate keys in any sample, and demand is complete for 2000–2025 for the United States, China and World.
5. Every Epoch timeline site has a country, and no power value is negative.
6. Construction spending has 12 months in both 2020 and 2025, the years used for the construction rate.

## 10. Limits

- **All data centres, not only AI ones:** no public source separates AI data centres, so measured values are an upper limit on AI-driven use.
- **No data centre share is published for 2021 and 2022.**
- **Epoch AI covers 95 frontier AI sites,** not every data centre, and planned capacity reflects announcements that may be delayed or cancelled. Few projects are announced beyond 2028, so the planned line levels off there.
- **The projection is arithmetic, not a forecast:** it assumes a constant growth rate.
- **Tab 3 uses whole-facility power** (`Power (MW)`, including cooling), while Tab 2 uses IT power (servers only), so the two tabs show different MW for the same site.

## 11. AI use

Recorded in [PROVENANCE.md](PROVENANCE.md), row 9.

| What | Tool | How it was checked |
|---|---|---|
| Researched public sources on data centre electricity use, prepared the data into processed files with checks, and built the Tab 3 page (the analysis outcomes were set by the owner; Claude's first page design was reviewed, found unclear, and rebuilt section by section) | Claude (Anthropic) | Recomputed the main card by hand from the two raw CSV files: 4.9384785% × 4,535.81 TWh = 224 TWh, matching the card; compared the calculated world total for 2024 (416 TWh) with the IEA's published 415 TWh |
