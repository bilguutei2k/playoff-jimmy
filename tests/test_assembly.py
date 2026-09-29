"""Narration spoken forms, shot planning, captions and the render timemap."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "studio/tools"))
import assemble  # noqa: E402

VENV_PYTHON = ROOT / ".venv/bin/python"


def line(words):
    return {"written": " ".join(w for w, _, _ in words), "duration": words[-1][2], "wav": "x.wav",
            "words": [{"w": w, "start": s, "end": e} for w, s, e in words]}


NARRATION = {"scenes": {"S01": {"lines": [line([("The", 0.0, 0.2), ("number", 0.2, 0.6), ("26.9.", 0.6, 1.5)]),
                                          line([("Next.", 0.0, 0.5)])]}}}
EDIT = {"lead": 0.4, "gap": 0.5, "tail": 1.0}


class PlanTests(unittest.TestCase):
    def shot(self, cues):
        return {"scene": "x", "lines": ["S01", [0, 1]], "cues": cues}

    def test_cues_land_on_their_words(self):
        plan = assemble.plan_shot(self.shot([{"t": 0, "line": 0}, {"t": 2.1, "line": 0, "word": "26.9", "offset": -0.55},
                                             {"t": 3, "line": 1}]), NARRATION, EDIT)
        self.assertEqual(plan["starts"], [0.4, 2.4])
        self.assertEqual(plan["anchors"], [[0, 0.0], [0, 0.4], [2.1, 0.45], [3, 2.4]])
        self.assertAlmostEqual(plan["duration"], 3.9)

    def test_cues_out_of_order_are_refused(self):
        with self.assertRaises(ValueError):
            assemble.plan_shot(self.shot([{"t": 0, "line": 0}, {"t": 3, "line": 0, "word": "number"},
                                          {"t": 2, "line": 1}]), NARRATION, EDIT)

    def test_a_missing_cue_word_is_an_error(self):
        with self.assertRaises(KeyError):
            assemble.plan_shot(self.shot([{"t": 0, "line": 0, "word": "Milwaukee"}]), NARRATION, EDIT)


class CaptionTests(unittest.TestCase):
    def test_captions_are_two_short_rows_timed_to_the_words(self):
        text = ("Maybe that's unfair, because stars and role players are in the same pile. So, after seeing these "
                "results, I added a check: only players who scored at a similar rate in the regular season.")
        words = [(w, i * 0.3, i * 0.3 + 0.25) for i, w in enumerate(text.split())]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "x.srt")
            n = assemble.captions([(10.0, line(words))], path)
            blocks = path.read_text().strip().split("\n\n")
        self.assertEqual(len(blocks), n)
        self.assertGreater(n, 1)
        rows = [r for b in blocks for r in b.split("\n")[2:]]
        self.assertTrue(all(len(r) <= 42 for r in rows), rows)
        self.assertEqual(" ".join(rows), text)
        self.assertTrue(blocks[0].split("\n")[1].startswith("00:00:10,000 --> "))


@unittest.skipUnless(VENV_PYTHON.exists(), "needs the project .venv with mlx-audio (see studio/tools/narrate.py)")
class SpokenFormTests(unittest.TestCase):
    def test_numbers_seasons_and_tags_are_spoken(self):
        code = ("import json, sys; sys.path.insert(0, 'studio/tools'); from narrate import spoken_form; "
                "print(json.dumps([spoken_form(s)[0] for s in sys.argv[1:]]))")
        cases = {"The 2022–23 season, 22.9 points a game. [PJ-C002]": "The twenty twenty-two to twenty-three season, "
                                                                     "twenty-two point nine points a game.",
                 "That's 1,325 player-seasons.": "That's one thousand three hundred twenty-five player seasons.",
                 "the 71st percentile, a 4.0-point rise, since 2011–12": "the seventy-first percentile, a four-point "
                                                                         "rise, since twenty eleven to twelve",
                 "6 of his 11 runs, every 17-game stretch": "six of his eleven runs, every seventeen-game stretch"}
        done = subprocess.run([str(VENV_PYTHON), "-c", code] + list(cases), cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout), list(cases.values()))


def chromium_available():
    return bool(list(Path.home().glob("Library/Caches/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell")))


@unittest.skipUnless(shutil.which("node") and shutil.which("ffmpeg") and chromium_available(), "needs Node, ffmpeg, Chromium")
class TimemapTests(unittest.TestCase):
    def test_a_timemap_holds_between_cues_and_reuses_held_frames(self):
        page = ROOT / "studio/episodes/playoff-jimmy/scenes/title.html"
        with tempfile.TemporaryDirectory() as tmp:
            tm, out = Path(tmp, "tm.json"), Path(tmp, "clip.mp4")
            tm.write_text(json.dumps({"duration": 1.0, "anchors": [[0, 0], [0.2, 0.9]]}))
            done = subprocess.run(["node", str(ROOT / "studio/render/render.mjs"), str(page), "--video", "--timemap", str(tm),
                                   "--out", str(out)], capture_output=True, text=True, timeout=120)
            self.assertEqual(done.returncode, 0, done.stderr)
            manifest = json.loads(Path(str(out) + ".json").read_text())
        self.assertEqual(manifest["frames"], 30)
        self.assertLess(manifest["captured"], 15)      # 0.2 s of motion, one held frame, then 0.1 s more
        self.assertEqual(manifest["timemap"]["anchors"], [[0, 0], [0.2, 0.9]])


if __name__ == "__main__":
    unittest.main()
