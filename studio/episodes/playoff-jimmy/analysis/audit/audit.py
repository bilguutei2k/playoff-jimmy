"""Read-only statistical audit of the locked episode, with reproducible evidence.

Run with Python 3.9+: python3 -B analysis/audit/audit.py
Only files in analysis/audit/ are written. No imports from the production
analysis, parser, verifier, or scene exporter. The HTML parser and rational
arithmetic helpers come from the separately authored overnight recheck,
preserved in claim_rederivation.py with its original SHA-256.
"""

from collections import Counter, defaultdict
from fractions import Fraction as F
from hashlib import sha256
from itertools import groupby
from pathlib import Path
from statistics import median
import gzip
import json
import math
import re
import sys

import claim_rederivation as independent

EPISODE = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
RESULTS = json.loads((EPISODE / "analysis/results.json").read_text())
CLAIMS = json.loads((EPISODE / "CLAIMS.json").read_text())["claims"]
CHECKS = Counter()
FAILURES = []
SOURCE_NOTES = []
FIELDS = ("games games_started mp fg fga fg3 fg3a fg2 fg2a ft fta orb drb trb ast stl blk tov pf pts").split()


def normal(v):
    if isinstance(v, F):
        return float(v)
    if isinstance(v, dict):
        return {str(k): normal(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [normal(x) for x in v]
    return v


def check(group, label, actual, expected, tolerance=1e-9):
    CHECKS[group] += 1
    actual, expected = normal(actual), normal(expected)
    if type(expected) in (float, int) and type(actual) in (float, int):
        ok = math.isfinite(actual) and math.isfinite(expected) and abs(actual - expected) <= tolerance * max(1, abs(expected))
    else:
        ok = actual == expected
    if not ok:
        FAILURES.append({"group": group, "label": label, "stored_or_observed": actual, "independent_or_expected": expected})


def resolve(tree, path):
    # Separate key resolver: bracket selectors must match one and only one row.
    segments = re.findall(r"([^.\[\]]+)(\[[^\]]+\])?", path)
    for field, bracket in segments:
        tree = tree[field]
        if bracket:
            query = bracket[1:-1]
            if query.isdecimal():
                tree = tree[int(query)]
            else:
                terms = [term.split("=", 1) for term in query.split(",")]
                hits = [row for row in tree if all(str(row.get(k)) == v for k, v in terms)]
                if len(hits) != 1:
                    raise ValueError((path, query, len(hits)))
                tree = hits[0]
    return tree


def compare_fields(group, stored, expected, prefix):
    for k, v in expected.items():
        check(group, prefix + "." + k, stored.get(k, "MISSING"), v)


def label(year):
    return f"{year-1}-{year%100:02d}"


def source_checks():
    manifest_file = EPISODE / "data/bbref-manifest.json"
    manifest = json.loads(manifest_file.read_text())
    expected_ids = {f"totals/season-{y}" for y in range(2012, 2027)}
    for page in manifest["pages"]:
        data = gzip.decompress((EPISODE / page["path"]).read_bytes())
        check("source_integrity", page["id"] + ".hash", sha256(data).hexdigest(), page["sha256"])
        check("source_integrity", page["id"] + ".bytes", len(data), page["bytes"])
    check("source_integrity", "15 season pages", {p["id"] for p in manifest["pages"] if p["id"].startswith("totals/")}, expected_ids)
    check("source_integrity", "manifest digest", RESULTS["sources"]["bbref_manifest_sha256"], sha256(manifest_file.read_bytes()).hexdigest())
    digest = sha256((EPISODE / "analysis/results.json").read_bytes()).hexdigest()
    for claim in CLAIMS:
        check("source_integrity", claim["id"] + ".results_hash", claim["results_sha256"], digest)
        for path, expected in claim["input_hashes"].items():
            check("source_integrity", claim["id"] + "." + path, sha256((EPISODE / path).read_bytes()).hexdigest(), expected)
    for source in json.loads((EPISODE / "data/media-guide-manifest.json").read_text())["sources"]:
        path = EPISODE / "data/raw" / (source["id"] + ".pdf")
        check("source_integrity", source["id"], sha256(path.read_bytes()).hexdigest(), source["sha256"])
    return manifest, digest


def load_seasons():
    full, paired, counts = {}, {}, Counter()
    for year in range(2012, 2027):
        path = EPISODE / f"data/raw/bbref/totals/season-{year}.html.gz"
        phases = {}
        for phase, table_id in [("regular", "totals_stats"), ("playoffs", "totals_stats_post")]:
            groups = defaultdict(list)
            for row in independent.table_rows(path, table_id):
                if not row.get("player_id"):
                    continue
                counts["source_player_rows"] += 1
                data = {field: int(row[field] or 0) for field in FIELDS}
                groups[row["player_id"]].append((row, data))
                where = f"{year}.{phase}.{row['player_id']}.{row['team_name_abbr']}"
                check("source_row_identities", where + ".nonnegative", all(v >= 0 for v in data.values()), True)
                for made, attempted in [("fg", "fga"), ("fg3", "fg3a"), ("fg2", "fg2a"), ("ft", "fta"), ("games_started", "games")]:
                    check("source_row_identities", where + "." + made, data[made] <= data[attempted], True)
                for total, parts in [("pts", 2*data["fg"]+data["fg3"]+data["ft"]), ("trb", data["orb"]+data["drb"]), ("fg", data["fg2"]+data["fg3"]), ("fga", data["fg2a"]+data["fg3a"])]:
                    check("source_row_identities", where + ".identity." + total, data[total], parts, 0)
            chosen = {}
            for pid, entries in groups.items():
                aggregate = [e for e in entries if re.fullmatch(r"(?:\d+TM|TOT)", e[0]["team_name_abbr"])]
                check("aggregate_selection", f"{year}.{phase}.{pid}.unique", len(aggregate) if aggregate else len(entries), 1, 0)
                row, data = aggregate[0] if aggregate else entries[0]
                if aggregate:
                    counts["combined_rows"] += 1
                    for field in FIELDS:
                        check("aggregate_sums", f"{year}.{phase}.{pid}.{field}", data[field], sum(e[1][field] for e in entries if e is not aggregate[0]), 0)
                chosen[pid] = {**data, "name": row["name_display"], "team": row["team_name_abbr"]}
            phases[phase] = chosen
        full[year] = phases
        paired[year] = []
        for pid in sorted(phases["regular"].keys() & phases["playoffs"].keys()):
            a, b = phases["regular"][pid], phases["playoffs"][pid]
            if a["mp"] > 0 and b["mp"] > 0:
                def total(row):
                    return independent.Totals(row["name"], *(row[k] for k in ("games", "mp", "pts", "fga", "fta")))
                paired[year].append(independent.Season(year, pid, total(a), total(b)))
    return full, paired, counts


def rates(row):
    g, m, p = row.games, row.mp, row.pts
    tsa = row.fga + F(11, 25)*row.fta
    return {"ppg": F(p, g), "mpg": F(m, g), "points_per_36": F(36*p, m), "tsa_per_36": 36*tsa/m, "approx_ts": F(p, 2)/tsa if tsa else None}


def numeric_checks(paired):
    eligible = {t: {year: [s for s in rows if s.eligible(t)] for year, rows in paired.items()} for t in (100, 200)}
    subjects = {name: [s for rows in paired.values() for s in rows if s.player == pid] for name, pid in independent.SUBJECTS.items()}
    for t, seasons in eligible.items():
        deltas = [s.delta for rows in seasons.values() for s in rows]
        compare_fields("benchmark_context", RESULTS["benchmark_context"][str(t)], {"n_player_seasons": len(deltas), "median_delta_per_36": median(deltas), "share_below_zero": F(sum(d < 0 for d in deltas), len(deltas))}, str(t))
    for year, seasons in eligible[100].items():
        stored = {p["player"]: p for p in RESULTS["peers_primary_threshold"][label(year)]}
        check("peer_population", label(year), sorted(stored), sorted(s.player for s in seasons))
        for s in seasons:
            compare_fields("peer_population", stored[s.player], {"regular_ppg": s.regular.ppg, "regular_points_per_36": 36*s.regular.rate, "regular_tsa_per_36": s.regular.shot_volume, "regular_minutes": s.regular.mp, "playoff_minutes": s.playoffs.mp, "delta_points_per_36": s.delta}, label(year)+"."+s.player)
    for name, seasons in subjects.items():
        stored_seasons = {row["season"]: row for row in RESULTS["subjects"][name] if row.get("measures")}
        check("subject_measures", name + ".paired", sorted(stored_seasons), sorted(label(s.year) for s in seasons))
        for s in seasons:
            key = name+"."+label(s.year)
            stored = stored_seasons[label(s.year)]["measures"]
            r, p = s.regular, s.playoffs
            rr, pr = rates(r), rates(p)
            for phase, measures in [("regular", rr), ("playoffs", pr)]:
                compare_fields("subject_measures", stored[phase], measures, key+"."+phase)
            compare_fields("subject_measures", stored, {"regular_games": r.games, "regular_minutes": r.mp, "playoff_games": p.games, "playoff_minutes": p.mp, "playoff_points": p.pts, "delta_points_per_36": s.delta, "delta_ppg": p.ppg-r.ppg, "expected_playoff_points": p.mp*r.rate, "excess_points": p.pts-p.mp*r.rate, "delta_tsa_per_36": pr["tsa_per_36"]-rr["tsa_per_36"], "delta_approx_ts": pr["approx_ts"]-rr["approx_ts"] if pr["approx_ts"] is not None else None}, key)
            compare_fields("subject_measures", stored["ppg_decomposition"], {"minutes_component": (p.mpg-r.mpg)*(p.rate+r.rate)/2, "rate_component": (p.rate-r.rate)*(p.mpg+r.mpg)/2}, key+".decomposition")
        for threshold in (100, 200):
            for peer_set in ("A", "B"):
                version = f"{peer_set}_{threshold}"
                selected = [s for s in seasons if s.eligible(threshold)]
                c = independent.career(selected, eligible[threshold], peer_set)
                c["condition_met"] = c["pooled_excess_per_36"] > c["minute_weighted_peer_median"] and 2*c["seasons_above_peer_median"] > c["n_eligible_seasons"]
                compare_fields("career_benchmarks", RESULTS["benchmark"][name]["career"][version], c, name+"."+version)
                for row in RESULTS["benchmark"][name]["per_season"][version]:
                    s = next(s for s in seasons if label(s.year) == row["season"])
                    peers = independent.peers_for(s, eligible[threshold], peer_set) if s.eligible(threshold) else []
                    pct = independent.percentile(s.delta, [p.delta for p in peers]) if peers else None
                    compare_fields("per_season_benchmarks", row, {"eligible": s.eligible(threshold), "peer_n": len(peers), "peer_median": median([p.delta for p in peers]) if peers else None, "percentile": pct, "wording": independent.wording(pct) if peers else None, "delta_points_per_36": s.delta, "excess_points": s.playoffs.pts-s.playoffs.mp*s.regular.rate, "playoff_minutes": s.playoffs.mp}, name+"."+version+"."+row["season"])
        selected = [s for s in seasons if s.eligible()]
        for version in ("rate_within_3", "rate_nearest_25", "shot_volume_within_3"):
            stored = RESULTS["exploratory"]["matched_peers"][name][version]
            c = independent.career(selected, eligible[100], matched=version)
            compare_fields("matched_peers", stored["career"], c, name+"."+version)
            compare_fields("matched_peers", stored["season_count"], {"n_eligible_seasons": len(selected), "seasons_above_peer_median": c["seasons_above_peer_median"], "one_sided_p": independent.tail(len(selected), c["seasons_above_peer_median"])}, name+"."+version)
            for row in stored["per_season"]:
                s = next(s for s in selected if label(s.year) == row["season"])
                peers = independent.peers_for(s, eligible[100], matched=version)
                compare_fields("matched_peers", row, {"peer_n": len(peers), "peer_median": median([p.delta for p in peers]), "percentile": independent.percentile(s.delta, [p.delta for p in peers]), "delta_points_per_36": s.delta}, name+"."+version+"."+row["season"])
    common = {s.year for s in subjects["butler"]} & {s.year for s in subjects["murray"]}
    for version, players in RESULTS["season_sets"].items():
        for name, seasons in subjects.items():
            selected = [s for s in seasons if version == "all_paired" or (version == "shared" and s.year in common) or (version == "min_100_playoff_minutes" and s.playoffs.mp >= 100)]
            actual = sum(s.playoffs.pts for s in selected)
            expected = sum(s.playoffs.mp*s.regular.rate for s in selected)
            compare_fields("season_sets", players[name], {"n_seasons": len(selected), "playoff_minutes": sum(s.playoffs.mp for s in selected), "actual_points": actual, "expected_points": expected, "excess_points": actual-expected, "excess_per_36": independent.pooled(selected), "equal_season_mean_delta_per_36": sum(s.delta for s in selected)/len(selected), "seasons": [label(s.year) for s in selected]}, version+"."+name)
    return eligible, subjects


def ranking_and_pilot_checks(eligible, subjects):
    grouped = defaultdict(list)
    for seasons in eligible[100].values():
        for s in seasons:
            grouped[s.player].append(s)
    edges = {}
    for pid, seasons in grouped.items():
        if len(seasons) < 6:
            continue
        c = independent.career(seasons, eligible[100])
        edges[pid] = {"name":seasons[0].playoffs.name,"player":pid,"runs":len(seasons),"playoff_minutes":c["playoff_minutes"],"pooled_delta_per_36":c["pooled_excess_per_36"],"minute_weighted_peer_median":c["minute_weighted_peer_median"],"edge_per_36":c["pooled_excess_per_36"]-c["minute_weighted_peer_median"],"runs_above_peer_median":c["seasons_above_peer_median"]}
    for cohort in RESULTS["exploratory"]["career_edge"]:
        candidates = [e for e in edges.values() if e["runs"] >= cohort["min_eligible_runs"]]
        candidates.sort(key=lambda e:(-e["edge_per_36"],e["player"]))
        prefix = str(cohort["min_eligible_runs"])
        compare_fields("career_rankings",cohort,{"n_players":len(candidates),"median_edge_per_36":median([e["edge_per_36"] for e in candidates]),"share_positive":F(sum(e["edge_per_36"]>0 for e in candidates),len(candidates))},prefix)
        for i,e in enumerate(candidates[:10]):
            compare_fields("career_rankings",cohort["top_10"][i],e,prefix+".top."+str(i))
        for name,stored in cohort["subjects"].items():
            e = edges[independent.SUBJECTS[name]].copy()
            others = [p["edge_per_36"] for p in candidates if p["player"]!=e["player"]]
            e["rank"] = 1+sum(v>e["edge_per_36"] for v in others)
            e["percentile"] = independent.percentile(e["edge_per_36"],others)
            del e["player"]
            compare_fields("career_rankings",stored,e,prefix+"."+name)
    # All paired guide seasons have identical scoring inputs to BBRef; the
    # one-minute source discrepancy is in Murray's unpaired rookie season.
    guide_subjects = {name:[s for s in rows if s.year <= (2023 if name=="butler" else 2025)] for name,rows in subjects.items()}
    common = {s.year for s in guide_subjects["butler"]}&{s.year for s in guide_subjects["murray"]}
    sets = {"butler_all_guide_seasons":guide_subjects["butler"],"murray_all_guide_seasons":guide_subjects["murray"],"butler_2016_17_to_2022_23":[s for s in guide_subjects["butler"] if s.year>=2017],**{name+"_shared":[s for s in rows if s.year in common] for name,rows in guide_subjects.items()}}
    for key,rows in sets.items():
        actual = sum(s.playoffs.pts for s in rows)
        expected = sum(s.playoffs.mp*s.regular.rate for s in rows)
        compare_fields("guide_pilot",RESULTS["guide_pilot"][key],{"n_seasons":len(rows),"playoff_minutes":sum(s.playoffs.mp for s in rows),"actual_points":actual,"expected_points":expected,"excess_points":actual-expected,"excess_per_36":independent.pooled(rows),"equal_season_mean_delta_per_36":sum(s.delta for s in rows)/len(rows),"seasons":[label(s.year) for s in rows]},key)
    full_2023 = next(r["measures"] for r in RESULTS["subjects"]["butler"] if r["season"]=="2022-23")
    compare_fields("guide_pilot",RESULTS["guide_pilot"]["butler_2022_23"],full_2023,"butler_2022_23")


def log_checks(full, manifest):
    logs, gaps = {}, []
    for page in manifest["pages"]:
        if not page["id"].startswith("gamelogs/"):
            continue
        name, year = page["id"].split("/")[1].rsplit("-", 1)
        year = int(year)
        for phase, table_id in [("regular", "player_game_log_reg"), ("playoffs", "player_game_log_post")]:
            rows = []
            for row in independent.table_rows(EPISODE / page["path"], table_id):
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row.get("date", "")) or not re.fullmatch(r"\d+:\d{2}", row.get("mp", "")):
                    continue
                minutes, seconds = map(int, row["mp"].split(":"))
                data = {k: int(row[k] or 0) for k in FIELDS if k not in ("games", "games_started", "mp")}
                rows.append({**data, "date": row["date"], "seconds": 60*minutes+seconds, "opponent": row["opp_name_abbr"]})
                check("game_log_identities", page["id"]+"."+row["date"], data["pts"], 2*data["fg"]+data["fg3"]+data["ft"], 0)
            rows.sort(key=lambda r: r["date"])
            key = (name, year, phase)
            logs[key] = rows
            check("game_log_totals", str(key)+".unique_dates", len({r["date"] for r in rows}), len(rows), 0)
            total = full[year][phase][independent.SUBJECTS[name]]
            check("game_log_totals", str(key)+".games", len(rows), total["games"], 0)
            for field in FIELDS:
                if field not in ("games", "games_started", "mp"):
                    check("game_log_totals", str(key)+"."+field, sum(r[field] for r in rows), total[field], 0)
            gap = F(sum(r["seconds"] for r in rows), 60)-total["mp"]
            gaps.append({"player": name, "year": year, "phase": phase, "minutes_gap": gap})
            check("game_log_totals", str(key)+".minute_rounding", abs(gap) <= 1, True)
    def quantile(xs, q):
        xs = sorted(xs)
        pos = q*(len(xs)-1)
        lo = int(pos)
        return xs[lo] if lo == len(xs)-1 else xs[lo]+(pos-lo)*(xs[lo+1]-xs[lo])
    windows_detail = []
    for stored in RESULTS["variability"]:
        name, year = stored["player"], int(stored["season"][:4])+1
        regular, playoffs = logs[name, year, "regular"], logs[name, year, "playoffs"]
        k = len(playoffs)
        windows = [independent.game_rate(regular[i:i+k]) for i in range(len(regular)-k+1)]
        rate = independent.game_rate(playoffs)
        compare_fields("variability", stored, {"playoff_games": k, "regular_games": len(regular), "n_windows": len(windows), "regular_points_per_36": independent.game_rate(regular), "playoff_points_per_36": rate, "window_percentile_of_playoff_run": independent.percentile(rate, windows)}, name+"."+label(year))
        compare_fields("variability", stored["window_quantiles"], {"min": min(windows), "max": max(windows), **{f"p{p:02d}": quantile(windows, F(p, 100)) for p in (5,25,50,75,95)}}, name+"."+label(year))
        windows_detail.append({"player": name, "season": label(year), "n_windows": len(windows), "min": min(windows), "max": max(windows), "playoff_rate": rate})
    for name, stored in RESULTS["series_2022_23"].items():
        compare_fields("series", stored, {phase+"_points_per_36": independent.game_rate(logs[name, 2023, log_phase]) for phase, log_phase in [("regular","regular"),("playoff","playoffs")]}, name)
        groups = [(opp,list(g)) for opp,g in groupby(logs[name, 2023, "playoffs"], key=lambda r:r["opponent"])]
        check("series", name+".rounds", len(stored["series"]), len(groups), 0)
        for round_no, (opponent, rows) in enumerate(groups,1):
            points, seconds = sum(r["pts"] for r in rows), sum(r["seconds"] for r in rows)
            tsa = sum(r["fga"]+F(11,25)*r["fta"] for r in rows)
            compare_fields("series", stored["series"][round_no-1], {"round": round_no, "opponent": opponent, "games": len(rows), "ppg": F(points,len(rows)), "mpg": F(seconds,60*len(rows)), "points_per_36": independent.game_rate(rows), "approx_ts": F(points,2)/tsa, "first_date": rows[0]["date"], "last_date": rows[-1]["date"]}, name+"."+str(round_no))
    return gaps, windows_detail


def guide_checks(full):
    summaries = []
    for name, source in RESULTS["sources"]["media_guides"].items():
        path = EPISODE / f"data/extracted/{source['id']}/page-{source['page']:03d}.txt"
        check("source_integrity", name+".guide_text", sha256(path.read_bytes()).hexdigest(), source["text_sha256"])
        phase, rows = None, defaultdict(list)
        for line in path.read_text().splitlines():
            if "NBA REGULAR SEASON" in line:
                phase = "regular"
            elif "NBA PLAYOFFS" in line or "NBA POSTSEASON STATISTICS" in line:
                phase = "playoffs"
            cols = line.replace(",", "").split()
            if not phase or not cols:
                continue
            is_year = bool(re.fullmatch(r"\d{2}(?:\d{2})?-\d{2}", cols[0]))
            if not is_year and cols[0] != "TOTALS":
                continue
            is_total = cols[0] == "TOTALS"
            values = cols[1:] if is_total else cols[2:]
            if name == "butler":
                pairs = lambda v: list(map(int,v.split("-")))
                g,gs = pairs(values[0]); fg,fga = pairs(values[2]); fg3,fg3a = pairs(values[4]); ft,fta = pairs(values[6]); orb,drb,trb = pairs(values[8]); pf,dq = pairs(values[10])
                data = dict(games=g, games_started=gs, mp=int(values[1]), fg=fg,fga=fga,fg3=fg3,fg3a=fg3a,ft=ft,fta=fta,orb=orb,drb=drb,trb=trb,ast=int(values[9]),pf=pf,stl=int(values[11]),tov=int(values[12]),blk=int(values[13]),pts=int(values[14]))
            else:
                idx = dict(games=0,games_started=1,mp=2,fg=3,fga=4,fg3=6,fg3a=7,ft=9,fta=10,orb=12,drb=13,trb=14,ast=15,stl=16,tov=17,blk=18,pts=19)
                data = {k:int(values[i]) for k,i in idx.items()}
            if is_total:
                for field, printed in data.items():
                    summed = sum(row[field] for row in rows[phase])
                    if field == "mp" and printed != summed:
                        SOURCE_NOTES.append({"type":"guide_career_minutes_rounding","player":name,"phase":phase,"sum_rows":summed,"printed":printed})
                    check("media_guide_totals", name+"."+phase+"."+field, abs(summed-printed) <= (1 if field=="mp" else 0), True)
                phase = None
                continue
            year_start = int(cols[0].split("-")[0]); year = (2000+year_start if year_start < 100 else year_start)+1
            rows[phase].append(data)
            source_row = full[year][phase].get(independent.SUBJECTS[name])
            if not data["games"]:
                check("media_guide_rows", f"{name}.{year}.{phase}.no_games", source_row is None or source_row["games"]==0, True)
                continue
            if source_row is None:
                check("media_guide_rows", f"{name}.{year}.{phase}.exists", False, True)
                continue
            for field, v in data.items():
                if field == "mp" and v != source_row[field]:
                    SOURCE_NOTES.append({"type":"guide_bbref_minutes_rounding","player":name,"year":year,"phase":phase,"guide":v,"bbref":source_row[field]})
                if field == "mp":
                    check("media_guide_rows", f"{name}.{year}.{phase}.{field}", abs(v-source_row[field]) <= 1, True)
                else:
                    check("media_guide_rows", f"{name}.{year}.{phase}.{field}", v, source_row[field], 0)
        summaries.append({"player": name, "regular_rows":len(rows["regular"]), "playoff_rows":len(rows["playoffs"])})
    return summaries


def claims_and_scenes(digest):
    rederived = json.loads((OUT / "rederived_claim_values.json").read_text())["values"]
    flat = {}
    per_claim = []
    for claim in CLAIMS:
        before = len(FAILURES)
        for item in claim["values"]:
            key = item["key"]
            derived = rederived[key]
            check("claim_unrounded_values", key, resolve(RESULTS,key), derived)
            digits = item.get("digits")
            check("claim_published_rounding", claim["id"]+"."+key, item["stated"], round(derived,digits) if digits is not None else derived)
            flat[key] = derived
        per_claim.append({"id":claim["id"],"values":len(claim["values"]),"pass":len(FAILURES)==before})
    js = (EPISODE / "scenes/data.js").read_text()
    scenes = json.loads(js.split("window.SCENE_DATA =",1)[1].strip().removesuffix(";"))
    check("scene_export", "results_digest", scenes["results_sha256"], digest)
    check("scene_export", "keys", sorted(scenes["values"]), sorted(flat))
    for key, value in flat.items():
        check("scene_export", key, scenes["values"].get(key), value)
    series = scenes["series"]
    expected = sorted(p["delta_points_per_36"] for rows in RESULTS["peers_primary_threshold"].values() for p in rows)
    check("scene_export", "league_distribution", series["league_delta_per_36_100"], expected)
    for row in series["butler_runs_A100"]:
        source = next(r for r in RESULTS["benchmark"]["butler"]["per_season"]["A_100"] if r["season"]==row["season"])
        compare_fields("scene_export",row,{"delta":source["delta_points_per_36"],"peer_median":source["peer_median"],"peers":sorted(p["delta_points_per_36"] for p in RESULTS["peers_primary_threshold"][row["season"]] if p["player"]!="butleji01")},row["season"])
    for name, groups in series["above_median"].items():
        for group, rows in groups.items():
            source = RESULTS["benchmark"][name]["per_season"]["A_100"] if group=="all" else RESULTS["exploratory"]["matched_peers"][name]["rate_within_3"]["per_season"]
            expected = [{"season":r["season"],"above":r["delta_points_per_36"]>r["peer_median"]} for r in source if r.get("eligible",True)]
            check("scene_export",name+"."+group, rows, expected)
    band = next(v for v in RESULTS["variability"] if v["player"]=="butler" and v["season"]=="2021-22")
    check("scene_export", "2022_window_band", series["variability_butler_2021_22"], {"quantiles":band["window_quantiles"],"playoff":band["playoff_points_per_36"],"n_windows":band["n_windows"]})
    for season, games in series["butler_playoff_games"].items():
        check("scene_export",season+".games",games,next(s["playoff_games"] for s in RESULTS["subjects"]["butler"] if s["season"]==season))
    return per_claim


def main():
    independent.main()
    manifest,digest = source_checks()
    full,paired,counts = load_seasons()
    eligible,subjects = numeric_checks(paired)
    ranking_and_pilot_checks(eligible,subjects)
    gaps,windows = log_checks(full,manifest)
    guides = guide_checks(full)
    claims = claims_and_scenes(digest)
    input_files = [EPISODE/"METHOD.md",EPISODE/"CLAIMS.json",EPISODE/"STORY.md",EPISODE/"analysis/results.json",EPISODE/"scenes/data.js"]
    input_files += sorted((EPISODE/"scenes").glob("*.html"))
    report = {"scope":"Independent mathematical recomputation from frozen source pages, source identities and official-guide cross-checks; not a fresh live-source census or causal validation.","checks":dict(CHECKS),"total_checks":sum(CHECKS.values()),"failures":FAILURES,"status":"pass" if not FAILURES else "fail","claims":claims,"unique_claim_values":len(json.loads((OUT/"rederived_claim_values.json").read_text())["values"]),"source_pages":len(manifest["pages"]),"source_counts":dict(counts),"source_notes":SOURCE_NOTES,"guide_tables":guides,"log_tables":len(gaps),"maximum_log_minute_gap":max(abs(x["minutes_gap"]) for x in gaps),"variability":windows,"snapshot_hashes":{str(p.relative_to(EPISODE)):sha256(p.read_bytes()).hexdigest() for p in input_files}}
    source_groups = {"source_integrity","source_row_identities","aggregate_selection","aggregate_sums","game_log_identities","game_log_totals","media_guide_rows","media_guide_totals"}
    report["claim_values_status"] = "pass" if all(c["pass"] for c in claims) else "fail"
    report["calculation_status"] = "fail" if any(f["group"] not in source_groups for f in FAILURES) else "pass"
    report["source_reconciliation_status"] = "discrepancy" if any(f["group"] in source_groups for f in FAILURES) else "pass"
    (OUT/"audit_results.json").write_text(json.dumps(normal(report),indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    print(json.dumps({k:normal(report[k]) for k in ["status","total_checks","checks","failures","source_counts","source_notes","maximum_log_minute_gap"]},indent=2))
    return bool(FAILURES)


if __name__ == "__main__":
    sys.exit(main())
