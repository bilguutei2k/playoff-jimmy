"""Check that recheck/values.json has every required key with the right type. Values are not judged here.

    python3 recheck/check_format.py recheck/values.json
"""

import json
import math
import sys

KEYS = {
    "benchmark_context.100.median_delta_per_36": "number",
    "benchmark_context.100.share_below_zero": "number",
    "benchmark_context.100.n_player_seasons": "number",
    "subjects.butler[season=2022-23].measures.regular.ppg": "number",
    "subjects.butler[season=2022-23].measures.playoffs.ppg": "number",
    "subjects.butler[season=2022-23].measures.regular.mpg": "number",
    "subjects.butler[season=2022-23].measures.playoffs.mpg": "number",
    "subjects.butler[season=2022-23].measures.delta_ppg": "number",
    "subjects.butler[season=2022-23].measures.ppg_decomposition.minutes_component": "number",
    "subjects.butler[season=2022-23].measures.ppg_decomposition.rate_component": "number",
    "subjects.butler[season=2022-23].measures.regular.points_per_36": "number",
    "subjects.butler[season=2022-23].measures.playoffs.points_per_36": "number",
    "benchmark.butler.per_season.A_100[season=2022-23].percentile": "number",
    "benchmark.butler.per_season.A_100[season=2022-23].peer_n": "number",
    "benchmark.butler.per_season.A_100[season=2022-23].wording": "string",
    "benchmark.butler.career.A_100.n_eligible_seasons": "number",
    "benchmark.butler.career.A_100.playoff_minutes": "number",
    "benchmark.butler.career.A_100.pooled_excess_per_36": "number",
    "benchmark.butler.career.A_100.minute_weighted_peer_median": "number",
    "benchmark.butler.career.A_100.seasons_above_peer_median": "number",
    "benchmark.butler.real_per_minute_rule_met": "bool",
    "exploratory.season_count_check.butler.one_sided_p": "number",
    "exploratory.season_count_check.butler.mean_percentile": "number",
    "exploratory.career_edge[min_eligible_runs=8].n_players": "number",
    "exploratory.career_edge[min_eligible_runs=8].subjects.butler.rank": "number",
    "exploratory.career_edge[min_eligible_runs=8].top_10[0].name": "string",
    "exploratory.career_edge[min_eligible_runs=8].top_10[1].name": "string",
    "exploratory.career_edge[min_eligible_runs=8].top_10[2].name": "string",
    "exploratory.career_edge[min_eligible_runs=8].top_10[3].name": "string",
    "exploratory.career_edge[min_eligible_runs=8].top_10[4].name": "string",
    "exploratory.career_edge[min_eligible_runs=8].top_10[5].name": "string",
    "exploratory.career_edge[min_eligible_runs=6].n_players": "number",
    "exploratory.career_edge[min_eligible_runs=6].subjects.butler.rank": "number",
    "exploratory.career_edge[min_eligible_runs=6].subjects.murray.rank": "number",
    "subjects.butler[season=2021-22].measures.regular.points_per_36": "number",
    "subjects.butler[season=2021-22].measures.playoffs.points_per_36": "number",
    "benchmark.butler.per_season.A_100[season=2021-22].percentile": "number",
    "variability[player=butler,season=2021-22].playoff_games": "number",
    "variability[player=butler,season=2021-22].window_percentile_of_playoff_run": "number",
    "subjects.butler[season=2017-18].measures.playoff_games": "number",
    "benchmark.butler.per_season.A_100[season=2017-18].delta_points_per_36": "number",
    "benchmark.butler.per_season.A_100[season=2017-18].percentile": "number",
    "subjects.butler[season=2020-21].measures.playoff_games": "number",
    "benchmark.butler.per_season.A_100[season=2020-21].delta_points_per_36": "number",
    "benchmark.butler.per_season.A_100[season=2020-21].percentile": "number",
    "benchmark.butler.per_season.A_100[season=2020-21].peer_n": "number",
    "series_2022_23.butler.series[round=1].opponent": "string",
    "series_2022_23.butler.series[round=1].ppg": "number",
    "series_2022_23.butler.series[round=2].ppg": "number",
    "series_2022_23.butler.series[round=3].ppg": "number",
    "series_2022_23.butler.series[round=4].opponent": "string",
    "series_2022_23.butler.series[round=4].ppg": "number",
    "series_2022_23.butler.series[round=4].points_per_36": "number",
    "series_2022_23.butler.regular_points_per_36": "number",
    "benchmark.murray.per_season.A_100[season=2018-19].percentile": "number",
    "benchmark.murray.per_season.A_100[season=2019-20].percentile": "number",
    "benchmark.murray.per_season.A_100[season=2022-23].percentile": "number",
    "benchmark.murray.per_season.A_100[season=2023-24].percentile": "number",
    "benchmark.murray.per_season.A_100[season=2024-25].percentile": "number",
    "benchmark.murray.per_season.A_100[season=2025-26].percentile": "number",
    "benchmark.murray.career.A_100.pooled_excess_per_36": "number",
    "benchmark.murray.career.A_100.minute_weighted_peer_median": "number",
    "benchmark.murray.career.A_100.seasons_above_peer_median": "number",
    "benchmark.murray.real_per_minute_rule_met": "bool",
    "season_sets.all_paired.murray.excess_per_36": "number",
    "season_sets.all_paired.butler.excess_per_36": "number",
    "season_sets.shared.murray.excess_per_36": "number",
    "season_sets.shared.butler.excess_per_36": "number",
    "season_sets.min_100_playoff_minutes.murray.excess_per_36": "number",
    "season_sets.min_100_playoff_minutes.butler.excess_per_36": "number",
    "comparison.leader_in_every_set": "string",
    "exploratory.matched_peers.butler.rate_within_3.career.n_eligible_seasons": "number",
    "exploratory.matched_peers.butler.rate_within_3.career.pooled_excess_per_36": "number",
    "exploratory.matched_peers.butler.rate_within_3.career.minute_weighted_peer_median": "number",
    "exploratory.matched_peers.butler.rate_nearest_25.career.minute_weighted_peer_median": "number",
    "exploratory.matched_peers.butler.shot_volume_within_3.career.minute_weighted_peer_median": "number",
    "exploratory.matched_peers.butler.rate_within_3.season_count.seasons_above_peer_median": "number",
    "exploratory.matched_peers.butler.rate_within_3.season_count.n_eligible_seasons": "number",
    "exploratory.matched_peers.butler.rate_within_3.season_count.one_sided_p": "number",
    "exploratory.matched_peers.murray.rate_within_3.season_count.seasons_above_peer_median": "number",
    "exploratory.matched_peers.murray.rate_within_3.season_count.n_eligible_seasons": "number",
    "exploratory.matched_peers.butler.shot_volume_within_3.season_count.seasons_above_peer_median": "number",
}


def main(path):
    data = json.load(open(path))
    values = data.get("values", {})
    problems = [key for key in KEYS if key not in values]
    for key, kind in KEYS.items():
        if key not in values:
            continue
        value = values[key]
        ok = {"number": isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value),
              "bool": isinstance(value, bool),
              "string": isinstance(value, str) or value is None}[kind]
        if not ok:
            problems.append("%s should be a %s" % (key, kind))
    if not isinstance(data.get("notes", ""), str):
        problems.append("notes should be a string")
    for problem in problems:
        print("MISSING or WRONG: " + problem)
    print("%d of %d keys present and well-formed" % (len(KEYS) - len(problems), len(KEYS)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
