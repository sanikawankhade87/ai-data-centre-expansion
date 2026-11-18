# Tab 1 · Pace of Construction

| | |
|---|---|
| **Owner** | Sanika Wankhade |
| **Sub-question** | How fast is US data centre construction spending growing, and is the growth accelerating? |
| **Persona** | Dana Reyes, energy policy analyst advising a US state public utilities commission (the group persona, see [README.md](README.md)) |
| **Short answer for Dana** | Spending is still rising fast ($5.37bn in Aug 2026, +66% on a year earlier), but the growth rate peaked in the year to Aug 2024 and has slowed since |
| **Charts** | Line chart (change over time); column chart of yearly growth (change over time) |

## 1. Files

| File | Purpose |
|---|---|
| `tab1_construction.py` | The tab. `app.py` imports it and calls `render()` inside the first tab |
| `src/tab1_prep.py` | Every transformation, in commented steps, plus eight checks that can fail |
| `scripts/download_tab1.py` | Downloads a fresh, unedited copy from Our World in Data and compares it with the committed file |
| `data/monthly-spending-data-center-us.csv` | Raw download, never edited (shared with Tabs 3 and 4 so all tabs show the same numbers) |
| `data/sample/tab1_construction.csv` | Source sample: the rows and columns Tab 1 uses, values unchanged |
| `data/processed/tab1_monthly.csv` | The file the tab reads (also read by Tab 4) |

## 2. Run it

```bash
pip install -r requirements.txt
python -m src.tab1_prep               # raw file -> sample -> processed file, then the checks
python -m src.tab1_prep --from-sample # rebuild the processed file from the sample only
python -m src.tab1_prep --validate    # checks only
streamlit run app.py                  # Tab 1 is the first tab
```

## 3. Data

| Item | Detail |
|---|---|
| Source | US Census Bureau, *Value of Construction Put in Place* (private construction, data centres), adjusted to constant 2021 US$ with US Bureau of Labor Statistics producer price indexes, processed by Our World in Data |
| URL | https://ourworldindata.org/grapher/monthly-spending-data-center-us |
| Licence | CC BY 4.0 (Our World in Data); underlying US government data is public domain |
| Columns used | `Entity` (always United States); `Code` (USA); `Month` (YYYY-MM); `Data center construction` (constant 2021 US$) |
| Primary key | Month (152 rows) |
| Time coverage | January 2014 to August 2026, every month |
| Latest observation | August 2026 (OWID update 2 Oct 2026); recent months are preliminary |
| Downloaded | 23 Oct 2026 |

- Values are **monthly spending**, not annual rates, and are **not seasonally adjusted**.
- The series covers **buildings only** (materials, labour, contractor costs). It excludes servers and IT equipment, land and maintenance.
- It covers **all data centres**; no public source separates AI facilities.

Processed file `data/processed/tab1_monthly.csv`: `month` (YYYY-MM); `csv_line` (line in the raw file); `spend` (constant 2021 US$, as in the source); `spend_b` (US$ billions); `avg12_b` (US$ billions; empty for the first 11 months). Full column detail for every file is in [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md).

## 4. Transformations

All steps are in `src/tab1_prep.py`. No rows are dropped and no values are imputed.

| Step | What it does |
|---|---|
| 1 | Keep the United States rows and the four source columns, values unchanged → sample |
| 2 | Spending in billions = value ÷ 1,000,000,000; 12-month average = mean of the month and the 11 before it → processed file |
| 3 | Card figures (formulas below) |
| 3b | Growth chart: 12-month average in each August ÷ the same a year earlier − 1, one bar per year (computed on screen, not saved) |
| 4 | Checks (section 9) |

| Card | Formula | Value |
|---|---|---|
| Spending in the latest month | Aug 2026 value ÷ 10⁹ | $5.37bn |
| Change vs the same month a year earlier | Aug 2026 ÷ Aug 2025 − 1 | +66% |
| 12-month average per month | Mean of Sep 2025 to Aug 2026 | $3.83bn |
| Multiple of the level before ChatGPT | 12-month average now ÷ 12-month average at Nov 2022 | 4.6× |
| Growth of the 12-month average | Average now ÷ average a year earlier − 1 | +34% (was +57%) |

## 5. Charts and design decisions

| Chart | Visual task | Why this form | Alternative rejected |
|---|---|---|---|
| Line chart: monthly spending (thin grey) with a 12-month average (thick amber) and a marker at ChatGPT's release | See whether spending is growing | The raw data is not seasonally adjusted; the rolling average smooths the seasonal pattern so the trend is visible, while the raw line stays on the chart so nothing is hidden | A bar chart of 152 raw months: the bars jump up and down every month and the noise hides the trend |
| Column chart: growth of the 12-month average in each year to August (grey before ChatGPT, amber after) | See whether growth is speeding up or slowing down | Answers the "accelerating?" half of the question directly; bars on a shared baseline make the peak and the slowdown easy to compare | Reading the slope of the line chart: changes in slope are hard to judge by eye |

Every chart has a title, axis titles with units, and value labels, so it can be read without hovering.

## 6. Interaction

- **Show from** slider: start the line chart at any year, for example 2022 to zoom in on the years since ChatGPT.
- **12-month average** toggle: show or hide the average to compare it with the raw monthly line.
- **Hover:** shows both values for any month, and the exact growth for any bar.

## 7. What it shows for Dana

Spending is still rising fast. August 2026 was 66% above August 2025, and the 12-month average is 4.6 times its level before ChatGPT. But the growth *rate* has slowed: the 12-month average grew 72% in the year to August 2024, 57% to August 2025 and 34% to August 2026. More is being built every month, just not at an ever-faster rate.

## 8. Trace a number

1. Open `data/monthly-spending-data-center-us.csv`, row United States, `2026-08`: **5371310412**.
2. Divide by 1,000,000,000 and round to two decimals: **$5.37bn**, the first card.
3. Compare with the `2025-08` row (3228965955): 5371310412 ÷ 3228965955 − 1 = **+66%**.
4. The **🔍 Trace the headline number** section in the tab shows the same rows and every card's calculation on screen.

## 9. Checks

`python -m src.tab1_prep --validate` runs eight checks; the build stops if any fails.

1. The sample keeps the four source columns.
2. Every row is United States.
3. Every month from the first to the last is present once, with no gaps.
4. No missing or negative spending values.
5. The latest 12-month average equals a manual mean of the last 12 rows.
6. The latest card value traces to the source cell (5,371,310,412 ÷ 10⁹ = 5.37).
7. November 2022 and the month two years before the latest both exist, so every card can be computed.
8. The growth chart has one bar per year, and its last two bars equal the third card (+34%) and its comparison (+57%).

## 10. Limits

- **All data centres, not only AI ones,** so this is an upper bound on AI-driven building.
- **Buildings only:** servers and chips, often the larger cost, are not included.
- **Spending is not electricity load:** a building adds load only once it is fitted out and switched on (Tab 3 covers the load).
- **Not seasonally adjusted,** and recent months are preliminary and revised.
- **National totals only;** data centres cluster in a few states.
- **A slower growth rate is not a fall:** spending is still higher every year.

The same limits are shown in the tab under **⚠️ What this tab can and cannot tell Dana**.

## 11. AI use

Recorded in [PROVENANCE.md](PROVENANCE.md), rows 1 to 7.

| What | Tool | How it was checked |
|---|---|---|
| Drafted the tab code (cards, line chart, trace panel) | Claude (Anthropic) | Recomputed the cards by hand from the raw CSV: 5371310412 ÷ 10⁹ = 5.37; 5371310412 ÷ 3228965955 − 1 = 0.66; checked the 12-month average against the mean of the last 12 rows |
| Checked the units and coverage of the data | Claude (Anthropic) | Confirmed on the Our World in Data page that the values are monthly, in constant 2021 US$, not seasonally adjusted |
| Added the yearly growth chart and the limits section | Claude (Anthropic) | Recomputed the peak bar by hand: mean of Sep 2023 to Aug 2024 ($1.82bn) ÷ mean of Sep 2022 to Aug 2023 ($1.06bn) − 1 = +72%; check 8 fails unless the last two bars equal the cards |
