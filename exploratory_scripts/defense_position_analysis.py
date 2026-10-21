"""Explore rookie defensive position coverage and build a transparent impact score.

Run from the repository root:
    python exploratory_scripts/defense_position_analysis.py

Add --output PATH to export one row per defensive rookie, including seasonal
event totals and the cumulative score through the seasons present in the data.
Add --include-game-tracking to scan the much larger game-tracking files.

Research questions to investigate:
1. Which defensive positions produce the most recorded playmaking per snap?
2. How does rookie-year defensive opportunity vary by position and draft class?
3. For the 2023 class, how do playmaking and defensive role change in years two
   and three compared with the rookie season?
4. Do combine athleticism measures associate with subsequent defensive impact
   within a position, after accounting for draft capital and snap opportunity?
5. Are career starts, games active, or awards associated with on-field impact,
   or mostly with the amount of opportunity a player receives?

The score is intentionally narrow. It weights recorded sacks, tackles, assists,
TFLs, forced/recovered fumbles, pressures, and QB hurries per 100 career
defensive snaps. The data has no explicit interception or pass-breakup fields,
and no season-level defensive snap denominator, so compare the score only
within the same roster position and draft class. It is not a complete grade.
Percentile scores require at least 100 defensive snaps by default; lower-
exposure players still receive raw rates but are excluded from percentiles.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterator


SEASONS = (2023, 2024, 2025)
DEFENSIVE_GROUPS = {
    "DL": ("DE", "DT", "NT"),
    "LB": ("ILB", "MLB", "OLB"),
    "DB": ("CB", "DB", "FS", "SS"),
}
DEFENSIVE_POSITIONS = {
    position for positions in DEFENSIVE_GROUPS.values() for position in positions
}
EVENT_WEIGHTS = {
    "sacks": 4.0,
    "tackles": 1.0,
    "assists": 0.5,
    "tfls": 2.0,
    "forced_fumbles": 3.0,
    "recovered_fumbles": 2.0,
    "pressures": 1.0,
    "qb_hurries": 0.75,
}
REQUIRED_FILES = (
    "players.csv",
    "games.csv",
    "player_play.csv",
    "player_career_successes.csv",
    "combine_results.csv",
    "combine_tracking.csv",
)
COMBINE_MEASURES = (
    "forty",
    "vertical",
    "broad_jump",
    "bench_reps",
    "ngs_athleticism_score",
    "ngs_college_production_score",
    "ngs_final_score",
)
EVENT_FIELDS = {
    "sack": "sack",
    "tackle": "tackle",
    "assist": "assist",
    "tfl": "tackle_for_loss",
    "forced_fumble": "caused_forced_fumble",
    "recovered_fumble": "recovered_fumble",
    "pressure": "time_to_pressure",
    "qb_hurry": "time_to_qb_hurry",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def iter_csv(path: Path) -> Iterator[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as source:
        yield from csv.DictReader(source)


def number(value: str | None) -> float:
    if value is None or value.strip().upper() in {"", "NA", "N/A", "NULL"}:
        return 0.0
    try:
        return float(value)
    except ValueError as error:
        raise ValueError(f"Expected a numeric value, got {value!r}") from error


def is_true(value: str | None) -> bool:
    return value is not None and value.strip().upper() in {"TRUE", "1", "YES"}


def is_present(value: str | None) -> bool:
    return value is not None and value.strip().upper() not in {
        "",
        "NA",
        "N/A",
        "NULL",
    }


def group_for(position: str) -> str:
    return next(
        group for group, positions in DEFENSIVE_GROUPS.items() if position in positions
    )


def empty_events() -> Counter[str]:
    return Counter({event: 0 for event in EVENT_WEIGHTS})


def row_events(row: dict[str, str]) -> Counter[str]:
    events = empty_events()
    events["sacks"] = number(row.get("sack"))
    events["tackles"] = number(row.get("tackle"))
    events["assists"] = number(row.get("assist"))
    events["forced_fumbles"] = number(row.get("caused_forced_fumble"))
    events["recovered_fumbles"] = int(is_true(row.get("recovered_fumble")))
    events["tfls"] = int(is_true(row.get("tackle_for_loss")))
    events["pressures"] = int(is_present(row.get("time_to_pressure")))
    events["qb_hurries"] = int(is_present(row.get("time_to_qb_hurry")))
    return events


def add_events(destination: Counter[str], source: Counter[str]) -> None:
    for event in EVENT_WEIGHTS:
        destination[event] += source[event]


def weighted_points(events: Counter[str]) -> float:
    return sum(events[event] * weight for event, weight in EVENT_WEIGHTS.items())


def format_table(title: str, columns: list[str], rows: list[dict[str, Any]]) -> None:
    print(f"\n{title}")
    writer = csv.DictWriter(sys.stdout, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in columns})


def analyze(
    data_dir: Path,
    output_path: Path | None,
    min_snaps: int,
    include_game_tracking: bool,
) -> None:
    missing = [name for name in REQUIRED_FILES if not (data_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(
            f"Missing required data file(s) in {data_dir}: {', '.join(missing)}"
        )

    players = read_csv(data_dir / "players.csv")
    games = read_csv(data_dir / "games.csv")
    player_plays = read_csv(data_dir / "player_play.csv")
    career_rows = read_csv(data_dir / "player_career_successes.csv")
    combine_results = {
        row["nfl_id"]: row for row in read_csv(data_dir / "combine_results.csv")
    }

    player_by_id = {row["nfl_id"]: row for row in players}
    career_by_id = {row["nfl_id"]: row for row in career_rows}
    season_by_game = {
        row["game_id"]: int(row["season"])
        for row in games
        if int(row["season"]) in SEASONS
    }
    rookies = {
        player_id: row
        for player_id, row in player_by_id.items()
        if row["draft_year"].isdigit()
        and int(row["draft_year"]) in SEASONS
    }
    defensive_rookies = {
        player_id: row
        for player_id, row in rookies.items()
        if row["nfl_position"] in DEFENSIVE_POSITIONS
    }

    seasonal_events: dict[tuple[str, int], Counter[str]] = defaultdict(empty_events)
    cumulative_events: dict[str, Counter[str]] = defaultdict(empty_events)
    seasonal_play_rows: Counter[tuple[str, int]] = Counter()
    career_play_rows: Counter[str] = Counter()
    event_observations: Counter[tuple[str, str]] = Counter()
    combine_tracking_rows: Counter[str] = Counter()
    game_tracking_rows: Counter[tuple[str, int]] = Counter()
    unmatched_games = 0
    non_defensive_play_ids = 0

    for row in player_plays:
        player_id = row["nfl_id"]
        season = season_by_game.get(row["game_id"])
        if season is None:
            unmatched_games += 1
            continue
        player = player_by_id.get(player_id)
        if player is None or player["nfl_position"] not in DEFENSIVE_POSITIONS:
            non_defensive_play_ids += 1
            continue
        if player_id not in defensive_rookies:
            continue

        events = row_events(row)
        add_events(seasonal_events[(player_id, season)], events)
        add_events(cumulative_events[player_id], events)
        seasonal_play_rows[(player_id, season)] += 1
        career_play_rows[player_id] += 1
        for field in (
            "sack",
            "tackle",
            "assist",
            "tackle_for_loss",
            "caused_forced_fumble",
            "recovered_fumble",
            "time_to_pressure",
            "time_to_qb_hurry",
        ):
            if is_present(row.get(field)):
                event_observations[(player_id, field)] += 1

    defensive_rookie_ids = set(defensive_rookies)
    for row in iter_csv(data_dir / "combine_tracking.csv"):
        player_id = row["nfl_id"]
        if player_id in defensive_rookie_ids:
            combine_tracking_rows[player_id] += 1

    if include_game_tracking:
        for season in SEASONS:
            tracking_path = data_dir / f"game_tracking_{season}.csv"
            if not tracking_path.is_file():
                raise FileNotFoundError(f"Missing game-tracking file: {tracking_path}")
            for row in iter_csv(tracking_path):
                player_id = row["nfl_id"]
                if player_id in defensive_rookie_ids:
                    game_tracking_rows[(player_id, season)] += 1

    position_rows = []
    for draft_year in SEASONS:
        for position in sorted(DEFENSIVE_POSITIONS):
            members = [
                (player_id, player)
                for player_id, player in defensive_rookies.items()
                if int(player["draft_year"]) == draft_year
                and player["nfl_position"] == position
            ]
            if not members:
                continue
            position_rows.append(
                {
                    "draft_year": draft_year,
                    "group": group_for(position),
                    "position": position,
                    "rookies": len(members),
                    "with_play_rows": sum(
                        career_play_rows[player_id] > 0 for player_id, _ in members
                    ),
                    "defensive_snaps": sum(
                        number(career_by_id.get(player_id, {}).get("career_defensive_snaps"))
                        for player_id, _ in members
                    ),
                    "player_play_rows": sum(
                        career_play_rows[player_id] for player_id, _ in members
                    ),
                    "combine_results": sum(
                        player_id in combine_results for player_id, _ in members
                    ),
                    "combine_athletic_score": sum(
                        is_present(
                            combine_results.get(player_id, {}).get(
                                "ngs_athleticism_score"
                            )
                        )
                        for player_id, _ in members
                    ),
                    "combine_tracking_rows": sum(
                        combine_tracking_rows[player_id]
                        for player_id, _ in members
                    ),
                    **{
                        f"event_{name}_rows": sum(
                            event_observations[(player_id, field)]
                            for player_id, _ in members
                        )
                        for name, field in EVENT_FIELDS.items()
                    },
                }
            )

    cohort_roster_sizes = Counter(
        (player["nfl_position"], int(player["draft_year"]))
        for player in defensive_rookies.values()
    )
    score_rows: list[dict[str, Any]] = []
    for player_id, player in defensive_rookies.items():
        career = career_by_id.get(player_id, {})
        snaps = number(career.get("career_defensive_snaps"))
        events = cumulative_events[player_id]
        points = weighted_points(events)
        rate = points * 100 / snaps if snaps > 0 else None
        score_status = (
            "no defensive snaps"
            if snaps == 0
            else "below minimum exposure"
            if snaps < min_snaps
            else "scored"
        )
        score_rows.append(
            {
                "nfl_id": player_id,
                "display_name": player["display_name"],
                "draft_year": int(player["draft_year"]),
                "position_group": group_for(player["nfl_position"]),
                "nfl_position": player["nfl_position"],
                "draft_round": player.get("draft_round", ""),
                "draft_overall_pick": player.get("draft_overall_pick", ""),
                "career_defensive_snaps": int(snaps),
                "career_games_active": career.get("career_games_active", ""),
                "career_games_started": career.get("career_games_started", ""),
                "player_play_rows_2023_2025": career_play_rows[player_id],
                "combine_results_available": player_id in combine_results,
                "combine_tracking_rows": combine_tracking_rows[player_id],
                **{
                    f"combine_{measure}": combine_results.get(player_id, {}).get(
                        measure, ""
                    )
                    for measure in COMBINE_MEASURES
                },
                **{f"total_{name}": events[name] for name in EVENT_WEIGHTS},
                "weighted_points": round(points, 3),
                "impact_points_per_100_snaps": (
                    round(rate, 3) if rate is not None else ""
                ),
                "position_draft_class_roster_n": cohort_roster_sizes[
                    (player["nfl_position"], int(player["draft_year"]))
                ],
                "position_draft_class_n": "",
                "position_draft_class_percentile": "",
                "score_status": score_status,
                **{
                    f"{name}_{season}": seasonal_events[(player_id, season)][name]
                    for season in SEASONS
                    for name in EVENT_WEIGHTS
                },
                **{
                    f"play_rows_{season}": seasonal_play_rows[(player_id, season)]
                    for season in SEASONS
                },
                **{
                    f"game_tracking_rows_{season}": game_tracking_rows[
                        (player_id, season)
                    ]
                    for season in SEASONS
                },
            }
        )

    # The percentile is a relative ranking of the weighted rate among players
    # with defensive snaps at the same listed position and draft class.
    score_cohorts: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in score_rows:
        if row["score_status"] == "scored":
            score_cohorts[(row["nfl_position"], row["draft_year"])].append(row)
    for cohort in score_cohorts.values():
        cohort.sort(key=lambda row: row["impact_points_per_100_snaps"])
        size = len(cohort)
        start = 0
        while start < size:
            end = start + 1
            while (
                end < size
                and cohort[end]["impact_points_per_100_snaps"]
                == cohort[start]["impact_points_per_100_snaps"]
            ):
                end += 1
            average_rank = (start + 1 + end) / 2
            percentile = 100 * average_rank / size
            for row in cohort[start:end]:
                row["position_draft_class_n"] = size
                row["position_draft_class_percentile"] = round(percentile, 1)
            start = end

    by_group = []
    for group, positions in DEFENSIVE_GROUPS.items():
        members = [
            (player_id, player)
            for player_id, player in defensive_rookies.items()
            if player["nfl_position"] in positions
        ]
        by_group.append(
            {
                "group": group,
                "rookies": len(members),
                "with_play_rows": sum(
                    career_play_rows[player_id] > 0 for player_id, _ in members
                ),
                "defensive_snaps": sum(
                    number(career_by_id.get(player_id, {}).get("career_defensive_snaps"))
                    for player_id, _ in members
                ),
                "player_play_rows": sum(
                    career_play_rows[player_id] for player_id, _ in members
                ),
                "combine_results": sum(
                    player_id in combine_results for player_id, _ in members
                ),
                "combine_athletic_score": sum(
                    is_present(
                        combine_results.get(player_id, {}).get(
                            "ngs_athleticism_score"
                        )
                    )
                    for player_id, _ in members
                ),
                "combine_tracking_rows": sum(
                    combine_tracking_rows[player_id] for player_id, _ in members
                ),
            }
        )

    format_table(
        f"Defensive rookie coverage by exact position and draft year "
        f"({len(defensive_rookies)} defensive rookies / {len(rookies)} total rookies)",
        [
            "draft_year",
            "group",
            "position",
            "rookies",
            "with_play_rows",
            "defensive_snaps",
            "player_play_rows",
            "combine_results",
            "combine_athletic_score",
            "combine_tracking_rows",
            *[f"event_{name}_rows" for name in EVENT_FIELDS],
        ],
        position_rows,
    )
    format_table(
        "Coverage by broad defensive group, all draft classes",
        [
            "group",
            "rookies",
            "with_play_rows",
            "defensive_snaps",
            "player_play_rows",
            "combine_results",
            "combine_athletic_score",
            "combine_tracking_rows",
        ],
        by_group,
    )

    top_scores = []
    for position, draft_year in sorted(score_cohorts):
        top_scores.extend(
            sorted(
                score_cohorts[(position, draft_year)],
                key=lambda row: -row["impact_points_per_100_snaps"],
            )[:5]
        )
    format_table(
        "Highest impact rates by position and draft class (top five per cohort)",
        [
            "draft_year",
            "nfl_position",
            "display_name",
            "career_defensive_snaps",
            "impact_points_per_100_snaps",
            "position_draft_class_percentile",
            "position_draft_class_n",
        ],
        top_scores,
    )

    print(
        "\nData checks: "
        f"{len(players)} roster players; {len(player_plays)} player-play rows; "
        f"{len(rookies)} rookies drafted 2023-2025; "
        f"{len(defensive_rookies)} defensive rookies. "
        f"{unmatched_games} play rows had no 2023-2025 game-season match. "
        f"{non_defensive_play_ids} rows belonged to non-defensive or unmatched roster IDs."
    )
    print(
        "Score caveats: cumulative 2023-2025 events divided by career defensive "
        f"snaps; percentiles are within exact position + draft class for players "
        f"with at least {min_snaps} snaps. No coverage interception/pass-breakup "
        "outcomes or season-level snap denominators."
    )
    if include_game_tracking:
        print(
            "Game-tracking row counts for defensive rookies are included in the "
            "player-level output; coverage summary includes combine tracking."
        )

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(score_rows[0])
        with output_path.open("w", newline="", encoding="utf-8") as destination:
            writer = csv.DictWriter(destination, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(score_rows)
        print(f"\nWrote player-level score file: {output_path}")


def main() -> None:
    repository_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=repository_root / "nfl-big-data-bowl-2027",
        help="Directory containing the source CSV files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the player-level defensive score CSV.",
    )
    parser.add_argument(
        "--min-snaps",
        type=int,
        default=100,
        help="Minimum career defensive snaps for score percentiles (default: 100).",
    )
    parser.add_argument(
        "--include-game-tracking",
        action="store_true",
        help="Scan the large 2023-2025 game-tracking files for defensive rookies.",
    )
    arguments = parser.parse_args()
    if arguments.min_snaps < 0:
        parser.error("--min-snaps must be non-negative")
    analyze(
        arguments.data_dir,
        arguments.output,
        arguments.min_snaps,
        arguments.include_game_tracking,
    )


if __name__ == "__main__":
    main()
