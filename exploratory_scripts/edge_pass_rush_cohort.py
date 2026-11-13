"""Shared PASS_RUSH_DRILL cohort: DE/OLB minus primarily interior NFL alignments.

Role is determined from supplied 2023–2025 regular-season, non-nullified plays
with a known defensive alignment, across all available seasons per player.
This uses alignment context, never get-off values or performance outcomes.
Players without qualifying observations remain provisionally included and flagged.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'nfl-big-data-bowl-2027'
DEFENSIVE_ALIGNMENTS = {'EDGE', 'INTERIOR_LINE', 'MLB', 'OLB', 'SLOT_CB', 'CB', 'FS', 'SS', 'S', 'DB'}


def select_edge_cohort(roster, tracks):
    """Return retained roster and write an auditable role table for drill candidates."""
    drill_ids = tracks.loc[
        tracks.drill_name.eq('PASS_RUSH_DRILL') & tracks.entity_type.eq('PLAYER'), 'nfl_id']
    candidates = roster.loc[roster.nfl_position.isin(['DE', 'OLB']) &
                            roster.nfl_id.isin(drill_ids)].copy()
    plays = pd.read_csv(SOURCE / 'player_play.csv', usecols=[
        'game_id', 'play_id', 'nfl_id', 'lined_up_position', 'play_nullified_by_penalty'],
        keep_default_na=False)
    plays = plays.loc[plays.nfl_id.isin(candidates.nfl_id)].copy()
    if plays.duplicated(['game_id', 'play_id', 'nfl_id']).any():
        raise ValueError('Duplicate player-play alignment rows')
    games = pd.read_csv(SOURCE / 'games.csv', usecols=['game_id', 'season', 'season_type'])
    plays = plays.merge(games, on='game_id', how='left', validate='many_to_one')
    if plays.season_type.isna().any():
        raise ValueError('Player-play rows missing game metadata')
    valid = plays.loc[plays.season.between(2023, 2025) & plays.season_type.eq('REG') &
                      plays.play_nullified_by_penalty.eq('N') &
                      ~plays.lined_up_position.isin(['', 'NA'])].copy()
    unknown = set(valid.lined_up_position) - DEFENSIVE_ALIGNMENTS
    if unknown:
        raise ValueError(f'Review unexpected alignment labels: {sorted(unknown)}')
    valid['interior'] = valid.lined_up_position.eq('INTERIOR_LINE')
    valid['edge'] = valid.lined_up_position.eq('EDGE')
    counts = valid.groupby('nfl_id').agg(
        n_known_defensive_snaps=('play_id', 'size'), n_interior_snaps=('interior', 'sum'),
        n_edge_snaps=('edge', 'sum'), first_observed_season=('season', 'min'),
        last_observed_season=('season', 'max'))
    review = candidates.merge(counts, on='nfl_id', how='left', validate='one_to_one')
    for column in ['n_known_defensive_snaps', 'n_interior_snaps', 'n_edge_snaps']:
        review[column] = review[column].fillna(0).astype(int)
    review['interior_share'] = review.n_interior_snaps / review.n_known_defensive_snaps.replace(0, float('nan'))
    review['exclude_primary_interior'] = review.interior_share.gt(.5)
    review['role_evidence'] = 'observed_non_interior_majority_or_tie'
    review.loc[review.exclude_primary_interior, 'role_evidence'] = 'observed_interior_majority'
    review.loc[review.n_known_defensive_snaps.eq(0), 'role_evidence'] = 'no_qualifying_alignments_retained_provisionally'
    review = review.sort_values(['draft_year', 'display_name'])
    output = ROOT / 'data'
    output.mkdir(exist_ok=True)
    review.to_csv(output / 'edge_pass_rush_cohort.csv', index=False)
    review.loc[review.exclude_primary_interior].to_csv(
        output / 'edge_pass_rush_interior_exclusions.csv', index=False)
    return candidates.loc[~candidates.nfl_id.isin(
        review.loc[review.exclude_primary_interior, 'nfl_id'])].copy()
