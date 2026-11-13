"""Audit recorded PASS_RUSH_DRILL directions without assuming attempt = side.

Run from the repository root with .venv/bin/python. Direction labels describe
net travel in source coordinates, not a verified football alignment side.
Uses the shared cohort excluding primarily interior NFL alignments.
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from edge_pass_rush_cohort import select_edge_cohort

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'nfl-big-data-bowl-2027'
KEY = ['nfl_id', 'event_id', 'attempt']
COLORS = {'negative_y': '#c55b35', 'positive_y': '#286f9c'}


def main():
    roster = pd.read_csv(SOURCE / 'players.csv')
    tracks = pd.read_csv(SOURCE / 'combine_tracking.csv')
    edge_ids = set(select_edge_cohort(roster, tracks).nfl_id)
    tracks = tracks.loc[tracks.drill_name.eq('PASS_RUSH_DRILL') &
                        tracks.entity_type.eq('PLAYER')].copy()
    tracks = tracks.merge(roster.drop(columns='draft_year'), on='nfl_id',
                          how='left', validate='many_to_one')
    if tracks.nfl_position.isna().any():
        raise ValueError('Unmatched roster positions require cohort review')
    rows, groups = [], {}
    for key, group in tracks.groupby(KEY, dropna=False):
        g = group.sort_values('time').reset_index(drop=True)
        first, last = g.iloc[0], g.iloc[-1]
        times = pd.to_datetime(g.time)
        dx, dy = last.x - first.x, last.y - first.y
        if not np.isfinite(g[['x', 'y', 's']].to_numpy()).all():
            raise ValueError(f'Invalid tracking values: {key}')
        # Current recordings all have a large net lateral displacement. Do not
        # silently classify a future ambiguous/short recording by a tiny sign.
        direction = ('negative_y' if dy < 0 else 'positive_y') if abs(dy) >= 10 else 'ambiguous'
        rows.append(dict(zip(KEY, key)) | {
            'display_name': first.display_name, 'draft_year': first.draft_year,
            'nfl_position': first.nfl_position, 'drill_type': first.drill_type,
            'is_edge_proxy': first.nfl_position in ('DE', 'OLB'),
            'is_edge_cohort': first.nfl_id in edge_ids,
            'recording_start': first.time, 'n_frames': len(g),
            'duration_s': (times.iloc[-1] - times.iloc[0]).total_seconds(),
            'regular_10hz': bool(np.allclose(times.diff().dropna().dt.total_seconds(), .1, atol=.005)),
            'x_start': first.x, 'y_start': first.y,
            'x_end': last.x, 'y_end': last.y,
            'net_dx': dx, 'net_dy': dy, 'direction': direction,
            'initial_speed': first.s,
        })
        groups[key] = g

    attempts = pd.DataFrame(rows).sort_values(['nfl_id', 'recording_start', 'event_id', 'attempt'])
    edge = attempts.loc[attempts.is_edge_cohort].copy()
    players = edge.groupby(['nfl_id', 'display_name', 'draft_year'], as_index=False).agg(
        n_attempts=('attempt', 'size'), n_directions=('direction', 'nunique'),
        chronological_source_attempts=('attempt', lambda s: '|'.join(s.astype(str))),
        chronological_directions=('direction', lambda s: '|'.join(s)),
    )
    counts = edge.groupby(['draft_year', 'attempt', 'direction']).size().rename('n_attempts').reset_index()
    setup = edge.groupby(['draft_year', 'drill_type', 'direction'], as_index=False).agg(
        n_attempts=('attempt', 'size'), median_x_start=('x_start', 'median'),
        median_y_start=('y_start', 'median'), median_net_dx=('net_dx', 'median'),
        median_net_dy=('net_dy', 'median'), median_duration_s=('duration_s', 'median'),
    )
    data = ROOT / 'data'
    data.mkdir(exist_ok=True)
    attempts.to_csv(data / 'pass_rush_setup_attempts.csv', index=False)
    players.to_csv(data / 'edge_pass_rush_setup_players.csv', index=False)
    counts.to_csv(data / 'edge_pass_rush_direction_counts.csv', index=False)
    setup.to_csv(data / 'edge_pass_rush_setup_geometry.csv', index=False)

    fig, axes = plt.subplots(1, 3, figsize=(12, 6), sharex=True, sharey=True, layout='constrained')
    for ax, (year, subset) in zip(axes, edge.groupby('draft_year')):
        for row in subset.itertuples(index=False):
            g = groups[tuple(getattr(row, k) for k in KEY)]
            ax.plot(g.x, g.y, color=COLORS[row.direction], alpha=.30, lw=1)
            ax.scatter(g.x.iloc[0], g.y.iloc[0], color=COLORS[row.direction], s=10, alpha=.6)
        for direction, color in COLORS.items():
            n = subset.direction.eq(direction).sum()
            ax.plot([], [], color=color, label=f'{direction.replace("_", " ")}: {n} reps')
        ax.set_title(f'{year} | {subset.nfl_id.nunique()} players, {len(subset)} reps')
        ax.set_xlabel('Source x coordinate')
        ax.set_aspect('equal', adjustable='box')
        ax.grid(alpha=.15)
        ax.legend(loc='upper left', fontsize=8)
    axes[0].set_ylabel('Source y coordinate')
    fig.suptitle('PASS_RUSH_DRILL: retained EDGE paths run in both directions', fontsize=13)
    fig.supxlabel(f'Dots = recording starts; {len(edge)} retained recordings shown. Equipment and cue are not tracked.', fontsize=9)
    figures = ROOT / 'figures'
    figures.mkdir(exist_ok=True)
    fig.savefig(figures / 'edge_pass_rush_setup.png', dpi=160)
    plt.close(fig)

    multi = players.loc[players.n_attempts > 1]
    first_two = edge.groupby('nfl_id', sort=False).head(2)
    first_two_multi = first_two.loc[first_two.nfl_id.isin(multi.nfl_id)]
    opposite_first_two = first_two_multi.groupby('nfl_id').direction.nunique().eq(2).sum()
    old = pd.read_csv(data / 'edge_pass_rush_attempts.csv')
    old_pairs = old.loc[old.status.eq('usable')].sort_values(
        ['nfl_id', 'recording_start', 'event_id', 'attempt']).groupby('nfl_id').head(2)
    old_pairs = old_pairs.merge(attempts[KEY + ['direction']], on=KEY, validate='one_to_one')
    paired = old_pairs.groupby('nfl_id').filter(lambda g: len(g) == 2)
    paired_opposite = paired.groupby('nfl_id').direction.nunique().eq(2).sum()
    stats = [
        f'All PLAYER PASS_RUSH_DRILL: {len(attempts)} attempts, {attempts.nfl_id.nunique()} players',
        f'EDGE cohort after primary-interior exclusions: {len(edge)} attempts, {edge.nfl_id.nunique()} players',
        f'Attempt counts per player: {players.n_attempts.value_counts().sort_index().to_dict()}',
        f'Multi-attempt players covering both directions: {multi.n_directions.eq(2).sum()}/{len(multi)}',
        f'First two recorded attempts in opposite directions: {opposite_first_two}/{len(multi)}',
        f'Existing usable audit pairs in opposite directions: {paired_opposite}/{paired.nfl_id.nunique()}',
        f'Ambiguous direction recordings: {edge.direction.eq("ambiguous").sum()}',
        f'Irregular timestamp recordings: {(~edge.regular_10hz).sum()}',
        '\nDirection counts:\n' + counts.to_string(index=False),
        '\nRecordings longer than 6 seconds (review lead-in):\n' + edge.loc[
            edge.duration_s > 6, ['display_name', 'draft_year', 'attempt', 'duration_s', 'initial_speed']].to_string(index=False),
    ]
    summary = '\n'.join(stats) + '\n'
    (data / 'edge_pass_rush_setup_summary.txt').write_text(summary)
    print(summary)


if __name__ == '__main__':
    main()
