# V93: native dungeon9 full-entry validation

The native Mega Drive dungeon9 route now passes the strict traversal validator:
55483 emulator frames,25 room visits,15 axe hits reducing the genuine90HP
boss to0,one death,crystal presentation/confirmation/collection,progress128,
and return to outside cell0EB in state0C with126HP. The route starts from the
existing equipped overworld fixture; it is not a new-game-to-ending proof.
Only joypad input drives gameplay after fixture preparation.

The successful controller uses `--patient-boss --boss-projectile-window 8
--boss-projectile-distance 32`. Retreat at48 pixels had interrupted too many
axe openings and left6 boss HP. At64 pixels it performs worse, with5 hits.
The new distance option defaults to the previous48; the dungeon regression
wrapper chooses the validated32-pixel policy for native9 only. The same
policy fails on SMS after8 hits, so SMS keeps its previously validated
controller. Timing/platform trajectories differ; this change does not alter
production combat behavior or the prepared equipment.

Reproduction from the repository root:

```sh
python3 tools/test_md_emulator.py --core "$GAW_CORE" --nm "$GAW_NM" \
  --combat --dungeon 9 --patient-boss --boss-projectile-window 8 \
  --boss-projectile-distance 32 --frames 100000 --output md/build/native9-v93
```

`GAW_CORE` names the Genesis Plus GX libretro core; `GAW_NM` names the m68k
toolchain's nm. This uses the existing V50 image at md/build/gaw_md.bin.
Run `validate(report, ROUTES[8])` from tools/test_md_dungeon_emulator.py to
check the full route, actual full-HP defeat and outside return together.

Rejected probes are recorded, with private-report hashes, in
dungeon_progress_v93.json. Projectile trajectory prediction degraded native9
to6 hits and was removed. Window6 gives13 hits;window10 repeats14 hits.
Optional14B drainer axe geometry failed to preserve8MP or sufficient HP in
dungeon10 and was removed. Reserve8 dies14A;reserve16 dies14B with16MP.
Full-entry dungeon10 remains incomplete. Its separate equipped13C suffix
still has prior successful native/SMS ending proofs.

62 tooling tests pass, including close-projectile retreat versus preserving
a safe axe opening. Production C,ROM image and fixture remain unchanged.
A second native9 run also passes the strict validator with the same55483
frames,15 hits and126HP outside. Both private reports have recorded hashes.
