"""
NFL Big Data Bowl 2027 -- starter script: EDGE / DT draft + combine table.

What it does
  1. Pulls combine and draft-pick data from nflreadpy (nflverse).
  2. Joins them (draft picks are the base table, so drafted players with no
     combine data are KEPT -- missing combine data is informative).
  3. Keeps EDGE and interior DL, converts height to inches, builds speed score.
  4. Z-scores each trait within position group.
  5. Saves a player-level table, a by-round trait summary, a missingness
     summary, and a heatmap of mean trait z-score by draft round.

Run:
    pip install -r requirements.txt
    python build_edge_dt_table.py

Outputs (created next to this script):
    data/edge_dt_table.csv
    data/trait_by_round.csv
    data/missingness_by_round.csv
    figures/trait_by_round_heatmap.png
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nflreadpy as nfl
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Config -- adjust these first
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
FIG_DIR = ROOT / "figures"

MIN_SEASON = 2000
# Drafts after this year haven't had time to produce career outcomes yet.
# Only used to flag rows (`outcome_ready`); descriptive trait plots use all years.
MAX_OUTCOME_SEASON = 2021

# Draft-pick position labels -> position group. Print the value counts below
# and edit this if labels in your pull differ. OLB is deliberately left out:
# it mixes true edge rushers with off-ball linebackers.
POS_GROUPS = {
    "DE": "EDGE",
    "EDGE": "EDGE",
    "DT": "DT",
    "NT": "DT",
    "DL": "DT",
}

# Traits that should be present in the combine table. Arm length and hand
# size are NOT in the standard nflverse combine table, so they are picked up
# automatically only if a column with that name exists (e.g. after you merge
# in another source).
BASE_TRAITS = ["ht_in", "wt", "forty", "speed_score", "bench", "vertical", "broad_jump", "cone", "shuttle"]
OPTIONAL_TRAITS = ["arm_length", "hand_size"]

# For these, a LOWER raw value is better (timed drills). We flip the sign of the
# z-score so that positive always means "better / more of the trait".
LOWER_IS_BETTER = {"forty", "cone", "shuttle"}


def round_bucket(rnd: int) -> str:
    if rnd == 1:
        return "R1"
    if rnd == 2:
        return "R2"
    if rnd == 3:
        return "R3"
    if rnd in (4, 5):
        return "R4-5"
    return "R6-7"


BUCKET_ORDER = ["R1", "R2", "R3", "R4-5", "R6-7"]


def height_to_inches(ht) -> float:
    """Combine heights look like '6-4' (feet-inches). Returns inches or NaN."""
    if ht is None or (isinstance(ht, float) and np.isnan(ht)):
        return np.nan
    s = str(ht).strip()
    if "-" in s:
        try:
            ft, inch = s.split("-")
            return int(ft) * 12 + float(inch)
        except ValueError:
            return np.nan
    try:
        v = float(s)
        return v if v > 20 else np.nan  # already inches
    except ValueError:
        return np.nan


def load_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    combine = nfl.load_combine().to_pandas()
    draft = nfl.load_draft_picks().to_pandas()
    print(f"combine rows: {len(combine):,} | draft pick rows: {len(draft):,}")
    print("combine columns:", list(combine.columns))
    print("draft columns:  ", list(draft.columns))
    return combine, draft


def build_table(combine: pd.DataFrame, draft: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    # ---- draft side -------------------------------------------------------
    draft = draft[draft["season"] >= MIN_SEASON].copy()
    print("\nDraft-pick position labels (check POS_GROUPS covers what you want):")
    print(draft["position"].value_counts().to_string())

    draft["pos_group"] = draft["position"].map(POS_GROUPS)
    draft = draft[draft["pos_group"].notna()].copy()
    draft["round_bucket"] = draft["round"].apply(round_bucket)
    draft["outcome_ready"] = draft["season"] <= MAX_OUTCOME_SEASON

    # ---- combine side -----------------------------------------------------
    combine = combine.copy()
    combine["ht_in"] = combine["ht"].apply(height_to_inches)
    combine["speed_score"] = (combine["wt"] * 200) / (combine["forty"] ** 4)

    keep = ["pfr_id", "ht_in", "wt", "forty", "speed_score", "bench", "vertical", "broad_jump", "cone", "shuttle"]
    keep += [c for c in OPTIONAL_TRAITS if c in combine.columns]
    combine = combine[keep].drop_duplicates(subset="pfr_id", keep="first")

    # ---- join (draft picks are the base: keep players w/o combine data) ---
    df = draft.merge(combine, how="left", left_on="pfr_player_id", right_on="pfr_id")
    traits = [t for t in BASE_TRAITS + OPTIONAL_TRAITS if t in df.columns]
    df["has_combine"] = df[traits].notna().any(axis=1)

    print("\nCombine match rate by position group (share of drafted players with any combine data):")
    print(df.groupby("pos_group")["has_combine"].mean().round(3).to_string())

    # ---- z-scores within position group ------------------------------------
    for t in traits:
        grp = df.groupby("pos_group")[t]
        z = (df[t] - grp.transform("mean")) / grp.transform("std")
        if t in LOWER_IS_BETTER:
            z = -z
        df[f"z_{t}"] = z

    return df, traits


def summarize(df: pd.DataFrame, traits: list[str]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    FIG_DIR.mkdir(exist_ok=True)

    z_cols = [f"z_{t}" for t in traits]

    # mean z-score by position group x round bucket
    by_round = (
        df.groupby(["pos_group", "round_bucket"])[z_cols + ["pick"]]
        .agg(["mean", "count"])
    )
    by_round.to_csv(DATA_DIR / "trait_by_round.csv")

    # how much combine data exists per round -- missingness itself is a signal
    miss = (
        df.groupby(["pos_group", "round_bucket"])[traits]
        .apply(lambda g: g.notna().mean())
        .round(3)
    )
    miss["n_players"] = df.groupby(["pos_group", "round_bucket"]).size()
    miss.to_csv(DATA_DIR / "missingness_by_round.csv")
    print("\nShare of players with each measure, by round bucket:")
    print(miss.to_string())

    # heatmap: traits (rows) x round bucket (cols), one panel per position group
    groups = sorted(df["pos_group"].unique())
    fig, axes = plt.subplots(1, len(groups), figsize=(6.5 * len(groups), 5), squeeze=False)
    for ax, g in zip(axes[0], groups):
        sub = df[df["pos_group"] == g]
        mat = sub.groupby("round_bucket")[z_cols].mean().reindex(BUCKET_ORDER).T
        im = ax.imshow(mat.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
        ax.set_xticks(range(len(BUCKET_ORDER)), BUCKET_ORDER)
        ax.set_yticks(range(len(traits)), traits)
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                v = mat.values[i, j]
                if not np.isnan(v):
                    ax.text(j, i, f"{v:+.2f}", ha="center", va="center", fontsize=8)
        ax.set_title(f"{g}: mean trait z-score by round\n(+ = better/more; z within position group)")
        fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "trait_by_round_heatmap.png", dpi=150)
    plt.close(fig)


def main() -> None:
    combine, draft = load_tables()
    df, traits = build_table(combine, draft)

    DATA_DIR.mkdir(exist_ok=True)
    out_cols = [
        "season", "round", "pick", "round_bucket", "pfr_player_name", "pos_group", "position",
        "college", "has_combine", "outcome_ready",
    ]
    out_cols += [c for c in ["w_av", "car_av", "dr_av", "games", "seasons_started", "probowls", "allpro"] if c in df.columns]
    out_cols += traits + [f"z_{t}" for t in traits]
    df[out_cols].sort_values(["season", "pick"]).to_csv(DATA_DIR / "edge_dt_table.csv", index=False)
    print(f"\nSaved {len(df):,} rows to {DATA_DIR / 'edge_dt_table.csv'}")

    summarize(df, traits)
    print(f"Saved summaries to {DATA_DIR} and heatmap to {FIG_DIR}")


if __name__ == "__main__":
    main()
