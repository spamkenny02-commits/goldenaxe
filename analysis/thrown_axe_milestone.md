# Native water context and thrown axe

The original activation table at 2EDB assigns slot 3 to 2FD2, not to 3042. The provisional v0085 slot-3 activation was incorrect and has been replaced. The source hero dispatcher 2DBE routes every selected item through 3042 when C041=3, and inhibits activation in context 5. This is terrain-dependent gameplay, not a new inventory slot.

The current translation classifies the original terrain contexts from 2544/2569 using the two low name-table bytes under the hero, with source test ordering and one/two-foot rules. Context 3 selects the original normal/fast water walk tables and eight bank-5 hero bitmap poses. The collision cache applies the C0EC bit-5 obstacle rule and C0F0 water-equipment bit-6/bit-7 rules.

The thrown object uses source type 5 in C330, activation 3042/308B, behavior 39CC..3A26, descriptor 3D8D and velocity table 3A1F. It has two animation frames, eight integration steps, a two-pixel upward origin offset, four-pixel directional velocity, no magic cost, and attack strength from the basic weapon level. It checks screen bounds but does not stop at ordinary terrain. The fixed-ROM descriptor is read separately from the bank-12 actor descriptors. Existing actor collision/damage processing receives this shared projectile record.

## Validation scope

The fixtures inject an all-water software name table, initial ownership/equipment, position, enemy clearing and a one-time clock seed into the original SMS and native ROM. The original ROM executable bytes remain unmodified. The tests compare 121 frames of the 48-byte auxiliary record, seven hero fields, terrain cells, context, hero position/velocity/counter; active projectile motifs and four actual hero VDP motifs are compared separately. Tests cover four directions, two basic weapon levels, PAL/NTSC, zero/insufficient magic, repeated button presses and bounded normal/fast movement.

These are controlled within-room comparisons. They do not prove natural water arrival/departure, equipment acquisition, mixed shoreline collisions, combat damage, the complete SAT or framebuffer, audio waveforms, save/re-entry, or a complete playthrough. Other terrain contexts are classified but their full movement/rendering behaviors remain incomplete.

A longer fast downward movement reaches a room boundary and exposes a loading-phase map mismatch: at frame 2833 the original still retains the departing mutable cells while native has loaded the destination. This failed exploratory run is retained in validation/thrown-axe-walk-fast.log. The bounded movement tests deliberately stay within the room; they do not resolve or validate this crossing.

The two fire PAL insufficient-magic state discrepancies documented in v0084 do not recur in the 22 current fire state/pattern cases. This does not establish global timing equality. Full fire images were not rerun for this binary, so the previous image differences remain unverified here. Full enemy/boss behavior, remaining abilities, quests and ending remain unfinished.

Final v0089 checks: 22 throws, 16 normal walks, 16 fast walks, 22 second-spell cases and 22 fire cases, plus ordinary movement/scroll/enemy timing in both regions. All compared states and patterns match within these stated scopes.
