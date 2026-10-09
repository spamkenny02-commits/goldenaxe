# V59 — conserve magic with an optional potion-first probe

The emulator accepts `--potion-first` only with `--dungeon 10`. It spends
the ordinary equipped potion before healing magic at the existing24HP
threshold. The default heal policy and the retained V58 dungeon driver
are unchanged. Reports now identify potion-first and patient-boss options.
After the ordinary entrance fixture, only joypad inputs affect gameplay.

Native MD with potion-first opens the blocked $13E stair passage, reaches
$16A with46HP/24MP, then $18A with28HP/8MP and no curse. It dies there at
frame61782. This advances beyond V58's $13E timeout, but does not validate
the later south entry into $17B, the $17C switch or the final boss.

On original SMS, potion-first dies in $13D at frame25043, earlier than the
V58 controller's $18A death. Therefore this strategy remains opt-in; it is
not a general improvement to the retained SMS route.

A second trial applies axe geometry to minibosses as well. It regresses
SMS10 to $16A and is reverted. Native results for this combined trial are
recorded in dungeon_traversal_v59.json. No completed traversal is claimed.
Two initial launches used unchanged code and were cancelled immediately;
they are not validation evidence.

672 new differential cases verify magic drainers77/78/82 against their
unaccelerated original bank1 wrappers: four directions, eight contact
flags and magic0/1/7/8/9/16/255. Valid moving states are used (state6 for
77/78, state10 for82), with refresh entropy replayed. Every compared RAM
byte matches C, including subtract8 saturation and contact-flag clearing.
The combat suite passes8876cases; 48 tooling tests pass. Reference faults
now include the case, routine, slot and faulting PC to aid diagnosis.

There is no production C change or ROM rebuild. Private ROMs, binaries,
captures and RAM reports remain untracked. Full native9 and full10 remain
open. Next, preserve health through $18A while retaining enough magic to
open $13E; see the compact JSON report for exact failed-run evidence.
