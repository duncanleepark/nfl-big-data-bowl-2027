# nfl-big-data-bowl-2027
2027 NFL Big Data Bowl Repository

## EDGE/DT draft models

Build the joined combine and draft table, then fit Model A:

```bash
pip install -r requirements.txt
python build_edge_dt_table.py
python model_a.py
python model_b.py
```

Model A estimates `log(draft pick)` separately for EDGE and DT using
position-normalized combine traits. Missing measurements are retained with
explicit missingness indicators. It writes coefficient and prediction tables
under `data/` and the coefficient plot to `figures/model_a_coefficients.png`.

Model B estimates log-transformed career AV, games, and seasons started from
the same traits while controlling for log draft pick. It uses only rows marked
`outcome_ready` and writes its results to `data/model_b_coefficients.csv`,
`data/model_b_predictions.csv`, and `figures/model_b_coefficients.png`.

## EDGE Combine pass-rush movement audit

Run `python exploratory_scripts/edge_pass_rush_audit.py` to reproduce the
movement audit. It starts with roster DE/OLB and the exact `PASS_RUSH_DRILL`
label, then excludes players with `INTERIOR_LINE` on more than 50% of their
known defensive alignments in supplied 2023–2025 regular-season, non-nullified
plays. Players without qualifying alignment observations remain provisional.
The shared rule and exclusions are documented in the
[cohort review](figures/edge_pass_rush_cohort.md). Each
player/event/attempt is sorted by timestamp. Movement onset is the first of
three consecutive frames at speed >= 1.0 in the source's native units. The
exploratory feature is speed at onset + 0.5 seconds minus speed at onset. The
threshold detects movement rather than the drill cue, and units need to be
confirmed against the data dictionary. Attempts starting at or above the
threshold, with invalid values, missing onset/window, or irregular timestamps
through the window are flagged and excluded. No smoothing is applied.

The script writes attempt-level quality flags and metrics, player-level median
metrics, paired attempts, and a summary under `data/`. It creates a 15-player
example gallery (`figures/edge_pass_rush_examples.png`), selected across draft
years independently of speed gain, and a repeatability plot
(`figures/edge_pass_rush_repeatability.png`). Repeatability compares each
player's first two usable attempts chronologically using absolute-agreement
ICC(A,1), with a player bootstrap interval. The player-level median uses all
usable attempts; it is a provisional aggregation, not a validated measure.

In the filtered cohort, 112 of 116 attempts are usable (59 players); 52 players
have a pair. ICC is 0.058 (player-bootstrap 95% interval -0.205 to 0.409),
and median absolute paired difference is 0.276 source speed units. Some
windows include changes or pauses in motion, and the broad interval reflects
limited precision. This does not establish reliable player-level measurement;
review unusual attempts and alternative onset/phase definitions before using
the metric in an NFL-outcome model. NFL alignment data define the cohort;
no NFL performance outcomes are used to select players or evaluate this metric.

### Drill setup and direction

Run `python exploratory_scripts/edge_pass_rush_setup.py` after the movement
audit to inspect the recorded setup. All 55 retained players with multiple
recordings cover both mirrored path directions. Attempt numbers are not stable
side labels across years, and the 52 usable pairs contain 51
opposite-direction pairs. The ICC above primarily measures agreement across
mirrored reps with uncertain phase alignment, rather than same-side
test-retest reliability. See [the setup audit](figures/edge_pass_rush_setup.md)
and [all recorded paths](figures/edge_pass_rush_setup.png) for counts, geometry,
footage limitations, and the next steps for defining EDGE get-off.

### Combine burst versus rookie NFL get-off

Run `.venv/bin/python exploratory_scripts/edge_get_off.py` to compare
movement-aligned Combine features with supplied rookie-season NFL
`player_get_off` on regular-season EDGE passing plays. It exports attempt flags,
player coverage, direction-specific features, player-bootstrap associations and
a scatterplot. The default requires 20 observed NFL values per player; 36
players qualify. Primary rank correlation is -0.048 (95% interval -0.330 to
0.256), which does not establish a relationship. See [methods and limitations](figures/edge_get_off.md).
The Combine cue, contact phase and exact NFL field definition still need
validation; these are exploratory movement measures, not validated reaction times.

### Official 10-yard baseline and tracked 40s

Run `.venv/bin/python exploratory_scripts/edge_forty_audit.py` for the official
split baseline and a separate tracking quality/repeatability audit. The baseline
includes 27 players: rank correlation 0.440 (95% interval 0.057–0.762) between
official 10-yard split and median rookie NFL get-off. Tracking contains 86 reps
for 46 players; fixed early course-segment times have ICC 0.736 across 40 pairs,
with substantial uncertainty and player sensitivity. These moving-segment times
are not official splits or reaction times. See [the audit](figures/edge_forty_audit.md)
for geometry, quality flags, coverage, uncertainty and remaining validation work.

## WR speed-out and NFL OUT-route coverage

Run `.venv/bin/python exploratory_scripts/wr_out_coverage.py` to build the sample
and coverage tables. `SPEED_OUT_LEFT` and `SPEED_OUT_ROUTE_LEFT` are treated as
the same drill. All 107 Combine WRs have recordings. With observed separation
on rookie regular-season, non-nullified NFL OUT routes aligned at WR or slot,
46 players meet the primary 10-route threshold (1,310 routes), and 24 meet the
20-route sensitivity threshold (991 routes). Targets and non-targets are included.
See [full player coverage and sample funnel](figures/wr_out_coverage.md).
Player, qualifying-route, threshold-sample, and year-summary CSVs are exported
under `data/wr_out_*`; raw Combine recording metadata is in
`data/wr_speed_out_attempts.csv`. These are coverage-qualified samples pending
movement-quality review, not fitted separation models.
