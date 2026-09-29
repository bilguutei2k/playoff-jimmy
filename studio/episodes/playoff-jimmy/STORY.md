# Is Playoff Jimmy real? — story and scenes

Status: script v3, 2026-09-29. Script v2 was approved by the user 2026-09-28
(tag script-lock-v1), on verified claims (tag research-lock-v2), after an
external review (`analysis/review.md`, Review 3). v3 applies Astra's (Codex's)
final pre-production review (Review 4); the changes are listed under "Changes
after the lock" at the end. Narrated with a local AI voice
(`studio/tools/narrate.py`); the edit is `EDIT.json`, built by
`studio/tools/assemble.py`. Changes after the lock: edit, rerun the check,
record why, then rerun narrate.py and assemble.py.
Check with `python3 studio/tools/story_check.py studio/episodes/playoff-jimmy --say`.

## Argument: "Real, but not how you think"

Every factual beat cites a verified claim in `CLAIMS.json`. Numbers are never
retyped from memory: scenes read them from `analysis/results.json`.

| Beat | What the viewer learns | Claims |
|---|---|---|
| 1. Hook | The 2022–23 run: 22.9 to 26.9 points per game; 37.6 against Milwaukee. | PJ-C002, PJ-C009 |
| 2. Obvious answer | He scores more. Scope: how much, not how efficiently. His minutes rose too. | PJ-C002 |
| 3. Objection | The rectangle got wider, not taller: all of the rise came with minutes; per 36 barely moved. | PJ-C003, PJ-C004 |
| 4. What normally happens | Most players shrink in the playoffs. The test and its commit date go on screen. | PJ-C001 |
| 5. Fairer test | He shrinks less than players in the same seasons, and even less than similar scorers. | PJ-C005, PJ-C012 |
| 6. Not every year | Against similar scorers it's 6 of 11, close to a coin flip; worst runs were short; who looks steadier, Butler or Murray, depends on the comparison. | PJ-C013, PJ-C008 |
| 7. Twist | The legend season was typical per minute; the real transformation was the year before. | PJ-C004, PJ-C007 |
| 8. End | The evidence leans toward "holds up", on average, not every year. | PJ-C001, PJ-C003, PJ-C005, PJ-C012 |

Wording rules from the reviews: say "shrinks less than most" or "holds up",
never "scores more in the playoffs" (per minute) or "clutch". No consistency
comparison beyond the counts in PJ-C013. Narrate in the first person ("I").
One decimal in narration; thresholds and year ranges go on screen. The
career ranking (PJ-C006) stays out of the video for now.

## Scene table

| Scene | Viewer question | Claims | Visual (the design system decides the look) | Why next? |
|---|---|---|---|---|
| S01 Cold open | Why do people call him Playoff Jimmy? | C002, C009 | Big-number reveal 22.9 → 26.9; "37.6 vs Milwaukee" flashes; title card | The obvious answer is waiting. |
| S02 The obvious answer | So he scores more? | C002 | Before → after points per game; scope note "how much, not how efficiently"; minutes 33.4 → 39.7 slides in | The second number needs explaining. |
| S03 It's the minutes | Or does he just play more? | C003, C004 | Rectangle: width = minutes, height = scoring rate, area = points per game; it widens and dips a hair | Calling it a myth needs a baseline. |
| S04 What normally happens | Is holding steady good or bad? | C001 | Distribution of all 1,325 player-seasons with thresholds on screen; median at −1.5; then the pre-registered test and its commit date | The test is set; now run it. |
| S05 The fairer test | Does he shrink less than others? | C005, C012 | Dot strip by season, Butler highlighted; −0.25 vs −1.7; the pile narrows to similar scorers: −2.1 | Averages can hide the seasons. |
| S06 Not every year | Is it every year? And Murray? | C013, C008 | Season-by-season wins and losses against similar scorers (6 of 11); short runs flagged; the Butler/Murray count flips when the peers change | One season breaks the pattern. |
| S07 The twist | Did he ever really transform? | C004, C007 | 2022–23 at the 71st percentile beside 2021–22 at the 99th, above every 17-game stretch | Time for the verdict. |
| S08 Verdict | So, is it real? | C001, C003, C005, C012 | Rectangles: most players' get shorter; his widens and holds its height; closing card with sources | End. |

## Script (v3)

### S01 Cold open

> The 2022–23 season. Jimmy Butler finishes the regular season averaging 22.9 points a game. [PJ-C002]
> Then the playoffs start, and the number jumps to 26.9. [PJ-C002]
> The first round, against Milwaukee, becomes legend: 37.6 points a game. [PJ-C009]
> Miami makes the Finals. And fans have a name for this: Playoff Jimmy.
> So here's my question. Is Playoff Jimmy real? Not "did he have a great month". Does Jimmy Butler actually become a better scorer when the playoffs start?

### S02 The obvious answer

> The obvious answer is yes: 22.9 points a game became 26.9, in the games that matter most. [PJ-C002]
> One note before I go further: this video is about how much he scores, not how efficiently.
> Points per game has a hidden ingredient, and in the playoffs it changes a lot. Minutes.
> In the regular season Butler played 33.4 minutes a game. In the playoffs, 39.7. [PJ-C002]

### S03 It's the minutes

> Think of points per game as a rectangle. The width is minutes. The height is how fast you score while you're on the floor. The area is points per game.
> In the playoffs, Butler's rectangle got wider. It didn't get taller. If anything, it got a hair shorter. [PJ-C004]
> The extra minutes account for all of that 4.0-point rise, and a little more. His scoring rate actually subtracted. [PJ-C003]
> Scale his scoring to the same 36 minutes, and it barely moved: 24.7 in the regular season, 24.4 in the playoffs. [PJ-C004]
> Same scorer. More minutes.
> So is Playoff Jimmy a myth? Not yet. A myth needs something to compare against.

### S04 What normally happens

> To call anything a myth, I need to know what normally happens to a player's scoring when the playoffs start.
> So I took every player since 2011–12 who played real minutes in both the regular season and the playoffs of the same season. That's 1,325 player-seasons: each player counted once for each season. [PJ-C001]
> The typical one scored 1.5 fewer points per 36 minutes in the playoffs. Nearly three in four declined. [PJ-C001]
> Tougher defenses, slower games, tired legs: I can't separate those reasons here. But the pattern is clear. Most players shrink in the playoffs.
> So the real question isn't "does Butler score more in the playoffs?" It's "does he shrink less than most players?"
> Before I downloaded any of this league data, I wrote down exactly how I'd answer that, and what it would take to call Playoff Jimmy real. That's it on screen, with the date I committed it.

### S05 The fairer test

> Here's every eligible player, season by season. Each dot is one player's change in scoring rate. The highlighted dot is Butler.
> Butler has 11 playoff runs with real minutes. In those seasons, players typically fell by 1.7 points per 36 minutes. Butler fell by about a quarter of a point. [PJ-C005]
> Maybe that's unfair, because stars and role players are in the same pile. So, after seeing these results, I added a check: only players who scored at a similar rate in the regular season. The gap got bigger: they typically fell by 2.1. [PJ-C012]
> By the test I wrote down in advance, Playoff Jimmy passes. He doesn't grow in the playoffs. He shrinks less than most players do. [PJ-C005]

### S06 Not every year

> But an average can hide a lot. Season by season, against those similar scorers, Butler came out ahead in 6 of his 11 runs. That's close to a coin flip. [PJ-C013]
> Of those 11, his two worst runs were short: 5 games in 2017–18 and 4 games in 2020–21. Small samples swing hard. [PJ-C008, PJ-C013]
> And the player on the other side of those Finals? Against similar scorers, Jamal Murray came out ahead in 5 of his 6 runs. Against everyone, it was Butler who looked steadier: 8 of 11, to Murray's 3 of 6. [PJ-C013]
> Which of them is steadier depends on who you compare them with. Remember that the next time someone ranks the league's playoff risers.

### S07 The twist

> Here's the part I didn't expect. The run that made the legend, 2022–23, was typical per minute: his change in scoring rate ranked in the 71st percentile of that season's players. [PJ-C004]
> The real transformation came the year before. In 2021–22 his scoring rate jumped from 22.7 to 26.7 points per 36. That change ranked in the 99th percentile, and his playoff rate beat every 17-game stretch of his own regular season. [PJ-C007]
> The season that built the legend wasn't the season he changed.

### S08 Verdict

> So, is Playoff Jimmy real?
> If you mean a player who turns into someone else in April: mostly, no. In 2022–23, the extra minutes account for his whole rise in points per game. [PJ-C002, PJ-C003]
> If you mean a player who holds up when the games get harder, the evidence leans that way. Most players' rectangles get shorter in the playoffs. His, on average, barely does. [PJ-C001, PJ-C005, PJ-C012]
> Not every year, and not by a margin I'd bet the house on. But in a league where most players shrink, holding your height is worth noticing. [PJ-C013]
> Every number in this video, the data behind it and the checks I ran are linked in the description.

## Timing

AI narration (Kokoro-82M, voice af_heart, speed 1.0), measured 2026-09-29 from
the generated audio; the drafts add gaps between lines and time for the
charts.

| Scene | Words | Speech |
|---|---:|---:|
| S01 Cold open | 75 | 0:33 |
| S02 The obvious answer | 64 | 0:27 |
| S03 It's the minutes | 107 | 0:40 |
| S04 What normally happens | 150 | 0:56 |
| S05 The fairer test | 117 | 0:44 |
| S06 Not every year | 115 | 0:43 |
| S07 The twist | 82 | 0:36 |
| S08 Verdict | 110 | 0:38 |
| Short A | 81 | 0:35 |
| Short B | 67 | 0:27 |
| Short D | 63 | 0:32 |

Long-form speech 5:20; assembled drafts: film 5:49, Short A 0:40 (39.8 s),
Short B 0:30, Short D 0:35 (every verdict lands before 0:40).

## Short-form adaptations

Each short stands alone: its own hook, one supported finding, the scope
caption on screen for the whole short, and a payoff. Same claims and results
as the long film.

### Short A: He didn't score faster. He played longer.

Scope caption: Jimmy Butler, 2022–23 regular season vs playoffs. Data: Basketball-Reference.

> Jimmy Butler went from 22.9 points a game in the 2022–23 regular season to 26.9 in the playoffs. [PJ-C002]
> Playoff Jimmy, right? Now look at his minutes: 33.4 a game, then 39.7. [PJ-C002]
> Scale both to the same 36 minutes, and his scoring went from 24.7 to 24.4. [PJ-C004]
> He didn't score faster. He played longer. All of the rise came with the minutes. [PJ-C003]
> Whether that makes Playoff Jimmy a myth is a different question. The full video tests him against the whole league.

### Short B: Most players shrink in the playoffs

Scope caption: Players with at least 1,500 regular-season and 100 playoff minutes in the same season; Butler's 11 runs, 2012–13 to 2024–25. Points per 36 minutes.

> Most players score less per minute in the playoffs. [PJ-C001]
> Across Jimmy Butler's 11 qualifying playoff runs, the typical player in those seasons dropped 1.7 points per 36 minutes. [PJ-C005]
> Butler dropped about a quarter of a point. [PJ-C005]
> Not every year: season by season, against similar scorers, it's close to a coin flip. [PJ-C013]
> But on average, Playoff Jimmy isn't a player who grows. He's a player who shrinks less. [PJ-C005]

### Short C: held

The career ranking (PJ-C006) compares players across very different roles and
was built after the results. Held until a matched version exists.

### Short D: The series that built a legend

Scope caption: Jimmy Butler, 2022–23 playoffs by series. Game logs: Basketball-Reference.

> In the first round of the 2022–23 playoffs, Jimmy Butler scored 37.6 points a game against Milwaukee. [PJ-C009]
> That's the series everyone remembers.
> The next three series: 24.6, 24.7 and 21.6 points a game. [PJ-C009]
> The last of those was the Finals against Denver, below his regular-season 22.9. [PJ-C009, PJ-C002]
> One legendary series. Across the whole playoffs, his scoring per minute barely changed from the regular season. [PJ-C004]

## Interactive companion

One control: which seasons count (all runs, shared seasons, runs of at least
100 minutes) and which peers (all eligible, 20+ point scorers, or similar
scorers). The viewer watches Butler's and Murray's results move, or not.
Values come from `analysis/results.json`; the page does no statistics of its
own.

## Changes after the lock

2026-09-29, script v3, from Astra's (Codex's) final pre-production review
(`analysis/review.md`, Review 4). The user asked for the review and said to
proceed with its amendments. No number, claim or verdict changed; each edit
narrows wording to what its claim supports.

- S03, Short A: "Per 36 minutes, ..." now says how the scale works ("Scale
  ... to the same 36 minutes").
- S04: "1,325 player-seasons" is explained; "shrink less than everyone else"
  became "less than most players" (PJ-C005 compares with the typical peer).
- S05: the similar-scorer comparison is labelled as added after seeing the
  results (METHOD.md amendments 4 and 5 require the label wherever it is
  used); the 11 runs are "with real minutes" (his 2011–12 run is outside the
  cutoffs); the typical drop now comes before Butler's, matching the chart.
- S06: "a coin flip" became "close to a coin flip", the verified wording of
  PJ-C013; "his two worst runs" became "of those 11".
- S07: the percentiles are said to rank his change in scoring rate, and the
  17-game comparison is said to concern his playoff rate (PJ-C004, PJ-C007).
- S08: "His points per game rise because his minutes do" was general and
  causal; it now names 2022–23 and says the minutes "account for" the rise
  (PJ-C003 is a descriptive split of one season).
- Short A title: "He didn't score more. He played more." was false as
  written (he scored 4.0 more per game); now "He didn't score faster. He
  played longer."
- Short B: "11 qualifying playoff runs" replaces "the seasons he made a
  playoff run".
- Short D: "then a normal run" dropped (no claim supports it); "matched" became
  "barely changed" (24.7 to 24.4 per 36 is a small drop, not equality).
- On screen: S02/S03 headline "He scores more in the playoffs" became "He
  scores more per game" (the wording rules forbid the unqualified phrase);
  title caption "More points when it counts. Or just more minutes?"; Short
  A's rectangle labels "+4.3 MIN" and "−0.3 RATE" now say both are points per
  game ("+4.3 MIN" read as minutes, which rose 6.3); S04b states that every
  version of the test must pass; S05 labels the similar scorers "added
  later"; S06 headline "Year by year, nearly a coin flip"; S07 "Percentile of
  the change"; S08 and Short B captions say the coin flip is against similar
  scorers; Short B names the 11 qualifying runs and years; Short D "nearly
  matched".
- S02 shows the minutes (33.4 → 39.7) when the narration says them.

Not taken from the review: replacing "coin flip" with "close to half" (the
verified claim PJ-C013 uses "close to a coin flip"); a longer per-36
explanation in Short B (its scope caption carries the unit); rewording the
S05 chip "Passes" to "Original test: passes" (the narration says "by the test
I wrote down in advance" as the chip lands, and the similar-scorer row is now
labelled "added later").
