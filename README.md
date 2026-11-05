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
