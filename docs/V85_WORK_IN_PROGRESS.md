# V85: final-approach magic reservation checkpoint

This is an experimental controller checkpoint, not a completed dungeon10.
No production C, ROM or entrance fixture changes. The optional
`--final-magic-reserve {8,16}` retains MP for partition fire in15B, starting
in13C. It applies the budget to healing and ordinary offensive spells;
15B may spend it on unreachable targets. Default0 retains the V80 policy.

All full-entry native probes use potion-first, mini-boss spacing, late
shield-first, late ice, late live targets, window8 late retreat and
caster-room retreat. Each reaches13C with30HP/24MP/no potion.

| Probe | Outcome | Last resources entering14A |
| --- | --- | --- |
| V84 reserve8 | Dies14A at64270 frames; last8MP drained in14B |16HP/0MP|
| V84 reserve16 | Dies14A at62809 frames; no caster deaths there |14HP/16MP|
| V85 reserve16 | Dies14A at63695 frames; both casters killed |14HP/16MP|

V85 fixes a mismatch in the experimental reserve logic: caster retreat and
axe fallback now use the same available spell budget as fire casting.
Otherwise reserve16 could keep retreating for a fire spell it was forbidden
to cast. That correction improves caster kills but does not finish14A.
The cost of refusing the final24MP heal in13C remains a major health loss.
Reservation also cannot protect MP from a real drainer hit in14B.

Original SMS separate13C suffix, late ice/live targets/reserve16:
strict segment validator passes,19378frames,108HP,23 boss hits,1 boss
death, credits completed and title confirmed. It starts at an equipped
128HP/128MP checkpoint; it is not full-entry evidence. It has the same
measured ending outcome as the existing original-SMS suffix baseline.

59 Python tool tests and compilation pass. The experimental optional policy
is retained at this checkpoint for reproducibility; full-entry success
remains open. Future probes should address late health losses, and any
new policy must still pass the strict full-entry validator.

Private report SHA256 values:

- V84 reserve8: `7f5de68b5fae7a6fd9d972e0bf725ae0d0757ae49dce45b83bbffae3cf4ac0fb`
- V84 reserve16: `1cee6616459dc8b86a2bd5e82967a3ce7729efd9bf0578ac600f7ddc4118b1ad`
- V85 reserve16: `f81f195785acb9de9592c76c3194833dd57c6209ddb378e64b71cbfce4bebd07`
- SMS suffix: `cb7353e9db532547cc095b13976b78a8c91939a1fce59ab3c71e2373ed44c75d`

Raw reports, ROMs, screenshots and RAM dumps remain untracked.
