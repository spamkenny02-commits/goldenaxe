# V89: cycling-pit avoidance and renewed native9 baseline

No full-entry native9 or dungeon10 pass. Production C, the native V50 ROM
and all fixtures remain unchanged. The optional terrain policy is a
joypad-only test-controller probe, limited to14A.

V88's instantaneous-descriptor penalty has no measured input benefit:
ordinary native10 dies15B at69869frames,18HP/0MP on arrival; reserved16MP
dies14A at63695frames,14HP/16MP on arrival. The new before/after resource
trace shows0→4 environment transitions on multiple4HP losses in14A. This
supports the terrain-damage diagnosis instead of attributing each loss
to the old related-entity pointer. Other losses remain ordinary contacts.

`gaw_world_animate_frame` cycles metatiles41→4E→4F→50→50→4F→4E→41→41.
The room's final safe-phase map contains41 at the suspicious damage sites.
V89 therefore penalizes all phases of those pit locations, and rejects
them as escape destinations. It preserves the original game's timing and
damage; it only changes controller navigation. Cache identity includes
whether the per-room penalty is enabled. Two tests verify an open pit is
avoided despite its currently safe descriptor, and another room is unchanged.

| Native full-entry probe | Result |
| --- | --- |
| V89 cycle avoidance, ordinary resources | Dies15B at81516frames;20HP/0MP on arrival versus18HP/0MP in V80 |
| V89 cycle avoidance, reserve16 | Completes14A, enters14B with2HP/16MP, dies there at68174frames |
| Native9, patient boss baseline | Reproduces49106frame death after13 of15 genuine hits; boss retains12HP |

Reserve16's13C losses are2HP from a type24 projectile,10HP from type81,
and4HP from type96. It enters14A with14HP. With cycle avoidance,14A costs
12HP (four2HP contacts and one4HP projectile hit), leaving2HP for14B.
That confirms better local terrain survival but leaves too little health
for the remaining rooms. Ordinary-resource trial's four enemy deaths in
15B still leave two enemies behind the partition;0MP remains insufficient
for that pursuit. Extra survival time is not completion.

61 Python tool tests, compilation and whitespace checks pass. The next
useful controller probes are avoiding the13C type81 body hit while retaining
spell resources, and anticipating type117 projectiles in the native9 boss
fight. Original-SMS suffix and arena proofs remain separate from full entry.

Private result SHA256 values:

- V88 terrain: `6f08a7616dd10688eb29abe006c045e9e9dbab9b9fd2bfdb7d72eb814a0fdea0`
- V88 terrain/reserve16: `4605753b6babbafa4c1ba1c2e81ff34dc857a1866aa666b9af46b05a94fc8086`
- V89 cycle: `adef85319582b1914b4abc4eaecb3b162afb9b93d2b98beed507756fd546cff7`
- V89 cycle/reserve16: `4e7538415e8c7111d66d9cc57f16d73f7046e4aeaba36475af992505f77411ef`
- Native9 baseline: `7181d11bbaea6e4de9166e19481246217ac1988a18012474fdd2f077a1e345ef`
