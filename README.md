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
Combine-only audit. It uses roster DE and OLB as a provisional EDGE proxy and
the exact `PASS_RUSH_DRILL` label; some OLBs may not be edge rushers. Each
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

In the current data, 122 of 126 attempts are usable (65 players); 56 players
have a pair. ICC is 0.075 (player-bootstrap 95% interval -0.186 to 0.409),
and median absolute paired difference is 0.276 source speed units. Some
windows include changes or pauses in motion, and the broad interval reflects
limited precision. This does not establish reliable player-level measurement;
review unusual attempts and alternative onset/phase definitions before using
the metric in an NFL-outcome model. No game data are used in this audit.
