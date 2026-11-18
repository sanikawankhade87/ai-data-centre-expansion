# Tab 2 · Builders and Locations

| | |
|---|---|
| **Owner** | Erkebai (Eric) Bakhavadinov |
| **Sub-question** | Is AI data centre capacity concentrated in a few organisations or countries? |
| **Persona** | Dana Reyes, energy policy analyst advising a US state public utilities commission (the group persona, see [README.md](README.md)) |
| **Short answer for Dana** | Yes. The top 5 owners hold 71% of the operational AI data centre power Epoch AI tracks, so each grid request is a bet on a few companies' plans |
| **Charts** | Ranked horizontal bar chart (ranking) |

## 1. Files

| File | Purpose |
|---|---|
| `tab2_builders.py` | The tab. `app.py` imports it and calls `render()` inside the second tab |
| `src/tab2_prep.py` | Every transformation, in commented steps, plus six checks that can fail |
| `scripts/download_epoch.py` | Saves the Epoch AI file to `data/raw/` unedited |
| `data/raw/data_centers.csv` | Raw download, never edited (shared with Tab 3) |
| `data/sample/tab2_sites.csv` | Source sample: the five columns Tab 2 uses, values unchanged |
| `data/processed/tab2_sites_clean.csv`, `tab2_owner_share.csv`, `tab2_country_share.csv` | The files the tab reads |

## 2. Run it

```bash
pip install -r requirements.txt
python scripts/download_epoch.py      # saves data/raw/data_centers.csv, unedited
python -m src.tab2_prep               # raw file -> sample -> processed files, then the checks
python -m src.tab2_prep --from-sample # rebuild the processed files from the sample only
python -m src.tab2_prep --validate    # checks only
streamlit run app.py                  # Tab 2 is the second tab
```

## 3. Data

| Item | Detail |
|---|---|
| Source | Epoch AI, *AI data centers*, site list |
| URL | https://epoch.ai/data/data_centers/data_centers.csv |
| Licence | CC BY 4.0 |
| Columns used | `Name`; `Owner`; `Country`; `Current power (MW)`; `Current total capital cost (2025 USD billions)` |
| Primary key | Name (95 sites) |
| Time coverage | Snapshot |
| Latest observation | Epoch AI release of 19 Oct 2026 |
| Downloaded | 24 Oct 2026 |

- `Current power (MW)` is **IT power**, the power drawn by servers, networking and storage. It excludes cooling, so a site's grid draw is higher.
- `Owner` means the **owner of the AI chips**, not the building. Epoch tags each owner `#confident`, `#likely` or `#speculative`; the tab strips the tag for grouping and reports the counts in **Source and method**.
- Blank owners are grouped as **Owner not disclosed**. That group is never counted as one company in the top-N headline.
- Sites at 0 MW are announced or under construction. They are counted as "not yet drawing power" but add nothing to the shares.

Processed files: `tab2_sites_clean.csv` (one row per site, tag removed, `owner_confidence`, `operational`); `tab2_owner_share.csv` and `tab2_country_share.csv` (`power_mw`, `sites`, `share_pct`, `cumulative_pct`). Full column detail is in [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md).

## 4. Transformations

All steps are in `src/tab2_prep.py`. No rows are dropped and no values are imputed.

| Step | What it does |
|---|---|
| 0 | Keep the five columns the tab uses, values unchanged → sample |
| 1 | Read the sample |
| 2 | Strip Epoch's confidence tags from `Owner` (`Meta #confident` → `Meta`); blank owners become *Owner not disclosed* → `tab2_sites_clean.csv` |
| 3 | Group by Owner or Country, sum power (MW), share = group MW ÷ total MW × 100 → `tab2_owner_share.csv`, `tab2_country_share.csv` |
| 4 | Headline = sum of the top N named groups' MW ÷ total MW × 100 (computed live for the slider) |

| Card | Formula | Value |
|---|---|---|
| Share of operational power held by the top 5 owners | Top 5 named owners' MW ÷ total MW × 100 | 71% |
| Operational AI data centre power tracked | Sum of `Current power (MW)` | 14,203 MW |
| Sites announced but not yet drawing power | Sites at 0 MW | 21 of 95 |

## 5. Charts and design decisions

| Chart | Visual task | Why this form | Alternative rejected |
|---|---|---|---|
| Ranked horizontal bar chart of each group's % of total power; the top N in blue, the rest grey, undisclosed owners hatched | Rank owners (or countries) and show how much of the whole the leaders hold | Bars on a shared baseline are judged far more accurately than angles, and horizontal bars fit long owner names without rotating the text | A pie or donut chart: with more than 20 owners, most slices are 1–5%, so Meta (15.8%) and Amazon (13.2%) would look the same, and an "Other" slice would hide the tail this tab is about. For countries, a choropleth map was also rejected: the US holds over 80% of the power, so the map shows one dark country, and map area misleads (Malaysia ranks second but is tiny on a world map) |

Every bar is labelled with its value, and the axis gives the unit (share of current AI data centre IT power, %).

## 6. Interaction

- **Group by** toggle: switch between Owner and Country.
- **Highlight the top N owners** slider: moves the highlight and recomputes the headline, so Dana can see how few owners it takes to pass 50%.
- **Hover:** shows each group's MW and number of sites.

## 7. What it shows for Dana

Power is concentrated by builder: the top 5 owners hold 71% of the operational power Epoch tracks. The pipeline is where the change could come: of the 21 sites not yet drawing power, 7 belong to today's top 5 owners, and the largest pipeline owner is Oracle (4 sites). If those sites come online, the ranking can shift, but each one is still a single large grid request.

## 8. Trace a number

1. Open `data/raw/data_centers.csv` and filter `Owner` to the top 5 names shown in blue.
2. Sum `Current power (MW)` for those rows.
3. Divide by the column total (14,203 MW) and multiply by 100: **71%**, the headline card.
4. The **Source and method** section in the tab shows the same rows and the same division on screen.

## 9. Checks

`python -m src.tab2_prep --validate` runs six checks; the build stops if any fails.

1. No site is dropped between the sample and the processed file (95 rows).
2. Site names are unique (primary key).
3. No confidence tag is left in Owner.
4. No negative power values.
5. Owner shares add up to 100% and to the total MW.
6. Country shares add up to 100% and to the total MW.

## 10. Limits

- **Frontier AI sites only:** Epoch tracks 95 major AI sites, not every data centre, so this shows concentration at the frontier, not in the whole industry. Tab 1 covers total construction.
- **IT power excludes cooling,** so each site's draw on the grid is higher than shown.
- **Owner means the chip owner,** which can differ from the building owner.
- **Announced sites may change:** sites not yet drawing power may be delayed or cancelled.
- **Tab 3 uses whole-facility power** (`Power (MW)`, including cooling), so the two tabs show different MW for the same site.

## 11. AI use

Recorded in [PROVENANCE.md](PROVENANCE.md), row 8.

| What | Tool | How it was checked |
|---|---|---|
| Drafted the page code and the prep module | Claude (Anthropic) | Recomputed the headline % by hand from the raw CSV in Excel; confirmed the row count (95) and that tag stripping left no `#` in Owner |
