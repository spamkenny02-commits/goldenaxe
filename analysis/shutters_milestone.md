# Combat shutters — v0049

ROM: versions/v0049-3e6de542/gaw-megadrive-v0049.bin (512 KiB).

The source routines 5F2B and 5F0D close a room entrance after the hero steps inside an occupied room and reopen it when the last enemy death completes. C0A8/C0A9 describe shutter state and direction, not block pushing. Earlier milestone notes calling these push-block passages were incorrect. Actual block pushing remains unported.

13 shutter scripts and 27 additional completion handlers are translated to native 68000 C. The room-clear table now contains 96 handlers, covering 97 distinct rooms together with shutters. Source 5ECD can also award a key before reopening; existing reward flags prevent duplicate keys. The source asymmetric neighbour arithmetic when closing versus opening is preserved. Room 1BE retains its separate top-opening completion; room 174 has only the shutter portion ported.

Validation on this exact binary: 8192 isolated shutter cases, 8192 clear cases and 8192 key-door cases execute original Z80 scripts and compare native cells, maps, persistent flags, keys and relevant actor records. Shutter state/direction and repeated dispatch are checked. Controlled live scenarios cover top/left/right entrances, occupied and empty rooms and key rewards: ten cases each in PAL and NTSC. Occupied cases close at frame 3414 and reopen at 3504 on both systems. The final enemy death is injected; this does not establish natural combat or full dungeon progression.

Regression checks: 32 live reward cases, 12 room-clear cases, 18 key-door crossing/return cases, bounded movement timing sequences and two normal-menu save/cold-load cases. The audit binds 14 reports to the ROM hash and checks current production source copies used by isolated harnesses.

Evidence: validation/shutters_patch_audit.json and the immutable reports beside the archived ROM. All checks are targeted. True push blocks, contact prefixes such as 5C96, the 174 portal 5CFB, remaining quests, enemy AI, bosses and ending remain incomplete. Loading/redraw IRQ phase, sprite priority/flicker, scene pixels and audio waveforms still need comparison.
