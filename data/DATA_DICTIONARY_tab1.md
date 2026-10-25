# Data Dictionary: Tab 1 (Pace of Construction)

Every dataset Tab 1 reads, from the raw download to the processed file. All transforms are in `src/tab1_prep.py`.

| Command | Reads | Writes |
|---|---|---|
| `python scripts/download_tab1.py` | Published URLs | `data/raw/tab1/` (fresh copy, metadata and `retrieval_log.json`); compares it with the shared file |
| `python scripts/download_tab1.py --replace` | Published URLs | The above, and replaces the shared `data/monthly-spending-data-center-us.csv` (agree with the group first: Tabs 3 and 4 read it too) |
| `python -m src.tab1_prep` | Raw file | `data/processed/tab1_monthly.csv`, then runs the checks |
| `python -m src.tab1_prep --validate` | Raw file | Seven checks, printed as PASS or FAIL |

## Source dataset

| File | Source and URL | Licence | Columns and units | Primary key | Time coverage | Latest observation |
|---|---|---|---|---|---|---|
| `data/monthly-spending-data-center-us.csv` (152 rows, shared with Tabs 3 and 4) | US Census Bureau, *Value of Construction Put in Place* (private construction), and US Bureau of Labor Statistics producer price indexes, processed by Our World in Data. https://ourworldindata.org/grapher/monthly-spending-data-center-us | CC BY 4.0 (OWID); US government data | `Entity` (text, United States only); `Code` (USA); `Month` (YYYY-MM); `Data center construction` (constant 2021 US$, monthly, not seasonally adjusted) | Month | Jan 2014 to Aug 2026, every month | Aug 2026 (OWID update 2 Oct 2026); recent months are preliminary |

What the series covers: on-site work to build privately owned data centre buildings each month (materials, labour, contractor costs). It excludes servers and other IT equipment, land and maintenance. OWID adjusts it to 2021 prices with a composite index that weights the BLS producer price indexes for new industrial and new warehouse building construction equally.

## Processed dataset

| File | Primary key | Columns and units | Time coverage | Transform |
|---|---|---|---|---|
| `data/processed/tab1_monthly.csv` | month | `month` (YYYY-MM); `spend` (constant 2021 US$, as in the source); `spend_b` (US$ billions); `avg12_b` (US$ billions; empty for the first 11 months) | Jan 2014 to Aug 2026 | Keep United States rows. `spend_b` = `spend` ÷ 1,000,000,000. `avg12_b` = mean of `spend_b` for the month and the 11 before it |

## Card formulas

| Card | Formula | Value (Aug 2026) |
|---|---|---|
| Spending in the latest month | `spend_b` for Aug 2026 | $5.37bn |
| Change vs the same month a year earlier | Aug 2026 `spend` ÷ Aug 2025 `spend` − 1, × 100 | +66% |
| 12-month average per month | `avg12_b` for Aug 2026 | $3.83bn |
| Multiple of the level before ChatGPT | `avg12_b` Aug 2026 ÷ `avg12_b` Nov 2022 | 4.6× |
| Growth of the 12-month average | `avg12_b` Aug 2026 ÷ `avg12_b` Aug 2025 − 1, × 100 (and the same a year earlier) | +34% (was +57%) |

## Checks (run on every build)

1. The source columns `Entity`, `Month` and `Data center construction` are present.
2. Every row is United States.
3. Every month from the first to the last is present once, with no gaps or duplicates (152 rows, Jan 2014 to Aug 2026).
4. No missing or negative spending values.
5. The latest 12-month average equals a manual mean of the last 12 rows.
6. The latest card value traces back to the raw cell (5,371,310,412 ÷ 10⁹ = 5.37).
7. November 2022 and the month two years before the latest both exist, so every card can be computed.

## What the data cannot show

- Buildings only: servers and chips, often the largest part of AI data centre cost, are not included.
- All data centres: no public source separates AI facilities, so the series is an upper limit on AI-driven construction.
- Not seasonally adjusted, so single months rise and fall with the construction season; the tab compares the same month a year apart and uses the 12-month average for this reason.
- Recent months are preliminary, and the Census Bureau revises the previous two years each year.
- National totals only; data centres cluster in a few states.
