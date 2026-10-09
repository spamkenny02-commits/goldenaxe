# V64 — final dungeon suffix and ending verified on both platforms

The separate equipped13C checkpoint now traverses13C→13B→14B→13B→13A→14A
→14B→15A→15B→16B→16C→15C→14C, defeats the genuine full90HP type109 boss,
shows all nine ending crystals, scrolls the complete credits and returns
to title. The native MD run finishes at56382frames with62HP; the original
SMS run finishes at19378frames with108HP. Both have23 genuine boss damage
events and exactly one boss death. Both pass the explicit suffix validator.
This is **not** a completed run from the overworld entrance. Initial HP/MP
are128 with one potion at13C; no work-RAM writes follow that fixture.

The first suffix attempt found another partition-dependent route error:
14B's switch changes tile64 to9, opening a western passage to the lower
stair pocket. Entering from the north cannot reach that pocket. After the
switch, the route must return14B→13B→13A→14A→14B, then take the stair to15A.
The fresh suffix runs verify this complete circuit on both machines.
Routes1..9 remain unchanged.

The next stall was in15C: three type82 actors retained their initial[0,0]
coordinates while waiting to spawn. Low-health drainer priority repeatedly
sent the controller toward that invalid position. The opt-in live-target
filter keeps dormant type88 actors with genuine fixed positions available,
and lets the hero approach them and trigger their real activation. With
this filter the room clears and the final door opens in the actual game.

New `--dungeon-start-room` checkpoints and `validate_segment` explicitly
separate suffix evidence from full entry. The default validator rejects any
room checkpoint, while both validators still require ordered room traversal,
a genuine full-HP boss defeat, all crystals, sufficient credit scroll and
confirmed title return. Ending initialization clears inventory, so the
summary no longer misreports the zero key count at title as20 spent keys.

The controller remains opt-in. Ice trials against type81 in13C pass the
room in some full-entry attempts but leave only2–6HP, followed by death in
14B. Shield-ice and title-delay experiments regress or stall and are removed.
The best previously verified prefix still depends on optional miniboss
spacing and the selected shield policy. Full-entry resource survival remains
open. A new opt-in death-animation wait is under full-entry testing to avoid
leaving before real HP/MP loot appears; it is not claimed to solve the run.

55 tooling tests pass, including the second west-entry dependency, checkpoint
rejection by full-entry validation, suffix walk/ending requirements, waiting
for corpse resolution, and skipping unplaced drainers. Python compilation
passes. Production C and ROM remain unchanged; unchanged production combat
suites are not rerun. Private ROMs, binaries, screenshots, RAM dumps and raw
reports remain untracked. The JSON records both successful suffix proofs,
full boss HP chains, report hashes and failed experiments.
