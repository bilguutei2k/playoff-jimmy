# Playoff Jimmy — handoff

One screen: where the episode stands and what happens next. Task details,
decisions and failed attempts are in `STATE.json`; rules are in `METHOD.md`.

## Where we are

Stage: acquire. The research method is pre-registered (`METHOD.md`, committed
before any peer data was downloaded). The pilot analysis on the two official
media guides is reproducible and was independently reviewed
(`analysis/review.md`). No claim is verified yet; no script or render exists.

## Next actions

1. PJ-02: snapshot Basketball-Reference season totals (2011–12 to 2025–26)
   and the two players' game logs; reconcile against the media guides.
2. PJ-03: analysis v2 and a results packet of plain charts.
3. PJ-04: methods gate with Claude, then a research lock.

## Waiting on the user

- Opus examples for the visual direction (blocks PJ-05).
- Narration choice and approval to install ffmpeg (needed by PJ-07).

## Commands

```sh
python3 -m nightshift.episodes status playoff-jimmy
python3 -B -m unittest discover -s tests -v
```

`analysis/analyze.py` overwrites its outputs in `analysis/`; run it only when
you intend to regenerate them.
