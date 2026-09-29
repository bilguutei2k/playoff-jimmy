"""Every scene renders from the locked data without page errors (skipped without Node or Chromium)."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENES = ROOT / "studio/episodes/playoff-jimmy/scenes"
FORMATS = {"title.html": "landscape", "s02-before-after.html": "landscape", "s03-rectangle.html": "landscape",
           "s04-league-strip.html": "landscape", "short-b.html": "vertical",
           "s05-fairer-test.html": "landscape", "s06-not-every-year.html": "landscape",
           "s01-cold-open.html": "landscape", "s04b-test-card.html": "landscape", "s07-twist.html": "landscape",
           "s08-verdict.html": "landscape", "short-d.html": "vertical"}


def chromium_available():
    return bool(list(Path.home().glob("Library/Caches/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell")))


@unittest.skipUnless(shutil.which("node") and chromium_available(), "needs Node and headless Chromium")
class RenderTests(unittest.TestCase):
    def test_every_scene_renders_a_still_from_current_data(self):
        self.assertEqual(sorted(FORMATS), sorted(p.name for p in SCENES.glob("*.html")))
        with tempfile.TemporaryDirectory() as out:
            for page, fmt in FORMATS.items():
                target = Path(out, page.replace(".html", ".png"))
                done = subprocess.run(["node", str(ROOT / "studio/render/render.mjs"), str(SCENES / page), "--still", "30",
                                       "--format", fmt, "--out", str(target)], capture_output=True, text=True, timeout=120)
                self.assertEqual(done.returncode, 0, page + ": " + done.stderr)
                self.assertGreater(target.stat().st_size, 50000, page)
                manifest = json.loads(Path(str(target) + ".json").read_text())
                self.assertEqual((manifest["width"], manifest["height"]),
                                 (1080, 1920) if fmt == "vertical" else (1920, 1080))

    def test_short_a_scenes_render_vertically(self):
        with tempfile.TemporaryDirectory() as out:
            for page in ("s02-before-after.html", "s03-rectangle.html"):
                target = Path(out, page.replace(".html", ".png"))
                done = subprocess.run(["node", str(ROOT / "studio/render/render.mjs"), str(SCENES / page), "--still", "30",
                                       "--format", "vertical", "--out", str(target)], capture_output=True, text=True, timeout=120)
                self.assertEqual(done.returncode, 0, page + ": " + done.stderr)
                self.assertEqual(json.loads(Path(str(target) + ".json").read_text())["height"], 1920)

    def test_data_js_matches_the_verified_results(self):
        done = subprocess.run(["python3", "-B", str(SCENES / "build_data.py")], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        diff = subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", "--", str(SCENES / "data.js")])
        self.assertEqual(diff.returncode, 0, "data.js is stale; rerun scenes/build_data.py")


if __name__ == "__main__":
    unittest.main()
