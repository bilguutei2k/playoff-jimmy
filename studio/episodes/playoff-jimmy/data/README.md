# Sources and coverage

Raw inputs are never edited. Each has a URL, retrieval time and SHA-256 hash
in a manifest. What remains to be done is in `../HANDOFF.md`.

| Source | Role | Manifest |
|---|---|---|
| Basketball-Reference league totals, 2011–12 to 2025–26 (one page per season, holding both the regular-season and playoff tables) | Analysis source for subjects and peers | `bbref-manifest.json` |
| Basketball-Reference game logs: Butler and Murray, every season in which they appear in the playoff totals | Variability reference, 2022–23 series, minutes to the second | `bbref-manifest.json` |
| 2023/24 Miami HEAT media guide, PDF page 66 (printed 65): Butler through 2022–23 | Independent check | `media-guide-manifest.json` |
| 2025/26 Denver Nuggets media guide, PDF page 57 (printed 58): Murray through 2024–25 | Independent check | `media-guide-manifest.json` |

The Basketball-Reference snapshot was taken on 2026-09-29 UTC (September 28
Pacific), after the analysis rules were committed. Pages are stored
gzip-compressed under `raw/bbref/`; each manifest hash is of the
uncompressed page exactly as received. Game-log seasons were chosen from
the data: Butler 2011–12 to 2014–15, 2016–17 to 2022–23 and 2024–25; Murray
2018–19, 2019–20 and 2022–23 to 2025–26.

The media-guide tables were rendered and visually inspected (`qa/`). Their
whole-minute totals limit rate precision; the game logs record minutes and
seconds. Butler's printed career playoff minutes (4,512) exceed the sum of
his season rows (4,511); the gap is in the source and is immaterial.

Earlier access attempts (the stats.nba.com API timed out; nba.com player pages
lacked historical totals) are preserved in `probes/` and recorded in
`../STATE.json`.

## Reproduce

```sh
# Snapshot (network; one request every 7 seconds; never refetches saved pages)
python3 studio/episodes/playoff-jimmy/analysis/fetch_bbref.py totals
python3 studio/episodes/playoff-jimmy/analysis/fetch_bbref.py gamelogs

# Media-guide text and previews (needs pypdfium2, available in the Codex
# bundled Python: ~/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3)
python3 studio/episodes/playoff-jimmy/analysis/extract_guides.py
```

Different PDF extraction versions may change whitespace; do not bypass a text
hash mismatch without comparing the source page and reviewing the extraction.
A missing season is never evidence of zero participation.
