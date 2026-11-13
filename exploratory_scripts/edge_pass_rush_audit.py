"""Audit initial movement in EDGE Combine pass-rush attempts; no NFL outcomes.

Run from repository root: .venv/bin/python exploratory_scripts/edge_pass_rush_audit.py
DE/OLB candidates with primarily interior observed NFL alignments are excluded.
The retained cohort remains provisional for players without alignment evidence. Speed and
coordinate units are retained as supplied pending confirmation of data dictionary.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from edge_pass_rush_cohort import select_edge_cohort

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'nfl-big-data-bowl-2027'
DATA = ROOT / 'data'
FIGURES = ROOT / 'figures'
THRESHOLD = 1.0  # native speed units; confirm against official dictionary
CONFIRM = 3       # consecutive 10 Hz frames at/above threshold
WINDOW = 0.5
KEY = ['nfl_id', 'event_id', 'attempt']


def audit_attempt(frame):
    f = frame.sort_values('time').reset_index(drop=True)
    speed = pd.to_numeric(f.s, errors='coerce').to_numpy()
    times = pd.to_datetime(f.time, errors='coerce')
    result = {'n_frames': len(f), 'recording_start': f.time.iloc[0],
              'initial_speed': speed[0], 'status': None, 'onset_index': np.nan,
              'onset_time_s': np.nan, 'speed_onset': np.nan, 'speed_0_5': np.nan,
              'speed_gain_0_5': np.nan}
    if times.isna().any() or not np.isfinite(speed).all() or f.time.duplicated().any():
        result['status'] = 'invalid_time_or_speed'
        return result
    if speed[0] >= THRESHOLD:
        result['status'] = 'already_above_threshold'
        return result
    hits = np.flatnonzero(np.convolve((speed >= THRESHOLD).astype(int), np.ones(CONFIRM, dtype=int), 'valid') == CONFIRM) if len(f) >= CONFIRM else []
    if len(hits) == 0:
        result['status'] = 'no_sustained_onset'
        return result
    onset = int(hits[0])
    result['onset_index'] = onset
    result['onset_time_s'] = (times.iloc[onset] - times.iloc[0]).total_seconds()
    # Require the measurement window and confirmation to be uninterrupted 10 Hz.
    end = onset + 5
    if end >= len(f):
        result['status'] = 'insufficient_window'
        return result
    increments = times.iloc[:end + 1].diff().dropna().dt.total_seconds().to_numpy()
    if not np.allclose(increments, 0.1, atol=0.005):
        result['status'] = 'irregular_window'
        return result
    result.update(status='usable', speed_onset=speed[onset], speed_0_5=speed[end],
                  speed_gain_0_5=speed[end] - speed[onset])
    return result


def icc_agreement(x, y):
    # ICC(A,1), two-way random effects, absolute agreement, two ordered attempts.
    a = np.column_stack([x, y]); n, k = a.shape
    if n < 3: return np.nan
    grand = a.mean(); row = a.mean(axis=1); col = a.mean(axis=0)
    msr = k * np.sum((row-grand)**2)/(n-1)
    msc = n * np.sum((col-grand)**2)/(k-1)
    mse = np.sum((a-row[:, None]-col[None, :]+grand)**2)/((n-1)*(k-1))
    den = msr+(k-1)*mse+k*(msc-mse)/n
    return (msr-mse)/den if den > 0 else np.nan


def main():
    DATA.mkdir(exist_ok=True); FIGURES.mkdir(exist_ok=True)
    p = pd.read_csv(SOURCE / 'players.csv', usecols=['nfl_id','display_name','nfl_position','draft_year'])
    c = pd.read_csv(SOURCE / 'combine_tracking.csv')
    p = select_edge_cohort(p, c)
    c = c[(c.drill_name == 'PASS_RUSH_DRILL') & (c.entity_type == 'PLAYER')].copy()
    c = c.drop(columns=['draft_year']).merge(p, on='nfl_id', validate='many_to_one')
    rows = []
    groups = {}
    for key, frame in c.groupby(KEY, sort=False, dropna=False):
        groups[key] = frame.sort_values('time').reset_index(drop=True)
        meta = frame.iloc[0]
        rows.append(dict(zip(KEY,key)) | {'display_name':meta.display_name, 'nfl_position':meta.nfl_position,
                     'draft_year':meta.draft_year} | audit_attempt(frame))
    attempts = pd.DataFrame(rows).sort_values(['nfl_id','recording_start','event_id','attempt'])
    attempts.to_csv(DATA/'edge_pass_rush_attempts.csv', index=False)
    usable = attempts[attempts.status == 'usable'].copy()
    summary = usable.groupby(['nfl_id','display_name','nfl_position','draft_year'], as_index=False).agg(
        n_usable_attempts=('speed_gain_0_5','size'), median_speed_gain_0_5=('speed_gain_0_5','median'),
        min_speed_gain_0_5=('speed_gain_0_5','min'), max_speed_gain_0_5=('speed_gain_0_5','max'))
    summary.to_csv(DATA/'edge_pass_rush_players.csv', index=False)
    first = usable.groupby('nfl_id', sort=False).head(2).copy()
    first['order'] = first.groupby('nfl_id').cumcount()+1
    pairs = first.pivot(index='nfl_id', columns='order', values='speed_gain_0_5').dropna().rename(columns={1:'first',2:'second'})
    pairs['difference_second_minus_first'] = pairs.second-pairs['first']
    pairs = pairs.reset_index().merge(p[['nfl_id','display_name','nfl_position','draft_year']], on='nfl_id', validate='one_to_one')
    pairs.to_csv(DATA/'edge_pass_rush_repeatability.csv', index=False)
    # Cluster bootstrap: each resampling unit is a player, not an attempt.
    rng = np.random.default_rng(2027); boots=[]
    for _ in range(2000):
        sample = pairs.iloc[rng.integers(0, len(pairs), len(pairs))]
        boots.append(icc_agreement(sample['first'].to_numpy(), sample.second.to_numpy()))
    ci = np.nanpercentile(boots,[2.5,97.5])
    # Stratified, deterministic sample: five players per year, spread through IDs;
    # earliest usable attempt, independent of measured gain and NFL outcomes.
    chosen=[]
    for year, subset in usable.sort_values(['nfl_id','recording_start']).groupby('draft_year'):
        candidates = subset.drop_duplicates('nfl_id').sort_values('nfl_id')
        chosen.extend(candidates.iloc[np.linspace(0,len(candidates)-1,min(5,len(candidates)),dtype=int)].to_dict('records'))
    fig, axes = plt.subplots(len(chosen), 2, figsize=(12, 2.35*len(chosen)), constrained_layout=True)
    for axpair, row in zip(axes,chosen):
        key=tuple(row[k] for k in KEY); f=groups[key]; onset=int(row['onset_index']); end=onset+5
        time=(pd.to_datetime(f.time)-pd.to_datetime(f.time.iloc[0])).dt.total_seconds()
        ax=axpair[0]; ax.plot(f.x-f.x.iloc[0],f.y-f.y.iloc[0],color='#9aa5b1'); ax.plot(f.x.iloc[onset:end+1]-f.x.iloc[0],f.y.iloc[onset:end+1]-f.y.iloc[0],color='#ce5937',linewidth=3)
        ax.scatter([f.x.iloc[0]-f.x.iloc[0]],[f.y.iloc[0]-f.y.iloc[0]],marker='o',s=18,color='black'); ax.set_aspect('equal',adjustable='box'); ax.set_xlabel('x displacement (source units)'); ax.set_ylabel('y displacement')
        ax.set_title(f"{row['display_name']} | {row['nfl_position']} | {row['draft_year']} | attempt {row['attempt']}",fontsize=9)
        ax=axpair[1]; ax.plot(time,f.s,color='#315f91'); ax.axhline(THRESHOLD,color='grey',linestyle=':',linewidth=1); ax.axvspan(time.iloc[onset],time.iloc[end],color='#ce5937',alpha=.25); ax.set_xlabel('seconds from recording start'); ax.set_ylabel('speed (source units)'); ax.set_title(f"0.5 s gain: {row['speed_gain_0_5']:.2f}",fontsize=9)
    fig.suptitle('EDGE pass-rush drill: 15 preselected examples; orange = measurement window',fontsize=13)
    fig.savefig(FIGURES/'edge_pass_rush_examples.png',dpi=140); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,6)); ax.scatter(pairs['first'],pairs.second,alpha=.7); lim=[min(pairs['first'].min(),pairs.second.min()),max(pairs['first'].max(),pairs.second.max())]; ax.plot(lim,lim,'--',color='gray'); ax.set(xlabel='First usable attempt: speed gain',ylabel='Second usable attempt: speed gain',title='Within-player repeatability (source speed units)'); ax.text(.04,.96,f"Players: {len(pairs)}\nICC(A,1): {icc_agreement(pairs['first'],pairs.second):.2f}\nMedian absolute difference: {(pairs.second-pairs['first']).abs().median():.2f}",transform=ax.transAxes,va='top'); fig.tight_layout(); fig.savefig(FIGURES/'edge_pass_rush_repeatability.png',dpi=160); plt.close(fig)
    stats = [f'Players with recorded drill: {attempts.nfl_id.nunique()}', f'Recorded attempts: {len(attempts)}',
             f'Attempt statuses: {attempts.status.value_counts().to_dict()}',f'Players with usable attempts: {usable.nfl_id.nunique()}',
             f'Usable attempts per player: {summary.n_usable_attempts.value_counts().sort_index().to_dict()}',
             f'Paired players: {len(pairs)}',f'ICC(A,1): {icc_agreement(pairs["first"],pairs.second):.3f}',
             f'ICC bootstrap 95% interval: [{ci[0]:.3f}, {ci[1]:.3f}]',
             f'Median absolute paired difference: {(pairs.second-pairs["first"]).abs().median():.3f}',
             f'Mean second minus first: {(pairs.second-pairs["first"]).mean():.3f}',
             f'Median gain: {usable.speed_gain_0_5.median():.3f}',
             f'Paired gain SD (all first/second values): {np.std(np.r_[pairs["first"],pairs.second],ddof=1):.3f}']
    print('\n'.join(stats))
    (DATA/'edge_pass_rush_audit_summary.txt').write_text('\n'.join(stats)+'\n')

if __name__ == '__main__': main()
