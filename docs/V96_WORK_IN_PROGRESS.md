# V96: timed terrain navigation and second session checkpoint

Full-entry dungeon10 remains incomplete. The best observed full-entry probe
is still V95 guard melee with two hits on the real90HP final boss. The
final-only patient variant reaches that arena but dies without a boss hit.
SMS full entry with the guard policy dies18A at26171frames/16MP.

Strict rejection of all cycling-pit destinations clears every enemy in14A
and preserves46HP/16MP, but stalls at100000frames because the exit corridor
contains a cycling tile. A timed variant mirrors the actual $699C four-cell
group/phase sequence24 gameplay ticks ahead and permits stable41 tiles.
It continues past14A but its first full-entry run dies15C at75620frames.
The exit-room checked-melee/timed variant remains under observation; it is
not declared successful. The prediction horizon is a controller heuristic,
not a proof of zero terrain damage or game equivalence.

Forecast state is cached per room, animation group/phase and gameplay frame.
Navigation cache also observes animation phase. The original14A-only terrain
option is restored for reproducibility;15C penalties have their own option.
The shield-room experiment fails14A despite preserving more early HP and
has been removed. Old source and outcomes remain in the V95 checkpoint.

The SMS suffix exposed a controller-only IndexError when sampling the
north exit target Y8 beyond the1536-byte descriptor buffer. Terrain probes
now skip outside transition targets; a regression checks all four exits.
The fixed SMS suffix is being rerun. This was an experimental test-controller
failure, not a crash in production C.

67 tooling tests pass, including final-only patient behavior preserving123
mini-boss timing, dormant88 activation, pit timing and safe exit sampling.
Python compilation/diff checks pass. Production C, equipment fixture and
V50 image are unchanged. Every option remains experimental and disabled by
default. The report archive records hashes/policies for completed trials;
missing or still-running reports are not counted as passes. Continue the
remaining10 minutes of the requested30-minute session and save its results.
