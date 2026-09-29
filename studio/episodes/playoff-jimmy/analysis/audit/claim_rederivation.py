# Preserved from the independently authored overnight recheck; only output location changed.
# Original SHA-256: fd9b886c0f3157e62e913c61c692fd1b011285ba28e95889da94332c11949524
"""Independently derive RECHECK.md values from this checkout; stdlib only.

Run from any working directory: python3 -B recheck/code/run.py
No network, Git, external data, or third-party imports are used.
"""

from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction as F
import gzip
from html.parser import HTMLParser
from itertools import groupby
import json
from math import comb
from pathlib import Path
import re
import runpy
from statistics import median


ROOT = Path(__file__).resolve().parents[2]
SUBJECTS = {"butler": "butleji01", "murray": "murraja01"}


class Rows(HTMLParser):
    """Parse body rows, joining text across nested tags and decoding entities."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self.row = None
        self.cell = None
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tr":
            assert self.row is None
            self.row = {}
        if self.row is not None:
            if "data-append-csv" in attrs:
                self.row["player_id"] = attrs["data-append-csv"]
            if tag in ("td", "th"):
                self.cell = attrs.get("data-stat")
                self.parts = []

    def handle_data(self, data):
        if self.cell is not None:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            assert self.cell not in self.row
            self.row[self.cell] = "".join(self.parts).strip()
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def table_rows(path, table_id):
    with gzip.open(path, "rt", encoding="utf-8") as source:
        html = source.read()
    # Extract before parsing so tables inside HTML comments are included too.
    tables = re.findall(
        r'<table\b[^>]*\bid="' + re.escape(table_id) + r'"[^>]*>(.*?)</table>',
        html, re.S,
    )
    assert len(tables) == 1, (path, table_id, len(tables))
    bodies = re.findall(r"<tbody\b[^>]*>(.*?)</tbody>", tables[0], re.S)
    assert len(bodies) == 1, (path, table_id)
    parser = Rows()
    parser.feed(bodies[0])
    parser.close()
    return parser.rows


@dataclass(frozen=True)
class Totals:
    name: str
    games: int
    mp: int
    pts: int
    fga: int
    fta: int

    @property
    def rate(self):
        return F(self.pts, self.mp)

    @property
    def ppg(self):
        return F(self.pts, self.games)

    @property
    def mpg(self):
        return F(self.mp, self.games)

    @property
    def shot_volume(self):
        return 36 * (self.fga + F(44, 100) * self.fta) / self.mp


def totals(path, table_id):
    grouped = defaultdict(list)
    for row in table_rows(path, table_id):
        if "player_id" in row:
            grouped[row["player_id"]].append(row)
    result = {}
    for player, rows in grouped.items():
        combined = [r for r in rows if re.fullmatch(r"\d+TM", r["team_name_abbr"])]
        if combined:
            assert len(combined) == 1, (path, player)
            row = combined[0]
            # Confirm that the chosen aggregate really represents the stints.
            stints = [r for r in rows if r is not row]
            for field in ("games", "mp", "pts", "fga", "fta"):
                assert int(row[field]) == sum(int(r[field]) for r in stints), (
                    path, player, field)
        else:
            assert len(rows) == 1, (path, player, "no unique aggregate")
            row = rows[0]
        result[player] = Totals(row["name_display"], *(
            int(row[k]) for k in ("games", "mp", "pts", "fga", "fta")))
    assert result
    return result


@dataclass(frozen=True)
class Season:
    year: int
    player: str
    regular: Totals
    playoffs: Totals

    @property
    def delta(self):
        return 36 * (self.playoffs.rate - self.regular.rate)

    def eligible(self, threshold=100):
        return self.regular.mp >= 1500 and self.playoffs.mp >= threshold


def percentile(value, peers):
    assert peers
    return 100 * F(2 * sum(p < value for p in peers) + sum(p == value for p in peers),
                   2 * len(peers))


def wording(p):
    if p < 25:
        return "below typical"
    if p <= 75:
        return "typical"
    if p < 90:
        return "above typical"
    return "exceptional"


def tail(n, k):
    return F(sum(comb(n, j) for j in range(k, n + 1)), 2 ** n)


def pooled(seasons):
    minutes = sum(s.playoffs.mp for s in seasons)
    assert minutes > 0
    return 36 * sum(s.playoffs.pts - s.playoffs.mp * s.regular.rate
                    for s in seasons) / minutes


def peers_for(subject, eligible, peer_set="A", matched=None):
    peers = [s for s in eligible[subject.year] if s.player != subject.player]
    if peer_set == "B":
        peers = [s for s in peers if s.regular.ppg >= 20]
    if matched == "rate_within_3":
        peers = [s for s in peers if abs(36 * (s.regular.rate - subject.regular.rate)) <= 3]
    elif matched == "rate_nearest_25":
        peers = sorted(peers, key=lambda s: (
            abs(s.regular.rate - subject.regular.rate), s.player))[:25]
    elif matched == "shot_volume_within_3":
        peers = [s for s in peers if abs(s.regular.shot_volume - subject.regular.shot_volume) <= 3]
    assert peers, (subject.player, subject.year, peer_set, matched)
    return peers


def career(seasons, eligible, peer_set="A", matched=None):
    assert seasons
    medians = [median([p.delta for p in peers_for(s, eligible, peer_set, matched)])
               for s in seasons]
    minutes = sum(s.playoffs.mp for s in seasons)
    return {
        "n_eligible_seasons": len(seasons),
        "playoff_minutes": minutes,
        "pooled_excess_per_36": pooled(seasons),
        "minute_weighted_peer_median": sum(s.playoffs.mp * m for s, m in zip(seasons, medians)) / minutes,
        "seasons_above_peer_median": sum(s.delta > m for s, m in zip(seasons, medians)),
    }


def games(year, phase):
    path = ROOT / f"data/raw/bbref/gamelogs/butler-{year}.html.gz"
    played = []
    for row in table_rows(path, f"player_game_log_{phase}"):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row.get("date", "")):
            continue
        if not re.fullmatch(r"\d+:\d{2}", row.get("mp", "")):
            continue
        minutes, seconds = map(int, row["mp"].split(":"))
        assert 0 <= seconds < 60
        played.append({"date": row["date"], "seconds": 60 * minutes + seconds,
                       "pts": int(row["pts"]), "opponent": row["opp_name_abbr"]})
    played.sort(key=lambda g: g["date"])
    assert played and len({g["date"] for g in played}) == len(played)
    return played


def game_rate(run):
    return F(36 * 60 * sum(g["pts"] for g in run), sum(g["seconds"] for g in run))


NOTES = """All computations use only the supplied checkout, including the 2025-26 pages as supplied. Season end years 2012 through 2026 are inclusive. Totals-table integer minutes are authoritative for measures, eligibility, benchmarks, career edges and season sets; game-log seconds are used only for the explicitly requested variability and series calculations. A missing playoff row or nonpositive minutes does not make a paired season. Combined nTM rows replace all team stints, independently in each phase. Table-body text is joined across nested tags; entities are decoded; repeated headers and non-player rows are ignored. Names retain the first eligible playoff table's displayed spelling, with outer whitespace stripped.

Matched-peer definitions do not explicitly restate a base universe: 'like the career block' is interpreted as peer set A at 100 playoff minutes and 1,500 regular minutes for both the subject and peers. 'Within 3' includes the endpoints. Nearest 25 means up to 25 available eligible other players, sorted by absolute regular points-per-36 distance then player id. No selected peer set is empty; no season is dropped for matching. Peer set B applies the unrounded 20-ppg restriction only to peers, not to the subject; subject eligibility still uses the stated minutes thresholds. Each 100/200 version rebuilds both subject eligibility and peer eligibility. All medians are ordinary unweighted medians within each season (mean of the two middle observations for even counts), then weighted by the subject's playoff minutes across seasons. Career-edge rankings use only players meeting that ranking's minimum eligible-season count, with exact ties sharing rank and player-id ordering used only for the displayed top list.

Game logs are restricted to the specified regular/playoff tables, so separate play-in tables are excluded. Games require both a date and numeric mm:ss, are sorted chronologically, and omit headers/DNP rows. Consecutive regular-game windows overlap, advance one played game at a time, and can span calendar gaps or missed games. Consecutive playoff opponents define rounds among played games. Seconds are summed as integers before conversion to minutes. Season-set shared means the intersection of positive-minute paired seasons, with no regular-minutes eligibility floor; min_100_playoff_minutes likewise has no regular-minutes floor. A leader must be strictly higher in every set; otherwise the value is null, as permitted by the checker despite its string label.

Arithmetic is exact rational arithmetic, including 0.44 = 11/25, until final JSON conversion to full-precision Python floats; no presentation rounding or approximate equality tolerance is applied. Thus equality, strict comparisons, inclusive matching boundaries and ties follow the mathematical definitions without intermediate floating-point noise. Binomial tails include k through n. Only keys requested by check_format.py are emitted; other quantities are calculated internally as needed."""


def main():
    paired = {}
    all_totals = {}
    for year in range(2012, 2027):
        path = ROOT / f"data/raw/bbref/totals/season-{year}.html.gz"
        regular = totals(path, "totals_stats")
        playoffs = totals(path, "totals_stats_post")
        all_totals[year] = regular, playoffs
        paired[year] = [Season(year, p, regular[p], playoffs[p])
                        for p in sorted(regular.keys() & playoffs.keys())
                        if regular[p].mp > 0 and playoffs[p].mp > 0]
    eligible = {t: {y: [s for s in seasons if s.eligible(t)] for y, seasons in paired.items()}
                for t in (100, 200)}
    values = {}

    def put(prefix, mapping):
        for key, value in mapping.items():
            full_key = prefix + "." + key
            assert full_key not in values, full_key
            values[full_key] = value

    context = [s.delta for seasons in eligible[100].values() for s in seasons]
    put("benchmark_context.100", {
        "median_delta_per_36": median(context),
        "share_below_zero": F(sum(d < 0 for d in context), len(context)),
        "n_player_seasons": len(context),
    })
    subjects = {}
    for name, player in SUBJECTS.items():
        start = 2012 if name == "butler" else 2017
        subjects[name] = [s for y, seasons in paired.items() if y >= start
                          for s in seasons if s.player == player]
        for s in subjects[name]:
            label = f"{s.year - 1}-{s.year % 100:02d}"
            r, p = s.regular, s.playoffs
            measures = {"regular.ppg": r.ppg, "playoffs.ppg": p.ppg,
                        "regular.mpg": r.mpg, "playoffs.mpg": p.mpg,
                        "regular.points_per_36": 36 * r.rate,
                        "playoffs.points_per_36": 36 * p.rate,
                        "delta_ppg": p.ppg - r.ppg, "playoff_games": p.games,
                        "ppg_decomposition.minutes_component": (r.rate + p.rate) / 2 * (p.mpg - r.mpg),
                        "ppg_decomposition.rate_component": (r.mpg + p.mpg) / 2 * (p.rate - r.rate)}
            assert (measures["ppg_decomposition.minutes_component"] +
                    measures["ppg_decomposition.rate_component"] == measures["delta_ppg"])
            put(f"subjects.{name}[season={label}].measures", measures)
            if s.eligible():
                peers = peers_for(s, eligible[100])
                pct = percentile(s.delta, [p.delta for p in peers])
                put(f"benchmark.{name}.per_season.A_100[season={label}]", {
                    "percentile": pct, "wording": wording(pct), "peer_n": len(peers),
                    "delta_points_per_36": s.delta})
        seasons = [s for s in subjects[name] if s.eligible()]
        base = career(seasons, eligible[100])
        put(f"benchmark.{name}.career.A_100", base)
        pcts = [percentile(s.delta, [p.delta for p in peers_for(s, eligible[100])]) for s in seasons]
        put(f"exploratory.season_count_check.{name}", {
            "one_sided_p": tail(len(seasons), base["seasons_above_peer_median"]),
            "mean_percentile": sum(pcts) / len(pcts)})
        versions = [career([s for s in subjects[name] if s.eligible(t)], eligible[t], peer_set)
                    for t in (100, 200) for peer_set in ("A", "B")]
        values[f"benchmark.{name}.real_per_minute_rule_met"] = all(
            c["pooled_excess_per_36"] > c["minute_weighted_peer_median"] and
            2 * c["seasons_above_peer_median"] > c["n_eligible_seasons"] for c in versions)
        for matched in ("rate_within_3", "rate_nearest_25", "shot_volume_within_3"):
            c = career(seasons, eligible[100], matched=matched)
            prefix = f"exploratory.matched_peers.{name}.{matched}"
            put(prefix + ".career", c)
            put(prefix + ".season_count", {
                "seasons_above_peer_median": c["seasons_above_peer_median"],
                "n_eligible_seasons": len(seasons),
                "one_sided_p": tail(len(seasons), c["seasons_above_peer_median"])})

    by_player = defaultdict(list)
    for seasons in eligible[100].values():
        for s in seasons:
            by_player[s.player].append(s)
    edges = {}
    for player, seasons in by_player.items():
        if len(seasons) >= 6:
            c = career(seasons, eligible[100])
            weighted_delta = sum(s.playoffs.mp * s.delta for s in seasons) / c["playoff_minutes"]
            assert weighted_delta == c["pooled_excess_per_36"]
            edges[player] = weighted_delta - c["minute_weighted_peer_median"]
    for minimum in (6, 8):
        players = [p for p in edges if len(by_player[p]) >= minimum]
        players.sort(key=lambda p: (-edges[p], p))
        prefix = f"exploratory.career_edge[min_eligible_runs={minimum}]"
        values[prefix + ".n_players"] = len(players)
        for name, player in SUBJECTS.items():
            if player in players:
                values[prefix + f".subjects.{name}.rank"] = 1 + sum(edges[p] > edges[player] for p in players)
        for i, player in enumerate(players[:10]):
            values[prefix + f".top_10[{i}].name"] = by_player[player][0].playoffs.name

    logs = {(year, phase): games(year, phase) for year in (2022, 2023) for phase in ("reg", "post")}
    for (year, phase), log in logs.items():
        total = all_totals[year][phase == "post"][SUBJECTS["butler"]]
        assert len(log) == total.games
        assert sum(g["pts"] for g in log) == total.pts
        assert abs(F(sum(g["seconds"] for g in log), 60) - total.mp) <= 1
    regular, playoffs = logs[2022, "reg"], logs[2022, "post"]
    k = len(playoffs)
    windows = [game_rate(regular[i:i + k]) for i in range(len(regular) - k + 1)]
    put("variability[player=butler,season=2021-22]", {
        "playoff_games": k, "window_percentile_of_playoff_run": percentile(game_rate(playoffs), windows)})
    for round_no, (opponent, group) in enumerate(groupby(logs[2023, "post"], key=lambda g: g["opponent"]), 1):
        run = list(group)
        put(f"series_2022_23.butler.series[round={round_no}]", {
            "opponent": opponent, "ppg": F(sum(g["pts"] for g in run), len(run)),
            "points_per_36": game_rate(run)})
    values["series_2022_23.butler.regular_points_per_36"] = game_rate(logs[2023, "reg"])

    shared = set(s.year for s in subjects["butler"]) & set(s.year for s in subjects["murray"])
    leaders = []
    for label in ("all_paired", "shared", "min_100_playoff_minutes"):
        scores = {}
        for name, seasons in subjects.items():
            selected = [s for s in seasons if label == "all_paired" or
                        (label == "shared" and s.year in shared) or
                        (label == "min_100_playoff_minutes" and s.playoffs.mp >= 100)]
            scores[name] = pooled(selected)
            values[f"season_sets.{label}.{name}.excess_per_36"] = scores[name]
        leaders.append("butler" if scores["butler"] > scores["murray"] else
                       "murray" if scores["murray"] > scores["butler"] else None)
    values["comparison.leader_in_every_set"] = leaders[0] if len(set(leaders)) == 1 else None

    keys = runpy.run_path(str(ROOT / "recheck/check_format.py"))["KEYS"]
    missing = keys.keys() - values.keys()
    assert not missing, sorted(missing)
    requested = {k: float(values[k]) if isinstance(values[k], F) else values[k] for k in keys}
    destination = ROOT / "analysis/audit/rederived_claim_values.json"
    destination.write_text(json.dumps({"values": requested, "notes": NOTES},
                                     ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Computed {len(requested)} keys from {len(paired)} seasons; wrote {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
