"""
Model B: estimate outcomes from physical traits after controlling for draft slot.

Models are fit separately for EDGE and DT and use players with outcome-ready
career data. Outcomes are modeled as log1p(w_av), log1p(games), and
log1p(seasons_started). Missing combine measurements are retained using the
same position-mean imputation and missingness indicators as Model A.

Run:
    python model_b.py

Outputs:
    data/model_b_coefficients.csv
    data/model_b_predictions.csv
    figures/model_b_coefficients.png
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

from model_a import POSITION_GROUPS, TABLE_PATH, TRAITS, build_design_matrix

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
FIG_DIR = ROOT / "figures"
OUTCOMES = {
    "w_av": "log1p_w_av",
    "games": "log1p_games",
    "seasons_started": "log1p_seasons_started",
}


def fit_models(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit position-specific outcome models with log draft pick as a control."""
    coefficient_rows: list[dict[str, object]] = []
    prediction_frames: list[pd.DataFrame] = []

    for outcome, transformed_outcome in OUTCOMES.items():
        outcome_df = df[df[outcome].notna()].copy()
        for position in POSITION_GROUPS:
            group = outcome_df[outcome_df["pos_group"] == position].copy()
            design, trait_columns = build_design_matrix(group)
            design["log_pick"] = np.log(group["pick"].astype(float))
            x = sm.add_constant(design, has_constant="add")
            y = np.log1p(group[outcome].astype(float))

            result = sm.OLS(y, x).fit(cov_type="HC3")
            terms = trait_columns + ["log_pick"]
            intervals = result.conf_int()
            for term in terms:
                coefficient_rows.append(
                    {
                        "outcome": outcome,
                        "pos_group": position,
                        "term": term,
                        "coefficient": result.params[term],
                        "std_error": result.bse[term],
                        "p_value": result.pvalues[term],
                        "ci_low": intervals.loc[term, 0],
                        "ci_high": intervals.loc[term, 1],
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
                        "outcome": outcome,
                        "pick": group["pick"].to_numpy(),
                        "actual": group[outcome].to_numpy(),
                        "predicted_log1p": result.predict(x),
                        "residual": result.resid,
                    }
                )
            )

    return pd.DataFrame(coefficient_rows), pd.concat(prediction_frames, ignore_index=True)


def plot_coefficients(coefficients: pd.DataFrame) -> None:
    """Plot physical-trait coefficients; draft-slot controls are in the CSV."""
    traits = [term for term in TRAITS if term in coefficients["term"].unique()]
    colors = {"EDGE": "#377eb8", "DT": "#e66101"}
    fig, axes = plt.subplots(1, len(OUTCOMES), figsize=(15, 6), sharey=True)

    for ax, outcome in zip(axes, OUTCOMES):
        subset_all = coefficients[
            (coefficients["outcome"] == outcome) & coefficients["term"].isin(traits)
        ]
        y = np.arange(len(traits))
        offsets = {"EDGE": -0.13, "DT": 0.13}
        for position in POSITION_GROUPS:
            subset = subset_all[subset_all["pos_group"] == position].set_index("term")
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
        ax.set_title(outcome)
        ax.set_xlabel("Coefficient in log1p(outcome)")
        ax.set_yticks(y, traits)

    axes[0].invert_yaxis()
    axes[-1].legend(title="Position", loc="upper left", bbox_to_anchor=(1.02, 1))
    fig.suptitle("Model B: physical traits associated with outcomes, controlling for draft position")
    fig.text(0.01, 0.01, "Bars show 95% HC3 confidence intervals.", fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 0.9, 0.95))
    fig.savefig(FIG_DIR / "model_b_coefficients.png", dpi=150)
    plt.close(fig)


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    FIG_DIR.mkdir(exist_ok=True)

    df = pd.read_csv(TABLE_PATH)
    required = {
        "pick",
        "pos_group",
        "pfr_player_name",
        "season",
        "outcome_ready",
        *OUTCOMES,
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{TABLE_PATH} is missing required columns: {sorted(missing)}")

    df = df[
        df["outcome_ready"].astype(bool)
        & df["pos_group"].isin(POSITION_GROUPS)
        & df["pick"].notna()
    ].copy()
    coefficients, predictions = fit_models(df)
    coefficients.to_csv(DATA_DIR / "model_b_coefficients.csv", index=False)
    predictions.to_csv(DATA_DIR / "model_b_predictions.csv", index=False)
    plot_coefficients(coefficients)

    print(f"Fitted {len(OUTCOMES)} outcomes for {len(POSITION_GROUPS)} positions.")
    print(f"Saved coefficients to {DATA_DIR / 'model_b_coefficients.csv'}")
    print(f"Saved predictions to {DATA_DIR / 'model_b_predictions.csv'}")
    print(f"Saved plot to {FIG_DIR / 'model_b_coefficients.png'}")


if __name__ == "__main__":
    main()