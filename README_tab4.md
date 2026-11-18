# Tab 4 · Demand Comparison

| | |
|---|---|
| **Owner** | Aaron Sapkota |
| **Sub-question** | Is actual AI use growing at the same pace as data centre construction? |
| **Persona** | Dana Reyes, energy policy analyst advising a US state public utilities commission (the group persona, see [README.md](README.md)) |
| **Short answer for Dana** | Partly. From Sep 2023 to Sep 2025, AI use kept pace (index 269 against 236). Since Nov 2025, building has run ahead (index 168 against 132). This tab carries the group's answer on the opening screen |
| **Charts** | Indexed line chart (change over time); gap bar chart (deviation) |

## 1. Files

| File | Purpose |
|---|---|
| `tab4_demand.py` | The tab. `app.py` imports it and calls `render()` inside the fourth tab |
| `src/tab4_prep.py` | Every transformation, in commented steps, plus six checks that can fail |
| `data/AI Core Questions.xlsx` | Raw download, never edited: the original BTOS AI question |
| `data/National.xlsx` | Raw download, never edited: the revised BTOS AI question and the survey reference dates |
| `data/sample/tab4_btos_ai_use.csv`, `tab4_btos_dates.csv` | Source samples: the cells Tab 4 uses, text unchanged, with sheet, row and column for each |
| `data/processed/tab4_ai_monthly.csv` | The file the tab reads |

Construction spending comes from Tab 1's processed file (`data/processed/tab1_monthly.csv`), so Tabs 1 and 4 always show the same spending.

## 2. Run it

```bash
pip install -r requirements.txt
python -m src.tab4_prep               # raw files -> samples -> processed file, then the checks
python -m src.tab4_prep --from-sample # rebuild the processed file from the samples only
python -m src.tab4_prep --validate    # checks only
streamlit run app.py                  # Tab 4 is the fourth tab
```

## 3. Data

| Item | Detail |
|---|---|
| Source | US Census Bureau, *Business Trends and Outlook Survey* (BTOS), national estimates; construction spending as in Tab 1 |
| URL | https://www.census.gov/hfp/btos/data_downloads |
| Licence | US government work, public domain |
| Measure | Share of US employer businesses that used AI in the last two weeks (%), one estimate per two-week survey period, with its standard error |
| Original question | "used AI in producing goods or services" (`AI Core Questions.xlsx`, sheet *National Estimates*): periods 202319 to 202520, Sep 2023 to Sep 2025 |
| Revised question | "used AI in any of its business functions" (`National.xlsx`, sheet *Response Estimates*, row 16): periods 202524 to 202621, Nov 2025 to Oct 2026 |
| Latest observation | Period 202621 (reference period ending 4 Oct 2026, published 22 Oct 2026); construction spending to Aug 2026 |
| Downloaded | 23 Oct 2026 |

- The Census Bureau **changed the AI question on 17 Nov 2025**, and **collected no data during the October to November 2025 federal shutdown**. The jump from about 10% to 17% of firms between the two wordings comes from the new definition, not from new users, so the two are never joined into one line.

Processed file `tab4_ai_monthly.csv`: `window` (old or now); `month` (YYYY-MM, the month the reference period ends); `ai` (mean % of firms using AI); `ai_se` (standard error, % points); `n` (estimates averaged); `periods` (period codes averaged). Full column detail is in [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md).

## 4. Transformations

All steps are in `src/tab4_prep.py` and `tab4_demand.py`. No values are imputed.

| Step | What it does |
|---|---|
| 1 | Keep the "used AI in the last two weeks: Yes" row and its standard errors, cell text unchanged, with sheet, Excel row and column for each cell; keep the reference period of every survey period → samples |
| 2 | Each two-week estimate goes in the month its reference period ends; estimates in the same month are averaged → `tab4_ai_monthly.csv` |
| 3 | Checks (section 9) |
| 4 (in the tab) | Both series are set to 100 in the first month of the window the user picks: index = value ÷ first-month value × 100 |
| 5 (in the tab) | Verdict: AI use index ÷ build index at the end of the window. At least 1.00 = "AI use kept pace"; 0.90 to 1.00 = "Too close to call"; below 0.90 = "Building ran ahead" |

| Card | Value |
|---|---|
| Original question: Sep 2023 to Sep 2025 | AI use kept pace (AI use 269 vs build 236) |
| Revised question: Nov 2025 to Aug 2026 | Building ran ahead (AI use 132 vs build 168) |
| Latest share of US firms using AI | 24.6% (period 202621) |

## 5. Charts and design decisions

| Chart | Visual task | Why this form | Alternative rejected |
|---|---|---|---|
| Indexed line chart, one panel per question wording: AI use (blue) and construction spending (amber), both 100 at the start | Compare the growth of two series with different units | Dollars and % of firms cannot share an axis; indexing both to 100 means the steeper line is the one growing faster | One joined AI line across both wordings: the jump between them comes from the new definition, so joining them would show growth that did not happen |
| Gap bar chart: AI use index minus build index each month (index points) | See month by month which side is ahead | Bars above or below a zero line show the size and direction of the gap directly | Reading the gap off the line chart: small differences between two lines are hard to judge by eye |

Index values are labelled each quarter and every gap bar is labelled, so the charts can be read without hovering.

## 6. Interaction

- **Month sliders,** one per question wording: choose the comparison window. The first month picked becomes 100 for both lines, and the charts, cards and verdict update.
- **Hover:** shows both index values and the raw numbers (spending and % of firms) for any month.
- **🧪 Does the answer depend on which months are picked?** compares single months with three-month averages and gives the growth in yearly terms.

## 7. What it shows for Dana

From Sep 2023 to Sep 2025, the share of US firms using AI went from 3.70% to 9.95% (index 269) while construction spending reached index 236: AI use kept pace. Under the revised question, from Nov 2025 to Aug 2026, AI use reached index 132 and construction 168: building ran ahead. The three-month averages give the same verdicts (236 vs 220, and 122.5 vs 152.0). The newest wave of building is outpacing measured use, so part of the new data centre load may not be permanent, but that recent gap covers only nine months of data.

## 8. Trace a number

1. **AI use index:** `data/National.xlsx`, sheet *Response Estimates*, row 16. Base month Nov 2025: (17.3% in cell AB16 + 17.2% in cell AA16) ÷ 2 = **17.25%**. End month Aug 2026: (22.4% in cell I16 + 23.2% in cell H16) ÷ 2 = **22.80%**. Index = 22.80 ÷ 17.25 × 100 = **132.2**.
2. **Build index:** `data/monthly-spending-data-center-us.csv`, Aug 2026 ÷ Nov 2025 = 5,371,310,412 ÷ 3,189,271,464 × 100 = **168.4**.
3. **Verdict:** 132.2 ÷ 168.4 = **0.78**, below 0.90, so "Building ran ahead".
4. **Sampling error:** the 95% range on the AI use index is about ±3.4 points, against a gap of 36 points.
5. The **🔍 Trace** section in the tab shows every cell and step on screen.

## 9. Checks

`python -m src.tab4_prep --validate` runs six checks; the build stops if any fails.

1. Every original-question estimate with a value is averaged exactly once (54 estimates).
2. Every revised-question estimate with a value is averaged exactly once (24 estimates).
3. Every survey period with an estimate has reference dates.
4. Shares are between 0 and 100%.
5. One row per window and month (primary key).
6. Reference periods end after they start.

## 10. Limits

- **Construction spending is not seasonally adjusted.** The revised window runs from November, usually a low month for construction, to August, usually a high one, which favours the build line. The three-month averages still show building ahead.
- **Construction covers all data centres,** not only AI ones, so the build line is an upper bound on AI-driven building.
- **Spending is in constant 2021 US dollars,** so the build line is not inflated by rising prices. Recent months are preliminary.
- **BTOS measures how many firms use AI, not how much.** Heavy users could be growing faster than the share of users, and the share cannot pass 100%.
- **BTOS covers US employer businesses** only, not households, government, or users abroad served from US data centres.
- **Two windows, two definitions:** each window is compared only with itself, and the revised window covers only nine months.
- **No training compute line:** Epoch AI training compute was left out because it measures building by frontier labs rather than use, and its growth would squash the other two lines flat.

The same limits are shown in the tab under **⚠️ What this comparison can and cannot tell Dana**.

## 11. AI use

Recorded in [PROVENANCE.md](PROVENANCE.md), row 10.

| What | Tool | How it was checked |
|---|---|---|
| Built the page code, the code that extracts the BTOS AI-use row and averages it by month, and the draft answer for the opening screen | Claude (Anthropic) | Recomputed the Aug 2026 indexes by hand from the source cells (132.2 and 168.4), matching the cards and the trace panel; `src.build_data --check` confirms every published estimate is averaged exactly once (54 and 24) |
