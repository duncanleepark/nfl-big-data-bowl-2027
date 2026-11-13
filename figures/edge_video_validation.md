# Pilot video review: onset and first contact

Reviewed two visible Latu starts in the [official NFL 2024 workout clip](https://www.youtube.com/watch?v=-lMFW_3rpYw&t=49s).
Times below are playback seconds, rounded to milliseconds for reproducible
navigation, not claims of millisecond annotation accuracy. Screens were stepped
using the player's frame-step controls; observations are bracketed because the
review sampled frames and hand contact/body motion can be ambiguous.

| Shot | Last observed set stance | Launch visible by | Last observed pre-contact | Contact visible by | Possible launch-to-contact interval |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 50.383 | 50.483 | 50.583 | 50.683 | 0.10–0.30 s |
| B | 57.183 | 57.383 | 57.383 | 57.583 | 0.00–0.40 s |

The zero lower bound in B reflects coarse bracketing, not instantaneous contact.
Shot A shows the grounded hand lifting, forward launch, and hand contact with
the first upright bag. Shot B shows another launch and hand contact with a
bag that tilts. Both are identified by the Latu/DL42 overlay and visible player;
the shot-B lower third initially still names Kneeland before transitioning, so
the label at the beginning of the shot alone would misidentify the athlete.
No reliable start-cue frame was established from these images or commentary.

**A window ending 0.5 seconds after visible launch includes first bag contact
in both reviewed examples.** A 0.3-second window is also not certified as
pre-contact. This is evidence that this drill mixes launch and immediate hand
work, not proof that every existing tracking window contains contact.

## Tracking comparison and limits

Latu has two recorded tracking events:

- Attempt 1: `20240229100100_1709258501864_000`, negative-y path. Initial speed
  is 1.24, so the current rule excludes it as already above threshold. The
  speed subsequently falls below 1 before rising again around 0.9 seconds.
  That pattern demonstrates that an initial high speed need not mean the
  football rush start was truncated; video synchronization is needed to decide.
- Attempt 2: `20240229100100_1709259863030_000`, positive-y path. Current onset
  is 0.2 seconds after recording start and its scoring endpoint is 0.7 seconds.
  The clip's stance/launch markers cannot yet be placed onto that time axis.

The edited video has no supplied tracking event identifier or common clock.
Player identity and mirrored geometry alone do not establish a unique shot/event
assignment or clock offset. Shot order is not used as proof of attempt order.
Neither video shot is accepted as a synchronized tracking match. Therefore **zero
of the 116 cohort recordings currently has a validated pre-contact window**.
This pilot is one player/year and does not validate other years or the LB setup.

The current association remains an exploratory movement-feature comparison.
It should not be presented as a test of pure pre-contact get-off or cue reaction.
No new threshold, shorter window, or recovered attempt is promoted from these
two examples. The remaining blocker is footage with enough continuous course
coverage/shared landmarks to establish rep identity and video-to-tracking clock
alignment. More edited highlights without that evidence would not resolve it.

## Saved evidence and reproduction

`exploratory_scripts/edge_video_annotations.csv` records the observed playback
brackets, source, player, notes, and unverified matching/cue status. Run:

```bash
.venv/bin/python exploratory_scripts/edge_video_validation.py
```

This writes `data/edge_video_review_windows.csv`, comparing launch-aligned
0.3/0.5-second windows with the video brackets, and
`data/edge_video_review_queue.csv`, containing all 116 tracking recordings with
unknown synchronization/contact fields left blank. The main get-off script
also explicitly exports unverified phase and pre-contact validation flags.
These flags do not silently exclude all exploratory observations or change the
previous feature definition. The validator never treats a video-only bracket
as a validated tracking window.
