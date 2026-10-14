# Room-clear passages and dungeon floor animation (v0045)

Production ROM: 512 KiB, SHA256 e45374abc29f9db490922d958357cf73ade7682c42e6e12036710987eca194f8, checksum 7F80.

## Source behavior and native implementation

Source 1839..1850 counts the eight primary room records into C0A2, using 80 when the room is empty on arrival. Source 4B99..4BA3 decrements the counter only when the final death-particle pose ends. Native world_actor_count already followed these rules; the new code connects it to room scripts after the actor tick.

Decoded B762 script entries identify 49 passage-clear handlers: 41 use 5D4C/5E57 to inspect and open all blocked edges; eight use 5EB1 to open one designated edge. Both consume the zero counter by setting 80. An empty room therefore does not fire this event automatically. Repeated dispatch does not spend a key or re-open passages.

Opening shares the existing 5C40/5C18/5BF0 implementation with key doors, after key validation/consumption. Flags 20/40/80 and reciprocal side flags persist in the existing room-save bytes. Each opening rebuilds the current map and retains the existing approximate redraw pause. This does not interpret Z80 instructions in the Mega Drive cartridge.

A live case in room 17D exposed missing animated floor cells. Original 6AA5..6AEA scans four cells at a time and advances through overlapping pairs of [41,4E,4F,50,50,4F,4E,41,41]. Its phase advances only when matching cells are found, or during an odd phase. This state machine is now native, updates the collision map and the visible two-by-two tile rectangle, and resets its scan/phase with room loading as 24C5 clears C090..C0AF.

## Evidence tied to this ROM

- 8192 source/native clear-dispatch configurations: all 512 rooms, four counter states and four initial passage flag sets. Actual original scripts run for the 49 selected rooms with contact prefixes disabled. Cells, maps, all 256 room flags, counter/latch and keys match. 118 configurations request an opening; zero consume a key. Dispatch is repeated twice.
- 8192 source/native floor-animation steps: all 16 phases and all 36 scan offsets are covered across real room cells. Cells, maps, scan, phase and flags match original 6AA5/6D54/2279.
- 8192 key-door regression configurations: 180 openings and 120 ordinary key consumptions remain exact.
- Twelve live final-particle cases (six each PAL/NTSC): all/top/left/right opening, a remaining counter of one after death, and an empty-on-arrival sentinel. All opening requests occur on frame 3404, when the particle disappears. Settled cells/maps/flags/count/keys match.
- Six live crossing-and-return cases: top 17D, left 11C and right 151 in each region. On the first resumed frame after crossing and returning, room/position/keys/flags/cells/map match. Persistent flags/count/keys still match at the end. These cases use the source FF hurt guard to isolate passages from enemy attacks.
- Eighteen controller key-door regressions pass (opening, crossing and return; ordinary/master/empty inventories).
- Existing exterior movement/scroll timing sequences and the eight controlled enemy movements still have zero differing state/counter frames in both regions.

The audit binds eleven reports, all source copies in the three native harnesses, the production aliases and checksum. Test harnesses and source ROM fixtures are separate cartridges, never included in production.

## Remaining differences and next work

The PAL 17D return resumes one frame early (destination loading two frames early); at frame 3750, floor cells 64/65/66 are 4F on SMS versus 4E on MD. This is recorded in room_clear_cross-pal_report.json and the audit. The isolated animation algorithm is exact; its absolute phase across loading is not. Top NTSC loading remains five frames early in this fixture. Other passage timing offsets also remain explicit in the reports.

An exploratory longer DOWN hold after returning to 17D continued into 18D on MD while the SMS remained in 17D. The final persistence fixture releases before that extra traversal. Reproduce and compare the later obstacle/interaction path separately; this milestone does not validate that route.

Next: resolve the loading/animation phase and the 17D prolonged movement discrepancy, then port clear rewards (5E75/5E9C/5ECD/5FB1) and push-block passage scripts. Dungeon animated tile bitmaps from 6A66..6AA5, bosses, quests and ending remain incomplete. Natural full fights, full routes, transition pixels and audio waveforms are not proven by these fixtures.
