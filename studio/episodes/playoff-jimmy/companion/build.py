"""Build the companion web page from the locked results and claims.

    python3 companion/build.py

Writes companion/index.html (a complete, self-contained page for any static
host) and renders/companion/page.html (the same page without the document
wrapper, for publishing as a claude.ai Artifact). Every number on the page
comes from analysis/results.json, CLAIMS.json and analysis/recheck_report.json
through this script; the page itself only selects and formats them. Refuses to
run if results.json no longer matches the hash the claims were verified
against.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

EPISODE = Path(__file__).resolve().parent.parent
ROOT = EPISODE.parents[2]
sys.path.insert(0, str(ROOT / "studio/tools"))
from story_check import TAG, scenes  # noqa: E402

PREREGISTRATION = "2827174"      # the commit that fixed METHOD.md before any league data existed (scenes/build_data.py)
PLAYERS = {"butler": "Jimmy Butler", "murray": "Jamal Murray"}
COMPARISONS = {                  # key: (peer group, playoff minutes, source)
    "A_100": ("all", 100, ("benchmark", "A_100")), "A_200": ("all", 200, ("benchmark", "A_200")),
    "B_100": ("scorers", 100, ("benchmark", "B_100")), "B_200": ("scorers", 200, ("benchmark", "B_200")),
    "S_100": ("similar", 100, ("matched", "rate_within_3")),
}
SEASON_SETS = {"all_paired": "Every playoff run", "shared": "Seasons both played",
               "min_100_playoff_minutes": "Runs of 100+ playoff minutes"}


ON_THIS_PAGE = {"PJ-C010", "PJ-C011"}   # Murray's run-by-run results and the season sets, shown by the page's two panels
HELD = "A career ranking among long playoff careers. Held back from the video and this page: it compares players in very different roles and was built after the results (STORY.md, Short C)."


def season(s):
    return s.replace("-", "–")


def claim_entry(c, where):
    if not where and c["id"] not in ON_THIS_PAGE:
        return {"id": c["id"], "held": True, "reason": HELD, "where": [], "exploratory": bool(c.get("exploratory"))}
    return {"id": c["id"], "text": c["text"], "scope": c["scope"], "limitations": c["limitations"],
            "exploratory": bool(c.get("exploratory")), "where": where}


def comparison(results, name, source):
    if source[0] == "benchmark":
        block = results["benchmark"][name]
        career, rows = block["career"][source[1]], block["per_season"][source[1]]
    else:
        block = results["exploratory"]["matched_peers"][name][source[1]]
        career, rows = block["career"], block["per_season"]
    runs = [{"season": season(r["season"]), "delta": r["delta_points_per_36"], "median": r["peer_median"],
             "above": r["delta_points_per_36"] > r["peer_median"], "percentile": r["percentile"],
             "minutes": r["playoff_minutes"], "peers": r["peer_n"]}
            for r in rows if r.get("eligible", True) and r["peer_median"] is not None]
    assert len(runs) == career["n_eligible_seasons"], (name, source)
    assert sum(r["above"] for r in runs) == career["seasons_above_peer_median"], (name, source)
    return {"change": career["pooled_excess_per_36"], "typical": career["minute_weighted_peer_median"],
            "above": career["seasons_above_peer_median"], "runs_n": career["n_eligible_seasons"],
            "minutes": career["playoff_minutes"], "rule_met": career["condition_met"], "runs": runs}


def main():
    results_path = EPISODE / "analysis/results.json"
    digest = hashlib.sha256(results_path.read_bytes()).hexdigest()
    claims = json.loads((EPISODE / "CLAIMS.json").read_text())["claims"]
    stale = [c["id"] for c in claims if c["results_sha256"] != digest]
    if stale:
        raise SystemExit("results.json does not match the verified claims (%s); re-verify first." % ", ".join(stale))
    results = json.loads(results_path.read_text())
    recheck = json.loads((EPISODE / "analysis/recheck_report.json").read_text())
    manifest = json.loads((EPISODE / "data/bbref-manifest.json").read_text())

    story = scenes((EPISODE / "STORY.md").read_text())
    cited = {"film": set(), "shorts": set()}
    for (section, _), lines in story.items():
        kind = "film" if section.startswith("Script") else "shorts"
        for line in lines:
            cited[kind].update(c.strip() for g in TAG.findall(line) for c in g.split(","))

    comparisons = {key: dict(zip(("group", "minutes"), spec[:2]), **{name: comparison(results, name, spec[2]) for name in PLAYERS})
                   for key, spec in COMPARISONS.items()}
    values = [v for c in comparisons.values() for name in PLAYERS for r in c[name]["runs"] for v in (r["delta"], r["median"])]
    sets = {key: {"label": label, "leader": results["season_sets"][key]["higher_excess_per_36"],
                  **{name: {"change": results["season_sets"][key][name]["excess_per_36"],
                            "equal_weight": results["season_sets"][key][name]["equal_season_mean_delta_per_36"],
                            "runs_n": results["season_sets"][key][name]["n_seasons"],
                            "minutes": results["season_sets"][key][name]["playoff_minutes"],
                            "seasons": [season(s) for s in results["season_sets"][key][name]["seasons"]]} for name in PLAYERS}}
            for key, label in SEASON_SETS.items()}
    public = json.loads((EPISODE / "PUBLIC.json").read_text()) if (EPISODE / "PUBLIC.json").exists() else None
    if public:                           # cite the public repository's hash, which visitors can check
        log = [public["preregistration_commit"], public["preregistration_date"]]
    else:
        log = subprocess.run(["git", "-C", str(EPISODE), "log", "-1", "--format=%h %cs", PREREGISTRATION],
                             capture_output=True, text=True, check=True).stdout.split()
    pages = manifest["pages"]
    payload = {
        "players": PLAYERS,
        "comparisons": comparisons,
        "domain": [int(min(values) // 1), int(-(-max(values) // 1))],
        "season_sets": sets,
        "claims": [claim_entry(c, [k for k in ("film", "shorts") if c["id"] in cited[k]]) for c in claims],
        "checks": {"preregistration_commit": log[0], "preregistration_date": log[1],
                   "recheck_exact": recheck["counts"]["exact"],
                   "recheck_total": sum(recheck["counts"].values()),
                   "bbref_pages": len(pages),
                   "bbref_retrieved_utc": min(p["retrieved_at"][:10] for p in pages)},
        "method": results["method"],
        "public": public,
        "results_sha256": digest,
        "analysis_revision": claims[0]["analysis_revision"],
    }
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    template = (Path(__file__).parent / "template.html").read_text()
    head, body = template.replace("__DATA__", data).split("<!--BODY-->")
    standalone = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                  '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
                  + head + "</head>\n<body>\n" + body + "</body>\n</html>\n")
    (EPISODE / "companion/index.html").write_text(standalone)
    fragment = EPISODE / "renders/companion/page.html"
    fragment.parent.mkdir(parents=True, exist_ok=True)
    fragment.write_text(head + body)
    print("Wrote companion/index.html and %s (results %s)" % (fragment.relative_to(EPISODE), digest[:12]))


if __name__ == "__main__":
    main()
