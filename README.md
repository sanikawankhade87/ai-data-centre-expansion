# AI Data Centre Expansion

36104 Data Visualisation and Narratives, Assignment 3: The Rise of Artificial Intelligence: Data Narrative Studio.

**Question:** Is the rapid expansion of AI data centres justified by the actual demand for AI?

- **Live app:** https://ai-data-centre-expansion.streamlit.app/
- **Repository:** https://github.com/sanikawankhade87/ai-data-centre-expansion
- **Question territory:** Energy and water. What does AI infrastructure cost the grid?

## Persona

**Dana Reyes**, an energy policy analyst advising a US state public utilities commission.

**Her decision:** whether the state should plan new generation and grid capacity for data centres as **permanent demand**, or treat the current surge as a **short-term spike** that may not last.

She reads charts confidently but is not a data scientist, so every chart answers one question in plain language and every headline number shows its source. The app is built for her decision; investors and network planners may also find it useful.

## Why the question is arguable

The same data supports two readings. Construction spending, data centre electricity use and the share of businesses using AI are all rising, which reads as real demand being met by new supply. But in the most recent months construction spending has grown faster than AI use, and much planned capacity is still only announced, which reads as building running ahead of demand. Which reading wins depends on the window compared and on whether announced capacity is trusted as future use. The app tests one thing: whether the pace of construction matches the measured pace of AI use.

## The answer the data supports

**Partly.** From September 2023 to September 2025, the share of US firms using AI grew at least as fast as data centre construction spending (index 269 against 236). Since November 2025, construction spending has grown clearly faster than AI use (index 168 against 132), so the newest wave of building is running ahead of measured demand. That recent gap covers only nine months of data. The answer appears on the app's opening screen and is worked through in Tab 4.

## User stories

### 1. Is the building wave still speeding up?
**As an** energy policy analyst, **I want** to see how fast data centre construction spending is growing and whether that growth is accelerating, **so that** I can judge whether the building wave will keep adding load at an increasing rate before I plan new grid capacity.

**Walk through it in the app:**
1. Open the app and click **🏗️ 1 · Pace of Construction**.
2. Read the three cards: $5.37bn spent in August 2026 (+66% on August 2025), a 12-month average of $3.83bn a month (4.6 times the November 2022 level), and growth of the 12-month average of +34%, down from +57% a year earlier.
3. Drag **Show from** to 2022 to zoom in on the years since ChatGPT; switch **12-month average** off and on to compare the raw monthly line with the trend.
4. Read **What this means for Dana**: spending is still rising fast, but the growth rate has slowed.
5. Optional: open **🏢 2 · Builders and Locations** to see who is building. Five owners hold 71% of current AI data centre power, so each grid request is a bet on a few companies' plans.

### 2. How big is the load on the grid?
**As an** energy policy analyst, **I want** to see how much electricity data centres already use and how large that load could become by 2030, **so that** I can size the grid capacity my state may need to plan for.

**Walk through it in the app:**
1. Click **⚡ 3 · Electricity Demand**.
2. Section 2 shows US data centres used 224 TWh in 2025, 4.9% of US demand, and account for 26% of the rise in US demand since 2020.
3. In section 5, choose a **Region** and a **Growth rate**. The cards and chart show data centre use in 2030 under that rate (465 TWh, 9.1% of demand, at the 2020 to 2025 trend for the United States).
4. Read **What this means for Dana**: depending on the rate, US data centre use would reach 465 to 848 TWh by 2030.

### 3. Is it permanent demand or a spike?
**As an** energy policy analyst, **I want** to compare the growth of measured AI use with the growth of data centre construction, **so that** I can decide whether to plan for data centre load as permanent demand or as a spike that may not last.

**Walk through it in the app:**
1. Read the answer on the opening screen.
2. Click **📈 4 · Demand Comparison**. The cards give the verdict for each survey wording: "AI use kept pace" (Sep 2023 to Sep 2025) and "Building ran ahead" (Nov 2025 to Aug 2026).
3. Move the month sliders to choose the comparison window; the chart, cards and verdict update, and the first month picked becomes 100 for both lines.
4. Read the gap chart, which shows month by month whether AI use or building is ahead.
5. Open **🔍 Trace** to follow both index values back to the cells of the source files, and **Does the answer depend on which months are picked?** to test the verdict.

## What is in the app

| Tab | Question it answers | Main chart | Visual Vocabulary family | Owner |
|---|---|---|---|---|
| Opening screen | The group question, Dana and the answer | – | – | Shared |
| 1 · Pace of Construction | How fast is construction spending growing, and is it accelerating? | Line chart, monthly spending with a 12-month average | Change over time | Sanika Wankhade |
| 2 · Builders and Locations | Is capacity concentrated in a few organisations or countries? | Ranked horizontal bar chart | Ranking | Erkebai (Eric) Bakhavadinov |
| 3 · Electricity Demand | What does the expansion cost the US grid, and how large could the load become? | Line, bar and ranked bar charts (5) | Change over time, magnitude, ranking | Szexuan Yap |
| 4 · Demand Comparison | Is actual AI use growing as fast as construction? | Indexed line chart and a gap (deviation) bar chart | Change over time, deviation | Aaron Sapkota |

Nine charts across four Visual Vocabulary families. Every chart has a title or caption saying what it shows, labelled axes with units, and value labels so it can be read without hovering. Each tab states what the data cannot show and shows its sources and last data refresh on screen.

## Data

All data is public and citable: US Census Bureau (construction spending; Business Trends and Outlook Survey), US Bureau of Labor Statistics, IEA and Ember via Our World in Data, and Epoch AI.

```
data/
  raw/ and top-level source files   raw downloads, never edited
  sample/                           source samples: the rows and columns the app uses, values unchanged
  processed/                        files the app reads, built from the samples
  DATA_DICTIONARY.md                every dataset: source, URL, licence, columns and units,
                                    primary key, time coverage, latest observation, transform
src/                                one prep module per tab with the documented transforms and checks
scripts/                            download scripts, dictionary check, colour check
```

Regenerate every processed file from the samples and confirm they match exactly:

```bash
pip install -r requirements.txt
python -m src.build_data --check       # rebuilds in memory, compares byte for byte, runs every check
python -m src.build_data               # rewrites data/processed/ from data/sample/
python scripts/check_dictionary.py     # every data file and column is documented
python scripts/check_colours.py        # colour vision deficiency check
streamlit run app.py
```

## AI use

- **AI provenance matrix:** [`PROVENANCE.md`](PROVENANCE.md), one row per substantive AI use, with the check that verified it.
- **Data and AI disclosure statement:** [`DISCLOSURE.md`](DISCLOSURE.md).

## Team

| Member | Contribution |
|---|---|
| Sanika Wankhade | Tab 1; repository, deployment, opening screen and shared theme; data package build and checks; README, data dictionary and documentation |
| Erkebai (Eric) Bakhavadinov | Tab 2 |
| Szexuan Yap | Tab 3 |
| Aaron Sapkota | Tab 4 and the opening-screen answer |

## Assessed version

The assessed version is the commit hash given in the group's submitted PDF.
