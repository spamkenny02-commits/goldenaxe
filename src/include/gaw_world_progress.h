#ifndef GAW_WORLD_PROGRESS_H
#define GAW_WORLD_PROGRESS_H

#include <stdbool.h>
#include <stdint.h>

/* Persistent world-event bit used by original $193D/$1951. Returns true when
   the bit was already set before this call (the original returns NZ). */
bool gaw_world_progress_test_and_set(void);
bool gaw_world_progress_is_set(void);

/* $1A7C: apply the currently loaded C06F/C070 progression patch. */
void gaw_world_progress_apply_loaded_patch(void);

/* Explicit form useful for tests/tools: patch target is a $DC00 cell index. */
void gaw_world_progress_apply_patch(uint8_t patch_type, uint8_t target_cell);

/* $1976's event-record lookup portion. Loads C06E/C06F/C070 from the original
   bank-2 tables for RAM_WORLD_CELL_ID. Returns false when no record exists. */
bool gaw_world_progress_load_event_record(void);

/* $1BCD plus the persistent-bit reapplication performed by $1976. */
void gaw_world_progress_restore_for_current_cell(void);

/* Shared $1B0E/$35D4 map primitive: update $DC00, rebuild the corresponding
   two metatile rows in $D600, and enqueue the renderer's five-byte record. */
void gaw_world_set_tile(uint8_t cell, uint8_t tile_id);
void gaw_world_commit_metatile(uint8_t cell, uint8_t tile_id);

#endif
