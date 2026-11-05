"""
Model A: estimate which physical traits are associated with draft position.

The response is log draft pick (lower is better). Models are fit separately
for EDGE and DT so coefficients compare players within a position group.
Missing combine measurements are retained: missing trait z-scores are imputed
to zero (the position mean), and a missingness indicator is included for each
trait.

Run:
    python model_a.py

Outputs:
    data/model_a_coefficients.csv
    data/model_a_predictions.csv
    figures/model_a_coefficients.png
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parent
TABLE_PATH = ROOT / "data" / "edge_dt_table.csv"
DATA_DIR = ROOT / "data"
FIG_DIR = ROOT / "figures"

POSITION_GROUPS = ["EDGE", "DT"]
TRAITS = [
    "ht_in",
    "wt",
    "forty",
    "speed_score",
    "bench",
    "vertical",
    "broad_jump",
    "cone",
    "shuttle",
    "arm_length",
    "hand_size",
]


def build_design_matrix(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Create trait and missingness predictors without discarding rows."""
    predictors: dict[str, pd.Series] = {}
    trait_columns: list[str] = []

    for trait in TRAITS:
        z_column = f"z_{trait}"
        if z_column not in frame:
            continue

        missing_column = f"missing_{trait}"
        predictors[trait] = frame[z_column].fillna(0.0)
        predictors[missing_column] = frame[z_column].isna().astype(int)
        trait_columns.append(trait)

    return pd.DataFrame(predictors, index=frame.index), trait_columns


def fit_models(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit one OLS model per position group and return coefficients/predictions."""
    coefficient_rows: list[dict[str, object]] = []
    prediction_frames: list[pd.DataFrame] = []

    for position in POSITION_GROUPS:
        group = df[df["pos_group"] == position].copy()
        design, trait_columns = build_design_matrix(group)
        x = sm.add_constant(design, has_constant="add")
        y = np.log(group["pick"].astype(float))

        # HC3 is more conservative than classical standard errors for the
        # heteroskedasticity expected across draft rounds.
        result = sm.OLS(y, x).fit(cov_type="HC3")
        for term in trait_columns:
            coefficient_rows.append(
                {
                    "pos_group": position,
                    "term": term,
                    "coefficient": result.params[term],
                    "std_error": result.bse[term],
                    "p_value": result.pvalues[term],
                    "ci_low": result.conf_int().loc[term, 0],
                    "ci_high": result.conf_int().loc[term, 1],
                    "n_players": int(result.nobs),
                    "r_squared": result.rsquared,
                }
            )

        prediction_frames.append(
            pd.DataFrame(
                {
                    "pfr_player_name": group["pfr_player_name"].to_numpy(),
                    "season": group["season"].to_numpy(),
                    "pos_group": position,
                    "pick": group["pick"].to_numpy(),
                    "log_pick": y.to_numpy(),
                    "predicted_log_pick": result.predict(x),
                    "residual": result.resid,
                }
            )
        )

    return pd.DataFrame(coefficient_rows), pd.concat(prediction_frames, ignore_index=True)


def plot_coefficients(coefficients: pd.DataFrame) -> None:
    """Plot trait coefficients with 95% confidence intervals."""
    traits = list(dict.fromkeys(coefficients["term"]))
    y = np.arange(len(traits))
    colors = {"EDGE": "#377eb8", "DT": "#e66101"}

    fig, ax = plt.subplots(figsize=(9, 6))
    offsets = {"EDGE": -0.13, "DT": 0.13}
    for position in POSITION_GROUPS:
        subset = coefficients[coefficients["pos_group"] == position].set_index("term")
        subset = subset.reindex(traits)
        y_position = y + offsets[position]
        ax.errorbar(
            subset["coefficient"],
            y_position,
            xerr=[
                subset["coefficient"] - subset["ci_low"],
                subset["ci_high"] - subset["coefficient"],
            ],
            fmt="o",
            capsize=3,
            color=colors[position],
            label=position,
        )

    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_yticks(y, traits)
    ax.set_xlabel("Coefficient in log(draft pick)")
    ax.set_title("Model A: physical traits associated with draft position")
    ax.legend(title="Position", loc="upper left", bbox_to_anchor=(1.02, 1))
    ax.text(
        0.01,
        0.01,
        "Negative coefficients indicate earlier draft position.\n"
        "Bars show 95% HC3 confidence intervals.",
        transform=ax.transAxes,
        va="bottom",
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0, 0.84, 1))
    fig.savefig(FIG_DIR / "model_a_coefficients.png", dpi=150)
    plt.close(fig)


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    FIG_DIR.mkdir(exist_ok=True)

    df = pd.read_csv(TABLE_PATH)
    required = {"pick", "pos_group", "pfr_player_name", "season"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{TABLE_PATH} is missing required columns: {sorted(missing)}")

    df = df[df["pos_group"].isin(POSITION_GROUPS) & df["pick"].notna()].copy()
    coefficients, predictions = fit_models(df)
    coefficients.to_csv(DATA_DIR / "model_a_coefficients.csv", index=False)
    predictions.to_csv(DATA_DIR / "model_a_predictions.csv", index=False)
    plot_coefficients(coefficients)

    print(f"Fitted {len(POSITION_GROUPS)} position-specific models on {len(df):,} players.")
    print(f"Saved coefficients to {DATA_DIR / 'model_a_coefficients.csv'}")
    print(f"Saved predictions to {DATA_DIR / 'model_a_predictions.csv'}")
    print(f"Saved plot to {FIG_DIR / 'model_a_coefficients.png'}")


if __name__ == "__main__":
    main()
