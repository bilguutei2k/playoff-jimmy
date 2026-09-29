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

## Checks made while building analysis v2 (2026-09-28, Claude)

Not the PJ-04 review, which still needs to happen with the user.

- A separately written quick parse of the season pages re-derived peer count,
  peer median and percentile exactly for Butler 2018–19 (a traded season),
  2021–22 and 2022–23, and Murray 2019–20.
- Pilot values above reproduce exactly on the guide rows (tested).
- Post-result clarifications and their effect are listed in `METHOD.md`
  under Amendments; none changes a rule outcome.

## Review 2 — 2026-09-28, Claude (Opus 5.5): methods gate on analysis v2 (PJ-04)

Limitation of this review: Claude built analysis v2, so this is an adversarial
self-review, not an independent one. Mitigation: every claim value is
recomputed from the raw pages by separately written code
(`verify_claims.py`, which imports neither `bbref.py` nor `analyze.py`), and
the verifier was mutation-tested (a misstated value, a corrupted result and a
wrong wording are each caught). Optional before publication: have Codex
re-derive the claim values from the snapshot with its own code.

| # | Objection | Resolution |
|---|---|---|
| 1 | The pre-registered rule is met for Butler, but it gates wording; it does not test strength. 8 of 11 runs above the peer median would happen by chance 11% of the time; his mean percentile is 56. | Kept as a limitation on PJ-C005. Exploratory check added and labeled (METHOD.md amendment 4). Wording: "holds his scoring rate better than most", never "scores more in the playoffs" or "clutch". |
| 2 | "Better than typical" needs a population: how unusual is his career? | Exploratory career edge: 7th of 29 players with 8+ eligible runs; 12th of 64 with 6+ (Murray 8th). PJ-C006, labeled exploratory, with the cutoff sensitivity stated. |
| 3 | The per-game "Playoff Jimmy" jump and the per-minute result are different claims. | Kept separate: PJ-C002/C003 (per game, mostly minutes) and PJ-C004/C005 (per minute, against peers). |
| 4 | Murray has the higher pooled change in every season set but fails the majority condition. Which "rises more"? | Both stated with scope (PJ-C010, PJ-C011): higher on average is not more consistent. No blanket "who rises more" line. |
| 5 | Butler's two worst runs are 4 and 5 games. | Stated in PJ-C008. At the 200-minute threshold both drop out and the rule is still met. |
| 6 | 2022–23 regular-season efficiency was his best, so the playoff comparison starts high. | Limitation on PJ-C004. |
| 7 | Opponents, pace, fatigue and role are not controlled. | The peer benchmark compares like with like on average (same seasons, same phase); stated as a general limit. No causal wording. |
| 8 | Could the rounded-PPG reading or band edges change results? | Measured in METHOD.md amendments 2–3: no rule outcome changes. |

Outcome: 11 claims proposed in `CLAIMS.json`; all pass `verify_claims.py`
(`analysis/claims_check.json`). They stay `proposed` until the user approves
them, per the autonomy boundary in `docs/decisions.md`.

## Review 3 — 2026-09-28: external review of script draft v1

Source: an outside review the user pasted into the session. Two of its points
were testable against the data and were tested before acting.

| Point | Test or decision | Disposition |
|---|---|---|
| The benchmark mixes stars and role players; rerun against similar scorers. | Peer set B (20+ points per game) already existed and passed. The better design, matching on regular-season scoring rate, was added as METHOD.md amendment 5. | Accepted. Average edge grows (2.08 vs 1.70); runs above median fall to 6 of 11 (Murray rises to 5 of 6). New claims PJ-C012 and PJ-C013; PJ-C005, PJ-C006 and PJ-C011 limitations revised. Lock v2. |
| Holding rate over more minutes "usually costs something"; add a line. | Across 1,325 eligible player-seasons, players whose minutes rose 6+ a game declined least (median −1.1 per 36) and those whose minutes fell declined most (−2.2); slope +0.09 per extra minute, r = 0.14. Descriptive, probably coaches giving minutes to players who are playing well. | Rejected: the data does not support the assumption. No line added. |
| No efficiency; scope it. | Scope line added to S02. A true-shooting beat would need a new claim. | Accepted (scope line). |
| "The rule we wrote down" is unverifiable on screen. | The rules were committed (2827174) before the snapshot (de8233c); git records the order. | Accepted: show the rule and its commit date on screen. |
| Script errors: "barely got taller"; "stays the same size"; nickname origin implied; Short B benchmark; Short D mixes per-game and per-36; Short A "4.3 of 4.0". | Checked against the claims. | All accepted; fixed in draft v2. |
| S06 overloaded; S07 buries the twist; S08 overclaims; number density; one precision level; one voice; clichés; hold Short C; Short B needs its caveat. | Editorial. | All accepted in draft v2. Short C held. |

## Review 4 — 2026-09-29, Astra (Codex): final review of script v2 before production

Source: `codex exec --sandbox read-only` (reasoning effort high) over STORY.md,
CLAIMS.json, results.json, METHOD.md, review.md, DIRECTION.md and the scene
pages, at the user's request. It was told the numbers had already been
re-derived (PJ-09) and not to recompute them. Verdict: "ship with
amendments"; no number was wrong. Every point was checked against the claims
and METHOD.md before acting.

| Point | Check | Disposition |
|---|---|---|
| S08 "His points per game rise because his minutes do" is general and causal. | PJ-C003 is a descriptive split of 2022–23 only. | Accepted: "In 2022–23, the extra minutes account for his whole rise in points per game." |
| Short A title "He didn't score more. He played more." is false; its rectangle says "+4.3 MIN" and "−0.3 RATE". | He scored 4.0 more per game; +4.3 and −0.3 are points per game, and his minutes rose 6.3. | Accepted: title "He didn't score faster. He played longer."; labels say PTS/G. |
| S05 presents the similar-scorer comparison as if it were part of the advance test. | METHOD.md amendments 4 and 5: exploratory, "labeled as such wherever used". | Accepted: narration says it was added after seeing the results; S05 and S08 label it "added later". The chip "Passes" stays (the narration names the advance test as it lands). |
| "His 11 playoff runs" and "his two worst runs" drop the eligibility scope. | Butler's 2011–12 run is outside the cutoffs (PJ-C005, PJ-C008). | Accepted: "11 playoff runs with real minutes", "of those 11", "11 qualifying runs" (Short B, on screen with years). |
| S07 does not say what the percentiles rank. | They rank the change in scoring rate; the 17-game comparison is about the playoff rate (PJ-C004, PJ-C007). | Accepted, in shorter words than proposed; label "Percentile of the change". |
| "Coin flip" should become "close to half" and be scoped to similar scorers. | PJ-C013's verified text says "close to a coin flip", and it holds only against similar scorers (8 of 11 against everyone). | Scope accepted (S06, S08, Short B say "against similar scorers"); "close to a coin flip" kept as verified. |
| Short D "then a normal run" and "matched his regular season". | No claim calls the later series normal; 24.7 → 24.4 per 36 is a small drop. | Accepted: dropped; "barely changed", "nearly matched". |
| Explain per 36 minutes in S03, Short A and Short B. | Clarity. | Accepted for S03 and Short A ("Scale ... to the same 36 minutes"); Short B keeps its unit on screen. |
| S04 "1,325 player-seasons" and "shrink less than everyone else". | PJ-C005 compares with the typical peer. | Accepted. |
| S02/S03 headline "He scores more in the playoffs"; title caption. | The wording rules forbid the unqualified phrase. | Accepted: "He scores more per game"; "More points when it counts. Or just more minutes?" |
| S04b does not say every version must pass. | METHOD.md "Peer benchmark". | Accepted: "Every version must pass: against all players and against 20-point scorers, at 100 and at 200 playoff minutes." |
| TTS spoken forms. | — | Applied in `studio/tools/narrate.py` (seasons as "twenty twenty-two to twenty-three"; decimals, ordinals and counts spelled out). |

The full list of script changes is in STORY.md, "Changes after the lock".

### Presentation fixes from the statistical audit (2026-09-29)

A statistical audit written to `analysis/audit/` this morning by another
session (untracked when this was written; `AUDIT.md`) re-derived all 82
claim values (all agree) and raised two chart problems, both confirmed in the
scene code and fixed before the first narrated draft:

- S05 pinned 11 peer values to the plot edges (the axis ran −10 to +6; the
  values run about −14.4 to +9.4). The axis now spans every value shown.
- S07 drew the 5th–95th percentile band under "every 17-game stretch". It now
  adds whiskers over the full range of all 41 stretches and a key (line: all,
  band: middle 90%, dark: middle half).

Its other notes need no change now: S03's widen-then-lower animation is
schematic (both decompositions round to +4.3 / −0.3); −0.25 is weighted by
playoff minutes (S05's source line says so); "6 of 11" is an observed count,
not a probability model (the script says only "close to a coin flip").
