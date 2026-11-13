# WR speed-out / NFL OUT coverage

The two Combine drill names are treated as the same drill, as confirmed by the user.
Cohort: combine_position == WR. Qualifying NFL routes: rookie regular season,
non-nullified, lined_up_position WR or SLOT_WR, route_ran OUT, finite nonnegative
separation_at_pass_forward. Targets and non-targets are both included.
Primary threshold: 10 qualifying routes per player. Sensitivity: 20.
These are coverage-qualified samples, not validated movement-quality samples.

## Coverage by draft year

| Year | WRs | Speed-out recordings | Players with qualifying OUT | Qualifying OUT | ≥10 players | ≥20 players |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2023 | 39 | 46 | 29 | 664 | 20 | 10 |
| 2024 | 31 | 37 | 23 | 493 | 15 | 9 |
| 2025 | 37 | 41 | 21 | 277 | 11 | 5 |
| Total | 107 | 124 | 73 | 1434 | 46 | 24 |

## Threshold sample context

| Threshold | Players | Routes | Targeted | Non-targeted | Man | Zone | Unknown coverage | Missing cushion | Multiple Combine reps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ≥10 | 46 | 1310 | 390 | 920 | 370 | 939 | 1 | 43 | 7 |
| ≥20 | 24 | 991 | 305 | 686 | 272 | 718 | 1 | 32 | 4 |

## Funnel

| Stage | Players | Records | Record unit |
| --- | ---: | ---: | --- |
| combine_WR_metadata | 107 | 107 | player |
| has_either_speed_out_alias | 107 | 124 | Combine recording |
| all_supplied_nfl_player_plays | 106 | 43386 | player-play |
| rookie_regular_season_player_plays | 80 | 16931 | player-play |
| non_nullified_rookie_WR_or_slot_plays | 80 | 16450 | player-play |
| NFL_OUT_before_separation_filter | 73 | 1618 | player-play |
| qualifying_NFL_OUT_with_observed_separation | 73 | 1434 | player-play |
| speed_out_plus_at_least_10_qualifying_OUT_routes | 46 | 1310 | player-play |
| speed_out_plus_at_least_20_qualifying_OUT_routes | 24 | 991 | player-play |

## Player-level coverage

| Player | Year | Combine reps | Qualifying OUT | Targeted | Non-targeted | Man | Zone | ≥10 | ≥20 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| A.T. Perry | 2023 | 1 | 16 | 1 | 15 | 1 | 15 | yes | — |
| Andrei Iosivas | 2023 | 1 | 8 | 3 | 5 | 0 | 8 | — | — |
| Antoine Green | 2023 | 1 | 4 | 0 | 4 | 1 | 3 | — | — |
| Bryce Ford-Wheaton | 2023 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Cedric Tillman | 2023 | 2 | 19 | 4 | 15 | 8 | 11 | yes | — |
| Demario Douglas | 2023 | 1 | 33 | 11 | 22 | 15 | 18 | yes | yes |
| Derius Davis | 2023 | 2 | 3 | 1 | 2 | 0 | 3 | — | — |
| Dontay Demus | 2023 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Elijah Higgins | 2023 | 1 | 6 | 2 | 4 | 0 | 6 | — | — |
| Grant DuBose | 2023 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Jacob Copeland | 2023 | 2 | 0 | 0 | 0 | 0 | 0 | — | — |
| Jadon Haselwood | 2023 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Jake Bobo | 2023 | 1 | 17 | 4 | 13 | 2 | 15 | yes | — |
| Jalen Brooks | 2023 | 1 | 1 | 1 | 0 | 0 | 1 | — | — |
| Jalen Wayne | 2023 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Jalin Hyatt | 2023 | 1 | 7 | 4 | 3 | 2 | 5 | — | — |
| Jaray Jenkins | 2023 | 2 | 0 | 0 | 0 | 0 | 0 | — | — |
| Jason Brownlee | 2023 | 1 | 10 | 1 | 9 | 1 | 9 | yes | — |
| Jaxon Smith-Njigba | 2023 | 1 | 59 | 13 | 46 | 18 | 41 | yes | yes |
| Jayden Reed | 2023 | 1 | 44 | 16 | 28 | 15 | 28 | yes | yes |
| Jonathan Mingo | 2023 | 2 | 50 | 14 | 36 | 13 | 37 | yes | yes |
| Jordan Addison | 2023 | 1 | 67 | 29 | 38 | 11 | 56 | yes | yes |
| Joseph Ngata | 2023 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Justin Shorter | 2023 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Kayshon Boutte | 2023 | 1 | 4 | 1 | 3 | 1 | 3 | — | — |
| Malik Heath | 2023 | 2 | 10 | 3 | 7 | 6 | 4 | yes | — |
| Marvin Mims | 2023 | 1 | 12 | 2 | 10 | 1 | 11 | yes | — |
| Michael Wilson | 2023 | 1 | 53 | 9 | 44 | 8 | 45 | yes | yes |
| Mitch Tinsley | 2023 | 2 | 0 | 0 | 0 | 0 | 0 | — | — |
| Puka Nacua | 2023 | 1 | 44 | 12 | 32 | 13 | 31 | yes | yes |
| Quentin Johnston | 2023 | 1 | 16 | 3 | 13 | 2 | 14 | yes | — |
| Rakim Jarrett | 2023 | 1 | 6 | 3 | 3 | 1 | 5 | — | — |
| Rashee Rice | 2023 | 1 | 36 | 11 | 25 | 15 | 21 | yes | yes |
| Ronnie Bell | 2023 | 1 | 9 | 4 | 5 | 2 | 7 | — | — |
| Tank Dell | 2023 | 1 | 41 | 21 | 20 | 6 | 35 | yes | yes |
| Tre Tucker | 2023 | 1 | 10 | 4 | 6 | 3 | 7 | yes | — |
| Trey Palmer | 2023 | 1 | 47 | 11 | 36 | 5 | 42 | yes | yes |
| Tyler Scott | 2023 | 1 | 19 | 5 | 14 | 7 | 12 | yes | — |
| Xavier Hutchinson | 2023 | 1 | 13 | 2 | 11 | 6 | 7 | yes | — |
| Adonai Mitchell | 2024 | 2 | 17 | 9 | 8 | 5 | 12 | yes | — |
| Anthony Gould | 2024 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Brenden Rice | 2024 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Brian Thomas | 2024 | 2 | 66 | 24 | 42 | 17 | 49 | yes | yes |
| Bub Means | 2024 | 1 | 12 | 7 | 5 | 5 | 7 | yes | — |
| Cornelius Johnson | 2024 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Devaughn Vele | 2024 | 1 | 26 | 10 | 16 | 10 | 16 | yes | yes |
| Devontez Walker | 2024 | 1 | 1 | 0 | 1 | 0 | 1 | — | — |
| Isaiah Williams | 2024 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Ja'Lynn Polk | 2024 | 1 | 15 | 4 | 11 | 3 | 12 | yes | — |
| Jacob Cowing | 2024 | 1 | 5 | 0 | 5 | 0 | 5 | — | — |
| Jalen Coker | 2024 | 1 | 42 | 14 | 28 | 15 | 27 | yes | yes |
| Jalen McMillan | 2024 | 1 | 43 | 8 | 35 | 9 | 34 | yes | yes |
| Jamari Thrash | 2024 | 2 | 7 | 3 | 4 | 1 | 6 | — | — |
| Javon Baker | 2024 | 1 | 1 | 0 | 1 | 1 | 0 | — | — |
| Jermaine Burton | 2024 | 2 | 3 | 2 | 1 | 1 | 2 | — | — |
| Jha'Quan Jackson | 2024 | 1 | 1 | 0 | 1 | 1 | 0 | — | — |
| Johnny Wilson | 2024 | 1 | 14 | 2 | 12 | 4 | 10 | yes | — |
| Keon Coleman | 2024 | 1 | 11 | 1 | 10 | 4 | 7 | yes | — |
| Ladd McConkey | 2024 | 1 | 61 | 18 | 43 | 14 | 47 | yes | yes |
| Lideatrick Griffin | 2024 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Luke McCaffrey | 2024 | 1 | 23 | 4 | 19 | 12 | 11 | yes | yes |
| Malik Washington | 2024 | 1 | 18 | 9 | 9 | 5 | 13 | yes | — |
| Marcus Rosemy-Jacksaint | 2024 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Ricky Pearsall | 2024 | 2 | 41 | 14 | 27 | 11 | 30 | yes | yes |
| Roman Wilson | 2024 | 2 | 0 | 0 | 0 | 0 | 0 | — | — |
| Rome Odunze | 2024 | 1 | 41 | 8 | 33 | 13 | 28 | yes | yes |
| Ryan Flournoy | 2024 | 1 | 1 | 0 | 1 | 0 | 1 | — | — |
| Tahj Washington | 2024 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Troy Franklin | 2024 | 1 | 9 | 1 | 8 | 0 | 9 | — | — |
| Xavier Legette | 2024 | 1 | 35 | 12 | 23 | 18 | 17 | yes | yes |
| Andrew Armstrong | 2025 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Antwane Wells | 2025 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Arian Smith | 2025 | 1 | 8 | 2 | 6 | 2 | 6 | — | — |
| Chimere Dike | 2025 | 1 | 28 | 7 | 21 | 6 | 22 | yes | yes |
| Da'Quan Felton | 2025 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Dominic Lovett | 2025 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Dont'e Thornton | 2025 | 1 | 11 | 3 | 8 | 1 | 10 | yes | — |
| Elic Ayomanor | 2025 | 1 | 29 | 10 | 19 | 8 | 21 | yes | yes |
| Elijhah Badger | 2025 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Isaac TeSlaa | 2025 | 1 | 8 | 1 | 7 | 3 | 5 | — | — |
| Isaiah Bond | 2025 | 1 | 19 | 3 | 16 | 9 | 10 | yes | — |
| Isaiah Neyor | 2025 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Ja'Corey Brooks | 2025 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Jack Bech | 2025 | 1 | 18 | 4 | 14 | 5 | 13 | yes | — |
| Jacolby George | 2025 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Jalen Royals | 2025 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Jayden Higgins | 2025 | 1 | 31 | 13 | 18 | 6 | 25 | yes | yes |
| Jaylin Lane | 2025 | 1 | 10 | 2 | 8 | 8 | 2 | yes | — |
| Jaylin Noel | 2025 | 1 | 15 | 4 | 11 | 8 | 7 | yes | — |
| Jimmy Horn | 2025 | 1 | 2 | 1 | 1 | 1 | 1 | — | — |
| Jordan Watkins | 2025 | 1 | 3 | 2 | 1 | 0 | 3 | — | — |
| Josh Kelly | 2025 | 2 | 0 | 0 | 0 | 0 | 0 | — | — |
| Kaden Prather | 2025 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| KeAndre Lambert-Smith | 2025 | 1 | 6 | 2 | 4 | 3 | 3 | — | — |
| Kobe Hudson | 2025 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Konata Mumpfield | 2025 | 2 | 8 | 1 | 7 | 2 | 6 | — | — |
| Kyle Williams | 2025 | 1 | 7 | 2 | 5 | 1 | 6 | — | — |
| LaJohntay Wester | 2025 | 1 | 1 | 0 | 1 | 1 | 0 | — | — |
| Luther Burden | 2025 | 1 | 17 | 8 | 9 | 4 | 13 | yes | — |
| Nick Nash | 2025 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Pat Bryant | 2025 | 2 | 30 | 10 | 20 | 7 | 23 | yes | yes |
| Ricky White | 2025 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Roc Taylor | 2025 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Tai Felton | 2025 | 2 | 3 | 1 | 2 | 1 | 2 | — | — |
| Tez Johnson | 2025 | 1 | 21 | 6 | 15 | 7 | 14 | yes | yes |
| Traeshon Holden | 2025 | 1 | 0 | 0 | 0 | 0 | 0 | — | — |
| Xavier Restrepo | 2025 | 1 | 2 | 0 | 2 | 0 | 2 | — | — |

## Interpretation and limits

Zero counts mean no qualifying observations in these supplied files; they do not
prove a player never ran an OUT route. Missing separation is not imputed as zero.
Missing cushion or coverage does not exclude a route from this coverage audit.
Target and coverage counts are exported with unknown categories for reconciliation.
Use combine_position consistently: roster nfl_position can differ. Eligibility is
based on route count, not the measured separation value or conventional test results.
No pass-result filter is added; observed valid separation occurs only on C/I/IN
in this run. Combine frame/timestamp checks are diagnostic, not inclusion filters.
All current Combine recordings pass these finite-value and 10 Hz checks; this
does not validate route phase boundaries. Elijah Higgins is a Combine WR but
roster TE; he remains in the cohort and has six qualifying WR/slot OUT routes,
so he does not meet either sample threshold.
Both thresholds retain all qualifying routes for eligible players, not just the
first 10 or 20. Thresholds describe the sample, not established reliability.

Reproduce: `.venv/bin/python exploratory_scripts/wr_out_coverage.py`. All CSV
exports are under `data/wr_out_*`, with Combine recordings in
`data/wr_speed_out_attempts.csv`. The qualifying-route export carries sample flags.
