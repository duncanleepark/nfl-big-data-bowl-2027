"""Build the WR speed-out / rookie NFL OUT-route sample and coverage tables.

Run: .venv/bin/python exploratory_scripts/wr_out_coverage.py
The two speed-out names are aliases per the user's confirmed drill definition.
This is a coverage audit, not a movement-quality screen or performance model.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'nfl-big-data-bowl-2027'
ALIASES = {'SPEED_OUT_LEFT', 'SPEED_OUT_ROUTE_LEFT'}
KEY = ['nfl_id', 'event_id', 'attempt']
PRIMARY, SENSITIVITY = 10, 20


def qualifying_out_mask(frame):
    return (frame.season.eq(frame.draft_year) & frame.season_type.eq('REG') &
        frame.play_nullified_by_penalty.eq('N') &
        frame.lined_up_position.isin(['WR', 'SLOT_WR']) & frame.route_ran.eq('OUT') &
        np.isfinite(frame.separation_at_pass_forward) & frame.separation_at_pass_forward.ge(0))


def main():
    data = ROOT / 'data'
    data.mkdir(exist_ok=True)
    roster = pd.read_csv(SOURCE / 'players.csv')
    results = pd.read_csv(SOURCE / 'combine_results.csv')
    if results.duplicated(['nfl_id', 'draft_year']).any() or roster.nfl_id.duplicated().any():
        raise ValueError('Duplicate player metadata')
    cohort = results.loc[results.combine_position.eq('WR'),
        ['nfl_id', 'draft_year', 'combine_position', 'combine_height', 'combine_weight',
         'forty', 'ten_yd_split', 'three_cone', 'short_shuttle']].merge(
        roster[['nfl_id', 'draft_year', 'display_name', 'nfl_position', 'college_name']],
        on=['nfl_id', 'draft_year'], how='left', validate='one_to_one')
    if cohort.display_name.isna().any():
        raise ValueError('Unmatched WR roster metadata')
    tracking = pd.read_csv(SOURCE / 'combine_tracking.csv')
    tracks = tracking.loc[tracking.nfl_id.isin(cohort.nfl_id) &
        tracking.entity_type.eq('PLAYER') & tracking.drill_name.isin(ALIASES)].copy()
    attempts = []
    for key, g in tracks.groupby(KEY, dropna=False):
        g = g.sort_values('time')
        times = pd.to_datetime(g.time, errors='coerce')
        finite = np.isfinite(g[['x', 'y', 's']].to_numpy()).all()
        regular = times.notna().all() and np.allclose(times.diff().dropna().dt.total_seconds(), .1, atol=.005)
        attempts.append(dict(zip(KEY, key)) | dict(draft_year=g.draft_year.iloc[0],
            source_drill_names='|'.join(sorted(g.drill_name.unique())),
            canonical_drill='SPEED_OUT_ROUTE_LEFT', n_frames=len(g),
            recording_start=g.time.iloc[0], recording_end=g.time.iloc[-1],
            duration_s=(times.iloc[-1]-times.iloc[0]).total_seconds(),
            finite_tracking_values=bool(finite), regular_10hz=bool(regular)))
    attempts = pd.DataFrame(attempts).merge(cohort[['nfl_id','display_name']],on='nfl_id',validate='many_to_one')
    attempts.to_csv(data / 'wr_speed_out_attempts.csv', index=False)
    summary = attempts.groupby('nfl_id').agg(n_combine_speed_out_attempts=('attempt','size'),
        source_drill_names=('source_drill_names',lambda s:'|'.join(sorted(set(s)))),
        n_irregular_combine_attempts=('regular_10hz',lambda s:(~s).sum()),
        n_nonfinite_combine_attempts=('finite_tracking_values',lambda s:(~s).sum()))
    players = cohort.merge(summary,on='nfl_id',how='left',validate='one_to_one')
    players['n_combine_speed_out_attempts'] = players.n_combine_speed_out_attempts.fillna(0).astype(int)
    players['has_combine_speed_out'] = players.n_combine_speed_out_attempts.gt(0)

    columns = ['game_id','play_id','nfl_id','lined_up_position','route_ran','pass_result',
        'play_nullified_by_penalty','separation_at_pass_forward','target','cushion',
        'team_coverage_man_zone','team_coverage_type','receiver_alignment',
        'in_motion_at_ball_snap','offense_formation','team_abbr','play_direction']
    plays = pd.read_csv(SOURCE / 'player_play.csv',usecols=columns)
    plays = plays.loc[plays.nfl_id.isin(cohort.nfl_id)].copy()
    if plays.duplicated(['nfl_id','game_id','play_id']).any():
        raise ValueError('Duplicate player-play observations')
    games = pd.read_csv(SOURCE/'games.csv',usecols=['game_id','season','season_type'])
    plays = plays.merge(games,on='game_id',how='left',validate='many_to_one').merge(
        cohort[['nfl_id','draft_year']],on='nfl_id',validate='many_to_one')
    if plays.season.isna().any():
        raise ValueError('Missing game metadata')
    rookie = plays.loc[plays.season.eq(plays.draft_year) & plays.season_type.eq('REG')]
    receiver = rookie.loc[rookie.play_nullified_by_penalty.eq('N') & rookie.lined_up_position.isin(['WR','SLOT_WR'])]
    out = receiver.loc[receiver.route_ran.eq('OUT')]
    qualifying = plays.loc[qualifying_out_mask(plays)].copy()
    stages = [('all_supplied_nfl_player_plays',plays),('rookie_regular_season_player_plays',rookie),
        ('non_nullified_rookie_WR_or_slot_plays',receiver),('NFL_OUT_before_separation_filter',out),
        ('qualifying_NFL_OUT_with_observed_separation',qualifying)]
    funnel = [dict(stage='combine_WR_metadata',n_players=len(cohort),n_records=len(cohort),record_unit='player'),
        dict(stage='has_either_speed_out_alias',n_players=attempts.nfl_id.nunique(),n_records=len(attempts),record_unit='Combine recording')]
    for label, frame in stages:
        counts = frame.groupby('nfl_id').size()
        players['n_'+label] = players.nfl_id.map(counts).fillna(0).astype(int)
        funnel.append(dict(stage=label,n_players=frame.nfl_id.nunique(),n_records=len(frame),record_unit='player-play'))
    players['n_qualifying_out_routes'] = players.n_qualifying_NFL_OUT_with_observed_separation
    for name, mask in {
        'targeted':qualifying.target.eq(True), 'non_targeted':qualifying.target.eq(False),
        'unknown_target':qualifying.target.isna(),
        'man':qualifying.team_coverage_man_zone.eq('MAN_COVERAGE'),
        'zone':qualifying.team_coverage_man_zone.eq('ZONE_COVERAGE'),
        'unknown_coverage':~qualifying.team_coverage_man_zone.isin(['MAN_COVERAGE','ZONE_COVERAGE']),
        'wide':qualifying.lined_up_position.eq('WR'),
        'slot':qualifying.lined_up_position.eq('SLOT_WR'),
        'missing_cushion':qualifying.cushion.isna(),
    }.items():
        counts = qualifying.loc[mask].groupby('nfl_id').size()
        players['n_out_'+name] = players.nfl_id.map(counts).fillna(0).astype(int)
    players['eligible_10'] = players.has_combine_speed_out & players.n_qualifying_out_routes.ge(PRIMARY)
    players['eligible_20'] = players.has_combine_speed_out & players.n_qualifying_out_routes.ge(SENSITIVITY)
    players['coverage_status'] = np.select([
        ~players.has_combine_speed_out,
        players.n_all_supplied_nfl_player_plays.eq(0),
        players.n_qualifying_out_routes.eq(0),
        players.n_qualifying_out_routes.lt(PRIMARY),
        players.n_qualifying_out_routes.lt(SENSITIVITY)],
        ['no_combine_speed_out','no_supplied_NFL_player_plays','no_qualifying_rookie_OUT',
         'below_10','10_to_19'],default='20_plus')
    players = players.sort_values(['draft_year','display_name'])
    players.to_csv(data/'wr_out_player_coverage.csv',index=False)
    players.loc[players.eligible_10].to_csv(data/'wr_out_sample_10.csv',index=False)
    players.loc[players.eligible_20].to_csv(data/'wr_out_sample_20.csv',index=False)
    qualifying = qualifying.merge(players[['nfl_id','display_name','eligible_10','eligible_20']],
        on='nfl_id',validate='many_to_one')
    qualifying.to_csv(data/'wr_out_qualifying_routes.csv',index=False)
    for threshold in [PRIMARY,SENSITIVITY]:
        sample = players.loc[players['eligible_'+str(threshold)]]
        funnel.append(dict(stage=f'speed_out_plus_at_least_{threshold}_qualifying_OUT_routes',
            n_players=len(sample),n_records=int(sample.n_qualifying_out_routes.sum()),record_unit='player-play'))
    funnel = pd.DataFrame(funnel)
    funnel.to_csv(data/'wr_out_sample_funnel.csv',index=False)
    year_rows=[]
    for year,z in players.groupby('draft_year'):
        year_rows.append(dict(draft_year=year,n_WR=len(z),n_with_speed_out=int(z.has_combine_speed_out.sum()),
            n_combine_recordings=int(z.n_combine_speed_out_attempts.sum()),
            n_with_qualifying_OUT=int(z.n_qualifying_out_routes.gt(0).sum()),
            n_qualifying_OUT=int(z.n_qualifying_out_routes.sum()),
            n_players_10=int(z.eligible_10.sum()),n_players_20=int(z.eligible_20.sum()),
            n_routes_in_sample_10=int(z.loc[z.eligible_10,'n_qualifying_out_routes'].sum()),
            n_routes_in_sample_20=int(z.loc[z.eligible_20,'n_qualifying_out_routes'].sum())))
    years=pd.DataFrame(year_rows)
    years.to_csv(data/'wr_out_coverage_by_year.csv',index=False)
    report=['# WR speed-out / NFL OUT coverage','',
        'The two Combine drill names are treated as the same drill, as confirmed by the user.',
        'Cohort: combine_position == WR. Qualifying NFL routes: rookie regular season,',
        'non-nullified, lined_up_position WR or SLOT_WR, route_ran OUT, finite nonnegative',
        'separation_at_pass_forward. Targets and non-targets are both included.',
        'Primary threshold: 10 qualifying routes per player. Sensitivity: 20.',
        'These are coverage-qualified samples, not validated movement-quality samples.','',
        '## Coverage by draft year','',
        '| Year | WRs | Speed-out recordings | Players with qualifying OUT | Qualifying OUT | ≥10 players | ≥20 players |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for z in years.itertuples(index=False):
        report.append(f'| {z.draft_year} | {z.n_WR} | {z.n_combine_recordings} | {z.n_with_qualifying_OUT} | {z.n_qualifying_OUT} | {z.n_players_10} | {z.n_players_20} |')
    report.append(f'| Total | {len(players)} | {len(attempts)} | {players.n_qualifying_out_routes.gt(0).sum()} | {len(qualifying)} | {players.eligible_10.sum()} | {players.eligible_20.sum()} |')
    report += ['','## Threshold sample context','',
        '| Threshold | Players | Routes | Targeted | Non-targeted | Man | Zone | Unknown coverage | Missing cushion | Multiple Combine reps |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for threshold in [PRIMARY,SENSITIVITY]:
        z = players.loc[players['eligible_'+str(threshold)]]
        report.append(f'| ≥{threshold} | {len(z)} | {z.n_qualifying_out_routes.sum()} | {z.n_out_targeted.sum()} | {z.n_out_non_targeted.sum()} | {z.n_out_man.sum()} | {z.n_out_zone.sum()} | {z.n_out_unknown_coverage.sum()} | {z.n_out_missing_cushion.sum()} | {z.n_combine_speed_out_attempts.gt(1).sum()} |')
    report += ['','## Funnel','','| Stage | Players | Records | Record unit |','| --- | ---: | ---: | --- |']
    for z in funnel.itertuples(index=False):
        report.append(f'| {z.stage} | {z.n_players} | {z.n_records} | {z.record_unit} |')
    report += ['','## Player-level coverage','',
        '| Player | Year | Combine reps | Qualifying OUT | Targeted | Non-targeted | Man | Zone | ≥10 | ≥20 |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |']
    for z in players.itertuples(index=False):
        report.append(f'| {z.display_name} | {z.draft_year} | {z.n_combine_speed_out_attempts} | {z.n_qualifying_out_routes} | {z.n_out_targeted} | {z.n_out_non_targeted} | {z.n_out_man} | {z.n_out_zone} | {"yes" if z.eligible_10 else "—"} | {"yes" if z.eligible_20 else "—"} |')
    report += ['','## Interpretation and limits','',
        'Zero counts mean no qualifying observations in these supplied files; they do not',
        'prove a player never ran an OUT route. Missing separation is not imputed as zero.',
        'Missing cushion or coverage does not exclude a route from this coverage audit.',
        'Target and coverage counts are exported with unknown categories for reconciliation.',
        'Use combine_position consistently: roster nfl_position can differ. Eligibility is',
        'based on route count, not the measured separation value or conventional test results.',
        'No pass-result filter is added; observed valid separation occurs only on C/I/IN',
        'in this run. Combine frame/timestamp checks are diagnostic, not inclusion filters.',
        'All current Combine recordings pass these finite-value and 10 Hz checks; this',
        'does not validate route phase boundaries. Elijah Higgins is a Combine WR but',
        'roster TE; he remains in the cohort and has six qualifying WR/slot OUT routes,',
        'so he does not meet either sample threshold.',
        'Both thresholds retain all qualifying routes for eligible players, not just the',
        'first 10 or 20. Thresholds describe the sample, not established reliability.','',
        'Reproduce: `.venv/bin/python exploratory_scripts/wr_out_coverage.py`. All CSV',
        'exports are under `data/wr_out_*`, with Combine recordings in',
        '`data/wr_speed_out_attempts.csv`. The qualifying-route export carries sample flags.']
    (ROOT/'figures'/'wr_out_coverage.md').write_text('\n'.join(report)+'\n')
    print(funnel.to_string(index=False));print('\n'+years.to_string(index=False))
    print('\nCoverage status:',players.coverage_status.value_counts().to_dict())
    print('\nRoster-position differences:',players.loc[players.nfl_position.ne('WR'),['display_name','nfl_position','n_qualifying_out_routes']].to_dict('records'))


if __name__=='__main__':
    main()
