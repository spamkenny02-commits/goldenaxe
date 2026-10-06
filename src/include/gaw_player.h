#ifndef GAW_PLAYER_H
#define GAW_PLAYER_H

#include <stdint.h>
#include "gaw_entity.h"

/* Native reconstruction of entity type 2 / Z80 $2DBE. */
int gaw_player_handler(GawEntity *player);
void gaw_player_update_sprite_meta(GawEntity *player);
/* Native $2C63: construct Arthur and preprocess the local terrain cache. */
void gaw_player_init_from_world(void);
void gaw_player_use_item(GawEntity *player); /* $2FA8 selected-item dispatch */
void gaw_player_show_world_map(void); /* $31E7 */
void gaw_player_grid_transition(GawEntity *player); /* $2F18 */

#endif
