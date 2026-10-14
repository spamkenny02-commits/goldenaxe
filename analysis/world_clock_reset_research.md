# Source dialogue clock reset - research, production v0063 unchanged

Static source evidence (ROM SHA-256
852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9):

- 07F1 loads HL=C02F; 07F4 writes zero to that clock byte.
- 07F6 calls 0BC6. Its only subcall is 0B95, whose 0B98 PUSH HL
  is paired with 0BC1 POP HL; alternate registers are also saved/restored.
  Thus waiting for VBlank preserves the caller's HL.
- 07F9 calls 0805. It tests bit 3 at (HL), chooses FC/FD for the
  dialogue continuation marker and tail-calls 03D9. 03D9 uses RST 28;
  0028..0030 writes the DE VDP address without modifying HL.
- 07FC tests newly pressed B/C bits from C021. At successful confirmation,
  0803 writes FF to (HL), which is still C02F. The fallthrough at 0805
  draws the FC continuation marker because bit 3 of FF is set.

Consequently the source inter-page dialogue confirmation routine does reset the
global interrupt clock to FF, not a temporary local blink counter.
The native wait_dialog_continue uses a local blink counter and leaves
world_clock_shift unchanged. enter_initial_room also sets that shift to
zero for a new game. These are concrete candidates for the observed
natural absolute animation-phase mismatch.

No native correction has been made from static evidence alone. Next profile
actual dialogue entry/confirmation and initial loading in PAL and NTSC,
including all clock writes and missed IRQs. Updating only the reset without
accounting for loader interrupt counts could worsen later timing. Recheck
NPC, merchant, new-game and Continue paths before releasing another ROM.

## Natural new-game measurements, PAL and NTSC

tools/profile_world_clock.py now observes the original source and unchanged
native v0063 through 2600 emulated frames, without RAM injections. Selected
instruction-entry hooks in a separate research emulator DLL record source
PC/clock/HL and native function entries; production cartridges are unchanged.
tools/audit_world_clock_profile.py binds the ROMs, research core, tool hashes
and two profiles in validation/world_clock_diagnostic.json.

| Event | SMS NTSC | MD NTSC | SMS PAL | MD PAL |
| --- | --- | --- | --- | --- |
| Inter-page wait entered | 1596 | 1597 | 1583 | 1568 |
| Inter-page confirmation input | 2200 | 2200 | 2200 | 2200 |
| Final wait entered | 2231 | 2218 | 2225 | 2215 |
| Final confirmation input | 2400 | 2400 | 2400 | 2400 |
| First room state 12, room 95 | 2454 | 2425 | 2448 | 2419 |

Source HL is C02F at the 0803 write in both regions; RAM clock is FF at
frame 2200 and zero at 2201. First-room activation is 29 frames early on MD
in both regions. At source first-room activation the clock is 199 NTSC / 205
PAL; these values include source IRQ suppression during rendering/loading.

Crucial distinction: the final wait is source 7447..7451, not 07EE. It
waits on C021 & 3F (directions or B/C), with no clock reset or continuation
marker update. The native port invokes wait_dialog_continue for both waits.
Applying the FF reset indiscriminately to both native calls would introduce
another error. Also, 07EE begins with an extra 0786 bitmap upload before
resetting the counter; the reset's exact video-frame position depends on
that upload. Keep intermediate-page and final confirmation separate.

Next implementation should distinguish these two waits, restore original
clock resets, account for source suppressed IRQs during bitmap work and
initial loading, and compare live rendered dialogue scrolling. The 29-frame
initial activation discrepancy is measured, not corrected in v0063.
