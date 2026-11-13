"""Official 10-yard baseline and independent tracking-40 quality audit.

Run: .venv/bin/python exploratory_scripts/edge_forty_audit.py
Fixed coordinate gates are provisional source units, not official timing gates.
No NFL outcomes are used to choose tracking gates or quality thresholds.
"""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from edge_pass_rush_cohort import select_edge_cohort
from edge_pass_rush_audit import icc_agreement

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'nfl-big-data-bowl-2027'
KEY = ['nfl_id', 'event_id', 'attempt']
METRICS = ['time_x12_x22', 'time_x13_x23', 'speed_gain_x12_x17', 'mean_acceleration_x12_x17']


def crossing(x, t, speed, gate):
    """Interpolate first forward gate crossing; require a bracket in the record."""
    if x[0] > gate:
        return np.nan, np.nan
    hits = np.flatnonzero((x[:-1] <= gate) & (x[1:] > gate))
    if not len(hits):
        return np.nan, np.nan
    i = hits[0]
    fraction = (gate-x[i])/(x[i+1]-x[i])
    return t[i]+fraction*(t[i+1]-t[i]), speed[i]+fraction*(speed[i+1]-speed[i])


def audit_forty(g):
    g = g.sort_values('time').reset_index(drop=True)
    time = pd.to_datetime(g.time, errors='coerce')
    t = (time-time.iloc[0]).dt.total_seconds().to_numpy()
    x, y, s = (g[k].to_numpy(dtype=float) for k in ['x', 'y', 's'])
    result = dict(n_frames=len(g), recording_start=g.time.iloc[0],
        duration_s=t[-1], x_start=x[0], x_end=x[-1], y_start=y[0],
        initial_speed=s[0], start_below_0_2=bool(s[0] < .2),
        net_dx=x[-1]-x[0], lateral_range=np.ptp(y),
        reverse_steps=int((np.diff(x)<-.05).sum()),
        segment_reverse_steps=int(((np.diff(x)<-.05) & (x[1:]>=12) & (x[:-1]<=23)).sum()),
        regular_10hz=bool(time.notna().all() and np.allclose(np.diff(t), .1, atol=.005)))
    result['finite_values'] = bool(np.isfinite(np.r_[x,y,s,t]).all())
    quality = result['regular_10hz'] and result['finite_values']
    result['status'] = 'invalid_time_or_values' if not quality else 'usable_fixed_gates'
    # Broad course checks; do not impose a start speed/onset threshold.
    if quality and (result['segment_reverse_steps'] or result['lateral_range'] > 2 or not 35 <= result['net_dx'] <= 45):
        result['status'] = 'course_review'
    if quality:
        gates = {gate: crossing(x, t, s, gate) for gate in [12,13,17,20,22,23,50]}
        for gate, (at, speed) in gates.items():
            result[f't_x{gate}_s'] = at
            result[f'speed_x{gate}'] = speed
        result['time_x12_x22'] = gates[22][0]-gates[12][0]
        result['time_x13_x23'] = gates[23][0]-gates[13][0]
        result['speed_gain_x12_x17'] = gates[17][1]-gates[12][1]
        elapsed = gates[17][0]-gates[12][0]
        result['mean_acceleration_x12_x17'] = result['speed_gain_x12_x17']/elapsed if elapsed > 0 else np.nan
        if not np.isfinite([result[k] for k in METRICS]).all():
            result['status'] = 'missing_gate_bracket'
        result['median_dxdt_over_speed'] = np.median(np.diff(x)/np.diff(t)/((s[1:]+s[:-1])/2))
    return result


def correlation(frame, feature, adjusted):
    ranks = frame[[feature, 'median_nfl_get_off']].rank()
    if adjusted:
        ranks -= ranks.groupby(frame.draft_year).transform('mean')
    return ranks.corr().iloc[0,1] if len(frame) >= 3 else np.nan


def rookie_get_off(cohort):
    plays = pd.read_csv(SOURCE/'player_play.csv', usecols=['game_id','play_id','nfl_id',
        'lined_up_position','play_nullified_by_penalty','pass_result','player_get_off'], keep_default_na=False)
    plays = plays.loc[plays.nfl_id.isin(cohort.nfl_id)]
    if plays.duplicated(['game_id','play_id','nfl_id']).any():
        raise ValueError('Duplicate player-play rows')
    games = pd.read_csv(SOURCE/'games.csv', usecols=['game_id','season','season_type'])
    plays = plays.merge(games, on='game_id', how='left', validate='many_to_one').merge(
        cohort[['nfl_id','draft_year']], on='nfl_id', validate='many_to_one')
    if plays.season.isna().any():
        raise ValueError('Missing game metadata')
    eligible = plays.loc[plays.season_type.eq('REG') & plays.season.eq(plays.draft_year) &
        plays.lined_up_position.eq('EDGE') & plays.play_nullified_by_penalty.eq('N') &
        plays.pass_result.isin(['C','I','IN','S','R'])].copy()
    eligible['get_off'] = pd.to_numeric(eligible.player_get_off, errors='coerce')
    observed = eligible.loc[np.isfinite(eligible.get_off) & eligible.get_off.ge(0)]
    stats = observed.groupby('nfl_id').agg(n_get_off_snaps=('get_off','size'),
        median_nfl_get_off=('get_off','median'), mean_nfl_get_off=('get_off','mean'))
    stats['n_eligible_edge_pass_snaps'] = eligible.groupby('nfl_id').size()
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--min-snaps', type=int, default=20)
    parser.add_argument('--bootstrap', type=int, default=2000)
    args = parser.parse_args()
    if args.min_snaps < 1 or args.bootstrap < 100:
        parser.error('Require min-snaps >=1 and bootstrap >=100')
    data, figures = ROOT/'data', ROOT/'figures'
    data.mkdir(exist_ok=True); figures.mkdir(exist_ok=True)
    roster = pd.read_csv(SOURCE/'players.csv')
    tracking = pd.read_csv(SOURCE/'combine_tracking.csv')
    cohort = select_edge_cohort(roster, tracking)
    results = pd.read_csv(SOURCE/'combine_results.csv')
    if results.duplicated(['nfl_id','draft_year']).any():
        raise ValueError('Duplicate official Combine results')
    players = cohort.merge(results[['nfl_id','draft_year','ten_yd_split','forty','combine_weight']],
        on=['nfl_id','draft_year'], how='left', validate='one_to_one').merge(
        rookie_get_off(cohort), on='nfl_id', how='left', validate='one_to_one')
    players['n_get_off_snaps'] = players.n_get_off_snaps.fillna(0).astype(int)
    players['baseline_eligible'] = players.ten_yd_split.gt(0) & players.n_get_off_snaps.ge(args.min_snaps)
    baseline = players.loc[players.baseline_eligible].copy()
    if len(baseline) < 3:
        raise ValueError('Insufficient baseline coverage')
    rng = np.random.default_rng(2027)
    associations = []
    for adjusted in [False, True]:
        boots = []
        for _ in range(args.bootstrap):
            sample = pd.concat([g.iloc[rng.integers(0,len(g),len(g))]
                for _,g in baseline.groupby('draft_year')], ignore_index=True)
            boots.append(correlation(sample,'ten_yd_split',adjusted))
        lo, hi = np.nanpercentile(boots,[2.5,97.5])
        associations.append(dict(feature='official_ten_yd_split', draft_year_adjusted=adjusted,
            n_players=len(baseline), rho=correlation(baseline,'ten_yd_split',adjusted), ci_low=lo, ci_high=hi,
            leave_one_out_rho_min=min(correlation(baseline.drop(index=i),'ten_yd_split',adjusted) for i in baseline.index),
            leave_one_out_rho_max=max(correlation(baseline.drop(index=i),'ten_yd_split',adjusted) for i in baseline.index)))
    assoc = pd.DataFrame(associations)
    assoc.to_csv(data/'edge_ten_yard_baseline_associations.csv',index=False)

    tracks = tracking.loc[tracking.nfl_id.isin(cohort.nfl_id) &
        tracking.drill_name.eq('FORTY_YARD_DASH') & tracking.entity_type.eq('PLAYER')]
    rows, groups = [], {}
    for key, g in tracks.groupby(KEY):
        rows.append(dict(zip(KEY,key)) | audit_forty(g))
        groups[key] = g.sort_values('time')
    attempts = pd.DataFrame(rows).merge(cohort[['nfl_id','display_name','draft_year']],on='nfl_id',validate='many_to_one')
    attempts = attempts.sort_values(['nfl_id','recording_start','event_id','attempt'])
    attempts.to_csv(data/'edge_forty_attempts.csv',index=False)
    usable = attempts.loc[attempts.status.eq('usable_fixed_gates')]
    medians = usable.groupby('nfl_id')[METRICS].median().add_prefix('median_')
    medians['n_usable_forties'] = usable.groupby('nfl_id').size()
    players = players.merge(medians,on='nfl_id',how='left',validate='one_to_one')
    players['n_recorded_forties'] = players.nfl_id.map(attempts.groupby('nfl_id').size()).fillna(0).astype(int)
    players.to_csv(data/'edge_forty_players.csv',index=False)
    summaries, pair_rows = [], []
    first_two = usable.groupby('nfl_id').head(2).copy()
    first_two['chronological_order'] = first_two.groupby('nfl_id').cumcount()+1
    for metric in METRICS:
        pairs = first_two.pivot(index='nfl_id',columns='chronological_order',values=metric).dropna()
        x, y = pairs[1].to_numpy(), pairs[2].to_numpy()
        boots = []
        for _ in range(args.bootstrap):
            idx = rng.integers(0,len(x),len(x))
            boots.append(icc_agreement(x[idx],y[idx]))
        lo, hi = np.nanpercentile(boots,[2.5,97.5])
        summaries.append(dict(metric=metric,n_pairs=len(pairs),icc=icc_agreement(x,y),
            ci_low=lo,ci_high=hi,median_absolute_difference=np.median(abs(y-x)),
            mean_second_minus_first=np.mean(y-x),
            leave_one_out_icc_min=min(icc_agreement(np.delete(x,i),np.delete(y,i)) for i in range(len(x))),
            leave_one_out_icc_max=max(icc_agreement(np.delete(x,i),np.delete(y,i)) for i in range(len(x)))))
        pair_rows.extend(dict(nfl_id=n,metric=metric,first=a,second=b) for n,a,b in zip(pairs.index,x,y))
    repeat = pd.DataFrame(summaries)
    repeat.to_csv(data/'edge_forty_repeatability.csv',index=False)
    pair_details = pd.DataFrame(pair_rows).merge(cohort[['nfl_id','display_name','draft_year']],
        on='nfl_id',validate='many_to_one')
    pair_details['absolute_difference'] = abs(pair_details.second-pair_details['first'])
    pair_details.to_csv(data/'edge_forty_pairs.csv',index=False)
    geometry = attempts.groupby('draft_year').agg(n_attempts=('attempt','size'),
        n_players=('nfl_id','nunique'),median_x_start=('x_start','median'),
        min_x_start=('x_start','min'),max_x_start=('x_start','max'),
        median_x_end=('x_end','median'),median_net_dx=('net_dx','median'),
        median_initial_speed=('initial_speed','median'),
        median_dxdt_over_speed=('median_dxdt_over_speed','median'))
    geometry.to_csv(data/'edge_forty_geometry.csv')
    start_players = usable.groupby(['nfl_id','draft_year'])[['x_start']+METRICS].median().reset_index()
    sensitivity = []
    for metric in METRICS:
        for adjusted in [False,True]:
            ranks = start_players[['x_start',metric]].rank()
            if adjusted:
                ranks -= ranks.groupby(start_players.draft_year).transform('mean')
            sensitivity.append(dict(metric=metric,draft_year_adjusted=adjusted,
                n_players=len(start_players),rho_with_recording_start_x=ranks.corr().iloc[0,1]))
    start_sensitivity = pd.DataFrame(sensitivity)
    start_sensitivity.to_csv(data/'edge_forty_start_sensitivity.csv',index=False)

    fig, axes = plt.subplots(1,3,figsize=(15,4.8),layout='constrained')
    for year,g in baseline.groupby('draft_year'):
        axes[0].scatter(g.ten_yd_split,g.median_nfl_get_off,label=str(year),alpha=.8)
    r = assoc.iloc[0]
    axes[0].set(xlabel='Official 10-yard split (s)',ylabel='Median rookie NFL player_get_off (supplied units)',
        title=f'Baseline: {len(baseline)} players | rank r={r.rho:.2f}\n95% CI [{r.ci_low:.2f}, {r.ci_high:.2f}]')
    axes[0].legend(title='Draft year')
    for _,g in tracks.groupby(KEY):
        g=g.sort_values('time');axes[1].plot(g.x,g.y,alpha=.15,color='#286f9c')
    axes[1].axvline(12,color='#c55b35',ls='--');axes[1].axvline(22,color='#c55b35',ls='--')
    axes[1].set(xlabel='Source x coordinate',ylabel='Source y coordinate',title=f'40-yard tracking: {len(attempts)} reps\nDashed lines = provisional fixed gates')
    pair = pd.DataFrame(pair_rows);pair=pair.loc[pair.metric.eq(METRICS[0])]
    axes[2].scatter(pair['first'],pair.second,alpha=.7)
    limits=[min(pair['first'].min(),pair.second.min()),max(pair['first'].max(),pair.second.max())]
    axes[2].plot(limits,limits,'--',color='gray')
    axes[2].set(xlabel='First rep: x12 to x22 elapsed time (s)',ylabel='Second rep: same segment time (s)',
        title=f'Fixed segment repeatability: {len(pair)} pairs\nICC(A,1)={repeat.iloc[0].icc:.2f}')
    for ax in axes: ax.grid(alpha=.15)
    fig.savefig(figures/'edge_forty_audit.png',dpi=160);plt.close(fig)
    summary='\n'.join([
        f'Filtered cohort: {len(players)} players',
        f'Official 10-yard splits: {players.ten_yd_split.notna().sum()}; baseline eligible: {len(baseline)}',
        f'Baseline years: {baseline.draft_year.value_counts().sort_index().to_dict()}',
        assoc.round(3).to_string(index=False),
        f'Tracked 40s: {len(attempts)} attempts / {attempts.nfl_id.nunique()} players',
        f'Statuses: {attempts.status.value_counts().to_dict()}',
        f'Recordings starting below speed 0.2: {attempts.start_below_0_2.sum()}',
        f'Common baseline + fixed-gate coverage: {(players.baseline_eligible & players.median_time_x12_x22.notna()).sum()}',
        'Geometry:\n'+geometry.round(3).to_string(),
        'Repeatability:\n'+repeat.round(3).to_string(index=False),
        'Recording-start sensitivity (player medians):\n'+start_sensitivity.round(3).to_string(index=False),
        'Gate times are movement segment durations, not official splits or reaction times.',
        'No NFL alignment-depth adjustment, prospective role selection, or predictive validation performed.',
    ])+'\n'
    (data/'edge_forty_audit_summary.txt').write_text(summary);print(summary)


if __name__=='__main__':
    main()
