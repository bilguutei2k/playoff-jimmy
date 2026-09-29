# Playoff Jimmy — handoff

One screen: where the episode stands and what happens next. Task details,
decisions and failed attempts are in `STATE.json`; rules are in `METHOD.md`.

## Where we are

Stage: look. Research is locked at tag `research-lock-v2` (13 verified claims)
and the script at `script-lock-v1` (`STORY.md`). The design system "The Fairer
Test" is in `studio/design-system/`; `studio/DIRECTION.md` says how it applies
to this episode. ffmpeg is installed.

## Next actions

1. User: watch the S03 proof clips (`renders/motion/s03-rectangle.mp4` and
   `s03-rectangle-vertical.mp4`; regenerate with `studio/render/render.mjs`).
2. Tonight after 10:37 PM, plugged in: launch the blind Codex re-check
   (`recheck/PLAN.md`).
3. Remaining scenes (S05–S08, shorts A/B/D verticals); S08 needs the
   decision in `studio/DIRECTION.md` first.
4. Narration recording, then timing, assembly and QA.

## Waiting on the user

- Tonight, after 10:37 PM (Codex allowance reset), plugged in: launch the
  blind re-check, `python3 -m nightshift.runner
  studio/episodes/playoff-jimmy/recheck/PLAN.md` (details in that file).
- Narrator voice before PJ-08 (own voice, or a free local AI voice).

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
