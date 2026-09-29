# Overnight: blind re-derivation of the Playoff Jimmy claims

Codex recomputes every claim value from the raw snapshot alone, on the
`recheck-blind` branch, which holds only the data, `RECHECK.md` and the
format checker (no analysis code, results or claims). The runner commits its
work to a `night/...` branch; nothing on `main` changes.

**Launch** (Mac plugged in; Codex's allowance was exhausted until 10:37 PM on
2026-09-28, so start after that):

    cd ~/Documents/ChatGPT/operator
    python3 -m nightshift.runner studio/episodes/playoff-jimmy/recheck/PLAN.md --check
    python3 -m nightshift.runner studio/episodes/playoff-jimmy/recheck/PLAN.md

**Morning:** the run prints the path of its report. With the worktree path
from that report:

    python3 studio/episodes/playoff-jimmy/analysis/compare_recheck.py <worktree>/recheck/values.json
    grep -nE 'git (show|log|diff|checkout)|operator/studio' <run folder>/claims-recheck/attempt-*/agent/stdout.log

The first command compares values; the second checks that Codex stayed blind.

```nightshift
{
  "version": 1,
  "ref": "recheck-blind",
  "hours": 3,
  "agent": "codex",
  "effort": "high",
  "task_minutes": 90,
  "verify_minutes": 5,
  "max_attempts": 2,
  "require_ac": true,
  "protected": ["data/*", "RECHECK.md", "recheck/check_format.py"],
  "goals": [
    {"id": "claims-recheck",
     "verify": [["python3", "-B", "recheck/code/run.py"],
                ["python3", "-B", "recheck/check_format.py", "recheck/values.json"]]}
  ]
}
```

## claims-recheck

Read `RECHECK.md` in the repository root and do exactly what it says:
compute every key listed in `recheck/check_format.py` from the raw data in
this checkout, with your own standard-library Python under `recheck/code/`,
and write `recheck/values.json`. Work blind: do not use git history, other
branches or anything outside this checkout. Record every judgment call about
an ambiguous definition in the `notes` field.
