# Fast normal-ground movement

Source 32ED..32F6 selects base 33DB or 3441 with C0EE. Native normal ground always selected the first table: eight pixels in five ticks. The 17-byte fast ground table now comes directly from original ROM 3441..3451, retaining four ticks and signed 8.8 velocities +/-512. This is a real 25 percent speed difference with running boots, not emulator host performance. Water selection remains unchanged; other terrain physics remain incomplete.

The v0094 intermediate binary passes 16 within-room cases (four directions, two equipment speeds, PAL/NTSC). Nine motion/state fields agree for 121 frames per case; four actual hero VDP tile pixel arrays agree for 118 frames. Twenty held-direction ticks yield 32 pixels normally and 40 with boots. Eight fast ground departure diagnostics now enter transitions on the same frame as SMS, removing four-frame delays in up/left/right and six frames down. Arrival animation/loading and NTSC upward timing still differ and are retained explicitly.

The intermediate implementation still needs the native speed mirror synchronized when boots are acquired or loaded; injected equipment speed alone does not prove natural acquisition. This is addressed in the following build. Current evidence is bounded to controlled rooms/positions/maps and does not establish all terrain, obstacle, combat or audio/framebuffer fidelity.


## v0095 acquisition and saved equipment

C0EE is source inventory byte 14 (running boots). Native stored that byte in hero_items, but a separate hero_attack_speed mirror stayed zero on grant and was explicitly reset to zero during Continue. Both paths now synchronize from inventory byte 14. The original item guard and source-layout save payload remain unchanged. The reward test compares the native speed mirror with source C0EE after acquisition; the cold-load test checks it against saved inventory in addition to the existing full 592-byte payload comparison. Full item acquisition and Continue testing are rerun against this final binary.

The v0094 intermediate ROM is preserved separately and should not be used for natural boot acquisition. This source change also makes the already-ported fast attack and water tables reachable from acquired/loaded boots; their full combat and natural shore routes remain to verify.


Final v0095 evidence: 16 ground movement cases, 32 water walking cases, seven passing directional water-pose cases with NTSC up explicitly unresolved, eight corrected ground approaches with remaining arrival differences listed, 44 item reward cases PAL/NTSC and ten 592-byte save/cold-load inventory cases. Ordinary movement/three scroll directions/eight deterministic enemy timing checks pass PAL/NTSC. Running-boots acquisition in room 0x157 and saved inventory byte 14 both activate the native speed mirror. All reports are bound to the final 1 MiB ROM by fast_ground_patch_audit.json. This remains a partial game port.
