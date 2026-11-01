# Data and AI Disclosure Statement

## Data

- **All data is public and citable.** Sources: US Census Bureau, *Value of Construction Put in Place* and *Business Trends and Outlook Survey*; US Bureau of Labor Statistics producer price indexes; IEA, *Energy and AI*; Ember, *Yearly Electricity Data*; both via Our World in Data; and Epoch AI, *AI data centers*. Full sources, URLs and licences are in [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md).
- **Licences are respected.** Our World in Data, Ember and Epoch AI data are used under CC BY 4.0 with attribution on screen; IEA data under its terms of use with attribution; US government data is public domain.
- **No personal data** is used. Every dataset is aggregate (national, regional or per facility).
- **Raw files are unchanged.** Raw downloads are kept as published. Every change from raw file to displayed number is in code (`src/`), documented in the data dictionary, and reproducible with `python -m src.build_data --check`.
- **Limits are stated in the app.** Each tab says what its data cannot show, including that construction spending and electricity shares cover all data centres, not only AI ones; that construction spending excludes servers; that two years of electricity shares and a period of survey data are missing; and that projections are not forecasts.
- **Data last refreshed:** files downloaded 23 to 25 October 2026. Latest observations: construction spending August 2026; business AI use survey period ending 4 October 2026; electricity 2025; Epoch AI release of 19 October 2026.

## AI

- **Tools used:** Claude (Anthropic) was used by members of the group, as recorded in [`PROVENANCE.md`](PROVENANCE.md). *Szexuan and Aaron: add the tools you used, or state that you used none.*
- **What AI was used for:** drafting code for tab pages, data preparation and checks; checking facts about the data; drafting documentation. Each use is a row in the provenance matrix, with what was asked and what came back.
- **How AI output was checked:** every use names a check that could have failed, such as recomputing a displayed number by hand from the source file, a byte-for-byte rebuild of the processed files, a test that the data dictionary covers every file and column, and a colour vision deficiency simulation. Outputs that failed a check were corrected before use.
- **What AI was not used for:** AI did not generate, alter or invent any data. Every number in the app comes from the public sources above and can be traced to its source file on screen.
- **Responsibility:** the group reviewed all AI-assisted work and takes responsibility for the app, the analysis and the conclusions.

Each member confirms this statement by adding their name:

- Sanika Wankhade
- Erkebai (Eric) Bakhavadinov
- Szexuan Yap
- Aaron Sapkota
