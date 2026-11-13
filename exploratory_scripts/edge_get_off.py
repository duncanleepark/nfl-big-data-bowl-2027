"""Explore Combine initial burst versus supplied rookie NFL player_get_off.

Run: .venv/bin/python exploratory_scripts/edge_get_off.py
The Combine onset is movement-based, not cue-based reaction time. Source units
and the exact dataset definition of player_get_off still need dictionary validation.
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from edge_pass_rush_audit import audit_attempt
from edge_pass_rush_cohort import select_edge_cohort

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'nfl-big-data-bowl-2027'
KEY = ['nfl_id', 'event_id', 'attempt']
FEATURES = ['speed_gain_0_5', 'speed_gain_0_3', 'speed_at_0_3', 'displacement_0_3']


def rank_correlation(frame, feature, adjusted=False):
    ranks = frame[[feature, 'median_nfl_get_off']].rank()
    if adjusted:
        ranks = ranks - ranks.groupby(frame.draft_year).transform('mean')
    if len(frame) < 3 or (ranks.std() == 0).any():
        return np.nan
    return ranks.corr().iloc[0, 1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--min-snaps', type=int, default=20,
                        help='Minimum qualifying rookie EDGE passing plays with observed get-off')
    parser.add_argument('--bootstrap', type=int, default=1000)
    args = parser.parse_args()
    if args.min_snaps < 1 or args.bootstrap < 100:
        parser.error('min-snaps must be positive and bootstrap must be at least 100')
    data = ROOT / 'data'
    data.mkdir(exist_ok=True)
    roster = pd.read_csv(SOURCE / 'players.csv')
    tracking = pd.read_csv(SOURCE / 'combine_tracking.csv')
    cohort = select_edge_cohort(roster, tracking)
    tracks = tracking.loc[tracking.nfl_id.isin(cohort.nfl_id) &
                          tracking.drill_name.eq('PASS_RUSH_DRILL') & tracking.entity_type.eq('PLAYER')]
    rows = []
    for key, group in tracks.groupby(KEY):
        g = group.sort_values('time').reset_index(drop=True)
        result = audit_attempt(g)
        result.update(dict(zip(KEY, key)))
        result['duration_s'] = (pd.to_datetime(g.time.iloc[-1]) - pd.to_datetime(g.time.iloc[0])).total_seconds()
        result['direction'] = 'negative_y' if g.y.iloc[-1] < g.y.iloc[0] else 'positive_y'
        # A review flag, not a claim that duration proves preparatory motion.
        result['long_recording_review'] = result['duration_s'] > 6
        result['included'] = result['status'] == 'usable' and not result['long_recording_review']
        result['phase_validation_status'] = 'unverified'
        result['pre_contact_window_validated'] = False
        if result['status'] == 'usable':
            start = int(result['onset_index'])
            result['speed_gain_0_3'] = g.s.iloc[start + 3] - g.s.iloc[start]
            result['speed_at_0_3'] = g.s.iloc[start + 3]
            result['displacement_0_3'] = np.hypot(g.x.iloc[start + 3] - g.x.iloc[start],
                                                 g.y.iloc[start + 3] - g.y.iloc[start])
        rows.append(result)
    attempts = pd.DataFrame(rows)
    attempts.to_csv(data / 'edge_get_off_attempts.csv', index=False)
    valid = attempts.loc[attempts.included]
    combine = valid.groupby('nfl_id')[FEATURES].median().add_prefix('combine_')
    combine['n_combine_attempts'] = valid.groupby('nfl_id').size()
    by_direction = valid.groupby(['nfl_id', 'direction'])[FEATURES].median().reset_index()
    by_direction.to_csv(data / 'edge_get_off_by_direction.csv', index=False)

    plays = pd.read_csv(SOURCE / 'player_play.csv', usecols=[
        'game_id', 'play_id', 'nfl_id', 'lined_up_position', 'play_nullified_by_penalty',
        'pass_result', 'player_get_off'], keep_default_na=False)
    plays = plays.loc[plays.nfl_id.isin(cohort.nfl_id)]
    if plays.duplicated(['game_id', 'play_id', 'nfl_id']).any():
        raise ValueError('Duplicate player-play observations')
    games = pd.read_csv(SOURCE / 'games.csv', usecols=['game_id', 'season', 'season_type'])
    plays = plays.merge(games, on='game_id', how='left', validate='many_to_one').merge(
        cohort[['nfl_id', 'draft_year']], on='nfl_id', validate='many_to_one')
    eligible = plays.loc[plays.season_type.eq('REG') & plays.season.eq(plays.draft_year) &
                         plays.lined_up_position.eq('EDGE') & plays.play_nullified_by_penalty.eq('N') &
                         plays.pass_result.isin(['C', 'I', 'IN', 'S', 'R'])].copy()
    eligible['get_off'] = pd.to_numeric(eligible.player_get_off, errors='coerce')
    observed = eligible.loc[np.isfinite(eligible.get_off) & eligible.get_off.ge(0)]
    nfl = observed.groupby('nfl_id').agg(n_get_off_snaps=('get_off', 'size'),
        median_nfl_get_off=('get_off', 'median'), mean_nfl_get_off=('get_off', 'mean'),
        n_at_2=('get_off', lambda s: s.eq(2).sum()))
    players = cohort.merge(combine, on='nfl_id', how='left').merge(nfl, on='nfl_id', how='left')
    players['n_eligible_edge_pass_snaps'] = players.nfl_id.map(eligible.groupby('nfl_id').size()).fillna(0).astype(int)
    players['n_get_off_snaps'] = players.n_get_off_snaps.fillna(0).astype(int)
    players['included_in_comparison'] = players.n_get_off_snaps.ge(args.min_snaps) & players.combine_speed_gain_0_5.notna()
    players.to_csv(data / 'edge_get_off_players.csv', index=False)
    comparison = players.loc[players.included_in_comparison].copy()
    if len(comparison) < 3:
        raise ValueError('Insufficient player coverage; see edge_get_off_players.csv')
    rng = np.random.default_rng(2027)
    associations = []
    for feature in ['combine_' + f for f in FEATURES]:
        for adjusted in [False, True]:
            samples = []
            # Player bootstrap stratified by draft year; never resample snaps as players.
            for _ in range(args.bootstrap):
                sample = pd.concat([g.iloc[rng.integers(0, len(g), len(g))]
                                    for _, g in comparison.groupby('draft_year')], ignore_index=True)
                samples.append(rank_correlation(sample, feature, adjusted))
            low, high = np.nanpercentile(samples, [2.5, 97.5])
            associations.append(dict(feature=feature, draft_year_adjusted=adjusted,
                n_players=len(comparison), rank_correlation=rank_correlation(comparison, feature, adjusted),
                ci_low=low, ci_high=high))
    associations = pd.DataFrame(associations)
    associations.to_csv(data / 'edge_get_off_associations.csv', index=False)
    fig, ax = plt.subplots(figsize=(8, 5), layout='constrained')
    for year, group in comparison.groupby('draft_year'):
        ax.scatter(group.combine_speed_gain_0_5, group.median_nfl_get_off, label=str(year), alpha=.8)
    primary = associations.loc[associations.feature.eq('combine_speed_gain_0_5') &
                               ~associations.draft_year_adjusted].iloc[0]
    ax.set(xlabel='Combine speed gain over 0.5 s after detected movement (source units)',
           ylabel='Median rookie NFL player_get_off (supplied units)',
           title=f'EDGE initial burst versus NFL get-off | {len(comparison)} players')
    ax.text(.02, .98, f'Rank correlation: {primary.rank_correlation:.2f}\n95% bootstrap CI: [{primary.ci_low:.2f}, {primary.ci_high:.2f}]',
            transform=ax.transAxes, va='top', fontsize=9)
    ax.legend(title='Draft year')
    ax.grid(alpha=.15)
    fig.savefig(ROOT / 'figures' / 'edge_get_off_nfl.png', dpi=160)
    plt.close(fig)
    summary = '\n'.join([
        f'Cohort: {len(cohort)} players; {len(attempts)} recorded Combine attempts',
        f'Included Combine attempts: {len(valid)}; players: {valid.nfl_id.nunique()}',
        'Video-synchronized, pre-contact-validated attempts: 0 (see edge_video_validation.py)',
        f'Excluded statuses: {attempts.loc[~attempts.included, "status"].value_counts().to_dict()}',
        f'Long recording review flags: {attempts.long_recording_review.sum()}',
        f'Qualifying rookie EDGE passing plays: {len(eligible)}; observed nonnegative get-off: {len(observed)}',
        f'Comparison: {len(comparison)} players; minimum {args.min_snaps} observed NFL snaps each',
        f'Players by draft year: {comparison.draft_year.value_counts().sort_index().to_dict()}',
        associations.round(3).to_string(index=False),
        'Exploratory associations only. Onset/phase, units, and exact player_get_off definition require validation.',
        'No cue-aligned reaction time, contact annotation, causal effect, or predictive validation is established.',
    ]) + '\n'
    (data / 'edge_get_off_summary.txt').write_text(summary)
    print(summary)


if __name__ == '__main__':
    main()
