"""Parse the frozen Basketball-Reference snapshot. Never fetches; see fetch_bbref.py.

Season totals use one row per player: the combined row ("2TM", "3TM" or "TOT")
for a traded player, never also his team rows. Game logs keep minutes to the
second. Every page is checked against its manifest hash before parsing.
"""

import gzip
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SUBJECTS = {"butler": "butleji01", "murray": "murraja01"}
FIELDS = {"games": "games", "minutes": "mp", "points": "pts", "fgm": "fg", "fga": "fga", "fg3m": "fg3",
          "fg3a": "fg3a", "ftm": "ft", "fta": "fta", "assists": "ast", "turnovers": "tov"}
COMBINED = ("2TM", "3TM", "4TM", "5TM", "TOT")


def season_label(end_year):
    return "%d-%02d" % (end_year - 1, end_year % 100)


def table_rows(html, table_id):
    start = html.find('id="%s"' % table_id)
    if start < 0:
        raise ValueError("Missing table " + table_id)
    body = html[start:html.find("</table>", start)]
    rows = []
    for match in re.finditer(r"<tr([^>]*)>(.*?)</tr>", body, re.S):
        cells = {key: re.sub(r"<[^>]+>", "", value).strip()
                 for key, value in re.findall(r'data-stat="([^"]+)"[^>]*>(.*?)</t[dh]>', match.group(2))}
        player = re.search(r'data-append-csv="([^"]+)"', match.group(2))
        rows.append({"partial": "partial_table" in match.group(1),
                     "player_id": player.group(1) if player else None, "cells": cells})
    return rows


def count(text):
    return int(text) if text else 0


def season_totals(html, season, phase, table_id):
    """One record per player; traded players contribute their combined row once."""
    grouped = {}
    for row in table_rows(html, table_id):
        if row["player_id"]:
            grouped.setdefault(row["player_id"], []).append(row)
    records, traded = {}, []
    for player_id, rows in grouped.items():
        combined = [r for r in rows if r["cells"].get("team_name_abbr") in COMBINED]
        teams = [r for r in rows if r["partial"]]
        if len(rows) == 1 and not combined:
            chosen, final_team = rows[0], rows[0]["cells"]["team_name_abbr"]
        elif len(combined) == 1 and len(teams) == len(rows) - 1 and teams:
            chosen, final_team = combined[0], teams[-1]["cells"]["team_name_abbr"]
            sums = {field: sum(count(t["cells"].get(stat)) for t in teams) for field, stat in FIELDS.items()}
            mismatched = {f: [count(chosen["cells"].get(FIELDS[f])), s] for f, s in sums.items()
                          if count(chosen["cells"].get(FIELDS[f])) != s}
            traded.append({"player_id": player_id, "season": season, "phase": phase,
                           "teams": [t["cells"]["team_name_abbr"] for t in teams], "mismatched_fields": mismatched})
        else:
            raise ValueError("Unexpected row pattern for %s %s %s" % (player_id, season, phase))
        cells = chosen["cells"]
        record = {field: count(cells.get(stat)) for field, stat in FIELDS.items()}
        record.update(player=player_id, name=cells.get("name_display", ""), season=season, phase=phase,
                      team=cells.get("team_name_abbr"), final_team=final_team,
                      minutes_precision="published_whole_minutes")
        records[player_id] = record
    return records, traded


def check_record(record):
    key = (record["player"], record["season"], record["phase"])
    if any(record[f] < 0 for f in FIELDS):
        raise ValueError("Negative count: " + str(key))
    if not (record["fg3m"] <= record["fgm"] <= record["fga"] and record["fg3m"] <= record["fg3a"] <= record["fga"]
            and record["ftm"] <= record["fta"]):
        raise ValueError("Shooting constraints failed: " + str(key))
    if record["points"] != 2 * record["fgm"] + record["fg3m"] + record["ftm"]:
        raise ValueError("Points identity failed: " + str(key))


def seconds(clock):
    minutes, secs = clock.split(":")
    return int(minutes) * 60 + int(secs)


def game_log(html, table_id):
    games = []
    for row in table_rows(html, table_id):
        cells = row["cells"]
        if not re.fullmatch(r"\d{4}-\d\d-\d\d", cells.get("date", "")):
            continue  # repeated header or summary row
        if not re.fullmatch(r"\d+:\d\d", cells.get("mp", "")):
            continue  # did not play, inactive or not with team
        games.append({"date": cells["date"], "team": cells.get("team_name_abbr"),
                      "opponent": cells.get("opp_name_abbr"), "home": cells.get("game_location") != "@",
                      "result": cells.get("game_result"), "seconds": seconds(cells["mp"]),
                      **{field: count(cells.get(stat)) for field, stat in FIELDS.items() if field not in ("games", "minutes")}})
    dates = [g["date"] for g in games]
    if dates != sorted(dates) or len(set(dates)) != len(dates):
        raise ValueError("Game log dates are not unique and ordered in " + table_id)
    return games


def load(root=ROOT):
    """Return the parsed snapshot after verifying every page against the manifest."""
    manifest_path = root / "data/bbref-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    pages = {}
    for page in manifest["pages"]:
        body = gzip.decompress((root / page["path"]).read_bytes())
        if hashlib.sha256(body).hexdigest() != page["sha256"]:
            raise ValueError("Snapshot hash mismatch: " + page["id"])
        pages[page["id"]] = body.decode("utf-8")
    totals, traded, playoff_teams, logs = {}, [], {}, {}
    for page_id in sorted(p for p in pages if p.startswith("totals/season-")):
        end_year = int(page_id.rsplit("-", 1)[1])
        season = season_label(end_year)
        for phase, table_id in (("regular", "totals_stats"), ("playoffs", "totals_stats_post")):
            records, moves = season_totals(pages[page_id], season, phase, table_id)
            traded.extend(moves)
            for player_id, record in records.items():
                check_record(record)
                totals[(player_id, season, phase)] = record
            if phase == "playoffs":
                playoff_teams[season] = sorted({r["team"] for r in records.values()})
    for page_id in sorted(p for p in pages if p.startswith("gamelogs/")):
        name, end_year = page_id.split("/", 1)[1].rsplit("-", 1)
        season = season_label(int(end_year))
        logs[(name, season)] = {"regular": game_log(pages[page_id], "player_game_log_reg"),
                                "playoffs": game_log(pages[page_id], "player_game_log_post")}
    return {"totals": totals, "traded": traded, "playoff_teams": playoff_teams, "game_logs": logs,
            "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            "seasons": sorted({key[1] for key in totals})}
