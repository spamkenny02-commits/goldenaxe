# Native internal portals — v0054

ROM: versions/v0054-1dbffe65/gaw-megadrive-v0054.bin (512 KiB, checksum AB17).

All 36 original 5CFB portal call sites now have native coordinate/destination metadata and execute in compiled 68000 code. Generated stage metadata preserves whether each clear handler precedes or follows the portal. Contact and shutter prefixes execute first; a successful portal returns directly to the game-loop boundary, skipping the remaining room script.

The old room primary actor mask is saved before changing room id. Sound A6 is requested. The translated 1F78 wipe writes the original twenty interleaved sets of nametable positions, including the HUD, with each wait guaranteed to advance a video frame. Sprites and display are hidden after the wipe. Destination cells and persistent transformations load before arrival placement. The first 0C cell sets arrival; absent that marker, arrival defaults to 128,88. Fractional position bytes survive and the hero faces down.

The portal uses a dedicated dungeon loader that preserves the already-converted background. It reloads destination actor patterns, resets transient actor/loot/spell and animation state, applies the destination palette and restores the map/HUD while hidden. The generic house loader was too expensive because it reconverted and uploaded all 512 patterns; that intermediate approach is retained only in build-only v0052. v0053 is also an intermediate timing build. Use v0054 for this milestone.

Dynamic actor graphics T states plus shared NTSC/PAL preparation overhead determine loading duration. There is no per-room delay table. The regional overhead and the foreground phase following a preceding redraw remain approximations. They are not a proof of arbitrary IRQ/audio/load timing.

Current-ROM validation:

- 72 controller crossings: all 36 portals in NTSC and PAL. Fixtures seed a solved origin flag, a source-prepared map, hero position and frozen actor after a real dungeon entrance. The subsequent movement and portal execute in production cartridges.
- At each system first gameplay-ready frame following state 8, room id, complete hero arrival coordinates/direction, initial enemy count, 160 cell bytes, 1280 software map bytes, all 256 room flags, all 256 actor masks and 336 loot bytes match.
- All twenty visible wipe frames match the SMS erased-word positions, yielding 1440 frame comparisons. Ten stationary frames before controller movement verify the negative guard. Hidden VRAM preparation differs and is not included in the visible-wipe equality claim.
- Resume timing: 47 cases exact, 25 cases one frame late. No tested case resumes early. Full timing fidelity remains incomplete.
- Regression checks: 44 live contact scenarios, 20 combat-door scenarios, 18 key-door crossing/return cases, plus bounded hero/scroll/deterministic-enemy timing in both regions.

validation/portals_patch_audit.json binds ten current reports to this exact binary, checks aliases/header/checksum and generated script order, and proves the production delta from v0051 is confined to portal metadata, execution and dispatch. Earlier isolated contact/flag tests are evidence for unchanged functions, not new-ROM reruns. The original SMS transition reference remains preserved in analysis/portal-source-v0051.

A visual spot check confirms the characteristic wipe pattern on both systems. Full scene pixels, sprite priority/flicker and audio waveforms are not proven. Controlled fixtures do not establish natural puzzle completion, fights, travel, actor-history respawn or a complete dungeon route. Remaining contact/push-block scripts, AI, quests, bosses and ending still require porting. The overall game port remains incomplete.
