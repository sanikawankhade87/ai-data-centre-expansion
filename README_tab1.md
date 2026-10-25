# Tab 1 · Pace of Construction

**Owner:** Sanika Wankhade
**Sub-question:** How fast is US data centre construction spending growing, and is the growth accelerating?
**Persona:** Dana Reyes, energy policy analyst (the group persona, as on the front page).

## Files

| File | Purpose |
|---|---|
| `tab1_construction.py` | The tab. `app.py` imports it and calls `render()` inside the first tab. All loading and transformation steps are in `load_data()`, with comments |
| `data/monthly-spending-data-center-us.csv` | Raw Our World in Data download (never edited by hand). Shared with Tabs 3 and 4 so all tabs show the same numbers |

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py                 # Tab 1 is the first tab
streamlit run tab1_construction.py   # or preview Tab 1 on its own
```

## Data

US Census Bureau, *Value of Construction Put in Place* (private data centre construction), adjusted for inflation with US Bureau of Labor Statistics producer price indexes, processed by Our World in Data.
https://ourworldindata.org/grapher/monthly-spending-data-center-us

| Item | Detail |
|---|---|
| Columns | `Entity` (text, always United States); `Code` (USA); `Month` (YYYY-MM); `Data center construction` (constant 2021 US$) |
| Primary key | Month |
| Rows | 152 |
| Time coverage | January 2014 to August 2026, every month |
| Latest observation | August 2026 (OWID update 2 Oct 2026); recent months are preliminary and get revised |
| Licence | CC BY 4.0 (Our World in Data); US government data |

- Values are **monthly spending**, not annual rates, and are **not seasonally adjusted**, so they rise and fall with the construction season.
- The series covers the **buildings only**: materials, labour and contractor costs. It excludes servers and other IT equipment, land and maintenance, so it is only part of total data centre investment.
- Only privately owned projects are included.
- It covers **all data centres**. No public source separates AI facilities, so the series is an upper limit on AI-driven construction.

## Transformations

All steps are in `load_data()` in `tab1_construction.py`. No rows are dropped and no values are imputed.

| Step | What it does |
|---|---|
| 1 | Read the CSV and keep the United States rows (the only rows in the file) |
| 2 | Turn `Month` text (e.g. `2026-08`) into a date |
| 3 | Express spending in billions: value ÷ 1,000,000,000 |
| 4 | 12-month average = mean of the current month and the 11 before it (first value: December 2014) |

The cards then use these formulas:

| Card | Formula | Value (Aug 2026) |
|---|---|---|
| Spending in the latest month | Aug 2026 value ÷ 10⁹ | $5.37bn |
| Change vs the same month a year earlier | Aug 2026 ÷ Aug 2025 − 1 | +66% |
| 12-month average per month | Mean of Sep 2025 to Aug 2026 | $3.83bn |
| Multiple of the level before ChatGPT | 12-month average now ÷ 12-month average at Nov 2022 | 4.6× |
| Growth of the 12-month average, past year | Average now ÷ average a year earlier − 1 | +34% (was +57% the year before) |

Comparing the same month a year apart, and using the 12-month average, both remove the seasonal pattern.

## Design decision

- **Visual task:** see whether monthly spending is growing, and whether that growth is speeding up.
- **Form chosen:** a line chart of monthly spending (thin grey line) with a 12-month rolling average (thick amber line), and a marker at ChatGPT's release in November 2022.
- **Alternative rejected:** a bar chart of the raw monthly values.
- **Why it lost:** the data is not seasonally adjusted, so 152 bars jump up and down every month. That noise hides the trend, and the question is whether growth is accelerating. The rolling average smooths the seasonal pattern so the change in pace is visible, while the raw line stays on the chart so nothing is hidden.

## Interaction

- **Show from** slider: start the chart at any year, to zoom in on the period since 2022.
- **12-month average** toggle: show or hide the average to compare it with the raw monthly line.
- **Hover:** shows the monthly value and the 12-month average for any month.

## What it shows for Dana

Spending is still rising fast. August 2026 was 66% above August 2025, and the 12-month average is 4.6 times its level before ChatGPT. But the growth *rate* has slowed: the 12-month average grew 72% in the year to August 2024, 57% to August 2025 and 34% to August 2026. More is being built every month, just not at an ever-faster rate.

## Trace a number (for the recording)

1. Open `data/monthly-spending-data-center-us.csv` and find the row United States, `2026-08`: **5371310412**.
2. Divide by 1,000,000,000 and round to two decimals: **$5.37bn**, the first card.
3. Compare with the `2025-08` row (3228965955): 5371310412 ÷ 3228965955 − 1 = **+66%**.
4. The "Trace the headline number" expander in the tab shows the same row and every card's calculation on screen.

## Limits

- Buildings only: the series leaves out servers and chips, often the largest share of AI data centre cost.
- All data centres, not only AI ones.
- Not seasonally adjusted, and recent months are preliminary and revised each year.
- National figures only; data centres cluster in a few states.

## AI use log

| What | Tool | How I checked it |
|---|---|---|
| Drafted the tab code (cards, chart, trace panel) | Claude (Anthropic) | Recomputed the cards by hand from the raw CSV: 5371310412 ÷ 10⁹ = 5.37; 5371310412 ÷ 3228965955 − 1 = 0.663; checked the 12-month average against the mean of the last 12 rows |
| Checked the units and coverage of the data | Claude, using the OWID chart page | Confirmed on the OWID page that the values are monthly, in constant 2021 US$, not seasonally adjusted |
| _add your own entries_ | | |
