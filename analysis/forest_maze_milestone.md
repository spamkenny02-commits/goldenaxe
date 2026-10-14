# v0100 - native forest maze exit rule

The production port previously followed ordinary neighboring-room arithmetic at exterior room 0x77. Original Z80 21D7..2236 instead keeps most exits in that clearing and tracks transient byte C06C. The translated rule now runs exactly once at transition stage zero; preflight room checks remain pure. New games reset the transient byte, which is outside the original save payload.

The original sequence is east with hero Y >= 96, north, east with Y < 96, south, north. The first four correct exits return to 0x77 and advance progress; the fifth reaches 0x67. A wrong exit resets progress and loops to 0x77. West always reaches 0x76 and resets progress. Ordinary rooms and nonzero graphics classes use the normal destination and reset progress. Only the room low byte is tested, preserving the original high byte. Actor-mask storage remains in the existing transition entry path.

Validation executes unchanged original 21C5/21CB..2236 plus 18E2..190A on final success in a separate SMS fixture, against the compiled production helper in a separate MD harness. 480 cases cover four room words, three graphics classes, progress 0..4, all directions and Y=95/96. Six ordered cases additionally call native production begin_room_transition and step_room_transition stage zero with the normal room assets. All 486 resulting room/progress pairs match; the ordered sequence reaches the correct destination and resets on an ordinary return.

A second test uses the original unmodified SMS ROM and the production MD ROM with controlled RAM boundary positions, cleared enemies and temporary ground departure maps. Six consecutive exits execute through both actual game loops and full destination loaders in PAL and NTSC. Settled game state, room, progress, 160 metatiles and 1280 software tilemap bytes match after every exit. This is not a natural traversal of the world or frame-by-frame timing proof.

Ordinary PAL/NTSC movement, three scroll directions and eight deterministic enemy movements are rechecked, as are six inventory returns in the first two houses and exterior. The patch scope audit reconstructs the previous production main file after removing only the new helper, byte storage, stage-zero invocation and new-game reset.

Known global timing discrepancies, remaining story conditions, enemy AI/RNG, bosses, quests and ending are unfinished. No complete playthrough, full framebuffer, hardware or audio waveform equivalence is implied. Invalid maze progress values outside the reachable 0..4 input range are not compared.
