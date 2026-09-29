# Playoff Jimmy — handoff

One screen: where the episode stands and what happens next. Task details,
decisions and failed attempts are in `STATE.json`; rules are in `METHOD.md`.

## Where we are

Stage: look. Research is locked at tag `research-lock-v2` (13 verified claims)
and the script at `script-lock-v1` (`STORY.md`). The design system "The Fairer
Test" is in `studio/design-system/`; `studio/DIRECTION.md` says how it applies
to this episode. ffmpeg is installed. The blind Codex re-check (PJ-09, night
run 2026-09-28) re-derived all 82 claim values from the raw snapshot alone:
82 exact, none disagree (`analysis/recheck_report.json`).

## Next actions

1. User: look over every scene (`renders/stills/final-*.png`; regenerate with
   `studio/render/render.mjs`).
2. Narration: choose the voice and record the locked script scene by scene.
3. Then: fit scene timings to the audio, build Short A's opening (S02
   vertical), assemble, captions, loudness, final QA.

## Waiting on the user

- Optional tidy-up: the re-check's worktree can be removed (`git worktree
  remove ../operator-night/20260928-225624-287`); keep the branch
  `night/20260928-225624-287` as the record. Do not merge it into `main`: it
  grows from `recheck-blind`, not `main`.
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
