"""Official team media-guide tables: the independent check on Basketball-Reference.

Pure standard library. PDF text extraction is a separate step (extract_guides.py).
"""

import hashlib
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
COUNTS = ("games", "minutes", "points", "fgm", "fga", "fg3m", "fg3a", "ftm", "fta", "assists", "turnovers")


def integer(text):
    return int(text.replace(",", ""))


def butler_cells(cells):
    fg, fga = map(integer, cells[4].split("-"))
    threes, tpa = map(integer, cells[6].split("-"))
    ft, fta = map(integer, cells[8].split("-"))
    return {"games": integer(cells[2].split("-")[0]), "minutes": integer(cells[3]),
            "fgm": fg, "fga": fga, "fg3m": threes, "fg3a": tpa, "ftm": ft, "fta": fta,
            "points": integer(cells[16]), "assists": integer(cells[11]), "turnovers": integer(cells[14])}


def murray_cells(cells):
    return {"games": integer(cells[2]), "minutes": integer(cells[4]), "fgm": integer(cells[5]),
            "fga": integer(cells[6]), "fg3m": integer(cells[8]), "fg3a": integer(cells[9]),
            "ftm": integer(cells[11]), "fta": integer(cells[12]), "points": integer(cells[21]),
            "assists": integer(cells[17]), "turnovers": integer(cells[19])}


def parse_table(text, player):
    """Season rows plus each section's printed TOTALS row, which is kept for reconciliation."""
    records, totals, phase = [], {}, None
    for line in text.splitlines():
        line = line.strip()
        if "NBA REGULAR SEASON" in line:
            phase = "regular"
            continue
        if line == "NBA PLAYOFFS" or "NBA POSTSEASON STATISTICS" in line:
            phase = "playoffs"
            continue
        if not phase:
            continue
        cells = line.split()
        if not cells:
            continue
        if cells[0] == "TOTALS":
            # A totals row has no season or team cell; pad so the column mapping is shared.
            padded = ["", ""] + cells[1:]
            totals[phase] = butler_cells(padded) if player == "butler" else murray_cells(padded)
            phase = None
            continue
        if player == "butler" and re.fullmatch(r"\d{2}-\d{2}", cells[0]):
            if len(cells) != 18:
                raise ValueError("Unexpected Butler row: " + line)
            row = {"season": "20" + cells[0], "team": cells[1], **butler_cells(cells)}
        elif player == "murray" and re.fullmatch(r"\d{4}-\d{2}", cells[0]):
            if len(cells) != 23:
                raise ValueError("Unexpected Murray row: " + line)
            row = {"season": cells[0], "team": cells[1], **murray_cells(cells)}
        else:
            continue
        row.update(player=player, phase=phase, source_id=SOURCES[player]["id"],
                   pdf_page=SOURCES[player]["page"], printed_page=SOURCES[player]["printed_page"],
                   source_line=line, printed_ppg=float(cells[-1]), minutes_precision="published_whole_minutes")
        records.append(row)
    if not records:
        raise ValueError("No records parsed for " + player)
    return records, totals


def validate(records):
    keys = set()
    for row in records:
        key = (row["player"], row["season"], row["phase"])
        if key in keys:
            raise ValueError("Duplicate player-season-phase: " + str(key))
        keys.add(key)
        for field in COUNTS:
            if type(row[field]) is not int or row[field] < 0:
                raise ValueError("Invalid count: " + field)
        if not (row["fg3m"] <= row["fgm"] <= row["fga"] and
                row["fg3m"] <= row["fg3a"] <= row["fga"] and row["ftm"] <= row["fta"]):
            raise ValueError("Shooting constraints failed: " + str(key))
        if row["points"] != 2 * row["fgm"] + row["fg3m"] + row["ftm"]:
            raise ValueError("Points identity failed: " + str(key))
        if row["games"] == 0 and any(row[f] != 0 for f in COUNTS):
            raise ValueError("Nonzero counts with zero games: " + str(key))
        if "printed_ppg" in row and row["games"] and abs(row["points"] / row["games"] - row["printed_ppg"]) > 0.0501:
            raise ValueError("Printed per-game points disagree with totals: " + str(key))


def totals_discrepancies(records, totals):
    """Compare each printed TOTALS row with the sum of its season rows (minutes may differ by 1)."""
    found = []
    for (player, phase), printed in sorted(totals.items()):
        rows = [r for r in records if r["player"] == player and r["phase"] == phase]
        for field, value in sorted(printed.items()):
            summed = sum(r[field] for r in rows)
            if summed != value:
                found.append({"player": player, "phase": phase, "field": field, "sum_of_rows": summed,
                              "printed_total": value, "within_tolerance": field == "minutes" and abs(summed - value) <= 1})
    return found


def load(root=ROOT):
    """Return (records, printed totals keyed by (player, phase)) after hash and integrity checks."""
    records, totals = [], {}
    for player, source in SOURCES.items():
        pdf = root / "data/raw" / (source["id"] + ".pdf")
        text = root / "data/extracted" / source["id"] / ("page-%03d.txt" % source["page"])
        if hashlib.sha256(pdf.read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("Raw source hash mismatch: " + str(pdf))
        if hashlib.sha256(text.read_bytes()).hexdigest() != source["text_sha256"]:
            raise ValueError("Extracted text hash mismatch: " + str(text))
        rows, printed = parse_table(text.read_text(), player)
        records.extend(rows)
        totals.update({(player, phase): value for phase, value in printed.items()})
    validate(records)
    return records, totals
