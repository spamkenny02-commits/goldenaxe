# V37 — bounded dirty traversal and whole-pattern resource expansion

The physical adapter now consumes an ascending iterator over conservative
dirty-pattern bounds. A newly dirty pattern updates the bounds once; repeated
writes to the same pending pattern add no traversal bookkeeping. Legacy scalar
consumption remains valid. Reset/all-dirty, sparse/reordered writes, mixed API
consumption, new writes after a partial drain, unchanged values and address
wrap have explicit tests. All 4,274 scalar/block comparisons still pass.

Synchronous IRQ resources expand one 24-byte three-plane pattern into a 32-byte
temporary and submit one block. Contiguous cartridge/RAM spans are used only
within mapped boundaries; crossing/wrap cases retain mapped byte reads. The
32-byte temporary is small IRQ scratch; V34's 6.3 KiB bitmap stays persistent.

All existing regular local regression/differential targets, ASan/UBSan and the
compiled native completion gate pass. Actual native ELF/vector/RAM/header
checks pass: ROM 476,460 bytes, BSS 31,518 at FF0000-FF7B1E, checksum BC9D.
Boot/name/new-game/audio/emulator checks pass too.

Idle gameplay advances 239 updates/300 physical frames (V36 148, V35 136).
The checked controller exit takes 508 gameplay physical frames (V36 721,
V35 947, original SMS 348), finishing cell 94, position [56,104], HP 24 and
state 0C. Its sampled C-state update count is 345 versus SMS 346; the final
settled result matches, not every physical/input endpoint phase.

Visual comparison found a separate fidelity gap: black ground replaces SMS
background palette color zero because MD tile zero pixels are transparent.
Shadow-byte comparisons alone cannot catch this. A correct zero-color plane
with palette selection, scrolling and sprite/background priority is next,
followed by eight-per-line sprite output clipping, cadence and broader
controller/save/combat/playthrough validation. This is not renderer signoff or
a completed hardware port. Private ROM, output images and captures stay ignored.
