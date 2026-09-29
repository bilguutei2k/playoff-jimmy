"""Build the storyboard editor: every narration line beside what is on screen while it is spoken.

    python3 studio/tools/storyboard.py studio/episodes/<id>

Reads STORY.md (through narrate.py's narration.json), CLAIMS.json, EDIT.json and
the assembled drafts in renders/draft/. For each line it takes the frame as the
line starts and as it ends from the draft video, and the line's current
narration, and writes renders/storyboard/: page.html (published as a claude.ai
Artifact that saves edits to its own store) plus f/*.jpg and a/*.mp3 beside it.
Run assemble.py first so the frames match the current edit.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assemble import FPS, plan_shot  # noqa: E402

HERE = Path(__file__).resolve().parent
SCENE_NAMES = {"film": "Film", "short-a": "Short A", "short-b": "Short B", "short-d": "Short D"}


def line_id(scene, index):
    return scene.replace(" ", "") + "-" + str(index + 1)


def timeline(episode, edit, narration, name):
    """(line key, start, end) in the assembled video, the same layout assemble.py uses."""
    t, out = 0.0, []
    for shot in edit["deliverables"][name]["shots"]:
        plan = plan_shot(shot, narration, edit)
        scene, indices = shot["lines"]
        for start, index, line in zip(plan["starts"], indices, plan["lines"]):
            out.append(((scene, index), t + start, t + start + line["duration"]))
        t += round(plan["duration"] * FPS) / FPS
    return out


def grab(video, at, out, vertical):
    scale = "scale=240:-2" if vertical else "scale=480:-2"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "%.3f" % max(0, at), "-i", str(video), "-frames:v", "1",
                    "-vf", scale, "-q:v", "6", str(out)], check=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("episode", type=Path)
    args = parser.parse_args(argv)
    ep = args.episode.resolve()
    edit = json.loads((ep / "EDIT.json").read_text())
    narration = json.loads((ep / "renders/audio/narration.json").read_text())
    claims = {c["id"]: {"text": c["text"], "scope": c["scope"], "limitations": c["limitations"]}
              for c in json.loads((ep / "CLAIMS.json").read_text())["claims"]}
    out = ep / "renders/storyboard"
    (out / "f").mkdir(parents=True, exist_ok=True)
    (out / "a").mkdir(parents=True, exist_ok=True)

    placed = {}
    for name in edit["deliverables"]:
        video = ep / "renders/draft" / (name + ".mp4")
        vertical = edit["deliverables"][name]["format"] == "vertical"
        for key, start, end in timeline(ep, edit, narration, name):
            lid = line_id(*key)
            grab(video, start + 0.3, out / "f" / (lid + "-a.jpg"), vertical)
            grab(video, end - 0.1, out / "f" / (lid + "-b.jpg"), vertical)
            placed[key] = {"deliverable": name, "start": round(start, 2), "end": round(end, 2), "vertical": vertical}

    groups = []
    for scene, block in narration["scenes"].items():
        lines = []
        for line in block["lines"]:
            key = (scene, line["index"])
            lid = line_id(*key)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(ep / line["wav"]), "-ac", "1", "-c:a", "libmp3lame",
                            "-b:a", "64k", str(out / "a" / (lid + ".mp3"))], check=True)
            lines.append({"id": lid, "text": line["written"], "claims": line["claims"], "seconds": line["duration"],
                          "words": len(line["written"].split()), **placed[key]})
        groups.append({"id": scene.replace(" ", ""), "scene": scene, "heading": block["heading"],
                       "deliverable": lines[0]["deliverable"], "lines": lines})

    payload = {"episode": ep.name, "story_sha256": narration["story_sha256"], "voice": narration["engine"]["voice"],
               "deliverables": {k: SCENE_NAMES[k] for k in edit["deliverables"]}, "scenes": groups, "claims": claims}
    page = (HERE / "storyboard.html").read_text().replace("__DATA__", json.dumps(payload, ensure_ascii=False).replace("</", "<\\/"))
    (out / "page.html").write_text(page)
    n = sum(len(g["lines"]) for g in groups)
    print("Wrote %s: %d scenes, %d lines, %d frames" % (out / "page.html", len(groups), n, 2 * n))


if __name__ == "__main__":
    main()
