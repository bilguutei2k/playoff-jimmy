"""Analysis v2 checks against the frozen snapshot. They test integrity and the
pre-registered rules, not a preferred verdict."""

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


path = Path(__file__).resolve().parents[1] / "studio/episodes/playoff-jimmy/analysis/analyze.py"
spec = importlib.util.spec_from_file_location("playoff_analysis_v2", path)
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)

# The saved Basketball-Reference pages are not redistributed (see README.md); tests that
# rerun the analysis or check input hashes need them and are skipped without them.
SNAPSHOT = path.parents[1] / "data/raw/bbref"
needs_snapshot = unittest.skipUnless(SNAPSHOT.is_dir(), "needs the saved Basketball-Reference pages (not redistributed)")


def game(points, minutes):
    return {"points": points, "seconds": minutes * 60}


@needs_snapshot
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

    def test_exploratory_career_edge_agrees_with_the_benchmark(self):
        for name in analysis.SUBJECTS:
            career = self.results["benchmark"][name]["career"]["A_100"]
            edge = self.results["exploratory"]["career_edge"][0]["subjects"][name]
            self.assertAlmostEqual(edge["edge_per_36"],
                                   career["pooled_excess_per_36"] - career["minute_weighted_peer_median"], places=9)
            self.assertEqual(edge["runs_above_peer_median"], career["seasons_above_peer_median"])

    def test_matched_peers_are_similar_scorers(self):
        matched = self.results["exploratory"]["matched_peers"]
        butler, murray = matched["butler"]["rate_within_3"], matched["murray"]["rate_within_3"]
        self.assertEqual((butler["season_count"]["seasons_above_peer_median"], butler["season_count"]["n_eligible_seasons"]), (6, 11))
        self.assertEqual((murray["season_count"]["seasons_above_peer_median"], murray["season_count"]["n_eligible_seasons"]), (5, 6))
        self.assertAlmostEqual(butler["career"]["minute_weighted_peer_median"], -2.08, places=2)
        for row in butler["per_season"]:
            pool = self.results["peers_primary_threshold"][row["season"]]
            similar = [p for p in pool if p["player"] != "butleji01"
                       and abs(p["regular_points_per_36"] - row["regular_value"]) <= analysis.MATCH_WIDTH]
            self.assertEqual(row["peer_n"], len(similar))

    def test_rerun_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            self.assertEqual(analysis.main(["--out", first]), 0)
            self.assertEqual(analysis.main(["--out", second]), 0)
            for name in ("results.json", "coverage.json", "qa.json", "FINDINGS.md"):
                self.assertEqual(Path(first, name).read_bytes(), Path(second, name).read_bytes(), name)


    def test_packet_is_built_from_results_json_only(self):
        spec_p = importlib.util.spec_from_file_location("playoff_packet", path.with_name("packet.py"))
        packet = importlib.util.module_from_spec(spec_p)
        spec_p.loader.exec_module(packet)
        with tempfile.TemporaryDirectory() as out:
            self.assertEqual(analysis.main(["--out", out]), 0)
            packet.main(["--results", str(Path(out, "results.json")), "--out", out])
            page = Path(out, "index.html").read_text()
            digest = hashlib.sha256(Path(out, "results.json").read_bytes()).hexdigest()
            self.assertIn(digest, page)
            self.assertIn("Methods reviewed", page)


@needs_snapshot
class ClaimTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec_v = importlib.util.spec_from_file_location("playoff_verify_claims", path.with_name("verify_claims.py"))
        cls.verify = importlib.util.module_from_spec(spec_v)
        spec_v.loader.exec_module(cls.verify)

    def test_every_claim_passes_every_check(self):
        report = self.verify.check()
        self.assertTrue(report["all_passed"], [c for c in report["claims"] if not c["passed"]])

    def test_every_claim_value_is_independently_recomputed(self):
        claims = json.loads(path.parent.parent.joinpath("CLAIMS.json").read_text())["claims"]
        recomputed = self.verify.independent()
        self.assertEqual([v["key"] for c in claims for v in c["values"] if v["key"] not in recomputed], [])

    def test_precision_check_rejects_a_misstated_value(self):
        self.assertTrue(self.verify.agrees(-0.25, -0.2502, 2))
        self.assertFalse(self.verify.agrees(-0.26, -0.2502, 2))
        self.assertFalse(self.verify.agrees("typical", "above typical", None))


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
