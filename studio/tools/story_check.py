"""Check an episode's narration against its verified claims, and time it.

    python3 studio/tools/story_check.py studio/episodes/<id>          # lint + word-count timing
    python3 studio/tools/story_check.py studio/episodes/<id> --say    # also time a scratch read with macOS `say`

Narration lives in STORY.md as blockquote lines ("> ...") under "### " scene
headings, each citing claims like [PJ-C002]. Rules: every cited claim exists
and is verified; a line containing a number cites at least one claim; and
every number in the line appears in a cited claim's text, scope or
limitations. Lines without numbers may carry context without a citation.
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


TAG = re.compile(r"\[([A-Z]+-C\d{3}(?:,\s*[A-Z]+-C\d{3})*)\]")
NUMBER = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")
WORDS_PER_MINUTE = 150


def normalize(text):
    return text.replace("−", "-").replace("–", "-")


def scenes(story):
    """Narration lines keyed by (section, scene)."""
    section, current, found = None, None, {}
    for line in story.splitlines():
        if line.startswith("## "):
            section, current = line[3:].strip(), None
        elif line.startswith("### "):
            current = line[4:].strip()
        elif line.startswith("> ") and current:
            found.setdefault((section, current), []).append(line[2:].strip())
    return found


def lint(found, claims):
    problems = []
    for (_, scene), lines in found.items():
        for line in lines:
            cited = [c.strip() for group in TAG.findall(line) for c in group.split(",")]
            spoken = normalize(TAG.sub("", line))
            for claim_id in cited:
                if claim_id not in claims:
                    problems.append("%s: unknown claim %s" % (scene, claim_id))
                elif claims[claim_id]["status"] != "verified":
                    problems.append("%s: claim %s is not verified" % (scene, claim_id))
            numbers = NUMBER.findall(spoken)
            if numbers and not cited:
                problems.append("%s: numbers without a claim: %s" % (scene, line[:70]))
                continue
            evidence = " ".join(normalize(" ".join([claims[c]["text"], claims[c]["scope"]] + claims[c]["limitations"]))
                                for c in cited if c in claims)
            for number in numbers:
                if not re.search(r"(?<![\d.])%s(?![\d])" % re.escape(number), evidence):
                    problems.append("%s: %s is not in %s" % (scene, number, ", ".join(cited)))
    return problems


def say_seconds(text, rate):
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "read.aiff"
        subprocess.run(["say", "-r", str(rate), "-o", str(target), text], check=True)
        info = subprocess.run(["afinfo", str(target)], capture_output=True, text=True).stdout
        return float(re.search(r"estimated duration: ([\d.]+)", info).group(1))


def clock(seconds):
    return "%d:%02d" % divmod(round(seconds), 60)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("episode", type=Path)
    parser.add_argument("--say", action="store_true", help="time a scratch read with macOS say")
    parser.add_argument("--rate", type=int, default=160, help="words per minute for say")
    args = parser.parse_args(argv)
    claims = {c["id"]: c for c in json.loads((args.episode / "CLAIMS.json").read_text())["claims"]}
    found = scenes((args.episode / "STORY.md").read_text())
    problems = lint(found, claims)
    print("| Scene | Words | At %d wpm |%s" % (WORDS_PER_MINUTE, " say -r %d |" % args.rate if args.say else ""))
    print("|---|---:|---:|%s" % ("---:|" if args.say else ""))
    sections = {}
    for (section, scene), lines in found.items():
        text = " ".join(TAG.sub("", line) for line in lines)
        words = len(text.split())
        spoken = say_seconds(text, args.rate) if args.say else 0.0
        total = sections.setdefault(section, [0, 0.0])
        total[0], total[1] = total[0] + words, total[1] + spoken
        print("| %s | %d | %s |%s" % (scene, words, clock(words * 60 / WORDS_PER_MINUTE),
                                      " %s |" % clock(spoken) if args.say else ""))
    for section, (words, spoken) in sections.items():
        print("| **%s total** | %d | %s |%s" % (section, words, clock(words * 60 / WORDS_PER_MINUTE),
                                               " %s |" % clock(spoken) if args.say else ""))
    for problem in problems:
        print("LINT: " + problem, file=sys.stderr)
    print("Lint: %s" % ("passed" if not problems else "%d problem(s)" % len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
