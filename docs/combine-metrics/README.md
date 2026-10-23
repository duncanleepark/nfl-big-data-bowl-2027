# Combine movement metrics: first exploratory version

Analyzed 3,532 attempts, 269 offensive players and 77 position/drill categories. Excluded 6 attempts for measurement quality or insufficient sustained movement. RB and FB are excluded. WR/TE players retain roster position even when their Combine drill category differs.

## Definitions

- Every drill label and position remains separate, including apparent naming variants. Records begin at the first of three consecutive raw-speed frames >=1 yard/s. The remaining recorded attempt is retained, including any exit; this is not an official start or a segmented drill.
- Coordinates and speed are converted from yards to meters (×0.9144). Path distance is the sum of Euclidean frame displacements, not the supplied dis field. Position/speed disagreement is retained as a quality diagnostic.
- Speed is smoothed with a centered five-frame moving average (~0.4-second span); boundaries use fewer samples. Signed acceleration is the difference of smoothed speed over elapsed time. This is retrospective analysis, not a real-time signal.
- Reference speed = 75th percentile across players' median smoothed attempt peaks within position and exact drill category/name. Each player contributes once. References based on fewer than 10 players are flagged, not treated as stable benchmarks. References are exploratory and must be fitted only on training players in future prediction models.
- High speed = interval midpoint smoothed speed >=85% of reference. An effort is a continuous run lasting strictly more than 0.5 s. Acceleration/deceleration efforts require signed acceleration >=3.5 or <=−3.5 m/s² for strictly more than 0.3 s. No gap bridging. Durations are sums of actual intervals, not frame counts.
- Total threshold time/distance includes all qualifying intervals, including short runs. Qualified-effort distance includes only runs meeting the duration rule. Missing threshold attainment is blank, not zero. An effort count of zero means no qualifying bout was detected.
- Player-level metrics are medians across attempts. Median effort counts may be fractional; these are summaries, not individual-attempt counts. Drill summaries then weight players equally. Available-player counts accompany turn summaries.
- Time to fixed speeds (3, 5, 7 m/s) begins at detected movement onset; it is not a timing from rest. Initial speed is retained for context.

## Provisional turn measures

The candidate is the largest angle >=35° between preceding and following half-second displacement vectors, each spanning >=0.6 yards. Center speed must be >=1 yard/s and there must be one second on each side. Entry/exit speeds are measured 0.5 s before/after. Recovery is the first point at/after the candidate with four consecutive frames (0.3 s span) back at entry speed. It may be zero; blank means not observed. Multiple turns, curved drills and drill exits can cause mismatched phases. These are candidate measurements requiring trajectory review, not verified cut-efficiency scores. No anatomical technique or blocking force is measured.

## Sensitivity checks

threshold_sensitivity.csv compares 80%, 85%, 90% speed references; 3.0, 3.5, 4.0 m/s² acceleration thresholds; and 3-frame versus 5-frame speed smoothing. Event counts need not change monotonically: changing a threshold can split one bout into several. Distance and threshold time should be monotonic and were checked.

## Files

- attempt_metrics.csv: measurements and source identifiers for every eligible attempt.
- player_drill_metrics.csv: player-level medians, with attempt counts.
- reference_speeds.csv: position-and-drill reference speeds and sample sizes.
- drill_summary.csv: player-weighted quartiles and available-player counts.
- threshold_sensitivity.csv: alternative thresholds and smoothing.
- excluded_attempts.csv: rejected records and reasons.

## Interpretation

These measures describe movement, not player rankings. More distance, acceleration or braking is not inherently better. Compare equivalent drill phases and entry speeds. Whole-attempt metrics can be affected by recording length and exits; linking them to NFL outcomes requires further segmentation and validation.
