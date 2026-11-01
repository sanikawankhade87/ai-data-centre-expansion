# Data Dictionary: AI Data Centre Expansion

Every dataset the app uses, from the raw download to the file each tab reads. This file covers all four tabs. The tab-level files `DATA_DICTIONARY_tab1.md` and `DATA_DICTIONARY_tab3.md` give extra detail for those tabs.

## Folder layout

| Folder | What it holds | Edited by hand? |
|---|---|---|
| `data/raw/` and the source files at the top of `data/` | Raw downloads, exactly as published | Never |
| `data/sample/` | Source samples: only the rows and columns the app uses, with source values unchanged | Never (written by the prep modules) |
| `data/processed/` | The files the app reads, built from the samples by the documented transforms | Never (written by the prep modules) |

## Rebuilding

| Command | Reads | Writes |
|---|---|---|
| `python -m src.build_data` | Samples | Every processed file, then runs every check |
| `python -m src.build_data --check` | Samples and processed files | Nothing. Rebuilds in memory and confirms each processed file is byte-for-byte identical to its rebuild, then runs every check |
| `python -m src.tab1_prep` (and `tab2_prep`, `tab3_prep`, `tab4_prep`) | Raw files | That tab's samples and processed files, then its checks |
| `python scripts/check_dictionary.py` | This file and `data/` | Nothing. Confirms every data file and every column is documented here |
| `python scripts/check_colours.py` | Chart colours | Nothing. Colour vision deficiency check |

Raw files were downloaded between 23 and 25 October 2026 (dates per dataset below).

---

## 1. Raw source files

### R1. `data/monthly-spending-data-center-us.csv`
- **Source:** US Census Bureau, *Value of Construction Put in Place* (private construction, data centres), adjusted to constant 2021 US$ with US Bureau of Labor Statistics producer price indexes, processed by Our World in Data. https://ourworldindata.org/grapher/monthly-spending-data-center-us
- **Licence:** CC BY 4.0 (Our World in Data); underlying US government data is public domain.
- **Columns and units:** `Entity` (text, always United States); `Code` (USA); `Month` (YYYY-MM); `Data center construction` (US$ at constant 2021 prices, spending in that month, not seasonally adjusted).
- **Primary key:** Month. **Rows:** 152.
- **Time coverage:** January 2014 to August 2026, every month.
- **Latest observation:** August 2026 (OWID update 2 Oct 2026). Recent months are preliminary and the Census Bureau revises the previous two years each year.
- **Downloaded:** 23 Oct 2026. **Used by:** Tabs 1, 3 and 4.
- **Covers:** buildings only (materials, labour, contractor costs); excludes servers and IT equipment, land and maintenance; all data centres, not only AI.

### R2. `data/raw/data_centers.csv`
- **Source:** Epoch AI, *AI data centers*, site list. https://epoch.ai/data/data_centers/data_centers.csv
- **Licence:** CC BY 4.0.
- **Columns and units (16):** `Name` (text); `Current H100 equivalents` (count); `Current power (MW)` (IT power: servers, networking and storage, excluding cooling, MW); `Current total capital cost (2025 USD billions)`; `Owner` (owner of the AI chips, with a confidence tag `#confident`, `#likely` or `#speculative`); `Users`; `Selected Sources`; `Calculations sheet`; `Project`; `Current chip types`; `All chip types`; `Investors`; `Construction companies`; `Energy companies`; `Country` (text); `Address` (text). The app uses `Name`, `Owner`, `Country`, `Current power (MW)` and `Current total capital cost (2025 USD billions)`.
- **Primary key:** Name. **Rows:** 95 sites.
- **Time coverage:** snapshot. **Latest observation:** Epoch AI release of 19 Oct 2026.
- **Downloaded:** 24 Oct 2026. **Used by:** Tabs 2 and 3.

### R3. `data/raw/tab3/owid_dc_share.csv` (with `owid_dc_share.metadata.json`)
- **Source:** IEA, *Energy and AI* (2025, 2026), and Ember, *Yearly Electricity Data* (2026), processed by Our World in Data. https://ourworldindata.org/grapher/data-centers-share-electricity-demand
- **Licence:** IEA terms of use (© OECD/IEA, attribution required); Ember CC BY 4.0.
- **Columns and units:** `Entity` (text); `Code` (text); `Year` (integer); `Share of total electricity demand coming from data centers` (%).
- **Primary key:** Entity, Year. **Rows:** 40 (10 regions).
- **Time coverage:** 2020, 2023, 2024, 2025 (no values for 2021 and 2022).
- **Latest observation:** 2025 (OWID update 30 Jun 2026). **Downloaded:** 25 Oct 2026. **Used by:** Tab 3.

### R4. `data/raw/tab3/owid_electricity_demand.csv` (with `owid_electricity_demand.metadata.json`)
- **Source:** Ember, *Yearly Electricity Data* (2026), processed by Our World in Data. https://ourworldindata.org/grapher/electricity-demand
- **Licence:** CC BY 4.0.
- **Columns and units:** `Entity` (text); `Code` (text); `Year` (integer); `Electricity demand` (TWh).
- **Primary key:** Entity, Year. **Rows:** 6,378 (239 entities).
- **Time coverage:** 1990 to 2025. **Latest observation:** 2025. **Downloaded:** 25 Oct 2026. **Used by:** Tab 3.

### R5. `data/raw/tab3/epoch_data_center_timelines.csv`
- **Source:** Epoch AI, *AI data centers*, timelines table. https://epoch.ai/data/data_centers/data_center_timelines.csv
- **Licence:** CC BY 4.0.
- **Columns and units (14):** `Data center` (text); `Date` (YYYY-MM-DD); `Construction status`; `Buildings operational`; `IT power (MW)` (servers only); `Power (MW)` (whole facility including cooling); `H100 equivalents`; `Performance (8-bit OP/s)`; capital, compute, construction and annual operating costs (2025 USD billions); and source fields. The app uses `Data center`, `Date`, `IT power (MW)`, `Power (MW)`.
- **Primary key:** Data center, Date. **Rows:** 567.
- **Time coverage:** 18 Dec 2018 to 1 Jan 2030; dates after the download date are planned.
- **Latest observation:** reported records to 19 Oct 2026; planned to 1 Jan 2030. **Downloaded:** 25 Oct 2026. **Used by:** Tab 3.

### R6. `data/raw/tab3/retrieval_log.json`
- Download date, URL, size and MD5 hash of each Tab 3 raw file. Written by `scripts/download_tab3.py`.

### R7. `data/AI Core Questions.xlsx`
- **Source:** US Census Bureau, *Business Trends and Outlook Survey* (BTOS), AI core questions, national estimates. https://www.census.gov/hfp/btos/data_downloads
- **Licence:** US government work, public domain.
- **Content used:** sheet *National Estimates*, row 2, question 7: "In the last two weeks, did this business use Artificial Intelligence (AI) in producing goods or services?", answer "Yes" (% of US employer businesses, one column per two-week survey period); sheet *National SE*, row 2: the standard error of each estimate (% points).
- **Primary key:** Question ID, Answer ID (rows) by survey period code (columns, e.g. `202520`).
- **Time coverage:** survey periods 202319 to 202520 (reference periods 28 Aug 2023 to 21 Sep 2025).
- **Latest observation:** period 202520 (reference period ending 21 Sep 2025). This question was then replaced. **Downloaded:** 23 Oct 2026. **Used by:** Tab 4.

### R8. `data/National.xlsx`
- **Source:** US Census Bureau, BTOS, national response estimates. https://www.census.gov/hfp/btos/data_downloads
- **Licence:** US government work, public domain.
- **Content used:** sheet *Response Estimates*, row 16: the revised AI question, "used AI in any of its business functions in the last two weeks", answer "Yes" (%); sheet *Response Standard Errors*, row 16 (% points); sheet *Collection and Reference Dates*: `Smpdt` (period code), reference period start and end, publication date.
- **Primary key:** Question ID, Answer ID by survey period code; dates sheet: Smpdt.
- **Time coverage:** AI question from period 202524 (reference period from 3 Nov 2025) to 202621. No data was collected during the October to November 2025 federal shutdown.
- **Latest observation:** period 202621 (reference period ending 4 Oct 2026, published 22 Oct 2026). **Downloaded:** 23 Oct 2026. **Used by:** Tab 4.

---

## 2. Source samples (`data/sample/`)

Each sample keeps the source column names and values unchanged. Only the rows and columns the app uses are kept.

| Sample | From | Rows | Columns and units | Primary key | Time coverage | Latest observation | How it is made |
|---|---|---|---|---|---|---|---|
| `tab1_construction.csv` | R1 | 152 | `Entity`; `Code`; `Month` (YYYY-MM); `Data center construction` (constant 2021 US$) | Month | Jan 2014 to Aug 2026 | Aug 2026 | `src/tab1_prep.py` step 1: United States rows, read and written as text so every digit is unchanged |
| `tab2_sites.csv` | R2 | 95 | `Name`; `Owner` (with Epoch's tag); `Country`; `Current power (MW)` (IT power, MW); `Current total capital cost (2025 USD billions)` | Name | Snapshot | Release 19 Oct 2026 | `src/tab2_prep.py` step 0: the five columns above, read and written as text |
| `tab3_share.csv` | R3 | 16 | `Entity`; `Year`; `Share of total electricity demand coming from data centers` (%) | Entity, Year | 2020, 2023, 2024, 2025 | 2025 | `src/tab3_prep.py` step 1: United States, China, World and World excl. United States and China |
| `tab3_demand.csv` | R4 | 78 | `Entity`; `Year`; `Electricity demand` (TWh) | Entity, Year | 2000 to 2025 | 2025 | `src/tab3_prep.py` step 1: United States, China and World, 2000 to 2025 |
| `tab3_timelines.csv` | R5 | 567 | `Data center`; `Date` (YYYY-MM-DD); `IT power (MW)`; `Power (MW)` | Data center, Date | 2018-12-18 to 2030-01-01 | Reported 2026-10-19; planned 2030-01-01 | `src/tab3_prep.py` step 1: four columns |
| `tab3_sites.csv` | R2 | 95 | `Name`; `Country` | Name | Snapshot | Release 19 Oct 2026 | `src/tab3_prep.py` step 1: two columns |
| `tab3_construction.csv` | R1 | 152 | `Entity`; `Month`; `Data center construction` (constant 2021 US$) | Month | Jan 2014 to Aug 2026 | Aug 2026 | `src/tab3_prep.py` step 1: three columns |
| `tab3_samples.json` | R6 | – | `epoch_snapshot_date` (the download date that separates reported from planned capacity) | – | – | 2026-10-25 | `src/tab3_prep.py` step 1 |
| `tab4_btos_ai_use.csv` | R7, R8 | 135 | `window` (`old` = original question, `now` = revised question); `file`; `sheet`; `excel_row`; `column` (Excel column letter); `period` (survey period code); `estimate` (cell text, e.g. `10.0%`, or `.` when not published); `se_sheet`; `se_excel_row`; `standard_error` (cell text, % points) | window, period | Old: 202319 to 202520. Now: 202524 to 202621 | Period 202621 | `src/tab4_prep.py` step 1: the AI-use "Yes" row and its standard-error row, found by question text; each cell's text is copied unchanged with its sheet, row and column |
| `tab4_btos_dates.csv` | R8 | 99 | `period` (Smpdt code); `ref_start`, `ref_end` (reference period, YYYY-MM-DD); `dates_row` (row in the dates sheet); `published` (publication date, YYYY-MM-DD; empty if not given) | period | 202319 to 202713 (later periods are the published schedule) | Published 22 Oct 2026 for period 202621 | `src/tab4_prep.py` step 1: Excel dates written as ISO dates; nothing else changed |

---

## 3. Processed files (`data/processed/`, read by the app)

| File | Read by | Primary key | Columns and units | Time coverage | Latest observation | Transform (module and step) |
|---|---|---|---|---|---|---|
| `tab1_monthly.csv` | Tabs 1 and 4 | month | `month` (YYYY-MM); `csv_line` (line in R1 and the sample; line 1 is the header); `spend` (constant 2021 US$, as in the source); `spend_b` (US$ billions); `avg12_b` (US$ billions; empty for the first 11 months) | Jan 2014 to Aug 2026 | Aug 2026 | `src/tab1_prep.py` step 2: `spend_b` = `spend` ÷ 1,000,000,000; `avg12_b` = mean of `spend_b` for the month and the 11 before it |
| `tab2_sites_clean.csv` | Tab 2 | Name | `Name`; `Owner` (tag removed; blank becomes "Owner not disclosed"); `Country`; `Current power (MW)` (MW; blank becomes 0); `Current total capital cost (2025 USD billions)` (blank becomes 0); `owner_confidence` (confident, likely, speculative, untagged or none); `operational` (true if power > 0 MW) | Snapshot | Release 19 Oct 2026 | `src/tab2_prep.py` step 2 `clean()` |
| `tab2_owner_share.csv` | Tab 2 | Owner | `Owner`; `power_mw` (MW); `sites` (count); `share_pct` (% of all current IT power); `cumulative_pct` (%) | Snapshot | Release 19 Oct 2026 | `src/tab2_prep.py` step 3 `share_table()`: group by Owner, sum MW, count sites, sort largest first; share = group MW ÷ total MW × 100 |
| `tab2_country_share.csv` | Tab 2 | Country | `Country`; `power_mw` (MW); `sites` (count); `share_pct` (%); `cumulative_pct` (%) | Snapshot | Release 19 Oct 2026 | Same as above, grouped by Country |
| `tab3_us_demand.csv` | Tab 3 | year | `year`; `demand_twh` (TWh); `change_since_2021_pct` (%); `in_flat_period` (true for 2007 to 2021) | 2000 to 2025 | 2025 | `src/tab3_prep.py` step 2: United States rows; change = demand ÷ 2021 demand − 1, × 100 |
| `tab3_dc_use.csv` | Tab 3 | region, year | `region`; `year`; `share_pct` (%); `demand_twh`, `dc_twh`, `other_twh`, `dc_change_since_2020_twh`, `demand_change_since_2020_twh` (TWh); `dc_share_of_growth_pct` (%, empty in 2020); `share_of_world_dc_pct` (%) | 2020, 2023, 2024, 2025 | 2025 | `src/tab3_prep.py` step 3: join share and demand; `dc_twh` = share ÷ 100 × demand; Rest of world = World − United States − China; share of growth = change in `dc_twh` since 2020 ÷ change in demand × 100 |
| `tab3_ai_capacity.csv` | Tab 3 | month | `month` (YYYY-MM); `power_mw` (MW); `power_gw` (GW); `sites_drawing_power` (count); `status` (reported or planned) | Jan 2019 to Jan 2030 | Reported Sep 2026 (month end); planned Jan 2030 | `src/tab3_prep.py` step 4: US sites; at each month end each site keeps its latest `Power (MW)` record on or before that date; summed; months after the download date are planned |
| `tab3_scenarios.csv` | Tab 3 | region, scenario | `region`; `scenario` (trend, latest, construction); `scenario_label`; `dc_growth_pct`, `other_growth_pct` (% per year); `basis` | Rates measured over 2020 to 2025 | 2025 | `src/tab3_prep.py` step 5: trend = (2025 ÷ 2020)^(1/5) − 1; latest = 2025 ÷ 2024 − 1; construction (US only) = the same formula on calendar-year spending totals |
| `tab3_projection.csv` | Tab 3 | region, scenario, year | `region`; `scenario`; `year`; `dc_twh`, `other_twh`, `total_twh` (TWh); `dc_share_pct` (%); `multiple_of_2025` (ratio) | 2025 to 2030 | Projection | `src/tab3_prep.py` step 6: 2025 values grown each year at the scenario rates. An arithmetic projection, not a forecast |
| `tab4_ai_monthly.csv` | Tab 4 | window, month | `window` (old or now); `month` (YYYY-MM, the month the reference period ends); `ai` (mean % of US employer businesses using AI); `ai_se` (standard error of the mean, % points: √(sum of se²) ÷ n); `n` (estimates averaged); `periods` (period codes averaged, separated by `;`) | Old: Sep 2023 to Sep 2025. Now: Nov 2025 to Oct 2026 | Oct 2026 (period 202621) | `src/tab4_prep.py` step 2: each two-week estimate is placed in the month its reference period ends; estimates in the same month are averaged. The tab then indexes AI use and construction spending to 100 in the first month of the window the user picks |

---

## 4. Checks (run by `python -m src.build_data --check`; each can fail)

- **Reproducibility:** every processed file is rebuilt from the samples and compared byte for byte with the committed file. Tested by changing one digit in `tab1_construction.csv`: the check reported DIFFERENT and stopped.
- **Tab 1 (7 checks):** source columns kept; only United States rows; every month present once with no gaps; no missing or negative values; the latest 12-month average equals a manual mean of the last 12 rows; the latest card value traces to the source cell; November 2022 and the month two years before the latest both exist.
- **Tab 2 (6 checks):** no site dropped; site names unique; no confidence tag left in Owner; no negative power; Owner and Country shares each add up to 100% and to the total MW.
- **Tab 3 (6 checks):** world data centre use in 2024 within 2 TWh of the IEA's 415 TWh; US share of world use in 2024 within 5 points of the IEA's 45%; recalculated Rest of world share matches OWID within 0.01 points; no duplicate keys and complete demand years; every timeline site has a country and no negative power; 12 months of construction in 2020 and 2025.
- **Tab 4 (6 checks):** every estimate with a value is averaged exactly once, for each wording; every period with an estimate has reference dates; shares between 0 and 100%; one row per window and month; reference periods end after they start.

## 5. What the data cannot show

- **All data centres, not only AI.** Construction spending (R1) and electricity shares (R3) cover all data centres; no public source separates AI facilities, so they are upper limits on AI-driven building and use. Epoch AI (R2, R5) covers 95 frontier AI sites, not every data centre.
- **Buildings, not hardware.** R1 excludes servers and chips, often the largest part of AI data centre cost.
- **Gaps and revisions.** No data centre share for 2021 and 2022; no BTOS data during the October to November 2025 shutdown; recent construction months are preliminary and revised.
- **Use, not intensity.** BTOS counts how many businesses use AI, not how much they use it, and covers US employer businesses only. The two BTOS question wordings measure different things, so they are never joined.
- **National totals.** Data centres cluster in a few states, so state-level loads can be much higher than the national figures.
- **Planned capacity and projections** reflect announcements and assumed growth rates, not forecasts.
