"""Compare an independent, blind re-derivation of the claim values with results.json.

    python3 analysis/compare_recheck.py <path to recheck/values.json>

Writes analysis/recheck_report.json. "exact" means the same number to
floating-point precision; "published" means it differs in full precision but
agrees at the precision the claim states. Exits 1 if any value is missing or
disagrees.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_claims import EPISODE, agrees, resolve  # noqa: E402


def compare(values_path):
    results = json.loads((EPISODE / "analysis/results.json").read_text())
    submitted = json.loads(Path(values_path).read_text())
    theirs = submitted.get("values", {})
    stated = {}
    for claim in json.loads((EPISODE / "CLAIMS.json").read_text())["claims"]:
        for item in claim["values"]:
            stated.setdefault(item["key"], []).append((claim["id"], item))
    rows = []
    for key, uses in stated.items():
        ours = resolve(results, key)
        row = {"key": key, "claims": [c for c, _ in uses], "ours": ours, "theirs": theirs.get(key, "missing")}
        if key not in theirs:
            row["status"] = "missing"
        elif isinstance(ours, (bool, str)) or ours is None:
            row["status"] = "exact" if theirs[key] == ours else "disagrees"
        elif not isinstance(theirs[key], (int, float)) or isinstance(theirs[key], bool):
            row["status"] = "disagrees"
        elif abs(theirs[key] - ours) <= 1e-9 * max(1.0, abs(ours)):
            row["status"] = "exact"
        elif all(agrees(item["stated"], theirs[key], item.get("digits")) for _, item in uses):
            row["status"] = "published"
        else:
            row["status"] = "disagrees"
        rows.append(row)
    counts = {s: sum(r["status"] == s for r in rows) for s in ("exact", "published", "disagrees", "missing")}
    return {"values_file": str(values_path), "notes_from_rechecker": submitted.get("notes", ""),
            "counts": counts, "rows": rows}


def main():
    report = compare(sys.argv[1])
    (EPISODE / "analysis/recheck_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(report["counts"])
    for row in report["rows"]:
        if row["status"] in ("disagrees", "missing"):
            print("%s (%s): ours %r, theirs %r" % (row["key"], ", ".join(row["claims"]), row["ours"], row["theirs"]))
    return 0 if not report["counts"]["disagrees"] and not report["counts"]["missing"] else 1


if __name__ == "__main__":
    sys.exit(main())
