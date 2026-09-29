# Playoff Jimmy — handoff

One screen: where the episode stands and what happens next. Task details,
decisions and failed attempts are in `STATE.json`; rules are in `METHOD.md`.

## Where we are

Stage: look. Research is locked at tag `research-lock-v2` (13 verified claims)
and the script at `script-lock-v1` (`STORY.md`). The design system "The Fairer
Test" is in `studio/design-system/`; `studio/DIRECTION.md` says how it applies
to this episode. ffmpeg is installed.

## Next actions

1. Frame pipeline: HTML/SVG scene pages on an explicit frame clock, captured
   with headless Chromium, encoded with ffmpeg; fonts stored in the repo.
2. PJ-05: two or three stills of real scenes (title, before → after, the
   dot strip) with verified numbers.
3. PJ-07: silent proof of S03 at 1920×1080 and 1080×1920, then inspect it.

## Waiting on the user

- Rectangle scene: build a rectangle chart in the design system's style
  (recommended), or switch S03/S08 to the system's two-part split.
- Narrator voice before PJ-08 (own voice, or a free local AI voice).
- Optional: a Codex re-derivation of the 13 claims before publication.

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
