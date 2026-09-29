# Playoff Jimmy — statistical verification

Audit date: 2026-09-29. Scope: the frozen source data, locked results and
claims, current v2 narration, and numeric data used by the scenes.

**The published calculations reproduce. All 82 distinct claim values across
13 claims agree with a separately authored, exact-rational re-derivation.
Their stated rounding is correct.** The wider audit finds one unused source
column discrepancy and two chart presentation problems. This is not an
unqualified publication approval.

The overnight recheck was authored without the original analysis/results.
This audit preserves and reruns that implementation, then extends it to the
supporting calculations and source tables. The extension is not blind: the
reviewer has seen the results. Neither implementation imports the production
analysis, parser, claim verifier or scene exporter.

## Evidence and reproduction

- [Machine-readable audit](audit_results.json): checks, failures, source
  notes, per-claim outcomes and the hashes of the audited inputs.
- [Independently recalculated claim values](rederived_claim_values.json): all
  82 unrounded values, with the original rechecker's interpretation notes.
- [Extended audit program](audit.py).
- [Preserved independent recheck](claim_rederivation.py): original source
  SHA-256 is recorded in its header; only its output destination was changed.

From the repository root:

```sh
python3 -B studio/episodes/playoff-jimmy/analysis/audit/audit.py
python3 -B -m unittest discover -s tests -p 'test_analysis*.py' -v
python3 -B studio/tools/story_check.py studio/episodes/playoff-jimmy
```

The strict audit deliberately exits **1**, because the guide's nine starts
do not match the other source's ten. It does not silently waive the mismatch.
Its report separately records `calculation_status: pass`,
`claim_values_status: pass`, and `source_reconciliation_status: discrepancy`.
The analysis test suite passed all **24 tests**; the narration's numerical
claim-reference lint also passed. The lint is not a semantic fact checker.

Only audit artifacts were created by this verification. Source snapshots,
the approved script, production analysis and scene files were not changed.

## What was checked

1. Hashes and byte lengths of **33 frozen Basketball-Reference pages**:
   15 season-total pages and 18 player game-log pages. Both official PDF
   hashes, their extracted-table hashes, the results hash and all claim
   input hashes also match.
2. **13,211 raw player rows**: nonnegative counts, made shots not exceeding
   attempts, started games not exceeding appearances, scoring identity,
   rebound identity and two-/three-point splits.
3. **1,010 combined traded-player rows**, across 20 count columns: each
   aggregate equals its team stints and is selected once.
4. The eligible league populations at both 100 and 200 playoff minutes;
   all stored primary-population scoring values; every subject-season
   measure; all four A/B benchmark versions; all matched-peer variants;
   season-set summaries; and the six-/eight-run career rankings.
5. **36 regular/playoff game-log tables** reconciled against season totals,
   including scoring, shooting, rebounds, assists, steals, blocks, turnovers
   and fouls. The largest minutes discrepancy is **0.5 minute**, within the
   whole-minute rounding of the totals source.
6. All **17 playoff-length variability comparisons**, their overlapping
   regular-season windows and reported quantiles; every 2023 series for
   both Butler and Murray; and the earlier media-guide pilot summaries.
7. **39 media-guide season rows** across four tables, including three
   zero-appearance rows. The extended comparison includes games started,
   which the earlier scoring-focused reconciliation did not check.
8. All claim values at full numerical precision and at publication precision;
   all 82 exported scene values; and the distributions, run markers,
   playoff-game counts and variability-band data used by the scenes.

The complete automated audit performs 176,475 scalar/structural checks; one
fails, the unused games-started source mismatch described below. This count
is evidence of coverage, not a confidence level or significance measure.

## Main numbers

| Claim | Independent result | Publication result |
|---|---|---|
| Butler 2023 regular-season PPG | 1,466 / 64 = 22.906250 | 22.9 — correct |
| Butler 2023 playoff PPG | 592 / 22 = 26.909091 | 26.9 — correct |
| PPG increase | 4.002841 | +4.0 — correct |
| Minutes per game | 2,138 / 64 = 33.406250; 874 / 22 = 39.727273 | 33.4 → 39.7 — correct |
| Points per 36 | 36 × 1,466 / 2,138 = 24.684752; 36 × 592 / 874 = 24.384439 | 24.7 → 24.4 — correct |
| Symmetric minutes component | +4.307882 PPG | +4.3 points — correct |
| Symmetric rate component | −0.305041 PPG | −0.3 points — correct |
| Eligible league sample | 1,325 player-seasons | Correct |
| League median change | −1.535606 points per 36 | −1.5 — correct |
| Share declining | 968 / 1,325 = 73.056604% | 73% — correct |
| Butler eligible career | 11 runs; 4,904 playoff minutes | Correct |
| Butler pooled change | −0.250167 points per 36 | −0.25 — correct |
| Same-season peer benchmark, weighted by Butler's playoff minutes | −1.704022 points per 36 | −1.70 / −1.7 — correct |
| Butler above broad peer median | 8 / 11 runs | Correct |
| Butler 2023 percentile | 70.526316 among 95 **other** players | 71st — correct rounding |
| Binomial upper tail for 8+ out of 11 fair independent trials | 232 / 2,048 = 0.11328125 | About 11% — correct under that model |
| Career ranking, at least eight eligible runs | 7th of 29 | Correct |
| Similar-scoring peer benchmark | −2.084991 points per 36 | −2.1 — correct |
| Butler above similar-scoring peer median | 6 / 11 | Correct |
| Murray above similar-scoring peer median | 5 / 6 | Correct |
| Murray above broad peer median | 3 / 6 | Correct |

The symmetric decomposition used in the analysis is:

```text
minutes contribution = (playoff MPG − regular MPG)
                       × (playoff points/min + regular points/min) / 2

rate contribution    = (playoff points/min − regular points/min)
                       × (playoff MPG + regular MPG) / 2

4.307881590 − 0.305040681 = 4.002840909 PPG
```

These are arithmetic components, not estimates of what extra playing time
causes. The increase in **minutes** is 6.321023 per game; +4.3 is a number of
**points per game**, not minutes.

### 2021–22 and the rolling-window check

- Whole-minute season totals give **22.726049 → 26.670906** points per 36,
  rounding correctly to **22.7 → 26.7**. The unrounded increase is
  **3.944858**, which rounds to **+3.9**, not +4.0; subtracting the rounded
  endpoints creates that apparent difference.
- His change ranks at **98.850575** among 87 other eligible players,
  correctly rounded to the **99th percentile**.
- There are **57** regular-season appearances and **17** playoff appearances,
  yielding **57 − 17 + 1 = 41** consecutive 17-appearance windows.
- Using game-log seconds, the playoff rate is **26.654662**; every regular
  window lies between **20.120862 and 24.925009**. The claim that the playoff
  rate exceeds every window is correct.
- The different full-precision playoff rates come from whole-minute season
  totals versus game-log seconds. Both round to 26.7. The windows overlap;
  their percentile is descriptive, not a significance test.

### 2022–23 series

| Opponent | Games | Points | PPG | Points per 36, game-log seconds |
|---|---:|---:|---:|---:|
| Milwaukee | 5 | 188 | 37.6 | 36.348013 |
| New York | 5 | 123 | 24.6 | 21.610542 |
| Boston | 7 | 173 | 24.714286 → 24.7 | 22.444591 |
| Denver | 5 | 108 | 21.6 | 18.924312 → 18.9 |

The series sum to 22 appearances and 592 points. The short's quoted numbers
are correct. Murray's six broad-peer percentiles round to **86, 97, 92, 15,
45 and 34**, as originally stated. His pooled change is higher than Butler's
in all three specified season sets. That does not establish higher peaks;
the original draft's separate 'higher peaks' inference was not supported by
the run-level change measure and is absent from v2.

## Source discrepancies

**Unused games-started discrepancy, confirmed in the original PDF.**
The 2025–26 Nuggets guide's Murray table (PDF page 57, printed page 58)
lists **9** starts in 2016–17. The immediately preceding biography (PDF
page 56, printed page 57) says **10**. Basketball-Reference also says 10.
This is an internal inconsistency in the official guide, not an extraction
error. Games started is not used by any published scoring calculation, and
Murray had no playoff run that season, so no claim changes.

Two existing minutes discrepancies are also confirmed:

- Butler's guide prints **4,512** career playoff minutes, while its season
  rows sum to **4,511**. The analysis uses the season rows, as required for
  season-matched comparisons.
- Murray's rookie regular season has **1,765** minutes in the guide and
  **1,764** in Basketball-Reference. That season is not paired with playoffs.

The two table pages were freshly extracted and rendered from the original
PDFs during this audit. Extracted text matched the stored extraction exactly;
the table columns and Murray biography were visually inspected.

## Presentation corrections before publication

1. **S05 silently clamps 11 peer observations to the plot boundaries.**
   `scenes/s05-fairer-test.html:14` maps everything below −10 to −10 and
   everything above +6 to +6. Across the displayed seasons the actual peer
   values span about **−14.3502 to +9.4333**. Six observations are below −10
   and five above +6. Expand the domain or explicitly mark/count the overflow
   at both ends. The underlying rates, peer medians and Butler highlights
   are correct; the current chart understates the tails.
2. **S07's band is not the full range its caption suggests.**
   `scenes/s07-twist.html:28` draws the **5th–95th percentile** interval,
   **20.296676–24.395412**, with an unlabeled interquartile band, beneath
   'EVERY 17-GAME STRETCH'. The actual full range is
   **20.120862–24.925009**. Show min/max whiskers, all 41 windows, or label
   the central 90% and interquartile intervals. 'Playoffs: above all' remains
   numerically true.

Both issues were confirmed in the existing final S05/S07 stills as well as
their scene code. Neither requires changing the locked research values.

Minor S03 precision note: its animation first widens at the original rate,
then lowers the height, which depicts sequential components **+4.334247 /
−0.331406**. Its labels use the registered symmetric components **+4.307882 /
−0.305041**. Both round to the displayed **+4.3 / −0.3**. This does not create
an incorrect published number; label the graphic schematic or use consistent
geometry if displaying more precision. Its source line correctly includes
the required division by 36 for the rectangle's area.

## Statistical interpretation that still needs care

- **−0.25 is weighted by playoff minutes.** Giving each of the same eleven
  runs equal weight instead yields **−1.367555** points per 36. The weighting
  is consistently implemented for Butler and his peer benchmark; narration
  should disclose it. The S05 source line already does.
- **95 is the number of other eligible players in 2023.** Including Butler
  gives 96. 'Compared with 95 other players' removes the ambiguity in C004.
- **6/11 is an observed fraction, not proof of a coin-flip process.** The
  binomial arithmetic is right, but its model assumes fair independent trials;
  seasons are not established to satisfy that model. Likewise, 11.3% is not
  the probability that Playoff Jimmy is a myth or that the finding is luck.
- Points per 36 measure scoring per clock minute, not efficiency, scoring
  per possession, total impact or a causal playoff ability. Neither accurate
  arithmetic nor passing the predefined wording rule proves those claims.

## Boundary of verification

This verifies the calculations against the frozen source snapshots and
checks the available official-guide overlap. A live Basketball-Reference
fetch was blocked by the site's access response during this audit, so this
does not certify that every historical source row still matches today's
live site. The official guides do not independently cover the full league
or all later seasons. No original NBA scorekeeping or causal model was
independently audited.
