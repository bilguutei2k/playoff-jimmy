# Sources and coverage

The live `stats.nba.com` API timed out on two bounded requests. The official
player pages were reachable, but their embedded recent-game records did not
provide the required historical totals. Both attempts are preserved in `probes/`.

The current pilot uses downloaded official team media guides. Source URLs,
retrieval timestamps, sizes and SHA-256 hashes are in `media-guide-manifest.json`.

| Source | Relevant table | Coverage in that table |
|---|---|---|
| 2023/24 Miami HEAT media guide | PDF page 66, printed page 65 | Butler through 2022–23 |
| 2025/26 Denver Nuggets media guide | PDF page 57, printed page 58 | Murray through 2024–25 |

These tables were rendered and visually inspected to confirm column alignment
and the source text. Their whole-minute totals limit the precision of derived
rates. Text extraction is retained only for the relevant pages. Source PDFs
and raw snapshots remain unchanged.

Reproduce the pilot from the operator repository:

```sh
python3 studio/episodes/playoff-jimmy/analysis/analyze.py
python3 -m unittest discover -s tests -v
```

The numerical script has no third-party dependencies. To reproduce PDF text
extraction and previews, use Python with `pypdfium2`:

```sh
python3 studio/episodes/playoff-jimmy/analysis/extract_guides.py
```

The Codex bundled Python on this machine has that dependency:
`/Users/bilguutei/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`.
Different PDF extraction versions may change whitespace; do not bypass a text
hash mismatch without comparing the source page and reviewing the new extraction.

## What remains

- Acquire Butler's 2023–24, 2024–25 and 2025–26 totals, and Murray's 2025–26
  totals, or explicitly revise the research scope before a final conclusion.
- Add game-level coverage and verified playoff-round mapping for the 2023
  case study.
- Independently reconcile selected source totals and complete the methods review.
- A missing season in the current source is not evidence of zero participation.

There is no approved final episode claim yet. `analysis/qa.json` reports passing
arithmetic checks while retaining failed/full-coverage and pending-review status.
