"""Analysis v2 checks against the frozen snapshot. They test integrity and the
pre-registered rules, not a preferred verdict."""

import importlib.util
import tempfile
import unittest
from pathlib import Path


path = Path(__file__).resolve().parents[1] / "studio/episodes/playoff-jimmy/analysis/analyze.py"
spec = importlib.util.spec_from_file_location("playoff_analysis_v2", path)
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def game(points, minutes):
    return {"points": points, "seconds": minutes * 60}


class SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results, cls.coverage, cls.qa = analysis.analyze()

    def season(self, player, season):
        return next(r for r in self.results["subjects"][player] if r["season"] == season)

    def test_all_data_checks_pass(self):
        self.assertTrue(self.qa["all_data_checks_passed"], self.qa["checks"])

    def test_pilot_values_reproduce_on_guide_rows(self):
        pilot = self.results["guide_pilot"]
        expected = {"butler_2016_17_to_2022_23": (-31.2, -0.34), "butler_all_guide_seasons": (-27.1, -0.22),
                    "murray_all_guide_seasons": (20.9, 0.24), "butler_shared": (-17.4, -0.30),
                    "murray_shared": (122.5, 2.14)}
        for key, (points, per_36) in expected.items():
            self.assertAlmostEqual(pilot[key]["excess_points"], points, places=1)
            self.assertAlmostEqual(pilot[key]["excess_per_36"], per_36, places=2)
        split = pilot["butler_2022_23"]["ppg_decomposition"]
        self.assertAlmostEqual(split["minutes_component"], 4.31, places=2)
        self.assertAlmostEqual(split["rate_component"], -0.31, places=2)

    def test_every_guide_row_reconciles_with_bbref(self):
        rows = self.results["reconciliation"]["guide_vs_bbref"]
        self.assertEqual(len(rows), 39)
        self.assertFalse([r for r in rows if r["status"] == "mismatch"])
        within = [(r["player"], r["season"], r["phase"]) for r in rows if r["status"] == "minutes_within_1"]
        self.assertEqual(within, [("murray", "2016-17", "regular")])

    def test_exposure_classes_are_computed_not_assumed(self):
        classes = self.coverage["exposure_classes"]
        self.assertEqual(classes["butler"]["2015-16"], "team_missed_playoffs")
        self.assertEqual(classes["butler"]["2023-24"], "playoff_team_no_games")
        self.assertEqual(classes["murray"]["2020-21"], "playoff_team_no_games")
        self.assertEqual(classes["murray"]["2021-22"], "no_games")
        self.assertNotIn("measures", self.season("butler", "2023-24"))

    def test_traded_seasons_use_the_combined_row_once(self):
        self.assertEqual(self.season("butler", "2018-19")["measures"]["regular_games"], 65)
        self.assertEqual(self.season("butler", "2018-19")["final_team"], "PHI")
        self.assertEqual(self.season("butler", "2024-25")["measures"]["regular_games"], 55)
        self.assertEqual(self.season("butler", "2024-25")["final_team"], "GSW")

    def test_subject_is_never_his_own_peer(self):
        for name, subject_id in analysis.SUBJECTS.items():
            for row in self.results["benchmark"][name]["per_season"]["A_100"]:
                if row["eligible"]:
                    pool = self.results["peers_primary_threshold"][row["season"]]
                    self.assertEqual(row["peer_n"], sum(p["player"] != subject_id for p in pool))

    def test_rerun_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            self.assertEqual(analysis.main(["--out", first]), 0)
            self.assertEqual(analysis.main(["--out", second]), 0)
            for name in ("results.json", "coverage.json", "qa.json", "FINDINGS.md"):
                self.assertEqual(Path(first, name).read_bytes(), Path(second, name).read_bytes(), name)


class RuleTests(unittest.TestCase):
    def test_percentile_counts_ties_as_half(self):
        self.assertEqual(analysis.percentile(1, [0, 1, 1, 2]), 50)
        self.assertIsNone(analysis.percentile(1, []))

    def test_wording_bands_follow_the_table(self):
        self.assertEqual([analysis.band(p) for p in (24.9, 25, 75, 75.1, 89.9, 90)],
                         ["below typical", "typical", "typical", "above typical", "above typical", "exceptional"])

    def test_every_consecutive_stretch_is_used(self):
        games = [game(10, 30), game(20, 30), game(30, 30)]
        self.assertEqual(analysis.window_rates(games, 2), [18.0, 30.0])

    def test_career_condition_needs_pooled_edge_and_majority(self):
        def row(delta, median):
            return {"season": "x", "playoff_minutes": 360, "excess_points": delta * 10,
                    "delta_points_per_36": delta, "peer_median": median}
        self.assertTrue(analysis.career_condition([row(1, 0), row(1, 0), row(-1, 0)])["condition_met"])
        # A large pooled edge from one season is not enough without a majority of seasons.
        self.assertFalse(analysis.career_condition([row(9, 0), row(-1, 0), row(-1, 0)])["condition_met"])
        self.assertFalse(analysis.career_condition([])["condition_met"])


if __name__ == "__main__":
    unittest.main()
