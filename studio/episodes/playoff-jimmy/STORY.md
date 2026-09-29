# Is Playoff Jimmy real? — story and scenes

Status: script draft v1 (PJ-06), 2026-09-28, on verified claims (tag
research-lock-v1). Not recorded; timing below is a scratch machine read.
Check with `python3 studio/tools/story_check.py studio/episodes/playoff-jimmy --say`.

## Argument: "Real, but not how you think"

Every factual beat cites a verified claim in `CLAIMS.json`. Numbers are never
retyped from memory: scenes read them from `analysis/results.json`.

| Beat | What the viewer learns | Claims |
|---|---|---|
| 1. Hook | The 2023 run: 22.9 to 26.9 points per game. "Playoff Jimmy." | PJ-C002 |
| 2. Obvious answer | He scores more in the playoffs. | PJ-C002 |
| 3. Objection | He also played six more minutes a game; per 36 minutes his scoring barely moved (24.7 to 24.4). Almost all of the rise goes with the minutes. | PJ-C003, PJ-C004 |
| 4. "Myth busted?" | Not so fast: most high-minute players score 1.5 fewer points per 36 in the playoffs, and 73% decline. | PJ-C001 |
| 5. Better test | Against peers in the same seasons, Butler holds: −0.25 per 36 against a typical −1.70, above the peer median in 8 of 11 runs. | PJ-C005 |
| 6. Honesty | It could be luck (about 11%), he is not unique (7th of 29 long playoff careers, exploratory), and Murray's average is higher but streakier. | PJ-C005, PJ-C006, PJ-C010, PJ-C011 |
| 7. The exception | 2021–22: the one run where his rate truly jumped (99th percentile, above every 17-game regular-season stretch). His worst runs were short. | PJ-C007, PJ-C008 |
| 8. End | Playoff Jimmy is real as a player who doesn't shrink, not one who transforms. | PJ-C005 |

Available for a series-level scene or a short: the 2023 run series by series
(PJ-C009).

Wording rules from the methods review: say "holds his scoring rate better
than most", never "scores more in the playoffs" (per minute) or "clutch";
label the career ranking as a later, exploratory check.

## Scene table

| Scene | Viewer question | Claims | Visual (design system decides the look) | Why next? |
|---|---|---|---|---|
| S01 Cold open | Why do people call him Playoff Jimmy? | C002, C009 | Big-number reveal 22.9 → 26.9; Milwaukee 37.6 flashes; title card | The obvious answer is waiting. |
| S02 The obvious answer | So he scores more? | C002, C003 | Before → after points per game; minutes 33.4 → 39.7 slides in beside it | The second number demands an explanation. |
| S03 It's the minutes | Or does he just play more? | C003, C004 | Rectangle: width = minutes, height = scoring rate, area = points per game; it widens, barely rises; split +4.3 / −0.3 | "Myth busted" is too early without a baseline. |
| S04 What normally happens | Is a flat rate good or bad? | C001 | All 1,325 player-seasons as a distribution; median line at −1.5; share below zero | The question changes. |
| S05 The fairer test | Does he shrink less than everyone else? | C005, C004 | Season-by-season dot strip, Butler highlighted; running tally to 8 of 11; −0.25 vs −1.70 | Passing the test invites a harder look. |
| S06 Slow down | Could it be luck? Is he special? | C005, C006, C010, C011 | Coin flips; career ranking top 7 (labeled exploratory); Murray's run percentiles | One season breaks the pattern. |
| S07 The exception | Did he ever really transform? | C007, C008 | 2021–22 run against the band of 17-game stretches; short runs flagged | Time for the verdict. |
| S08 Verdict | So, is it real? | C001, C003, C005 | Rectangle returns: wider, not taller; closing card with sources | End. |

Every number on screen is read from `analysis/results.json` through the
claim's keys, never typed into scene code.

## Script (draft v1)

### S01 Cold open

> The 2022–23 season. Jimmy Butler finishes the regular season averaging 22.9 points a game. [PJ-C002]
> Then the playoffs start, and the number jumps to 26.9. [PJ-C002]
> The first round, against Milwaukee, becomes legend: 37.6 points a game. [PJ-C009]
> By the end, Miami is in the Finals, and everyone has a name for what they just watched. Playoff Jimmy.
> So here's the question. Is Playoff Jimmy real? Not "did he have a great month". Does Jimmy Butler actually become a better scorer when the playoffs start?

### S02 The obvious answer

> The obvious answer is yes. He went from 22.9 points a game to 26.9, a rise of 4.0 points, in the games that matter most. [PJ-C002, PJ-C003]
> But points per game has a hidden ingredient, and in the playoffs that ingredient changes a lot.
> In the regular season Butler played 33.4 minutes a game. In the playoffs, 39.7. [PJ-C002]

### S03 It's the minutes

> Think of points per game as a rectangle. The width is minutes. The height is how fast you score while you're on the floor. The area is points per game.
> In the playoffs, Butler's rectangle got wider. It barely got taller.
> Of that 4.0-point rise, 4.3 points go with the extra minutes. His scoring rate actually subtracted a little: −0.3. [PJ-C003]
> Measured per 36 minutes, his scoring barely moved: 24.7 in the regular season, 24.4 in the playoffs. [PJ-C004]
> Same scorer. More minutes.
> So is Playoff Jimmy a myth? That's where a lot of takes stop. We're not stopping there.

### S04 What normally happens

> Before we call anything a myth, we need to know what normally happens to a player's scoring when the playoffs start.
> So we took every player since 2011–12 who logged at least 1,500 regular-season minutes and 100 playoff minutes in the same season. That's 1,325 player-seasons. [PJ-C001]
> The typical player scored 1.5 fewer points per 36 minutes in the playoffs than in his own regular season, and 73% of them declined. [PJ-C001]
> Tougher defenses, slower games, heavier legs: we can't separate those reasons here. But the pattern is clear. Most players shrink in the playoffs.
> Which changes the question. It isn't "does Butler score more in the playoffs?" It's "does he shrink less than everyone else?"

### S05 The fairer test

> Here's every eligible player, season by season. Each dot is one player's change in scoring rate. The highlighted dot is Butler.
> Across his 11 eligible playoff runs, from 2012–13 to 2024–25, Butler's scoring rate fell by 0.25 points per 36. The typical player in those same seasons fell by 1.70. [PJ-C005]
> He beat that season's typical player in 8 of the 11 runs. [PJ-C005]
> Even in 2022–23, when his rate dipped from 24.7 to 24.4, the dip was smaller than most: the 71st percentile of 95 players. [PJ-C004]
> So by the rule we wrote down before looking at any of this data, Playoff Jimmy passes. He doesn't grow in the playoffs. He holds his scoring better than most players do. [PJ-C005]

### S06 Slow down

> Now, I have to be careful, because 8 out of 11 sounds more convincing than it is. [PJ-C005]
> If each run were a coin flip, you'd get 8 or more heads out of 11 about 11% of the time. That's not nothing. It's also not proof. [PJ-C005]
> He's also not unique. After seeing these results, I ran one more check: every player with at least eight playoff runs since 2011–12. There are 29 of them, and Butler ranks 7th at holding his scoring rate. [PJ-C006]
> Ahead of him: Andre Iguodala, Marcus Smart, Donovan Mitchell, Chris Paul, Draymond Green and Nikola Jokić. [PJ-C006]
> And then there's the player on the other side of those Finals.
> Jamal Murray's average is higher than Butler's in every way we sliced it. [PJ-C011]
> But Murray's runs swing. His rate beat his peers in 2018–19, 2019–20 and 2022–23, at the 86th, 97th and 92nd percentiles, then fell behind them in each of the last three seasons: 15th, 45th and 34th. [PJ-C010]
> Murray has the higher peaks. Butler has been above the middle more often. Neither one reliably turns into a different scorer. [PJ-C010, PJ-C011]

### S07 The exception

> There is one season where Butler really did transform: 2021–22. [PJ-C007]
> His scoring rate went from 22.7 points per 36 to 26.7, the 99th percentile that season. [PJ-C007]
> We checked it against every 17-game stretch of his own regular season. The playoff run beat all of them. [PJ-C007]
> His worst runs were short ones: 5 games in 2017–18 and 4 games in 2020–21. Small samples swing hard in both directions. [PJ-C008]

### S08 Verdict

> So, is Playoff Jimmy real?
> If you mean a player who turns into someone else in April: mostly, no. His points per game rise because his minutes do. [PJ-C003]
> But if you mean a player who doesn't shrink when the games get harder, that holds up. Most players get smaller in the playoffs. Jimmy Butler, mostly, stays the same size. [PJ-C001, PJ-C005]
> That's less exciting than a transformation. But in a league where most players shrink, staying the same size is worth noticing.
> Every number in this video, the data behind it and the checks we ran are linked in the description.

## Timing

Scratch read by `say -r 160` (a machine voice at about 160 words a minute);
a human read will differ, and chart holds add time on screen.

| Scene | Words | At 150 wpm | Machine read |
|---|---:|---:|---:|
| S01 Cold open | 82 | 0:33 | 0:33 |
| S02 The obvious answer | 56 | 0:22 | 0:21 |
| S03 It's the minutes | 98 | 0:39 | 0:37 |
| S04 What normally happens | 114 | 0:46 | 0:43 |
| S05 The fairer test | 117 | 0:47 | 0:49 |
| S06 Slow down | 180 | 1:12 | 1:08 |
| S07 The exception | 67 | 0:27 | 0:31 |
| S08 Verdict | 99 | 0:40 | 0:31 |
| **Long-form narration** | 813 | 5:25 | 5:13 |
| Short A | 70 | 0:28 | 0:32 |
| Short B | 62 | 0:25 | 0:25 |
| Short C | 72 | 0:29 | 0:28 |
| Short D | 65 | 0:26 | 0:30 |

With chart holds the long film should land around 6½–7½ minutes and each
short around 35–45 seconds. Measured 2026-09-28.

## Short-form adaptations

Each short stands alone: its own hook, one supported finding, the scope
caption on screen for the whole short, and a payoff. Same claims and results
as the long film.

### Short A: He didn't score more. He played more.

Scope caption: Jimmy Butler, 2022–23 regular season vs playoffs. Data: Basketball-Reference.

> Jimmy Butler went from 22.9 points a game in the 2022–23 regular season to 26.9 in the playoffs. [PJ-C002]
> Playoff Jimmy, right? Now look at his minutes: 33.4 a game, then 39.7. [PJ-C002]
> Per 36 minutes, his scoring went from 24.7 to 24.4. [PJ-C004]
> He didn't score faster. He played longer. Of his 4.0-point rise, 4.3 came with the minutes. [PJ-C003]
> But that's not the whole story. The full video asks the fairer question.

### Short B: Most players shrink in the playoffs

Scope caption: Players with at least 1,500 regular-season and 100 playoff minutes, 2011–12 to 2025–26. Points per 36 minutes.

> Here's something most fans miss: most players score less per minute in the playoffs. [PJ-C001]
> Since 2011–12, the typical high-minute player has dropped 1.5 points per 36 minutes, and 73% declined. [PJ-C001]
> Jimmy Butler? Across 11 playoff runs, he dropped 0.25. [PJ-C005]
> He beat the typical player in 8 of the 11. Playoff Jimmy isn't a player who grows. He's a player who doesn't shrink. [PJ-C005]

### Short C: Who holds up best in the playoffs?

Scope caption: Exploratory. 29 players with at least eight eligible playoff runs, 2011–12 to 2025–26; each run compared with same-season peers.

> Which players hold their scoring best when the playoffs start?
> We took the 29 players with at least eight playoff runs since 2011–12 and compared every run with everyone else that season. [PJ-C006]
> The top of the list: Andre Iguodala, Marcus Smart, Donovan Mitchell, Chris Paul, Draymond Green, Nikola Jokić. [PJ-C006]
> And 7th: Jimmy Butler. [PJ-C006]
> We built this ranking after seeing our main results, so treat it as a second look, not a verdict.

### Short D: The series that built a legend

Scope caption: Jimmy Butler, 2022–23 playoffs by series. Game logs: Basketball-Reference.

> In the first round of the 2022–23 playoffs, Jimmy Butler scored 37.6 points a game against Milwaukee. [PJ-C009]
> That's the series everyone remembers.
> The next three series: 24.6, 24.7 and 21.6. [PJ-C009]
> In the Finals against Denver, he scored 18.9 points per 36 minutes, below his regular-season 24.7. [PJ-C009]
> One legendary series. Over the whole run, per minute, he was the same scorer as in the regular season. [PJ-C004]

## Interactive companion

One control: which seasons count (all runs, shared seasons, runs of at least
100 minutes) and which peers (all eligible, or 20+ point scorers). The viewer
watches Butler's and Murray's results move, or not. Values come from
`analysis/results.json`; the page does no statistics of its own.
