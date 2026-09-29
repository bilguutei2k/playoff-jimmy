"""Check every claim in CLAIMS.json against the results and against an independent recomputation.

    python3 analysis/verify_claims.py      # writes analysis/claims_check.json; exits 1 if any check fails

For each claim: the recorded results hash matches results.json and the recorded
analysis revision produced that file; input hashes match; each stated value
resolves in results.json and agrees with it at the stated precision; and each
value is recomputed from the raw snapshot by the code below, which deliberately
does not import bbref.py or analyze.py. Same author as the analysis (Claude),
so this is an independent code path, not an independent reviewer.
"""

import gzip
import hashlib
import json
import math
import re
import statistics
import subprocess
import sys
from pathlib import Path


EPISODE = Path(__file__).resolve().parent.parent
REPO = EPISODE.parent.parent.parent
IDS = {"butler": "butleji01", "murray": "murraja01"}
FIRST = {"butler": 2012, "murray": 2017}
YEARS = range(2012, 2027)


# ---- resolving keys such as subjects.butler[season=2022-23].measures.regular.ppg ----

def resolve(data, key):
    for part in re.findall(r"[^.\[\]]+|\[[^\]]*\]", key):
        if part.startswith("["):
            inner = part[1:-1]
            if inner.isdigit():
                data = data[int(inner)]
            else:
                conditions = dict(c.split("=", 1) for c in inner.split(","))
                matches = [item for item in data if all(str(item.get(k)) == v for k, v in conditions.items())]
                if len(matches) != 1:
                    raise KeyError("%s matched %d items" % (part, len(matches)))
                data = matches[0]
        else:
            data = data[part]
    return data


def agrees(stated, value, digits):
    if isinstance(stated, bool) or isinstance(stated, str) or digits is None:
        return stated == value
    return abs(value - stated) <= 0.5 * 10 ** -digits + 1e-9


# ---- independent recomputation from the raw pages ------------------------------------

def page(page_id):
    return gzip.decompress((EPISODE / "data/raw/bbref" / (page_id + ".html.gz")).read_bytes()).decode("utf-8")


def cells(row_html):
    return {k: re.sub(r"<[^>]+>", "", v).strip() for k, v in re.findall(r'data-stat="([^"]+)"[^>]*>(.*?)</t[dh]>', row_html)}


def rows(html, table_id):
    start = html.find('id="%s"' % table_id)
    return re.findall(r"<tr[^>]*>(.*?)</tr>", html[start:html.find("</table>", start)], re.S)


def season_tables(year):
    """First row per player: Basketball-Reference lists a traded player's combined row before his team rows."""
    html, out = page("totals/season-%d" % year), {}
    for phase, table_id in (("regular", "totals_stats"), ("playoffs", "totals_stats_post")):
        found = {}
        for row in rows(html, table_id):
            pid = re.search(r'data-append-csv="([^"]+)"', row)
            if pid and pid.group(1) not in found:
                c = cells(row)
                found[pid.group(1)] = {"name": c["name_display"], "g": int(c["games"]), "mp": int(c["mp"] or 0),
                                       "pts": int(c["pts"] or 0), "fga": int(c["fga"] or 0), "fta": int(c["fta"] or 0)}
        out[phase] = found
    return out


def label(year):
    return "%d-%02d" % (year - 1, year % 100)


def pct(value, others):
    return 100 * (sum(o < value for o in others) + 0.5 * sum(o == value for o in others)) / len(others)


def wording(p):
    return "below typical" if p < 25 else "typical" if p <= 75 else "above typical" if p < 90 else "exceptional"


def games(page_id, table_id):
    found = []
    for row in rows(page(page_id), table_id):
        c = cells(row)
        if re.fullmatch(r"\d{4}-\d\d-\d\d", c.get("date", "")) and re.fullmatch(r"\d+:\d\d", c.get("mp", "")):
            m, s = c["mp"].split(":")
            found.append({"opp": c["opp_name_abbr"], "pts": int(c["pts"] or 0), "sec": int(m) * 60 + int(s)})
    return found


def rate36(block):
    return 36 * 60 * sum(g["pts"] for g in block) / sum(g["sec"] for g in block)


def independent():
    t = {year: season_tables(year) for year in YEARS}
    delta = {}  # (year, pid, threshold) -> change per 36 for eligible player-seasons
    for year, tables in t.items():
        for pid, post in tables["playoffs"].items():
            reg = tables["regular"].get(pid)
            if reg and reg["mp"] >= 1500 and post["mp"] >= 100:
                d = 36 * post["pts"] / post["mp"] - 36 * reg["pts"] / reg["mp"]
                for threshold in (100, 200):
                    if post["mp"] >= threshold:
                        delta[(year, pid, threshold)] = d
    out = {}
    all100 = [d for (y, p, th), d in delta.items() if th == 100]
    out["benchmark_context.100.median_delta_per_36"] = statistics.median(all100)
    out["benchmark_context.100.share_below_zero"] = sum(d < 0 for d in all100) / len(all100)
    out["benchmark_context.100.n_player_seasons"] = len(all100)

    def peers(year, pid, threshold, peer_set):
        return [d for (y, p, th), d in delta.items() if y == year and th == threshold and p != pid
                and (peer_set == "A" or t[year]["regular"][p]["pts"] / t[year]["regular"][p]["g"] >= 20.0)]

    paired = {}
    for name, pid in IDS.items():
        paired[name] = {}
        for year in YEARS:
            if year < FIRST[name]:
                continue
            reg, post = t[year]["regular"].get(pid), t[year]["playoffs"].get(pid)
            if not (reg and post and reg["mp"] and post["mp"]):
                continue
            paired[name][year] = (reg, post)
            base = "subjects.%s[season=%s].measures." % (name, label(year))
            r_rate, p_rate = reg["pts"] / reg["mp"], post["pts"] / post["mp"]
            r_mpg, p_mpg = reg["mp"] / reg["g"], post["mp"] / post["g"]
            out[base + "regular.ppg"], out[base + "playoffs.ppg"] = reg["pts"] / reg["g"], post["pts"] / post["g"]
            out[base + "regular.mpg"], out[base + "playoffs.mpg"] = r_mpg, p_mpg
            out[base + "regular.points_per_36"], out[base + "playoffs.points_per_36"] = 36 * r_rate, 36 * p_rate
            out[base + "delta_ppg"] = post["pts"] / post["g"] - reg["pts"] / reg["g"]
            out[base + "ppg_decomposition.minutes_component"] = (r_rate + p_rate) / 2 * (p_mpg - r_mpg)
            out[base + "ppg_decomposition.rate_component"] = (r_mpg + p_mpg) / 2 * (p_rate - r_rate)
            out[base + "playoff_games"] = post["g"]
            key = (year, pid, 100)
            if key in delta:
                others = peers(year, pid, 100, "A")
                b = "benchmark.%s.per_season.A_100[season=%s]." % (name, label(year))
                out[b + "percentile"], out[b + "peer_n"] = pct(delta[key], others), len(others)
                out[b + "delta_points_per_36"], out[b + "wording"] = delta[key], wording(pct(delta[key], others))

        conditions, percentiles = [], []
        for peer_set in ("A", "B"):
            for threshold in (100, 200):
                seasons = [y for y in paired[name] if (y, pid, threshold) in delta]
                minutes = sum(paired[name][y][1]["mp"] for y in seasons)
                excess = sum(paired[name][y][1]["pts"] - paired[name][y][1]["mp"] * paired[name][y][0]["pts"] / paired[name][y][0]["mp"]
                             for y in seasons)
                medians = {y: statistics.median(peers(y, pid, threshold, peer_set)) for y in seasons}
                pooled = 36 * excess / minutes
                weighted = sum(paired[name][y][1]["mp"] * medians[y] for y in seasons) / minutes
                above = sum(delta[(y, pid, threshold)] > medians[y] for y in seasons)
                conditions.append(pooled > weighted and above > len(seasons) / 2)
                if (peer_set, threshold) == ("A", 100):
                    c = "benchmark.%s.career.A_100." % name
                    out[c + "n_eligible_seasons"], out[c + "playoff_minutes"] = len(seasons), minutes
                    out[c + "pooled_excess_per_36"], out[c + "minute_weighted_peer_median"] = pooled, weighted
                    out[c + "seasons_above_peer_median"] = above
                    percentiles = [pct(delta[(y, pid, 100)], peers(y, pid, 100, "A")) for y in seasons]
                    n = len(seasons)
                    out["exploratory.season_count_check.%s.one_sided_p" % name] = sum(math.comb(n, k) for k in range(above, n + 1)) / 2 ** n
                    out["exploratory.season_count_check.%s.mean_percentile" % name] = statistics.mean(percentiles)
        out["benchmark.%s.real_per_minute_rule_met" % name] = all(conditions)

    for min_runs in (6, 8):
        runs = {}
        for (y, p, th), d in delta.items():
            if th == 100:
                runs.setdefault(p, []).append(y)
        edges = {}
        for p, years in runs.items():
            if len(years) < min_runs:
                continue
            minutes = sum(t[y]["playoffs"][p]["mp"] for y in years)
            pooled = sum(delta[(y, p, 100)] * t[y]["playoffs"][p]["mp"] for y in years) / minutes
            weighted = sum(t[y]["playoffs"][p]["mp"] * statistics.median(peers(y, p, 100, "A")) for y in years) / minutes
            edges[p] = pooled - weighted
        base = "exploratory.career_edge[min_eligible_runs=%d]." % min_runs
        out[base + "n_players"] = len(edges)
        for name, pid in IDS.items():
            if pid in edges:
                out[base + "subjects.%s.rank" % name] = 1 + sum(e > edges[pid] for e in edges.values())
        ranked = sorted(edges, key=lambda p: (-edges[p], p))
        latest = {p: next(t[y]["playoffs"][p]["name"] for y in sorted(runs[p])) for p in ranked[:10]}
        for i, p in enumerate(ranked[:10]):
            out[base + "top_10[%d].name" % i] = latest[p]

    def regular(year, p, field):
        r = t[year]["regular"][p]
        return 36 * (r["pts"] if field == "rate" else r["fga"] + 0.44 * r["fta"]) / r["mp"]

    for name, pid in IDS.items():
        seasons = [y for y in paired[name] if (y, pid, 100) in delta]
        for version, field, rule in (("rate_within_3", "rate", "width"), ("rate_nearest_25", "rate", "nearest"),
                                     ("shot_volume_within_3", "volume", "width")):
            medians = {}
            for y in seasons:
                pool = sorted(p for (yy, p, th) in delta if yy == y and th == 100 and p != pid)
                mine = regular(y, pid, field)
                if rule == "width":
                    pool = [p for p in pool if abs(regular(y, p, field) - mine) <= 3.0]
                else:
                    pool = sorted(pool, key=lambda p: (abs(regular(y, p, field) - mine), p))[:25]
                medians[y] = statistics.median(delta[(y, p, 100)] for p in pool)
            minutes = sum(paired[name][y][1]["mp"] for y in seasons)
            excess = sum(paired[name][y][1]["pts"] - paired[name][y][1]["mp"] * paired[name][y][0]["pts"] / paired[name][y][0]["mp"]
                         for y in seasons)
            above, n = sum(delta[(y, pid, 100)] > medians[y] for y in seasons), len(seasons)
            base = "exploratory.matched_peers.%s.%s." % (name, version)
            out[base + "career.n_eligible_seasons"] = n
            out[base + "career.pooled_excess_per_36"] = 36 * excess / minutes
            out[base + "career.minute_weighted_peer_median"] = sum(paired[name][y][1]["mp"] * medians[y] for y in seasons) / minutes
            out[base + "season_count.seasons_above_peer_median"] = above
            out[base + "season_count.n_eligible_seasons"] = n
            out[base + "season_count.one_sided_p"] = sum(math.comb(n, k) for k in range(above, n + 1)) / 2 ** n

    reg, post = games("gamelogs/butler-2022", "player_game_log_reg"), games("gamelogs/butler-2022", "player_game_log_post")
    k = len(post)
    windows = [rate36(reg[i:i + k]) for i in range(len(reg) - k + 1)]
    out["variability[player=butler,season=2021-22].playoff_games"] = k
    out["variability[player=butler,season=2021-22].window_percentile_of_playoff_run"] = pct(rate36(post), windows)

    reg, post = games("gamelogs/butler-2023", "player_game_log_reg"), games("gamelogs/butler-2023", "player_game_log_post")
    series = []
    for g in post:
        if not series or series[-1][0]["opp"] != g["opp"]:
            series.append([])
        series[-1].append(g)
    for number, block in enumerate(series, 1):
        base = "series_2022_23.butler.series[round=%d]." % number
        out[base + "opponent"], out[base + "ppg"] = block[0]["opp"], sum(g["pts"] for g in block) / len(block)
        out[base + "points_per_36"] = rate36(block)
    out["series_2022_23.butler.regular_points_per_36"] = rate36(reg)

    def pooled_set(name, years):
        minutes = sum(paired[name][y][1]["mp"] for y in years)
        excess = sum(paired[name][y][1]["pts"] - paired[name][y][1]["mp"] * paired[name][y][0]["pts"] / paired[name][y][0]["mp"]
                     for y in years)
        return 36 * excess / minutes
    shared = sorted(set(paired["butler"]) & set(paired["murray"]))
    sets = {"all_paired": {n: sorted(paired[n]) for n in IDS}, "shared": {n: shared for n in IDS},
            "min_100_playoff_minutes": {n: [y for y in paired[n] if paired[n][y][1]["mp"] >= 100] for n in IDS}}
    leaders = set()
    for set_name, chosen in sets.items():
        values = {n: pooled_set(n, chosen[n]) for n in IDS}
        for n, value in values.items():
            out["season_sets.%s.%s.excess_per_36" % (set_name, n)] = value
        leaders.add(max(values, key=values.get))
    out["comparison.leader_in_every_set"] = leaders.pop() if len(leaders) == 1 else None
    return out


# ---- main ------------------------------------------------------------------------------

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check():
    claims = json.loads((EPISODE / "CLAIMS.json").read_text())["claims"]
    results_path = EPISODE / "analysis/results.json"
    results = json.loads(results_path.read_text())
    current = sha256(results_path)
    recomputed = independent()
    report = {"results_sha256": current, "claims": [],
              "note": "Independent code path by the same author as the analysis; not an independent reviewer."}
    for claim in claims:
        checks = {"results_hash_current": claim["results_sha256"] == current}
        shown = subprocess.run(["git", "-C", str(REPO), "show", "%s:%s" % (claim["analysis_revision"],
                                (EPISODE / claim["result_file"]).relative_to(REPO))], capture_output=True)
        checks["revision_produced_results"] = (shown.returncode == 0
                                               and hashlib.sha256(shown.stdout).hexdigest() == claim["results_sha256"])
        checks["input_hashes_match"] = all(sha256(EPISODE / path) == digest for path, digest in claim["input_hashes"].items())
        values = []
        for item in claim["values"]:
            try:
                resolved = resolve(results, item["key"])
            except (KeyError, IndexError, TypeError) as error:
                values.append({**item, "error": str(error), "ok": False})
                continue
            other = recomputed.get(item["key"], "not recomputed")
            same = (other == resolved if isinstance(resolved, (str, bool)) or resolved is None
                    else isinstance(other, (int, float)) and abs(other - resolved) <= 1e-9)
            values.append({**item, "resolved": resolved, "independent": other,
                           "stated_matches_results": agrees(item["stated"], resolved, item.get("digits")),
                           "independent_matches_results": same,
                           "ok": agrees(item["stated"], resolved, item.get("digits")) and same})
        checks["all_values_ok"] = all(v["ok"] for v in values)
        report["claims"].append({"id": claim["id"], "passed": all(checks.values()), "checks": checks, "values": values})
    report["all_passed"] = all(c["passed"] for c in report["claims"])
    return report


def main():
    report = check()
    (EPISODE / "analysis/claims_check.json").write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    for c in report["claims"]:
        failed = [k for k, ok in c["checks"].items() if not ok] + [v["key"] for v in c["values"] if not v["ok"]]
        print("%s %s%s" % (c["id"], "pass" if c["passed"] else "FAIL", ": " + "; ".join(failed) if failed else ""))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
