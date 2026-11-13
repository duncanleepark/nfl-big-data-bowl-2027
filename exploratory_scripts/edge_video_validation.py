"""Summarize observed video phase brackets and export unmatched tracking queue.

Run after edge_get_off.py. Video observations are not tracking annotations
until the event identity and a common clock have been independently established.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def classify_launch_window(onset_low, onset_high, contact_low, contact_high, window):
    if not (onset_low <= onset_high <= contact_low <= contact_high):
        raise ValueError('Invalid onset/contact brackets')
    earliest = contact_low - onset_high
    latest = contact_high - onset_low
    if window < earliest - 1e-8:
        return 'ends_before_contact_for_all_bracket_times'
    if window >= latest - 1e-8:
        return 'reaches_contact_for_all_bracket_times'
    return 'contact_overlap_possible_within_brackets'


def main():
    annotations = pd.read_csv(ROOT / 'exploratory_scripts' / 'edge_video_annotations.csv')
    rows = []
    for a in annotations.itertuples(index=False):
        for window in [.3, .5]:
            rows.append({'clip_id': a.clip_id, 'nfl_id': a.nfl_id,
                'window_s': window,
                'launch_to_contact_low_s': max(0, a.contact_low_s-a.onset_high_s),
                'launch_to_contact_high_s': a.contact_high_s-a.onset_low_s,
                'video_window_assessment': classify_launch_window(a.onset_low_s,
                    a.onset_high_s, a.contact_low_s, a.contact_high_s, window),
                'tracking_window_validated': False})
    windows = pd.DataFrame(rows)
    windows.to_csv(ROOT / 'data' / 'edge_video_review_windows.csv', index=False)
    attempts = pd.read_csv(ROOT / 'data' / 'edge_get_off_attempts.csv')
    roster = pd.read_csv(ROOT / 'nfl-big-data-bowl-2027' / 'players.csv')
    queue = attempts.merge(roster[['nfl_id', 'display_name', 'draft_year']],
                           on='nfl_id', validate='many_to_one')
    queue['video_candidate_available'] = queue.nfl_id.isin(annotations.nfl_id)
    queue['phase_validation_status'] = 'unverified'
    # Deliberately leave unknown times blank rather than imputing video markers
    # onto tracking recordings with no verified event match or synchronization.
    for col in ['video_onset_s', 'tracking_onset_s', 'tracking_first_contact_s']:
        queue[col] = np.nan
    queue.to_csv(ROOT / 'data' / 'edge_video_review_queue.csv', index=False)
    print(windows.to_string(index=False))
    print(f'Tracking queue: {len(queue)} recordings; 0 synchronized/validated recordings.')


if __name__ == '__main__':
    main()
