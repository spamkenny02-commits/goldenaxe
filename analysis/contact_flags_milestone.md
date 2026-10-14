# Complete room-contact flags — v0050

ROM: versions/v0050-12d69d55/gaw-megadrive-v0050.bin (512 KiB, checksum 8A40).

The source 5B5A..5BA8 builds C0A6 from direction (bits 0/1), UP held (bit 2), eight-pixel alignment (bit 4), changed pre-movement C060 coordinate (bit 5), changed direction since the last aligned tick (bit 6), and inside-room bounds (bit 7). C062 and C064 only update on aligned ticks. Native room_script_flags previously supplied only bits 7/5/4 for shutters; it now supplies the complete value and caches direction as well. Pending room initialization uses the direction before the movement tail, mirroring the source room-init cache.

Isolated validation executes original 5B5A with a RET inserted before downstream door dispatch. 8192 cases cover 16 horizontal and 16 vertical boundary positions, four directions, UP held/released and four cache configurations, including pending room initialization. Each case executes twice, toggling horizontal alignment, direction and input. All flags and cached coordinate/direction bytes match. The pending-init fixture explicitly seeds source caches to the room-init values; it does not execute the room loader.

Normal controller-only exterior movement matches both cached fields on 371 frames in NTSC and 371 frames in PAL. Existing live shutter tests (ten scenarios per region) still close at 3414 and reopen at 3504 in occupied cases, with no closure in empty rooms. Bounded hero, scrolling and deterministic enemy timing checks pass in both regions.

validation/contact_flags_patch_audit.json binds seven current reports to the exact binary, verifies its header/checksum/aliases and source copies, and proves the production change is confined to contact flags and their cached direction. The archived v0049 audit supplies evidence for unchanged room-effect handlers; those old unit reports are not claimed as current-ROM reruns.

This is a prerequisite for the 47 contact calls inventoried in contact_script_reference.json: seven stationary-UP passage scripts, one cell mutation, three empty-cell triggers and 36 internal portals. Their effects are not enabled in this ROM. The full game, true push blocks, remaining quest scripts, bosses and ending remain incomplete. Loading IRQ phase, full visual equivalence and audio waveforms also remain unresolved.
