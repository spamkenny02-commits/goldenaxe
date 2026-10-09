# V76: less damage in14A

Opt-in `--caster-room-retreat` avoids pursuing flashing type83/86 enemies
in14A when hero invulnerability has at most eight ticks remaining.
It changes controller inputs only; production game code is unchanged.

Native full-entry `v76_caster_retreat` uses V75's window8 policy plus this
option. It enters14A with40HP/0MP and exits with18HP, then reaches15A and15B
with18HP. V75 exits14A with10HP and enters15B with8HP. The new run dies
in15B at74421 frames, so full-entry completion remains unvalidated.
Private report SHA256:
`ca53395a140741425deea83ea99e99a64beddf29f23d71f0ce5a9134493ef866`.

An additional projectile-dodge experiment in15B dies sooner at71707
frames, still in15B with no boss hits. That experiment was removed.
A separate13C suffix with both experimental options reaches the final
boss with74HP/64MP but dies after15 hits at35516 frames. This is neither
a full-entry pass nor a successful ending test. Preserve the V75
window0 suffix policy for the previously validated ending scenario.

57 Python tool tests pass. The next blocker is15B: repeated type20
projectiles hit the hero at the same position in the full-entry trace.
