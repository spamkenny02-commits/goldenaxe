# V53 — checked collision geometry, traversal not finished

The controller now uses original hitbox geometry rather than a single radius
for boss swings. `combat_geometry.py` reads the 48 checked native boxes and
lists axe-2 poses from bank-12 metadata at $80B8. The private-ROM checker verifies
all 48 boxes and 16 weapon poses against the approved original revision.
It handles signed offsets and the asymmetric touching-endpoint rule of $2346.

2640 new original-Z80/native scans cover large-actor boxes 40..44 against axe
poses 14..25, both axes and 11 positive/negative offsets. Both hero-receiving and
boss-receiving scans match all compared RAM bytes. Total combat comparisons:
7692. 39 tooling tests pass. Production C/ROM remains V50, 484504 bytes / BB38.

Initial geometry boss-108 arena runs pass on original SMS and native MD with all
90 HP, 15 genuine hits and crystal collection. Both retain the potion and all
120 MP. Before reward HP is 50 on SMS and 26 on MD. Reports are summarized in
`combat_geometry_v53.json`. These are isolated equipped arenas, not traversal.

The saved inactive-source retreat guard now passes fresh boss-108 arenas on
both backends: 15 hits, crystal collection, no healing, 120 MP and one potion
remaining. SMS takes 1971 frames with 96 HP before reward; MD takes 4715
frames with 42 HP before reward. These results validate the current controller.

Full dungeon 9 still fails after 11 boss hits on SMS (24 boss HP remaining).
Two travel-geometry experiments were tested and reverted: applying geometry to
ordinary enemies and minibosses dies at cell $1BE before the boss; restricting
it to ordinary enemies reaches the boss but dies after only two hits. The
saved travel behavior is retained. Dungeon 10 remains at the V52 partial
circuit. No completed traversal or release claim is made.

Continue with safe melee placement during ordinary late-dungeon travel, which
currently consumes most healing before boss arrival. Retain the strict route,
full-HP boss, reward and survival validator. Private reports are ignored under
`md/build/v53_*`; original ROMs, binaries, captures and RAM dumps are not published.
