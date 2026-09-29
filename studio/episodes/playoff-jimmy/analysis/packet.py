"""Results packet for the PJ-04 review: plain charts and tables, no styling for video.

Reads only results.json (whose SHA-256 is stamped in the footer) and writes a
self-contained HTML page. Nothing is recomputed here except display values.

    python3 analysis/packet.py                      # analysis/results.json -> analysis/packet/index.html
    python3 analysis/packet.py --results R --out D
"""

import argparse
import hashlib
import html
import json
from pathlib import Path


ANALYSIS = Path(__file__).resolve().parent
SUBJECT_IDS = {"butler": "butleji01", "murray": "murraja01"}
W, LEFT, RIGHT = 880, 118, 118
PLOT = W - LEFT - RIGHT
ROW = 26


def esc(value):
    return html.escape(str(value), quote=True)


def num(value, digits=1, sign=False):
    if value is None:
        return "—"
    text = ("%+.*f" if sign else "%.*f") % (digits, value)
    return text.replace("-", "−")


def ordinal(p):
    if p is None:
        return "—"
    n = int(round(p))
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return "%d%s" % (n, suffix)


class Scale:
    def __init__(self, lo, hi):
        self.lo, self.hi = lo, hi

    def __call__(self, value):
        value = min(max(value, self.lo), self.hi)
        return LEFT + (value - self.lo) / (self.hi - self.lo) * PLOT


def x_axis(scale, step, top, bottom, zero=False):
    parts, value = [], scale.lo
    while value <= scale.hi + 1e-9:
        x = scale(value)
        css = "baseline" if zero and abs(value) < 1e-9 else "grid"
        parts.append('<line class="%s" x1="%.1f" x2="%.1f" y1="%d" y2="%d"/>' % (css, x, x, top, bottom))
        parts.append('<text class="tick" x="%.1f" y="%d" text-anchor="middle">%s</text>'
                     % (x, bottom + 15, num(value, 0, sign=zero and value != 0)))
        value += step
    return parts


def svg(height, parts, label):
    return ('<svg viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg>'
            % (W, height, esc(label), "".join(parts)))


def row_label(y, text):
    return '<text class="label" x="%d" y="%.1f" text-anchor="end">%s</text>' % (LEFT - 12, y + 4, esc(text))


def note(y, text, css="note"):
    return '<text class="%s" x="%d" y="%.1f">%s</text>' % (css, W - RIGHT + 12, y + 4, esc(text))


def dot(x, y, css, title, r=5):
    return '<circle class="%s" cx="%.1f" cy="%.1f" r="%s"><title>%s</title></circle>' % (css, x, y, r, esc(title))


def hbar(x0, x1, y, height, css, title, radius=4):
    """Horizontal bar from the zero baseline with a rounded data end only."""
    length = abs(x1 - x0)
    r = min(radius, length, height / 2)
    d = 1 if x1 >= x0 else -1
    tip = x1 - d * r
    path = ("M%.1f %.1f H%.1f Q%.1f %.1f %.1f %.1f V%.1f Q%.1f %.1f %.1f %.1f H%.1f Z"
            % (x0, y, tip, x1, y, x1, y + r, y + height - r, x1, y + height, tip, y + height, x0))
    return '<path class="%s" d="%s"><title>%s</title></path>' % (css, path, esc(title))


def legend(items):
    keys = "".join('<span class="key"><span class="swatch %s"></span>%s</span>' % (css, esc(text)) for css, text in items)
    return '<div class="legend">%s</div>' % keys


def table(headers, rows, numeric_from=1):
    head = "".join("<th%s>%s</th>" % (' class="n"' if i >= numeric_from else "", esc(h)) for i, h in enumerate(headers))
    body = "".join("<tr>%s</tr>" % "".join("<td%s>%s</td>" % (' class="n"' if i >= numeric_from else "", esc(c))
                                               for i, c in enumerate(r)) for r in rows)
    return '<div class="scroll"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (head, body)


def details(summary, content):
    return "<details><summary>%s</summary>%s</details>" % (esc(summary), content)


# ---- charts --------------------------------------------------------------------

def paired(results, name):
    return [r for r in results["subjects"][name] if r.get("measures")]


def dumbbell(results, name):
    rows = paired(results, name)
    scale, top = Scale(0, 32), 12
    bottom = top + ROW * len(rows)
    parts = x_axis(scale, 4, top, bottom)
    for i, row in enumerate(rows):
        m, y = row["measures"], top + ROW * i + ROW / 2
        a, b = m["regular"]["points_per_36"], m["playoffs"]["points_per_36"]
        tip = "%s %s: %s → %s points per 36 (%d playoff games, %d minutes)" % (
            name.title(), row["season"], num(a), num(b), m["playoff_games"], m["playoff_minutes"])
        parts += [row_label(y, row["season"]),
                  '<line class="connector" x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f"/>' % (scale(a), scale(b), y, y),
                  dot(scale(a), y, "open " + name, tip), dot(scale(b), y, "fill " + name, tip),
                  note(y, "%s · %d min" % (num(m["delta_points_per_36"], sign=True), m["playoff_minutes"]))]
    return svg(bottom + 26, parts, "%s points per 36, regular season to playoffs" % name.title())


def components(results, name):
    rows = paired(results, name)
    scale, top = Scale(-10, 6), 12
    bottom = top + ROW * len(rows)
    parts = x_axis(scale, 2, top, bottom, zero=True)
    for i, row in enumerate(rows):
        m, y = row["measures"], top + ROW * i + ROW / 2
        split = m["ppg_decomposition"]
        parts += [row_label(y, row["season"]),
                  hbar(scale(0), scale(split["minutes_component"]), y - 9, 8, "bar minutes",
                       "%s %s minutes part: %s PPG" % (name.title(), row["season"], num(split["minutes_component"], 2, True))),
                  hbar(scale(0), scale(split["rate_component"]), y + 1, 8, "bar rate",
                       "%s %s rate part: %s PPG" % (name.title(), row["season"], num(split["rate_component"], 2, True))),
                  note(y, "PPG %s" % num(m["delta_ppg"], sign=True))]
    return svg(bottom + 26, parts, "%s change in points per game split into minutes and rate" % name.title())


def benchmark_chart(results):
    per = {name: {r["season"]: r for r in results["benchmark"][name]["per_season"]["A_100"]} for name in SUBJECT_IDS}
    seasons = sorted(s for s in results["peers_primary_threshold"]
                     if any(per[n].get(s, {}).get("eligible") for n in SUBJECT_IDS))
    scale, top, row = Scale(-15, 12), 12, 32
    bottom = top + row * len(seasons)
    parts = x_axis(scale, 3, top, bottom, zero=True)
    for i, season in enumerate(seasons):
        y = top + row * i + row / 2
        parts.append(row_label(y, season))
        peers = [p for p in results["peers_primary_threshold"][season] if p["player"] not in SUBJECT_IDS.values()]
        low = sum(p["delta_points_per_36"] < scale.lo for p in peers)
        high = sum(p["delta_points_per_36"] > scale.hi for p in peers)
        for j, p in enumerate(peers):
            parts.append(dot(scale(p["delta_points_per_36"]), y + (j * 7 % 15) - 7, "peer",
                             "%s: %s per 36" % (p["name"], num(p["delta_points_per_36"], sign=True)), r=2.6))
        if low:
            parts.append('<text class="tick" x="%d" y="%.1f" text-anchor="end">◂%d</text>' % (LEFT - 2, y - 8, low))
        if high:
            parts.append('<text class="tick" x="%d" y="%.1f">%d▸</text>' % (W - RIGHT + 2, y - 8, high))
        ref = next(per[n][season] for n in SUBJECT_IDS if per[n].get(season, {}).get("eligible"))
        ref_name = next(n for n in SUBJECT_IDS if per[n].get(season, {}).get("eligible"))
        x = scale(ref["peer_median"])
        parts.append('<line class="median" x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f"><title>Peer median %s (peers excluding %s)</title></line>'
                     % (x, x, y - 11, y + 11, num(ref["peer_median"], 2, True), ref_name.title()))
        labels = []
        for name in SUBJECT_IDS:
            r = per[name].get(season)
            if r and r["eligible"]:
                parts.append(dot(scale(r["delta_points_per_36"]), y, "fill " + name,
                                 "%s %s: %s per 36, %s percentile (%s)" % (name.title(), season,
                                 num(r["delta_points_per_36"], 1, True), ordinal(r["percentile"]), r["wording"]), r=5.5))
                labels.append((name, ordinal(r["percentile"])))
        for k, (name, text) in enumerate(labels):
            xk = W - RIGHT + 14 + k * 52
            parts.append('<circle class="fill %s" cx="%d" cy="%.1f" r="4"/>' % (name, xk, y))
            parts.append('<text class="note" x="%d" y="%.1f">%s</text>' % (xk + 8, y + 4, text))
    return svg(bottom + 26, parts, "Change in points per 36 for every eligible player, by season")


def variability_chart(results):
    rows = results["variability"]
    scale, top = Scale(5, 35), 12
    bottom = top + ROW * len(rows)
    parts = x_axis(scale, 5, top, bottom)
    for i, v in enumerate(rows):
        y, q = top + ROW * i + ROW / 2, v["window_quantiles"]
        parts += [row_label(y, "%s %s" % (v["player"].title(), v["season"])),
                  '<rect class="band-outer" x="%.1f" y="%.1f" width="%.1f" height="8" rx="4"><title>5th–95th percentile of %d stretches: %s–%s</title></rect>'
                  % (scale(q["p05"]), y - 4, scale(q["p95"]) - scale(q["p05"]), v["n_windows"], num(q["p05"]), num(q["p95"])),
                  '<rect class="band-inner" x="%.1f" y="%.1f" width="%.1f" height="8"><title>Middle half of stretches: %s–%s</title></rect>'
                  % (scale(q["p25"]), y - 4, scale(q["p75"]) - scale(q["p25"]), num(q["p25"]), num(q["p75"])),
                  '<line class="median" x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f"/>' % (scale(q["p50"]), scale(q["p50"]), y - 7, y + 7),
                  dot(scale(v["playoff_points_per_36"]), y, "fill " + v["player"],
                      "%s %s playoffs: %s per 36 over %d games" % (v["player"].title(), v["season"],
                      num(v["playoff_points_per_36"]), v["playoff_games"])),
                  note(y, "%s pct" % ordinal(v["window_percentile_of_playoff_run"]))]
    return svg(bottom + 26, parts, "Playoff points per 36 against same-length regular-season stretches")


def series_chart(results):
    block = results["series_2022_23"]
    rounds = max(len(b["series"]) for b in block.values())
    scale, top = Scale(10, 40), 30
    bottom = top + 34 * rounds
    parts = x_axis(scale, 5, top, bottom)
    for k, name in enumerate(SUBJECT_IDS):
        x = scale(block[name]["regular_points_per_36"])
        parts.append('<line class="ref %s" x1="%.1f" x2="%.1f" y1="%d" y2="%d"/>' % (name, x, x, top - 6, bottom))
        parts.append('<text class="note" x="%.1f" y="%d" text-anchor="middle">%s regular season %s</text>'
                     % (x, 10 + k * 12, name.title(), num(block[name]["regular_points_per_36"])))
    for i in range(rounds):
        y = top + 34 * i + 17
        parts.append(row_label(y, "Round %d" % (i + 1)))
        opponents = []
        for name in SUBJECT_IDS:
            if i >= len(block[name]["series"]):
                continue
            s = block[name]["series"][i]
            opponents.append(s["opponent"])
            parts.append(dot(scale(s["points_per_36"]), y, "fill " + name,
                             "%s vs %s: %s per 36, %s PPG in %d games" % (name.title(), s["opponent"],
                             num(s["points_per_36"]), num(s["ppg"]), s["games"]), r=5.5))
        parts.append(note(y, "vs " + " / ".join(opponents)))
    return svg(bottom + 26, parts, "2022-23 points per 36 by playoff series")


# ---- page ------------------------------------------------------------------------

CSS = """
:root { color-scheme: light;
  --page:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink-2:#52514e; --muted:#898781;
  --grid:#e1e0d9; --axis:#c3c2b7; --border:rgba(11,11,11,.10);
  --butler:#2a78d6; --murray:#eb6834; --minutes:#1baf7a; --rate:#4a3aa7;
  --peer:#898781; --band-outer:#e1e0d9; --band-inner:#c3c2b7; --good:#006300; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { color-scheme: dark;
  --page:#0d0d0d; --surface:#1a1a19; --ink:#ffffff; --ink-2:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,.10);
  --butler:#3987e5; --murray:#d95926; --minutes:#199e70; --rate:#9085e9;
  --peer:#898781; --band-outer:#2c2c2a; --band-inner:#52514e; --good:#0ca30c; } }
:root[data-theme="dark"] { color-scheme: dark;
  --page:#0d0d0d; --surface:#1a1a19; --ink:#ffffff; --ink-2:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,.10);
  --butler:#3987e5; --murray:#d95926; --minutes:#199e70; --rate:#9085e9;
  --peer:#898781; --band-outer:#2c2c2a; --band-inner:#52514e; --good:#0ca30c; }
* { box-sizing: border-box; }
body { margin:0; background:var(--page); color:var(--ink);
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 960px; margin: 0 auto; padding: 24px 16px 64px; }
h1 { font-size: 26px; margin: 0 0 4px; } h2 { font-size: 19px; margin: 40px 0 4px; }
h3 { font-size: 15px; margin: 18px 0 6px; color: var(--ink-2); }
p { margin: 6px 0; max-width: 72ch; } .sub { color: var(--ink-2); }
.status { border:1px solid var(--border); background:var(--surface); border-radius:8px; padding:12px 14px; margin:16px 0; }
.card { background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:12px 12px 4px; margin:10px 0; }
.stats { display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:10px; margin:14px 0; }
.stat { background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:10px 12px; }
.stat .v { font-size: 24px; font-weight: 600; } .stat .l { color: var(--ink-2); font-size: 13px; }
svg { width:100%; height:auto; display:block; }
svg text { font: 12px system-ui, -apple-system, "Segoe UI", sans-serif; }
.tick { fill: var(--muted); font-variant-numeric: tabular-nums; } .label { fill: var(--ink-2); }
.note { fill: var(--ink-2); font-variant-numeric: tabular-nums; }
.grid { stroke: var(--grid); stroke-width:1; } .baseline { stroke: var(--axis); stroke-width:1; }
.connector { stroke: var(--axis); stroke-width:2; stroke-linecap: round; }
.median { stroke: var(--ink-2); stroke-width:2; stroke-linecap: round; }
.ref { stroke-width:1; } .ref.butler { stroke: var(--butler); } .ref.murray { stroke: var(--murray); }
circle.fill { stroke: var(--surface); stroke-width:2; }
circle.fill.butler { fill: var(--butler); } circle.fill.murray { fill: var(--murray); }
circle.open { fill: var(--surface); stroke-width:2; }
circle.open.butler { stroke: var(--butler); } circle.open.murray { stroke: var(--murray); }
circle.peer { fill: var(--peer); fill-opacity:.45; }
.bar.minutes { fill: var(--minutes); } .bar.rate { fill: var(--rate); }
.band-outer { fill: var(--band-outer); } .band-inner { fill: var(--band-inner); }
.legend { display:flex; flex-wrap:wrap; gap:6px 18px; font-size:13px; color:var(--ink-2); margin:4px 0 6px; }
.key { display:inline-flex; align-items:center; gap:6px; }
.swatch { width:12px; height:12px; border-radius:50%; display:inline-block; }
.swatch.butler { background:var(--butler); } .swatch.murray { background:var(--murray); }
.swatch.open-butler { border:2px solid var(--butler); } .swatch.open-murray { border:2px solid var(--murray); }
.swatch.minutes { background:var(--minutes); border-radius:3px; } .swatch.rate { background:var(--rate); border-radius:3px; }
.swatch.peer { background:var(--peer); opacity:.6; width:8px; height:8px; }
.swatch.median { background:var(--ink-2); width:3px; height:14px; border-radius:1px; }
.swatch.band { background:linear-gradient(90deg, var(--band-outer) 0 30%, var(--band-inner) 30% 70%, var(--band-outer) 70%); width:30px; height:8px; border-radius:4px; }
details { margin: 4px 0 10px; } summary { cursor:pointer; color:var(--ink-2); font-size:13px; }
.scroll { overflow-x:auto; }
table { border-collapse: collapse; font-size: 13px; margin: 8px 0; min-width: 100%; }
th, td { padding: 4px 8px; border-bottom: 1px solid var(--grid); text-align: left; white-space: nowrap; }
th { color: var(--ink-2); font-weight: 600; } td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; }
footer { margin-top: 40px; color: var(--muted); font-size: 12px; word-break: break-all; }
"""


def build(results, results_sha256):
    bench, ctx = results["benchmark"], results["benchmark_context"]
    sets = results["season_sets"]
    leader = results["comparison"]["leader_in_every_set"]
    b100, m100 = bench["butler"]["career"]["A_100"], bench["murray"]["career"]["A_100"]
    stats = [
        (num(ctx["100"]["median_delta_per_36"], 2, True),
         "Typical change in points per 36 for eligible players, 2011–12 to 2025–26 (n = %d; %d%% declined)"
         % (ctx["100"]["n_player_seasons"], round(100 * ctx["100"]["share_below_zero"]))),
        (num(b100["pooled_excess_per_36"], 2, True),
         "Butler, pooled over %d eligible runs (%s playoff minutes); peer median for his seasons %s"
         % (b100["n_eligible_seasons"], "{:,}".format(b100["playoff_minutes"]), num(b100["minute_weighted_peer_median"], 2, True))),
        (num(m100["pooled_excess_per_36"], 2, True),
         "Murray, pooled over %d eligible runs (%s playoff minutes); peer median for his seasons %s"
         % (m100["n_eligible_seasons"], "{:,}".format(m100["playoff_minutes"]), num(m100["minute_weighted_peer_median"], 2, True))),
    ]
    rules = []
    for name in SUBJECT_IDS:
        for key, c in bench[name]["career"].items():
            rules.append([name.title(), "Peers %s, ≥%s playoff min" % tuple(key.split("_")), c["n_eligible_seasons"],
                          num(c.get("pooled_excess_per_36"), 2, True), num(c.get("minute_weighted_peer_median"), 2, True),
                          "%s of %d" % (c.get("seasons_above_peer_median", 0), c["n_eligible_seasons"]),
                          "yes" if c["condition_met"] else "no"])
    verdicts = " ".join("<b>%s:</b> %s." % (name.title(), "met in all four versions" if bench[name]["real_per_minute_rule_met"]
                                            else "not met in all four versions") for name in SUBJECT_IDS)
    per_season = []
    for name in SUBJECT_IDS:
        pct = {r["season"]: r for r in bench[name]["per_season"]["A_100"]}
        for row in paired(results, name):
            m = row["measures"]
            a, b, split = m["regular"], m["playoffs"], m["ppg_decomposition"]
            p = pct[row["season"]]
            per_season.append([name.title(), row["season"], m["playoff_games"], m["playoff_minutes"],
                               "%s → %s" % (num(a["ppg"]), num(b["ppg"])), "%s → %s" % (num(a["points_per_36"]), num(b["points_per_36"])),
                               num(m["delta_points_per_36"], 1, True), num(split["minutes_component"], 1, True),
                               num(split["rate_component"], 1, True), "%s → %s" % (num(a["tsa_per_36"]), num(b["tsa_per_36"])),
                               "%s → %s" % (num(a["approx_ts"], 3), num(b["approx_ts"], 3)),
                               ordinal(p["percentile"]) if p["eligible"] else "not eligible", p["wording"] or "—"])
    set_rows = [[s.replace("_", " "), name.title(), sets[s][name]["n_seasons"], "{:,}".format(sets[s][name]["playoff_minutes"]),
                 num(sets[s][name]["excess_points"], 1, True), num(sets[s][name]["excess_per_36"], 2, True),
                 num(sets[s][name]["equal_season_mean_delta_per_36"], 2, True)]
                for s in ("all_paired", "shared", "min_100_playoff_minutes") for name in SUBJECT_IDS]
    var_rows = [[v["player"].title(), v["season"], v["playoff_games"], num(v["playoff_points_per_36"]), v["n_windows"],
                 "%s–%s" % (num(v["window_quantiles"]["p05"]), num(v["window_quantiles"]["p95"])),
                 num(v["window_quantiles"]["p50"]), ordinal(v["window_percentile_of_playoff_run"])] for v in results["variability"]]
    series_rows = [[name.title(), s["round"], s["opponent"], s["games"], num(s["ppg"]), num(s["mpg"]), num(s["points_per_36"]),
                    num(s["approx_ts"], 3)] for name, blk in results["series_2022_23"].items() for s in blk["series"]]
    recon = results["reconciliation"]
    guide_counts = {}
    for r in recon["guide_vs_bbref"]:
        guide_counts[r["status"]] = guide_counts.get(r["status"], 0) + 1
    exposure = [[name.title(), r["season"], r["exposure"].replace("_", " "), r["final_team"] or "—"]
                for name in SUBJECT_IDS for r in results["subjects"][name] if r["exposure"] != "paired"]
    players = [("butler", "Butler"), ("murray", "Murray")]

    body = ['<main>',
            '<h1>Playoff Jimmy: results packet</h1>',
            '<p class="sub">Analysis v2 on frozen Basketball-Reference and media-guide data, as pre-registered in METHOD.md.</p>',
            '<div class="status"><b>Methods reviewed (PJ-04).</b> Descriptive results; only statements in CLAIMS.json are '
            'verified claims. Exploratory checks are labeled as such.</div>',
            '<h2>Headline numbers</h2>',
            '<p class="sub">Change in points per 36 minutes, playoffs minus the same season\'s regular season, weighted by playoff minutes. '
            'Eligible means at least 1,500 regular-season and 100 playoff minutes.</p>',
            '<div class="stats">%s</div>' % "".join('<div class="stat"><div class="v">%s</div><div class="l">%s</div></div>'
                                                   % (esc(v), esc(l)) for v, l in stats),
            '<p>Pre-registered rule for calling the per-minute effect "real" (pooled change above the peer median <i>and</i> a majority of '
            'seasons above their peer median, for both peer groups and both minute thresholds). %s</p>' % verdicts,
            table(["Player", "Version", "Eligible runs", "Pooled Δ/36", "Peer median", "Seasons above median", "Condition met"], rules, 2),
            '<p>Raw pooled comparison across the three season sets: <b>%s</b> has the higher pooled change in every set.</p>'
            % esc(leader.title() if leader else "no single player"),
            table(["Season set", "Player", "Seasons", "Playoff min", "Actual − expected pts", "Pooled Δ/36", "Mean Δ/36 (equal seasons)"], set_rows, 2),

            '<h2>Exploratory checks (not pre-registered)</h2>',
            '<p class="sub">%s</p>' % esc(results["exploratory"]["label"]),
            table(["Player", "Eligible runs", "Runs above peer median", "Chance if each run were a coin flip", "Mean percentile"],
                  [[n.title(), c["n_eligible_seasons"], c["seasons_above_peer_median"], num(c["one_sided_p"], 3),
                    num(c["mean_percentile"], 0)] for n, c in results["exploratory"]["season_count_check"].items()], 1),
            '<p>Career edge: pooled change minus the peer median for the same seasons, for every player with enough eligible runs.</p>',
            "".join(table(["Rank", "Player (at least %d runs; %d players)" % (c["min_eligible_runs"], c["n_players"]),
                           "Runs", "Edge per 36", "Runs above median"],
                          [[i + 1, t["name"], t["runs"], num(t["edge_per_36"], 2, True), t["runs_above_peer_median"]]
                           for i, t in enumerate(c["top_10"])], 2) for c in results["exploratory"]["career_edge"]),

            '<p class="sub">%s</p>' % esc(results["exploratory"]["matched_peers_label"]),
            table(["Player", "Peers", "Pooled Δ/36", "Peer median", "Runs above median", "Chance if coin flips"],
                  [[n.title(), k.replace("_", " "), num(v["career"]["pooled_excess_per_36"], 2, True),
                    num(v["career"]["minute_weighted_peer_median"], 2, True),
                    "%d of %d" % (v["season_count"]["seasons_above_peer_median"], v["season_count"]["n_eligible_seasons"]),
                    num(v["season_count"]["one_sided_p"], 2)]
                   for n, versions in results["exploratory"]["matched_peers"].items() for k, v in versions.items()], 2),

            '<h2>1. Scoring rate, regular season to playoffs</h2>',
            '<p class="sub">Points per 36 minutes. Right column: change, then playoff minutes.</p>']
    for name, title in players:
        body += ['<div class="card"><h3>%s</h3>%s%s</div>' % (title, legend([("open-" + name, "Regular season"), (name, "Playoffs")]),
                                                           dumbbell(results, name))]
    body += ['<h2>2. Where the change in points per game comes from</h2>',
             '<p class="sub">The per-game change split exactly into a minutes part and a scoring-rate part. Descriptive arithmetic, not cause.</p>']
    for name, title in players:
        body += ['<div class="card"><h3>%s</h3>%s%s</div>' % (title, legend([("minutes", "More or fewer minutes"), ("rate", "Higher or lower rate")]),
                                                           components(results, name))]
    body += [details("Table view: per-season measures", table(
                 ["Player", "Season", "Playoff G", "Playoff min", "PPG", "Pts/36", "Δ/36", "Minutes part", "Rate part",
                  "Shot attempts/36", "TS (approx.)", "Percentile", "Wording"], per_season, 2)),
             '<h2>3. Against every eligible player in the same season</h2>',
             '<p class="sub">Gray dots are other eligible players (peer group A, ≥ 100 playoff minutes). The dark tick is the peer median. '
             'Right column: percentile among peers. Arrows count dots beyond the axis.</p>',
             '<div class="card">%s%s</div>' % (legend([("butler", "Butler"), ("murray", "Murray"), ("peer", "Other eligible players"),
                                                       ("median", "Peer median")]), benchmark_chart(results)),
             '<h2>4. Is the playoff run outside normal variation?</h2>',
             '<p class="sub">Each bar is every run of the same number of consecutive regular-season games that season: light = 5th–95th percentile, '
             'dark = middle half, tick = median. The dot is the playoff run. A variability reference, not a significance test.</p>',
             '<div class="card">%s%s</div>' % (legend([("butler", "Butler playoffs"), ("murray", "Murray playoffs"), ("band", "Regular-season stretches")]),
                                               variability_chart(results)),
             details("Table view: variability reference", table(
                 ["Player", "Season", "Playoff G", "Playoff /36", "Stretches", "5th–95th", "Median", "Playoff run percentile"], var_rows, 2)),
             '<h2>5. 2022–23, series by series</h2>',
             '<p class="sub">Points per 36 in each playoff series; vertical lines mark each player\'s regular-season rate. The Finals was Miami against Denver.</p>',
             '<div class="card">%s%s</div>' % (legend([("butler", "Butler"), ("murray", "Murray")]), series_chart(results)),
             details("Table view: 2022–23 series", table(["Player", "Round", "Opponent", "G", "PPG", "MPG", "Pts/36", "TS"], series_rows, 3)),
             '<h2>Data checks</h2>',
             '<p>Media guide against Basketball-Reference: %d rows match exactly, %d differ by one minute, and %d zero-game rows '
             'agree; %d mismatch. Game logs against season totals: %d of %d tables reconcile. Seasons without a paired run are '
             'listed below; missing is never treated as zero.</p>'
             % (guide_counts.get("match", 0), guide_counts.get("minutes_within_1", 0), guide_counts.get("both_no_games", 0),
                guide_counts.get("mismatch", 0), sum(r["status"] == "match" for r in recon["gamelogs_vs_totals"]),
                len(recon["gamelogs_vs_totals"])),
             table(["Player", "Season", "Exposure", "Final team"], exposure, 4),
             '<footer>Generated by analysis/packet.py from results.json (sha256 %s). Status: %s.</footer>'
             % (results_sha256, esc(results["status"])),
             '</main>']
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Playoff Jimmy results packet</title><style>%s</style></head><body>%s</body></html>\n'
            % (CSS, "".join(body)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", type=Path, default=ANALYSIS / "results.json")
    parser.add_argument("--out", type=Path, default=ANALYSIS / "packet")
    args = parser.parse_args(argv)
    raw = args.results.read_bytes()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "index.html").write_text(build(json.loads(raw), hashlib.sha256(raw).hexdigest()))
    print("Wrote %s" % (args.out / "index.html"))


if __name__ == "__main__":
    main()
