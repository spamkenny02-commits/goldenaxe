# V94: preserving magic through the late dungeon10 rooms

Full-entry dungeon10 is still incomplete. Native/SMS dungeon1–9 validation
from V93 remains the current completed scope. This step changes optional
joypad-controller policies only; production C, V50 image and fixture are
unchanged.

Two optional controls address actual contact geometry and projectiles:

- `--late-contact-awareness` adds navigation cost for overlapping enemy
  target rectangles in14A/14B, using the original hitbox table and a4-pixel
  margin. The cache includes those live rectangles, including activation
  changes. Existing terrain and room-crossing rules still apply.
- `--caster-projectile-awareness` evades active type113 shots within32
  pixels in14A when hero flash is at most8 ticks, after finishing a swing.

With the existing reserve8/late-ice/retreat8/cycling-pit policy, contact
awareness preserves18HP/8MP through the first14B circuit; the previous
drainer probe returned with16HP/0MP. Contact awareness alone still dies14A.
Adding projectile awareness clears14A and leaves8HP/8MP. A type78 contact
on the second14B visit at frame71392 then takes8→6HP and8→0MP, at hero
position[72,104] and enemy[60,116]. The run arrives15B with4HP/0MP and
dies there at73436frames. It cannot cast the real8MP ice passage trigger.
Reserve16 does not solve the health deficit and dies14A.

The curse trace distinguishes a different earlier event: a curse in18E at
11928frames, cured with the single antidote at15088 after the casters die.
The improved14A reserve8 attempt has no new curse there; its recorded
losses are three2HP type86 contacts and one4HP type113 hit. Therefore its
remaining health deficit must not be attributed to a14A curse.

A separate original-SMS equipped13C suffix with both new options passes
the strict segment validator:17929frames,23 hits against the full90HP final
boss, one death, nine crystals, credits and confirmed title return,128HP.
This starts with128HP/128MP and a potion; it is not a full-entry proof.
The same separate native suffix passes at42576frames with23 boss hits,
credits/title and104HP. The native suffix also does not prove full entry.

The important full-entry advance uses late-retreat window0 instead of8:
13C clears with30HP/16MP,14A clears with12HP/24MP, and15B is entered with
10HP/16MP. At frame71862 the real item5 ice cast costs8MP at[136,88], opens
the trigger passage, and the route enters16B with10HP/8MP. It dies there
at73112frames after6HP type69 contact,2HP type112 projectile damage and a
second type69 contact. A real magic drop brings the remaining MP to16,
still below the24MP healing cost. No new fixture or game-state write is
used. Disabling late retreat altogether fails earlier in14B at62214frames.
The next blocker is health/guard combat in16B, not activation of15B.

Reproduce the improved native full-entry probe from the repository root:

```sh
python3 tools/test_md_emulator.py --core "$GAW_CORE" --nm "$GAW_NM" \
  --combat --dungeon 10 --potion-first --miniboss-spacing \
  --late-shield-first --late-ice --late-live-targets --late-retreat \
  --late-retreat-window 0 --caster-room-retreat --late-terrain-awareness \
  --late-contact-awareness --caster-projectile-awareness \
  --final-magic-reserve 8 --frames 100000 --output md/build/dungeon10-v94
```

`GAW_CORE` is the Genesis Plus GX libretro core, `GAW_NM` the m68k nm.
The runner still asserts failure for incomplete routes and enforces no RAM
writes after preparation.63 tooling tests pass, including a navigation
case that avoids a large active body and restores the original path when
its hitbox deactivates. Compilation and diff checks pass. Compact outcomes
and private-report SHA256 values are in dungeon_progress_v94.json.
