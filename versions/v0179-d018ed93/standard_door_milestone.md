# v0179 standard house and dungeon door transitions

The v0178 baseline entered and left standard rooms directly: both B0 requests
and the original exit fade / state8 / 1FA7 reveal sequence were absent.
The original ROM markers0B12,0B24,0ACE,1FB6,2002 establish18 exit-fade,
18 entry-fade and32 contour clock ticks in each controlled roundtrip.

Standard house and dungeon doors now use load_door_room: save the outside actor
mask before publishing the destination,fade out,request B0 for graphics-class
changes,load without enabling the display,request destination music,restore the
sprite palette and armor,then run the existing fade/contour reveal.
The logical loading clock uses the source single-tick rule. Paid loading also
keeps the display disabled until reveal;its observable phase includes exit fade.

Four house/dungeon PAL/NTSC roundtrips compare command order and source markers.
Native phases show nine color changes each direction and16 contours/32 ticks.
One PAL house exit samples19 fade-in frames versus18 in the source;the initial
reveal wait can consume a pending VBlank. Full physical loading durations still
differ. No arbitrary constant wait was added and exact timing is not claimed.

Regressions cover20 dungeon entrance/exit paths,16 gift contexts,12 actual
controller house exit/re-entry paths,20 paid-passage scenarios,24 paid-exit music
paths,3072 compiled paid-loader clock cases,and three save slots/cold Continue.
These tests use documented room/hero/progression fixtures. They do not establish
a full natural playthrough or all intermediate pixels/audio equality.

The paid-exit music assertion ends after destination hero initialization returns
to idle. Later combat can push the hero through another house door;its new B0
and house music requests are retained separately instead of being confused with
the tested initial exit. RNG and combat timing differences remain open.
