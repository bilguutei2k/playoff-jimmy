# Is Playoff Jimmy real? — methods

Status: pre-analysis working specification. Calculations and source coverage
must be validated before any substantive result is called verified.

## Definitions

The main observation is a player-season with recorded positive minutes in both
regular season and playoffs. Use totals from the full corresponding regular
season and full postseason. Proposed window: 2016–17 through 2025–26. Do not
include preseason or play-in games in postseason totals. Explain NBA Cup
classification if it affects source coverage.

The primary descriptive comparison is playoff minus regular-season points per
36. Per-game scoring and efficiency are complementary endpoints. No composite
score or global "best riser" title is specified.

## Data contract

Required season totals: player ID, player name, season, season type, games,
minutes, points, field-goal attempts, free-throw attempts. Field goals made,
three-point makes and free-throw makes allow an independent points identity
check. Assists, turnovers, team and opponent/series identifiers extend context.

Preserve source totals and units. Minutes may be decimal or a minutes:seconds
string; record conversion and source precision. Missing counts are not zeros.
When a traded player has both aggregate and team-stint rows, use the verified
aggregate once, or reconcile and sum the stints once. Never add both.

Each raw input has a URL, retrieval timestamp, SHA-256, source schema and
coverage description. Save source failures and missing periods in the coverage
report. Keep raw bytes immutable; transformations write separate outputs.

For round-level work, require game ID, player ID, date, season type, team,
opponent, minutes, points and a supported series/round mapping. Enforce a unique
player-game key. Do not infer a career-wide pattern from season totals that
were selected because their results looked interesting.

## Analysis

For each player-season/type, compute from totals:

- Points per game = points / games.
- Minutes per game = minutes / games.
- Points per 36 = 36 × points / minutes.
- Approximate true shooting = points / [2 × (FGA + 0.44 × FTA)].

Treat the 0.44 free-throw coefficient as an approximation; check the actual
source definition before asserting agreement with a provider's displayed TS%.
Return an undefined result for a zero denominator rather than inventing zero.

Define `m = minutes/games` and `r = points/minutes`. The per-game difference
can be decomposed exactly as:

`PPG_playoffs - PPG_regular = mean(r) * change(m) + mean(m) * change(r)`

This symmetric arithmetic decomposition associates one part with minutes and
one with scoring rate. It is not a causal estimate of what would happen if a
coach changed minutes. Verify the identity against full-precision totals.

Show all paired seasons and exposure, including short runs. For multi-season
summaries, report the number of pairs; show equal-season summaries separately
from pooled-exposure summaries. Repeat a clearly labeled sensitivity view with
minimum postseason games of 5 and 10. Retain the full table so the filters
cannot hide an inconvenient result. Identify common paired seasons when
directly comparing players; differences in their postseason selection matter.

For 2022–23, compare Butler's round-level rates with the complete postseason
only if game-level coverage and round mapping are verified. Treat a single
series as a descriptive case study, not an independent replication.

Do not manufacture uncertainty intervals from aggregate rates alone. If adding
game-level bootstrap or hierarchical estimates, specify the sampling unit and
dependence assumptions, check their suitability for few series, and distinguish
sampling uncertainty from sensitivity to analytic choices. League-wide ranks
and predictive modeling are later extensions requiring a declared cohort and
validation; they are not required to answer this first episode's question.

## Verification

Required checks:

1. Snapshot hashes, schema and coverage; unique keys; nonnegative counts;
   shooting makes no greater than attempts; no duplicated aggregate/stint rows.
2. Reconcile selected player-season totals with an independent primary source,
   preferably the team media guide or published season totals.
3. Recompute all rates from totals and check the per-game decomposition.
4. Exercise missing/zero exposure, traded-player rows and short playoff runs.
5. Produce the complete table before selecting the story's examples.
6. A partner review checks exclusions, arithmetic, causal language and whether
   the narrative overstates the endpoint. Record objections and resolutions.
7. A fresh analysis run reproduces result content using the frozen raw inputs.

Execution commands and outputs must be recorded in `STATE.json` and the
analysis QA report once they exist. Planned checks are not passing checks.

## Limits

Playoff selection, opponent quality, health, team role and changing workloads
are not controlled by dividing by minutes. Scoring is not total player impact.
The chosen window is not both players' entire careers. An observed difference
is not proof of a psychological transformation or a repeatable causal effect.
Numbers from prior prose research remain unverified until inputs are checked.
