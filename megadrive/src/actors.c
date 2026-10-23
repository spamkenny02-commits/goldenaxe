#include "actors.h"
extern void sound_effect(u16 command),sound_effect_main(u16 command);
extern const u8 actor_room_types[],actor_stats[],actor_pattern_index[];
extern const u8 actor_tile_counts[],actor_patterns[],actor_md_patterns[],actor_loading_costs[];
extern const u8 actor_descriptors[];
#include "actor_descriptor_words.inc"
extern const u8 actor_ground_modes[],actor_ground_sequence_index[],actor_ground_sequences[];
extern const u8 actor_spawn_terrain[];
extern const u8 actor_projectile_types[],actor_projectile_templates[];
extern const u8 actor_collision_boxes[],actor_shield_strength[];
u8 world_actor_state[0x300],world_loot_state[0x150],world_spell_state[0x30];
extern const u8 world_fire_velocity[],world_fire_origin[];
extern const u8 world_second_spell_velocity[];
extern const u8 world_axe_velocity[],world_axe_descriptors[],world_attack_strength[];
extern bool mutate_world_spell_terrain(u8 *entity,u16 level);
u16 world_loot_style,world_loot_patterns_pending;
extern const u8 actor_drop_exceptions[],actor_drop_choices[],actor_loot_patterns[];
static u16 actor_room_class;
static inline __attribute__((always_inline)) u16 descriptor_word(u16 address);
static const u8 *descriptor_frame(u16 address);
extern const u8 gem_descriptor_data[];
extern void tick_world_gem(u8 *entity),tick_world_boss_death(u8 *entity);
u16 world_actor_tiles,world_actor_count,world_object_tick_count;
u32 world_actor_load_tstates;
volatile u16 world_sms_sprite_overflow,world_sms_sprite_display_overflow,world_sms_sprite_prepared_overflow;

/* 21B6..21C0: clear every non-hero record's display/contact flags before
 * rebuilding the sprite table for an exterior scroll. Keep types and HP for
 * the persistence mask; room loading replaces the records after scrolling. */
void hide_world_objects(void)
{
    u16 slot;
    world_spell_state[3]=0;
    for(slot=0;slot<7;slot++) world_loot_state[slot*0x30+3]=0;
    for(slot=0;slot<16;slot++) world_actor_state[slot*0x30+3]=0;
}

/* Hero collision scan 2346 and successful shield branch 2E18..2E9D.
 * Hit order is room actors then transient records. Unblocked damage, hurt
 * timers, water/attack states and the shield sound remain to integrate. */
/* 2346: first overlapping actor; collision precedes hero behavior. */
s16 find_world_actor_contact(u16 hero_x,u16 hero_y,u16 collision_index,u16 frame)
{
    const u8 *box=actor_collision_boxes+((collision_index*4)&255);
    u16 left,right,top,bottom,slot;
    if((frame&1) || !collision_index) return -1;
    left=(hero_x+box[0])&255;right=(left+box[1])&255;
    top=(hero_y+box[2])&255;bottom=(top+box[3])&255;
    for(slot=0;slot<23;slot++)
    {
        u8 *entity=slot<7?world_loot_state+slot*0x30:world_actor_state+(slot-7)*0x30;
        u16 x,y,end;
        if(!entity[0] || entity[6] || !(entity[3]&2) || !entity[0x1c]) continue;
        box=actor_collision_boxes+((entity[0x1c]*4)&255);
        x=entity[0x13]+box[0];if(x<256) continue;x&=255;
        if(x>=right) continue;
        end=x+box[1];if(end>=256 || end<left) continue;
        y=entity[0x11]+box[2];if(y<256) continue;y&=255;
        if(y>=bottom) continue;
        end=y+box[3];if(end>=256 || end<top) continue;
        entity[3]|=4;
        return slot<7?-(s16)slot-2:(s16)slot-7;
    }
    return -1;
}

/* 2E08: successful projectile block, resolved after hero behavior. */
bool reflect_world_actor(u16 slot,u16 direction,u16 shield_level)
{
    u8 *entity=world_actor_state+slot*0x30;
    u16 axis,velocity;
    if(!(entity[3]&16) || shield_level>3 || actor_shield_strength[shield_level]<entity[0x19]) return FALSE;
    axis=direction<2?0x14:0x16;
    velocity=entity[axis]|((u16)entity[axis+1]<<8);
    if(!velocity || ((direction==0 || direction==2)?(velocity&0x8000):!(velocity&0x8000))) return FALSE;
    velocity=-velocity;entity[axis]=velocity;entity[axis+1]=velocity>>8;
    entity[4]=10;entity[3]&=253;
    sound_effect_main(0x98); /* 2E98: successful shield reflection. */
    return TRUE;
}

bool reflect_world_projectile(u16 hero_x,u16 hero_y,u16 direction,u16 collision_index,u16 shield_level,u16 frame)
{
    s16 slot=find_world_actor_contact(hero_x,hero_y,collision_index,frame);
    return slot>=0?reflect_world_actor(slot,direction,shield_level):FALSE;
}

/* 1780..18E2: eight room objects, persistence mask and shared graphics.
 * Source RLE/palette conversion is performed by extract_actors.py. The game
 * initializes/allocates the original entity records here in native 68000 C.
 * 1805..1838 applies the dungeon progression byte before allocating graphics. */
void load_world_actors_progression(u16 room,u8 persistence,u8 progression,u8 *vram,u32 *native_patterns)
{
    u16 slot;u8 flags=0;
    memset(world_spell_state,0,sizeof(world_spell_state));memset(world_actor_state,0,sizeof(world_actor_state));memset(world_loot_state,0,sizeof(world_loot_state));
    actor_room_class=room>>8;world_loot_style=0;world_loot_patterns_pending=0;
    world_actor_count=0;world_actor_tiles=0;world_actor_load_tstates=0;
    for(slot=0;slot<8;slot++)
    {
        u8 *entity=world_actor_state+slot*0x30;
        u16 type=actor_room_types[room*8+slot];
        if(!(persistence&(0x80>>slot))) continue;
        entity[0]=type;
        if(type<0x20) continue;
        memcpy(entity+0x18,actor_stats+(type-0x20)*4,3);
        entity[3]=actor_stats[(type-0x20)*4+3];
        flags|=entity[3];
    }
    /* 1805..1838: surviving boss flags gate replacement of the first eight
     * records. Positive progress leaves object 0F; bit 7 removes it too. */
    if((flags&0x40) && progression)
    {
        memset(world_actor_state,0,0x180);
        if(!(progression&0x80)) world_actor_state[0]=0x0f;
    }
    for(slot=0;slot<8;slot++)
    {
        u8 *entity=world_actor_state+slot*0x30;
        u16 type=entity[0],previous;
        if(type) world_actor_count++;
        if(type<0x20) continue;
        for(previous=0;previous<slot;previous++)
            if(world_actor_state[previous*0x30]==type) break;
        if(previous<slot) entity[2]=world_actor_state[previous*0x30+2];
        else
        {
            const u8 *position=actor_pattern_index+type*4;
            u32 offset=((u32)position[0]<<24)|((u32)position[1]<<16)|((u16)position[2]<<8)|position[3];
            u16 count=actor_tile_counts[type];
            const u8 *cost=actor_loading_costs+type*4;
            world_actor_load_tstates+=((u32)cost[0]<<24)|((u32)cost[1]<<16)|((u16)cost[2]<<8)|cost[3];
            entity[2]=world_actor_tiles;
            memcpy(vram+0x2000+world_actor_tiles*32,actor_patterns+offset,count*32);
            memcpy(native_patterns+(256+world_actor_tiles)*8,actor_md_patterns+offset,count*32);
            world_actor_tiles+=count;
        }
    }
    if(!world_actor_count) world_actor_count=0x80;
}

/* Compatibility entry for callers without dungeon progression. */
void load_world_actors(u16 room,u8 persistence,u8 *vram,u32 *native_patterns)
{
    load_world_actors_progression(room,persistence,0,vram,native_patterns);
}

/* 48F3: limits and ground flags at the leading edge of an 8-pixel step. */
static bool ground_blocked(const u8 *entity,const u8 *tilemap,u16 direction)
{
    static const s8 dx[4]={-8,-8,-16,8},dy[4]={-16,0,-8,-8};
    u16 x=entity[0x13],y=entity[0x11],offset,first,second;
    if((direction==0 && y<25) || (direction==1 && y>=152) ||
       (direction==2 && x<17) || (direction==3 && x>=232)) return TRUE;
    offset=(((y+dy[direction])&248)*8)+(((x+dx[direction])&248)>>2);
    first=tilemap[offset+1];second=direction<2?tilemap[offset+3]:first;
    if(entity[0]==0x34) return (first&second&0xc0)!=0xc0;
    return ((first|second)&0xa0)!=0;
}

/* 8760..87C3: emerging enemies select/continue direction, then move.
 * SGDK random is temporary: the Z80 refresh-register stream is not yet
 * reproduced. 4C7E damage/cloning remains pending. The VBlank clock schedules
 * one slot per eight frames; the original C02F phase is not yet reproduced. */
static bool spawn_world_actor(u8 *entity,const u8 *cells,u16 hero_x,u16 hero_y,
                              u16 frame,u16 slot,u16 terrain_start,u16 terrain_count)
{
        u16 cell,n; s16 distance;
        if((frame&7)!=(slot&7)) return FALSE;
        cell=(random()&127)+16;
        if(((cell-1)&15)>=14) return FALSE;
        for(n=0;n<terrain_count;n++) if(cells[cell]==actor_spawn_terrain[terrain_start+n]) break;
        if(n==terrain_count) return FALSE;
        entity[0x13]=((cell&15)<<4)+8;
        distance=(s16)hero_x-entity[0x13];if(distance<0) distance=-distance;
        if(distance<16) return FALSE;
        entity[0x11]=(cell&240)+16;
        distance=(s16)hero_y-entity[0x11];if(distance<0) distance=-distance;
        if(distance<16) return FALSE;
        entity[10]=random()&3;entity[3]|=3;
        return TRUE;
}
static void ground_behavior(u8 *entity,const u8 *tilemap,const u8 *cells,
                            u16 hero_x,u16 hero_y,u16 frame,u16 slot)
{
    u16 state=entity[1],type=entity[0]-0x26;
    if(state==0)
    {
        if(!spawn_world_actor(entity,cells,hero_x,hero_y,frame,slot,0,4)) return;
        entity[8]=0xfa;entity[9]=0x84;entity[13]=16;entity[12]=4;entity[1]=2;
        return;
    }
    if(state==2)
    {
        if(entity[11]!=3) return;
        entity[11]=0;entity[8]=0x24;entity[9]=0x86;entity[12]=2;
        entity[0x20]=actor_ground_modes[type];entity[1]=state=4;
    }
    if(state==4)
    {
        u16 direction=random()&3;
        if(ground_blocked(entity,tilemap,direction)) return;
        entity[10]=direction;state=6;
    }
    if(state==6)
    {
        const u8 *sequence=actor_ground_sequences+actor_ground_sequence_index[type];
        entity[4]=sequence[0];
        memcpy(entity+0x14,sequence+1+entity[10]*4,4);
        entity[13]=entity[4];entity[1]=8;return;
    }
    if(state==8 && !entity[4])
    {
        if(entity[0x20]==1) { entity[0x20]=0;entity[1]=4; }
        else if(ground_blocked(entity,tilemap,entity[10]) || !(random()&15)) entity[1]=4;
        else entity[1]=6;
    }
}

/* 4965: direct allocation intentionally bypasses the 495E overflow guard. */
static u8 *create_projectile_type(const u8 *parent,u16 type)
{
    u16 slot;
    for(slot=8;slot<16;slot++)
    {
        u8 *entity=world_actor_state+slot*0x30;
        if(entity[0]) continue;
        entity[0]=type;
        entity[2]=parent[2];entity[0x13]=parent[0x13];entity[0x11]=parent[0x11];
        entity[10]=parent[10];return entity;
    }
    return NULL;
}

extern const u8 first_boss_movement[],first_boss_aimed[],first_boss_fan[];
/* 57F8 with BC=0004: preserve partial X/Y writes on rejected placements. */
static bool burst_boss_place(u8 *e,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot,const u8 *roll)
{
    u16 cell,n; s16 distance;
    if((frame&7)!=(slot&7)) return FALSE;
    cell=((roll?roll[0]:random())&127)+16;
    if(((cell-1)&15)>=14) return FALSE;
    for(n=0;n<4;n++) if(cells[cell]==actor_spawn_terrain[n]) break;
    if(n==4) return FALSE;
    e[0x13]=((cell&15)<<4)+8;distance=(s16)hero_x-e[0x13];if(distance<0) distance=-distance;
    if(distance<16) return FALSE;
    e[0x11]=(cell&240)+16;distance=(s16)hero_y-e[0x11];if(distance<0) distance=-distance;
    if(distance<16) return FALSE;
    e[10]=(roll?roll[1]:random())&3;e[3]|=3;return TRUE;
}
/* 54D3 -> AB40: appearance, eight shots, disappearance and relocation.
 * The duplicated write to animation period in AB7F leaves count unchanged. */
void burst_boss_behavior(u8 *e,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot,const u8 *roll)
{
    u16 state=e[1],n;u8 *last=NULL;
    if(!state)
    {
        e[0x13]=128;e[0x11]=56;e[5]=32;e[4]=56;e[11]=0;e[8]=0x5a;e[9]=0x9d;
        e[13]=8;e[12]=7;e[1]=2;return;
    }
    if(state==2)
    { if(e[11]==6) { e[13]=0;e[11]=6;e[1]=4; }return; }
    if(state==4) { e[1]=6;return; }
    if(state==6)
    {
        if(!e[4]) { e[11]=0;e[13]=e[12]=2;e[8]=0xda;e[9]=0x9d;e[4]=52;e[1]=8; }
        return;
    }
    if(state==8)
    {
        if(e[4]) return;
        for(n=8;n;n--)
        {
            u8 *shot=create_projectile_type(e,0x74);if(shot) last=shot;
            /* Original writes through last IY after allocation failure. */
            if(last) last[10]=n-1;
        }
        e[4]=32;e[1]=10;return;
    }
    if(state==10)
    {
        if(!e[4]) { e[0x20]=0;e[11]=0;e[8]=0xc4;e[9]=0x9d;e[13]=8;e[12]=7;e[1]=12; }
        return;
    }
    if(state==12)
    { if(e[11]==6) { e[3]&=252;e[4]=64;e[1]=14; }return; }
    if(state==14 && !e[4])
    {
        e[11]=0;e[8]=0x5a;e[9]=0x9d;
        if(burst_boss_place(e,cells,hero_x,hero_y,frame,slot,roll)) e[1]=2;
    }
}
extern const u8 composite_boss_positions[];
/* A9AE: overwrite only type/state/wait of the five delayed apparitions. */
static void composite_boss_spawn(u8 *e,u8 formation)
{
    u16 n;
    for(n=1;n<6;n++)
    { u8 *p=world_actor_state+n*48;p[0]=0x67;p[1]=16;p[4]=(6-n)*16; }
    if(!e[0x20]) { formation&=3;e[0x21]=formation==3?2:formation; }
}
/* 5193 -> A972, with four explicit refresh-byte inputs for branch comparisons.
 * Type67 uses the primary record and five coordinated apparitions. */
void composite_boss_behavior(u8 *e,u16 slot,const u8 *roll)
{
    u16 state=e[1],n;const u8 *position;
    switch(state)
    {
        case 0:
            e[11]=0;e[0x21]=0;e[8]=0x62;e[9]=0x9a;e[0x20]=1;
            e[0x13]=128;e[0x11]=88;e[4]=112;e[1]=2;
            composite_boss_spawn(e,roll[0]);break;
        case 2:
            if(e[4]) break;
            e[5]=40;e[3]|=1;e[1]=4;e[13]=16;e[12]=2;e[4]=39;e[0x20]=0;break;
        case 4:
            if(e[4]) break;
            e[11]=0;e[8]=0x98;e[9]=0x9a;e[4]=39;e[1]=6;break;
        case 6:
            if(e[4]) break;
            e[3]&=254;n=roll[1]&7;if(n>=5) n-=3;
            position=composite_boss_positions+e[0x21]*10+n*2;
            e[0x13]=position[0];e[0x11]=position[1];e[3]|=2;e[1]=8;break;
        case 8:break;
        case 10:
            e[11]=0;e[8]=0xa4;e[9]=0x9a;e[13]=8;e[12]=2;e[4]=10;e[3]&=252;e[1]=12;break;
        case 12:
            if(!e[4]) e[1]=14;break;
        case 14:
            e[4]=39;e[1]=4;composite_boss_spawn(e,roll[0]);break;
        case 16:
            if(e[4]) break;
            e[11]=0;e[8]=0x34;e[9]=0x9b;e[13]=8;e[12]=2;e[3]|=1;e[3]&=253;
            e[5]=e[4]=48;position=composite_boss_positions+world_actor_state[0x21]*10+(slot-1)*2;
            e[0x13]=position[0];e[0x11]=position[1];e[1]=18;break;
        case 18:
            if(e[4]) break;
            e[3]|=2;e[1]=20;e[4]=(roll[2]&15)+113;
            /* AAD1 falls through the parent-death test in AADA. */
        case 20:
            if(world_actor_state[0]==7 || world_actor_state[1]==14)
            { e[1]=22;e[5]=e[4]=48;e[3]&=253; }
            else if(!e[4])
            {
                if((roll[3]&15)<4) create_projectile_type(e,0x15);
                e[4]=(roll[2]&15)+113;
            }
            break;
        case 22:
            if(!e[4]) memset(e,0,48);break;
    }
    /* Fixed wrapper 5199 executes before generic 2803 damage processing. */
    if(e[0x1d] && e[0x18]>e[0x1d]) { e[3]|=1;e[1]=10; }
}
/* 506B -> bank2 A754. Random bytes are explicit inputs for source comparison.
 * Production supplies provisional random() values, not the SMS refresh stream. */
void first_boss_behavior(u8 *e,u8 gate,u8 choice)
{
    u16 state=e[1],n;u8 *last=NULL;
    if(!state)
    {
        e[3]|=3;e[8]=0x13;e[9]=0x99;e[10]=1;e[13]=40;e[12]=2;
        e[0x20]=5;e[0x21]=0;e[0x13]=128;e[0x11]=40;e[5]=64;e[4]=64;e[1]=2;return;
    }
    if(state==2 && e[4]) return;
    if(state==2 || state==4)
    {
        e[4]=first_boss_movement[0];memcpy(e+0x14,first_boss_movement+1+e[10]*4,4);
        e[1]=6;return;
    }
    if(e[4]) return;
    if(state==6)
    {
        e[1]=4;
        if(!e[10]) { --e[0x21];++e[0x20];if(e[0x20]==5) e[10]=1; }
        else { --e[0x20];++e[0x21];if(e[0x21]==5) e[10]=0; }
        if((gate&15)>=4) return;
        e[1]=8;e[8]=0x7f;e[9]=0x99;
        if(e[0]==0x64 && (choice&15)<13) { e[1]=10;e[8]=0xb9; }
        e[0x14]=e[0x15]=e[13]=e[12]=e[11]=0;e[4]=32;return;
    }
    if(state!=8 && state!=10) return;
    for(n=state==8?3:5;n;n--)
    {
        u8 *shot=create_projectile_type(e,state==8?0x72:0x73);
        if(shot) last=shot;
        /* A82D writes through the last IY even after a later allocation fails.
         * An already-full pool's inherited IY side effect remains unmodeled. */
        if(state==10 && last) last[10]=n-1;
    }
    e[8]=0x13;e[9]=0x99;e[13]=40;e[12]=2;e[1]=4;
}

static u8 *create_guarded_projectile_type(const u8 *parent,u16 type)
{
    if(world_sms_sprite_overflow) return NULL;
    return create_projectile_type(parent,type);
}

static void create_projectile(const u8 *parent)
{
    create_guarded_projectile_type(parent,actor_projectile_types[parent[0]-0x20]);
}
extern const u8 actor_mobile_sequences[];
extern const u8 actor_fixed_placement_tables[];
/* 5878/589C/58AC: first room match, reversed pointer index, then primary slot. */
static bool place_fixed_actor(u8 *e,u16 room,u16 slot,u16 count)
{
    const u8 *tables=actor_fixed_placement_tables;
    u16 layer=room>>8,n,remaining,list=layer?0x5d:0;
    u16 pointers=layer?0x96:11,offset,address;
    if(layer>1) return FALSE; /* 5898 contains only the two supported layer entries. */
    for(n=0;n<count;n++) if(tables[list+n]==(room&255)) break;
    remaining=n==count?0:count-n-1; /* CPIR exhaustion selects pointer0 as well. */
    offset=pointers+remaining*2;
    address=tables[offset]|((u16)tables[offset+1]<<8);
    offset=address-0x58bc+slot*2;
    if(offset+1>=0x264) return FALSE;
    e[0x13]=tables[offset];e[0x11]=tables[offset+1];e[3]|=3;return TRUE;
}
/* 89D8..8A0E: hidden fixed emitters, random shoot decision and113..128 delay. */
static void fixed_shooter_behavior(u8 *e,u16 room,u16 slot)
{
    if(!e[1])
    {
        if(!place_fixed_actor(e,room,slot,room>>8?57:11)) return;
        e[3]&=254;e[4]=64;e[1]=2;return;
    }
    if(e[1]!=2 || e[4]) return;
    if((random()&15)>=8) create_projectile_type(e,0x14);
    e[4]=(random()&15)+113;
}
extern void replace_world_actor_cell(u16 x,u16 y,u16 cell);
static bool mobile_align_hero(u8 *entity,u16 hero_x,u16 hero_y);
/* 8FFF/901D/9021/9062/90A5: emerging walkers and cardinal bursts. */
static void burst_walker_behavior(u8 *e,const u8 *tilemap,u16 hero_x,u16 hero_y)
{
    u16 state=e[1],choice,n;
    if(state==2 || state==4)
    {
        if(e[11]!=3) return;
        e[11]=0;e[8]=0xb7;e[9]=0x89;e[13]=10;e[12]=2;e[1]=state=6;
    }
    if(state==6)
    {
        choice=random()&3;if(ground_blocked(e,tilemap,choice)) return;
        e[10]=choice;state=8;
    }
    if(state==8)
    {
        const u8 *data=e[0]==0x36?actor_ground_sequences:actor_mobile_sequences;
        e[4]=data[0];memcpy(e+0x14,data+1+e[10]*4,4);e[1]=10;
        /* 902E falls through9032, whose counter test returns for these steps. */
        return;
    }
    if(state!=10 || e[4]) return;
    choice=random()&(e[0]==0x36?15:7);
    if(!choice)
    {
        if(e[0]==0x37) create_guarded_projectile_type(e,0x1e);
        else for(n=4;n;n--)
        {
            u8 *shot=create_guarded_projectile_type(e,0x19);
            if(!shot) break;
            shot[10]=n-1;
        }
    }
    if(ground_blocked(e,tilemap,e[10])) { e[1]=6;return; }
    choice=random()&15;
    if(choice<2) e[1]=6;
    else if(choice<8 || !mobile_align_hero(e,hero_x,hero_y)) e[1]=8;
    else e[1]=6;
}
/* 90DB..919A: walkers38/39 pause, aim horizontally, then emit a bouncing1F. */
static void bouncing_shooter_behavior(u8 *e,const u8 *tilemap,u16 hero_x)
{
    u16 state=e[1],choice;
    if(state==2)
    {
        if(e[11]!=3) return;
        e[11]=0;e[8]=0xe1;e[9]=0x89;e[13]=16;e[12]=2;e[1]=state=4;
    }
    if(state==4)
    {
        choice=random()&3;if(ground_blocked(e,tilemap,choice)) return;
        e[10]=choice;state=6;
    }
    if(state==6)
    {
        e[4]=actor_ground_sequences[0];
        memcpy(e+0x14,actor_ground_sequences+1+e[10]*4,4);e[1]=8;return;
    }
    if(state==8)
    {
        if(e[4]) return;
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        choice=random()&15;
        if(choice<4) { e[1]=4;return; }
        if(choice<14) { e[1]=6;return; }
        e[10]=hero_x<e[0x13]?2:3;memset(e+0x14,0,4);e[4]=16;e[1]=10;return;
    }
    if(state==10 && !e[4])
    {
        create_projectile_type(e,0x1f);e[11]=0;e[8]=0xa1;e[9]=0x8a;e[4]=32;e[1]=12;return;
    }
    if(state==12 && !e[4])
    { e[8]=0xe1;e[9]=0x89;e[4]=16;e[1]=14;return; }
    if(state==14 && !e[4]) e[1]=4;
}
extern const u8 actor_charge_sequence[];
/* 91A9..927E: emerge on terrain03/19, walk, then charge an aligned hero. */
static void charging_behavior(u8 *e,const u8 *tilemap,const u8 *cells,
                              u16 hero_x,u16 hero_y,u16 frame,u16 slot)
{
    u16 state=e[1],choice;
    if(!state)
    {
        if(!spawn_world_actor(e,cells,hero_x,hero_y,frame,slot,9,2)) return;
        e[8]=0xf5;e[9]=0x8a;e[13]=6;e[12]=2;e[3]&=253;e[4]=32;e[1]=2;return;
    }
    if(state==2)
    {
        if(e[4]) return;
        e[11]=0;e[8]=0x1f;e[9]=0x8b;e[13]=10;e[12]=2;e[3]|=2;e[1]=4;return;
    }
    if(state==4)
    {
        choice=random()&3;if(ground_blocked(e,tilemap,choice)) return;
        e[10]=choice;state=6;
    }
    if(state==6 || state==10)
    {
        const u8 *sequence=state==6?actor_ground_sequences+17:actor_charge_sequence;
        e[4]=sequence[0];memcpy(e+0x14,sequence+1+e[10]*4,4);
        e[1]=state==6?8:12;return;
    }
    if(state==8)
    {
        if(e[4]) return;
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        choice=random()&15;
        if(choice<4) { e[1]=4;return; }
        if(choice<10 || !mobile_align_hero(e,hero_x,hero_y)) { e[1]=6;return; }
        memset(e+0x14,0,4);e[8]=0xaf;e[9]=0x8b;e[13]=8;e[12]=2;e[0x2c]=32;e[1]=10;return;
    }
    if(state==12 && !e[4])
    {
        if(!ground_blocked(e,tilemap,e[10]) && --e[0x2c]) { e[1]=10;return; }
        e[8]=0x1f;e[9]=0x8b;e[13]=10;e[12]=2;e[1]=4;
    }
}
/* 96C7..9725: hidden terrain3F ambusher, brief reveal and two opposite lob shots. */
static void ambusher_behavior(u8 *e,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot)
{
    u16 state=e[1],n;u8 *shot;
    if(!state)
    {
        if(!spawn_world_actor(e,cells,hero_x,hero_y,frame,slot,6,1)) return;
        e[3]&=254;e[8]=0x30;e[9]=0x90;e[13]=4;e[12]=2;
        e[4]=(random()&15)|0x70;e[1]=2;return;
    }
    if(state==2)
    {
        if(e[4]) return;
        e[3]|=1;e[4]=10;e[1]=4;return;
    }
    if(state==4 && !e[4])
    {
        e[3]&=254;
        for(n=2;n;n--)
        {
            shot=create_projectile_type(e,0x1d);if(!shot) break;
            shot[10]=n-1;
        }
        if(!n) e[4]=(random()&15)|0x70;
        e[1]=0;
    }
}
extern const u8 actor_dash_vectors[];
/* 92A0..93F1: terrain1F emergence, walking, aimed dash and hidden respawn. */
static void dashing_behavior(u8 *e,const u8 *tilemap,const u8 *cells,
                             u16 hero_x,u16 hero_y,u16 frame,u16 slot)
{
    u16 state=e[1],choice,octant=2,dx,dy;
    if(!state)
    {
        if(e[4] || !spawn_world_actor(e,cells,hero_x,hero_y,frame,slot,7,1)) return;
        e[8]=0xfa;e[9]=0x84;e[13]=10;e[12]=4;e[1]=state=2;
    }
    if(state==2)
    {
        if(e[11]!=3) return;
        e[11]=0;e[8]=0xef;e[9]=0x8b;e[13]=10;e[12]=2;e[1]=state=4;
    }
    if(state==4)
    {
        choice=random()&3;if(ground_blocked(e,tilemap,choice)) return;
        e[10]=choice;state=6;
    }
    if(state==6)
    {
        e[4]=actor_ground_sequences[17];memcpy(e+0x14,actor_ground_sequences+18+e[10]*4,4);
        e[1]=8;return;
    }
    if(state==8)
    {
        if(e[4]) return;
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        choice=random()&15;
        if(choice<2) { e[1]=4;return; }
        if(choice!=8) { e[1]=6;return; }
        memset(e+0x14,0,4);e[8]=0x67;e[9]=0x8c;e[11]=0;e[13]=32;e[12]=2;e[4]=8;e[1]=10;return;
    }
    if(state==10)
    {
        if(e[4]) return;
        e[8]=0x91;e[9]=0x8c;e[11]=0;e[13]=0;e[12]=1;state=12;
    }
    if(state==12)
    {
        if(hero_x<e[0x13]) { dx=e[0x13]-hero_x;octant|=4; } else dx=hero_x-e[0x13];
        if(hero_y<e[0x11]) { dy=e[0x11]-hero_y;octant&=~2; } else dy=hero_y-e[0x11];
        if(dy<dx) octant++;
        e[10]=actor_dash_vectors[octant];
        memcpy(e+0x16,actor_dash_vectors+8+octant*4,2);
        memcpy(e+0x14,actor_dash_vectors+10+octant*4,2);e[1]=14;e[4]=96;return;
    }
    if(state==14 && (e[0x11]<8 || e[0x11]>=152 || e[0x13]<8 || e[0x13]>=248 || !e[4]))
    {
        e[3]&=252;memset(e+0x14,0,4);e[4]=(random()&15)+113;e[1]=0;
    }
}
/* 9426..94A7: walkers3D/3E align, take one step towards the hero, then fire1A. */
static void pursuit_shooter_behavior(u8 *e,const u8 *tilemap,u16 hero_x,u16 hero_y)
{
    u16 state=e[1],choice;
    if(state==2)
    {
        if(e[11]!=3) return;
        e[11]=0;e[8]=e[0]==0x40?0xb2:0xaa;e[9]=e[0]==0x40?0x8d:0x8c;
        e[13]=10;e[12]=2;e[1]=state=4;
    }
    if(state==4)
    {
        choice=random()&3;if(ground_blocked(e,tilemap,choice)) return;
        e[10]=choice;state=6;
    }
    if(state==6)
    {
        e[4]=actor_ground_sequences[17];memcpy(e+0x14,actor_ground_sequences+18+e[10]*4,4);
        e[1]=8;return;
    }
    if(state==8)
    {
        if(e[4]) return;
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        choice=random()&15;
        if(choice<(e[0]==0x40?2:4)) { e[1]=4;return; }
        if(choice<(e[0]==0x40?8:10) || !mobile_align_hero(e,hero_x,hero_y)) { e[1]=6;return; }
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        e[4]=actor_ground_sequences[17];memcpy(e+0x14,actor_ground_sequences+18+e[10]*4,4);
        e[1]=10;return;
    }
    if(state==10 && !e[4])
    {
        if(ground_blocked(e,tilemap,e[10]) || (e[0]!=0x40 && (random()&15)<4)) { e[1]=4;return; }
        create_guarded_projectile_type(e,e[0]==0x40?0x1b:0x1a);e[1]=6;
    }
}
/* 984F..98F8: dungeon walkers 43/44/45. The larger distance axis is preferred;
 * equal distances keep the current direction, as the RET Z at 4A2F. */
static void dungeon_walker_behavior(u8 *e,const u8 *tilemap,const u8 *cells,
                                   u16 hero_x,u16 hero_y,u16 frame,u16 slot)
{
    u16 state=e[1],choice,offset=e[0]==0x43?0:17;
    if(!state)
    {
        if(!spawn_world_actor(e,cells,hero_x,hero_y,frame,slot,0,1)) return;
        e[8]=0xfa;e[9]=0x84;e[13]=10;e[12]=4;e[1]=state=2;
    }
    if(state==2)
    {
        if(e[11]!=3) return;
        e[11]=0;e[8]=2;e[9]=0x91;e[13]=10;e[12]=2;e[1]=state=4;
    }
    if(state==4)
    {
        choice=random()&3;if(ground_blocked(e,tilemap,choice)) return;
        e[10]=choice;state=6;
    }
    if(state==6)
    {
        e[4]=actor_ground_sequences[offset];
        memcpy(e+0x14,actor_ground_sequences+offset+1+e[10]*4,4);e[1]=8;return;
    }
    if(state==8)
    {
        u16 dx,dy;
        if(e[4]) return;
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        if((random()&15)<4) { e[1]=6;return; }
        dx=hero_x<e[0x13]?e[0x13]-hero_x:hero_x-e[0x13];
        dy=hero_y<e[0x11]?e[0x11]-hero_y:hero_y-e[0x11];
        if(dx!=dy)
        {
            choice=dy<dx?(hero_x<e[0x13]?2:3):(hero_y<e[0x11]?0:1);
            if(!ground_blocked(e,tilemap,choice)) e[10]=choice;
        }
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        e[4]=actor_ground_sequences[offset];
        memcpy(e+0x14,actor_ground_sequences+offset+1+e[10]*4,4);e[1]=10;return;
    }
    if(state==10 && !e[4])
    {
        if(ground_blocked(e,tilemap,e[10]) || (random()&15)<10) { e[1]=4;return; }
        e[1]=6;
        if(e[0]>=0x44) create_guarded_projectile_type(e,0x70);
    }
}

/* 8F7A..905D: proximity-triggered terrain trap, then walking and shot16. */
static void trap_walker_behavior(u8 *e,const u8 *tilemap,u16 hero_x,u16 hero_y,u16 room,u16 slot)
{
    u16 state=e[1],offset,choice; s16 distance;
    if(!state)
    {
        if(!place_fixed_actor(e,room,slot,11)) return;
        e[8]=0x8d;e[9]=0x89;e[3]&=254;e[1]=2;return;
    }
    if(state==2)
    {
        distance=(s16)hero_x-e[0x13];if(distance<0) distance=-distance;if(distance>=24) return;
        distance=(s16)hero_y-e[0x11];if(distance<0) distance=-distance;if(distance>=32) return;
        e[13]=2;e[12]=2;e[4]=24;e[3]|=1;e[1]=4;
        offset=(((e[0x11]-24)&248)*8)+(((e[0x13]-8)&248)>>2);
        replace_world_actor_cell((e[0x13]-8)&255,(e[0x11]-16)&255,tilemap[offset]==0x6b?0x27:1);
        offset=((e[0x11]&248)*8)+(((e[0x13]-8)&248)>>2);
        if(tilemap[offset]==0x53) replace_world_actor_cell((e[0x13]-8)&255,e[0x11],1);
        return;
    }
    if(state==4)
    {
        if(e[4]) return;
        e[10]=1;e[11]=0;e[8]=0xb7;e[9]=0x89;e[13]=10;e[12]=2;e[1]=state=6;
    }
    if(state==6)
    {
        choice=random()&3;if(ground_blocked(e,tilemap,choice)) return;
        e[10]=choice;state=8;
    }
    if(state==8)
    {
        const u8 *data=actor_mobile_sequences+17;
        e[4]=data[0];memcpy(e+0x14,data+1+e[10]*4,4);e[1]=10;return;
    }
    if(state==10 && !e[4])
    {
        if(!(random()&15)) create_guarded_projectile_type(e,0x16);
        if(ground_blocked(e,tilemap,e[10])) { e[1]=6;return; }
        choice=random()&15;
        if(choice<2) e[1]=6;
        else if(choice<8 || !mobile_align_hero(e,hero_x,hero_y)) e[1]=8;
        else e[1]=6;
    }
}

/* 894E..89D3: vertical walks may pause for64 ticks; horizontal walks continue. */
static void resting_behavior(u8 *e,const u8 *tilemap)
{
    u16 state=e[1],choice;
    if(state==2)
    {
        if(e[11]!=3) return;
        e[11]=0;e[8]=0x80;e[9]=0x87;e[13]=5;e[12]=2;e[1]=state=4;
    }
    if(state==4)
    {
        u16 direction=random()&3;
        if(ground_blocked(e,tilemap,direction)) return;
        e[10]=direction;state=6;
    }
    if(state==6)
    {
        const u8 *sequence=actor_mobile_sequences+17;
        e[4]=sequence[0];memcpy(e+0x14,sequence+1+e[10]*4,4);e[1]=8;return;
    }
    if(state==8 && !e[4])
    {
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        if(e[10]&2) { e[1]=6;return; }
        choice=random()&15;
        if(choice<4) { e[1]=4;return; }
        if(choice<14) { e[1]=6;return; }
        e[8]=0xaa;e[9]=0x87;memset(e+0x14,0,4);e[4]=64;e[1]=10;return;
    }
    if(state==10 && !e[4]) { e[8]=0x80;e[9]=0x87;e[1]=4; }
}

/* 8A19..8ACC: emerge on specific terrain, open, shoot, close, hide. */
static void emerging_shooter_behavior(u8 *e,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot)
{
    u16 state=e[1];
    if(!state)
    {
        if(e[4] || !spawn_world_actor(e,cells,hero_x,hero_y,frame,slot,e[0]==0x2e?4:5,e[0]==0x2e?2:1)) return;
        e[8]=0xd4;e[9]=0x87;e[11]=0;e[13]=8;e[12]=2;e[4]=32;e[1]=2;return;
    }
    if(state==2)
    {
        if(e[4]) return;
        e[8]=0xdc;e[9]=0x87;e[13]=12;e[12]=5;e[11]=0;e[1]=state=4;
    }
    if(state==4)
    {
        if(e[11]!=4) return;
        create_projectile_type(e,e[0]==0x2e?0x14:0x15);
        e[8]=0xe4;e[9]=0x87;e[13]=12;e[12]=5;e[11]=0;e[1]=6;return;
    }
    if(state==6)
    {
        if(e[11]!=4) return;
        e[8]=0xd4;e[9]=0x87;e[11]=0;e[13]=8;e[12]=2;e[4]=32;e[1]=8;return;
    }
    if(state==8 && !e[4]) { e[3]&=254;e[4]=(random()&31)|96;e[1]=0; }
}

extern const u8 actor_flying_sine[],actor_flying_acceleration[],actor_flying_facing[];
extern const u8 actor_aimed_projectile_templates[],actor_aimed_projectile_facing[];
static u16 actor_word(const u8 *e,u16 offset)
{
    return e[offset]|((u16)e[offset+1]<<8);
}
static void actor_put_word(u8 *e,u16 offset,u16 word)
{
    e[offset]=word;e[offset+1]=word>>8;
}
extern const u8 actor_jumping_vectors[];
/* 8B27/8C14: horizontal ground position, height and signed vertical momentum. */
static void reset_actor_jump(u8 *e)
{
    memset(e+0x20,0,2);memset(e+0x24,0,2);
    actor_put_word(e,0x28,e[0]==0x32?512:256);e[1]=6;
}
static void integrate_ballistic_actor(u8 *e,u16 gravity)
{
    u16 height,momentum;
    actor_put_word(e,0x22,actor_word(e,0x22)+actor_word(e,0x20));
    actor_put_word(e,0x26,actor_word(e,0x26)+actor_word(e,0x24));
    momentum=actor_word(e,0x28)+gravity;actor_put_word(e,0x28,momentum);
    height=momentum+actor_word(e,0x2a);if(height&32768) height=0;
    actor_put_word(e,0x2a,height);actor_put_word(e,0x10,actor_word(e,0x26)-height);
    actor_put_word(e,0x12,actor_word(e,0x22));
}
extern const u8 actor_lob_vectors[];
/* 4191..420B: lob1D retains fractional ground bytes and clears on landing. */
static void lob_projectile_behavior(u8 *e)
{
    const u8 *vector;
    if(!e[1])
    {
        e[8]=0x4e;e[9]=0x90;e[13]=4;e[12]=2;e[0x19]=16;
        actor_put_word(e,0x2e,0xfff0);e[0x23]=e[0x13];e[0x27]=e[0x11];e[1]=2;
    }
    if(e[1]==2)
    {
        e[3]|=3;vector=actor_lob_vectors+e[10]*5;
        memcpy(e+0x20,vector,2);memcpy(e+0x24,vector+2,2);e[10]=vector[4];
        actor_put_word(e,0x28,512);e[1]=4;integrate_ballistic_actor(e,actor_word(e,0x2e));return;
    }
    if(e[1]==4)
    {
        if(!actor_word(e,0x2a)) { memset(e,0,0x30);return; }
        integrate_ballistic_actor(e,actor_word(e,0x2e));
    }
}
static void integrate_actor_jump(u8 *e)
{
    integrate_ballistic_actor(e,e[0]==0x32?0xff80:0xffe0);
    e[8]=e[1]>=10 && e[0x2b]<3?0x8a:0x71;e[9]=0x88;
}
/* 8AF6..8C9E: jumping body31/32, with shadow30 in the following record. */
static void jumping_behavior(u8 *e,const u8 *tilemap,u16 slot)
{
    u16 state=e[1],offset,flags;
    const u8 *vector;
    if(state==2)
    {
        if(e[11]!=3) return;
        e[11]=e[12]=e[0x2a]=e[0x2b]=0;e[3]|=3;
        e[0x23]=e[0x13];e[0x27]=e[0x11];
        if(slot<15) { e[0x30]=0x30;e[0x32]=e[2]; }
        reset_actor_jump(e);integrate_actor_jump(e);return;
    }
    if(state==4) { reset_actor_jump(e);integrate_actor_jump(e);return; }
    if(state==6)
    {
        if(!actor_word(e,0x2a)) e[1]=(random()&3)?4:8;
        integrate_actor_jump(e);return;
    }
    if(state==10 && actor_word(e,0x2a)) { integrate_actor_jump(e);return; }
    if(state!=8 && state!=10) return;
    vector=actor_jumping_vectors+(e[0]==0x32?64:0)+(random()&7)*8;flags=vector[4];
    if((e[0x27]<49 && (flags&1)) || (e[0x27]>=128 && (flags&2)) ||
       (e[0x23]<41 && (flags&4)) || (e[0x23]>=216 && (flags&8)))
    { reset_actor_jump(e);integrate_actor_jump(e);return; }
    offset=(((e[0x11]+vector[5])&248)*8)+((((e[0x13]+vector[6])&255)>>2)&62);
    if((tilemap[offset+1]|tilemap[offset+3])&0xe0)
    { reset_actor_jump(e);integrate_actor_jump(e);return; }
    memcpy(e+0x20,vector,2);memcpy(e+0x24,vector+2,2);e[10]=vector[7];
    actor_put_word(e,0x28,e[0]==0x32?0x420:0x210);e[1]=10;integrate_actor_jump(e);
}
/* 94B8..963A: terrain3A emergence, walking, four parabolic hops and retreat. */
static void hopping_behavior(u8 *e,const u8 *tilemap,const u8 *cells,
                             u16 hero_x,u16 hero_y,u16 frame,u16 slot)
{
    u16 state=e[1],choice,flags,offset;
    const u8 *vector;
    if(!state)
    {
        if(e[4] || !spawn_world_actor(e,cells,hero_x,hero_y,frame,slot,3,1)) return;
        e[3]|=1;e[8]=0x6a;e[9]=0x8d;e[11]=0;e[13]=6;e[12]=2;
        actor_put_word(e,0x2e,0xffe0);e[4]=48;e[1]=2;return;
    }
    if(state==2)
    {
        if(e[4]) return;
        e[11]=0;e[8]=0x88;e[9]=0x8d;e[13]=10;e[12]=2;e[1]=state=4;
    }
    if(state==4)
    {
        choice=random()&3;if(ground_blocked(e,tilemap,choice)) return;
        e[10]=choice;state=6;
    }
    if(state==6)
    {
        e[4]=actor_mobile_sequences[17];memcpy(e+0x14,actor_mobile_sequences+18+e[10]*4,4);
        e[1]=8;return;
    }
    if(state==8)
    {
        if(e[4]) return;
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        choice=random()&15;
        if(choice<2) { e[1]=4;return; }
        if(choice!=8) { e[1]=6;return; }
        memset(e+0x14,0,4);e[4]=16;e[0x23]=e[0x13];e[0x27]=e[0x11];e[0x2c]=4;e[1]=10;return;
    }
    if(state==10)
    {
        if(e[4]) return;
        vector=actor_jumping_vectors+(random()&7)*8;flags=vector[4];
        if((e[0x27]<49 && (flags&1)) || (e[0x27]>=128 && (flags&2)) ||
           (e[0x23]<41 && (flags&4)) || (e[0x23]>=216 && (flags&8))) return;
        offset=(((e[0x11]+vector[5])&248)*8)+((((e[0x13]+vector[6])&255)>>2)&62);
        if((tilemap[offset+1]|tilemap[offset+3])&0xe0) return;
        memcpy(e+0x20,vector,2);memcpy(e+0x24,vector+2,2);e[10]=vector[7];
        actor_put_word(e,0x28,528);e[1]=12;integrate_ballistic_actor(e,actor_word(e,0x2e));return;
    }
    if(state==12)
    {
        if(actor_word(e,0x2a)) { integrate_ballistic_actor(e,actor_word(e,0x2e));return; }
        if(--e[0x2c]) { e[1]=10;return; }
        memset(e+0x14,0,4);e[8]=0x6a;e[9]=0x8d;e[13]=6;e[12]=2;e[4]=48;e[1]=14;return;
    }
    if(state==14 && !e[4]) { e[3]&=254;e[4]=(random()&15)|0x70;e[1]=0; }
}
/* 8AD1/8ADD: visible shadow follows ground coordinates of the preceding body. */
static void shadow_behavior(u8 *e,u16 slot)
{
    if(!slot || (e[1]!=0 && e[1]!=2)) return;
    if(!e[1]) { e[3]=1;e[8]=0x5e;e[9]=0x88; }
    e[0x13]=e[-13];e[0x11]=e[-9];
}
extern const u8 actor_water_jump_choices[];
/* 8D4B..8F39: water emergence, optional walking, ballistic leap and aimed shot. */
static void water_jump_behavior(u8 *e,const u8 *tilemap,const u8 *cells,
                                u16 hero_x,u16 hero_y,u16 frame,u16 slot)
{
    u16 state=e[1],choice,offset;
    const u8 *data;
    if(e[0]==0x33 && state<10) { e[1]=10;return; }
    if(state==0)
    {
        if(e[4] || !spawn_world_actor(e,cells,hero_x,hero_y,frame,slot,5,1)) return;
        e[8]=0x9d;e[9]=0x88;e[11]=0;e[13]=6;e[12]=2;
        actor_put_word(e,0x2e,0xffc0);e[4]=32;e[1]=2;return;
    }
    if(state==2)
    {
        if(e[4]) return;
        e[11]=0;e[8]=0x63;e[9]=0x89;e[13]=10;e[12]=2;e[1]=4;return;
    }
    if(state==4)
    {
        choice=random()&3;if(ground_blocked(e,tilemap,choice)) return;
        e[10]=choice;state=6;
    }
    if(state==6)
    {
        data=actor_mobile_sequences;e[4]=data[0];memcpy(e+0x14,data+1+e[10]*4,4);e[1]=8;return;
    }
    if(state==8)
    {
        if(e[4]) return;
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        choice=random()&15;
        if(choice<2) { e[1]=4;return; }
        if(choice!=8 || (e[0x11]&15)) { e[1]=6;return; }
        if(!(e[0x13]&8)) { e[1]=4;return; }
        memset(e+0x14,0,4);e[4]=16;e[0x23]=e[0x13];e[0x27]=e[0x11];e[1]=10;return;
    }
    if(state==10)
    {
        if(e[0]==0x33)
        {
            if(e[4]) return;
            e[11]=0;
            if(!spawn_world_actor(e,cells,hero_x,hero_y,frame,slot,5,1)) return;
            e[3]&=254;
        }
        choice=random()&3;
        if(choice<2 && e[0x13]<72) choice|=2;
        else if(choice>=2 && e[0x13]>=200) choice&=1;
        e[0x2c]=choice;data=actor_water_jump_choices+choice*3;e[10]=data[0];
        offset=(((e[0x11]+data[2])&248)*8)+(((((e[0x13]+data[1])&255)>>2))&62);
        if((tilemap[offset+1]&0xc0)!=0xc0) { e[1]=2;return; }
        e[3]|=1;e[8]=0x9d;e[9]=0x88;e[13]=13;e[12]=3;actor_put_word(e,0x2e,0xffc0);e[1]=12;return;
    }
    if(state==12)
    {
        if(e[11]!=2) return;
        e[0x23]=e[0x13];e[0x27]=e[0x11];e[8]=0x17;e[9]=0x89;e[11]=0;e[13]=24;e[12]=2;e[1]=14;return;
    }
    if(state==14)
    {
        data=actor_water_jump_choices+12+e[0x2c]*4;memcpy(e+0x20,data,2);memcpy(e+0x24,data+2,2);
        actor_put_word(e,0x28,0x420);e[1]=16;integrate_ballistic_actor(e,actor_word(e,0x2e));return;
    }
    if(state==16)
    {
        if(e[0x2b]==32) create_projectile_type(e,0x13);
        if(actor_word(e,0x2a)) { integrate_ballistic_actor(e,actor_word(e,0x2e));return; }
        e[8]=0xe1;e[9]=0x88;e[11]=0;e[13]=13;e[12]=4;e[1]=18;return;
    }
    if(state==18 && e[11]==3)
    {
        if(e[0]==0x33) { e[3]&=254;e[4]=(random()&15)|0x79;e[1]=10; }
        else { e[10]=random()&3;e[1]=2; }
    }
}
/* 8642: the magnitude test is on the signed high byte, before the shift. */
static void flying_axis(u8 *e,u16 hero,u16 position,u16 velocity,u16 center,u16 limit,u16 acceleration)
{
    s16 value=hero<e[position]?-(s16)acceleration:(s16)acceleration;
    s16 high=(s8)e[velocity+1];
    if(high<0) high=-high;
    if(high<2) value=(s16)((u16)value+actor_word(e,velocity));
    if(((e[center+1]-32)&255)>=limit) value>>=1;
    actor_put_word(e,velocity,(u16)value);
    actor_put_word(e,center,actor_word(e,center)+(u16)value);
}
/* 044E/0450: signed table value doubled, multiplied, then take high byte. */
static u8 flying_offset(u16 phase,u16 amplitude)
{
    s16 product=(s8)actor_flying_sine[phase&255]*2*amplitude;
    return (u16)product>>8;
}
extern const u8 actor_orbit_facing[];
extern const u8 second_boss_turns[],second_boss_fast[],second_boss_slow[];
/* 4EB7 and 4E0A: eight-way selection and source nibble-aligned boundaries. */
static u16 second_boss_direction(u8 *e,u16 hero_x,u16 hero_y,u8 select,u8 turn)
{
    u16 d;
    if(select&1) d=hero_x>=e[0x13]?(hero_y>=e[0x11]?7:4):(hero_y>=e[0x11]?5:6);
    else d=turn<32?(turn&7):second_boss_turns[e[0x20]*4+(turn&3)];
    {
        u16 x=e[0x13]&240,y=e[0x11]&240;
        if(d==0 && y<48) d=1;
        else if(d==1 && y>=112) d=0;
        else if(d==2 && x<80) d=3;
        else if(d==3 && x>=176) d=2;
        else if(d==4 && (x>=176 || y<48)) d=5;
        else if(d==5 && (x<80 || y>=112)) d=4;
        else if(d==6 && (x<80 || y<48)) d=7;
        else if(d==7 && (x>=176 || y>=112)) d=6;
    }
    return d;
}
static u8 dungeon_phase_roll(const u8 *roll,u16 n) { return roll?roll[n]:(u8)random(); }
/* Provisional input for direct LD A,R sites. Cold reset clears R7 and this
 * ROM contains no LD R,A. Keep explicit fixture inputs unchanged; this is
 * a domain correction, not reconstruction of the source R/IRQ sequence. */
static u8 dungeon_phase_refresh(const u8 *roll,u16 n)
{ return roll?roll[n]:((u8)random()&127); }
/* 57F8 with BC=0001: only terrain00 is accepted, with retained partial writes. */
static bool dungeon_phase_spawn(u8 *e,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot,const u8 *roll)
{
    u16 cell;s16 distance;
    if((frame&7)!=(slot&7)) return FALSE;
    cell=(dungeon_phase_roll(roll,0)&127)+16;if(((cell-1)&15)>=14 || cells[cell]!=actor_spawn_terrain[0]) return FALSE;
    e[0x13]=((cell&15)<<4)+8;distance=(s16)hero_x-e[0x13];if(distance<0) distance=-distance;if(distance<16) return FALSE;
    e[0x11]=(cell&240)+16;distance=(s16)hero_y-e[0x11];if(distance<0) distance=-distance;if(distance<16) return FALSE;
    e[10]=dungeon_phase_roll(roll,1)&3;e[3]|=3;return TRUE;
}
/* 4D32 ->98FF: fixed placement, proximity trigger and repeated ballistic hops. */
void dungeon_proximity_behavior(u8 *e,const u8 *tilemap,u16 hero_x,u16 hero_y,u16 room,u16 slot,const u8 *roll)
{
    u16 state=e[1],direction,offset,flags,dx,dy;const u8 *vector;
    if(!state)
    {
        place_fixed_actor(e,room,slot,57);e[8]=0xc2;e[9]=0x91;e[12]=e[13]=0;e[11]=2;
        actor_put_word(e,0x2e,0xffe0);e[1]=2;return;
    }
    if(state==2)
    {
        dx=hero_x>=e[0x13]?hero_x-e[0x13]:e[0x13]-hero_x;dy=hero_y>=e[0x11]?hero_y-e[0x11]:e[0x11]-hero_y;
        if(dx<29 && dy<29) { e[13]=5;e[12]=2;e[11]=0;e[4]=24;e[1]=4; }return;
    }
    if(state==4)
    {
        if(e[4]) return;e[8]=0xfd;e[9]=0x91;e[11]=0;e[13]=14;e[12]=2;e[0x23]=e[0x13];e[0x27]=e[0x11];e[1]=6;return;
    }
    if(state==6)
    {
        if((dungeon_phase_roll(roll,0)&15)>=10) direction=dungeon_phase_roll(roll,1)&7;
        else
        {
            dx=hero_x>=e[0x13]?hero_x-e[0x13]:e[0x13]-hero_x;dy=hero_y>=e[0x11]?hero_y-e[0x11]:e[0x11]-hero_y;
            direction=dy>=dx?(hero_x>=e[0x13]?1:0)+(hero_y>=e[0x11]?2:0):(hero_x>=e[0x13]?6:4)+(hero_y>=e[0x11]?1:0);
        }
        vector=actor_jumping_vectors+direction*8;flags=vector[4];
        if((e[0x27]<49 && (flags&1)) || (e[0x27]>=128 && (flags&2)) ||
           (e[0x23]<41 && (flags&4)) || (e[0x23]>=216 && (flags&8))) return;
        offset=(((e[0x11]+vector[5])&248)*8)+((((e[0x13]+vector[6])&255)>>2)&62);
        if((tilemap[offset+1]|tilemap[offset+3])&0xe0) return;
        memcpy(e+0x20,vector,2);memcpy(e+0x24,vector+2,2);e[10]=vector[7];actor_put_word(e,0x28,528);e[1]=8;
        integrate_ballistic_actor(e,actor_word(e,0x2e));return;
    }
    if(state==8)
    { if(actor_word(e,0x2a)) integrate_ballistic_actor(e,actor_word(e,0x2e));else e[1]=6; }
}
static void dungeon_phase_move(u8 *e,u16 hero_x,u16 hero_y,const u8 *roll)
{
    u8 select=e[0]>=0x49?dungeon_phase_refresh(roll,2):0,turn=(select&1)?0:dungeon_phase_refresh(roll,3);
    u16 direction=second_boss_direction(e,hero_x,hero_y,select,turn);const u8 *v=second_boss_fast+1+direction*5;
    e[0x20]=direction;e[4]=second_boss_fast[0];memcpy(e+0x14,v,4);e[10]=v[4];e[1]=6;
}
static void dungeon_phase_reset(u8 *e)
{ e[8]=0x27;e[9]=0x92;e[11]=0;e[13]=4;e[12]=2;e[0x2e]=20; }
/* 4D38: types47..49 eight-way movement and progressive pause/animation slowdown. */
void dungeon_phase_behavior(u8 *e,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot,const u8 *roll)
{
    u16 state=e[1];
    if(!state)
    {
        if(!dungeon_phase_spawn(e,cells,hero_x,hero_y,frame,slot,roll)) return;
        e[8]=0xfa;e[9]=0x84;e[13]=10;e[12]=4;e[1]=2;return;
    }
    if(state==2)
    { if(e[11]!=3) return;dungeon_phase_reset(e);state=4; }
    if(state==4) { dungeon_phase_move(e,hero_x,hero_y,roll);return; }
    if(state==6)
    {
        if(e[4]) return;
        if(e[0x2e]) { e[0x2e]--;dungeon_phase_move(e,hero_x,hero_y,roll);return; }
        if(dungeon_phase_roll(roll,4)>=8) { dungeon_phase_move(e,hero_x,hero_y,roll);return; }
        memset(e+0x14,0,4);e[0x2f]=16;e[1]=8;state=8;
    }
    if(state==8)
    {
        if(--e[0x2f]) return;
        e[13]++;
        if(e[13]<10 || e[11]) { e[0x2f]=15;e[1]=8;return; } /* 4DC4 falls through DEC. */
        e[0x2f]=64;e[13]=e[12]=0;e[1]=10;state=10;
    }
    if(state==10)
    {
        if(e[0]==0x49 && e[0x2f]==32) create_projectile_type(e,0x14);
        if(!--e[0x2f]) { dungeon_phase_reset(e);dungeon_phase_move(e,hero_x,hero_y,roll); }
    }
}
extern const u8 dungeon_split_data[];
/* 4F44 ->9A1B: wandering and a surviving-hit split into up to four bodies. */
static void dungeon_split_state(u8 *e,const u8 *tilemap,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot,const u8 *roll)
{
    u16 state=e[1],direction,offset;const u8 *v;
    if(!state)
    {
        if(dungeon_phase_spawn(e,cells,hero_x,hero_y,frame,slot,roll))
        { e[8]=0xfa;e[9]=0x84;e[13]=10;e[12]=4;e[1]=2; }return;
    }
    if(state==2)
    {
        if(e[11]!=3) return;e[11]=0;e[8]=0x51;e[9]=0x92;e[13]=5;e[12]=2;e[0x20]=e[0]!=0x4a;e[1]=4;return;
    }
    if(state==4)
    {
        direction=dungeon_phase_roll(roll,2)&3;
        if(direction==e[10] || (direction==0 && e[0x11]<49) || (direction==1 && e[0x11]>=136) ||
           (direction==2 && e[0x13]<41) || (direction==3 && e[0x13]>=216)) return;
        e[10]=direction;v=dungeon_split_data+17+direction*4;e[4]=dungeon_split_data[16];memcpy(e+0x14,v,4);e[1]=6;return;
    }
    if(state==6)
    {
        if(e[4]) return;
        if(!ground_blocked(e,tilemap,e[10]) && (dungeon_phase_roll(roll,3)&15)<2) { e[1]=4;return; }
        memset(e+0x14,0,4);e[4]=32;e[1]=8;return;
    }
    if(state==8)
    { if(!e[4]) { if((dungeon_phase_roll(roll,3)&15)<2) e[1]=4;else e[4]=32; }return; }
    if(state==10)
    {
        if((frame&255)!=e[0x21]) return;v=dungeon_split_data+e[0x22]*2;
        offset=(((e[0x11]+v[0])&248)*8)+(((((e[0x13]+v[1])&255)>>2))&62);
        if(!(tilemap[offset+1]&128)) { e[0x15]=v[8];e[0x17]=v[9]; }
        e[4]=4;e[1]=12;return;
    }
    if(state==12)
    { if(e[4]) return;e[0x15]=e[0x17]=0;e[1]=14;state=14; }
    if(state==14 && !e[5]) { e[3]|=2;e[4]=(dungeon_phase_roll(roll,4)&15)+16;e[1]=6; }
}
void dungeon_split_behavior(u8 *e,const u8 *tilemap,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot,const u8 *roll)
{
    u16 n,branch=3;u8 damage;
    dungeon_split_state(e,tilemap,cells,hero_x,hero_y,frame,slot,roll);
    damage=e[0x1d];if(!damage || e[0x18]<=damage || !e[0x20]) return;
    e[0x20]=e[0x22]=e[11]=e[12]=e[13]=0;memset(e+0x14,0,4);e[8]=0x7b;e[9]=0x92;
    e[0x21]=(frame+1)&255;e[1]=10;e[3]&=253;
    for(n=0;n<16 && branch;n++) if(!world_actor_state[n*48])
    { u8 *child=world_actor_state+n*48;memcpy(child,e,34);child[0x22]=branch--; }
}
extern const u8 dungeon_hop_data[];
/* 4FB1 ->9B1E: gravity-driven hops and a clock-selected temporary body. */
void dungeon_hop_behavior(u8 *e,const u8 *tilemap,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot,const u8 *roll)
{
    u16 state=e[1],choice,flags,destination;const u8 *v;
    if(state<=2) { dungeon_split_state(e,tilemap,cells,hero_x,hero_y,frame,slot,roll);return; }
    if(state==4)
    { memset(e+0x14,0,4);e[4]=(dungeon_phase_roll(roll,2)&31)|96;e[1]=6;return; }
    if(state==6)
    {
        if(e[4]) return;e[4]=32;choice=(dungeon_phase_roll(roll,3)&14)>>1;v=dungeon_hop_data+choice*6;flags=v[0];
        if((e[0x11]<65 && (flags&1)) || (e[0x11]>=128 && (flags&2)) ||
           (e[0x13]<57 && (flags&4)) || (e[0x13]>=200 && (flags&8))) return;
        e[10]=v[1];memcpy(e+0x14,v+2,4);
        if(slot<8)
        {
            destination=8+((frame&14)>>1);
            if(!world_actor_state[destination*48]) { e[1]=4;memcpy(world_actor_state+destination*48,e,32); }
        }
        e[1]=8;state=8;
    }
    if(state==8)
    {
        actor_put_word(e,0x14,actor_word(e,0x14)+32);
        if(!e[4]) { memset(e+0x14,0,4);e[4]=(dungeon_phase_roll(roll,2)&31)|96;e[1]=6; }
    }
}
extern const u8 dungeon_drain_vectors[];
extern void world_drain_hero_magic(void);
static void aim_velocity(u8 *e,const u8 *vectors,u16 hero_x,u16 hero_y);
static void dungeon_drain_move(u8 *e,u16 hero_x,u16 hero_y,const u8 *roll)
{
    if(e[0]==0x4e && (dungeon_phase_roll(roll,3)&15)<8) aim_velocity(e,dungeon_drain_vectors,hero_x,hero_y);
    else
    {
        const u8 *v=dungeon_drain_vectors+e[0x20]*4;
        memcpy(e+0x16,v,2);memcpy(e+0x14,v+2,2);e[10]=actor_dash_vectors[e[0x20]];
    }
    e[0x21]=128;e[1]=6;e[4]=32;
}
/* 4FB7 ->9C02: roaming, border redirects and optional aimed motion.
 * Interior lifetime expiry inherits Z80 E. Valid nonzero trajectories meet a
 * border before128 segments; explicit E is available only for routine tests. */
void dungeon_drain_behavior(u8 *e,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot,const u8 *roll,u8 inherited_edge)
{
    static const u8 turns[16]={3,6,2,7,4,0,5,1,0,3,1,2,5,4,7,6};u16 state=e[1],edge;
    if(!state)
    {
        if(dungeon_phase_spawn(e,cells,hero_x,hero_y,frame,slot,roll))
        { e[8]=0xfa;e[9]=0x84;e[13]=10;e[12]=4;e[1]=2; }
    }
    else if(state==2)
    { if(e[11]==3) { e[11]=0;e[8]=0x8b;e[9]=0x92;e[13]=1;e[12]=2;e[1]=4; } }
    else if(state==4) { e[0x20]=dungeon_phase_roll(roll,2)&7;dungeon_drain_move(e,hero_x,hero_y,roll); }
    else if(state==6)
    {
        edge=4;
        if(e[0x11]<40) edge=0;else if(e[0x11]>=144) edge=1;else if(e[0x13]<40) edge=2;else if(e[0x13]>=216) edge=3;
        if(edge==4 && !e[4]) { if(--e[0x21]) e[4]=32;else edge=inherited_edge; }
        if(edge<4) { e[0x20]=turns[edge*4+((dungeon_phase_roll(roll,4)&15)>>2)];dungeon_drain_move(e,hero_x,hero_y,roll); }
    }
    if(e[3]&4) { world_drain_hero_magic();e[3]&=251; }
}
/* 4FD2 ->9DA6: pursuit, aligned charge50 and occasional cardinal shot51. */
static void dungeon_hunter_walk(u8 *e,u16 state)
{ e[4]=first_boss_movement[0];memcpy(e+0x14,first_boss_movement+1+e[10]*4,4);e[1]=state; }
void dungeon_hunter_behavior(u8 *e,const u8 *tilemap,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot,const u8 *roll)
{
    u16 state=e[1],direction,dx,dy;
    if(!state)
    { if(dungeon_phase_spawn(e,cells,hero_x,hero_y,frame,slot,roll)) { e[8]=0xfa;e[9]=0x84;e[13]=10;e[12]=4;e[1]=2; }return; }
    if(state==2)
    { if(e[11]!=3) return;e[11]=0;e[8]=0xb5;e[9]=0x92;e[13]=10;e[12]=2;e[1]=4;state=4; }
    if(state==4)
    { direction=dungeon_phase_roll(roll,2)&3;if(ground_blocked(e,tilemap,direction)) return;e[10]=direction;state=6; }
    if(state==6) { dungeon_hunter_walk(e,8);return; }
    if(state==8)
    {
        if(e[4]) return;
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        if((dungeon_phase_roll(roll,3)&15)<2) { e[1]=6;return; }
        dx=hero_x>=e[0x13]?hero_x-e[0x13]:e[0x13]-hero_x;dy=hero_y>=e[0x11]?hero_y-e[0x11]:e[0x11]-hero_y;
        if(dx!=dy)
        { direction=dy<dx?(hero_x<e[0x13]?2:3):(hero_y<e[0x11]?0:1);if(!ground_blocked(e,tilemap,direction)) e[10]=direction; }
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        if(e[0]==0x50)
        {
            if((hero_x&240)==(e[0x13]&240)) e[10]=hero_y<e[0x11]?0:1;
            else if((hero_y&240)==(e[0x11]&240)) e[10]=hero_x<e[0x13]?2:3;
            else { e[1]=6;return; }
            if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
            memset(e+0x14,0,4);e[0x2c]=16;e[1]=10;return;
        }
        dungeon_hunter_walk(e,10);return;
    }
    if(state==10)
    {
        if(e[0]==0x50) { e[4]=actor_charge_sequence[0];memcpy(e+0x14,actor_charge_sequence+1+e[10]*4,4);e[1]=12;return; }
        if(e[4]) return;
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        if(e[0]==0x51 && (dungeon_phase_roll(roll,4)&15)<4) create_projectile_type(e,0x18);
        e[1]=6;return;
    }
    if(state==12 && !e[4])
    { if(ground_blocked(e,tilemap,e[10]) || !--e[0x2c]) e[1]=4;else e[1]=10; }
}
extern const u8 dungeon_hunter_shot[];
extern const u8 dungeon_ambush_vectors[];
extern bool world_hero_zero_floor(void);
/* 4FD8 ->9EA5: cached floor trigger, emergence, aimed motion and pauses. */
static void dungeon_ambush_state(u8 *e,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot,const u8 *roll)
{
    u16 state=e[1];
    if(!state) { if(world_hero_zero_floor()) e[1]=2;return; }
    if(state==2)
    {
        if(!dungeon_phase_spawn(e,cells,hero_x,hero_y,frame,slot,roll)) return;
        e[8]=0x45;e[9]=0x93;e[13]=8;e[12]=3;e[1]=4;state=4;
    }
    if(state==4)
    { if(e[11]!=2) return;e[11]=0;e[8]=0x6b;e[9]=0x93;e[13]=4;e[12]=2;e[1]=6;state=6; }
    if(state==6)
    { aim_velocity(e,dungeon_ambush_vectors,hero_x,hero_y);e[1]=8;e[4]=32;return; }
    if(state==8)
    {
        if(e[0x11]<16 || e[0x11]>=144 || e[0x13]<16 || e[0x13]>=240) { e[1]=6;return; }
        if(e[4]) return;
        if((dungeon_phase_roll(roll,2)&15)<4) { e[1]=10;memset(e+0x14,0,4);e[4]=72; }
        else e[1]=6;return;
    }
    if(state==10 && !e[4]) e[1]=6;
}
void dungeon_ambush_behavior(u8 *e,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot,const u8 *roll)
{
    dungeon_ambush_state(e,cells,hero_x,hero_y,frame,slot,roll);
    if(e[3]&4) { world_drain_hero_magic();e[3]&=251; }
}
extern void world_curse_hero(void);
/* 4FF3 ->9F81: hunter4F movement with a different descriptor and curse contact. */
void dungeon_curse_behavior(u8 *e,const u8 *tilemap,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot,const u8 *roll)
{
    bool reveal=e[1]==2 && e[11]==3;
    dungeon_hunter_behavior(e,tilemap,cells,hero_x,hero_y,frame,slot,roll);
    if(reveal) { e[8]=0xfb;e[9]=0x93; }
    if(e[3]&4) { world_curse_hero();e[3]&=251; }
}
/* 5008 ->9FFC: fixed emitters54/55, telegraph, cardinal71 shots and repeats. */
void dungeon_emitter_behavior(u8 *e,u16 room,u16 slot,u16 hero_x,u16 hero_y,const u8 *roll)
{
    u16 state=e[1];
    if(!state)
    {
        if(!place_fixed_actor(e,room,slot,57)) return;
        e[8]=0xfa;e[9]=0x84;e[13]=10;e[12]=4;e[1]=2;state=2;
    }
    if(state==2) { if(e[11]!=3) return;state=4; }
    if(state==4)
    {
        e[13]=e[12]=e[11]=0;e[8]=0x8b;e[9]=0x94;e[1]=6;
        e[4]=(dungeon_phase_roll(roll,0)&15)+113;return;
    }
    if(state==6)
    {
        if(e[0]==0x55) { if(!mobile_align_hero(e,hero_x,hero_y)) return; }
        else
        {
            if(e[4]) return;
            if((dungeon_phase_roll(roll,1)&15)>=2) { e[4]=32;return; }
        }
        e[8]=0xd7;e[9]=0x94;e[13]=8;e[12]=2;e[4]=8;e[1]=8;return;
    }
    if(state==8)
    {
        if(e[4]) return;
        if(e[0]!=0x55) e[10]=dungeon_phase_roll(roll,2)&3;
        e[4]=8;e[1]=10;return;
    }
    if(state==10 && !e[4])
    {
        if((dungeon_phase_roll(roll,3)&15)>=4)
        {
            create_projectile_type(e,0x71);
            if(e[0]!=0x55 && (dungeon_phase_roll(roll,4)&15)>=4) { e[4]=128;e[1]=8;return; }
        }
        e[13]=e[12]=e[11]=0;e[8]=0x8b;e[9]=0x94;
        e[4]=(dungeon_phase_roll(roll,0)&15)+113;e[1]=6;
    }
}
extern const u8 dungeon_emitter_shot[];
/* 500E/A0E6 and501A/A29A: teleporting emitters56/59/5A. */
void dungeon_teleport_behavior(u8 *e,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot,const u8 *roll)
{
    u16 state=e[1],dx,dy;
    if(!state)
    {
        e[3]&=254;if(e[4]) return;
        if(!dungeon_phase_spawn(e,cells,hero_x,hero_y,frame,slot,roll)) return;
        e[8]=e[0]==0x56?0xd7:0xaa;e[9]=e[0]==0x56?0x94:0x95;
        e[5]=32;e[3]&=253;e[1]=2;
        if(e[0]==0x56) e[4]=32;
        else
        {
            dx=hero_x>=e[0x13]?hero_x-e[0x13]:e[0x13]-hero_x;
            dy=hero_y>=e[0x11]?hero_y-e[0x11]:e[0x11]-hero_y;
            e[10]=dx>=dy?(hero_x<e[0x13]?2:3):(hero_y<e[0x11]?0:1);
        }
        return;
    }
    if(state==2)
    {
        if(e[0]==0x56) { if(e[4]) return;e[4]=32; }
        else { if(e[5]) return;e[8]=0xf6;e[9]=0x95;e[4]=(dungeon_phase_roll(roll,2)&7)+40; }
        e[3]|=2;e[1]=4;return;
    }
    if(state==4)
    {
        if(e[4]) return;create_projectile_type(e,e[0]==0x56?0x71:0x17);
        e[4]=e[0]==0x56?16:(dungeon_phase_roll(roll,3)&3)+24;e[1]=6;return;
    }
    if(state==6)
    { if(e[4]) return;e[4]=e[0]==0x5a?8:16;e[1]=8;e[5]=16;e[3]&=253;return; }
    if(state==8 && !e[4])
    { e[4]=(dungeon_phase_roll(roll,4)&15)+(e[0]==0x5a?72:104);e[1]=0; }
}
/* 5014 ->A181: fixed hidden57/58, proximity reveal and pursuit. */
void dungeon_sentinel_behavior(u8 *e,const u8 *tilemap,u16 hero_x,u16 hero_y,u16 room,u16 slot,const u8 *roll)
{
    u16 state=e[1],direction,dx,dy;const u8 *sequence;
    if(!state)
    {
        if(!place_fixed_actor(e,room,slot,57)) return;
        e[8]=0x67;e[9]=0x95;e[13]=12;e[12]=2;e[3]&=252;e[1]=2;state=2;
    }
    if(state==2)
    {
        dx=hero_x>=e[0x13]?hero_x-e[0x13]:e[0x13]-hero_x;
        dy=hero_y>=e[0x11]?hero_y-e[0x11]:e[0x11]-hero_y;
        if(dx<24 && dy<24) { e[3]|=1;e[5]=32;e[4]=32;e[1]=10; }return;
    }
    if(state==4)
    {
        direction=dungeon_phase_roll(roll,0)&3;if(ground_blocked(e,tilemap,direction)) return;
        e[10]=direction;state=6;
    }
    if(state==6)
    { sequence=actor_mobile_sequences;e[4]=sequence[0];memcpy(e+0x14,sequence+1+e[10]*4,4);e[1]=8;return; }
    if(state==8)
    {
        if(e[4]) return;
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        if((dungeon_phase_roll(roll,1)&15)<2) { e[1]=6;return; }
        dx=hero_x>=e[0x13]?hero_x-e[0x13]:e[0x13]-hero_x;
        dy=hero_y>=e[0x11]?hero_y-e[0x11]:e[0x11]-hero_y;
        if(dx!=dy)
        { direction=dy<dx?(hero_x<e[0x13]?2:3):(hero_y<e[0x11]?0:1);if(!ground_blocked(e,tilemap,direction)) e[10]=direction; }
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        sequence=actor_mobile_sequences+17;e[4]=sequence[0];memcpy(e+0x14,sequence+1+e[10]*4,4);e[1]=10;return;
    }
    if(state==10)
    {
        if(e[4]) return;e[3]|=2;
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        if(e[0]==0x58 && (dungeon_phase_roll(roll,2)&15)<2)
        { e[8]=0x91;e[9]=0x95;e[12]=e[11]=0;memset(e+0x14,0,4);e[4]=128;e[1]=12;return; }
        e[1]=6;return;
    }
    if(state==12 && !e[4]) { e[8]=0x67;e[9]=0x95;e[13]=12;e[12]=2;e[1]=4; }
}
extern u16 world_hero_state(void);
extern bool world_tick_hero_grab(u8 *e,u16 frame);
/* 5043 ->A302: wandering5B, close-range attachment and gold stealing. */
void dungeon_thief_behavior(u8 *e,const u8 *tilemap,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot,const u8 *roll)
{
    u16 state=e[1],direction,dx,dy;bool reset=FALSE;
    if(!state)
    { if(dungeon_phase_spawn(e,cells,hero_x,hero_y,frame,slot,roll)) { e[8]=0xfa;e[9]=0x84;e[13]=10;e[12]=4;e[1]=2; }return; }
    if(state==12)
    {
attached:
        if(!world_tick_hero_grab(e,frame)) return;
        e[0x11]-=8;reset=TRUE;
    }
    if(state==2) { if(e[11]!=3) return;reset=TRUE; }
    if(reset)
    { e[11]=0;e[8]=0x42;e[9]=0x96;e[13]=10;e[12]=2;e[0x20]=0;e[0x21]=16;e[1]=4;state=4; }
    if(state==4)
    { direction=dungeon_phase_roll(roll,2)&3;if(ground_blocked(e,tilemap,direction)) return;e[10]=direction;state=6; }
    if(state==6) { dungeon_hunter_walk(e,8);return; }
    if(state==8)
    {
        if(e[4]) return;
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        if((dungeon_phase_roll(roll,3)&15)<2) { e[1]=6;return; }
        dx=hero_x>=e[0x13]?hero_x-e[0x13]:e[0x13]-hero_x;
        dy=hero_y>=e[0x11]?hero_y-e[0x11]:e[0x11]-hero_y;
        if(dx!=dy)
        { direction=dy<dx?(hero_x<e[0x13]?2:3):(hero_y<e[0x11]?0:1);if(!ground_blocked(e,tilemap,direction)) e[10]=direction; }
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        dungeon_hunter_walk(e,10);return;
    }
    if(state==10)
    {
        dx=hero_x>=e[0x13]?hero_x-e[0x13]:e[0x13]-hero_x;
        dy=hero_y>=e[0x11]?hero_y-e[0x11]:e[0x11]-hero_y;
        if(dx<9 && dy<9 && world_hero_state()!=12)
        { e[8]=0x6c;e[9]=0x96;e[11]=e[13]=e[12]=e[4]=0;e[1]=12;goto attached; }
        if(e[4]) return;e[1]=ground_blocked(e,tilemap,e[10])?4:6;
    }
}
extern u16 world_hero_direction(void);
/* 5049 ->A421:5C cardinal wander/alignment,5D pursuit, facing damage gate. */
static void dungeon_guard_state(u8 *e,const u8 *tilemap,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot,const u8 *roll)
{
    u16 state=e[1],direction,dx,dy;const u8 *sequence=actor_mobile_sequences;
    if(!state)
    { if(dungeon_phase_spawn(e,cells,hero_x,hero_y,frame,slot,roll)) { e[8]=0xfa;e[9]=0x84;e[13]=10;e[12]=4;e[1]=2; }return; }
    if(state==2)
    { if(e[11]!=3) return;e[11]=0;e[8]=0x85;e[9]=0x96;e[13]=10;e[12]=2;e[1]=4;state=4; }
    if(state==4)
    { direction=dungeon_phase_roll(roll,2)&3;if(ground_blocked(e,tilemap,direction)) return;e[10]=direction;state=6; }
    if(state==6)
    { e[4]=sequence[0];memcpy(e+0x14,sequence+1+e[10]*4,4);e[1]=8;return; }
    if(state==8)
    {
        if(e[4]) return;
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        direction=dungeon_phase_roll(roll,3)&15;
        if(e[0]==0x5c)
        {
            if(direction<2 || (direction>=8 && mobile_align_hero(e,hero_x,hero_y))) e[1]=4;
            else e[1]=6;
            return;
        }
        if(direction<2) { e[1]=6;return; }
        dx=hero_x>=e[0x13]?hero_x-e[0x13]:e[0x13]-hero_x;
        dy=hero_y>=e[0x11]?hero_y-e[0x11]:e[0x11]-hero_y;
        if(dx!=dy)
        { direction=dy<dx?(hero_x<e[0x13]?2:3):(hero_y<e[0x11]?0:1);if(!ground_blocked(e,tilemap,direction)) e[10]=direction; }
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        e[4]=sequence[0];memcpy(e+0x14,sequence+1+e[10]*4,4);e[1]=10;return;
    }
    if(state==10 && !e[4]) e[1]=ground_blocked(e,tilemap,e[10])?4:6;
}
void dungeon_guard_behavior(u8 *e,const u8 *tilemap,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot,const u8 *roll)
{
    dungeon_guard_state(e,tilemap,cells,hero_x,hero_y,frame,slot,roll);
    if(world_hero_direction()!=(e[10]^1)) e[0x1d]=0; /* A48D: checked after AI changed facing. */
}
/* 5059 ->A50B: hidden fixed floor trap, one77 emission then48-tick wait. */
void dungeon_floor_trap_behavior(u8 *e,u16 room,u16 slot)
{
    u16 state=e[1];
    if(!state)
    { if(!place_fixed_actor(e,room,slot,57)) return;e[8]=0x15;e[9]=0x97;e[3]&=252;e[1]=2;return; }
    if(state==2) { if(world_hero_zero_floor()) e[1]=4;return; }
    if(state==4) { create_projectile_type(e,0x77);e[4]=48;e[1]=6;return; }
    if(state==6 && !e[4]) e[1]=2;
}
extern const u8 dungeon_floor_shot[];
/* 505F ->A566:5F wandering close attack;60 aimed pursuit and close attack. */
void dungeon_melee_behavior(u8 *e,const u8 *tilemap,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 slot,const u8 *roll)
{
    u16 state=e[1],direction,dx,dy;const u8 *sequence=actor_mobile_sequences;
    if(!state)
    { if(dungeon_phase_spawn(e,cells,hero_x,hero_y,frame,slot,roll)) { e[8]=0xfa;e[9]=0x84;e[13]=10;e[12]=4;e[1]=2; }return; }
    if(state==2 || state==10)
    {
        if(e[11]!=3) return;
        if(state==10) e[10]^=1;
        e[11]=0;e[8]=0x49;e[9]=0x97;e[13]=16;e[12]=2;e[1]=4;
        if(state==10) return;state=4;
    }
    if(state==4)
    { direction=dungeon_phase_roll(roll,2)&3;if(ground_blocked(e,tilemap,direction)) return;e[10]=direction;state=6; }
    if(state==6)
    { e[4]=sequence[0];memcpy(e+0x14,sequence+1+e[10]*4,4);e[1]=8;return; }
    if(state==12 && !e[4]) { e[1]=ground_blocked(e,tilemap,e[10])?4:6;return; }
    if(state!=8 || e[4]) return;
    if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
    dx=hero_x>=e[0x13]?hero_x-e[0x13]:e[0x13]-hero_x;
    dy=hero_y>=e[0x11]?hero_y-e[0x11]:e[0x11]-hero_y;
    if(e[0]==0x5f)
    {
        if((dungeon_phase_roll(roll,3)&15)<6) { e[1]=6;return; }
        if(dx>=24) { e[1]=4;return; }
        if(dy>=24) { e[1]=6;return; }
    }
    else
    {
        if(dx!=dy)
        { direction=dy<dx?(hero_x<e[0x13]?2:3):(hero_y<e[0x11]?0:1);if(!ground_blocked(e,tilemap,direction)) e[10]=direction; }
        if(ground_blocked(e,tilemap,e[10])) { e[1]=4;return; }
        if(dx>=24 || dy>=24)
        { e[4]=sequence[0];memcpy(e+0x14,sequence+1+e[10]*4,4);e[1]=12;return; }
    }
    memset(e+0x14,0,4);e[11]=0;e[13]=11;e[12]=4;e[8]=0xd9;e[9]=0x97;e[1]=10;
}
/* 5065 ->A6C7: fixed horizontal61/vertical62 patrol, reverse on96 steps or wall. */
void dungeon_patrol_behavior(u8 *e,const u8 *tilemap,u16 room,u16 slot)
{
    u16 state=e[1];
    if(!state)
    { if(!place_fixed_actor(e,room,slot,57)) return;e[8]=0x55;e[9]=0x98;e[13]=6;e[12]=2;e[1]=2;state=2; }
    if(state==2)
    { e[8]=0x55;e[9]=0x98;e[13]=6;e[12]=2;e[10]=e[0]==0x62?1:3;e[1]=4;state=4; }
    if(state==4)
    {
        static const u8 velocity[]={0x00,0xfe,0,0,0,2,0,0,0,0,0,0xfe,0,0,0,2};
        e[4]=4;memcpy(e+0x14,velocity+e[10]*4,4);e[1]=6;return;
    }
    if(state==6 && !e[4])
    {
        if(ground_blocked(e,tilemap,e[10]) || ++e[0x20]==96) { e[0x20]=0;e[10]^=1; }
        e[1]=4;
    }
}
/* 5071 -> A86D: core movement, eight satellites, vulnerability and orbit.
 * Explicit random inputs allow comparison with the original state routines. */
void second_boss_behavior(u8 *e,u16 hero_x,u16 hero_y,u8 select,u8 turn,u8 gate,u8 pause)
{
    u16 state=e[1],n,count=0,phase;u8 a,b;bool move=FALSE;
    if(!state)
    {
        e[3]|=1;e[0x13]=128;e[0x11]=80;e[8]=2;e[9]=0x9a;e[0x2b]=8;e[5]=48;e[1]=2;
        state=2; /* A877 falls through A897, whose flash guard now returns. */
    }
    if(state==2 && !e[5])
    {
        for(n=0;n<8;n++) { u8 *sat=world_actor_state+(8+n)*48;sat[0]=0x66;sat[0x29]=(7-n)*32; }
        e[13]=e[12]=2;e[0x28]=e[0x2a]=0;e[0x2e]=20;e[1]=4;
    }
    else if(state==4) move=TRUE;
    else if(state==6 && !e[4])
    {
        if(e[0x2e]) { --e[0x2e];move=TRUE; }
        else if(gate>=8) move=TRUE;
        else
        {
            memset(e+0x14,0,4);e[0x2f]=(pause&63)+64;e[1]=8;
            --e[0x2f]; /* A93E falls through A942 in the same call. */
        }
    }
    else if(state==8 && !--e[0x2f]) { e[0x2e]=20;e[1]=4; }
    if(move)
    {
        const u8 *data=e[0x2b]?second_boss_slow:second_boss_fast;
        e[0x20]=second_boss_direction(e,hero_x,hero_y,select,turn);
        e[4]=data[0];data+=1+e[0x20]*5;memcpy(e+0x14,data,4);e[10]=data[4];e[1]=6;
    }
    /* Wrapper 5077 executes after every state, including flash/idle returns. */
    for(n=8;n<16;n++) if(world_actor_state[n*48]) ++count;
    e[0x2b]=count;e[3]&=253;if(!count) e[3]|=2;
    a=e[0x28];
    if(!e[0x2a]) { ++a;if(a>=32) e[0x2a]=1;else e[0x28]=a; }
    else { --a;if(a<16) e[0x2a]=0;else e[0x28]=a; }
    e[0x29]+=count<4?4:2;phase=e[0x29];
    a=flying_offset(phase+64,e[0x28]);b=flying_offset(phase,e[0x28]);
    world_actor_state[8*48+0x20]=a;world_actor_state[14*48+0x21]=a;
    world_actor_state[10*48+0x21]=-a;world_actor_state[12*48+0x20]=-a;
    world_actor_state[8*48+0x21]=b;world_actor_state[10*48+0x20]=b;
    world_actor_state[12*48+0x21]=-b;world_actor_state[14*48+0x20]=-b;
    a=flying_offset(phase+96,e[0x28]);b=flying_offset(phase+32,e[0x28]);
    world_actor_state[9*48+0x20]=a;world_actor_state[15*48+0x21]=a;
    world_actor_state[13*48+0x20]=-a;world_actor_state[11*48+0x21]=-a;
    world_actor_state[9*48+0x21]=b;world_actor_state[11*48+0x20]=b;
    world_actor_state[13*48+0x21]=-b;world_actor_state[15*48+0x20]=-b;
}
/* 512B: satellites inherit the core center, wrap coordinates, and hide outside. */
void second_boss_satellite_behavior(u8 *e)
{
    if(!e[1])
    { e[3]|=0x23;e[8]=0x4a;e[9]=0x9a;e[13]=4;e[12]=2;e[0x18]=12;e[0x19]=10;e[1]=2; }
    e[3]|=3;e[0x11]=world_actor_state[0x11]+e[0x21];e[0x13]=world_actor_state[0x13]+e[0x20];
    if(e[0x11]<17 || e[0x11]>=152 || e[0x13]<25 || e[0x13]>=232) e[3]&=252;
}
/* 9730..983E: fixed-center expanding orbit, asymmetric facing and shot1C. */
static void orbit_behavior(u8 *e,u16 hero_x)
{
    u16 phase;
    if(!e[1])
    {
        e[3]|=3;e[0x13]=128;e[0x11]=81;e[8]=0xfa;e[9]=0x84;e[13]=10;e[12]=4;e[1]=2;return;
    }
    if(e[1]==2)
    {
        if(e[11]!=3) return;
        e[11]=0;e[0x26]=e[0x13];e[0x28]=e[0x11];
        e[8]=0x42;e[9]=0x8e;e[13]=7;e[12]=2;memset(e+0x21,0,4);e[1]=4;return;
    }
    if(e[1]==4)
    {
        if(e[0x2a]!=96) e[0x2a]++;
        phase=e[0x29];e[0x13]=e[0x26]+flying_offset(phase+64,e[0x2a]);
        if(e[0x2b]!=56) e[0x2b]++;
        e[0x11]=e[0x28]+flying_offset(phase,e[0x2b]);e[0x29]++;
        e[10]=actor_orbit_facing[((e[0x29]-32)&192)>>6];
        if((random()&127)!=127) return;
        e[8]=0x7e;e[9]=0x8e;e[11]=0;e[13]=0;e[12]=0;
        e[10]=hero_x>=e[0x13]?3:e[0x13]-hero_x<48?0:2;e[1]=6;e[4]=24;return;
    }
    if(e[1]==6 && !e[4]) { create_projectile_type(e,0x1c);e[4]=16;e[1]=8;return; }
    if(e[1]==8 && !e[4]) { e[8]=0x42;e[9]=0x8e;e[13]=7;e[12]=2;e[1]=4; }
}
/* 85FB..8755: moving center plus growing sinusoidal orbit, then optional shot. */
static void flying_behavior(u8 *e,u16 hero_x,u16 hero_y,u16 slot)
{
    u16 phase,acceleration;
    if(e[1]==2)
    {
        u16 index=16+slot;
        if(e[11]!=3) return;
        e[11]=0;e[0x26]=e[0x13];e[0x28]=e[0x11];
        e[8]=0xee;e[9]=0x85;e[13]=5;e[12]=2;
        e[0x29]=(index>>3)|(index<<5);
        memset(e+0x21,0,4);e[1]=4;return;
    }
    if(e[1]!=4) return;
    acceleration=actor_flying_acceleration[(e[0]-0x23)*2]|((u16)actor_flying_acceleration[(e[0]-0x23)*2+1]<<8);
    flying_axis(e,hero_x,0x13,0x21,0x25,192,acceleration);
    flying_axis(e,hero_y,0x11,0x23,0x27,88,acceleration);
    if(e[0x2a]!=16) e[0x2a]++;
    if(e[0x2b]!=12) e[0x2b]++;
    phase=e[0x29];e[0x13]=e[0x26]+flying_offset(phase+64,e[0x2a]);
    e[0x11]=e[0x28]+flying_offset(phase,e[0x2b]);
    e[0x29]+=5;phase=((e[0x29]-32)&192)>>6;e[10]=actor_flying_facing[phase];
    if(e[0]!=0x23 && !e[4])
    {
        /* 8732/8741 call4965 directly, without the495E overflow guard. */
        create_projectile_type(e,e[0]==0x24?0x13:0x15);e[4]=128;
    }
}

/* 87DE/8893: types29/2A and the type2B terrain modifier. */
extern const u8 actor_mobile_sequences[];
extern void replace_world_actor_cell(u16 x,u16 y,u16 cell);
static bool mobile_choose_direction(u8 *entity,const u8 *tilemap)
{
    u16 direction=random()&3;
    if(ground_blocked(entity,tilemap,direction)) return FALSE;
    entity[10]=direction;return TRUE;
}
static bool mobile_align_hero(u8 *entity,u16 hero_x,u16 hero_y)
{
    if((entity[0x13]&240)==(hero_x&240)) entity[10]=hero_y<entity[0x11]?0:1;
    else if((entity[0x11]&240)==(hero_y&240)) entity[10]=hero_x<entity[0x13]?2:3;
    else return FALSE;
    return TRUE;
}
static void mobile_behavior(u8 *entity,const u8 *tilemap,const u8 *cells,u16 hero_x,u16 hero_y)
{
    u16 state=entity[1],type=entity[0],choice;
    if(state==2)
    {
        if(entity[11]!=3) return;
        entity[11]=0;entity[13]=10;entity[12]=2;entity[1]=state=4;
        if(type!=0x2b) return; /* 87EC returns; 88A1 falls through. */
    }
    if(state==4)
    {
        entity[8]=type==0x2b?0x2c:0x48;entity[9]=type==0x2b?0x87:0x86;
        if(!mobile_choose_direction(entity,tilemap)) return;
        if(type!=0x2b && ground_blocked(entity,tilemap,entity[10]) && !mobile_choose_direction(entity,tilemap)) return;
        state=6;
    }
    if(state==6)
    {
        if(type!=0x2b && ground_blocked(entity,tilemap,entity[10]) && !mobile_choose_direction(entity,tilemap)) return;
        const u8 *sequence=actor_mobile_sequences+(type==0x2a?17:0);
        entity[4]=sequence[0];memcpy(entity+0x14,sequence+1+entity[10]*4,4);
        entity[1]=8;return;
    }
    if(state==8 && !entity[4])
    {
        if(ground_blocked(entity,tilemap,entity[10])) { entity[1]=4;return; }
        choice=random()&15;
        if(choice<(type==0x2b?4:2)) { entity[1]=4;return; }
        if(choice<(type==0x2b?14:8)) { entity[1]=6;return; }
        if(type==0x2b)
        {
            u16 x=(entity[0x13]-8)&255,y=(entity[0x11]-16)&255,cell=(y&240)|(x>>4);
            if(cell>=160 || cells[cell]!=3 || !(entity[0x13]&8) || (entity[0x11]&8)) { entity[1]=6;return; }
            replace_world_actor_cell(x,y,0x66);entity[8]=0x56;entity[9]=0x87;
            memset(entity+0x14,0,4);entity[4]=32;entity[1]=10;return;
        }
        if(!mobile_align_hero(entity,hero_x,hero_y) || type==0x29) { entity[1]=6;return; }
        memset(entity+0x14,0,4);entity[4]=16;entity[1]=10;return;
    }
    if(state==10 && !entity[4])
    {
        if(type==0x2a) { create_guarded_projectile_type(entity,0x17);entity[8]=0xd8;entity[9]=0x86; }
        entity[4]=16;entity[1]=12;return;
    }
    if(state==12 && !entity[4]) entity[1]=4;
}

/* 854B..85D5: walking, alignment to the hero, windup and firing recovery. */
static void ranged_behavior(u8 *entity,const u8 *tilemap,u16 hero_x,u16 hero_y)
{
    u16 state=entity[1];
    if(state==2)
    {
        if(entity[11]!=3) return;
        entity[11]=0;entity[8]=0x2e;entity[9]=0x85;
        entity[13]=10;entity[12]=2;entity[1]=state=4;
    }
    if(state==4)
    {
        u16 direction=random()&3;
        if(ground_blocked(entity,tilemap,direction)) return;
        entity[10]=direction;state=6;
    }
    if(state==6)
    {
        const u8 *sequence=actor_ground_sequences+17;
        entity[4]=sequence[0];memcpy(entity+0x14,sequence+1+entity[10]*4,4);
        entity[1]=8;return;
    }
    if(state==8)
    {
        u16 choice;
        if(entity[4]) return;
        if(ground_blocked(entity,tilemap,entity[10])) { entity[1]=4;return; }
        choice=random()&15;
        if(choice<2) { entity[1]=4;return; }
        if(choice<8) { entity[1]=6;return; }
        if((entity[0x13]&240)==(hero_x&240)) entity[10]=hero_y<entity[0x11]?0:1;
        else if((entity[0x11]&240)==(hero_y&240)) entity[10]=hero_x<entity[0x13]?2:3;
        else { entity[1]=6;return; }
        memset(entity+0x14,0,4);entity[4]=16;entity[1]=10;return;
    }
    if(state==10 && !entity[4])
    { create_projectile(entity);entity[4]=8;entity[1]=12;return; }
    if(state==12 && !entity[4]) entity[1]=4;
}

/* 3F07: octant choice and fixed-point velocity, also used by homing1C. */
static void aim_velocity(u8 *e,const u8 *vectors,u16 hero_x,u16 hero_y)
{
    u16 octant=2,dx,dy;
    if(hero_x<e[0x13]) { dx=e[0x13]-hero_x;octant|=4; } else dx=hero_x-e[0x13];
    if(hero_y<e[0x11]) { dy=e[0x11]-hero_y;octant&=~2; } else dy=hero_y-e[0x11];
    if(dy<dx) octant++;
    e[10]=actor_aimed_projectile_facing[octant];
    memcpy(e+0x16,vectors+octant*4,2);memcpy(e+0x14,vectors+2+octant*4,2);
}
static void aim_projectile(u8 *e,const u8 *data,u16 hero_x,u16 hero_y)
{
    e[8]=data[0];e[9]=data[1];e[0x19]=data[2];e[0x11]+=data[3];e[12]=data[4];e[13]=data[5];
    aim_velocity(e,data+6,hero_x,hero_y);
}
extern const u8 charging_boss_walk[],charging_boss_vectors[],charging_boss_facing[],charging_boss_chase[];
static u8 charging_boss_roll(const u8 *roll,u16 n) { return roll?roll[n]:(u8)random(); }
/* 577F with BC=0: pursue on permitted axes, preserving the source lookup. */
static s16 charging_boss_chase_direction(const u8 *e,u16 hero_x,u16 hero_y)
{
    u16 d=0,x=e[0x13],y=e[0x11];
    if(hero_x!=x) d|=hero_x<x?2:3;
    if(hero_y!=y) d|=hero_y<y?8:12;
    if((d&2) && ((!(d&1) && x<49) || ((d&1) && x>=208))) d&=~2;
    if((d&8) && ((!(d&4) && y<49) || ((d&4) && y>=136))) d&=~8;
    return d&10?charging_boss_chase[d]:-1;
}
static void charging_boss_reset(u8 *e)
{ e[11]=0;e[8]=0x6a;e[9]=0x9b;e[13]=20;e[12]=2;e[10]=1;e[0x25]=13;e[1]=2; }
static void charging_boss_launch(u8 *e,u16 hero_x,u16 hero_y,const u8 *roll)
{
    if((charging_boss_roll(roll,1)&15)<8) aim_velocity(e,charging_boss_vectors,hero_x,hero_y);
    else
    {
        const u8 *v=charging_boss_vectors+e[0x20]*4;
        memcpy(e+0x16,v,2);memcpy(e+0x14,v+2,2);e[10]=charging_boss_facing[e[0x20]];
    }
    e[0x21]=128;e[1]=18;e[4]=32;
}
/* 51AE: types68/69 and later 7A/7B variants. Optional explicit random inputs
 * are for comparison; production passes NULL and samples only executed sites. */
void charging_boss_behavior(u8 *e,u16 hero_x,u16 hero_y,const u8 *roll,u8 inherited_e)
{
    u16 state=e[1],choice,boundary=inherited_e; s16 direction;
    static const u8 rebounds[16]={3,6,2,7,4,0,5,1,0,3,1,2,5,4,7,6};
    if(!state)
    {
        e[3]|=3;e[0x13]=128;e[0x11]=56;e[5]=e[4]=64;charging_boss_reset(e);return;
    }
    if(state==2 && e[4]) return;
    if(state==2 || state==4)
    {
        if(state==2) e[1]=4;
        direction=charging_boss_chase_direction(e,hero_x,hero_y);
        if(direction<0) goto attack_choice;
        e[0x22]=direction;state=6;
    }
    if(state==6)
    {
        e[4]=charging_boss_walk[0];memcpy(e+0x14,charging_boss_walk+1+e[0x22]*4,4);e[1]=8;return;
    }
    if(state==8)
    {
        if(e[4]) return;
attack_choice:
        e[1]=4;choice=charging_boss_roll(roll,3);if(choice>=32) return;
        memset(e+0x14,0,4);e[11]=0;
        if((e[0]==0x69 || e[0]==0x7b) && (choice&15)<6)
        { e[13]=e[12]=0;e[8]=0xae;e[9]=0x9c;e[4]=26;e[1]=14; }
        else { e[8]=0xd6;e[9]=0x9b;e[13]=4;e[12]=2;e[4]=8;e[1]=10; }
        return;
    }
    if(state==10)
    {
        if(!e[4]) { e[11]=0;e[8]=0x39;e[9]=0x9c;e[13]=e[12]=2;e[4]=24;e[1]=12; }
        return;
    }
    if(state==12) { if(!e[4]) charging_boss_reset(e);return; }
    if(state==14)
    { if(!e[4]) { e[8]=0xe8;e[9]=0x9c;e[13]=1;e[12]=2;e[1]=16; }return; }
    if(state==16)
    { e[0x20]=charging_boss_roll(roll,0)&7;charging_boss_launch(e,hero_x,hero_y,roll);return; }
    if(state!=18) return;
    if(e[0x11]<56) boundary=0;
    else if(e[0x11]>=144) boundary=1;
    else if(e[0x13]<48) boundary=2;
    else if(e[0x13]>=208) boundary=3;
    else
    {
        if(e[4]) return;
        if(--e[0x21]) { e[4]=32;return; }
        /* Source retains caller E on this degenerate interior expiry route.
         * Ordinary charges encounter a boundary long before 128 segments. */
    }
    if(!--e[0x25])
    {
        e[0x11]&=248;e[0x13]&=248;e[0x10]=e[0x12]=e[4]=0;memset(e+0x14,0,4);
        charging_boss_reset(e);return;
    }
    e[0x20]=rebounds[(boundary&3)*4+((charging_boss_roll(roll,2)&15)>>2)];
    charging_boss_launch(e,hero_x,hero_y,roll);
}
extern const u8 sword_boss_walk[],sword_boss_shot[],sword_boss_paths[];
/* 54D9: type6C's ten states, including shared recovery and satellite states. */
void sword_boss_behavior(u8 *e,u16 hero_x,u16 hero_y,const u8 *roll)
{
    u16 state=e[1],n;s16 direction;u8 *last=NULL;
    if(!state)
    {
        e[0x13]=128;e[0x11]=72;e[5]=64;e[3]|=2;e[10]=1;
reset_walk:
        e[4]=64;e[8]=0x28;e[9]=0x9e;e[13]=16;e[12]=4;e[1]=2;return;
    }
    if(state==2) { if(!e[4]) e[1]=4;return; }
    if(state==4)
    {
        direction=charging_boss_chase_direction(e,hero_x,hero_y);
        if(direction<0) goto attack;
        e[0x22]=direction;state=6;
    }
    if(state==6)
    { e[4]=sword_boss_walk[0];memcpy(e+0x14,sword_boss_walk+1+e[0x22]*4,4);e[1]=8;return; }
    if(state==8)
    {
        if(e[4]) return;
attack:
        e[1]=4;if((charging_boss_roll(roll,0)&15)>=4) return;
        e[1]=10;e[0x23]=0;memset(e+0x14,0,4);e[11]=e[13]=e[12]=0;
        e[8]=0xe3;e[9]=0x9e;e[4]=32;return;
    }
    if(state==10)
    {
        if(!e[4]) { e[11]=0;e[8]=0xed;e[9]=0x9e;e[13]=8;e[12]=3;e[4]=22;e[1]=12; }
        return;
    }
    if(state==12)
    {
        if(e[4]) return;
        e[1]=10;e[11]=e[13]=e[12]=0;e[8]=0xe3;e[9]=0x9e;
        create_projectile_type(e,0x75);e[4]=32;
        if(++e[0x23]==2) goto reset_walk;
        return;
    }
    if(state==14)
    { e[0x13]=128;e[0x11]=72;e[10]=1;e[8]=0x28;e[9]=0x9e;e[5]=64;e[1]=2;return; }
    if(state==16)
    {
        if(e[11]!=2) return;
        direction=charging_boss_roll(roll,1)&3;
        for(n=4;n;n--)
        {
            u8 *shot=create_projectile_type(e,0x76);if(shot) last=shot;
            if(last) { last[0x21]=n-1;last[0x20]=direction; }
        }
        e[8]=0x14;e[9]=0xa0;e[13]=e[12]=e[11]=0;e[4]=112;e[1]=18;return;
    }
    if(state==18 && !e[4])
    { for(n=8;n<16;n++) if(world_actor_state[n*48]) return;e[1]=4; }
}
/* 55F1/560A: type6D shares recovery and satellite entries with54D9. */
static void final_boss_state(u8 *e,u16 hero_x,u16 hero_y,const u8 *roll)
{
    u16 state=e[1],choice;s16 direction;
    if(!state || state==14)
    { e[0x13]=128;e[0x11]=72;e[10]=1;e[8]=0x28;e[9]=0x9e;e[5]=64;e[1]=2;return; }
    if(state==2)
    { if(e[5]) return;e[3]|=2;state=4;e[1]=4; }
    if(state==4)
    { e[8]=0x28;e[9]=0x9e;e[11]=e[14]=0;e[1]=6;state=6; }
    if(state==6)
    {
        direction=charging_boss_chase_direction(e,hero_x,(hero_y-16)&255);
        if(direction<0) return;
        e[0x22]=direction;memcpy(e+0x14,sword_boss_walk+1+direction*4,4);
        e[13]=12;e[12]=4;e[4]=64;e[1]=8;return;
    }
    if(state==8)
    {
        if(e[4]) return;
        memset(e+0x14,0,4);choice=charging_boss_roll(roll,0)&15;
        if(choice<4)
        { e[8]=0xa9;e[9]=0x9f;e[11]=e[14]=0;e[13]=12;e[12]=3;e[1]=16;return; }
        if(choice>=12 || ((hero_y-16)&255)<e[0x11]) { e[1]=6;return; }
        e[11]=e[13]=e[12]=0;e[8]=0xe3;e[9]=0x9e;e[0x23]=3;e[4]=32;e[1]=10;return;
    }
    if(state==10)
    { if(!e[4]) { e[8]=0xed;e[9]=0x9e;e[13]=8;e[12]=3;e[4]=18;e[1]=12; }return; }
    if(state==12)
    {
        if(e[4]) return;
        e[11]=e[13]=e[12]=0;e[8]=0xe3;e[9]=0x9e;create_projectile_type(e,0x75);
        e[4]=20;e[1]=10;if(!--e[0x23]) e[1]=18;return;
    }
    if(state==16 || state==18) sword_boss_behavior(e,hero_x,hero_y,roll);
}
void final_boss_behavior(u8 *e,u16 hero_x,u16 hero_y,const u8 *roll,bool weapon_valid)
{
    final_boss_state(e,hero_x,hero_y,roll);
    /* Runs after every state routine and before generic hurt27A2. */
    if(!weapon_valid) e[0x1d]=0;
}
extern bool world_final_boss_weapon_valid(void);
/* 45C4: byte-coordinate attraction, with the source signed-high-byte cap. */
static void sword_shot_attract(u8 *e,u16 x,u16 y,u16 acceleration)
{
    u16 axis;
    for(axis=0;axis<2;axis++)
    {
        u16 at=axis?0x16:0x14,target=axis?x:y;
        u16 velocity=(e[at]|((u16)e[at+1]<<8))+(e[at-3]<target?acceleration:-acceleration);
        u16 high=velocity>>8;if(high&128) high=(0-high)&255;
        if(high<3) { e[at]=velocity;e[at+1]=velocity>>8; }
    }
}
/* 4518: shot75 homes on hero, bounces, then returns to its parent. The common
 * tail runs even after the state routine clears the record, as on SMS. */
void sword_boss_projectile_behavior(u8 *e,u16 hero_x,u16 hero_y)
{
    u16 state=e[1],axis;
    if(!state)
    { e[0x21]=0;e[0x22]=192;aim_projectile(e,sword_boss_shot,hero_x,hero_y);e[1]=2;e[4]=96;e[3]=0x13; }
    else if(state==2 && !e[0x21]) sword_shot_attract(e,hero_x,hero_y,32);
    else if(state==2 || state==4)
    {
        u16 close=0;e[1]=4;
        sword_shot_attract(e,world_actor_state[0x13],world_actor_state[0x11],48);
        for(axis=0;axis<2;axis++)
        {
            u16 at=axis?0x16:0x14,coordinate=e[at-3],parent=world_actor_state[at-3];
            u16 velocity=e[at]|((u16)e[at+1]<<8),diff=(coordinate-parent)&255;
            if((!(velocity&0x8000) && coordinate<parent && diff>=(axis?240:232)) ||
               ((velocity&0x8000) && coordinate>=parent && diff<(axis?16:24)))
            { velocity+=(velocity&0x8000)?24:-24;e[at]=velocity;e[at+1]=velocity>>8;close++; }
        }
        if(close==2) memset(e,0,48);
    }
    e[4]=8;
    for(axis=0;axis<2;axis++)
    {
        u16 at=axis?0x16:0x14,coordinate=e[at-3],velocity=e[at]|((u16)e[at+1]<<8);
        if((coordinate<(axis?40:32) && (velocity&0x8000)) ||
           (coordinate>=(axis?216:144) && !(velocity&0x8000)))
        { velocity=-velocity;e[at]=velocity;e[at+1]=velocity>>8;e[0x21]=1; }
    }
    if((e[3]&4) || e[0x22]<48) e[0x21]=1;
    if(!--e[0x22]) memset(e,0,48);
}
/* 46B4: satellite76 follows an original relative path and its animation. */
void sword_boss_satellite_behavior(u8 *e)
{
    u16 state=e[1],offset,position;
    if(!state)
    { e[0x19]=28;e[3]=0x13;e[8]=0xa4;e[9]=0xa0;e[13]=6;e[12]=4;e[0x22]=0;state=2;e[1]=2; }
    if(state==2)
    {
        e[11]=e[14]=0;offset=e[0x20]*8+e[0x21]*2;
        offset=sword_boss_paths[offset]|((u16)sword_boss_paths[offset+1]<<8);
        offset=offset-0x4745+e[0x22]*2;
        if(sword_boss_paths[offset]==255) { memset(e,0,48);return; }
        position=(world_actor_state[0x13]+sword_boss_paths[offset])&255;e[0x13]=position;
        if(position<25 || position>=232) { memset(e,0,48);return; }
        position=(world_actor_state[0x11]+sword_boss_paths[offset+1])&255;e[0x11]=position;
        if(position<25 || position>=145) { memset(e,0,48);return; }
        e[1]=4;
    }
    if(state==2 || state==4)
    {
        if((u8)(e[11]+1)<e[12] || (u8)(e[14]+1)<e[13]) return;
        e[14]--;e[0x22]++;e[1]=2;
    }
}
extern const u8 actor_homing_template[];
/* 40F0..415B: eight16-tick aimed segments, one selection tick between them. */
static void homing_projectile_behavior(u8 *e,u16 hero_x,u16 hero_y)
{
    if(!e[1])
    {
        const u8 *data=actor_homing_template;
        e[8]=data[0];e[9]=data[1];e[0x19]=data[2];e[0x11]+=data[3];e[12]=data[4];e[13]=data[5];
        e[0x20]=8;e[1]=2;e[3]=3;
    }
    if(e[1]==2)
    { aim_velocity(e,actor_homing_template+6,hero_x,hero_y);e[1]=4;e[4]=16;return; }
    if(e[1]==4 && !e[4])
    {
        if(e[0x11]<8 || e[0x11]>=160 || e[0x13]<8 || e[0x13]>=248 || !--e[0x20])
        { memset(e,0,0x30);return; }
        e[1]=2;
    }
}
/* 42B4..4365: projectile1F, repeated parabolic hops and exterior bounds. */
static void bouncing_projectile_behavior(u8 *e,u16 hero_x,u16 hero_y)
{
    u16 state=e[1];
    if(!state)
    {
        actor_put_word(e,0x2e,0xffd8);e[3]|=3;e[0x23]=e[0x13];e[0x27]=e[0x11];e[1]=state=2;
    }
    if(state==2)
    {
        aim_projectile(e,actor_aimed_projectile_templates+152,hero_x,hero_y);
        actor_put_word(e,0x20,actor_word(e,0x16));actor_put_word(e,0x24,actor_word(e,0x14));state=4;
    }
    if(state==4)
    { actor_put_word(e,0x28,528);e[4]=96;e[1]=6;integrate_ballistic_actor(e,actor_word(e,0x2e));return; }
    if(state!=6) return;
    if(e[0x11]<8 || e[0x11]>=160 || e[0x13]<8 || e[0x13]>=248 || !e[4])
    { memset(e,0,0x30);return; }
    if(actor_word(e,0x2a)) integrate_ballistic_actor(e,actor_word(e,0x2e));
    else e[1]=4;
}

/* 3DA5/3E69/3E8C: initialize a projectile, then cull at boundaries/lifetime.
 * Exterior class is handled here; dungeon projectile bounds remain pending. */
static void projectile_behavior(u8 *entity,const u8 *tilemap,u16 hero_x,u16 hero_y,u16 frame,u16 slot)
{
    u16 type=entity[0];
    if(!entity[1])
    {
        if(type==0x72 || type==0x13 || type==0x14 || type==0x15 || type==0x1e)
        {
            const u8 *data=type==0x72?first_boss_aimed:actor_aimed_projectile_templates+(type==0x1e?114:type==0x14?76:type==0x15?38:0);
            aim_projectile(entity,data,hero_x,hero_y);
            entity[1]=2;entity[4]=96;entity[3]=0x13;
            if(type==0x72 && (slot==9 || slot==10))
            { entity[0x17]+=slot==9?-1:1;entity[0x14]-=0x40; }
            return;
        }
        const u8 *data=type==0x77?dungeon_floor_shot:type==0x71?dungeon_emitter_shot:type==0x18?dungeon_hunter_shot:type==0x73?first_boss_fan:actor_projectile_templates+(type==0x70?9:type==0x1b?8:type==0x1a?7:type==0x19?5+(frame&1):type==0x16?4:type==0x17?3:type-0x10)*22;
        entity[8]=data[0];entity[9]=data[1];entity[0x19]=data[2];
        entity[0x11]+=data[3];entity[12]=data[4];entity[13]=data[5];
        memcpy(entity+0x14,data+6+entity[10]*4,4);
        if(type==0x73) entity[10]=1;
        entity[1]=2;entity[4]=128;entity[3]=0x13;return;
    }
    if(type==0x1b)
    {
        u16 offset=(((entity[0x11]-4)&248)*8)+((entity[0x13]>>2)&62);
        if(tilemap[offset+1]&128) { memset(entity,0,0x30);return; }
    }
    if(entity[0x11]<(actor_room_class==1?32:8) || entity[0x11]>=(actor_room_class==1?136:152) ||
       entity[0x13]<(actor_room_class==1?32:8) || entity[0x13]>=(actor_room_class==1?224:248) ||
       !entity[4]) memset(entity,0,0x30);
    if(type==0x12)
    {
        u16 phase=entity[14]+1;
        if(phase>=2) phase=0;
        entity[14]=phase;
        if(!phase) { phase=entity[11]+1;entity[11]=phase>=4?1:phase; }
    }
}

/* 47F7/4804/4821: edge-directed77, independent28..131/28..227 bounds. */
void dungeon_floor_shot_behavior(u8 *e)
{
    if(!e[1])
    {
        e[10]=e[0x11]<33?1:e[0x13]==32?3:2;
        projectile_behavior(e,NULL,0,0,0,0);return;
    }
    if(e[0x11]<28 || e[0x11]>=132 || e[0x13]<28 || e[0x13]>=228 || !e[4]) memset(e,0,48);
}
extern const u8 burst_boss_shot_template[],burst_boss_shot_facing[];
/* 4457: burst74 stops, then type6A flashes out; other parents release it. */
void burst_boss_projectile_behavior(u8 *e)
{
    u16 state=e[1];
    if(!state)
    {
        const u8 *data=burst_boss_shot_template;u16 direction=e[10];
        e[8]=data[0];e[9]=data[1];e[0x19]=data[2];e[0x11]+=data[3];e[12]=data[4];e[13]=data[5];
        memcpy(e+0x14,data+6+direction*4,4);e[10]=burst_boss_shot_facing[direction];
        e[3]=0x13;e[4]=12;e[1]=2;return;
    }
    if(state==2) { if(!e[4]) { e[0x22]=24;e[1]=4; }return; }
    if(state==4)
    {
        if(--e[0x22]) return;
        if(world_actor_state[0]==0x6a) { e[0x22]=32;e[1]=8; }
        else { e[8]=0x48;e[9]=0xa0;e[13]=e[12]=0;e[4]=96;e[1]=6; }
        return;
    }
    if(state==6) { projectile_behavior(e,NULL,0,0,0,0);return; }
    if(state==8) { if(!--e[0x22]) { e[5]=e[0x22]=56;e[1]=10; }return; }
    if(state==10 && !--e[0x22]) memset(e,0,48);
}

static u16 attacking_hero_x,attacking_hero_y,attacking_hero_direction,attacking_hero_box,attacking_hero_strength;
static u16 *attacking_hero_flags;
void set_world_hero_attack(u16 x,u16 y,u16 direction,u16 box,u16 strength,u16 *flags)
{
    attacking_hero_x=x;attacking_hero_y=y;attacking_hero_direction=direction;
    attacking_hero_box=box;attacking_hero_strength=strength;attacking_hero_flags=flags;
}

/* 2346: room/transient entities scan C300 first on their parity slot. */
static void actor_hero_contact(u8 *entity,u16 slot,u16 frame)
{
    const u8 *box;u16 left,right,top,bottom,x,y,end,candidate; s16 damage;
    if(((frame^slot)&1) || entity[5] || !(entity[3]&2) || !entity[0x1b]) return;
    box=actor_collision_boxes+((entity[0x1b]*4)&255);
    left=(entity[0x13]+box[0])&255;right=(left+box[1])&255;
    top=(entity[0x11]+box[2])&255;bottom=(top+box[3])&255;
    /* 242D: enemies test source records C300..C480 in ascending order.
     * Currently the native hero and C330 fire are the active attack records. */
    for(candidate=0;candidate<2;candidate++)
    {
        u16 index,strength,tx,ty;
        if(!candidate)
        {
            if(!attacking_hero_flags || !(*attacking_hero_flags&2)) continue;
            index=attacking_hero_box;strength=attacking_hero_strength;
            tx=attacking_hero_x;ty=attacking_hero_y;
        }
        else
        {
            if(!world_spell_state[0] || world_spell_state[6] || !(world_spell_state[3]&2)) continue;
            index=world_spell_state[0x1c];strength=world_spell_state[0x19];
            tx=world_spell_state[0x13];ty=world_spell_state[0x11];
        }
        if(!index) continue;
        box=actor_collision_boxes+((index*4)&255);
        x=tx+box[0];if(x<256) continue;x&=255;if(x>=right) continue;
        end=x+box[1];if(end>=256 || end<left) continue;
        y=ty+box[2];if(y<256) continue;y&=255;if(y>=bottom) continue;
        end=y+box[3];if(end>=256 || end<top) continue;
        damage=(s16)strength-entity[0x1a];if(damage<=0) damage=2;
        entity[0x1d]+=damage;entity[0x1e]=candidate?0x30:0;entity[0x1f]=0xc3;
        if(candidate) world_spell_state[3]|=4;else *attacking_hero_flags|=4;
        return;
    }
}

/* 4C7E: surviving mode-2 ground enemies split into their paired transient slot. */
static void clone_hurt_actor(u8 *entity,u16 slot)
{
    u8 damage=entity[0x1d];u16 destination=8+(slot&7);
    if(!damage || entity[0x18]<=damage || entity[0x20]!=2) return;
    entity[0x20]--;
    if(world_actor_state[destination*0x30]) return;
    entity[0x1d]=0;memcpy(world_actor_state+destination*0x30,entity,0x21);entity[0x1d]=damage;
}

/* 2768/2803/2838..28E1: HP, hurt interval and terrain-limited knockback.
 * Death changes to source type 1; its particle handler uses the original drop tables. */
static void hurt_world_actor(u8 *entity,const u8 *tilemap)
{
    u16 damage=entity[0x1d],direction=entity[0x1e]==0x30?world_spell_state[10]:attacking_hero_direction,x,y,offset;
    static const s8 dx[4]={-8,-8,-16,8},dy[4]={-16,0,-8,-8};
    if(!damage) return;entity[0x1d]=0;
    if(!(entity[3]&0x60)) return;
    entity[0x18]=damage>=entity[0x18]?0:entity[0x18]-damage;
    if(!entity[0x18])
    {
        sound_effect((entity[3]&64)?0x9e:0xa0); /* 27C4/27FD */
        if(entity[3]&64) entity[0]=7;
        else { entity[7]=entity[0];entity[0]=1; }
        entity[1]=entity[6]=0;memset(entity+0x14,0,4);return;
    }
    sound_effect(0x9c);entity[5]=32; /* 2803: surviving hit. */
    if(!(entity[3]&8)) return;
    x=entity[0x13];y=entity[0x11];
    if(direction<2) { x=(x+4)&248;y=(y+(direction==1?7:0))&248; }
    else { y=(y+4)&248;x=(x+(direction==3?7:0))&248; }
    entity[0x13]=x;entity[0x11]=y;
    if(!((direction==0 && y<25) || (direction==1 && y>=136) ||
         (direction==2 && x<25) || (direction==3 && x>=232)))
    {
        u16 high;
        offset=(((y+dy[direction])&248)*8)+(((x+dx[direction])&248)>>2);
        high=tilemap[offset+1];if(direction<2) high|=tilemap[offset+3];
        if(!(high&0xa0))
        { if(direction<2) y+=direction?8:-8;else x+=direction==3?8:-8; }
    }
    entity[0x13]=x;entity[0x11]=y;entity[0x10]=entity[0x12]=entity[4]=0;memset(entity+0x14,0,4);
}

/* 4AFB/4B30: five explosion poses, then ROM drop threshold/class rules.
 * SGDK supplies the provisional random byte; reproducing 04E1/R is pending. */
static void death_particle_behavior(u8 *entity,u16 slot)
{
    u16 n;u8 chance,roll,type;
    if(!entity[1])
    {
        entity[3]|=1;entity[8]=0xcc;entity[9]=0x90;entity[13]=4;entity[12]=5;
        if(slot<15 && entity[0x30]==0x30) memset(entity+0x30,0,0x30);
        entity[11]=entity[14]=0;entity[0x1b]=entity[0x1c]=0;entity[1]=2;return;
    }
    if(entity[11]<4) return;
    if(!entity[7]) { memset(entity,0,0x30);return; }
    chance=actor_room_class;
    for(n=0;n<actor_drop_exceptions[0];n++)
        if(actor_drop_exceptions[1+n]==entity[7]) { chance=actor_drop_exceptions[1+actor_drop_exceptions[0]+n];break; }
    roll=(u8)random();n=((roll&0xe0)>>4)|(chance<<4);type=actor_drop_choices[n+1];
    if((roll&31)<actor_drop_choices[n])
    {
        for(n=0;n<7;n++) if(!world_loot_state[n*0x30]) break;
        if(n<7)
        {
            u8 *loot=world_loot_state+n*0x30;
            loot[0]=type;loot[1]=loot[3]=0;loot[0x11]=entity[0x11];loot[0x13]=entity[0x13];
        }
    }
    memset(entity,0,0x30);world_actor_count=(world_actor_count-1)&255;
}

/* 2907/2926/2939/2946 and 2ADD: dropped gold, HP, magic and enemy freeze. */
void tick_world_loot(u16 hero_state,u16 *gold,u16 *health,u16 max_health,u16 *magic,u16 max_magic,u16 *keys)
{
    u16 slot,n;
    for(slot=0;slot<7;slot++)
    {
        u8 *loot=world_loot_state+slot*0x30;u16 type=loot[0],value;
        if(type) world_object_tick_count++;
        if(type<8 || type>14) continue;
        if(!loot[1])
        {
            u16 tile=type==8?0x92:type==9?0x94:type==10?0xaa:type==14?0x96:0xbc;
            if(type>=11 && type<=13)
            {
                u16 style=type+0x10;
                if(world_loot_style && world_loot_style!=style) { memset(loot,0,0x30);continue; }
                if(!world_loot_style) { world_loot_style=style;world_loot_patterns_pending=type-10; }
            }
            loot[2]=tile;loot[8]=(type<10 || type==14)?0xce:0xe1;loot[9]=0x84;
            loot[13]=loot[12]=loot[11]=loot[0x1d]=0;loot[3]=1;loot[1]=2;
        }
        else if(loot[1]==2)
        { if(hero_state==1) { loot[3]|=2;if(type!=14) loot[14]=240;loot[1]=4; } }
        else if(loot[1]==4 && type!=14)
        { if(!--loot[14]) { loot[5]=120;loot[1]=6; } }
        else if(loot[1]==6 && !loot[5]) { memset(loot,0,0x30);continue; }
        if(loot[0x1d] || (loot[3]&4))
        {
            sound_effect(0x96); /* 2AEA: dropped item collected. */
            memset(loot,0,0x30);
            if(type<=9) { value=*gold+(type==8?1:5);*gold=value>255?255:value; }
            else if(type<=11) { value=*health+(type==10?8:24);*health=value>max_health?max_health:value; }
            else if(type==12) { value=*magic+8;*magic=value>max_magic?max_magic:value; }
            else if(type==14) { if(*keys<99) (*keys)++; }
            else for(n=0;n<16;n++) if(world_actor_state[n*0x30]>=0x20) world_actor_state[n*0x30+6]=255;
            continue;
        }
        value=(u8)(loot[5]-1);
        if(!(value&128)) { loot[5]=value;loot[3]|=1;if(value&2) loot[3]&=254; }
        if(loot[3]&1)
        {
            u16 table=loot[8]|((u16)loot[9]<<8);
            table=descriptor_word(table+loot[10]*2);table=descriptor_word(table+loot[11]*2);
            loot[0x1b]=actor_descriptors[(table&0x3fff)+1];loot[0x1c]=actor_descriptors[(table&0x3fff)+2];
        }
    }
}

/* Shared object tail 26E5..2753. Collision/damage dispatch remains pending. */
void tick_world_actors(const u8 *tilemap,const u8 *cells,u16 hero_x,u16 hero_y,u16 frame,u16 room)
{
    u16 slot;
    for(slot=0;slot<16;slot++)
    {
        u8 *entity=world_actor_state+slot*0x30;
        u8 counter;
        if(!entity[0]) continue;
        world_object_tick_count++;
        actor_hero_contact(entity,slot,frame);
        if(entity[6]) entity[6]--;
        else
        {
            if(entity[0]>=0x26 && entity[0]<=0x28)
                { ground_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot);clone_hurt_actor(entity,slot); }
            else if(entity[0]>=0x20 && entity[0]<=0x22)
            {
                if(!entity[1]) ground_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot);
                else ranged_behavior(entity,tilemap,hero_x,hero_y);
            }
            else if(entity[0]>=0x23 && entity[0]<=0x25)
            {
                if(!entity[1]) ground_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot);
                else flying_behavior(entity,hero_x,hero_y,slot);
            }
            else if(entity[0]>=0x29 && entity[0]<=0x2b)
            {
                if(!entity[1]) ground_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot);
                else mobile_behavior(entity,tilemap,cells,hero_x,hero_y);
            }
            else if(entity[0]==0x2c)
            {
                if(!entity[1]) ground_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot);
                else resting_behavior(entity,tilemap);
            }
            else if(entity[0]==0x2e || entity[0]==0x2f)
                emerging_shooter_behavior(entity,cells,hero_x,hero_y,frame,slot);
            else if(entity[0]==0x2d) fixed_shooter_behavior(entity,room,slot);
            else if(entity[0]==0x31 || entity[0]==0x32)
            {
                if(!entity[1]) ground_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot);
                else jumping_behavior(entity,tilemap,slot);
            }
            else if(entity[0]==0x30) shadow_behavior(entity,slot);
            else if(entity[0]==0x33 || entity[0]==0x34) water_jump_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot);
            else if(entity[0]==0x35) trap_walker_behavior(entity,tilemap,hero_x,hero_y,room,slot);
            else if(entity[0]==0x36 || entity[0]==0x37)
            {
                if(!entity[1]) ground_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot);
                else burst_walker_behavior(entity,tilemap,hero_x,hero_y);
            }
            else if(entity[0]==0x38 || entity[0]==0x39)
            {
                if(!entity[1]) ground_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot);
                else bouncing_shooter_behavior(entity,tilemap,hero_x);
            }
            else if(entity[0]==0x3a || entity[0]==0x3b)
                charging_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot);
            else if(entity[0]==0x3c)
                dashing_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot);
            else if(entity[0]==0x3d || entity[0]==0x3e || entity[0]==0x40)
            {
                if(!entity[1]) ground_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot);
                else pursuit_shooter_behavior(entity,tilemap,hero_x,hero_y);
            }
            else if(entity[0]==0x3f)
                hopping_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot);
            else if(entity[0]==0x41)
                ambusher_behavior(entity,cells,hero_x,hero_y,frame,slot);
            else if(entity[0]==0x42) orbit_behavior(entity,hero_x);
            else if(entity[0]>=0x43 && entity[0]<=0x45)
                dungeon_walker_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot);
            else if(entity[0]==0x46) dungeon_proximity_behavior(entity,tilemap,hero_x,hero_y,room,slot,NULL);
            else if(entity[0]>=0x47 && entity[0]<=0x49) dungeon_phase_behavior(entity,cells,hero_x,hero_y,frame,slot,NULL);
            else if(entity[0]==0x4a || entity[0]==0x4b) dungeon_split_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot,NULL);
            else if(entity[0]==0x4c) dungeon_hop_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot,NULL);
            else if(entity[0]==0x4d || entity[0]==0x4e) dungeon_drain_behavior(entity,cells,hero_x,hero_y,frame,slot,NULL,0);
            else if(entity[0]>=0x4f && entity[0]<=0x51) dungeon_hunter_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot,NULL);
            else if(entity[0]==0x52) dungeon_ambush_behavior(entity,cells,hero_x,hero_y,frame,slot,NULL);
            else if(entity[0]==0x53) dungeon_curse_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot,NULL);
            else if(entity[0]==0x54 || entity[0]==0x55) dungeon_emitter_behavior(entity,room,slot,hero_x,hero_y,NULL);
            else if(entity[0]==0x56 || entity[0]==0x59 || entity[0]==0x5a) dungeon_teleport_behavior(entity,cells,hero_x,hero_y,frame,slot,NULL);
            else if(entity[0]==0x57 || entity[0]==0x58) dungeon_sentinel_behavior(entity,tilemap,hero_x,hero_y,room,slot,NULL);
            else if(entity[0]==0x5b) dungeon_thief_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot,NULL);
            else if(entity[0]==0x5c || entity[0]==0x5d) dungeon_guard_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot,NULL);
            else if(entity[0]==0x5e) dungeon_floor_trap_behavior(entity,room,slot);
            else if(entity[0]==0x77) dungeon_floor_shot_behavior(entity);
            else if(entity[0]==0x5f || entity[0]==0x60) dungeon_melee_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot,NULL);
            else if(entity[0]==0x61 || entity[0]==0x62) dungeon_patrol_behavior(entity,tilemap,room,slot);
            else if(entity[0]==0x1c) homing_projectile_behavior(entity,hero_x,hero_y);
            else if(entity[0]==0x1d) lob_projectile_behavior(entity);
            else if(entity[0]==0x1f) bouncing_projectile_behavior(entity,hero_x,hero_y);
            else if((entity[0]>=0x10 && entity[0]<=0x18) || entity[0]==0x19 || entity[0]==0x1a || entity[0]==0x1b || entity[0]==0x1e || entity[0]==0x70 || entity[0]==0x71 || entity[0]==0x72 || entity[0]==0x73)
                projectile_behavior(entity,tilemap,hero_x,hero_y,frame,slot);
            else if(entity[0]==0x63 || entity[0]==0x64)
            {
                u8 gate=255,choice=255;
                if(entity[1]==6 && !entity[4]) { gate=random();if(entity[0]==0x64 && (gate&15)<4) choice=random(); }
                first_boss_behavior(entity,gate,choice);
            }
            else if(entity[0]==0x65)
            {
                u8 select=0,turn=0,gate=255,pause=0;bool move=entity[1]==4;
                if(entity[1]==6 && !entity[4])
                {
                    if(entity[0x2e]) move=TRUE;
                    else { gate=random();if(gate<8) pause=random()&127;else move=TRUE; }
                }
                if(move) { select=random()&127;if(!(select&1)) turn=random()&127; }
                second_boss_behavior(entity,hero_x,hero_y,select,turn,gate,pause);
            }
            else if(entity[0]==0x66) second_boss_satellite_behavior(entity);
            else if(entity[0]==0x67)
            {
                u8 roll[4]={0,0,0,255};
                if(entity[1]==14 && !entity[0x20]) roll[0]=random();
                if(entity[1]==6 && !entity[4]) roll[1]=random();
                if(entity[1]==18 && !entity[4]) roll[2]=random();
                if(entity[1]==20 && !entity[4] && world_actor_state[0]!=7 && world_actor_state[1]!=14)
                { roll[3]=random();roll[2]=random(); }
                composite_boss_behavior(entity,slot,roll);
            }
            else if(entity[0]==0x68 || entity[0]==0x69 || entity[0]==0x7a || entity[0]==0x7b)
                charging_boss_behavior(entity,hero_x,hero_y,NULL,0);
            else if(entity[0]==0x6a || entity[0]==0x6b)
                burst_boss_behavior(entity,cells,hero_x,hero_y,frame,slot,NULL);
            else if(entity[0]==0x74) burst_boss_projectile_behavior(entity);
            else if(entity[0]==0x6c) sword_boss_behavior(entity,hero_x,hero_y,NULL);
            else if(entity[0]==0x6d) final_boss_behavior(entity,hero_x,hero_y,NULL,world_final_boss_weapon_valid());
            else if(entity[0]==0x75) sword_boss_projectile_behavior(entity,hero_x,hero_y);
            else if(entity[0]==0x76) sword_boss_satellite_behavior(entity);
            else if(entity[0]==7) tick_world_boss_death(entity);
            else if(entity[0]==0x0f) tick_world_gem(entity);
            else if(entity[0]==1) death_particle_behavior(entity,slot);
            counter=entity[4]-1;
            if(!(counter&128))
            {
                u16 y=(entity[0x10]|((u16)entity[0x11]<<8))+
                      (entity[0x14]|((u16)entity[0x15]<<8));
                u16 x=(entity[0x12]|((u16)entity[0x13]<<8))+
                      (entity[0x16]|((u16)entity[0x17]<<8));
                if(!counter) { x&=0xff00;y&=0xff00; }
                entity[4]=counter;entity[0x10]=y;entity[0x11]=y>>8;
                entity[0x12]=x;entity[0x13]=x>>8;
            }
            if(entity[12])
            {
                counter=entity[14]+1;
                if(counter>=entity[13]) counter=0;
                entity[14]=counter;
                if(!counter)
                { counter=entity[11]+1;entity[11]=counter==entity[12]?0:counter; }
            }
        }
        counter=entity[5]-1;
        if(!(counter&128))
        {
            entity[5]=counter;entity[3]|=1;
            if(counter&2) entity[3]&=254;
        }
        hurt_world_actor(entity,tilemap);
        /* 0940 follows 26B6: publish these actors' collision boxes from the
         * current behavior/flash state even before their delayed SAT. */
        if((entity[0]==0x0f || entity[0]==0x14 || entity[0]==0x17 || entity[0]==0x18 || entity[0]==0x71 || entity[0]==0x77 || (entity[0]>=0x46 && entity[0]<=0x49) || (entity[0]>=0x63 && entity[0]<=0x6d) || (entity[0]>=0x72 && entity[0]<=0x76) || entity[0]==0x7a || entity[0]==0x7b) && (entity[3]&1))
        {
            u16 table=descriptor_word((entity[8]|((u16)entity[9]<<8))+entity[10]*2);
            const u8 *frame=descriptor_frame(descriptor_word(table+entity[11]*2));
            entity[0x1b]=frame[1];entity[0x1c]=frame[2];
        }
    }
    /* 0940 scans after all behaviors. A4F44 clone can occupy an earlier slot
     * already processed above; publish its new927B frame in this same tick. */
    for(slot=0;slot<16;slot++)
    {
        u8 *entity=world_actor_state+slot*48;
        if((entity[0]>=0x4a && entity[0]<=0x62) && (entity[3]&1))
        {
            u16 table=descriptor_word((entity[8]|((u16)entity[9]<<8))+entity[10]*2);
            const u8 *frame=descriptor_frame(descriptor_word(table+entity[11]*2));
            entity[0x1b]=frame[1];entity[0x1c]=frame[2];
        }
    }
}

/* 393A..39BB: exterior fire projectile, then shared 26E5 integration.
 * Collision boxes are committed after behavior, as by the source renderer. */
void tick_world_spell(const u8 *tilemap,u16 level)
{
    u8 *e=world_spell_state;u16 n,word,table;const u8 *frame;
    bool second=e[0]==4,axe=e[0]==5;
    if(e[0]) world_object_tick_count++;
    if(e[0]!=3 && !second && !axe) return;
    if(!e[1])
    {
        n=e[10]*2;e[3]=3;word=axe?0x3d8d:second?0x8461:0x8411+(level==1?0:8);
        e[8]=word;e[9]=word>>8;e[12]=axe?2:4;e[13]=second?2:1;
        e[0x15]=axe?world_axe_velocity[n]:second?world_second_spell_velocity[n]:world_fire_velocity[n];
        e[0x17]=axe?world_axe_velocity[n+1]:second?world_second_spell_velocity[n+1]:world_fire_velocity[n+1];
        if(axe) { e[0x11]-=2;e[4]=8;e[0x19]=world_attack_strength[level]; }
        else if(!second) { e[0x11]+=world_fire_origin[n];e[0x13]+=world_fire_origin[n+1]; }
        e[1]++;
    }
    if(axe) { if(!e[4]) { memset(e,0,0x30);return; } }
    else e[4]=2;
    /* Out-of-range coordinates also clear before integration in 398D. */
    if(e[0x13]<8 || e[0x13]>=248 || (u8)(e[0x11]+8)>=(second?169:168))
    { memset(e,0,0x30);return; }
    n=((u8)(e[0x11]-(second?8:0))&248)*8+((e[0x13]>>2)&62);
    word=tilemap[n+1]&0xe0;
    if(!axe && (second?(word&0x80):(word==0x80 || word==0xa0))) { memset(e,0,0x30);return; }
    if(second && mutate_world_spell_terrain(e,level)) { memset(e,0,0x30);return; }
    e[4]--;
    word=(e[0x10]|((u16)e[0x11]<<8))+(e[0x14]|((u16)e[0x15]<<8));e[0x10]=word;e[0x11]=word>>8;
    word=(e[0x12]|((u16)e[0x13]<<8))+(e[0x16]|((u16)e[0x17]<<8));e[0x12]=word;e[0x13]=word>>8;
    if(++e[14]>=e[13]) { e[14]=0;e[11]++;if(e[11]==e[12]) e[11]=0; }
    n=(u8)(e[5]-1);
    if(!(n&128)) { e[5]=n;e[3]|=1;if(n&2) e[3]&=254; }
    e[0x1d]=0;
    if(!(e[3]&1)) return;
    table=descriptor_word((e[8]|((u16)e[9]<<8))+e[10]*2);
    table=descriptor_word(table+e[11]*2);frame=descriptor_frame(table);
    e[0x1b]=frame[1];e[0x1c]=frame[2];
}

static const u8 *descriptor_frame(u16 address)
{
    if(address>=0x2acd && address<0x2add) return gem_descriptor_data+address-0x2acd;
    if(address>=0x3d8d && address<0x3da5) return world_axe_descriptors+address-0x3d8d;
    return actor_descriptors+(address&0x3fff);
}

static __attribute__((noinline,cold)) u16 descriptor_word_fallback(u16 address)
{
    if(address>=0x2acd && address<0x2adc) return gem_descriptor_data[address-0x2acd]|((u16)gem_descriptor_data[address-0x2acc]<<8);
    if(address>=0x3d8d && address<0x3da4) return world_axe_descriptors[address-0x3d8d]|((u16)world_axe_descriptors[address-0x3d8c]<<8);
    address&=0x3fff;
    return actor_descriptors[address]|((u16)actor_descriptors[address+1]<<8);
}

static inline __attribute__((always_inline)) u16 descriptor_word(u16 address)
{
    u16 offset=address&0x3fff;
    /* Inline the common native word read; gem/axe and the legacy fallback
     * retain their byte reads outside this immutable bank slice. */
    if(offset<ACTOR_DESCRIPTOR_WORD_COUNT) return actor_descriptor_words[offset];
    return descriptor_word_fallback(address);
}

/* 09EE: one actor descriptor, shared by depth and rotating order. */
static u16 add_world_entity_sprites(u16 index,u8 *entity)
{
    u16 n;
    u16 table=entity[8]|((u16)entity[9]<<8),count,base;
    const u8 *frame;VDPSprite *sprite;
    u8 x=entity[0x13],y=entity[0x11];
    table=descriptor_word(table+entity[10]*2);
    table=descriptor_word(table+entity[11]*2);
    frame=descriptor_frame(table);
    count=frame[0]&127;base=frame[0]&128?0:entity[2];
    /* Teleport flash state is published after AI by0940. Cached sprite
     * ordering must not publish the preceding visible pose's boxes. */
    if(entity[0]<0x56 || entity[0]>0x62)
    { entity[0x1b]=frame[1];entity[0x1c]=frame[2]; }
    /* 09EE emits the complete descriptor; large bosses exceed16 parts. */
    if(!count || index+count>64) return index;
    sprite=vdpSpriteCache+index;
    for(n=0;n<count;n++)
    {
        s16 screen_y;
        u8 tile=(base+frame[4+count+n*2])&255;
        y+=frame[3+n];x+=frame[3+count+n*2];
        screen_y=y>208?(s16)y-256:y;
        /* All parts are8x8. Advance the cache pointer and write the
         * packed size/link word rather than recomputing index*8 per part. */
        sprite->y=screen_y+145;sprite->size_link=index+1;
        sprite->attribut=TILE_ATTR_FULL(PAL1,0,0,0,16+256+tile);
        sprite->x=x+128;sprite++;index++;
    }
    return index;
}


/* 0951: overlapping32-word windows at phase*16 in source bank12:8000. */
u16 world_sprite_order_slot(u16 n,u16 phase)
{
    static const u8 order[]={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,0,31,30,29,28,27,26,25,24,23,22,21,20,19,18,17,16,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15};
    return order[(phase&3)*16+n];
}
u16 add_world_ordered_actor_sprites(u16 index,u16 slot)
{
    u8 *entity;
    if(slot==1) entity=world_spell_state;
    else if(slot>=9 && slot<16) entity=world_loot_state+(slot-9)*48;
    else if(slot>=16 && slot<32) entity=world_actor_state+(slot-16)*48;
    else return index; /* Source C360..C480 unused by the current native record model. */
    if(!entity[0] || !(entity[3]&1)) return index;
    return add_world_entity_sprites(index,entity);
}

/* 097E/09EE: depth order and two levels of direction/pose indirection.
 * Actor coordinates and tile deltas accumulate in eight-bit SMS registers. */
u16 add_world_actor_sprites(u16 index,s16 minimum_y,s16 maximum_y)
{
    static u8 *order[24];
    static u16 length;
    u8 *entity=world_loot_state;
    u16 slot,n;
    if(minimum_y>=0)
    {
    length=0;
    for(slot=0;slot<24;slot++)
    {
        s16 y;
        entity=slot==0?world_spell_state:slot<8?world_loot_state+(slot-1)*0x30:world_actor_state+(slot-8)*0x30;
        if(!(entity[3]&1)) continue;
        y=entity[0x11];
        n=length++;
        while(n && order[n-1][0x11]<y)
        { order[n]=order[n-1];n--; }
        order[n]=entity;
    }
    }
    for(slot=0;slot<length;slot++)
    {
        entity=order[slot];
        if(entity[0x11]<=minimum_y || entity[0x11]>maximum_y) continue;
        { u16 next=add_world_entity_sprites(index,entity);if(next==index) break;index=next; }
    }
    return index;
}
