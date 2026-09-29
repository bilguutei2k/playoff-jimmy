"""Assemble narrated drafts: the long film and the shorts, with captions.

    python3 studio/tools/assemble.py studio/episodes/<id> [film short-a ...] [--jobs 4]

Reads EDIT.json (which lines play over which scene, and the word that starts
each animation beat) and renders/audio/narration.json (from narrate.py). For
each shot it lays the lines out with fixed gaps, turns the cues into a timemap
and renders the scene with studio/render/render.mjs --timemap. The shots are
joined with hard cuts; a "wipe" shot gets the design system's panel wipe (a
Night or Paper panel across the frame in 450 ms, centred on the cut). The
narration is placed on one track and normalised to -14 LUFS (-1 dBTP), the
level YouTube plays at. Writes renders/draft/<deliverable>.mp4, a matching
.srt caption file and <deliverable>.json with every shot's timing and hashes.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RENDER = ROOT / "studio/render/render.mjs"
FPS = 30
SIZE = {"landscape": (1920, 1080), "vertical": (1080, 1920)}
PANEL = {"paper": "0x1C1916", "night": "0xF3EBDD"}      # the panel contrasts with the incoming scene
RATE = 24000
PUNCT = "\"'“”‘’.,:;?!()"


def find_word(line, word, nth=1):
    target = word.strip(PUNCT).lower()
    seen = 0
    for w in line["words"]:
        if w["w"].strip(PUNCT).lower() == target:
            seen += 1
            if seen == nth:
                return w
    raise KeyError("word %r not in line: %s" % (word, line["written"]))


def plan_shot(shot, narration, edit):
    """Line start times within the shot, its duration, and the timemap anchors."""
    scene_id, indices = shot["lines"]
    lines = [narration["scenes"][scene_id]["lines"][i] for i in indices]
    t, starts = shot.get("lead", edit["lead"]), []
    for i, line in enumerate(lines):
        starts.append(t)
        t += line["duration"] + (edit["gap"] if i + 1 < len(lines) else 0)
    duration = t + shot.get("tail", edit["tail"])
    if "hold" in shot:                                  # a still: the scene frozen at one moment (a recap)
        return {"lines": lines, "starts": starts, "duration": round(duration, 3),
                "anchors": [[shot["hold"], 0.0], [shot["hold"] + 0.05, round(duration + 60, 3)]]}
    anchors = []
    for cue in shot["cues"]:
        line, base = lines[cue["line"]], starts[cue["line"]]
        at = base + (find_word(line, cue["word"], cue.get("nth", 1))["start"] if "word" in cue else 0)
        anchors.append([cue["t"], round(max(0.0, at + cue.get("offset", 0)), 3)])
    if anchors[0][1] > 0:
        anchors.insert(0, [anchors[0][0], 0.0])
    for a, b in zip(anchors, anchors[1:]):
        if b[1] < a[1] or b[0] < a[0]:
            raise ValueError("%s: cues out of order at scene t=%s" % (shot["scene"], b[0]))
    return {"lines": lines, "starts": starts, "duration": round(duration, 3), "anchors": anchors}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def render_shot(job):
    page, fmt, timemap, out = job
    tm = out.with_suffix(".timemap.json")
    tm.write_text(json.dumps(timemap) + "\n")
    key = hashlib.sha256((sha(page) + sha(page.parent / "data.js") + fmt + json.dumps(timemap)).encode()).hexdigest()
    stamp = out.with_suffix(".key")
    if out.exists() and stamp.exists() and stamp.read_text() == key:
        return out, "cached"
    subprocess.run(["node", str(RENDER), str(page), "--video", "--format", fmt, "--timemap", str(tm), "--out", str(out)],
                   check=True, capture_output=True, text=True)
    stamp.write_text(key)
    return out, json.loads(out.with_suffix(".mp4.json").read_text())["captured"]


def read_wav(path):
    with wave.open(str(path)) as f:
        assert f.getframerate() == RATE and f.getnchannels() == 1 and f.getsampwidth() == 2
        return f.readframes(f.getnframes())


def build_audio(placements, duration, out):
    track = bytearray(2 * int(round(duration * RATE)))
    for at, pcm in placements:
        i = 2 * int(round(at * RATE))
        pcm = pcm[: max(0, len(track) - i)]
        track[i:i + len(pcm)] = pcm
    with wave.open(str(out), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(bytes(track))


def loudnorm_filter(wav):
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(wav), "-af",
                            "loudnorm=I=-14:TP=-1:LRA=11:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True, check=True).stderr
    m = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
    return ("loudnorm=I=-14:TP=-1:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true"
            % (m["input_i"], m["input_tp"], m["input_lra"], m["input_thresh"], m["target_offset"]))


def wipe_graph(cuts, fmt, wipe, total):
    """Filter graph from [0:v] to [v]: at each cut a solid panel enters from the left, covers the cut, and
    leaves to the right, easing out like the system's settle curve."""
    w, h = SIZE[fmt]
    half, parts, last = wipe / 2, [], "[0:v]"
    ease = lambda p: "(1-pow(1-(%s),3))" % p
    for k, (t, color) in enumerate(cuts):
        a, b = t - half, t + half
        x = "if(lt(t,%.4f),-%d+%d*%s,%d*%s)" % (t, w, w, ease("(t-%.4f)/%.4f" % (a, half)), w, ease("(t-%.4f)/%.4f" % (t, half)))
        parts.append("color=c=%s:s=%dx%d:r=%d:d=%.3f[p%d]" % (color, w, h, FPS, total, k))
        parts.append("%s[p%d]overlay=x='%s':y=0:enable='between(t,%.4f,%.4f)'[w%d]" % (last, k, x, a, b, k))
        last = "[w%d]" % k
    parts.append("%snull[v]" % last)
    return ";".join(parts)


def text_of(words):
    return " ".join(w["w"] for w in words)


def split_cue(words, limit):
    """Split words into pieces of at most `limit` characters, at the comma (or else the space) that best
    balances each split."""
    if len(text_of(words)) <= limit or len(words) < 2:
        return [words]
    def cost(i):
        left, right = len(text_of(words[:i])), len(text_of(words[i:]))
        return abs(left - right) - (12 if re.search(r"[,;:]\W*$", words[i - 1]["w"]) else 0)
    i = min(range(1, len(words)), key=cost)
    return split_cue(words[:i], limit) + split_cue(words[i:], limit)


def wrap(words, width):
    """One line, or two balanced lines of at most `width` characters where possible."""
    if len(text_of(words)) <= width:
        return text_of(words)
    i = min(range(1, len(words)), key=lambda i: max(len(text_of(words[:i])), len(text_of(words[i:]))))
    return text_of(words[:i]) + "\n" + text_of(words[i:])


def captions(timed_lines, path, width=42):
    """SRT captions: sentences, merged when short and split at commas when long, at most two lines of
    `width` characters each, timed from the spoken words."""
    def fmt(s):
        ms = int(round(s * 1000))
        return "%02d:%02d:%02d,%03d" % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)
    cues = []
    for offset, line in timed_lines:
        sentences, current = [], []
        for w in line["words"]:
            current.append(w)
            if re.search(r"[.?!]\W*$", w["w"]):
                sentences.append(current)
                current = []
        if current:
            sentences.append(current)
        merged = []
        for s in sentences:
            if merged and len(text_of(merged[-1] + s)) <= width:
                merged[-1] = merged[-1] + s
            else:
                merged.append(s)
        for s in merged:
            cues.extend((offset, piece) for piece in split_cue(s, 2 * width - 2))
    entries = [[offset + chunk[0]["start"], offset + chunk[-1]["end"], wrap(chunk, width)] for offset, chunk in cues]
    for a, b in zip(entries, entries[1:]):
        a[1] = max(a[1], min(a[0] + 1.0, b[0]))
        if b[0] - a[1] < 0.25:
            a[1] = b[0]
    path.write_text("".join("%d\n%s --> %s\n%s\n\n" % (i + 1, fmt(a), fmt(b), t) for i, (a, b, t) in enumerate(entries)))
    return len(entries)


def assemble(episode, name, spec, edit, narration, jobs):
    out = episode / "renders/draft"
    shots_dir = out / name
    shots_dir.mkdir(parents=True, exist_ok=True)
    fmt, plans, t = spec["format"], [], 0.0
    for k, shot in enumerate(spec["shots"]):
        plan = plan_shot(shot, narration, edit)
        plan.update(start=round(t, 3), shot=shot, file=shots_dir / ("%02d-%s.mp4" % (k + 1, shot["scene"])))
        frames = round(plan["duration"] * FPS)
        plan["duration"] = frames / FPS                     # whole frames, so cuts land where the audio expects
        t += plan["duration"]
        plans.append(plan)
    total = t
    work = [(episode / "scenes" / (p["shot"]["scene"] + ".html"), fmt,
             {"duration": p["duration"], "anchors": p["anchors"]}, p["file"]) for p in plans]
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for path, how in pool.map(render_shot, work):
            print("  %s: %s" % (path.name, how if how == "cached" else "%s frames captured" % how))
    listing = shots_dir / "concat.txt"
    listing.write_text("".join("file '%s'\n" % p["file"].name for p in plans))
    joined = shots_dir / "joined.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(joined)],
                   check=True)
    placements, timed = [], []
    for p in plans:
        for start, line in zip(p["starts"], p["lines"]):
            placements.append((p["start"] + start, read_wav(episode / line["wav"])))
            timed.append((p["start"] + start, line))
    voice = shots_dir / "narration.wav"
    build_audio(placements, total, voice)
    cuts = [(p["start"], PANEL[p["shot"]["bg"]]) for p in plans if p["shot"]["in"] == "wipe"]
    final = out / (name + ".mp4")
    graph = wipe_graph(cuts, fmt, edit["wipe"], total) + ";[1:a]%s,aresample=48000[a]" % loudnorm_filter(voice)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(joined), "-i", str(voice), "-filter_complex", graph,
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                    "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", "%.3f" % total,
                    "-movflags", "+faststart", str(final)], check=True)
    n_captions = captions(timed, out / (name + ".srt"))
    record = {"deliverable": name, "title": spec.get("title"), "format": fmt, "duration": round(total, 3),
              "output_sha256": sha(final), "captions": n_captions, "narration_engine": narration["engine"],
              "story_sha256": narration["story_sha256"], "data_js_sha256": sha(episode / "scenes/data.js"),
              "shots": [{"scene": p["shot"]["scene"], "start": p["start"], "duration": p["duration"],
                         "lines": p["shot"]["lines"], "anchors": p["anchors"], "transition_in": p["shot"]["in"]} for p in plans]}
    (out / (name + ".json")).write_text(json.dumps(record, indent=1) + "\n")
    print("Wrote %s (%d:%04.1f, %d shots, %d captions)" % (final, total // 60, total % 60, len(plans), n_captions))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("episode", type=Path)
    parser.add_argument("deliverables", nargs="*")
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args(argv)
    edit = json.loads((args.episode / "EDIT.json").read_text())
    narration = json.loads((args.episode / "renders/audio/narration.json").read_text())
    story = sha(args.episode / "STORY.md")
    if narration["story_sha256"] != story:
        sys.exit("STORY.md changed since the narration was generated; rerun narrate.py")
    for name in args.deliverables or list(edit["deliverables"]):
        assemble(args.episode, name, edit["deliverables"][name], edit, narration, args.jobs)


if __name__ == "__main__":
    main()
