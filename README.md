# Is Playoff Jimmy real?

The data, code and checks behind the video. Every number in it comes from
`analysis/results.json` through a verified claim, and every step that produced
those numbers is here.

**Companion page:** https://bilguutei2k.github.io/playoff-jimmy/

## The short version

Jimmy Butler's points per game rose from 22.9 to 26.9 in the 2022–23 playoffs,
and his extra minutes account for all of that rise; per 36 minutes his scoring
barely moved (24.7 to 24.4). Most
players score less per minute in the playoffs; across his 11 runs with real
minutes Butler fell by 0.25 points per 36, where players in the same seasons
typically fell by 1.7. Against similar scorers he was ahead in 6 of 11 runs.

## Where things are

All paths are under `studio/episodes/playoff-jimmy/`.

| What | File |
|---|---|
| The question, the measures and the pass-or-fail test, written before any league data | `METHOD.md` |
| The 13 claims the video may make, each tied to a result key, input hashes and checks | `CLAIMS.json` |
| The analysis and its outputs | `analysis/analyze.py`, `analysis/results.json`, `analysis/qa.json` |
| Claim verification (independent recomputation of every claim value) | `analysis/verify_claims.py`, `analysis/claims_check.json` |
| Methods and script reviews, and what changed because of them | `analysis/review.md` |
| A blind re-derivation of all 82 claim values from the raw data (82 of 82 matched) | `analysis/recheck_report.json`, `recheck/` |
| An extended statistical audit | `analysis/audit/AUDIT.md` |
| The script, with every numbered line citing a claim | `STORY.md` |
| The animated scenes (they read numbers only from `scenes/data.js`, built from the results) | `scenes/` |
| The edit: which words start each animation | `EDIT.json` |
| The companion page | `companion/` |

The renderer is in `studio/render/`, and the narration, assembly and script
checks are in `studio/tools/`.

## Written down before the data

Commit `1ea694c` (2026-09-28) fixed `METHOD.md`, including the rule for when
the video may call Playoff Jimmy real, before commit `eedac44` saved any league
data. Later clarifications are listed, with their effects, under "Amendments"
in `METHOD.md`; comparisons added after the results (such as similar scorers)
are labelled exploratory wherever they appear.

## Data

Season totals and game logs come from
[Basketball-Reference](https://www.basketball-reference.com). The 33 saved
pages are **not redistributed** here: Sports Reference does not allow copies
of its pages to be republished. `data/bbref-manifest.json` lists each page's
address, retrieval time and SHA-256, and the numbers derived from them are in
`analysis/results.json`, cited to Basketball-Reference. The Miami Heat 2023–24
and Denver Nuggets 2025–26 media guides served as an independent check
(`data/media-guide-manifest.json`) and are not redistributed either.

To rerun the analysis, save the listed pages to the paths in the manifest.
The analysis checks every file against its SHA-256 and reports a mismatch, so
pages that have changed since the snapshot will be flagged.

## Running the checks

```sh
python3 -B -m unittest discover -s tests -v
python3 studio/tools/story_check.py studio/episodes/playoff-jimmy
```

Tests that need the saved pages are skipped without them. Rendering needs Node
and a headless Chromium; narration needs Apple Silicon and
`studio/tools/requirements-voice.txt`.

## About this history

This repository's history was filtered from the working repository to remove
third-party files; the commits, their order and their dates are otherwise
unchanged, so their hashes differ from any quoted elsewhere before
publication.

Code is under the MIT license (`LICENSE`). Statistics are facts from
Basketball-Reference, credited to it.
