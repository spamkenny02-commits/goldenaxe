#ifndef GAW_PLAYER_H
#define GAW_PLAYER_H

#include <stdint.h>
#include "gaw_entity.h"

/* Native reconstruction of entity type 2 / Z80 $2DBE. */
int gaw_player_handler(GawEntity *player);
void gaw_player_update_sprite_meta(GawEntity *player);
/* Native $2C63: construct Arthur and preprocess the local terrain cache. */
void gaw_player_init_from_world(void);

#endif
