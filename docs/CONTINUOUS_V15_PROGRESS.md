# V15 — independent presentation services, effects and item graphics

Separated ROM data and SMS VRAM/CRAM/register/dirty-flag services into video.c.
Native modules consume gaw_video.h, without depending on instruction execution.
A standalone protocol test links only video.c. Reset now also clears buffered
read/latch state, giving a reproducible cold video model.

Implemented $6DA6/$6D2C/$6D40 restoration in effects.c. Both C090 and C098
receive their correct state pointer. The previous bridge supplied IX=0, so its
indexed counter writes did not target the intended state. 8,192 differential
cases compare RAM outside Z80 stack space, all VRAM, CRAM, registers and timing.
Full-screen states 1/2 still execute original instructions.

Implemented item graphics dispatch $2AF4 in assets.c, including ROM transfers,
VRAM copies, zero fills and the four-plane RLE decoder. The host and MD item
resource hooks now load the actual shared video shadow at $7780. Map-entity
resources remain separate and unimplemented.

132 item/destination cases and four compressed resources run the original
Z80 decoder with the old $0327 accelerator disabled. This exposed two accelerator
omissions: the final stream destination stored at C031 and preservation of
VDP command bits when a destination crosses $8000. Both are corrected. RLE
command $80 also retains the original zero-counter/256-byte behavior.

Coverage remains 127/127 entity and 512/512 world registrations, with two
bridge call sites and seven empty MD hooks. This is not full-game equivalence
or a linked/play-tested Mega Drive ROM. Reference game data remains ignored.
