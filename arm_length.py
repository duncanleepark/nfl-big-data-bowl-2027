"""Analyze arm length separately for EDGE and DT prospects.

The local combine file covers the 2023-2025 classes. This script joins those
measurements to draft and career data using ``nfl_id``, then estimates:

* draft position from arm length, height, weight, and draft year; and
* early career outcomes from arm length, draft position, height, and weight.

Run:
    python arm_length.py

Outputs:
    data/arm_length_analysis.csv
    data/arm_length_draft_coefficients.csv
    data/arm_length_success_coefficients.csv
    figures/arm_length_analysis.png
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parent
NFL_DATA = ROOT / "nfl-big-data-bowl-2027"
DATA_DIR = ROOT / "data"
FIG_DIR = ROOT / "figures"
POSITIONS = {"DE": "EDGE", "EDGE": "EDGE", "DT": "DT", "NT": "DT"}
SUCCESS_OUTCOMES = {
    "career_defensive_snaps": "log1p_defensive_snaps",
    "career_games_active": "log1p_games_active",
    "career_games_started": "log1p_games_started",
}


def load_analysis_table() -> pd.DataFrame:
    """Join combine, player, and career data and retain EDGE/DT players."""
    combine = pd.read_csv(NFL_DATA / "combine_results.csv")
    players = pd.read_csv(NFL_DATA / "players.csv")
    successes = pd.read_csv(NFL_DATA / "player_career_successes.csv")

    required = {
        "nfl_id",
        "draft_year",
        "arm_length",
        "combine_height",
        "combine_weight",
    }
    missing = required - set(combine.columns)
    if missing:
        raise ValueError(f"combine_results.csv is missing columns: {sorted(missing)}")

    player_columns = [
        "nfl_id",
        "nfl_position",
        "draft_overall_pick",
        "draft_round",
    ]
    df = combine.merge(players[player_columns], on="nfl_id", how="left", validate="one_to_one")
    df = df.merge(successes, on="nfl_id", how="left", validate="one_to_one")
    df["pos_group"] = df["nfl_position"].map(POSITIONS)
    df = df[df["pos_group"].notna()].copy()

    numeric_columns = [
        "arm_length",
        "combine_height",
        "combine_weight",
        "draft_overall_pick",
        "career_defensive_snaps",
        "career_games_active",
        "career_games_started",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["log_draft_pick"] = np.log(df["draft_overall_pick"])
    for outcome, transformed in SUCCESS_OUTCOMES.items():
        df[transformed] = np.log1p(df[outcome])
    return df


def fit_model(
    frame: pd.DataFrame, response: str, predictors: list[str]
) -> tuple[pd.DataFrame, int]:
    """Fit one robust OLS model and return coefficient rows and sample size."""
    model_frame = frame[[response, *predictors]].dropna()
    if len(model_frame) <= len(predictors):
        raise ValueError(
            f"Not enough complete rows to fit {response}: "
            f"{len(model_frame)} rows for {len(predictors)} predictors."
        )
    x = sm.add_constant(model_frame[predictors], has_constant="add")
    result = sm.OLS(model_frame[response], x).fit(cov_type="HC3")
    intervals = result.conf_int()
    rows = [
        {
            "term": term,
            "coefficient": result.params[term],
            "std_error": result.bse[term],
            "p_value": result.pvalues[term],
            "ci_low": intervals.loc[term, 0],
            "ci_high": intervals.loc[term, 1],
            "n_players": int(result.nobs),
            "r_squared": result.rsquared,
        }
        for term in predictors
    ]
    return pd.DataFrame(rows), int(result.nobs)


def run_models(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit separate draft and success models for EDGE and DT."""
    draft_rows: list[pd.DataFrame] = []
    success_rows: list[pd.DataFrame] = []
    draft_predictors = ["arm_length", "combine_height", "combine_weight", "draft_year"]
    success_predictors = [
        "arm_length",
        "log_draft_pick",
        "combine_height",
        "combine_weight",
    ]

    for position in ("EDGE", "DT"):
        group = df[df["pos_group"] == position]
        coefficients, n_players = fit_model(group, "log_draft_pick", draft_predictors)
        coefficients.insert(0, "pos_group", position)
        coefficients.insert(1, "analysis", "draft_position")
        draft_rows.append(coefficients)

        for outcome, transformed in SUCCESS_OUTCOMES.items():
            coefficients, n_players = fit_model(group, transformed, success_predictors)
            coefficients.insert(0, "pos_group", position)
            coefficients.insert(1, "outcome", outcome)
            success_rows.append(coefficients)
            print(f"{position} {outcome}: {n_players} complete players")

    return pd.concat(draft_rows, ignore_index=True), pd.concat(success_rows, ignore_index=True)


def plot_results(df: pd.DataFrame) -> None:
    """Plot the two primary relationships, separated by position."""
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), sharex="col")
    colors = {"EDGE": "#377eb8", "DT": "#e66101"}
    for position in ("EDGE", "DT"):
        group = df[df["pos_group"] == position]
        axes[0, 0].scatter(
            group["arm_length"], group["log_draft_pick"], label=position, alpha=0.75, color=colors[position]
        )
        axes[0, 1].scatter(
            group["arm_length"], group["career_defensive_snaps"], label=position, alpha=0.75, color=colors[position]
        )
        axes[1, 0].scatter(
            group["arm_length"], group["career_games_active"], label=position, alpha=0.75, color=colors[position]
        )
        axes[1, 1].scatter(
            group["arm_length"], group["career_games_started"], label=position, alpha=0.75, color=colors[position]
        )

    axes[0, 0].set_ylabel("log(overall draft pick)")
    axes[0, 1].set_ylabel("Career defensive snaps")
    axes[1, 0].set_ylabel("Career games active")
    axes[1, 1].set_ylabel("Career games started")
    for ax in axes.flat:
        ax.set_xlabel("Arm length (inches)")
        ax.grid(alpha=0.2)
    axes[0, 0].set_title("Draft position")
    axes[0, 1].set_title("Early success")
    axes[0, 0].legend(title="Position")
    fig.suptitle("Arm length: EDGE vs. DT (2023-2025 combine classes)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "arm_length_analysis.png", dpi=150)
    plt.close(fig)


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    FIG_DIR.mkdir(exist_ok=True)
    df = load_analysis_table()
    if df["arm_length"].notna().sum() == 0:
        raise ValueError("No arm-length measurements are available after joining the data.")

    draft_coefficients, success_coefficients = run_models(df)
    output_columns = [
        "nfl_id",
        "draft_year",
        "nfl_position",
        "pos_group",
        "arm_length",
        "combine_height",
        "combine_weight",
        "draft_overall_pick",
        *SUCCESS_OUTCOMES,
    ]
    df[output_columns].to_csv(DATA_DIR / "arm_length_analysis.csv", index=False)
    draft_coefficients.to_csv(DATA_DIR / "arm_length_draft_coefficients.csv", index=False)
    success_coefficients.to_csv(DATA_DIR / "arm_length_success_coefficients.csv", index=False)
    plot_results(df.dropna(subset=["arm_length"]))

    print(f"Analyzed {len(df):,} EDGE/DT players.")
    print(df.groupby("pos_group")["arm_length"].agg(["count", "mean", "std"]).round(2))
    print(f"Saved outputs to {DATA_DIR} and {FIG_DIR / 'arm_length_analysis.png'}")


if __name__ == "__main__":
    main()