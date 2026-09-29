# Playoff Jimmy — handoff

One screen: where the episode stands and what happens next. Task details,
decisions and failed attempts are in `STATE.json`; rules are in `METHOD.md`.

## Where we are

Stage: analyze. PJ-02 and PJ-03 are done (2026-09-28): sources reconcile, and
analysis v2 ran exactly as pre-registered. Open `analysis/packet/index.html`
for the charts, or read `analysis/FINDINGS.md`. The results are **unreviewed**:
no claim is verified and the storyline is not chosen.

## Next actions

1. PJ-04 (daytime, with Claude): review the packet against `METHOD.md`,
   resolve objections, write 5–10 claims in `CLAIMS.json`, choose the
   storyline, tag the research lock.
2. PJ-05 when the Opus examples arrive: two or three stills of real scenes.
3. PJ-06 after the lock: scenes, script draft and short-form outlines.

## Waiting on the user

- Opus examples for the visual direction (blocks PJ-05).
- Narration choice and approval to install ffmpeg (needed by PJ-07).

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
