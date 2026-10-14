# v0148 - fixed patrols61/62

Previous goal turn completed5E/77 with direct and actual-room evidence. This turn translates source5065/A6C7 for fixed horizontal61 and vertical62 patrols. Full faithful native game remains the objective.

State0 uses5878 fixed placement with count57 and falls through state2, selecting descriptor9855, period6/count2 and initial direction right61/down62. State2 falls through state4, which loads sourceA743 four-tick cardinal velocity table (two pixels per tick) and state6. State6 waits for counter0, then checks48F3 ground. Blocked ground resets byte20 and reverses heading. Otherwise byte20 increments modulo256 and reverses only at96, resetting to0. The next state is4. Constructor does not reset animation, phase or byte20 beyond the actual source writes. There are no random reads.

2463 isolated original/native cases compare all768 actor bytes: all four states, timers0/1/4, all headings, step counters0/1/94/95/96/255, map bytes00/01/20/80, boundary positions and every actual61/62 room slot. Ground collision masksA0, so map01 is passable; explicit20/80 cases ensure blocked branches are exercised. Velocity literals match sourceA744..A753 exactly.

Thirty-two PAL/NTSC controlled production segments compare2656 full-pool and hero-position frames. They cover150-frame walks in all four directions for each type, blocked-ground reversal,96-step reversal,255-to0 rollover without reversal and state2 axis reset. Surrounding world clocks align explicitly at controlled fixture initialization; full natural global clock/RNG is not claimed.

Actual127 (two61) and132 (three62) execute destination scripts, resource loading and fixed actors after controlled exterior doorway entry/departure relocation and normal right scroll. Four room/region cases compare1200 frames of all768 actor bytes plus actual hero/patrol sprite-table records/order, with no excluded actor fields and no post-load actor/hero/floor/clock writes. Each case samples24 sprite pattern tiles at three times (288 comparisons). Timelines align to first initialized patrol, not absolute room loading time. These rooms contain only deterministic patrol types, enabling whole-pool comparison without random alignment.

Audit confines production changes to61/62 AI/dispatch/post-AI collider publication/cached-renderer exclusions. main.c and older actor implementations remain byte-equivalent after removing those additions relative tov0147.1MiB aliases, checksum and SRAM header checked. Regression actual140 floor-trap whole-pool/SAT600 frames and natural New Game/Continue music89 PAL/NTSC pass.

Two reviewed room actor types5F/60 remain untranslated. Original RNG/global clock, absolute loading cadence/hidden animation phase, inherited loot-expiry presentation, complete natural fights/progression, quests/saves, remaining audio hooks, ending, complete framebuffer/audio equivalence, hardware and a natural complete playthrough remain incomplete or unverified. Port incomplete.
