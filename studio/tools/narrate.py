"""Narrate an episode's script with a local AI voice, keeping word timings.

    .venv/bin/python studio/tools/narrate.py studio/episodes/<id>
    .venv/bin/python studio/tools/narrate.py studio/episodes/<id> --audition af_heart am_michael bm_george

Reads the narration lines from STORY.md (the same parse as story_check.py),
writes each in a spoken form (claim tags removed; numbers, ordinals and season
years spelled out), and synthesizes it with Kokoro-82M (Apache-2.0 weights)
through mlx-audio on Apple Silicon. Nothing leaves the machine.

Writes renders/audio/lines/<hash>.wav, one per line and cached by content, and
renders/audio/narration.json: for every line its written and spoken text, WAV,
duration, and the start and end of every written word, taken from the
durations the model itself predicted. Assembly (studio/tools/assemble.py) uses
those timings for animation cues and captions. --audition instead reads the
first two lines of the film in each named voice, for choosing one by ear.
"""

import argparse
import hashlib
import json
import re
import sys
import wave
from pathlib import Path

import numpy as np
from num2words import num2words

sys.path.insert(0, str(Path(__file__).resolve().parent))
from story_check import TAG, scenes  # noqa: E402

MODEL = "mlx-community/Kokoro-82M-bf16"
SAMPLE_RATE = 24000
SCENE_ID = re.compile(r"(S\d\d|Short [A-Z])")


def words(n):
    """US-style cardinal: 1325 -> 'one thousand three hundred twenty-five'."""
    return num2words(n).replace(",", "").replace(" and ", " ")


def year(y):
    return "two thousand " + words(y - 2000) if 2000 < y < 2010 else words(y // 100) + " " + words(y % 100)


RULES = [
    # Seasons: 2022–23 -> twenty twenty-two to twenty-three
    (re.compile(r"(\d{4})[–-](\d{2})\b"), lambda m: year(int(m[1])) + " to " + words(int(m[2]))),
    # 4.0-point -> four-point
    (re.compile(r"(\d+)\.0-point"), lambda m: words(int(m[1])) + "-point"),
    # Decimals: 22.9 -> twenty-two point nine
    (re.compile(r"(\d+)\.(\d+)"), lambda m: words(int(m[1])) + " point " + " ".join(words(int(d)) for d in m[2])),
    # Ordinals: 71st -> seventy-first
    (re.compile(r"(\d+)(?:st|nd|rd|th)\b"), lambda m: num2words(int(m[1]), to="ordinal")),
    # Whole numbers, with thousands separators
    (re.compile(r"\d{1,3}(?:,\d{3})+|\d+"), lambda m: words(int(m[0].replace(",", "")))),
]
PHRASES = [("player-seasons", "player seasons")]


def speak(token):
    for written, said in PHRASES:
        token = token.replace(written, said)
    for pattern, repl in RULES:
        token = pattern.sub(repl, token)
    return token


def spoken_form(line):
    """The spoken text, and for each written word its character span in it."""
    written = TAG.sub("", line).split()
    spoken, spans = "", []
    for w in written:
        s = speak(w)
        start = len(spoken) + (1 if spoken else 0)
        spoken = (spoken + " " + s) if spoken else s
        spans.append((w, start, len(spoken)))
    return spoken, spans


def synthesize(pipeline, text, voice, speed):
    """Audio (float32) and [(char_start, char_end, t_start, t_end)] for each timed token."""
    chunks, timed, offset = [], [], 0.0
    for result in pipeline(text, voice=voice, speed=speed, split_pattern=None):
        audio = np.array(result.audio, dtype=np.float32).reshape(-1)
        cursor = 0
        for tok in result.tokens or []:
            at = text.find(tok.text, cursor) if tok.text else -1
            if at < 0:
                continue
            cursor = at + len(tok.text)
            if getattr(tok, "start_ts", None) is not None and getattr(tok, "end_ts", None) is not None:
                timed.append((at, cursor, offset + tok.start_ts, offset + tok.end_ts))
        chunks.append(audio)
        offset += len(audio) / SAMPLE_RATE
    return np.concatenate(chunks), timed


def word_times(spans, timed, duration):
    """Start and end of each written word; untimed words (punctuation) borrow their neighbours'."""
    out = []
    for w, a, b in spans:
        hits = [(s, e) for (x, y, s, e) in timed if x < b and y > a]
        out.append({"w": w, "start": round(min(s for s, _ in hits), 3) if hits else None,
                    "end": round(max(e for _, e in hits), 3) if hits else None})
    last = 0.0
    for item in out:
        if item["start"] is None:
            item["start"] = item["end"] = last
        last = item["end"]
    for item in out:
        item["end"] = min(item["end"], round(duration, 3))
    return out


def write_wav(path, audio):
    pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(pcm.tobytes())


def load_pipeline():
    from mlx_audio.tts.utils import load_model
    return load_model(MODEL)._get_pipeline("a")


def engine_info(voice, speed):
    from importlib.metadata import version
    return {"model": MODEL, "weights_license": "Apache-2.0", "voice": voice, "speed": speed,
            "mlx_audio": version("mlx-audio"), "misaki": version("misaki"), "sample_rate": SAMPLE_RATE}


def narrate(episode, voice, speed):
    story_path = episode / "STORY.md"
    out = episode / "renders/audio"
    (out / "lines").mkdir(parents=True, exist_ok=True)
    engine = engine_info(voice, speed)
    pipeline, report = None, {"engine": engine,
                              "story_sha256": hashlib.sha256(story_path.read_bytes()).hexdigest(), "scenes": {}}
    for (section, heading), lines in scenes(story_path.read_text()).items():
        match = SCENE_ID.match(heading)
        if not match:
            continue
        entries = []
        for index, line in enumerate(lines):
            spoken, spans = spoken_form(line)
            key = hashlib.sha256(json.dumps([spoken, engine], sort_keys=True).encode()).hexdigest()[:20]
            wav, meta = out / "lines" / (key + ".wav"), out / "lines" / (key + ".json")
            if not (wav.exists() and meta.exists()):
                pipeline = pipeline or load_pipeline()
                audio, timed = synthesize(pipeline, spoken, voice, speed)
                duration = len(audio) / SAMPLE_RATE
                write_wav(wav, audio)
                meta.write_text(json.dumps({"duration": round(duration, 3),
                                            "words": word_times(spans, timed, duration)}, indent=1) + "\n")
                print("  %s line %d: %.1f s" % (match[1], index + 1, duration))
            timing = json.loads(meta.read_text())
            entries.append({"index": index, "written": TAG.sub("", line).strip(), "spoken": spoken,
                            "claims": [c.strip() for g in TAG.findall(line) for c in g.split(",")],
                            "wav": str(wav.relative_to(episode)), **timing})
        report["scenes"][match[1]] = {"section": section, "heading": heading, "lines": entries}
    (out / "narration.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    total = sum(e["duration"] for s in report["scenes"].values() for e in s["lines"])
    print("Wrote %s (%d scenes, %.0f s of speech)" % (out / "narration.json", len(report["scenes"]), total))


def audition(episode, voices, speed):
    out = episode / "renders/audio/audition"
    out.mkdir(parents=True, exist_ok=True)
    lines = next(iter(scenes((episode / "STORY.md").read_text()).values()))[:2]
    text = " ".join(spoken_form(line)[0] for line in lines)
    pipeline = load_pipeline()
    gap = np.zeros(int(0.8 * SAMPLE_RATE), dtype=np.float32)
    for voice in voices:
        audio, _ = synthesize(pipeline, text, voice, speed)
        write_wav(out / (voice + ".wav"), np.concatenate([audio, gap]))
        print("  " + voice)
    print("Wrote %d auditions to %s" % (len(voices), out))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("episode", type=Path)
    parser.add_argument("--voice", default="af_heart")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--audition", nargs="+", metavar="VOICE")
    args = parser.parse_args(argv)
    if args.audition:
        audition(args.episode, args.audition, args.speed)
    else:
        narrate(args.episode, args.voice, args.speed)


if __name__ == "__main__":
    main()
