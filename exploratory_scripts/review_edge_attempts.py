"""Plot paired attempts for the six largest existing burst disagreements.

Run after edge_pass_rush_audit.py. This is an outcome-selected diagnostic,
not a representative sample or a change to the measurement rule.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
SOURCE = ROOT / 'nfl-big-data-bowl-2027'
OUT = ROOT / 'figures' / 'edge_attempt_review'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pairs = pd.read_csv(DATA / 'edge_pass_rush_repeatability.csv')
    pairs['abs_difference'] = pairs.difference_second_minus_first.abs()
    pairs = pairs.sort_values(['abs_difference', 'nfl_id'], ascending=[False, True]).head(6)
    attempts = pd.read_csv(DATA / 'edge_pass_rush_attempts.csv')
    attempts = attempts[(attempts.nfl_id.isin(pairs.nfl_id)) & (attempts.status == 'usable')]
    attempts = attempts.sort_values(['nfl_id', 'recording_start', 'event_id', 'attempt']).groupby('nfl_id').head(2)
    tracks = pd.read_csv(SOURCE / 'combine_tracking.csv')
    tracks = tracks[(tracks.nfl_id.isin(pairs.nfl_id)) & (tracks.drill_name == 'PASS_RUSH_DRILL') & (tracks.entity_type == 'PLAYER')]
    for pair in pairs.itertuples(index=False):
        subset = attempts[attempts.nfl_id == pair.nfl_id]
        assert len(subset) == 2
        fig, axes = plt.subplots(2, 2, figsize=(12, 7), constrained_layout=True)
        for i, row in enumerate(subset.itertuples(index=False)):
            f = tracks[(tracks.nfl_id == row.nfl_id) & (tracks.event_id == row.event_id) & (tracks.attempt == row.attempt)].sort_values('time').reset_index(drop=True)
            onset = int(row.onset_index); end = onset + 5
            assert len(f) > end and np.isclose(f.s.iloc[end] - f.s.iloc[onset], row.speed_gain_0_5)
            seconds = (pd.to_datetime(f.time) - pd.to_datetime(f.time.iloc[0])).dt.total_seconds().to_numpy()
            x = f.x.to_numpy() - f.x.iloc[0]; y = f.y.to_numpy() - f.y.iloc[0]
            ax = axes[0, i]
            ax.plot(x, y, color='#b8c2cc', lw=1.5, label='Full path')
            ax.plot(x[onset:end+1], y[onset:end+1], color='#ca572c', lw=4, label='Scored window')
            ax.scatter(x[0], y[0], color='black', s=25, zorder=4, label='Recording start')
            ax.scatter(x[onset], y[onset], color='#ca572c', edgecolors='white', s=45, zorder=5, label='Detected onset')
            ax.set_aspect('equal', adjustable='box'); ax.set_xlabel('x displacement (source units)'); ax.set_ylabel('y displacement (source units)'); ax.grid(alpha=.2)
            ax.set_title(f'Attempt {i+1} (source attempt {row.attempt}) | gain {row.speed_gain_0_5:.2f}')
            ax = axes[1, i]; ax.plot(seconds, f.s, color='#285d91', lw=2)
            ax.axhline(1, color='gray', ls=':', label='Onset threshold')
            ax.axvspan(seconds[onset], seconds[end], alpha=.25, color='#ca572c', label='Scored 0.5 s')
            ax.scatter([seconds[onset],seconds[end]], [f.s.iloc[onset],f.s.iloc[end]], color='#ca572c', s=25, zorder=4)
            ax.set(xlabel='Seconds since recording start', ylabel='Speed (source units)', ylim=(0, 10)); ax.grid(alpha=.2)
        axes[0,0].legend(loc='best', fontsize=8); axes[1,0].legend(loc='best', fontsize=8)
        fig.suptitle(f'{pair.display_name} | {pair.nfl_position}, {pair.draft_year} | difference {pair.abs_difference:.2f} (source speed units)', fontsize=14)
        fig.savefig(OUT / f'{pair.nfl_id}.png', dpi=150); plt.close(fig)
        print(f'{pair.display_name}: {pair.first:.3f} vs {pair.second:.3f}; saved {OUT / str(pair.nfl_id)}.png')

if __name__ == '__main__': main()
