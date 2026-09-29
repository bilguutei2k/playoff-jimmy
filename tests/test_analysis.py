"""Regression checks for research integrity, not a test of a preferred verdict."""

import importlib.util
import unittest
from pathlib import Path


path = Path(__file__).resolve().parents[1] / "studio/episodes/playoff-jimmy/analysis/analyze.py"
spec = importlib.util.spec_from_file_location("playoff_analysis", path)
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def record(phase="regular", games=10, minutes=300, points=100):
    return {"player": "test", "season": "2022-23", "phase": phase, "games": games,
            "minutes": minutes, "points": points, "fgm": points // 2, "fga": points,
            "fg3m": 0, "fg3a": 0, "ftm": 0, "fta": 0, "assists": 0, "turnovers": 0}


class AnalysisTests(unittest.TestCase):
    def test_extracted_columns_match_visually_audited_tables(self):
        rows = analysis.load_records()
        expected = {("butler", "regular"): (64, 2138, 1466, 888, 555, 340, 101),
                    ("butler", "playoffs"): (22, 874, 592, 442, 186, 129, 41),
                    ("murray", "regular"): (65, 2133, 1298, 1041, 216, 400, 145),
                    ("murray", "playoffs"): (20, 799, 522, 410, 81, 142, 50)}
        for row in rows:
            if row["season"] == "2022-23":
                actual = tuple(row[key] for key in ("games", "minutes", "points", "fga", "fta", "assists", "turnovers"))
                self.assertEqual(actual, expected[(row["player"], row["phase"])])

    def test_extra_minutes_alone_does_not_raise_scoring_rate(self):
        pair = analysis.paired_results([record(), record("playoffs", minutes=600, points=200)])[0]
        self.assertEqual(pair["delta_points_per_36"], 0)
        self.assertAlmostEqual(pair["ppg_decomposition"]["rate_component"], 0)
        self.assertAlmostEqual(pair["ppg_decomposition"]["minutes_component"], 10)

    def test_zero_exposure_is_undefined_and_not_a_pair(self):
        empty = record("playoffs", games=0, minutes=0, points=0)
        self.assertIsNone(analysis.rates(empty)["points_per_36"])
        self.assertEqual(analysis.paired_results([record(), empty]), [])

    def test_missing_playoffs_is_not_zero_performance(self):
        self.assertEqual(analysis.paired_results([record()]), [])

    def test_double_counted_player_season_fails(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            analysis.validate([record(), record()])

    def test_inconsistent_shooting_totals_fail(self):
        row = record()
        row["points"] += 1
        with self.assertRaisesRegex(ValueError, "Points identity"):
            analysis.validate([row])

    def test_decomposition_preserves_both_components(self):
        pair = analysis.paired_results([record(), record("playoffs", games=5, minutes=200, points=120)])[0]
        parts = pair["ppg_decomposition"]
        self.assertAlmostEqual(pair["delta_ppg"], parts["rate_component"] + parts["minutes_component"])


if __name__ == "__main__":
    unittest.main()
