# V63 — pass18A and correct the17B stair approach

Dungeon10 remains incomplete. The new optional `--miniboss-spacing`
controller uses the existing left-side boss geometry against type123 in15E.
On native MD with `--potion-first`, the unchanged entrance fixture now
reaches18A with48HP/72MP, clears it, reaches18B, enters17B from the south,
activates17C, and returns to17B alive. At180000frames it stalls at[120,104]
with22HP. No RAM writes follow the ordinary equipped entrance fixture.

The live descriptor buffer shows a solid partition between this southern
floor and the upper stairs. Offline planning on that buffer can reach
[120,64] from the western entry, but not from the southern entry. The room
switch has correctly set bit2 (mask4), and the13C/17B callback positions
match the generated stair target. The missing dependency is a second entry
into17B from17A after visiting17C. The corrected route goes17C→17B→18B→18A
→17A→17B→13C. A fresh full-entry native run takes that actual staircase and
reaches13C with22HP, then dies there at58746frames. This validates the
switch circuit and staircase in production, not the remaining dungeon.

Routes1..9 are unchanged. The route test requires initial south entry,
17C activation ordering, the exact return circuit and final west entry.
50 tooling tests and Python compilation pass. Production C and ROM are
unchanged. The new controller probes are opt-in and remain work in progress.

Other probes are unsuccessful: C0EE speed equipment dies in15E (native)
or16A (SMS); close-range geometric shield combat dies in18A; extending it
to17D/13D regresses native to a16A stall and SMS to an18A death. These
methods/equipment flags are removed. A shield-first active-enemy controller
reaches17B on SMS but regresses native to16A. It is kept opt-in for the next
route experiment, together with optional fire against the dangerous type81
and96 actors in13C. Neither is a completed traversal claim.

Private ROMs, binaries, screenshots, state dumps and raw reports remain
untracked. The compact JSON records completed trials and report hashes.
The remaining proof must traverse13C onward, defeat full-HP boss109, then
show all nine crystals, complete the credits and return to title.
