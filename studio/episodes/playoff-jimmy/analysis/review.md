# Methods and plan reviews

## Review 1 — 2026-09-28, Claude (Opus 5.5): pilot and plan

Scope: plan documents, pilot analysis and tests, source extraction and the
nightshift code. Method: a separately written parser for both guide tables,
reconciliation with the printed totals rows, recomputation of every published
value, a clean-copy rerun, and bounded watchdog tests in a scratch directory.

Checks that passed:

- All 39 rows and every published change match the independent parse exactly.
- Printed totals rows reconcile for games, minutes, points, FGA, FTA, assists
  and turnovers in all four tables, except Butler's playoff minutes: seasons
  sum to 4,511 while the guide prints 4,512. The gap is in the source and is
  immaterial.
- Per-game columns and the points identity hold on every row.
- A clean-copy rerun reproduced all four outputs byte for byte.
- Worst-case minute rounding (±0.5 per game) keeps Butler's 2022–23 playoff
  points per 36 within 24.08–24.70.

Findings and disposition:

| # | Finding | Disposition |
|---|---|---|
| 1 | No benchmark, so a near-zero per-minute change cannot be called "real" or "myth". | User decided: add a peer benchmark; rules in `METHOD.md`. |
| 2 | Conclusions depend on the season set: Murray is +2.14 per 36 in the shared seasons but +0.24 across all his runs. The pilot also dropped Butler's 2011–15 runs. | Three season sets pre-registered; Butler's full career in scope. |
| 3 | The harness is off the critical path: quiet work is killed, session-escaping children survive, killing the watchdog orphans the agent, several settings are unenforced. | User decided: minimal runner, overnight runs only when needed. |
| 4 | The pilot lacks the summaries `METHOD.md` required and the volume/efficiency split. | PJ-03, analysis v2. |
| 5 | The noise of a single playoff run is unquantified. | Game-log variability reference pre-registered. |
| 6 | Several competing next-step lists; checks recorded without evidence; coverage hardcoded. | Consolidated into `HANDOFF.md` and `STATE.json`; coverage to be computed in PJ-02/PJ-03. |
| 7 | Extraction tests pin only 4 of 39 rows. | Totals-row checks and guide-to-BBRef reconciliation in PJ-02/PJ-03. |
| 8 | No render path yet (ffmpeg absent); visual examples pending. | PJ-05 and PJ-07; installing ffmpeg needs user approval. |

Amendment made while writing the pre-registration: the proposed 200-minute
playoff threshold would have silently dropped two of Butler's weakest runs
(2017–18, 170 minutes; 2020–21, 154 minutes). The primary threshold is
therefore 100 minutes, with 200 as a sensitivity check.

Pilot values (media-guide data) that analysis v2 must reproduce when run on
the guide rows:

- Butler 2016–17 to 2022–23: 2,031 actual versus 2,062.2 expected playoff
  points, −31.2 points, −0.34 per 36 over 3,293 playoff minutes. All guide
  seasons: −27.1 points, −0.22 per 36.
- Murray 2018–19 to 2024–25: +20.9 points, +0.24 per 36 over 3,100 minutes.
- Shared seasons (2018–19, 2019–20, 2022–23): Butler −17.4 (−0.30 per 36),
  Murray +122.5 (+2.14 per 36).
- Butler 2022–23: 22.9 to 26.9 points per game, split into +4.31 from minutes
  and −0.31 from rate; TSA per 36 19.1 to 21.6; TS .647 to .565.

These are descriptive pilot values, not verified claims. BBRef values may
differ slightly; differences are reconciled, not forced to match.

## Review 2 — pending

Methods gate after analysis v2 and the results packet (PJ-04).
