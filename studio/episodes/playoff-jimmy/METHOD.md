# Is Playoff Jimmy real? — methods

Status: pre-registered specification, committed on 2026-09-28 before any
Basketball-Reference or peer data was downloaded. Later changes go under
"Amendments" with a reason, and are never made because a result looked more
or less attractive.

## Question

Does Jimmy Butler score more in the playoffs than in the same season's regular
season? How much of any change comes from playing time rather than scoring
rate? Is his per-minute change unusual compared with other high-minute players
in the same seasons? Jamal Murray is a named comparison, not the benchmark.

Per game and per minute are separate questions. A per-game rise that comes
from extra minutes is reported as such; it is not evidence of a different
scoring rate.

## Scope and sources

- Butler: every season from 2011–12 through 2025–26 with positive minutes in
  both the regular season and the playoffs.
- Murray: every such season from 2016–17 through 2025–26.
- Peers: all players in the same seasons.
- Analysis source: Basketball-Reference (BBRef) season totals (regular season
  and playoffs) and player game logs, so subjects and peers share one set of
  definitions. Pages are snapshotted once with hashes; analysis never fetches.
- Independent check: every official media-guide row (Butler 2011–12 to
  2022–23, Murray 2016–17 to 2024–25) is reconciled against BBRef. Counts must
  match exactly and minutes within ±1. Other discrepancies are listed and
  resolved before results are used; neither source is edited.
- Play-in and preseason games are excluded. For a traded player, use the
  season aggregate row once (BBRef "TOT", "2TM" or "3TM"), never also the
  team rows.
- Every player-season in scope gets an exposure class: paired; team missed the
  playoffs; player on a playoff team with 0 playoff games; not in source. Only
  paired seasons enter rates. Missing is never zero.

## Measures

For a player-season, with r = regular-season points / regular-season minutes:

- Expected playoff points E = playoff minutes × r.
- Excess = actual playoff points − E.
- Excess per 36 = 36 × excess / playoff minutes. For one season this equals
  the change in points per 36. Across seasons, 36 × Σ excess / Σ playoff
  minutes is the playoff-minute-weighted change; always report Σ minutes and
  the number of seasons beside it.
- Points per game, minutes per game, and the exact decomposition of the
  per-game change into a minutes part and a rate part (symmetric average
  form). Descriptive arithmetic, not a causal estimate.
- Shot volume and efficiency: points per 36 = 2 × TS × TSA per 36, where
  TSA = FGA + 0.44 × FTA. Report the change in each factor. TS uses the
  conventional 0.44 approximation and is labeled approximate.

Season sets, always reported side by side:

1. All paired seasons for each player.
2. Seasons that both Butler and Murray have paired.
3. Paired seasons with at least 100 playoff minutes.

No "who rises more" statement unless it holds in all three sets.

## Peer benchmark

- Eligible player-season: at least 1,500 regular-season minutes and at least
  100 playoff minutes. Sensitivity: at least 200 playoff minutes.
- Peer set A (primary): every eligible player in that season except the
  subject. Peer set B (sensitivity): eligible peers who averaged at least 20.0
  regular-season points per game.
- Per season, the subject's percentile is the share of peers with a lower
  excess per 36, counting ties as half.
- Career comparison: the subject's pooled excess per 36 against the peer
  median for each of his seasons, weighted by his playoff minutes; plus the
  number of his eligible seasons above that season's peer median.
- Subject seasons below the eligibility threshold stay in the full table,
  labeled; they are not removed from the season sets above.
- The same procedure applies to Butler and to Murray.

Wording, fixed in advance:

| Percentile among peers | Wording |
|---|---|
| below 25th | below typical |
| 25th to 75th | typical |
| 75th to 90th | above typical |
| 90th and above | exceptional |

The film may say Playoff Jimmy is real in the per-minute sense only if his
pooled excess per 36 is above the minute-weighted peer median and a majority
of his eligible seasons are above their season's peer median, in both peer
sets and at both playoff-minute thresholds. Otherwise it states what the
per-game and per-minute results show, without a "real" or "myth" verdict.

## Variability reference

For each subject run with k playoff games and at least 100 playoff minutes,
take every window of k consecutive regular-season games he played that
season, compute points per 36 for each window (36 × Σ points / Σ minutes),
and report where the playoff run falls in that distribution. This is a
variability reference, not a significance test: the windows overlap, and
playoff opponents and minutes differ.

Game logs must reconcile with the same source's season totals (games,
points, FGA and FTA exactly; minutes within rounding) before use.

## 2022–23 case study

Map each 2022–23 playoff game to its series by opponent. Report per-series
points per game, minutes per game and points per 36 for both players,
including the Finals in which they met. Descriptive only; one series is not a
replication.

## Verification

1. Snapshot hashes, schema and coverage; unique keys; nonnegative counts;
   makes no greater than attempts; points = 2 × FGM + 3PM + FTM; printed
   totals rows and per-game columns reconcile where a source has them.
2. Guide-to-BBRef reconciliation as specified above.
3. Rates recomputed from totals; decomposition identities hold.
4. Tests cover zero and missing exposure, traded-player aggregate rows and
   short runs.
5. Full tables exist before any example is chosen for the film.
6. A partner methods review checks exclusions, arithmetic and wording against
   these rules. Objections and resolutions go in `analysis/review.md`.
7. A fresh run reproduces the results byte for byte from the frozen snapshots.

Planned checks are not passing checks. Record commands and outcomes in
`STATE.json` and `analysis/qa.json`.

## Limits

Dividing by minutes does not control for opponents, health, role, pace or
workload. Scoring is not total player impact. The benchmark says how unusual a
change is among high-minute players; it does not explain why. An observed
difference is not proof of a psychological "clutch" trait or a repeatable
causal effect.

## Amendments

2026-09-28, during PJ-02/PJ-03. These clarifications were written after the
first results existed, so each records its effect:

1. Exposure class "no games that season" added (Murray 2021–22). The four
   pre-registered classes had no label for a season with no regular-season
   games; "not in source" would have implied a data gap. Labeling only; no
   rate changes.
2. Wording bands at the boundaries follow the table literally: 25 ≤ p ≤ 75 is
   "typical", 75 < p < 90 "above typical", p ≥ 90 "exceptional". One value
   sits exactly on a boundary (Butler, peer set B, 2014–15, 90.0).
3. Peer set B uses unrounded regular-season points per game (≥ 20.0). Two
   eligible peers average 19.95–19.99, including Murray in 2022–23. Reading
   the threshold as a rounded average would move three percentiles by at most
   2.8 points and changes no career condition or rule outcome for either
   player.
4. Exploratory analysis added during the PJ-04 review, after results existed
   and not pre-registered: (a) a coin-flip check on the count of seasons
   above the peer median, with the mean percentile; (b) a career-level edge
   (pooled per-36 change minus the minute-weighted peer median) for every
   player with at least 6, and separately 8, eligible runs, 2011–12 to
   2025–26. It is reported under `exploratory` in `results.json`, labeled as
   such wherever used, and cannot change the rule outcome above. Reason: the
   rule gates wording but does not say whether the pattern exceeds chance or
   how unusual it is among long playoff careers; both temper the headline.
5. Matched-peer check added after an external review of the script objected
   that the benchmark mixes stars and role players: each eligible run is also
   compared with eligible peers whose regular-season scoring rate was within
   3 points per 36 of the subject's (sensitivities: the 25 nearest scorers;
   shot volume within 3 attempts per 36). Exploratory, reported whichever way
   it came out, under `exploratory.matched_peers`. Outcome: Butler's average
   edge grows (similar scorers fell 2.08 per 36, against 1.70 for all peers),
   but his runs above the median fall from 8 of 11 to 6 of 11, while
   Murray's rise from 3 of 6 to 5 of 6. Which player looks more consistent
   depends on the peer group, so no consistency comparison is claimed beyond
   the counts. The rule outcome above is unchanged.
