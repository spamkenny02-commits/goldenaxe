# V88: resource tracing and damaging-terrain probe checkpoint

No full-entry dungeon10 success. This checkpoint preserves ongoing
controller experiments and read-only observations; production C, the
native ROM and the entrance fixture remain unchanged.

## Completed native full-entry probes

All use the V85 prefix flags. Optional changes and results:

| Probe | Optional change | Result |
| --- | --- | --- |
| V86 r24/m4 | Reserve24MP | Dies13C at56916frames, retains24MP |
| V86 r24/m2 | Reserve24MP,14A caster axe margin2 | Same death13C at56916frames; never tests14A |
| V86 r16/m2 | Reserve16MP,14A caster axe margin2 | Dies14A at63405frames, retains16MP |
| V87 collect | Wait for corpse resolution before leaving | Dies15E at31579frames,8MP remaining |
| V87 caster margin |14A caster axe margin2, no reserve | Same V80 death15B at69869frames;18HP/0MP on arrival |

Reserve24 prohibits both the final13C heal and ice; merely retaining all
magic loses that fight. Waiting for death loot changes earlier encounter
timing and regresses to the mini-boss. Caster margin2 alone does not change
the successful prefix or solve15B. These are failed probes, not production
improvements.

## New observations

Combat reports include `resource_changes`, sampled immediately before and
after each physical emulator frame. Each entry records HP, MP, selected
item, environment mode, player state and position. This observes costs,
healing and drain without relying on the later inventory selection in the
dungeon driver's MP events. It does not infer a cause or change inputs/RAM.
The initial boot's resource initialization and gradual potion increments
are included; consumers must filter by cell/item rather than treat every
HP increase as a healing spell.

V86 r16/m2 directly observes two18A item7 casts, both in environment0:
24→40HP and72→48MP atframe48144;24→40HP and48→24MP atframe49469.
V87 caster-margin observes the final13C heal in environment0 atframe57734:
18→34HP and24→0MP, selected item7, hero[112,64].

The production `$2DF7-$2EDA` player contact handler adds4 pending damage in
environment mode4 while hero flash is zero. That path does not refresh the
related-entity pointer. Therefore an old related slot can misidentify
terrain damage as a remote enemy hit. V87 has such suspicious4HP events in
14A with an alleged type86 far from Arthur. This motivates a probe, but the
old report lacks environment-at-damage evidence and does not prove each
event's cause.

V88 adds environment mode to player-hit records and reports empty prior
related slots as unknown rather than type0. The new optional
`--late-terrain-awareness` penalizes mode4 terrain samples in14A navigation;
ordinary and reserved16MP full-entry trials are in progress at this
checkpoint. No outcome is claimed. The optional `--caster-axe-margin` and
reserve24 remain experimental for reproducibility; default controller
decisions remain unchanged.

59 Python tool tests, compilation and whitespace checks pass.

Private report SHA256 values:

- V86 r24/m4: `71a34177b7c04c63c3efd2b3487a65b2e4aa0715a136446b5c5cb4f30dea55ec`
- V86 r24/m2: `1444fde4c577bf1aa2ad4e50b1b6ea84565bd92d24ef2ed54eaf5984628624fe`
- V86 r16/m2: `375d8ef8311bdff397c6e9979b4e0e1acdb93baed6b79f43e096875cf3fccb44`
- V87 collect: `c4c74444e60559aeaa9350ba75e45e42046cf08e7ffc8a08d07feadd89ea6dc0`
- V87 caster-margin: `d0ab8a6ab5f689934805f17684e6c7bef40eb6bd8e19ceabcbfaf781d544b7cc`
