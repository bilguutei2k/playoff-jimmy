"""The narration check: every spoken number must come from a cited, verified claim."""

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("story_check", ROOT / "studio/tools/story_check.py")
story_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(story_check)

CLAIMS = {
    "PJ-C001": {"status": "verified", "text": "The typical player fell 1.5 points per 36; 73% declined.",
                "scope": "1,325 player-seasons, 2011–12 to 2025–26.", "limitations": []},
    "PJ-C002": {"status": "proposed", "text": "He scored 26.9.", "scope": "", "limitations": []},
}


def check(line):
    return story_check.lint({("Script", "S01"): [line]}, CLAIMS)


class StoryCheckTests(unittest.TestCase):
    def test_supported_numbers_pass(self):
        self.assertEqual(check("Most players fell 1.5 per 36, and 73% declined, across 1,325 seasons since 2011–12. [PJ-C001]"), [])

    def test_context_without_numbers_needs_no_claim(self):
        self.assertEqual(check("Most players shrink in the playoffs."), [])

    def test_number_without_a_claim_fails(self):
        self.assertTrue(check("He scored 26.9 a game."))

    def test_number_missing_from_the_cited_claim_fails(self):
        self.assertIn("1.6", check("The typical player fell 1.6 per 36. [PJ-C001]")[0])

    def test_unverified_or_unknown_claims_fail(self):
        self.assertTrue(check("He scored 26.9. [PJ-C002]"))
        self.assertTrue(check("Something. [PJ-C999]"))

    def test_episode_script_passes(self):
        episode = ROOT / "studio/episodes/playoff-jimmy"
        claims = {c["id"]: c for c in story_check.json.loads((episode / "CLAIMS.json").read_text())["claims"]}
        self.assertEqual(story_check.lint(story_check.scenes((episode / "STORY.md").read_text()), claims), [])


if __name__ == "__main__":
    unittest.main()
