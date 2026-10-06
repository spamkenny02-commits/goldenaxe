# V31 — Complete player presentation actions in portable C

Implemented the work formerly omitted behind three platform hooks. The aligned
grid transition now rebuilds the actual SAT on each of its sixteen rotations.
The interior item performs its forty palette cycles, restores the interior
palette and transitions to it. Full healing advances HP one unit at a time with
the original HUD/sound barriers. Teleport saves entity presence and wipes the
old screen before clearing entities and preparing the destination.

Terrain transformation copies the source pattern and replaces the destination
through eight masked passes, preserving both barriers per pass and the original
entity-collapse/progression behavior. Corrected its sound request on a rejected
layer and its unchanged/already-open early return. The overworld map now builds
all 225 cells, aggregates terrain classes into color planes, preserves the
current map on either SRAM page, blinks position/acquired-map symbols and restores
scene/inventory/HUD. Everything writes the same portable SMS shadow as other UI.

48 complete raw-original comparisons cover success/refusal paths, both SRAM
pages, palette/marker phases, healing, destination layers and rotation terrain
variants. Each shared frame compares RAM C000-DF8F, all VRAM/CRAM/registers; final
SRAM and exact frame totals match. ASan/UBSan passes. The map required a larger
bounded reference instruction budget between synchronous barriers. The old
Phase 17 smoke fixture now supplies valid HUD capacities for these real effects.

The native MD image cross-links: 473,672 bytes, BSS 25,174, checksum A28D. Physical
controller boot/attack/Pause/inventory/movement continues to pass in Genesis
Plus GX. Two scroll hooks, wider integration, performance and hardware tests
remain; these comparisons do not establish a full-game playthrough.
