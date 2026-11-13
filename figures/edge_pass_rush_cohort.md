# EDGE pass-rush cohort exclusions

Start with the 66 roster DE/OLB players recorded in `PASS_RUSH_DRILL`. Exclude
a player if `INTERIOR_LINE` accounts for **more than 50%** of their known
defensive alignments in the supplied 2023–2025 NFL regular-season data.
Count one row per player/play; exclude nullified plays, postseason games, and
missing/`NA` alignment labels. Use all available seasons per player, not only
the rookie season. This is an NFL usage definition of role, not a college-role
classification. No get-off values or performance outcomes determine exclusion.

| Removed player | Draft year | Interior snaps / known defensive snaps | Interior share | Drill reps removed |
| --- | ---: | ---: | ---: | ---: |
| Tyler Lacy | 2023 | 523 / 698 | 74.9% | 2 |
| Dante Stills | 2023 | 1,340 / 1,537 | 87.2% | 2 |
| Jalen Redmond | 2023 | 655 / 957 | 68.4% | 2 |
| Braden Fiske | 2024 | 946 / 1,144 | 82.7% | 1 |
| Justin Eboigbe | 2024 | 321 / 414 | 77.5% | 1 |
| Elijah Roberts | 2025 | 458 / 488 | 93.9% | 2 |

The cohort is now **60 players and 116 recorded drill reps**, down from 66 and
126. Of these, 59 players have 112 usable reps under the unchanged onset rule,
and 52 players have two usable reps. All 55 players with multiple recorded reps
cover both mirrored directions.

Keion White (36.2% interior) and Tyrion Ingram-Dawkins (35.6% interior) remain:
both line up at EDGE on a majority of qualifying recorded snaps. Other retained
players can also take interior snaps; the exclusion targets a majority role.

Ten players have no qualifying regular-season alignment observations and remain
provisionally included: Habakkuk Baldonado, Ikenna Enechukwu, Lonnie Phelps,
Bralen Trice, Nelson Ceaser, Trajan Jeffcoat, Ahmed Hassanein,
Antwaun Powell-Ryland, David Walker, and Jah Joyner. Missing observations are
not evidence of an interior role or verified evidence of an EDGE role.

The rule is shared by `exploratory_scripts/edge_pass_rush_cohort.py` and used by
both the movement and setup audits. Re-running them writes all 66 candidates,
snap counts, fractions, exclusion decisions, and evidence flags to
`data/edge_pass_rush_cohort.csv`; the six exclusions are also written to
`data/edge_pass_rush_interior_exclusions.csv`. Movement, setup, and paired-review
outputs have been regenerated. The underlying source datasets are unchanged.
