# Cleared dungeon loading and room 17D (v0046)

ROM: 512 KiB; SHA256 3f77f21f (full digest in empty_dungeon_loading_audit.json); checksum 5835.

The longer DOWN hold from the v0045 investigation does not expose a missing obstacle in room 17D. On SMS the hero returns on frame 3610 PAL and reaches Y=160 on the final held-input frame 3700. MD returned on 3609, reached the edge one frame earlier, and started another scroll before the key was released. After the input ends, SMS remains in 17D and MD was entering 18D. The cause is the earlier room-loading resumption.

Original 24C5..24F2 still initializes a cleared room even with no remaining actor graphics: clears transient buffers, applies room history, initializes/filters actor records, prepares hero room state, installs the script and palette. The read-only research-core trace measures 52075 foreground Z80 T states in both regions for this room. IRQ work adds 4081 T NTSC / 4136 T PAL in this controlled sample.

The native loader previously skipped its entire foreground delay when world_actor_load_tstates was zero. It now retains that delay for dungeon rooms. This changes one conditional in the production source; it uses the existing approximate overhead model and has no room-ID special case or measured 17D delay constant.

## Current evidence

- Long-hold room 17D profiles in PAL/NTSC: 90 consecutive same-frame position/motion-counter/velocity/game-state comparisons per region match (3611..3700). Both finish in 17D, with equal floor cells at 3750. The unintended extra scroll is gone.
- Short crossing/return cases in 17D: resumption now equals SMS at 3611 NTSC and 3610 PAL. The PAL floor-cell mismatch seen in v0045 is gone at the tested checkpoint.
- Sixteen dungeon scroll cases preserve destination maps, hero positions, palettes, flags, masks and hidden old objects.
- Twelve final-particle cases and six crossing/return cases still pass the passage-state checks.
- Eighteen key-door controller cases still pass opening, crossing, returning and key inventory checks.
- Exterior movement/scroll sequences and eight deterministic enemy movements remain exact in both regions.

Ten runtime reports and two read-only source profiles are bound to the ROM in empty_dungeon_loading_audit.json. The three 8192-case isolated v0045 tests were not repeated: the audit verifies all other production source bytes and the exact one-conditional/comment change against the v0045 source snapshot, whose SHA is bound to its archived audit. Do not present those isolated executions as having run against v0046.

## Remaining timing limits

The overhead model is still approximate. The controlled 17D upward crossing remains five frames early NTSC / two frames early PAL. Some other dungeon loads are one frame early or late. In particular, PAL return to 151 is now one frame late, whereas v0045 was exact; the 1F0 left scroll also resumes one frame late. The generic empty-room delay fixes the omitted initialization work, but a precise IRQ/upload-phase model is still needed to remove those offsets without direction-specific patches.

This milestone does not prove full natural fights/routes, transition pixel accuracy or audio waveform fidelity. Next: source IRQ phase during loading, clear rewards and push-block passage scripts; full quests, bosses and ending remain incomplete.
