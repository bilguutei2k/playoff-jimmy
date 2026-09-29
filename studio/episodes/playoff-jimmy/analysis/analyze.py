"""Playoff Jimmy analysis v2: the pre-registered measures in METHOD.md.

Reads only frozen inputs (media-guide text and the Basketball-Reference
snapshot). Pure standard library.

    python3 analysis/analyze.py              # regenerate the outputs in analysis/
    python3 analysis/analyze.py --out DIR    # write elsewhere, e.g. for a rerun check

Exits non-zero if any data check fails; the outputs still record what failed.
Never treats a missing season as a zero-stat season.
"""

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bbref  # noqa: E402
import guides  # noqa: E402
from guides import SOURCES, validate  # noqa: E402,F401  (re-exported for tests)


ROOT = guides.ROOT
SUBJECTS = bbref.SUBJECTS
FIRST_SEASON = {"butler": "2011-12", "murray": "2016-17"}
LAST_SEASON = "2025-26"
GUIDE_COVERAGE = {"butler": ("2011-12", "2022-23"), "murray": ("2016-17", "2024-25")}
THRESHOLDS = (100, 200)  # playoff minutes; 100 is primary, 200 the sensitivity check
REGULAR_MINUTES = 1500
PEER_B_PPG = 20.0
VARIABILITY_MIN_MINUTES = 100
CASE_SEASON = "2022-23"


# ---- per-season measures -------------------------------------------------

def divide(a, b):
    return a / b if b else None


def rates(row):
    tsa = row["fga"] + 0.44 * row["fta"]
    return {"ppg": divide(row["points"], row["games"]),
            "mpg": divide(row["minutes"], row["games"]),
            "points_per_36": divide(36 * row["points"], row["minutes"]),
            "tsa_per_36": divide(36 * tsa, row["minutes"]),
            "approx_ts": divide(row["points"], 2 * tsa)}


def difference(a, b):
    return None if a is None or b is None else b - a


def pair(reg, post):
    """Paired regular-season and playoff measures. Both must have positive minutes."""
    regular, playoffs = rates(reg), rates(post)
    reg_rate, post_rate = reg["points"] / reg["minutes"], post["points"] / post["minutes"]
    minutes_part = (reg_rate + post_rate) / 2 * (playoffs["mpg"] - regular["mpg"])
    rate_part = (regular["mpg"] + playoffs["mpg"]) / 2 * (post_rate - reg_rate)
    delta_ppg = playoffs["ppg"] - regular["ppg"]
    if not math.isclose(delta_ppg, minutes_part + rate_part, abs_tol=1e-10):
        raise ValueError("Decomposition identity failed")
    expected = post["minutes"] * reg_rate
    return {"regular": regular, "playoffs": playoffs,
            "regular_games": reg["games"], "playoff_games": post["games"],
            "regular_minutes": reg["minutes"], "playoff_minutes": post["minutes"],
            "playoff_points": post["points"], "expected_playoff_points": expected,
            "excess_points": post["points"] - expected,
            "delta_ppg": delta_ppg,
            "delta_points_per_36": playoffs["points_per_36"] - regular["points_per_36"],
            "delta_tsa_per_36": difference(regular["tsa_per_36"], playoffs["tsa_per_36"]),
            "delta_approx_ts": difference(regular["approx_ts"], playoffs["approx_ts"]),
            "ppg_decomposition": {"minutes_component": minutes_part, "rate_component": rate_part,
                                  "interpretation": "descriptive_arithmetic_not_causal"}}


def paired_results(records):
    """Every player-season with positive minutes in both phases; others are not pairs."""
    indexed = {(r["player"], r["season"], r["phase"]): r for r in records}
    pairs = []
    for (player, season, phase), post in sorted(indexed.items()):
        reg = indexed.get((player, season, "regular"))
        if phase != "playoffs" or not reg or min(reg["minutes"], reg["games"], post["minutes"], post["games"]) == 0:
            continue
        pairs.append({"player": player, "season": season, **pair(reg, post)})
    return pairs


def summarize(pairs):
    minutes = sum(p["playoff_minutes"] for p in pairs)
    actual = sum(p["playoff_points"] for p in pairs)
    expected = sum(p["expected_playoff_points"] for p in pairs)
    return {"seasons": [p["season"] for p in pairs], "n_seasons": len(pairs), "playoff_minutes": minutes,
            "actual_points": actual, "expected_points": expected, "excess_points": actual - expected,
            "excess_per_36": divide(36 * (actual - expected), minutes),
            "equal_season_mean_delta_per_36": statistics.mean(p["delta_points_per_36"] for p in pairs) if pairs else None}


# ---- benchmark -------------------------------------------------------------

def percentile(value, peers):
    """Share of peers below the value, counting ties as half, on a 0-100 scale."""
    if not peers:
        return None
    return 100 * (sum(p < value for p in peers) + 0.5 * sum(p == value for p in peers)) / len(peers)


def band(pct):
    if pct is None:
        return None
    if pct < 25:
        return "below typical"
    if pct <= 75:
        return "typical"
    if pct < 90:
        return "above typical"
    return "exceptional"


def eligible_players(totals, season, threshold):
    found = []
    for (player_id, s, phase), post in totals.items():
        if s != season or phase != "playoffs" or post["minutes"] < threshold:
            continue
        reg = totals.get((player_id, season, "regular"))
        if reg and reg["minutes"] >= REGULAR_MINUTES:
            found.append({"player": player_id, "name": post["name"], "regular_ppg": reg["points"] / reg["games"],
                          "regular_minutes": reg["minutes"], "playoff_minutes": post["minutes"],
                          "delta_points_per_36": 36 * post["points"] / post["minutes"] - 36 * reg["points"] / reg["minutes"]})
    return sorted(found, key=lambda p: p["player"])


def peer_values(eligible, subject_id, peer_set):
    return [p["delta_points_per_36"] for p in eligible if p["player"] != subject_id
            and (peer_set == "A" or p["regular_ppg"] >= PEER_B_PPG)]


def career_condition(rows):
    """Pooled excess per 36 above the minute-weighted peer median, and a majority of seasons above it."""
    rows = [r for r in rows if r["peer_median"] is not None]
    minutes = sum(r["playoff_minutes"] for r in rows)
    if not minutes:
        return {"n_eligible_seasons": 0, "condition_met": False}
    pooled = 36 * sum(r["excess_points"] for r in rows) / minutes
    weighted_median = sum(r["playoff_minutes"] * r["peer_median"] for r in rows) / minutes
    above = sum(r["delta_points_per_36"] > r["peer_median"] for r in rows)
    return {"n_eligible_seasons": len(rows), "seasons": [r["season"] for r in rows], "playoff_minutes": minutes,
            "pooled_excess_per_36": pooled, "minute_weighted_peer_median": weighted_median,
            "seasons_above_peer_median": above,
            "condition_met": pooled > weighted_median and above > len(rows) / 2}


def benchmark(totals, subject_pairs, seasons):
    eligible = {(s, t): eligible_players(totals, s, t) for s in seasons for t in THRESHOLDS}
    result = {}
    for name, pairs in subject_pairs.items():
        subject_id = SUBJECTS[name]
        by_rule, conditions = {}, {}
        for peer_set in ("A", "B"):
            for threshold in THRESHOLDS:
                rows = []
                for p in pairs:
                    pool = eligible[(p["season"], threshold)]
                    is_eligible = p["regular_minutes"] >= REGULAR_MINUTES and p["playoff_minutes"] >= threshold
                    peers = peer_values(pool, subject_id, peer_set) if is_eligible else []
                    pct = percentile(p["delta_points_per_36"], peers) if is_eligible else None
                    rows.append({"season": p["season"], "eligible": is_eligible,
                                 "delta_points_per_36": p["delta_points_per_36"],
                                 "playoff_minutes": p["playoff_minutes"], "excess_points": p["excess_points"],
                                 "peer_n": len(peers), "peer_median": statistics.median(peers) if peers else None,
                                 "percentile": pct, "wording": band(pct)})
                key = "%s_%d" % (peer_set, threshold)
                by_rule[key] = rows
                conditions[key] = career_condition([r for r in rows if r["eligible"]])
        result[name] = {"per_season": by_rule, "career": conditions,
                        "real_per_minute_rule_met": all(c["condition_met"] for c in conditions.values())}
    context = {}
    for threshold in THRESHOLDS:
        values = [p["delta_points_per_36"] for s in seasons for p in eligible[(s, threshold)]]
        context[str(threshold)] = {"n_player_seasons": len(values), "median_delta_per_36": statistics.median(values),
                                   "share_below_zero": sum(v < 0 for v in values) / len(values)}
    peers = {s: eligible[(s, THRESHOLDS[0])] for s in seasons}
    return result, context, peers


# ---- exploratory (added after results; not pre-registered) -------------------

CAREER_MIN_RUNS = (6, 8)


def career_edges(peers, min_runs):
    """Every player's pooled per-36 change minus the minute-weighted median of his peers, over his eligible runs."""
    runs = {}
    for season, pool in peers.items():
        for p in pool:
            runs.setdefault(p["player"], []).append((season, p))
    medians = {(s, pid): statistics.median([q["delta_points_per_36"] for q in pool if q["player"] != pid])
               for s, pool in peers.items() for pid in (p["player"] for p in pool)}
    edges = {}
    for pid, items in runs.items():
        if len(items) < min_runs:
            continue
        minutes = sum(p["playoff_minutes"] for _, p in items)
        pooled = sum(p["delta_points_per_36"] * p["playoff_minutes"] for _, p in items) / minutes
        weighted = sum(p["playoff_minutes"] * medians[(s, pid)] for s, p in items) / minutes
        edges[pid] = {"name": items[0][1]["name"], "runs": len(items), "playoff_minutes": minutes,
                      "pooled_delta_per_36": pooled, "minute_weighted_peer_median": weighted, "edge_per_36": pooled - weighted,
                      "runs_above_peer_median": sum(p["delta_points_per_36"] > medians[(s, pid)] for s, p in items)}
    values = [e["edge_per_36"] for e in edges.values()]
    ranked = sorted(edges.items(), key=lambda item: (-item[1]["edge_per_36"], item[0]))
    return {"min_eligible_runs": min_runs, "n_players": len(edges), "median_edge_per_36": statistics.median(values),
            "share_positive": sum(v > 0 for v in values) / len(values),
            "subjects": {name: {**edges[pid], "percentile": percentile(
                             edges[pid]["edge_per_36"], [e["edge_per_36"] for p, e in edges.items() if p != pid]),
                             "rank": 1 + sum(e["edge_per_36"] > edges[pid]["edge_per_36"] for e in edges.values())}
                         for name, pid in SUBJECTS.items() if pid in edges},
            "top_10": [{"player": pid, **e} for pid, e in ranked[:10]]}


def sign_test(benchmark_rows):
    """Chance of at least this many seasons above the peer median if each were a coin flip."""
    rows = [r for r in benchmark_rows if r["eligible"]]
    n, above = len(rows), sum(r["delta_points_per_36"] > r["peer_median"] for r in rows)
    return {"n_eligible_seasons": n, "seasons_above_peer_median": above,
            "one_sided_p": sum(math.comb(n, k) for k in range(above, n + 1)) / 2 ** n,
            "mean_percentile": statistics.mean(r["percentile"] for r in rows)}


def exploratory(bench, peers):
    return {"label": "Exploratory: added 2026-09-28 during the PJ-04 review, after results existed. Not pre-registered; "
                     "it cannot change the METHOD.md rule outcome.",
            "career_edge": [career_edges(peers, m) for m in CAREER_MIN_RUNS],
            "season_count_check": {name: sign_test(b["per_season"]["A_100"]) for name, b in bench.items()}}


# ---- game logs -------------------------------------------------------------

def per_36(games):
    seconds = sum(g["seconds"] for g in games)
    return divide(36 * 60 * sum(g["points"] for g in games), seconds)


def window_rates(games, k):
    return [per_36(games[i:i + k]) for i in range(len(games) - k + 1)]


def variability(logs, subject_pairs):
    found = []
    for name, pairs in subject_pairs.items():
        for p in pairs:
            log = logs.get((name, p["season"]))
            if p["playoff_minutes"] < VARIABILITY_MIN_MINUTES or not log:
                continue
            k = len(log["playoffs"])
            windows = window_rates(log["regular"], k)
            if len(windows) < 2:
                continue
            playoff = per_36(log["playoffs"])
            cuts = statistics.quantiles(windows, n=20, method="inclusive")
            found.append({"player": name, "season": p["season"], "playoff_games": k,
                          "regular_games": len(log["regular"]), "n_windows": len(windows),
                          "playoff_points_per_36": playoff, "regular_points_per_36": per_36(log["regular"]),
                          "window_percentile_of_playoff_run": percentile(playoff, windows),
                          "window_quantiles": {"min": min(windows), "p05": cuts[0], "p25": cuts[4], "p50": cuts[9],
                                               "p75": cuts[14], "p95": cuts[18], "max": max(windows)},
                          "label": "variability reference, not a significance test"})
    return found


def series(logs, season):
    found = {}
    for name in SUBJECTS:
        log = logs.get((name, season))
        if not log:
            continue
        rounds = []
        for game in log["playoffs"]:
            if not rounds or rounds[-1]["opponent"] != game["opponent"]:
                rounds.append({"opponent": game["opponent"], "games": []})
            rounds[-1]["games"].append(game)
        if len({r["opponent"] for r in rounds}) != len(rounds):
            raise ValueError("An opponent appears in two separate series")
        rows = []
        for number, block in enumerate(rounds, 1):
            games = block["games"]
            points, fga, fta = (sum(g[f] for g in games) for f in ("points", "fga", "fta"))
            minutes = sum(g["seconds"] for g in games) / 60
            rows.append({"round": number, "opponent": block["opponent"], "games": len(games),
                         "first_date": games[0]["date"], "last_date": games[-1]["date"],
                         "ppg": points / len(games), "mpg": minutes / len(games),
                         "points_per_36": per_36(games), "approx_ts": divide(points, 2 * (fga + 0.44 * fta))})
        found[name] = {"regular_points_per_36": per_36(log["regular"]),
                       "playoff_points_per_36": per_36(log["playoffs"]), "series": rows}
    return found


# ---- reconciliation ----------------------------------------------------------

def reconcile_guides(guide_records, totals):
    rows = []
    for g in guide_records:
        b = totals.get((SUBJECTS[g["player"]], g["season"], g["phase"]))
        row = {"player": g["player"], "season": g["season"], "phase": g["phase"]}
        if g["games"] == 0:
            row["status"] = "both_no_games" if b is None else "mismatch"
        elif b is None:
            row["status"] = "mismatch"
            row["note"] = "missing from Basketball-Reference"
        else:
            diffs = {f: [g[f], b[f]] for f in guides.COUNTS if f != "minutes" and g[f] != b[f]}
            gap = b["minutes"] - g["minutes"]
            row["status"] = ("match" if not diffs and gap == 0 else
                             "minutes_within_1" if not diffs and abs(gap) <= 1 else "mismatch")
            if diffs or gap:
                row["differences"] = {**diffs, **({"minutes": [g["minutes"], b["minutes"]]} if gap else {})}
        rows.append(row)
    seen = {(g["player"], g["season"], g["phase"]) for g in guide_records if g["games"]}
    for (player_id, season, phase), b in sorted(totals.items()):
        for name, subject_id in SUBJECTS.items():
            first, last = GUIDE_COVERAGE[name]
            if player_id == subject_id and first <= season <= last and (name, season, phase) not in seen:
                rows.append({"player": name, "season": season, "phase": phase, "status": "mismatch",
                             "note": "missing from the media guide"})
    return rows


def reconcile_logs(logs, totals):
    rows = []
    for (name, season), log in sorted(logs.items()):
        for phase in ("regular", "playoffs"):
            games, total = log[phase], totals[(SUBJECTS[name], season, phase)]
            diffs = {f: [sum(g[f] for g in games), total[f]] for f in ("points", "fgm", "fga", "fg3m", "ftm", "fta")
                     if sum(g[f] for g in games) != total[f]}
            if len(games) != total["games"]:
                diffs["games"] = [len(games), total["games"]]
            gap = sum(g["seconds"] for g in games) / 60 - total["minutes"]
            rows.append({"player": name, "season": season, "phase": phase, "minutes_gap": gap,
                         "differences": diffs, "status": "match" if not diffs and abs(gap) <= 1 else "mismatch"})
    return rows


# ---- assembly ----------------------------------------------------------------

def exposure(reg, post, playoff_teams):
    if reg is None and post is None:
        return "no_games"
    if reg is None:
        raise ValueError("Playoff row without a regular-season row")
    if post is not None:
        return "paired" if reg["minutes"] > 0 and post["minutes"] > 0 else "zero_minutes"
    return "playoff_team_no_games" if reg["final_team"] in playoff_teams else "team_missed_playoffs"


def load_records():
    """Media-guide records, kept under this name for the pilot tests."""
    return guides.load()[0]


def guide_pilot(guide_records):
    pairs = {(p["player"], p["season"]): p for p in paired_results(guide_records)}
    def pick(player, seasons):
        return summarize([pairs[(player, s)] for s in seasons if (player, s) in pairs])
    butler = sorted(s for p, s in pairs if p == "butler")
    shared = sorted({s for p, s in pairs if p == "butler"} & {s for p, s in pairs if p == "murray"})
    return {"butler_2016_17_to_2022_23": pick("butler", [s for s in butler if s >= "2016-17"]),
            "butler_all_guide_seasons": pick("butler", butler),
            "murray_all_guide_seasons": pick("murray", sorted(s for p, s in pairs if p == "murray")),
            "butler_shared": pick("butler", shared), "murray_shared": pick("murray", shared),
            "butler_2022_23": pairs[("butler", "2022-23")]}


def analyze(root=ROOT):
    guide_records, printed_totals = guides.load(root)
    snapshot = bbref.load(root)
    totals, logs = snapshot["totals"], snapshot["game_logs"]
    seasons = [s for s in snapshot["seasons"] if s <= LAST_SEASON]

    subjects, subject_pairs, coverage = {}, {}, {}
    for name, subject_id in SUBJECTS.items():
        rows, pairs = [], []
        for season in seasons:
            if season < FIRST_SEASON[name]:
                continue
            reg, post = totals.get((subject_id, season, "regular")), totals.get((subject_id, season, "playoffs"))
            row = {"season": season, "exposure": exposure(reg, post, snapshot["playoff_teams"][season]),
                   "regular_team": reg and reg["team"], "final_team": reg and reg["final_team"],
                   "regular_games": reg and reg["games"], "playoff_games": post and post["games"],
                   "game_log": (name, season) in logs}
            if row["exposure"] == "paired":
                measures = {"season": season, **pair(reg, post)}
                pairs.append(measures)
                row["measures"] = measures
            rows.append(row)
        subjects[name] = rows
        subject_pairs[name] = pairs
        coverage[name] = {r["season"]: r["exposure"] for r in rows}

    by_name = {name: {p["season"]: p for p in pairs} for name, pairs in subject_pairs.items()}
    shared = sorted(set(by_name["butler"]) & set(by_name["murray"]))
    season_sets = {}
    for set_name, choose in (("all_paired", lambda name: sorted(by_name[name])),
                             ("shared", lambda name: shared),
                             ("min_100_playoff_minutes", lambda name: sorted(s for s, p in by_name[name].items()
                                                                             if p["playoff_minutes"] >= 100))):
        season_sets[set_name] = {name: summarize([by_name[name][s] for s in choose(name)]) for name in SUBJECTS}
        leader = max(SUBJECTS, key=lambda n: season_sets[set_name][n]["excess_per_36"])
        season_sets[set_name]["higher_excess_per_36"] = leader
    leaders = {season_sets[s]["higher_excess_per_36"] for s in season_sets}
    comparison = {"leader_in_every_set": leaders.pop() if len(leaders) == 1 else None,
                  "rule": "No 'who rises more' statement unless the same player leads in all three sets."}

    bench, context, peers = benchmark(totals, subject_pairs, seasons)
    guide_rows = reconcile_guides(guide_records, totals)
    log_rows = reconcile_logs(logs, totals)
    printed = guides.totals_discrepancies(guide_records, printed_totals)
    traded_bad = [t for t in snapshot["traded"] if t["mismatched_fields"]]

    qa = {"status": "analysis_v2_pending_methods_review",
          "checks": {
              "guide_hashes_and_integrity": {"status": "passed", "rows": len(guide_records),
                                             "scope": "source and text hashes, unique keys, counts, shooting limits, points identity, printed per-game column"},
              "guide_printed_totals": {"status": "passed" if all(d["within_tolerance"] for d in printed) else "failed",
                                       "discrepancies": printed},
              "bbref_hashes_and_integrity": {"status": "passed", "records": len(totals),
                                             "scope": "manifest hashes, one row per player, counts, shooting limits, points identity"},
              "bbref_traded_combined_rows": {"status": "passed" if not traded_bad else "failed",
                                             "checked": len(snapshot["traded"]), "mismatched": traded_bad},
              "guide_vs_bbref": {"status": "passed" if all(r["status"] != "mismatch" for r in guide_rows) else "failed",
                                 "counts": {s: sum(r["status"] == s for r in guide_rows)
                                            for s in sorted({r["status"] for r in guide_rows})}},
              "gamelogs_vs_totals": {"status": "passed" if all(r["status"] == "match" for r in log_rows) else "failed",
                                     "checked": len(log_rows),
                                     "max_minutes_gap": max(abs(r["minutes_gap"]) for r in log_rows)},
              "decomposition_identity": {"status": "passed"},
              "independent_methods_review": {"status": "pending", "task": "PJ-04"}}}
    qa["all_data_checks_passed"] = all(c["status"] == "passed" for k, c in qa["checks"].items()
                                       if k != "independent_methods_review")

    results = {
        "status": "analysis_v2_pending_methods_review",
        "method": {"specification": "METHOD.md", "regular_minutes_min": REGULAR_MINUTES,
                   "playoff_minutes_thresholds": list(THRESHOLDS), "peer_set_b_min_ppg": PEER_B_PPG,
                   "first_season": FIRST_SEASON, "last_season": LAST_SEASON},
        "sources": {"media_guides": SOURCES, "bbref_manifest_sha256": snapshot["manifest_sha256"]},
        "subjects": subjects, "season_sets": season_sets, "comparison": comparison,
        "benchmark": bench, "benchmark_context": context, "peers_primary_threshold": peers,
        "exploratory": exploratory(bench, peers),
        "variability": variability(logs, subject_pairs),
        "series_" + CASE_SEASON.replace("-", "_"): series(logs, CASE_SEASON),
        "reconciliation": {"guide_vs_bbref": guide_rows, "gamelogs_vs_totals": log_rows},
        "guide_pilot": guide_pilot(guide_records)}
    coverage_out = {"exposure_classes": coverage, "bbref_seasons": seasons,
                    "guide_coverage": {k: list(v) for k, v in GUIDE_COVERAGE.items()},
                    "game_log_seasons": sorted("%s %s" % key for key in logs),
                    "note": "Exposure classes are computed from the snapshot. Only 'paired' seasons enter rates; "
                            "missing is never zero."}
    return results, coverage_out, qa


# ---- readable summary ----------------------------------------------------------

def fmt(value, digits=1, sign=False):
    if value is None:
        return "—"
    return ("%+.*f" if sign else "%.*f") % (digits, value)


def findings(results, qa):
    out = ["# Playoff Jimmy: analysis v2 findings", "",
           "Status: generated from frozen inputs; **independent methods review (PJ-04) pending**. "
           "Descriptive scoring comparisons; nothing here is a verified claim yet.", "",
           "Data checks: %s. Source of truth: `results.json`." %
           ("all passed" if qa["all_data_checks_passed"] else "**FAILED — see qa.json**"), ""]
    for name in SUBJECTS:
        out += ["## %s by season" % name.title(), "",
                "| Season | Exposure | Playoff G / min | PPG reg → PO | MPG reg → PO | Pts/36 reg → PO | Δ/36 | "
                "PPG Δ: minutes / rate | TSA/36 reg → PO | TS reg → PO |",
                "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for row in results["subjects"][name]:
            m = row.get("measures")
            if not m:
                out.append("| %s | %s | | | | | | | | |" % (row["season"], row["exposure"].replace("_", " ")))
                continue
            a, b, d = m["regular"], m["playoffs"], m["ppg_decomposition"]
            out.append("| %s | paired | %d / %d | %s → %s | %s → %s | %s → %s | %s | %s / %s | %s → %s | %s → %s |" % (
                row["season"], m["playoff_games"], m["playoff_minutes"], fmt(a["ppg"]), fmt(b["ppg"]),
                fmt(a["mpg"]), fmt(b["mpg"]), fmt(a["points_per_36"]), fmt(b["points_per_36"]),
                fmt(m["delta_points_per_36"], sign=True), fmt(d["minutes_component"], sign=True),
                fmt(d["rate_component"], sign=True), fmt(a["tsa_per_36"]), fmt(b["tsa_per_36"]),
                fmt(a["approx_ts"], 3), fmt(b["approx_ts"], 3)))
        out.append("")
    out += ["## Season sets (playoff-minute-weighted)", "",
            "| Set | Player | Seasons | Playoff min | Actual − expected pts | Excess /36 | Equal-season mean Δ/36 |",
            "|---|---|---:|---:|---:|---:|---:|"]
    for set_name, block in results["season_sets"].items():
        for name in SUBJECTS:
            s = block[name]
            out.append("| %s | %s | %d | %d | %s | %s | %s |" % (set_name, name.title(), s["n_seasons"],
                       s["playoff_minutes"], fmt(s["excess_points"], sign=True), fmt(s["excess_per_36"], 2, True),
                       fmt(s["equal_season_mean_delta_per_36"], 2, True)))
    leader = results["comparison"]["leader_in_every_set"]
    out += ["", "Same leader in all three sets: %s." % (leader.title() if leader else "no — no 'who rises more' statement"), ""]
    ctx = results["benchmark_context"]
    out += ["## Peer benchmark", "",
            "Eligible player-seasons 2011–12 to 2025–26 (≥ %d regular-season minutes): median change %s per 36 at "
            "≥ 100 playoff minutes (n = %d; %.0f%% below zero); %s at ≥ 200 (n = %d)." % (
                REGULAR_MINUTES, fmt(ctx["100"]["median_delta_per_36"], 2, True), ctx["100"]["n_player_seasons"],
                100 * ctx["100"]["share_below_zero"], fmt(ctx["200"]["median_delta_per_36"], 2, True),
                ctx["200"]["n_player_seasons"]), ""]
    for name in SUBJECTS:
        b = results["benchmark"][name]
        out += ["### %s" % name.title(), "",
                "| Season | Δ/36 | Peers (A, ≥100) | Peer median | Percentile | Wording |", "|---|---:|---:|---:|---:|---|"]
        for r in b["per_season"]["A_100"]:
            out.append("| %s | %s | %s | %s | %s | %s |" % (
                r["season"], fmt(r["delta_points_per_36"], sign=True), r["peer_n"] if r["eligible"] else "not eligible",
                fmt(r["peer_median"], sign=True), fmt(r["percentile"], 0), r["wording"] or "—"))
        out += ["", "| Rule | Eligible seasons | Pooled excess /36 | Minute-weighted peer median | Seasons above median | Met |",
                "|---|---:|---:|---:|---:|---|"]
        for key, c in b["career"].items():
            out.append("| %s | %d | %s | %s | %s | %s |" % (
                key.replace("_", ", ≥"), c["n_eligible_seasons"], fmt(c.get("pooled_excess_per_36"), 2, True),
                fmt(c.get("minute_weighted_peer_median"), 2, True), c.get("seasons_above_peer_median", "—"),
                "yes" if c["condition_met"] else "no"))
        out += ["", "Pre-registered per-minute 'real' rule met (all four): **%s**." %
                ("yes" if b["real_per_minute_rule_met"] else "no"), ""]
    ex = results["exploratory"]
    out += ["## Exploratory (not pre-registered)", "", ex["label"], "",
            "| Player | Eligible runs | Runs above peer median | Chance if coin flips | Mean percentile |",
            "|---|---:|---:|---:|---:|"]
    for name, c in ex["season_count_check"].items():
        out.append("| %s | %d | %d | %s | %s |" % (name.title(), c["n_eligible_seasons"], c["seasons_above_peer_median"],
                                                  fmt(c["one_sided_p"], 3), fmt(c["mean_percentile"], 0)))
    out += ["", "Career edge = pooled per-36 change minus the minute-weighted peer median, over each player's eligible runs.", "",
            "| Players with at least | Players | Median edge | Butler edge (percentile) | Murray edge (percentile) |",
            "|---|---:|---:|---:|---:|"]
    for c in ex["career_edge"]:
        cells = []
        for name in SUBJECTS:
            e = c["subjects"].get(name)
            cells.append("%s (%s)" % (fmt(e["edge_per_36"], 2, True), fmt(e["percentile"], 0)) if e else "not included")
        out.append("| %d runs | %d | %s | %s | %s |" % (c["min_eligible_runs"], c["n_players"],
                                                       fmt(c["median_edge_per_36"], 2, True), cells[0], cells[1]))
    out += [""]
    out += ["## Variability reference", "",
            "Playoff points per 36 against every same-length stretch of that season's regular-season games "
            "(minutes to the second). Not a significance test.", "",
            "| Player | Season | k | Playoff /36 | Stretches | 5th–95th pct of stretches | Playoff run's percentile |",
            "|---|---|---:|---:|---:|---:|---:|"]
    for v in results["variability"]:
        q = v["window_quantiles"]
        out.append("| %s | %s | %d | %s | %d | %s–%s | %s |" % (v["player"].title(), v["season"], v["playoff_games"],
                   fmt(v["playoff_points_per_36"]), v["n_windows"], fmt(q["p05"]), fmt(q["p95"]),
                   fmt(v["window_percentile_of_playoff_run"], 0)))
    out += ["", "## 2022–23 playoffs by series", "",
            "| Player | Round | Opponent | G | PPG | MPG | Pts/36 | TS |", "|---|---:|---|---:|---:|---:|---:|---:|"]
    for name, block in results["series_2022_23"].items():
        for s in block["series"]:
            out.append("| %s | %d | %s | %d | %s | %s | %s | %s |" % (name.title(), s["round"], s["opponent"], s["games"],
                       fmt(s["ppg"]), fmt(s["mpg"]), fmt(s["points_per_36"]), fmt(s["approx_ts"], 3)))
    checks = qa["checks"]
    out += ["", "## Checks", "",
            "- Media guide vs Basketball-Reference: %s." % ", ".join("%s %d" % (k.replace("_", " "), v)
                                                                for k, v in checks["guide_vs_bbref"]["counts"].items()),
            "- Game logs vs season totals: %d tables, largest minutes gap %.2f." % (
                checks["gamelogs_vs_totals"]["checked"], checks["gamelogs_vs_totals"]["max_minutes_gap"]),
            "- Traded players: %d combined rows equal the sum of their team rows." % checks["bbref_traded_combined_rows"]["checked"],
            "- Printed guide totals vs sum of season rows: %s." % ("; ".join(
                "%s %s %s %d vs printed %d (%s)" % (d["player"].title(), d["phase"], d["field"], d["sum_of_rows"],
                                                    d["printed_total"], "within tolerance" if d["within_tolerance"] else "FAILED")
                for d in checks["guide_printed_totals"]["discrepancies"]) or "all equal"), "",
            "## Limits", "",
            "Dividing by minutes does not control for opponents, health, role, pace or workload. The benchmark says how "
            "unusual a change is among high-minute players, not why. TS uses the 0.44 approximation. No claim here is "
            "verified until the PJ-04 review."]
    return "\n".join(out) + "\n"


def write(path, payload):
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=ROOT / "analysis")
    args = parser.parse_args(argv)
    results, coverage, qa = analyze()
    args.out.mkdir(parents=True, exist_ok=True)
    write(args.out / "results.json", results)
    write(args.out / "coverage.json", coverage)
    write(args.out / "qa.json", qa)
    (args.out / "FINDINGS.md").write_text(findings(results, qa))
    print("Wrote analysis v2 to %s. Data checks: %s. Methods review pending." %
          (args.out, "passed" if qa["all_data_checks_passed"] else "FAILED"))
    return 0 if qa["all_data_checks_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
