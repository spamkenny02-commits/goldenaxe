# V13 — durable source import and native reset

Imported 136 V12 source/tool/test/backend files in commit 796552f. The previous
remote tree held documentation and build configuration only. Original ROMs,
full-ROM include data and generated executables are ignored.

Added native $0404/$03C0 implementations and differential tests against original
execution. The save routine preserves reserved bytes and $9FFF, clears only
$8010-$9FFE when the signature is bad, and preserves C036 on that bad-signature
branch. The initial video routine issues eleven registers and clears sprite
palette entry $10, preserving VRAM. Tests check both SRAM pages and every
signature mismatch position, RAM, full SRAM and full video shadow state.

Made fresh checkout preparation reproducible with a reference-size/SHA-256
checked embed_rom.py and make prepare-rom. Negative extraction tests ensure a
wrong input cannot overwrite existing verified data. Added include/header build
dependencies so changing a generated input rebuilds tests.

Replaced hardcoded completed-type/world lists with a compiled-dispatcher probe.
The audit also lists bridge calls and ten empty MD hooks. --require-complete
currently exits 1; it must not be mistaken for full-game fidelity verification.
The ROM entity-table audit now checks the table against the input ROM and uses
the compiled probe for native registration counts.

Added push/PR syntax/tooling CI and explicit optional private-ROM behavioral
checks. Fixed the manual MD workflow to restore/verify its required ignored ROM
input before attempting a build. No ROM data is checked into Git.

The interactive scripts have not been converted in V13. Native reset, reliable
reproduction and honest completion reporting were the completed work here.
A console build remains unlinked/unplayed locally and the presentation hooks
remain unfinished; no claim of a finished portable game or MD ROM is made.
