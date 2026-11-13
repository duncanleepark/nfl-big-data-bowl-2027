# EDGE initial movement and NFL get-off

Run from the repository root:

```bash
.venv/bin/python exploratory_scripts/edge_get_off.py
```

Optional arguments: `--min-snaps 20 --bootstrap 1000`. The minimum count is an
explicit exploratory coverage choice. The bootstrap is seeded for reproducibility.

The shared cohort rule retains 60 players after six interior-role exclusions.
For Combine tracking, the script preserves the existing movement onset: first
of three consecutive 10 Hz frames at speed >=1.0. It excludes four recordings
already moving above that threshold and holds out Tyrus Wheat's 10.2-second
recording for lead-in review. Duration >6 seconds is a transparent review flag,
not a validated detector of preparatory motion. There are 111 included attempts
from 59 players. Existing audit outputs are not overwritten by this script.

For every included attempt, it measures speed gain over 0.5 seconds (the primary
existing feature), speed gain over 0.3 seconds, speed at 0.3 seconds, and straight
line displacement over 0.3 seconds. Coordinates/speed retain source units. Player
features are medians across included attempts. A separate direction table retains
medians for each mirrored path; cross-direction equivalence is not assumed to
be validated. None of these windows has been independently verified to precede
first bag contact. Time from recording start to onset is not reaction time.

NFL comparison uses `player_play.csv` joined to `games.csv`: rookie season only,
regular season, non-nullified plays, `lined_up_position == EDGE`, and pass results
`C`, `I`, `IN`, `S`, or `R` (including sacks and scrambles). Missing/nonfinite or
negative `player_get_off` values are excluded from the observed outcome, but
eligible-play counts and missingness remain visible in player exports. Values
of exactly 2 are counted separately without assuming whether the field is capped.
At least 20 observed values are required; players remain equally weighted in
correlations regardless of snap count. This is observed EDGE usage on passing
plays, not independently charted pass-rush assignments.

The NFL describes its general NGS get-off concept as elapsed time from snap to
crossing the line of scrimmage in its [Jets media guide](https://static.www.nfl.com/image/upload/league/apps/league-site/media-guides/2023/NYJ.pdf).
The exact competition-field definition, units, treatment of non-crossings, and
potential censoring still require official dictionary verification. Outputs label
the outcome as the supplied `player_get_off` rather than assigning an unverified
dataset-specific definition. It is a different construct from movement-aligned
Combine burst.

The current run has 6,421 eligible rookie EDGE passing plays and 5,660 observed
nonnegative get-off values. Thirty-six players qualify for comparison: 14 from
2023, 11 from 2024, and 11 from 2025. Primary rank correlation is **−0.048**, with
a player bootstrap 95% interval of **[−0.330, 0.256]**. After subtracting draft-year
means from global ranks, the correlation is **0.128 [−0.191, 0.429]**. Bootstrap
resampling is by player within draft year. Every tested feature's interval
includes zero. These exploratory analyses do not establish a relationship or
predictive value; several correlated features are inspected without a multiple
comparison correction. The weak existing cross-rep agreement and uncertain
Combine phase remain major measurement limitations.

The cohort's interior-role exclusion uses all available supplied regular seasons,
whereas this outcome comparison uses the rookie season. Thus cohort selection
uses later NFL role information for some players and is not a prospective
Combine-only scouting evaluation. No body-size, alignment-depth, or team/scheme
adjustment is made; draft-year adjustment alone does not resolve those factors.

Outputs under `data/`:

- `edge_get_off_attempts.csv`: all 116 attempts, flags, movement onset, features.
- `edge_get_off_by_direction.csv`: player feature medians by mirrored path.
- `edge_get_off_players.csv`: all 60 players, coverage and inclusion indicators.
- `edge_get_off_associations.csv`: four features, raw and year-adjusted correlations,
  confidence intervals, and player counts.
- `edge_get_off_summary.txt`: filters, coverage and results.

Plot: `figures/edge_get_off_nfl.png`. Next: match stance, cue, rush start, and first
contact in video, then validate onset/window definitions before player ranking
or model development.

A [pilot video review](edge_video_validation.md) now documents two Latu starts.
Both reach first bag contact within 0.5 seconds of visible launch. Neither shot
has a verified tracking-event/clock match, so no tracking scoring window has
been certified as pre-contact. Exports now explicitly carry that status.
