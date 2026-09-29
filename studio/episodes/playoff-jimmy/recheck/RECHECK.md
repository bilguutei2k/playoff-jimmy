# Independent re-derivation: Playoff Jimmy claim values

You are checking another analyst's numbers without seeing them. Compute every
quantity listed in `recheck/check_format.py` (the `KEYS` table) from the raw
data in this checkout, with your own code, and write them to
`recheck/values.json`.

## Rules

- Use only the files in this checkout: `data/raw/bbref/` (gzip-compressed
  Basketball-Reference pages), `data/bbref-manifest.json`, this file and
  `recheck/check_format.py`. Do not use git history, other branches, the
  network, or anything outside this checkout.
- Write your code under `recheck/code/`, standard-library Python only, and
  make it rerunnable: `python3 recheck/code/run.py` must regenerate
  `recheck/values.json`.
- Do not edit `data/`, this file or `recheck/check_format.py`.
- Output format: `{"values": {"<key>": <value>, ...}, "notes": "<anything
  ambiguous and how you resolved it>"}`. Numbers unrounded (full floating
  precision), booleans as JSON booleans, text as strings.
- If a definition below is ambiguous, choose the most literal reading and
  say so in `notes`. Do not look for, or guess at, the other analyst's
  values.

## Data

- `data/raw/bbref/totals/season-YYYY.html.gz`: one page per NBA season,
  named by the season's end year (2012 = 2011–12, ..., 2026 = 2025–26). Each
  page holds two tables: `id="totals_stats"` (regular season) and
  `id="totals_stats_post"` (playoffs). A player's id is the
  `data-append-csv` attribute of his row. Cells are identified by
  `data-stat` (`games`, `mp` minutes, `pts`, `fga`, `fta`, `team_name_abbr`,
  `name_display`, ...). Some cells wrap their text in tags.
- A player traded during a season has a combined row (team "2TM", "3TM",
  ...) plus one row per team. Use the combined row, once.
- `data/raw/bbref/gamelogs/<name>-YYYY.html.gz`: game logs for `butler`
  (id `butleji01`) and `murray` (id `murraja01`). Tables
  `id="player_game_log_reg"` and `id="player_game_log_post"`. A game he
  played has a `date` (YYYY-MM-DD) and `mp` as minutes:seconds; other rows
  (headers, did-not-play) are not games.
- Season labels in keys look like `2022-23`.

## Definitions

- **Eligible player-season:** at least 1,500 regular-season minutes and at
  least 100 playoff minutes in the same season (the "200" variants use 200
  playoff minutes). Seasons 2011–12 to 2025–26.
- **Change per 36** for a player-season: 36 × playoff points / playoff
  minutes − 36 × regular points / regular minutes.
- **Paired season** for a subject: positive minutes in both the regular
  season and playoffs. Butler's seasons start in 2011–12, Murray's in
  2016–17; both run to 2025–26.
- **Measures** (`subjects.<name>[season=S].measures.*`): `ppg` = points /
  games; `mpg` = minutes / games; `points_per_36` = 36 × points / minutes
  (`regular.*` and `playoffs.*`); `delta_ppg` = playoff ppg − regular ppg;
  `playoff_games`. With rate r = points / minutes:
  `ppg_decomposition.minutes_component` = (r_reg + r_playoff) / 2 ×
  (mpg_playoff − mpg_reg) and `ppg_decomposition.rate_component` =
  (mpg_reg + mpg_playoff) / 2 × (r_playoff − r_reg).
- **Peers of a subject in a season (peer set A):** every other eligible
  player that season. **Peer set B:** those peers whose regular-season
  points per game (unrounded) is at least 20.0.
- **Percentile** of a value among peers: 100 × (number of peers lower + 0.5
  × number equal) / number of peers.
- **Wording** of a percentile p: below 25 "below typical"; 25 to 75
  inclusive "typical"; above 75 and below 90 "above typical"; 90 or more
  "exceptional".
- `benchmark.<name>.per_season.A_100[season=S].*`: for an eligible subject
  season, `percentile` and `wording` of his change per 36 among peer set A,
  `peer_n` the number of peers, `delta_points_per_36` his change per 36.
- **Career** (`benchmark.<name>.career.A_100.*`), over the subject's
  eligible seasons: `n_eligible_seasons`; `playoff_minutes` (sum);
  `pooled_excess_per_36` = 36 × Σ(playoff points − playoff minutes × regular
  points / regular minutes) / Σ playoff minutes;
  `minute_weighted_peer_median` = Σ(playoff minutes × median of the peers'
  change per 36) / Σ playoff minutes; `seasons_above_peer_median` = seasons
  where his change per 36 is strictly above that season's peer median.
- `benchmark.<name>.real_per_minute_rule_met`: true only if, for each of the
  four versions (peer set A or B, 100 or 200 playoff minutes, eligibility
  and peers both at that threshold), pooled excess per 36 > minute-weighted
  peer median AND seasons above the peer median > half the eligible seasons.
- `benchmark_context.100.*`: over all eligible player-seasons (100
  minutes), the `median_delta_per_36`, the `share_below_zero` (fraction with
  change per 36 < 0) and `n_player_seasons`.
- `exploratory.season_count_check.<name>.*`: with n eligible seasons and k
  above the median (peer set A, 100 minutes), `one_sided_p` = Σ over j = k
  to n of C(n, j) / 2^n, and `mean_percentile` = mean of his season
  percentiles.
- `exploratory.career_edge[min_eligible_runs=M].*`: for every player with
  at least M eligible seasons (100 minutes): edge = (minute-weighted mean of
  his change per 36) − (minute-weighted mean of his seasons' peer medians,
  peers excluding him). `n_players`; `subjects.<name>.rank` = 1 + number of
  players with a strictly higher edge; `top_10[i].name` = the i-th highest
  edge (0-based; ties broken by player id), named as in his first eligible
  season's playoff table.
- `exploratory.matched_peers.<name>.<version>.*`: like the career block,
  but each season's peers are restricted: `rate_within_3` = peers whose
  regular-season points per 36 is within 3 of his; `rate_nearest_25` = the 25
  peers nearest to his regular-season points per 36 (ties by player id);
  `shot_volume_within_3` = peers whose regular-season 36 × (FGA + 0.44 × FTA)
  / minutes is within 3 of his. Report `career.n_eligible_seasons`,
  `career.pooled_excess_per_36`, `career.minute_weighted_peer_median`,
  `season_count.seasons_above_peer_median`, `season_count.n_eligible_seasons`
  and `season_count.one_sided_p`.
- `variability[player=butler,season=2021-22].*`: from Butler's 2021–22 game
  log, k = number of playoff games he played (`playoff_games`); for every run
  of k consecutive regular-season games he played, 36 × Σ points / Σ minutes
  (minutes from mm:ss); `window_percentile_of_playoff_run` = percentile of
  his playoff 36 × Σ points / Σ minutes among those runs.
- `series_2022_23.butler.*`: from Butler's 2022–23 playoff game log, group
  consecutive games by opponent into rounds 1, 2, ...; for each round the
  `opponent` abbreviation, `ppg` and `points_per_36` (minutes from mm:ss);
  `regular_points_per_36` from his regular-season game log the same way.
- **Season sets** (`season_sets.<set>.<name>.excess_per_36`): pooled excess
  per 36 (as in the career block, no eligibility filter) over
  `all_paired` = all his paired seasons; `shared` = seasons paired for both
  subjects; `min_100_playoff_minutes` = paired seasons with at least 100
  playoff minutes. `comparison.leader_in_every_set` = the subject name
  (`butler` or `murray`) with the higher value in all three sets, else null.
