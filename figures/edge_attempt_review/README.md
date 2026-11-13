# EDGE pass-rush attempt review

## Scope and method

This is a visual diagnostic of the **six largest absolute differences** among the 52 players with two usable attempts in the filtered audit. Six primarily interior players were removed using [observed NFL alignments](../edge_pass_rush_cohort.md); these six disagreement examples remain the same. The sample was selected because of disagreement; it is not representative of all players. The plots compare each player's first two usable attempts chronologically. The original onset and gain rules are unchanged.

Each plot shows the full tracked path relative to recording start, the scored path segment in orange, and the speed curves with the half-second scoring windows shaded. Path axes retain source coordinates; the paths are not rotated or mirrored. The speed units have not been independently confirmed. The plots do not show the drill cue, body orientation, coaching instructions, or video.

| Player | First gain | Second gain | Visual observation |
| --- | ---: | ---: | --- |
| [Javontae Jean-Baptiste](57342.png) | -0.25 | 2.57 | First window captures a small initial rise followed by a decline; the larger acceleration begins after the window. Second window captures a sustained rise. |
| [Tyler Baron](58381.png) | -0.19 | 2.06 | First window is almost flat and ends below its starting speed; a larger rise follows. Second window captures the early rise. |
| [Jalyx Hunt](57215.png) | 2.41 | 0.59 | First window captures a rapid rise. In the second, speed stays near the threshold for much of the window and rises more sharply near and after its end. |
| [Landon Jackson](58277.png) | 0.23 | 1.86 | First window sits on a low-speed plateau, followed by a gradual increase; the second captures a more sustained initial increase. |
| [Kyle Kennard](58330.png) | 0.51 | 2.12 | First window includes a short rise and plateau, with a steeper rise later. Second window captures a steep rise. |
| [Bralen Trice](57195.png) | 2.21 | 1.03 | Both windows show increases; the second rise is shallower and includes a flattening before a later increase. This case is less clearly a complete mismatch of phases. |

Gains are changes in speed over 0.5 seconds, in the dataset's unverified native speed units. Negative values indicate that speed at the end of the window is lower than speed at its start; they do not necessarily represent an entire half-second of continuous deceleration.

## Interpretation and limitation

In the first five examples, one window captures a low-speed plateau or decrease while the paired attempt captures a stronger rise. The speed-threshold rule can therefore select visibly different portions of the recorded movement. In all six pairs, the full paths finish on opposite sides of the recording start along the y axis. This is an observation in this selected sample, not proof of a left/right drill protocol or the reason for the differences. Preparatory motion, different instructions or timing, true movement variation, and tracking artifacts remain possible; the tracking traces alone cannot distinguish them.

The review supports testing a more explicit phase definition, but it does not prove which phase is the football-relevant rush start. Any revised rule should be evaluated across all attempts and against independently reviewed examples, not tuned only to these six outliers. No NFL outcomes were used.

Reproduce the figures from the repository root after running the audit:

```bash
python exploratory_scripts/review_edge_attempts.py
```
