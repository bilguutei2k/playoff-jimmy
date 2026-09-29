# Playoff Jimmy — current handoff

## What exists

- Reusable workflow, episode templates and a working episode creation/status CLI.
- A question, methods specification and ordered episode task queue.
- Recorded API and webpage access failures/limitations.
- Two official media-guide snapshots with provenance and visually audited tables.
- A dependency-free analysis of 39 source rows and 12 positive-exposure paired
  player-seasons, plus coverage and arithmetic QA reports.
- Seven passing regression checks, including zero exposure, duplicate records,
  source-column mapping and the minutes/rate arithmetic decomposition.

## Read first

1. `EPISODE.md` — what the project is trying to establish.
2. `analysis/coverage.json` — the source gaps that constrain the pilot.
3. `analysis/FINDINGS.md` — the current descriptive results.
4. `STATE.json` — task dependencies and the next available task.

## Next executable work

Continue PJ-02: locate official source totals for the missing later seasons,
then acquire 2023 game-level records for the round-by-round case study. Preserve
all existing snapshots. Do not keep retrying the same timed-out API without
new evidence. If coverage cannot be completed, document a narrower supported
scope before writing a broader conclusion.

PJ-03 has a working pilot but still needs complete coverage and the additional
specified analysis views. PJ-04, independent review, remains pending. The
attempted live Claude review was rejected by automatic approval review before
execution because it would transmit the local methods, code, results and source
extracts to Anthropic. Obtain the user's specific authorization for that
payload before retrying; do not route around the rejection.

Visual design can proceed when the user's examples arrive. Final audience,
language and narration are still open; they do not block source acquisition.

## Commands

```sh
python3 -m nightshift.episodes status playoff-jimmy
python3 studio/episodes/playoff-jimmy/analysis/analyze.py
python3 -m unittest discover -s tests -v
```

## Current completion limits

The workflow and research pilot are usable. The full scope is not yet covered;
no complete script, rendered video, portrait export or companion site is claimed.
The overnight supervisor is not ready to launch. Its initial process/state
scaffolding still needs agent adapters, orchestration, limits, checkout handling,
recovery tests and a successful live rehearsal.
