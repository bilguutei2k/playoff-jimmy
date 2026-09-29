# Playoff Jimmy — handoff

One screen: where the episode stands and what happens next. Task details,
decisions and failed attempts are in `STATE.json`; rules are in `METHOD.md`.

## Where we are

Stage: tell. Research is locked at tag `research-lock-v2`: 13 verified claims
in `CLAIMS.json` (checked by `analysis/verify_claims.py`), methods review in
`analysis/review.md`. Storyline chosen: "Real, but not how you think"
(`STORY.md`). Any change to data or method now needs a recorded amendment,
a rerun, re-verification and a new lock tag.

## Next actions

1. User: review script draft v2 in `STORY.md` (8 scenes, about 5 minutes of
   narration, shorts A, B and D; C held). Changes go back through
   `python3 studio/tools/story_check.py studio/episodes/playoff-jimmy`.
2. PJ-05: design system in Claude Design using `studio/design-prompt.md`,
   then two or three stills of real scenes.
3. PJ-07: silent proof render of one scene (S03, the rectangle) once PJ-05
   exists.

## Waiting on the user

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
