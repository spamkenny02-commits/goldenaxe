# Paid passage foreground palette correction v0175

ROM: versions/v0175-82520cf7/gaw-megadrive-v0175.bin
SHA-256: 82520cf76895fb015494576f4a71275838a3ea6cd7a7e24d9b6166b3d1efc929

v0174 faded all32 colors to black, but load_house_room restores only the
background half. Original state8 ->1DE2 falls through1DEB, which reloads all
16 foreground colors, then1DF6 applies armor/curse and flashing color31.
v0175 restores the same menu palette, armor colors and clock-flashing color
before revealing the destination. No rule, route, actor, save or other main
source changes. Without this restoration many actor/hero color indices remained
black after a paid exit, despite correct logical placement and damage.

Current checks:18528 original/native rule cases and20 PAL/NTSC controlled
passage integrations repeated. All15 fixed foreground colors16..30 now match
original CRAM after Genesis color conversion in all20 cases. Animated31 is
excluded from fixed-color equality. Prompt/confirmation, payment/cadence,
opening, menu roundtrip, routes/coordinates/visitation flag and static cells
continue to match. Destination enemies are cleared by pre-entry save-mask setup
for isolated passage checks; this does not prove matching combat behavior.
The archived v0174 minigame/fairy regressions are verified baseline evidence,
not claimed rerun for v0175. Their source plus main/actors is byte-identical.

Uncontrolled6D->96 read-only profile retains original enemies and RNG. Original
source is unpatched. Each region captures601 room/hero/clock/768-byte actor
states4200..4800. Native first state12 is not a true ready event because native
frontend runs synchronously. Initialized hero0 -> idle1 identifies first normal
simulation: source4335/native4303 NTSC and source4327/native4299 PAL. Native
resumes32/28 frames earlier, with different clocks and spawn coordinates.
Native later takes4 HP damage where source has not; this remains unresolved.

Read-only timing-core events measure original class0/resource work:
NTSC first032A4232 ->24ED4281:2791792 foreground T states,173919 IRQ T states.
PAL first032A4232 ->24ED4274:2828739 foreground T states,173919 IRQ T states.
1780..18E1 actor loading alone:1494853 foreground T states in both regions.
Background/map part differs because foreground wait/control work is included.
These measurements are evidence for a future loader cost model, not hardcoded
frame delays or a current timing-equivalence claim. Source RNG04E1/refresh stream
and complete global timing/progression/audio/video/hardware remain open.
