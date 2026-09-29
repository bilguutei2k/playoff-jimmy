# Playoff Jimmy — handoff

One screen: where the episode stands and what happens next. Task details,
decisions and failed attempts are in `STATE.json`; rules are in `METHOD.md`.

## Where we are

Stage: produce → review. Research is locked at tag `research-lock-v2` (13
verified claims); the blind Codex re-check re-derived all 82 claim values
exactly (PJ-09). The script is v3 (`STORY.md`): v2 plus Astra's final review
(`analysis/review.md`, Review 4), wording only.

Draft videos exist, narrated by a local AI voice (Kokoro-82M, voice
`af_heart`): the film and shorts A, B and D in `renders/draft/`, each with an
`.srt` caption file and a `.json` record of its shots, cues and hashes.
`renders/` is not in git; everything in it rebuilds from the commands below.

## Next actions

1. User: revise the script in the script desk,
   https://claude.ai/artifact/FJKKJQXat7T8z5De4nU88B (rebuild it with
   `python3 studio/tools/storyboard.py studio/episodes/playoff-jimmy`). Claude reads
   the edits (collections `lines` and `notes`) and makes script v4.
2. Optional: pick another voice from `renders/audio/audition/`, then rerun
   narrate.py with `--voice` and assemble.py; the timing follows the words.
3. Companion page (PJ-11): first draft published privately at
   https://claude.ai/artifact/BB687E4Z5fPCJwXqadMdZ3, built from
   `companion/build.py`. It needs the public data-and-code link and the video
   link before release.
4. The publishing package (PJ-12).

## Waiting on the user

- The draft review (PJ-10).
- Optional tidy-up: the re-check's worktree can be removed (`git worktree
  remove ../operator-night/20260928-225624-287`); keep the branch
  `night/20260928-225624-287` as the record. Do not merge it into `main`: it
  grows from `recheck-blind`, not `main`.

## Public

- Repository: https://github.com/bilguutei2k/playoff-jimmy (history filtered by
  `studio/tools/public_repo.sh`; hashes differ from this repository's).
- Companion site: https://bilguutei2k.github.io/playoff-jimmy/ (branch `gh-pages`).
- To update both after new commits here:

  ```sh
  studio/tools/public_repo.sh /tmp/pj-public
  git -C /tmp/pj-public push https://github.com/bilguutei2k/playoff-jimmy.git main --tags
  # site: copy companion/index.html into a checkout of gh-pages, commit, push
  ```

## Commands

```sh
python3 studio/tools/story_check.py studio/episodes/playoff-jimmy           # script against claims
.venv/bin/python studio/tools/narrate.py studio/episodes/playoff-jimmy      # narration (cached per line)
python3 studio/tools/assemble.py studio/episodes/playoff-jimmy [film short-a short-b short-d]
python3 studio/episodes/playoff-jimmy/companion/build.py                    # companion page
python3 -m nightshift.episodes status playoff-jimmy
python3 studio/episodes/playoff-jimmy/analysis/analyze.py   # regenerate results
python3 -B -m unittest discover -s tests -v
```

The `.venv` (Python 3.12, `pip install mlx-audio 'misaki[en]'`) holds the
voice; everything else runs on the system Python. `analyze.py` overwrites its
outputs in `analysis/`; use `--out DIR` for a check that should leave them
untouched.
