# V98: conserve15C magic and land eleven final-boss hits

Full-entry native dungeon10 now reaches14C with22HP/16MP, compared with
V97's20HP/8MP. Optional `--exit-room-axe-only` suppresses offensive spell
selection only in15C. The original8MP ice trigger in15B and healing remain
available. The real magic drop in15C raises8MP to16MP; two88 contacts cost
4HP. No environment4 terrain damage is recorded in this room.

The final boss still starts at90HP. Removing the final-only patient policy
and setting projectile window0 yields11 genuine4HP axe hits, leaving46HP.
The hero dies and strict route validation rejects the run with “Missing
genuine full-HP boss defeat”. This is progress in the optional test
controller, not a completed dungeon or a production decompilation change.
16MP remains below the24MP healing cost.

| Native full-entry variant | Frames | Boss hits | Boss HP remaining |
| --- | ---: | ---: | ---: |
| Axe-only15C, patient final boss, window8/distance32 |77758|0|90|
| Axe-only15C, standard boss, window8/distance32 |77517|6|66|
| Axe-only15C, standard boss, window0/distance32 |78099|11|46|
| Axe-only15C, standard boss, window8/distance48 |77564|6|66|
| Standard window8/distance32, also evade type118 |77517|6|66|

The patient run loses16HP to a type118 attack before any successful axe
hit. Optional `--final-projectile-awareness` includes active118 actors in
the existing retreat checks only against109. It reproduces the standard
six-hit outcome in this comparison and does not improve it. Existing
117 behavior for108 and all defaults remain unchanged. Both new options
are rejected outside dungeon10.

Reproduce the best eleven-hit run from the repository root:

```sh
python3 tools/test_md_emulator.py --core "$GAW_CORE" --nm "$GAW_NM" \
  --combat --dungeon 10 --potion-first --miniboss-spacing \
  --late-shield-first --late-ice --late-live-targets --late-retreat \
  --late-retreat-window 0 --caster-room-retreat --late-terrain-awareness \
  --late-contact-awareness --caster-projectile-awareness \
  --final-magic-reserve 8 --guard-melee-geometry --guard-axe-margin 4 \
  --timed-late-terrain --exit-room-melee-geometry --exit-room-axe-only \
  --boss-projectile-window 0 --boss-projectile-distance 32 \
  --frames 100000 --output md/build/dungeon10-v98
```

Completion is expected to fail. Every post-fixture action remains a joypad
input.69 tooling tests, Python compilation and diff checks pass. New tests
check15C-only spell suppression and109-only118 awareness. Report hashes,
controller options, genuine resource changes and final damage observations
are archived in dungeon_progress_v98.json. No production C, equipped-entry
fixture or V50 MD image changed. No new SMS or full-entry ending pass is
claimed; earlier equipped suffix proofs retain their own recorded options.
