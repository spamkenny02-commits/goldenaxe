#ifndef GAW_ACTORS_H
#define GAW_ACTORS_H
#include <genesis.h>
extern u8 world_actor_state[0x300],world_loot_state[0x150],world_spell_state[0x30];
void tick_world_spell(const u8 *tilemap,u16 level);
extern u16 world_loot_style,world_loot_patterns_pending;
void tick_world_loot(u16 hero_state,u16 *gold,u16 *health,u16 max_health,u16 *magic,u16 max_magic,u16 *keys);
extern u16 world_actor_tiles,world_actor_count,world_object_tick_count;
extern u32 world_actor_load_tstates;
extern volatile u16 world_sms_sprite_overflow,world_sms_sprite_display_overflow,world_sms_sprite_prepared_overflow;
void load_world_actors(u16 room,u8 persistence,u8 *vram,u32 *native_patterns);
void load_world_actors_progression(u16 room,u8 persistence,u8 progression,u8 *vram,u32 *native_patterns);
void hide_world_objects(void);
u16 add_world_actor_sprites(u16 index,s16 minimum_y,s16 maximum_y);
u16 world_sprite_order_slot(u16 n,u16 phase);
u16 add_world_ordered_actor_sprites(u16 index,u16 slot);
void set_world_hero_attack(u16 x,u16 y,u16 direction,u16 box,u16 strength,u16 *flags);
void tick_world_actors(const u8 *tilemap,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 room);
s16 find_world_actor_contact(u16 hero_x,u16 hero_y,u16 collision_index,u16 frame);
bool reflect_world_actor(u16 slot,u16 direction,u16 shield_level);
bool reflect_world_projectile(u16 hero_x,u16 hero_y,u16 direction,u16 collision_index,u16 shield_level,u16 frame);
#endif
