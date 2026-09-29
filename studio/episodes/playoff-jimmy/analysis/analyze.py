"""Reproduce an explicitly incomplete research pilot from frozen guide tables.

Pure standard library. PDF extraction is a separate optional preparation step.
Never treat missing later-season coverage as a zero-stat season.
"""

import hashlib
import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCES = {
    "butler": {"id": "heat-2023-24", "page": 66, "printed_page": "65",
               "sha256": "4ff14b44d9ad98df0899d8625f01154ad61bf205c01b526d310f28051097d701",
               "text_sha256": "0769d8aa831d2fb9a67120ee7c6668515739812c9c555978906427c021c18b22"},
    "murray": {"id": "nuggets-2025-26", "page": 57, "printed_page": "58",
               "sha256": "59f5e565ae57f46f3b76ec5749d9e6a9959cded6024c7d0409da19403782b00a",
               "text_sha256": "d3d2141414a7e6e6af9fbb29cdb41716f0869e96cf98c3912c74e8c57d5145ca"},
}


def integer(text):
    return int(text.replace(",", ""))


def parse_table(text, player):
    records, phase = [], None
    for line in text.splitlines():
        line = line.strip()
        if "NBA REGULAR SEASON" in line:
            phase = "regular"
            continue
        if line == "NBA PLAYOFFS" or "NBA POSTSEASON STATISTICS" in line:
            phase = "playoffs"
            continue
        if line.startswith("TOTALS "):
            phase = None
            continue
        if not phase:
            continue
        cells = line.split()
        if not cells:
            continue
        if player == "butler" and re.fullmatch(r"\d{2}-\d{2}", cells[0]):
            if len(cells) != 18:
                raise ValueError("Unexpected Butler row: " + line)
            fg, fga = map(integer, cells[4].split("-"))
            threes, tpa = map(integer, cells[6].split("-"))
            ft, fta = map(integer, cells[8].split("-"))
            row = {"season": "20" + cells[0], "team": cells[1],
                   "games": integer(cells[2].split("-")[0]), "minutes": integer(cells[3]),
                   "fgm": fg, "fga": fga, "fg3m": threes, "fg3a": tpa,
                   "ftm": ft, "fta": fta, "points": integer(cells[16]),
                   "assists": integer(cells[11]), "turnovers": integer(cells[14])}
        elif player == "murray" and re.fullmatch(r"\d{4}-\d{2}", cells[0]):
            if len(cells) != 23:
                raise ValueError("Unexpected Murray row: " + line)
            row = {"season": cells[0], "team": cells[1], "games": integer(cells[2]),
                   "minutes": integer(cells[4]), "fgm": integer(cells[5]),
                   "fga": integer(cells[6]), "fg3m": integer(cells[8]),
                   "fg3a": integer(cells[9]), "ftm": integer(cells[11]),
                   "fta": integer(cells[12]), "points": integer(cells[21]),
                   "assists": integer(cells[17]), "turnovers": integer(cells[19])}
        else:
            continue
        row.update(player=player, phase=phase, source_id=SOURCES[player]["id"],
                   pdf_page=SOURCES[player]["page"], printed_page=SOURCES[player]["printed_page"],
                   source_line=line, minutes_precision="published_whole_minutes")
        records.append(row)
    if not records:
        raise ValueError("No records parsed for " + player)
    return records


def validate(records):
    keys = set()
    for row in records:
        key = (row["player"], row["season"], row["phase"])
        if key in keys:
            raise ValueError("Duplicate player-season-phase: " + str(key))
        keys.add(key)
        for field in ("games", "minutes", "points", "fgm", "fga", "fg3m", "fg3a", "ftm", "fta", "assists", "turnovers"):
            if type(row[field]) is not int or row[field] < 0:
                raise ValueError("Invalid count: " + field)
        if not (row["fg3m"] <= row["fgm"] <= row["fga"] and
                row["fg3m"] <= row["fg3a"] <= row["fga"] and row["ftm"] <= row["fta"]):
            raise ValueError("Shooting constraints failed: " + str(key))
        if row["points"] != 2 * row["fgm"] + row["fg3m"] + row["ftm"]:
            raise ValueError("Points identity failed: " + str(key))
        if row["games"] == 0 and any(row[f] != 0 for f in ("minutes", "points", "fga", "fta", "assists", "turnovers")):
            raise ValueError("Nonzero counts with zero games: " + str(key))


def rates(row):
    def divide(a, b):
        return a / b if b else None
    return {"ppg": divide(row["points"], row["games"]),
            "mpg": divide(row["minutes"], row["games"]),
            "points_per_36": divide(36 * row["points"], row["minutes"]),
            "approx_ts": divide(row["points"], 2 * (row["fga"] + 0.44 * row["fta"]))}


def paired_results(records):
    indexed = {(r["player"], r["season"], r["phase"]): r for r in records}
    pairs = []
    for key, post in sorted(indexed.items()):
        player, season, phase = key
        if phase != "playoffs" or season < "2016-17" or season > "2025-26":
            continue
        reg = indexed.get((player, season, "regular"))
        if not reg or min(reg["minutes"], reg["games"], post["minutes"], post["games"]) == 0:
            continue
        regular, playoffs = rates(reg), rates(post)
        avg_rate = (reg["points"] / reg["minutes"] + post["points"] / post["minutes"]) / 2
        avg_minutes = (regular["mpg"] + playoffs["mpg"]) / 2
        minutes_component = avg_rate * (playoffs["mpg"] - regular["mpg"])
        rate_component = avg_minutes * (post["points"] / post["minutes"] - reg["points"] / reg["minutes"])
        delta_ppg = playoffs["ppg"] - regular["ppg"]
        if not math.isclose(delta_ppg, minutes_component + rate_component, abs_tol=1e-10):
            raise ValueError("Decomposition identity failed")
        pairs.append({"player": player, "season": season,
                      "regular_games": reg["games"], "playoff_games": post["games"],
                      "regular": regular, "playoffs": playoffs,
                      "delta_ppg": delta_ppg,
                      "delta_points_per_36": playoffs["points_per_36"] - regular["points_per_36"],
                      "delta_approx_ts": playoffs["approx_ts"] - regular["approx_ts"],
                      "ppg_decomposition": {"minutes_component": minutes_component,
                                            "rate_component": rate_component,
                                            "interpretation": "descriptive_arithmetic_not_causal"}})
    return pairs


def load_records():
    records = []
    for player, source in SOURCES.items():
        pdf = ROOT / "data/raw" / (source["id"] + ".pdf")
        text = ROOT / "data/extracted" / source["id"] / ("page-%03d.txt" % source["page"])
        if hashlib.sha256(pdf.read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("Raw source hash mismatch: " + str(pdf))
        if hashlib.sha256(text.read_bytes()).hexdigest() != source["text_sha256"]:
            raise ValueError("Extracted text hash mismatch: " + str(text))
        records.extend(parse_table(text.read_text(), player))
    validate(records)
    return records


def main():
    records = load_records()
    pairs = paired_results(records)
    coverage = {
        "status": "incomplete_for_planned_scope", "planned_window": ["2016-17", "2025-26"],
        "source_last_season": {"butler": "2022-23", "murray": "2024-25"},
        "missing_source_seasons": {"butler": ["2023-24", "2024-25", "2025-26"], "murray": ["2025-26"]},
        "game_level_coverage": "not_acquired", "independent_secondary_check": "pending",
        "guide_pages_visually_inspected": True,
        "common_positive_exposure_seasons": sorted(
            {p["season"] for p in pairs if p["player"] == "butler"} &
            {p["season"] for p in pairs if p["player"] == "murray"}),
        "note": "Missing later seasons must not be interpreted as absent participation. No career-wide verdict is cleared."
    }
    result = {"status": "pilot_pending_independent_review_and_coverage", "sources": SOURCES,
              "coverage": coverage, "records": records, "pairs": pairs,
              "sensitivity_pair_keys": {str(threshold): [p["player"] + ":" + p["season"] for p in pairs if p["playoff_games"] >= threshold]
                                        for threshold in (1, 5, 10)}}
    for name, payload in (("results.json", result), ("coverage.json", coverage),
                          ("qa.json", {"status": "arithmetic_checks_passed_only", "row_count": len(records),
                                       "pair_count": len(pairs), "source_hashes": "passed", "text_hashes": "passed",
                                       "shooting_constraints": "passed", "points_identity": "passed",
                                       "unique_player_season_phase": "passed", "decomposition_identity": "passed",
                                       "independent_review": "pending", "full_coverage": "not_passed"})):
        (ROOT / "analysis" / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    lines = ["# Playoff Jimmy: reproducible research pilot", "",
             "Status: incomplete source coverage; independent review pending. These are descriptive scoring comparisons.", "",
             "Rates use published whole-minute totals. TS is the conventional 0.44 approximation; show sensible rounding.", "",
             "| Player | Season | Playoff games | PPG regular → playoffs | Points/36 regular → playoffs | Change /36 |",
             "|---|---|---:|---:|---:|---:|"]
    for p in pairs:
        a, b = p["regular"], p["playoffs"]
        lines.append("| %s | %s | %d | %.2f → %.2f | %.2f → %.2f | %+.2f |" %
                     (p["player"].title(), p["season"], p["playoff_games"], a["ppg"], b["ppg"],
                      a["points_per_36"], b["points_per_36"], p["delta_points_per_36"]))
    lines += ["", "## Sources and limits", "",
              "Butler: official 2023/24 Miami HEAT media guide, PDF page 66 / printed page 65.",
              "Murray: official 2025/26 Denver Nuggets media guide, PDF page 57 / printed page 58.",
              "See data/media-guide-manifest.json for retrieval URLs and hashes.", "",
              "Butler coverage stops at 2022–23, Murray at 2024–25. Later missing coverage is not zero performance.",
              "Per-minute comparisons do not control for opponent, health, role or playoff selection. No overall player ranking is made."]
    (ROOT / "analysis/FINDINGS.md").write_text("\n".join(lines) + "\n")
    print("Reproduced %d source rows and %d paired seasons. Full coverage and independent review remain open." % (len(records), len(pairs)))


if __name__ == "__main__":
    main()
