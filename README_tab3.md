# Tab 3 · Electricity Demand

**Owner:** Szexuan Yap
**Sub-question:** What does the data centre expansion cost the US electricity grid, and how large could this load become?
**Persona:** Dana Reyes, energy policy analyst (the group persona, as on the front page).

## Files

| File | Purpose |
|---|---|
| `tab3_electricity.py` | The tab. `app.py` imports it and calls `render()` inside the third tab |
| `src/tab3_prep.py` | Every transformation, in seven numbered steps, plus six checks |
| `scripts/download_tab3.py` | Downloads the three Tab 3 sources, unedited, to `data/raw/tab3/` and records the download date and size of each file |
| `data/raw/tab3/` | Raw downloads (never edited by hand), with the Our World in Data metadata files and `retrieval_log.json` |
| `data/sample/tab3_*.csv` | Source samples: the rows and columns Tab 3 uses, values unchanged |
| `data/processed/tab3_*.csv` | The five processed files the tab reads, one for each section of the page |
| `data/DATA_DICTIONARY_tab3.md` | Every column, unit, formula and check |

## Run it

```bash
pip install -r requirements.txt
python scripts/download_tab3.py        # optional: fresh copies of the raw files
python -m src.tab3_prep                # raw files -> samples -> processed files, then the checks
python -m src.tab3_prep --from-sample  # rebuild the processed files from the samples
python -m src.tab3_prep --validate     # checks only
streamlit run app.py                   # Tab 3 is the third tab
streamlit run tab3_electricity.py      # or preview Tab 3 on its own
```

## Data

| Source | Publisher | Coverage | Latest observation | Licence |
|---|---|---|---|---|
| Data centre share of electricity demand (%) | IEA, *Energy and AI*, and Ember, via Our World in Data | 2020, 2023, 2024 and 2025 | 2025 (OWID update 30 Jun 2026) | IEA terms of use with attribution; Ember CC BY 4.0 |
| Total electricity demand (TWh) | Ember, via Our World in Data | Every year, 2000 to 2025 | 2025 (OWID update 30 Jun 2026) | CC BY 4.0 |
| Frontier AI data centre timelines (MW) | Epoch AI, *AI data centers* | Dated records, 2018 to 2030 | Reported to Oct 2026; planned to Jan 2030 | CC BY 4.0 |
| AI data centre sites (country of each site) | Epoch AI (same file as Tab 2) | 95 sites | Release of 19 Oct 2026 | CC BY 4.0 |
| Data centre construction spending (constant 2021 US$) | US Census Bureau, via Our World in Data (same file as Tab 1) | Monthly, Jan 2014 to Aug 2026 | Aug 2026 | CC BY 4.0; US government data |

## Transformations

All steps are in `src/tab3_prep.py`. Full column-by-column detail is in `data/DATA_DICTIONARY_tab3.md`.

| Step | What it does | Processed file |
|---|---|---|
| 1 | Keep the rows and columns Tab 3 uses, values unchanged | `data/sample/tab3_*.csv` |
| 2 | US total demand by year, with the change since 2021 and the 2007 to 2021 flat period marked | `tab3_us_demand.csv` |
| 3 | Data centre use (TWh) = share ÷ 100 × total demand, for the United States, China and World. Rest of world = World − United States − China | `tab3_dc_use.csv` |
| 4 | US frontier AI power at each month end: every site keeps its latest reported value until its next record. Months after the download date are marked planned | `tab3_ai_capacity.csv` |
| 5 | Yearly growth rates measured from the data: the 2020 to 2025 trend, the latest year, and the construction spending trend (United States only) | `tab3_scenarios.csv` |
| 6 | 2025 data centre use grown forward each year to 2030 at each rate | `tab3_projection.csv` |
| 7 | Six checks; the build stops if any fails | |

The cards then use these formulas:

| Section | Card | Formula | Value |
|---|---|---|---|
| 1 | Change since 2021 | 2025 demand ÷ 2021 demand − 1 | +8.2% |
| 2 | Data centre use, 2025 | 4.9384785% ÷ 100 × 4,535.81 TWh | 224 TWh |
| 2 | Share of US demand growth, 2020 to 2025 | Rise in data centre use ÷ rise in total demand | 116 ÷ 445 TWh = 26% |
| 3 | US share of world data centre use, 2025 | US data centre use ÷ world data centre use | 224 ÷ 485 TWh = 46% |
| 4 | Planned power capacity, end of 2028 | Sum of planned site power capacity at Dec 2028 | 43.0 GW (2.8 times Sep 2026) |
| 5 | Growth rate, measured trend | (2025 use ÷ 2020 use)^(1/5) − 1 | 15.7% a year |
| 5 | Data centre use, 2030 | 2025 use × (1 + rate)^5 | 465 TWh (9.1% of demand) |

## Design decision

- **Visual task:** compare how much electricity US data centres used in each year with data (Section 2).
- **Form chosen:** a bar chart with every value labelled.
- **Alternative rejected:** a line chart over time.
- **Why it lost:** the source only publishes data centre shares for 2020, 2023, 2024 and 2025. A line would draw a slope across 2021 and 2022, suggesting values that do not exist, while separate bars show only what was measured. For the same reason, the tab opens with total US demand, which has data for every year from 2000 to 2025, ensuring the continuous trend comes from complete data.

## Interaction

- **Region** (Section 5): the United States, China, Rest of world or World.
- **Growth rate** (Section 5): the measured trend, the latest year, or the construction spending trend. The cards and the projection chart update.
- **Empty state:** the construction spending rate exists for the United States only. Selecting it for any other region shows a message in place of the chart.

## What it shows for Dana

After almost no growth between 2007 (4,174 TWh) and 2021 (4,193 TWh), US electricity demand rose by 8% in four years. Data centres used 224 TWh in 2025 (4.9% of US demand) and account for 26% of the rise in demand since 2020. Announced AI projects would raise frontier AI power capacity from 15.2 GW in September 2026 to 43.0 GW by the end of 2028. Depending on the growth rate, US data centre use would reach between 465 and 848 TWh by 2030, which is the load the grid may need to absorb if the expansion continues.

## Limits

- All data centres, not only AI ones.
- No data centre share for 2021 and 2022.
- Epoch AI covers frontier AI sites only, and planned capacity follows announcements that may be delayed or cancelled. Few projects are announced beyond 2028, so the planned line levels off there.
- The projection applies a constant growth rate, so it shows a possible size of the load, not a forecast.
- National figures only; data centres cluster in a few states.
