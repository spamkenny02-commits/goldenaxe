# V91: corrected15B mechanism and ongoing boss/13C probes

No full-entry dungeon10 or native9 completion yet. Controller-only changes;
production C, V50 ROM and checkpoint equipment remain unchanged.

**Correction to the V83–V89 working hypothesis:** the15B passage needs one
8MP ice cast at the real trigger, not fire kills of the stranded enemies.
The successful original-SMS13C suffix arrives15B with60HP/104MP, records
one item5 cast (104→96MP), no axe attacks or enemy damage there, then enters
16B with60HP/96MP. The native trigger/patch record is `{5B,48,67,08}`;
ice changes the trigger's0B tile through the original action4 table and
applies the loaded progression patch. The existing controller already
targets the trigger whenever8MP is available. The optional reserve help
now names this passage, and its unnecessary15B partition-fire exception
has been removed. Preserving at least8MP and enough HP is the real problem.

Completed full-entry probes:

| Probe | Result |
| --- | --- |
| Native10, reserve16/cycle avoidance/close invulnerable ice | Dies13C at58424frames,16MP remaining |
| Native9, patient boss/projectile window8 | Dies at49013frames after14 hits;6 boss HP remain |
| Native9, patient boss/projectile window16 | Dies at48951frames after13 hits;12 boss HP remain |

The8-tick projectile window improves one native9 measurement by a hit, but
does not complete the boss. Window16 does not improve it. Original-SMS
regressions for these boss variants are not yet claimed.

Further trials are in progress:13C axe/body geometry before hero flash
expires, with/without close ice; native9 projectile window4; and holding
attack reach while hero invulnerability outlasts boss flash. New options
are experimental and disabled by default.61 tooling tests and compilation
pass. Next examine14B drainer contact as well as13C health losses: a magic
reserve alone cannot prevent actual8MP drain.

Private completed-report SHA256 values:

- Close ice: `13ab1d78b6ca8a01c6f728edb256a3c68f9bc838308b888ac4a3c25490bbcef3`
- Native9 window8: `8aea6328acd3b86aeff101df666591600f2450345179862ac48c845de15e6c8c`
- Native9 window16: `b7cdd7858589f34e8a3b2e8cf2349fbc93ee818fe422156df3bfb8df9c97342a`
