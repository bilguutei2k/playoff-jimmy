# Playoff Jimmy — handoff

One screen: where the episode stands and what happens next. Task details,
decisions and failed attempts are in `STATE.json`; rules are in `METHOD.md`.

## Where we are

Stage: analyze, at the PJ-04 gate. The methods review is written
(`analysis/review.md`, Review 2) and 11 claims are proposed in `CLAIMS.json`.
Every claim value is recomputed independently by `analysis/verify_claims.py`
and passes. Charts: `analysis/packet/index.html`.

## Next actions

1. User: approve the claims (or edit wording) and choose the storyline.
2. Then: mark the claims verified, commit, tag `research-lock-v1`.
3. PJ-06: scenes, script draft and short-form outlines from the verified claims.

## Waiting on the user

- PJ-04 review session (about an hour).
- Design system, set up separately (possibly in Claude Design) before the
  PJ-05 stills. The Raphinha reel was a sample only.
- Narrator voice (own voice or a free local AI voice) before PJ-08; approval
  to install ffmpeg before PJ-07.

## Commands

```sh
python3 -m nightshift.episodes status playoff-jimmy
python3 studio/episodes/playoff-jimmy/analysis/analyze.py   # regenerate results
python3 studio/episodes/playoff-jimmy/analysis/packet.py    # regenerate the packet
open studio/episodes/playoff-jimmy/analysis/packet/index.html
python3 -B -m unittest discover -s tests -v
```

`analyze.py` overwrites its outputs in `analysis/`; use `--out DIR` for a
check that should leave them untouched. Both scripts are deterministic.
