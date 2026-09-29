# Playoff Jimmy — handoff

One screen: where the episode stands and what happens next. Task details,
decisions and failed attempts are in `STATE.json`; rules are in `METHOD.md`.

## Where we are

Stage: acquire. The research rules are pre-registered in `METHOD.md`
(commit 2827174), committed before any peer data was downloaded. The
Basketball-Reference snapshot is saved and hash-verified (commit de8233c): 15
league totals pages for 2011–12 to 2025–26 and 18 game logs. The media-guide
pilot is reproducible and independently reviewed (`analysis/review.md`). No
claim is verified yet; no script or render exists.

## Next actions (daytime sessions)

1. PJ-02: parse the snapshot; reconcile every media-guide row against it
   (counts exact, minutes within 1); give every player-season an exposure
   class computed from the data.
2. PJ-03: analysis v2 exactly as `METHOD.md` specifies, then a results packet
   of plain charts that read only `results.json`.
3. PJ-04: methods review with Claude, then 5–10 claims and a research-lock
   commit. The storyline is chosen here, from the results.

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
