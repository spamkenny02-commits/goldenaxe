#include <genesis.h>
#include "actors.h"
#include "key_redraw_cost.inc"
#include "room_clear.inc"
#include "room_contact.inc"
#include "room_puzzles.inc"
#include "item_rewards.inc"
#include "room_portals.inc"

/* Native 68000 port of the title, menu, naming, narrative and initial room.
 * The source Z80 instructions are not executed by this ROM.
 * Normal-ground walking is ported; other game logic, sound and saves are pending. */
extern const u8 title_bank7[];
extern const u32 title_bank7_size;
extern const u32 title_loading_tstates;
extern const u8 menu_rle[],font_bitmap[],normal_font[],menu_cursor_bitmap[];
extern const u8 number_font_rle[],symbol_font_rle[],menu_frame_tiles[];
extern const u8 text_charset[],menu_text[],menu_palette[];
extern const u8 name_text[],name_grid[],name_typed_tiles[],name_ascii[];
extern const u8 name_positions[],name_caret_positions[];
extern const u8 name_cursor_frame[],name_delete_frame[],name_finish_frame[],name_caret_frame[];
extern const u8 dialog_font[],dialog_charset[],dialog_widths[],opening_text[];
extern const u8 world_background_rle[],world_room_rle[],world_palette[],world_extra_meta[];
extern const u8 world_hud_rle[],world_hud_font_rle[],world_hud_patterns_rle[];
extern const u8 world_item_icon[],world_icon_remap[],world_hud_icon_words[];
extern const u8 world_hero_bitmap[],world_hero_frame[];
extern const u8 world_hero_bitmaps[],world_hero_frames[],world_walk_table[],world_fast_ground_walk[];
extern const u8 world_hero_collisions[];
extern const u8 world_combat_bitmap_index[],world_combat_bitmaps[],world_combat_frame_index[],world_combat_frames[];
extern const u8 world_combat_collisions[],world_attack_sequences[],world_attack_strength[];
extern const u8 actor_loot_patterns[];
extern const u8 world_cast_bitmaps[],world_cast_frames[],world_cast_collisions[];
extern const u8 inventory_header_rle[],inventory_map_rle[],inventory_icons[],inventory_cursor_bitmap[];
extern const u8 inventory_cursor_frame[],inventory_marker_frame[],inventory_positions[],inventory_charset[],inventory_equipment_words[];
extern const u8 world_death_bitmaps[],world_gameover_font[],world_gameover_words[];
extern const u8 world_gray_tones[],world_water_cycle[],world_armor_colors[],world_reveal_contours[];
extern const u8 world_room_index[],world_room_streams[];
extern const u8 world_house_animation_bitmaps[];
extern const u8 world_house_background_rle[],world_house_palette[],world_house_extra_meta[];
extern const u8 world_dungeon_background_rle[],world_dungeon_palette[],world_dungeon_extra_meta[];
extern const u8 world_dungeon_palettes[],world_dungeon_dark_rooms[],world_dungeon_color_cycle[];
extern const u8 world_room_metadata[],world_dungeon_metadata[];
#define TITLE_TILE_COUNT 449

static u8 sms_vram[0x4000];
static u8 scratch[0x1000];
static u8 title_map[0x600], animation_map[0x600];
static u32 md_patterns[512*8];
static u16 md_map[32*24];
static u16 md_palette[32];
static u16 sms_palette[32];
static u16 input;
static u16 map_origin=0x3900;
static bool title_phase, title_requested;
static u16 menu_selection;
static u16 name_cursor,name_position;
static u8 character_name[9];
/* C310..C317 positions/velocities, C304 counter, C30A/B pose, C068 sliding. */
static u16 hero_y,hero_x,hero_direction,hero_animation,hero_counter,hero_pending;
static u16 hero_shield_level,hero_armor_level,hero_health,hero_hurt,hero_flags,hero_state,hero_defense;
static u16 hero_health_drawn,hero_health_capacity_drawn,hero_gold,death_menu_selection;
static u16 hero_selected_item,hero_weapon_level,hero_basic_level,hero_attack_speed,hero_attack_phase,hero_attack;
static u8 hero_items[17];
static volatile u16 inventory_slot;
static u16 hero_keys,hero_fire_charge,hero_casting,hero_terrain_context;
extern const u8 world_terrain_records[],world_water_walk[],world_water_bitmaps[];
static u16 world_previous_input,hero_loaded_pose=8,hero_pattern_tiles=4;
static u16 hero_max_health,hero_magic,hero_max_magic,hero_gold_drawn,hero_magic_drawn,hero_magic_capacity_drawn,hero_magic_delay;
static bool hero_gold_pending,hero_magic_pending;
static bool return_to_title,world_palette_pending;
static bool hero_health_pending;
static s16 hero_dy,hero_dx;
static u16 house_animation_scan,house_animation_patterns_pending,house_talk_latch;
static volatile u16 house_dialogue_active,house_dialogue_index;
static volatile u16 save_service_phase;
static u8 house_dialogue_backup[0x1c50];
static bool save_resume_pending;
static u16 save_resume_room,save_resume_health;
static u16 world_graphics_class,house_return_room,house_return_x,house_return_y;
static u16 world_dungeon_number;
static u16 world_dungeon_dark;
static u8 game_save_state[0x250];
static u8 room_metadata[3]; /* C06E..C070 */
static u16 room_id,game_state,transition_direction,transition_stage,transition_step;
static bool transition_pose_prepared;
static u8 forest_maze_progress; /* C06C: transient, outside the save record. */
static u16 hero_pattern_wait_frames;
static s16 hero_scroll_x,hero_scroll_y;
static u16 transition_loading_frames;
static bool map_queue;
static bool door_transition_loading;
/* Observable loader stages for emulator regression; never stores captured states. */
static volatile u16 resume_phase,resume_contour,resume_fade_step;
static u32 world_clock_shift;
static u8 dungeon_animation_scan,dungeon_animation_phase;
static u16 room_shutter_state,room_shutter_direction,room_script_coordinate,room_script_coordinate_pending,room_script_direction;
static u8 world_clock(void) { return (u8)(vtimer-world_clock_shift); }
/* 55F8: selected item1 at level2 is required for type6D pending damage. */
bool world_final_boss_weapon_valid(void) { return hero_selected_item==1 && hero_weapon_level==2; }
/* 4FC2..4FCA: contact with4D/4E subtracts eight magic, clamped at zero. */
void world_drain_hero_magic(void) { hero_magic=hero_magic>=8?hero_magic-8:0; }
/* 2CD5/9EB1: low tile bytes at center cache positions5/6, before movement. */
static bool hero_floor_zero=TRUE; /* Original boot cache C052/C054 is zero. */
void world_set_hero_floor(u8 left,u8 right) { hero_floor_zero=!left || !right; }
bool world_hero_zero_floor(void) { return hero_floor_zero; }
/* C0BF is byte15 of the existing C0B0-layout persistent save record. */
void world_curse_hero(void) { game_save_state[15]=1; }
static void prepare_hero_defense(void) { hero_defense=(hero_shield_level-1)*2+(game_save_state[15]?0:(hero_armor_level-1)*4); }
/* A36F/A3BF:5B capture excludes an already grabbed hero. */
u16 world_hero_state(void) { return hero_state; }
u16 world_hero_direction(void) { return hero_direction; }
extern void sound_effect(u16 command);
/* Returns true when the thief must release; consumes fresh direction edges. */
bool world_tick_hero_grab(u8 *e,u16 frame)
{
    if(!hero_health) return TRUE;
    e[0x11]=(hero_y>>8)+8;e[0x13]=(hero_x>>8)+((frame&2)?1:255);
    if(!hero_counter) { hero_state=12;hero_animation=0; }
    if(!--e[0x21])
    { e[0x21]=16;if(hero_gold) { hero_gold--;sound_effect(0x95); } }
    if(input&~world_previous_input&15)
    { e[0x20]++;if(e[0x20]>=6) { hero_state=0;return TRUE; } }
    return FALSE;
}
static s16 world_hscroll[224];
static u16 world_metatiles_md[0x220],world_old_md[640],world_new_md[640];

/* 032A: four separate RLE streams, interleaved in the VDP pattern buffer.
 * 0BFE: same grammar with a stride of two for low/high tilemap bytes. */
static const u8 *decode_planes(const u8 *src, u8 *dst, u16 stride)
{
    u16 plane;
    for (plane=0; plane<stride; plane++)
    {
        u8 *write=dst+plane;
        u16 command;
        while ((command=*src++)!=0)
        {
            u16 count=command&127;
            if (!count) count=256; /* Z80 DJNZ with B=0 */
            while (count--)
            {
                *write=*src;
                write+=stride;
                if (command&128) src++;
            }
            if (!(command&128)) src++;
        }
    }
    return src;
}

/* 0BD3: expand literal or incrementing sequences into D100, then 0BFE. */
static const u8 *decode_map(const u8 *src, u8 *dst)
{
    u8 *write=scratch;
    u16 command;
    while ((command=*src++)!=0)
    {
        u16 count=command&127;
        if (!count) count=256;
        if (command&128)
            while (count--) *write++=*src++;
        else
        {
            u8 value=*src++;
            while (count--) *write++=value++;
        }
    }
    decode_planes(scratch,dst,2);
    return src;
}

/* Lookup removes four bit-spreading function calls per SMS pattern row. */
static const u32 plane_spread[256]={
    0x00000000,0x00000001,0x00000010,0x00000011,0x00000100,0x00000101,0x00000110,0x00000111,
    0x00001000,0x00001001,0x00001010,0x00001011,0x00001100,0x00001101,0x00001110,0x00001111,
    0x00010000,0x00010001,0x00010010,0x00010011,0x00010100,0x00010101,0x00010110,0x00010111,
    0x00011000,0x00011001,0x00011010,0x00011011,0x00011100,0x00011101,0x00011110,0x00011111,
    0x00100000,0x00100001,0x00100010,0x00100011,0x00100100,0x00100101,0x00100110,0x00100111,
    0x00101000,0x00101001,0x00101010,0x00101011,0x00101100,0x00101101,0x00101110,0x00101111,
    0x00110000,0x00110001,0x00110010,0x00110011,0x00110100,0x00110101,0x00110110,0x00110111,
    0x00111000,0x00111001,0x00111010,0x00111011,0x00111100,0x00111101,0x00111110,0x00111111,
    0x01000000,0x01000001,0x01000010,0x01000011,0x01000100,0x01000101,0x01000110,0x01000111,
    0x01001000,0x01001001,0x01001010,0x01001011,0x01001100,0x01001101,0x01001110,0x01001111,
    0x01010000,0x01010001,0x01010010,0x01010011,0x01010100,0x01010101,0x01010110,0x01010111,
    0x01011000,0x01011001,0x01011010,0x01011011,0x01011100,0x01011101,0x01011110,0x01011111,
    0x01100000,0x01100001,0x01100010,0x01100011,0x01100100,0x01100101,0x01100110,0x01100111,
    0x01101000,0x01101001,0x01101010,0x01101011,0x01101100,0x01101101,0x01101110,0x01101111,
    0x01110000,0x01110001,0x01110010,0x01110011,0x01110100,0x01110101,0x01110110,0x01110111,
    0x01111000,0x01111001,0x01111010,0x01111011,0x01111100,0x01111101,0x01111110,0x01111111,
    0x10000000,0x10000001,0x10000010,0x10000011,0x10000100,0x10000101,0x10000110,0x10000111,
    0x10001000,0x10001001,0x10001010,0x10001011,0x10001100,0x10001101,0x10001110,0x10001111,
    0x10010000,0x10010001,0x10010010,0x10010011,0x10010100,0x10010101,0x10010110,0x10010111,
    0x10011000,0x10011001,0x10011010,0x10011011,0x10011100,0x10011101,0x10011110,0x10011111,
    0x10100000,0x10100001,0x10100010,0x10100011,0x10100100,0x10100101,0x10100110,0x10100111,
    0x10101000,0x10101001,0x10101010,0x10101011,0x10101100,0x10101101,0x10101110,0x10101111,
    0x10110000,0x10110001,0x10110010,0x10110011,0x10110100,0x10110101,0x10110110,0x10110111,
    0x10111000,0x10111001,0x10111010,0x10111011,0x10111100,0x10111101,0x10111110,0x10111111,
    0x11000000,0x11000001,0x11000010,0x11000011,0x11000100,0x11000101,0x11000110,0x11000111,
    0x11001000,0x11001001,0x11001010,0x11001011,0x11001100,0x11001101,0x11001110,0x11001111,
    0x11010000,0x11010001,0x11010010,0x11010011,0x11010100,0x11010101,0x11010110,0x11010111,
    0x11011000,0x11011001,0x11011010,0x11011011,0x11011100,0x11011101,0x11011110,0x11011111,
    0x11100000,0x11100001,0x11100010,0x11100011,0x11100100,0x11100101,0x11100110,0x11100111,
    0x11101000,0x11101001,0x11101010,0x11101011,0x11101100,0x11101101,0x11101110,0x11101111,
    0x11110000,0x11110001,0x11110010,0x11110011,0x11110100,0x11110101,0x11110110,0x11110111,
    0x11111000,0x11111001,0x11111010,0x11111011,0x11111100,0x11111101,0x11111110,0x11111111,
};

static void convert_patterns_range(u16 first,u16 count)
{
    u16 tile,y;
    for (tile=first;tile<first+count;tile++)
        for (y=0;y<8;y++)
        {
            const u8 *planes=sms_vram+tile*32+y*4;
            md_patterns[tile*8+y]=plane_spread[planes[0]]|
                (plane_spread[planes[1]]<<1)|(plane_spread[planes[2]]<<2)|
                (plane_spread[planes[3]]<<3);
        }
}
static void convert_patterns(u16 count) { convert_patterns_range(0,count); }

static void draw_map(void)
{
    u16 n;
    /* SMS R9=$20: visible row zero starts at VRAM $3900 (name table row 4).
     * Place the 192-line image in the middle of MD's 224-line display. */
    for (n=0;n<32*24;n++)
    {
        const u8 *entry=sms_vram+map_origin+n*2;
        u16 sms=entry[0]|((u16)entry[1]<<8);
        md_map[n]=TILE_ATTR_FULL((sms>>11)&1,(sms>>12)&1,
                                (sms>>10)&1,(sms>>9)&1,16+(sms&511));
    }
    VDP_setTileMapDataRect(BG_A,md_map,0,2,32,24,32,map_queue?DMA_QUEUE:CPU);
}

static void set_palette(const u16 *sms)
{
    static const u16 levels[4]={0,3,5,7};
    u16 n;
    for (n=0;n<32;n++)
        md_palette[n]=(levels[sms[n]&3]<<1)|(levels[(sms[n]>>2)&3]<<5)|(levels[(sms[n]>>4)&3]<<9);
    /* SMS color zero is transparent. BG_B provides the original green backdrop.
     * The 16 additional lines above and below remain black. */
    md_palette[0]=0;
    PAL_setColors(0,md_palette,32,CPU);
    /* The SMS backdrop is color 0 of its second palette. */
    PAL_setColor(33,(levels[sms[16]&3]<<1)|(levels[(sms[16]>>2)&3]<<5)|(levels[(sms[16]>>4)&3]<<9));
}

static void set_world_palette(void)
{
    static const u16 levels[4]={0,3,5,7};
    u16 color=sms_palette[0],n;
    for(n=1;n<32;n++)
    {
        u16 sms=sms_palette[n];
        u16 converted=(levels[sms&3]<<1)|(levels[(sms>>2)&3]<<5)|(levels[(sms>>4)&3]<<9);
        if(converted!=md_palette[n]) { md_palette[n]=converted;PAL_setColor(n,converted); }
    }
    color=(levels[color&3]<<1)|(levels[(color>>2)&3]<<5)|(levels[(color>>4)&3]<<9);
    if(PAL_getColor(33)!=color) PAL_setColor(33,color);
}

static void wait_frame(void)
{
    SYS_doVBlankProcess();
    input=JOY_readJoypad(JOY_1);
    if(title_phase && (input&(BUTTON_A|BUTTON_B|BUTTON_C|BUTTON_START))) title_requested=TRUE;
}
static void wait_frames(u16 n) { while(n-- && !title_requested) wait_frame(); }

/* 1470 -> 0B48 / 0B12: fade the preceding story out before loading the title. */
static void fade_before_title(void)
{
    u16 step,n;
    for(step=1;step<=16;step*=4)
    {
        bool changed;
        do
        {
            changed=FALSE;
            for(n=0;n<32;n++) if(sms_palette[n]&(step*3))
            {
                sms_palette[n]-=step;changed=TRUE;
            }
            if(changed) { set_palette(sms_palette);wait_frames(2); }
        } while(changed && !title_requested);
        if(title_requested) return;
    }
}

/* 0AA4 / 169C: the first ramp is blue/green/red, two IRQs per step;
 * the later warrior ramp is red/green/blue, six IRQs per step. */
static void fade_title_palette(bool initial)
{
    u16 pass,step,n,target_palette[32];
    for(n=0;n<32;n++)
        target_palette[n]=initial?((n==0 || (n>=12 && n<=14) || n==16 || n==17)?title_bank7[n&15]:0):(n<16?title_bank7[n]:sms_palette[n]);
    for(pass=0;pass<3;pass++)
    {
        bool changed;
        step=initial?(16>>(pass*2)):(1<<(pass*2));
        do {
            changed=FALSE;
            for(n=0;n<32;n++)
            {
                u16 current=sms_palette[n]&(step*3);
                u16 target=target_palette[n]&(step*3);
                if(current!=target)
                {
                    sms_palette[n]+=current<target?step:-step;
                    changed=TRUE;
                }
            }
            if(changed) { set_palette(sms_palette); wait_frames(initial?2:6); }
        } while(changed && !title_requested);
        if(title_requested) return;
    }
}

static void copy_rows(const u8 *source,u16 address,u16 rows,u16 width)
{
    u16 column;
    while(rows--)
    {
        u16 offset=(address-map_origin)/2;
        memcpy(sms_vram+address,source,width);
        for(column=0;column<width/2;column++)
        {
            u16 sms=source[column*2]|((u16)source[column*2+1]<<8);
            md_map[offset+column]=TILE_ATTR_FULL((sms>>11)&1,(sms>>12)&1,
                                  (sms>>10)&1,(sms>>9)&1,16+(sms&511));
        }
        VDP_setTileMapDataRect(BG_A,md_map+offset,offset%32,2+offset/32,width/2,1,width/2,DMA_QUEUE);
        address+=64;
        source+=width;
    }
}

static volatile u16 intro_timer;
#include "sound.inc"

static void title_sequence(void)
{
    const u8 *src=title_bank7+16;
    u16 n,k,loading_frames;
    u32 loading_started,budget;
    fade_before_title();
    if(title_requested) return;
    loading_started=vtimer;
    VDP_setEnable(FALSE);
    memset(sms_vram,0,sizeof(sms_vram));
    map_origin=0x3900;
    VDP_fillTileMapRect(BG_B,TILE_ATTR_FULL(PAL2,0,0,0,1),0,2,32,24);
    src=decode_planes(src,sms_vram,4);
    src=decode_map(src,title_map);
    decode_map(src,animation_map);
    /* 1499..14A2: select palette 1 for ten entries at the bottom of the map. */
    for(n=0;n<10;n++) title_map[0x5ab+2*n]|=8;
    memcpy(sms_vram+0x3900,title_map,sizeof(title_map));
    convert_patterns(TITLE_TILE_COUNT);
    VDP_loadTileData(md_patterns,16,TITLE_TILE_COUNT,CPU);
    memset(sms_palette,0,sizeof(sms_palette));
    set_palette(sms_palette);
    draw_map();
    /* 0B56..14CF: preserve original resource work instead of MD decoder speed.
     * Costs are generated from the source instruction loops and packed assets.
     * Keep the same IRQ reserve as the exterior actor loader; elapsed native
     * VBlanks already spent decoding/converting/uploading count toward the work. */
    budget=(SYS_isPAL()?71364:59736)-3072;
    loading_frames=(title_loading_tstates+budget-1)/budget;
    while(vtimer-loading_started<loading_frames && !title_requested) wait_frame();
    if(title_requested) return;
    /* 0AA4 waits one IRQ with a black palette before enabling the display. */
    wait_frame();
    if(title_requested) return;
    VDP_setEnable(TRUE);
    fade_title_palette(TRUE);
    if(title_requested) return;
    sound_music(0x81);
    /* 165C..167E: three cape poses, six IRQs each, eleven cycles. */
    for(n=0;n<11;n++)
        for(k=0;k<3;k++)
        {
            wait_frames(6);
            if(title_requested) return;
            copy_rows(animation_map+0x200+234*k,0x3cc4,9,26);
        }
    wait_frames(6);
    if(title_requested) return;
    copy_rows(title_map+0x3c0,0x3cc0,9,64);
    /* 169C palette ramp follows, then 163F reveals the eight upper rows. */
    fade_title_palette(FALSE);
    if(title_requested) return;
    wait_frames(60);
    if(title_requested) return;
    for(n=0;n<8;n++)
    {
        wait_frames(1);
        if(title_requested) return;
        copy_rows(animation_map+n*64,0x3900+n*64,1,64);
    }
    /* 161D: flashing prompt. Full game state 14ED is not ported yet. */
    for(n=360;n>0;n--)
    {
        wait_frame();
        if(title_requested) return;
        copy_rows((n&0x30)?animation_map+0x4be:title_map+0x240,0x3b40,1,64);
    }
}

/* Native 0365 / 0C36: monochrome rows expanded to four SMS bit planes. */
static void load_mono(u16 destination,const u8 *source,u16 rows,u16 mask,bool background)
{
    u16 n,p;
    for(n=0;n<rows;n++)
    {
        for(p=0;p<4;p++) sms_vram[destination+n*4+p]=(mask&(1<<p))?source[n]:0;
        if(background) sms_vram[destination+n*4]=255; /* 0C51 */
    }
}

/* 0877: nine-slice frame expressed through the original nine tile words. */
static void draw_frame(u16 destination,u16 width,u16 height)
{
    u16 x,y;
    for(y=0;y<height;y++)
        for(x=0;x<width;x++)
        {
            u16 kind=(y==0?0:y==height-1?2:1)*3+(x==0?0:x==width-1?2:1);
            sms_vram[destination+y*64+x*2]=menu_frame_tiles[kind*2];
            sms_vram[destination+y*64+x*2+1]=menu_frame_tiles[kind*2+1];
        }
}

/* 0812: ROM charset descriptor $8A8E, newline $FF, terminator $00. */
static void draw_text(u16 destination,const u8 *text)
{
    u16 line=destination;
    u8 value;
    while((value=*text++)!=0)
    {
        u16 index;
        if(value==255) { line+=64; destination=line; continue; }
        for(index=0;index<48;index++) if(text_charset[index]==value) break;
        sms_vram[destination++]=(0xd0+index)&255;
        sms_vram[destination++]=8;
    }
}

static void update_menu_selection(void)
{
    /* 1524..1537: original green cursor and blank word exchanged by selection. */
    u16 first=menu_selection?0x18ff:0x0982;
    u16 second=menu_selection?0x0982:0x18ff;
    sms_vram[0x3a96]=first; sms_vram[0x3a97]=first>>8;
    sms_vram[0x3ad6]=second; sms_vram[0x3ad7]=second>>8;
    draw_map();
}

/* 0A78: relative SMS sprite descriptors, compiled to MD sprite attributes.
 * Descriptors contain count, cumulative Y deltas, then X delta/tile pairs. */
static u16 add_sms_sprite_frame(u16 index,s16 x,s16 y,const u8 *frame,u16 priority)
{
    u16 count=*frame++,n;
    const u8 *xs=frame+count;
    if(!count || count>16 || index+count>64) return index;
    for(n=0;n<count;n++)
    {
        y+=(s8)frame[n];
        x+=(s8)xs[n*2];
        VDP_setSpriteFull(index,x,y+17,SPRITE_SIZE(1,1),
                         TILE_ATTR_FULL(PAL1,priority,0,0,16+256+xs[n*2+1]),index+1);
        index++;
    }
    return index;
}

 #include "intro.inc"

static void update_name_sprites(void)
{
    const u8 *frame=name_cursor<40?name_cursor_frame:name_cursor==40?name_delete_frame:name_finish_frame;
    u16 count;
    VDP_resetSprites();
    count=add_sms_sprite_frame(0,name_positions[name_cursor*2+1],name_positions[name_cursor*2],frame,1);
    count=add_sms_sprite_frame(count,name_caret_positions[name_position*2+1],name_caret_positions[name_position*2],name_caret_frame,1);
    if(count && count<=64) { VDP_setSpriteLink(count-1,0);VDP_updateSprites(count,CPU); }
}

/* 129F/12A3/12B6: raw glyph tiles, either spaced or contiguous. */
static const u8 *draw_raw_glyphs(u16 destination,const u8 *glyphs,u16 count,bool spaced)
{
    while(count--)
    {
        sms_vram[destination++]=*glyphs++;
        sms_vram[destination++]=8; /* 1169 removes priority from every name-table word */
        if(spaced) destination+=2;
    }
    return glyphs;
}

/* 0524..07EE: proportional 8x10 ROM glyphs into the original 208x40 bitmap.
 * scratch is the D100-style column-major bitmap while no RLE loader is active. */
static u16 dialog_glyph(u8 value,bool small)
{
    s16 index;
    if(value==0xb0) value='-';
    for(index=190;index>=0;index--) if(dialog_charset[index]==value) break;
    if(index<0) index=80;
    if(small && index>=0x88 && index<0xbf) index-=0x37; /* 05DF..05F0, DCC6 bit 0 */
    return index;
}

static void upload_dialog_bitmap(void)
{
    #include "dialogue_packed_pixels.inc"
    const u8 *source=scratch;
    u8 *destination=sms_vram+0x2000;
    u32 *patterns=md_patterns+256*8;
    u16 n;
    for(n=0;n<0x410;n++)
    {
        u16 bitmap=*source++;
        *destination++=255;*destination++=bitmap;
        *destination++=0;*destination++=0;
        *patterns++=dialogue_packed_pixels[bitmap];
    }
    VDP_loadTileData(md_patterns+256*8,16+256,130,CPU);
}

/* 068A..06B6: publish each of the four original bitmap scroll poses. */
static void scroll_dialog_bitmap(void)
{
    static const u8 steps[4]={2,3,3,2};
    u16 phase,column,row;
    for(phase=0;phase<4;phase++)
    {
        u16 step=steps[phase];
        for(column=0;column<26;column++)
        {
            for(row=0;row<40-step;row++)
                scratch[column*40+row]=scratch[column*40+row+step];
            memset(scratch+column*40+40-step,0,step);
        }
        sound_effect(0x9f);upload_dialog_bitmap();
        /* PAL conversion/upload already spans the two source video frames.
         * NTSC retains the third frame before the next pose. */
        if(!SYS_isPAL()) wait_frame();
    }
    /* 06D6 calls 0786 again before parsing/drawing the next word. */
    sound_effect(0x9f);upload_dialog_bitmap();
}

static void draw_dialog_glyph(u16 x,u16 y,u16 index)
{
    u16 row,column;
    for(row=0;row<10;row++)
        for(column=0;column<8;column++)
            if((dialog_font[index*10+row]&(128>>column)) && x+column<208)
            {
                u16 pixel=x+column;
                scratch[(pixel>>3)*40+y+row]|=128>>(pixel&7);
            }
}

/* 7447..7451 / 627A..6282: final text acknowledgement has no blink
 * or C02F reset, and accepts the six original controller inputs. */
static void wait_dialog_end(void)
{
    u16 previous=input;
    while(TRUE)
    {
        wait_frame();
        if((input&~previous)&(BUTTON_A|BUTTON_B|BUTTON_C|BUTTON_START|
            BUTTON_UP|BUTTON_DOWN|BUTTON_LEFT|BUTTON_RIGHT)) return;
        previous=input;
    }
}

/* 0805 writes only the marker's name-table byte. */
static void set_dialog_marker(u16 tile)
{
    u16 sms,word;
    sms_vram[0x3cde]=tile;sms=tile|((u16)sms_vram[0x3cdf]<<8);
    word=TILE_ATTR_FULL((sms>>11)&1,(sms>>12)&1,(sms>>10)&1,
        (sms>>9)&1,16+(sms&511));
    md_map[623]=word;VDP_setTileMapXY(BG_A,word,15,21);
}

/* Intermediate pages and service frontends retain their separate marker. */
static void wait_dialog_continue(void)
{
    u16 previous=input,blink=0;
    while(TRUE)
    {
        wait_frame();
        if((input&~previous)&(BUTTON_A|BUTTON_B|BUTTON_C|BUTTON_START|
            (house_dialogue_active?(BUTTON_UP|BUTTON_DOWN|BUTTON_LEFT|BUTTON_RIGHT):0))) break;
        previous=input;
        set_dialog_marker((blink++&8)?0xfc:0xfd);
    }
    set_dialog_marker(0xfc);
}

/* First new-game room ($0095). Original loaders 16D0/190B/2279/1E4E.
 * Retain collision bits in the source map; draw_map only translates VDP bits.
 * scratch: C900..CD37 metatiles at 0, DC00..DC9F cells at $800. */
static s16 collision_direction(u16 direction,const u8 *cache)
{
#define WALL(n) (cache[n]&128)
    if(direction==0)
    {
        if(!WALL(1)) return WALL(2)?(WALL(4)?-1:2):0;
        if(WALL(2)||WALL(7)) return -1;
        return 3;
    }
    if(direction==1)
    {
        if(!WALL(10)) return WALL(9)?(WALL(7)?-1:3):1;
        if(WALL(9)||WALL(4)) return -1;
        return 2;
    }
    if(direction==2)
    {
        if(!WALL(4)) return 2;
        if(!(WALL(0)||WALL(1)||WALL(2))) return 0;
        if(WALL(8)||WALL(9)||WALL(10)) return -1;
        return 1;
    }
    if(!WALL(7)) return 3;
    if(!(WALL(3)||WALL(2)||WALL(1))) return 0;
    if(WALL(11)||WALL(10)||WALL(9)) return -1;
    return 1;
#undef WALL
}

/* 2D11/386E: terrain context tests the two tiles under the hero. */
static u16 classify_hero_terrain(void)
{
    u16 p=((((hero_y>>8)-4)&248)*8)+(((((hero_x>>8)-4)&255)>>2)&62),n,j;
    u8 left=sms_vram[0x3800+p],right=sms_vram[0x3800+p+2];
    const u8 *record=world_terrain_records+(world_graphics_class==2?0x39:0x14);
    if(world_graphics_class==1) return 0;
    for(n=0;n<5;n++,record+=4)
    {
        u16 address=record[0]|((u16)record[1]<<8);
        const u8 *list=world_terrain_records+address-0x2530;
        for(j=0;j<record[2];j++) if(list[j]==left || ((n==1 || n==2) && list[j]==right)) return record[3];
    }
    return 0;
}

/* 2D41: water equipment changes collision flags only while both feet are on water. */
static void apply_water_collision_cache(u8 *cache)
{
    u16 n;u8 flags=cache[5]&cache[6]&0xc0;
    if(!hero_items[16] || !(flags&0x40)) return;
    for(n=0;n<12;n++)
    {
        if(cache[n]&0x40) cache[n]&=127;
        else if(flags&0x80) cache[n]|=128;
    }
}

/* 32ED..32F6 selects fast movement with C0EE; 26E5..2718 integrates. */
static void move_hero(void)
{
    u16 n;
    const u8 *walk=hero_terrain_context==3?world_water_walk+(hero_attack_speed?17:0):
        hero_terrain_context==0 && hero_attack_speed?world_fast_ground_walk:world_walk_table;
    if(!hero_counter)
    {
        u16 previous=hero_direction,buttons=input&15,requested;
        hero_dy=hero_dx=0;
        if(hero_pending&128) { previous=hero_pending&3;hero_pending=previous; }
        requested=buttons&(1<<previous);
        if(!requested) requested=buttons;
        for(n=0;n<4;n++) if(requested&(1<<n)) break;
        if(n<4)
        {
            u8 cache[12];u16 row,column;
            u16 y=((hero_y>>8)-12)&255,x=((hero_x>>8)-12)&255;
            u16 offset=(y&248)*8+((x>>2)&62);
            s16 accepted;
            hero_direction=n;if(input&BUTTON_C) return;hero_counter=walk[0];
            for(row=0;row<3;row++) for(column=0;column<4;column++)
            {
                u16 p=offset+row*64+column*2;
                u8 high=p+1<0x600?sms_vram[0x3801+p]:128;
                if(!hero_items[12] && (high&32)) high|=128;
                cache[row*4+column]=high;
            }
            apply_water_collision_cache(cache);
            accepted=collision_direction(n,cache);
            if(accepted>=0)
            {
                const u8 *velocity=walk+1+accepted*4;
                if(n!=(u16)accepted) hero_pending=n|128;
                hero_direction=accepted;
                hero_dy=velocity[0]|((u16)velocity[1]<<8);
                hero_dx=velocity[2]|((u16)velocity[3]<<8);
            }
            hero_animation=(hero_animation+1)&3;
        }
    }
}

static void integrate_hero(void)
{
    if(hero_counter)
    {
        hero_counter--;
        hero_y+=hero_dy;hero_x+=hero_dx;
        if(!hero_counter) { hero_y&=0xff00;hero_x&=0xff00; }
    }
}

/* 37DA: eight-pixel knockback, using the pre-movement terrain cache. */
static void hurt_hero(u16 slot,const u8 *cache,u16 damage)
{
    const u8 *entity=world_actor_state+slot*0x30;
    u16 vertical=entity[10]<2,negative,blocked,position;
    hero_health=damage>=hero_health?0:hero_health-damage;
    sound_effect_main(0x91); /* 2ED5: hero hurt. */
    hero_hurt=48;
    negative=vertical?(hero_y>>8)<entity[0x11]:(hero_x>>8)<entity[0x13];
    position=vertical?hero_y>>8:hero_x>>8;
    if((negative && position<17) || (!negative && position>=(vertical?160:240))) return;
    blocked=vertical?(negative?(cache[1]|cache[2]):(cache[9]|cache[10])):
                     (negative?cache[4]:cache[7]);
    hero_x=(((hero_x>>8)+4)&248)<<8;hero_y=(((hero_y>>8)+4)&248)<<8;
    hero_animation=hero_counter=hero_state=0;hero_dx=hero_dy=0;
    if(!(blocked&128))
    {
        if(vertical) hero_y+=negative?-2048:2048;
        else hero_x+=negative?-2048:2048;
    }
}

/* 1EEE/1EF4: one heart per eight HP, partial hearts at two-HP steps.
 * Source HUD is prepared on phase 1 and displayed by the following IRQ. */
static void prepare_hero_health_bar(bool force)
{
    u16 n,remaining=hero_health,count=hero_max_health>>3;
    if(!force && ((world_clock()&3)!=1 || (hero_health==hero_health_drawn && hero_max_health==hero_health_capacity_drawn))) return;
    for(n=0;n<count;n++)
    {
        u16 tile=remaining>=8?0x8b:0x8f-(remaining>>1);
        u16 sms=0x1900|tile,index=21*32+15+n;
        if(remaining>=8) remaining-=8;else remaining=0;
        sms_vram[0x3d5e + n*2]=tile;sms_vram[0x3d5f+n*2]=0x19;
        md_map[index]=TILE_ATTR_FULL(1,1,0,0,16+(sms&511));
    }
    hero_health_drawn=hero_health;hero_health_capacity_drawn=hero_max_health;hero_health_pending=TRUE;
}

/* 1F25: one full/empty orb for each eight points of magic. */
static void prepare_hero_magic_bar(void)
{
    u16 n,count=hero_max_magic>>3;
    if((world_clock()&3)!=2 || (hero_magic==hero_magic_drawn && hero_max_magic==hero_magic_capacity_drawn)) return;
    for(n=0;n<count;n++)
    {
        u16 tile=hero_magic>=(n+1)*8?0x90:0x91;
        sms_vram[0x3dde + n*2]=tile;sms_vram[0x3ddf+n*2]=0x19;
        if(23*32+15+n<32*24) md_map[23*32+15+n]=TILE_ATTR_FULL(PAL1,1,0,0,16+256+tile);
    }
    hero_magic_drawn=hero_magic;hero_magic_capacity_drawn=hero_max_magic;hero_magic_pending=TRUE;hero_magic_delay=1;
}

/* 1F4B/085B: gold is prepared on phase 3 and presented on the next IRQ. */
static void prepare_hero_gold_bar(void)
{
    u16 n;
    if((world_clock()&3)!=3 || hero_gold==hero_gold_drawn) return;
    for(n=0;n<3;n++)
    {
        u16 tile=0xf0+(n==0?hero_gold/100:n==1?(hero_gold/10)%10:hero_gold%10);
        sms_vram[0x3dd0+n*2]=tile;sms_vram[0x3dd1+n*2]=0x18;
        md_map[23*32+8+n]=TILE_ATTR_FULL(PAL1,1,0,0,16+tile);
    }
    hero_gold_drawn=hero_gold;hero_gold_pending=TRUE;
}

static bool hero_patterns_pending;
static u16 hero_render_pose(void)
{
    u16 variant=hero_terrain_context!=3 && hero_selected_item==1?hero_weapon_level+1:0;
    if(variant>3) variant=0;
    return variant*32+hero_direction*8+hero_animation;
}

static u16 hero_collision_index(u16 which)
{
    return hero_casting?world_cast_collisions[hero_direction*2+which]:world_combat_collisions[hero_render_pose()*2+which];
}

/* 2FAA/2FB4 and 34A7/34BD/3661: fresh action, then ROM pose sequence.
 * Direction changes accept exactly one held cardinal button. Existing motion
 * continues through the shared integration tail. Other selected items pending. */
static void inventory_hud_icon(void);
static u16 dungeon_bitmap_pending;

static void update_hero_sprites(void);

/* 30BB/3021: a fresh heal activation costs magic even at full health.
 * Current normal exterior class heals sixteen, clamped to C0DA. */
static bool spend_spell_magic(void)
{
    static const u8 costs[4]={8,8,32,24};
    u16 cost=costs[hero_selected_item&3];
    if(hero_magic<cost) return FALSE;
    hero_magic-=cost;return TRUE;
}

static void spawn_hero_projectile(u16 type)
{
    u8 *e=world_spell_state;u16 descriptor=0x80a0+(hero_terrain_context!=3 && hero_selected_item==1?(hero_weapon_level+1)*8:0);
        /* 308B copies the hero record before either object's behavior. */
        memset(e,0,0x30);e[0]=type;e[2]=0xf0;e[3]=hero_flags;e[4]=hero_counter;e[5]=hero_hurt;
        e[8]=descriptor;e[9]=descriptor>>8;e[10]=hero_direction;e[14]=hero_attack_phase;
        e[0x10]=hero_y;e[0x11]=hero_y>>8;e[0x12]=hero_x;e[0x13]=hero_x>>8;
        e[0x15]=hero_dy>>8;e[0x17]=hero_dx>>8;
        e[0x18]=hero_health;e[0x19]=hero_attack;e[0x1a]=hero_defense;
        e[0x1b]=hero_collision_index(0);e[0x1c]=hero_collision_index(1);
}

static void activate_hero_item(void)
{
    if(hero_terrain_context==5) return;
    if(hero_terrain_context==3)
    {
        if(!world_spell_state[0]) { sound_effect_main(0xaa);spawn_hero_projectile(5); }
        return;
    }
    if(hero_selected_item<2)
    { hero_state=hero_selected_item?4:2;sound_effect_main(hero_selected_item?0x99:0x90); }
    else if(hero_selected_item==2 && game_save_state[15])
    {
        /* 2FBE/7226: remedy only consumes itself when cursed; no magic cost. */
        game_save_state[15]=0;hero_items[2]=0;hero_selected_item=0;
        sound_effect_main(0x97);inventory_hud_icon();
        wait_frame();world_clock_shift+=2;
    }
    else if((hero_selected_item==4 || hero_selected_item==5) && !world_spell_state[0])
    {
        if((hero_selected_item==5 || !hero_fire_charge) && !spend_spell_magic())
        {
            if(hero_selected_item==4)
            { hero_selected_item=0;inventory_hud_icon();wait_frame();world_clock_shift+=2; }
            return;
        }
        if(hero_selected_item==4) hero_fire_charge=(hero_fire_charge+1)&3;
        hero_state=10;sound_effect_main(hero_selected_item==4?0x92:0x93);
        spawn_hero_projectile(hero_selected_item==4?3:4);
    }
    else if(hero_selected_item==7 && spend_spell_magic())
    {
        u16 amount=hero_health+16;
        hero_health=amount>hero_max_health?hero_max_health:amount;
        sound_effect_main(0x97);
    }    else if(hero_selected_item==8 && hero_health!=hero_max_health)
    {
        /* 30D6/601C: refill one point per forced HUD update/two waits.
         * A potion at full health is retained. No magic is spent. */
        while(hero_health<hero_max_health)
        {
            hero_health++;prepare_hero_health_bar(TRUE);
            wait_frame();update_hero_sprites();wait_frame();
        }
        hero_items[8]=0;hero_selected_item=0;inventory_hud_icon();
        wait_frame();wait_frame();world_clock_shift+=2;
    }
}

static void attack_hero(void)
{
    u16 buttons=input&15,offset;
    if(hero_state==2 || hero_state==4) { hero_attack_phase=255;hero_state++; }
    if(buttons==1) hero_direction=0;
    else if(buttons==2) hero_direction=1;
    else if(buttons==4) hero_direction=2;
    else if(buttons==8) hero_direction=3;
    offset=hero_state==3?(hero_attack_speed?13:0):(hero_attack_speed?35:22);
    hero_attack_phase=(hero_attack_phase+1)&255;
    hero_animation=world_attack_sequences[offset+hero_attack_phase];
    if(!hero_animation) { hero_state=0;hero_attack_phase=0; }
}

static void prepare_hero_patterns(void)
{
    u16 pose=hero_state==9?128+(u16)((world_clock()&2)>>1):hero_terrain_context==3?134+hero_direction*2+(hero_animation&1):hero_casting?130+hero_direction:hero_render_pose(),n;
    if(pose!=hero_loaded_pose)
    {
        const u8 *source;
        if(pose>=134) source=world_water_bitmaps+(pose-134)*97;
        else if(pose>=130) source=world_cast_bitmaps+(pose-130)*145;
        else if(pose>=128) source=world_death_bitmaps+(pose-128)*97;
        else { u16 offset=world_combat_bitmap_index[pose*2]|((u16)world_combat_bitmap_index[pose*2+1]<<8);source=world_combat_bitmaps+offset; }
        hero_pattern_tiles=*source++;
        for(n=0;n<hero_pattern_tiles*8;n++)
        {
            memcpy(sms_vram+0x3e00+n*4,source,3);source+=3;
            sms_vram[0x3e03+n*4]=0;
        }
        convert_patterns_range(496,hero_pattern_tiles);hero_patterns_pending=TRUE;hero_loaded_pose=pose;
    }
}

/* SMS mode-4 sprites: eight 8x8 entries per active scanline; X clipping does
 * not remove an entry from the Y scan. This models SMS status, not MD limits. */
static void prepare_world_sms_sprite_overflow(u16 count)
{
    s8 edges[193];
    s16 used=0,top,bottom;
    u16 n,raw;
    memset(edges,0,sizeof(edges));
    for(n=0;n<count && n<64;n++)
    {
        raw=(vdpSpriteCache[n].y-145)&255;
        if(raw==208) break;
        top=raw<208?(s16)raw+1:(s16)raw-255;
        bottom=top+8;
        if(top<0) top=0;
        if(bottom>192) bottom=192;
        if(top>=bottom) continue;
        edges[top]++;edges[bottom]--;
    }
    world_sms_sprite_prepared_overflow=0;
    for(n=0;n<192;n++)
    {
        used+=edges[n];
        if(used>8) { world_sms_sprite_prepared_overflow=1;break; }
    }
}

static u16 dungeon_bitmap_pending;

/* Source0940 selects depth order or a four-phase object scan. */
static u16 add_world_sprite_scene(u16 order_phase,bool order_overflow,const u8 *hero_frame,s16 x,s16 y,bool visible,bool include_actors)
{
    u16 count;
    count=0;
    if(include_actors && (world_object_tick_count>=8 || order_overflow))
    {
        u16 n;
        for(n=0;n<32;n++)
        {
            u16 slot=world_sprite_order_slot(n,order_phase);
            if(!slot)
            { if(visible) count=add_sms_sprite_frame(count,x,y,hero_frame,0); }
            else count=add_world_ordered_actor_sprites(count,slot);
        }
    }
    else
    {
        count=include_actors?add_world_actor_sprites(0,y,255):0;
        if(visible) count=add_sms_sprite_frame(count,x,y,hero_frame,0);
        if(include_actors) count=add_world_actor_sprites(count,-1,y);
    }
    return count;
}

static u16 ending_hero_descriptor;
extern const u8 ending_held_frame[],ending_axe_frame[];

static void update_hero_sprites_for_frame(u16 order_phase,bool order_overflow)
{
    u16 pose=hero_render_pose(),count,frame_offset=world_combat_frame_index[pose*2]|((u16)world_combat_frame_index[pose*2+1]<<8);
    if(hero_patterns_pending && !(game_state==10 && transition_step==0))
    {
        if(hero_pattern_wait_frames) hero_pattern_wait_frames--;
        else { VDP_loadTileData(md_patterns+496*8,16+496,hero_pattern_tiles,CPU);hero_patterns_pending=FALSE; }
    }
    if(dungeon_bitmap_pending)
    { u16 tile=dungeon_bitmap_pending-1;VDP_loadTileData(md_patterns+tile*8,16+tile,6,CPU);dungeon_bitmap_pending=0; }
    if(house_animation_patterns_pending)
    { u16 tile=house_animation_patterns_pending-1;VDP_loadTileData(md_patterns+tile*8,16+tile,4,CPU);house_animation_patterns_pending=0; }
    if(world_loot_patterns_pending)
    {
        memcpy(sms_vram+0x3780,actor_loot_patterns+(world_loot_patterns_pending-1)*128,128);
        convert_patterns_range(444,4);VDP_loadTileData(md_patterns+444*8,16+444,4,CPU);world_loot_patterns_pending=0;
    }
    if(hero_magic_pending)
    {
        if(hero_magic_delay) hero_magic_delay--;
        else { VDP_setTileMapDataRect(BG_A,md_map+23*32+15,15,25,hero_max_magic>>3,1,hero_max_magic>>3,CPU);hero_magic_pending=FALSE; }
    }
    if(hero_gold_pending)
    { VDP_setTileMapDataRect(BG_A,md_map+23*32+8,8,25,3,1,3,CPU);hero_gold_pending=FALSE; }
    if(hero_health_pending)
    {
        VDP_setTileMapDataRect(BG_A,md_map+21*32+15,15,23,hero_max_health>>3,1,hero_max_health>>3,CPU);
        hero_health_pending=FALSE;
    }
    VDP_resetSprites();
    count=add_world_sprite_scene(order_phase,order_overflow,ending_hero_descriptor==0x8495?ending_held_frame:ending_hero_descriptor==0x84e1?ending_axe_frame:hero_casting?world_cast_frames+hero_direction*13:world_combat_frames+frame_offset,(hero_x>>8)+hero_scroll_x,(hero_y>>8)+hero_scroll_y,hero_flags&1,game_state!=10);
    prepare_world_sms_sprite_overflow(count);
    if(count && count<=64) { VDP_setSpriteLink(count-1,0);VDP_updateSprites(count,CPU); }
    else if(!count) { VDP_setSpriteFull(0,0,0,SPRITE_SIZE(1,1),0,0);VDP_updateSprites(1,CPU); }
    if(world_palette_pending) { set_world_palette();world_palette_pending=FALSE; }
}

static void update_hero_sprites(void)
{ update_hero_sprites_for_frame(world_clock(),world_sms_sprite_overflow); }

/* 1B0E: initial map construction folds cell changes into both tile maps. */
static void prepare_room_cell(u16 index,u8 value)
{
    if(index<160) scratch[0x800+index]=value;
}

/* 1A7C: all 21 source transformations; metadata selects positions/operation. */
static void prepare_room_transformation(void)
{
    u16 index=room_metadata[1],n;
    u8 value=0,below;
    switch(room_metadata[2])
    {
        case 0: value=0;break;
        case 1: index=room_metadata[0];value=room_metadata[1];break;
        case 2: value=0x15;break;
        case 3: value=3;break;
        case 4: value=4;break;
        case 5: prepare_room_cell(index,1);prepare_room_cell(index+16,1);return;
        case 6: prepare_room_cell(0x30,0x30);prepare_room_cell(0x40,0x31);prepare_room_cell(0x50,0x1f);return;
        case 7: prepare_room_cell(index,1);prepare_room_cell(index+16,4);return;
        case 8: prepare_room_cell(index,8);prepare_room_cell(index+1,8);return;
        case 9: prepare_room_cell(index,0x4d);return;
        case 10: prepare_room_cell(index,0x4c);return;
        case 11: prepare_room_cell(index,9);prepare_room_cell(index+16,6);prepare_room_cell(0x1b,0x4d);return;
        case 12: for(n=0;n<4;n++) prepare_room_cell(index+n,0);return;
        case 13: prepare_room_cell(index,0x0c);return;
        case 14: prepare_room_cell(index,0);return;
        case 15: prepare_room_cell(index,9);prepare_room_cell(room_metadata[0],9);return;
        case 16:
            prepare_room_cell(index,0);prepare_room_cell(index+1,0);
            prepare_room_cell(index+16,0);prepare_room_cell(index+17,0);
            prepare_room_cell(room_metadata[0],0x4d);return;
        case 17: prepare_room_cell(index,8);prepare_room_cell(index+1,8);prepare_room_cell(room_metadata[0],0x4d);return;
        case 18: prepare_room_cell(index,8);prepare_room_cell(index+1,8);prepare_room_cell(room_metadata[0],0);return;
        case 19: prepare_room_cell(index,9);prepare_room_cell(room_metadata[0],0x4d);return;
        case 20: prepare_room_cell(0x4a,0x0a);prepare_room_cell(0x5a,0x6b);return;
        default:return;
    }
    prepare_room_cell(index,value);
    /* 1ACA: remove the supporting tile only for these four original cells. */
    if(index+16>=160) return;
    below=scratch[0x810+index];
    if(below==0x27) prepare_room_cell(index+16,1);
    else if(below==0x28) prepare_room_cell(index+16,3);
    else if(below==0x29) prepare_room_cell(index+16,0);
    else if(below==0x39) prepare_room_cell(index+16,0x3a);
}

/* 1976/1BCD: persistent room flags are shared by their low-byte room ID. */
static void prepare_room_cells(u16 number)
{
    const u8 *record=number>=256?world_dungeon_metadata:world_room_metadata;
    u8 flags=game_save_state[0x50+(number&255)];
    u16 flag_room=world_graphics_class==1?house_return_room:number;
    if(number>=256)
    {
        game_save_state[0x50+(number&255)]|=0x10;
        if(flags&0x20) { prepare_room_cell(0x17,0);prepare_room_cell(0x18,0); }
        if(flags&0x40) { prepare_room_cell(0x31,0x18);prepare_room_cell(0x41,0);prepare_room_cell(0x51,0x19); }
        if(flags&0x80) { prepare_room_cell(0x3e,0x22);prepare_room_cell(0x4e,0);prepare_room_cell(0x5e,0x23); }
    }
    while(*record && *record!=(number&255)) record+=4;
    if(*record) memcpy(room_metadata,record+1,3);
    else { room_metadata[0]=255;room_metadata[1]=255;room_metadata[2]=0; }
    if(game_save_state[0x50+(flag_room&255)]&(1<<world_graphics_class)) prepare_room_transformation();
}

/* 190B/2279: reuse the original metatiles and reconstruct a 32x20 map. */
static void build_room_map(u8 *destination,u16 *native_map)
{
    u16 y,x;
    for(y=0;y<20;y++) for(x=0;x<32;x++)
    {
        u16 tile=scratch[0x800+(y/2)*16+x/2];
        u16 address=tile*8+(y&1)*4+(x&1)*2;
        destination[(y*32+x)*2]=scratch[address];
        destination[(y*32+x)*2+1]=scratch[address+1];
        native_map[y*32+x]=world_metatiles_md[address/2];
    }
}

static void decode_room_map(u16 number,u8 *destination,u16 *native_map)
{
    u16 offset=world_room_index[number*2]|((u16)world_room_index[number*2+1]<<8);
    decode_planes(world_room_streams+offset,scratch+0x800,1);
    prepare_room_cells(number);build_room_map(destination,native_map);
}

/* 5C40/5C18/5BF0: shared passage opening after the empty-cell guard. */
static void redraw_current_room(u32 redraw_started)
{
    u32 budget;
    prepare_room_cells(room_id);build_room_map(sms_vram+0x3800,world_new_md);
    memcpy(md_map,world_new_md,sizeof(world_new_md));
    /* 1976/2279/1E4E run in the foreground while IRQ audio/video continues.
     * Account for native work already spent, then retain the 0B95 VBlank
     * barrier before the map upload. HUD/IRQ phase remains approximate. */
    budget=(SYS_isPAL()?71364UL:59736UL)-3072;
    while(vtimer-redraw_started<WORLD_REDRAW_PREPARE_TSTATES/budget) wait_frame();
    wait_frame();
    VDP_setTileMapDataRect(BG_A,world_new_md,0,2,32,20,32,CPU);
}

static void open_dungeon_passage(u8 flag)
{
    u32 redraw_started=vtimer;
    u16 neighbor;
    game_save_state[0x50+(room_id&255)]|=flag;
    if(flag!=0x20)
    {
        neighbor=(room_id&240)|((room_id+(flag==0x40?-1:1))&15);
        game_save_state[0x50+neighbor]|=flag==0x40?0x80:0x40;
    }
    /* 1BF0/1BF7/1C06, then 5E90 re-applies persistent transformations. */
    sound_effect(0xa5); /* 5C4E queues this before the redraw begins. */
    redraw_current_room(redraw_started);
}

/* 5BB4..5C93: held direction opens an adjacent locked dungeon passage. */
static void check_dungeon_key_door(void)
{
    u16 x=hero_x>>8,y=hero_y>>8,probe_x,probe_y,index;
    u8 cell,flag;
    if(world_graphics_class!=2 || (!hero_items[15] && !hero_keys)) return;
    if(hero_direction==0)
    {
        if(!(input&BUTTON_UP) || y!=40) return;
        probe_x=x;probe_y=(u8)(y-16);cell=0x18;flag=0x20;
    }
    else if(hero_direction==2)
    {
        if(!(input&BUTTON_LEFT) || x!=32) return;
        probe_x=(u8)(x-16);probe_y=(u8)(y-8);cell=0x41;flag=0x40;
    }
    else if(hero_direction==3)
    {
        if(!(input&BUTTON_RIGHT) || x!=224) return;
        probe_x=(u8)(x+8);probe_y=(u8)(y-8);cell=0x4e;flag=0x80;
    }
    else return;
    index=(probe_y&248)*8+((probe_x>>2)&62);
    if(index>=0x500 || (sms_vram[0x3801+index]&0xe0)!=0xa0) return;
    /* 5C56 precedes the source's empty-cell guard, including key consumption. */
    if(!hero_items[15]) hero_keys=(hero_keys-1)&255;
    if(!scratch[0x800+cell]) return;
    open_dungeon_passage(flag);
}

/* 5EE1 searches six slots; slot six is overwritten if they are all occupied.
 * Source initializes only these five record bytes, preserving the others. */
static void spawn_room_key(void)
{
    u16 slot;u8 *loot;
    for(slot=0;slot<6;slot++) if(!world_loot_state[slot*0x30]) break;
    loot=world_loot_state+slot*0x30;sound_effect_main(0xa8);
    loot[0]=14;loot[1]=loot[3]=0;loot[0x11]=0x60;loot[0x13]=0x80;
}

static void open_cleared_room_passages(void)
{
    prepare_room_cells(room_id); /* 5E57 */
    if(scratch[0x817]==0x3d && scratch[0x818]) open_dungeon_passage(0x20);
    if(scratch[0x831]==0x33 && scratch[0x841]) open_dungeon_passage(0x40);
    if(scratch[0x83e]==0x38 && scratch[0x84e]) open_dungeon_passage(0x80);
}

/* 5F17 sets the consumed state before the source empty-cell guard. */
static void open_room_shutter(void)
{
    u8 flag=room_shutter_direction<2?0x20:room_shutter_direction==2?0x40:0x80;
    u16 cell=flag==0x20?0x18:flag==0x40?0x41:0x4e;
    if(room_shutter_state!=1) return;
    room_shutter_state=2;
    if(scratch[0x800+cell]) open_dungeon_passage(flag);
}

/* Source C060 uses the position before the common movement tail. C062
 * updates only when the resulting hero position is aligned to eight pixels. */
static u8 room_script_flags(u16 old_x,u16 old_y,u16 old_direction)
{
    u16 x=hero_x>>8,y=hero_y>>8;
    u16 coordinate=(((u8)(old_y-12)&248)<<3)+(((u8)(old_x-12)>>2)&62)+126;
    u8 flags=(u8)hero_direction;
    if(input&BUTTON_UP) flags|=4;
    if(room_script_coordinate_pending) { room_script_coordinate=coordinate;room_script_direction=old_direction;room_script_coordinate_pending=0; }
    if((u8)(x-40)<177 && !((u8)(y-40)&128)) flags|=0x80;
    if(!((x|y)&7))
    {
        flags|=0x10;
        if(room_script_coordinate!=coordinate) flags|=0x20;
        room_script_coordinate=coordinate;
        if(room_script_direction!=hero_direction) flags|=0x40;
        room_script_direction=hero_direction;
    }
    return flags;
}

/* 5F2B..5FAE: entering an occupied room shuts its designated edge. */
static void check_room_shutter(u8 flags)
{
    u8 direction,bit;u16 neighbor;u32 started;
    if(world_graphics_class!=2 || (flags&0xb0)!=0xb0 ||
       !((world_actor_count*2)&255) || room_shutter_state) return;
    direction=world_room_shutter_direction[room_id&255];if(!direction) return;
    direction--;room_shutter_state=1;room_shutter_direction=direction;
    started=vtimer;
    if(direction<2)
    {
        game_save_state[0x50+(room_id&255)]&=~0x20;
        scratch[0x817]=scratch[0x818]=0x3d;
    }
    else
    {
        if(direction==2 && scratch[0x831]==0x33) return;
        bit=direction==2?0x40:0x80;
        game_save_state[0x50+(room_id&255)]&=~bit;
        /* Closing uses DEC/INC L; opening uses the nibble-wrapped helper. */
        neighbor=(u8)(room_id+(direction==2?-1:1));
        game_save_state[0x50+neighbor]&=~(direction==2?0x80:0x40);
        if(direction==2) { scratch[0x831]=0x33;scratch[0x841]=0x34;scratch[0x851]=0x35; }
        else { scratch[0x83e]=0x38;scratch[0x84e]=0x39;scratch[0x85e]=0x3a; }
    }
    sound_effect(0xa5);redraw_current_room(started);
}

/* 5D4C/5EB1/5E75/5E9C/5FB1: C0A2 zero fires once after final particles.
 * 80 means consumed or empty on arrival. Persist reward before the redraw. */
static void check_dungeon_room_clear(void)
{
    u8 kind;
    if(world_graphics_class==1 || world_actor_count) return;
    kind=world_room_clear_kind[room_id];if(!kind) return;
    world_actor_count=0x80;
    if(kind==8 || kind==9)
    {
        if(kind==9)
        {
            u8 *saved=game_save_state+0x50+(room_id&255);
            if(!(*saved&8)) { *saved|=8;spawn_room_key(); }
        }
        open_room_shutter();
    }
    else if(kind>=5)
    {
        u8 flag=kind==6?8:(1<<world_graphics_class);
        u8 *saved=game_save_state+0x50+(room_id&255);
        if(*saved&flag) return;
        *saved|=flag;
        if(kind==6) { open_cleared_room_passages();spawn_room_key(); }
        else
        {
            u32 started=vtimer;
            if(kind==5 && (room_id&255)==0x13) spawn_room_key();
            sound_effect_main(0xa8);redraw_current_room(started);
        }
    }
    else if(kind==1) open_cleared_room_passages();
    else if(kind==2 && scratch[0x818]) open_dungeon_passage(0x20);
    else if(kind==3 && scratch[0x841]) open_dungeon_passage(0x40);
    else if(kind==4 && scratch[0x84e]) open_dungeon_passage(0x80);
}

/* 49A9: source cell and its two-by-two tile rectangle change together. */
void replace_world_actor_cell(u16 x,u16 y,u16 cell)
{
    u16 index=(y&240)|(x>>4),row=(y&248)>>3,col=(x>>3)&31,n,p;
    if(index>=160 || row>=19 || col>=31) return;
    scratch[0x800+index]=cell;
    for(n=0;n<4;n++)
    {
        u16 address=0x3800+(row+n/2)*64+(col+n%2)*2,word;
        sms_vram[address]=scratch[cell*8+n*2];sms_vram[address+1]=scratch[cell*8+n*2+1];
        word=sms_vram[address]|((u16)sms_vram[address+1]<<8);p=(row+n/2)*32+col+n%2;
        md_map[p]=world_new_md[p]=TILE_ATTR_FULL((word>>11)&1,(word>>12)&1,(word>>10)&1,(word>>9)&1,16+(word&511));
    }
    VDP_setTileMapDataRect(BG_A,md_map+row*32+col,col,row+2,2,2,32,CPU);
}

extern const u8 world_second_spell_terrain[],world_second_spell_probes[];
/* 35B7: special metadata cell records progress before preparing dependent cells. */
static void write_spell_terrain_cell(u16 index,u8 value)
{
    u16 n;u8 before[160],flag=1<<world_graphics_class;
    replace_world_actor_cell((index&15)*16,index&240,value);
    if(index!=room_metadata[0]) { sound_effect_main(0x9b);return; }
    n=0x50+((world_graphics_class==1?house_return_room:room_id)&255);
    if(game_save_state[n]&flag) return;
    game_save_state[n]|=flag;sound_effect(0xa8);
    memcpy(before,scratch+0x800,160);prepare_room_cells(room_id);
    for(n=0;n<160;n++) if(before[n]!=scratch[0x800+n])
        replace_world_actor_cell((n&15)*16,n&240,scratch[0x800+n]);
}

/* 3A9A/3591: both probes run even when the first has changed terrain. */
bool mutate_world_spell_terrain(u8 *entity,u16 level)
{
    u16 probe;bool changed=FALSE;
    for(probe=0;probe<2;probe++)
    {
        u16 offset=probe*8+entity[10]*2;
        u8 y=entity[0x11]+world_second_spell_probes[offset];
        u8 x=entity[0x13]+world_second_spell_probes[offset+1];
        u16 index=(y&240)|(x>>4),table=room_id>=256?0:level==1?21:9;
        const u8 *record=world_second_spell_terrain+table;
        if(index>=160) continue;
        while(*record && *record!=scratch[0x800+index]) record+=4;
        if(!*record) continue;
        changed=TRUE;write_spell_terrain_cell(index,record[1]);
        index+=16;
        if(index<160 && scratch[0x800+index]==record[2]) write_spell_terrain_cell(index,record[3]);
    }
    return changed;
}

/* 5C96 marks passages in the specified room; E can differ from this room. */
static void mark_contact_passage(u16 number,u8 flag)
{
    u16 neighbor;
    game_save_state[0x50+(number&255)]|=flag;
    if(flag==0x20) return;
    neighbor=(number&240)|((number+(flag==0x40?-1:1))&15);
    game_save_state[0x50+neighbor]|=flag==0x40?0x80:0x40;
}

/* Contact prefixes run before existing shutter and clear suffixes. */
static void check_room_contact(u8 flags)
{
    u16 n;u8 *saved;
    const u16 *record;
    if(world_graphics_class!=2) return;
    for(n=0;n<11;n++) if(world_room_contacts[n][0]==room_id) break;
    if(n==11) return;
    record=world_room_contacts[n];saved=game_save_state+0x50+(room_id&255);
    if(record[1]==3) /* 5CEC: a cleared cell, independently of enemy count. */
    {
        if((*saved&4) || scratch[0x800+record[3]]) return;
        *saved|=4;open_cleared_room_passages();return;
    }
    if((flags&0x77)!=0x14 || room_script_coordinate!=record[2]) return;
    if(record[1]==1) /* 5C96: persistent flag is set before the repeat guard. */
    {
        u8 already=*saved&4;u32 started=vtimer;
        *saved|=4;if(already) return;
        if(record[4]&1) mark_contact_passage(record[3],0x20);
        if(record[4]&4) mark_contact_passage(record[3],0x40);
        if(record[4]&8) mark_contact_passage(record[3],0x80);
        sound_effect(0xa5);redraw_current_room(started);
    }
    else /* 5CC7: the marker cell itself is the repeat guard. */
    {
        if(scratch[0x81b]==0x4d) return;
        if(scratch[0x84e]) open_dungeon_passage(0x80); /* Source E is 3. */
        replace_world_actor_cell(176,16,0x4d);
    }
}

/* Stationary UP scripts: preserve flag-before-repeat and prefix/suffix order. */
static void check_room_puzzle(u8 flags,u16 stage)
{
    u16 n;const u16 *record;u8 *saved,already;u32 started;
    if(world_graphics_class!=2 || (flags&0x77)!=0x14) return;
    for(n=0;n<31;n++) if(world_room_puzzles[n][0]==room_id) break;
    if(n==31) return;
    record=world_room_puzzles[n];
    if(record[4]!=stage || room_script_coordinate!=record[2]) return;
    saved=game_save_state+0x50+(room_id&255);already=*saved&4;
    *saved|=4;if(already) return;
    if(record[1]==5)
    {
        u16 cell;
        open_cleared_room_passages();
        /* All fourteen 5E45 rooms use transformation 9. Original 1B0E
         * updates the software map/VDP queue even if no edge redraw occurs. */
        cell=room_metadata[1];
        replace_world_actor_cell((cell&15)*16,cell&240,scratch[0x800+cell]);
        return;
    }
    started=vtimer;redraw_current_room(started); /* 5E90 has no sound request. */
    if(record[1]==4)
    {
        if(record[3]<2) { if(scratch[0x818]) open_dungeon_passage(0x20); }
        else if(record[3]==2) { if(scratch[0x841]) open_dungeon_passage(0x40); }
        else { if(scratch[0x84e]) open_dungeon_passage(0x80); }
        return;
    }
    sound_effect_main(0xa8);
    if(record[1]==2) { game_save_state[0x50+record[3]]|=4;sound_effect_main(0xa8); }
    else if(record[1]==3) { sound_effect_main(0xa8);spawn_room_key(); }
}

extern const u8 reward_labels[],reward_label_index[],reward_hero_bitmap[],reward_hero_frame[];
extern const u8 fairy_heart_icon[],fairy_magic_icon[];
static volatile u16 item_reward_active,item_reward_number;
static volatile u8 world_boss_state; /* C0AE, cleared by gem appearance. */
static bool boss_death_music_hold;
extern const u8 gem_labels[],gem_label_index[],gem_window_icons[],gem_reward_hero_frame[],gem_tile_table[];
static void update_world_music(void);

/* 6317: the acquisition window keeps the room and its actors frozen. */
static void prepare_hero_armor_palette(void);
static void show_item_reward_text(u16 item,u16 index,const u8 *custom_label)
{
    bool gem=index>=10;
    u16 n,count,label;
    const u8 *labels=gem?gem_labels:reward_labels;
    const u8 *indices=gem?gem_label_index:reward_label_index;
    const u8 *hero_frame=gem?gem_reward_hero_frame:reward_hero_frame;
    if(gem) index-=10;
    label=indices[index*2]|((u16)indices[index*2+1]<<8);
    u32 started;
    item_reward_active=1;item_reward_number=item;
    memcpy(house_dialogue_backup,sms_vram+0x3800,0x600);
    memcpy(house_dialogue_backup+0x600,sms_vram+0x1a00,0x380);
    memcpy(house_dialogue_backup+0x980,sms_vram+0x3780,128);
    for(n=0x3d00;n<0x3e00;n+=2) { sms_vram[n]=255;sms_vram[n+1]=0x18; }
    draw_frame(0x3cc2,30,5);map_origin=0x3800;draw_map();
    load_mono(0x1a00,normal_font,28*8,3,TRUE);
    if(gem) memcpy(sms_vram+0x3780,gem_window_icons+index*32,32);
    else if(item==42) memcpy(sms_vram+0x3780,fairy_heart_icon,128);
    else if(item==28) memcpy(sms_vram+0x3780,fairy_magic_icon,128);
    else memcpy(sms_vram+0x3780,inventory_icons+item*128,128);
    draw_text(0x3d46,custom_label?custom_label:labels+label);
    if(custom_label) { prepare_hero_armor_palette();sms_palette[31]=(world_clock()&2)?2:1;set_world_palette(); }
    for(n=0;n<reward_hero_bitmap[0]*8;n++)
    {
        memcpy(sms_vram+0x3e00+n*4,reward_hero_bitmap+1+n*3,3);
        sms_vram[0x3e03+n*4]=0;
    }
    convert_patterns_range(208,28);convert_patterns_range(444,4);convert_patterns_range(496,6);
    VDP_loadTileData(md_patterns+208*8,224,28,CPU);
    VDP_loadTileData(md_patterns+444*8,460,4,CPU);
    VDP_loadTileData(md_patterns+496*8,512,6,CPU);
    VDP_resetSprites();count=add_world_sprite_scene(world_clock(),world_sms_sprite_overflow,hero_frame,hero_x>>8,hero_y>>8,TRUE,TRUE);
    prepare_world_sms_sprite_overflow(count);
    VDP_setSpriteLink(count-1,0);VDP_updateSprites(count,CPU);
    draw_map();sound_music(0x8c);
    started=vtimer;while(vtimer-started<180) wait_frame();
    do { wait_frame(); } while(!(input&(BUTTON_UP|BUTTON_DOWN|BUTTON_LEFT|BUTTON_RIGHT|BUTTON_B|BUTTON_C)));
    started=vtimer;update_world_music();hero_state=0;
    memcpy(sms_vram+0x3800,house_dialogue_backup,0x600);
    memcpy(sms_vram+0x1a00,house_dialogue_backup+0x600,0x380);
    memcpy(sms_vram+0x3780,house_dialogue_backup+0x980,128);
    convert_patterns_range(208,28);convert_patterns_range(444,4);
    VDP_loadTileData(md_patterns+208*8,224,28,CPU);VDP_loadTileData(md_patterns+444*8,460,4,CPU);
    inventory_hud_icon();hero_loaded_pose=65535;prepare_hero_patterns();update_hero_sprites();
    /* 637D..638A: source window clear and 7219 HUD restoration precede
     * the shared full redraw. Include native work already spent. */
    {
        u32 budget=(SYS_isPAL()?71364UL:59736UL)-3072;
        u32 cost=SYS_isPAL()?333564UL:324168UL;
        while(vtimer-started<(cost+budget-1)/budget) wait_frame();
    }
    redraw_current_room(vtimer);
    item_reward_active=0;
}

/* 4BF5..4C3E: first free transient slot, then byte-wrapped particle bounds. */
static void spawn_world_boss_particle(u8 *entity,u8 roll)
{
    u16 slot;u8 y,x;u8 *particle;
    for(slot=8;slot<16;slot++) if(!world_actor_state[slot*0x30]) break;
    if(slot==16) return;
    y=(roll&0x3c)+entity[0x11]-0x10;
    if((u8)(y-0x18)>=0x80) return;
    x=(((roll>>4)|(roll<<4))&0x3c)+entity[0x13]-0x20;
    if((u8)(x-0x18)>=0xd0) return;
    particle=world_actor_state+slot*0x30;
    particle[0x11]=y;particle[0x13]=x;
    particle[0]=1;particle[1]=particle[7]=0;
}

static void show_item_reward(u16 item,u16 index)
{ show_item_reward_text(item,index,NULL); }

/* 4BA4..4C5C: boss death records defeat before its 180-tick animation. */
void tick_world_boss_death(u8 *entity)
{
    u16 slot;u8 dungeon=(u8)world_dungeon_number;
    if(!entity[1])
    {
        boss_death_music_hold=TRUE; /* 1CAF is not called during the death/gem wait. */
        if(dungeon>=10) hero_state=12;
        game_save_state[0x1e + dungeon]=1;
        memset(world_actor_state+0x180,0,0x180);
        entity[3]&=~0x41;entity[0x28]=180;entity[1]=2;
    }
    else if(entity[1]==2)
    {
        if(!--entity[0x28]) { entity[1]=4;return; }
        /* The source uses LD A,R here and 04E1 for placement. As with other
         * actors, SGDK random remains provisional until that stream is ported. */
        if(random()&3) return;
        for(slot=8;slot<16;slot++) if(!world_actor_state[slot*0x30]) break;
        if(slot<16) spawn_world_boss_particle(entity,(u8)random());
    }
    else if(entity[1]==4)
    {
        sound_effect(0xb0);entity[1]=entity[0]=0;
        if(dungeon<10) entity[0]=0x0f;
        else game_state=14; /* 6EBE ending dispatch. */
    }
}

/* 2A6B..2ACC: gem appearance, contact gate and dungeon progression reward. */
void tick_world_gem(u8 *entity)
{
    u16 tile=gem_tile_table[((u8)(world_dungeon_number-1)*2)&255];
    if(!entity[1])
    {
        world_boss_state=0;entity[2]=tile;entity[8]=0xcd;entity[9]=0x2a;
        entity[13]=entity[12]=entity[11]=entity[0x1d]=0;
        entity[3]=1;entity[1]=2;entity[0x11]=0x1c;entity[0x13]=0x80;
    }
    else if(entity[1]==2 && hero_state==1) { entity[3]|=2;entity[1]=4; }
    if(!entity[0x1d] && !(entity[3]&4)) return;
    memset(entity,0,0x30);sound_effect(0x96);boss_death_music_hold=FALSE;
    game_save_state[0x1e + (u8)world_dungeon_number]=0x80;
    /* 631A/631D: flag the current room and apply its acquisition transform. */
    {
        u16 n,number=world_graphics_class==1?house_return_room:room_id;
        u8 before[160];memcpy(before,scratch+0x800,160);
        game_save_state[0x50+(number&255)]|=1<<world_graphics_class;
        prepare_room_transformation();
        for(n=0;n<160;n++) if(before[n]!=scratch[0x800+n])
            replace_world_actor_cell((n&15)*16,n&240,scratch[0x800+n]);
    }
    if(world_dungeon_number>=1 && world_dungeon_number<=9)
        show_item_reward((tile+0x9f)&255,9+world_dungeon_number);
    { u8 capacity=hero_max_health+8;if(capacity<0x81) hero_max_health=capacity; }
    hero_magic=hero_max_magic;prepare_hero_magic_bar();
    while(hero_health!=hero_max_health)
    {
        hero_health=(u8)(hero_health+1);prepare_hero_health_bar(TRUE);
        sound_effect(0x95);wait_frame();update_hero_sprites();wait_frame();
    }
    update_world_music();
}

/* 5D59: write room bit 4 before the repeat and weapon ownership guards. */
static u16 begin_dungeon_item_reward(u8 flags)
{
    u16 n,index;const u16 *record;u8 *saved,already,before[160];
    if(world_graphics_class!=2 || (flags&0x77)!=0x14) return 0;
    for(n=0;n<10;n++) if(world_item_rewards[n][0]==room_id) break;
    if(n==10) return 0;record=world_item_rewards[n];index=n;
    if(room_script_coordinate!=record[1]) return 0;
    saved=game_save_state+0x50+(room_id&255);already=*saved&4;*saved|=4;
    if(already) return 0;
    memcpy(before,scratch+0x800,160);prepare_room_cells(room_id);
    for(n=0;n<160;n++) if(before[n]!=scratch[0x800+n])
        replace_world_actor_cell((n&15)*16,n&240,scratch[0x800+n]);
    if(record[5] && hero_weapon_level) return 0;
    if(record[2]==1) { hero_weapon_level=record[3];hero_items[1]=record[3]; }
    else hero_items[record[2]]=record[3];
    if(record[2]==14) hero_attack_speed=hero_items[14];
    return index+1;
}

static void check_dungeon_item_reward(u8 flags)
{
    u16 reward=begin_dungeon_item_reward(flags);
    if(reward) show_item_reward(world_item_rewards[reward-1][4],reward-1);
}

extern const u8 dungeon_animation_bitmaps[];
/* 6A6E..6AA2: queue six tile patterns for the next presentation frame. */
static void animate_dungeon_bitmaps(void)
{
    static const u8 order[]={0,1,2,1};
    u16 tile,phase;u8 clock=world_clock();
    if(world_graphics_class!=2 || (clock&7)) return;
    tile=scratch[0x30];phase=order[(clock&24)>>3];
    memcpy(sms_vram+tile*32,dungeon_animation_bitmaps+phase*192,192);
    convert_patterns_range(tile,6);dungeon_bitmap_pending=tile+1;
}

/* 6AA5..6AEA: four-cell dungeon floor scan, eight overlapping poses.
 * Only advance the phase when matching cells exist; scan resumes after pose 15. */
static void animate_dungeon_cells(void)
{
    static const u8 poses[]={0x41,0x4e,0x4f,0x50,0x50,0x4f,0x4e,0x41,0x41};
    u16 n,changed=0;
    if(world_graphics_class!=2) return;
    if(!(dungeon_animation_phase&1))
    {
        u8 phase=dungeon_animation_phase>>1;
        for(n=dungeon_animation_scan;n<dungeon_animation_scan+4;n++)
            if(scratch[0x800+n]==poses[phase])
            { replace_world_actor_cell((n&15)*16,n&240,poses[phase+1]);changed++; }
        if(!changed) goto advance;
    }
    dungeon_animation_phase=(dungeon_animation_phase+1)&15;
    if(dungeon_animation_phase) return;
advance:
    dungeon_animation_scan+=4;
    if(dungeon_animation_scan>=0x90) dungeon_animation_scan=0x20;
}

static void save_room_actor_mask(u16 number);
static u8 saved_room_actor_mask(u16 number);

/* 1816..181F: C0CE plus the low byte of C037, within the save record. */
static void load_current_world_actors(u16 number)
{
    boss_death_music_hold=FALSE;
    load_world_actors_progression(number,saved_room_actor_mask(number),
        game_save_state[0x1e + (u8)world_dungeon_number],sms_vram,md_patterns);
}


/* 21C5/21CB: only C0B9 changes; C0BA retains the dungeon layer. */
static u16 neighboring_room(u16 direction)
{
    if(direction<2) return (room_id&256)|((room_id+(direction==0?-16:16))&255);
    return (room_id&496)|((room_id+(direction==2?-1:1))&15);
}

/* 21D7..2236: incorrect exits loop to the same forest clearing. */
static u16 resolve_room_transition(u16 direction)
{
    u16 number=neighboring_room(direction);
    bool correct=FALSE;
    if(world_graphics_class || (room_id&255)!=0x77 || (number&255)==0x76)
    { forest_maze_progress=0;return number; }
    forest_maze_progress++;
    switch(forest_maze_progress)
    {
        case 1: correct=(number&255)==0x78 && (hero_y>>8)>=0x60;break;
        case 2: correct=(number&255)==0x67;break;
        case 3: correct=(number&255)==0x78 && (hero_y>>8)<0x60;break;
        case 4: correct=(number&255)==0x87;break;
        case 5: correct=(number&255)==0x67;break;
    }
    if(!correct) forest_maze_progress=0;
    return correct && forest_maze_progress==5?number:room_id;
}

/* Bank 5 BE78: the destination palette is selected before its map scrolls. */
static void prepare_dungeon_palette(u16 number)
{
    u16 n,index;
    world_dungeon_dark=0;
    for(n=0;n<38;n++) if((number&255)==world_dungeon_dark_rooms[n]) world_dungeon_dark=1;
    index=(world_dungeon_dark || world_dungeon_number>10)?0:world_dungeon_number;
    for(n=0;n<16;n++) sms_palette[n]=world_dungeon_palettes[index*16+n];
}

static void begin_room_transition(void)
{
    u16 direction,number;
    if((hero_x>>8)<16) direction=2;
    else if((hero_x>>8)>=241) direction=3;
    else if((hero_y>>8)<16) direction=0;
    else if((hero_y>>8)>=161) direction=1;
    else return;
    if(world_graphics_class==1) return;
    number=neighboring_room(direction);
    if(!world_graphics_class && (number<16 || (number&15)==15)) return;
    if(world_room_index[number*2]==255 && world_room_index[number*2+1]==255) return;
    if(direction==2) hero_x=0x1000;
    else if(direction==3) hero_x=0xf000;
    else if(direction==0) hero_y=0x1000;
    else hero_y=0xa000;
    hero_counter=0;hero_dy=hero_dx=0;
    save_room_actor_mask(room_id);
    hide_world_objects();
    game_state=10;transition_direction=direction;transition_stage=0;transition_step=0;
    transition_pose_prepared=FALSE;
    memcpy(title_map,sms_vram+0x3800,0x500);
    memcpy(world_old_md,world_new_md,sizeof(world_old_md));
    /* 21C2 -> 0938 rebuilds the SAT immediately; do not retain the previous
     * frame's monster sprites until the next transition update. */
    hero_flags|=1;update_hero_sprites();
}

/* 2099..20AC: the upward path makes two extra 1280-byte buffer exchanges.
 * 79,385 Z80 T states * 15 master clocks / 7 clocks per 68000 cycle.
 * DBRA takes ten 68000 cycles per iteration; interrupts remain enabled. */
static void retain_room_map_swap_work(void)
{
    u16 iterations=17010;
    __asm__ volatile ("1: dbra %0,1b" : "+d" (iterations));
}

/* 2C63/369F prepares with the old terrain context before 2C8D classifies arrival. */
static void prepare_arrival_pose(void)
{
    hero_state=0;hero_flags=3;hero_animation=0;prepare_hero_patterns();transition_pose_prepared=TRUE;
    if(SYS_isPAL() && transition_direction==1 && hero_patterns_pending) hero_pattern_wait_frames=1;
    else hero_terrain_context=classify_hero_terrain();
}

static void step_room_transition(void)
{
    u16 y,extent=transition_direction<2?20:32;
    if(transition_stage==4)
    {
        if(transition_loading_frames) transition_loading_frames--;
        /* The right-exit preparation crosses an IRQ after 2C63 initializes animation. */
        if(transition_direction==3 && !SYS_isPAL() && transition_loading_frames==1)
        { hero_state=0;hero_flags=3;hero_animation=0;transition_pose_prepared=TRUE; }
        if(!transition_loading_frames)
        {
            prepare_arrival_pose();
            if(hero_pattern_wait_frames) { transition_stage=6;return; }
            game_state=12;map_queue=FALSE;
        }
        return;
    }
    if(transition_stage==6)
    {
        hero_terrain_context=classify_hero_terrain();transition_pose_prepared=TRUE;
        game_state=12;map_queue=FALSE;return;
    }
    if(transition_stage==5 && transition_step==extent)
    {
        /* The right-exit room preparation crosses one additional SMS IRQ
         * after the destination position/pose has already been initialized. */
        game_state=12;map_queue=FALSE;return;
    }
    if(transition_stage==0)
    {
        room_id=resolve_room_transition(transition_direction);
        if(world_graphics_class==2)
        {
            prepare_dungeon_palette(room_id);world_palette_pending=TRUE;
            game_save_state[0x50+(room_id&255)]|=0x10; /* 1BCD */
        }
        decode_room_map(room_id,animation_map,world_new_md);
        if(transition_direction==0) retain_room_map_swap_work();
        if(transition_direction>=2)
        {
            VDP_setScrollingMode(HSCROLL_LINE,VSCROLL_PLANE);
            VDP_setTileMapDataRect(BG_A,world_new_md,32,2,32,20,32,DMA_QUEUE);
        }
        transition_stage=1;return;
    }
    /* Match the setup frames observed around 21A1/2260 before scrolling. */
    if(transition_stage<(SYS_isPAL()?2:3)) { transition_stage++;return; }
    if(transition_step==extent)
    {
        if(transition_direction>=2)
        {
            memset(world_hscroll,0,sizeof(world_hscroll));
            VDP_setHorizontalScrollLine(BG_A,0,world_hscroll,224,DMA_QUEUE);
            VDP_setTileMapDataRect(BG_A,world_new_md,0,2,32,20,32,DMA_QUEUE);
        }
        if(transition_direction==2) hero_x=0xf000;
        else if(transition_direction==3) hero_x=0x1000;
        else if(transition_direction==0) hero_y=0xa000;
        else hero_y=0x1000;
        hero_scroll_x=hero_scroll_y=0;
        hero_pending=0;hero_counter=0;hero_dy=hero_dx=0;
        dungeon_animation_scan=dungeon_animation_phase=0;dungeon_bitmap_pending=0;
        if(transition_direction==0) retain_room_map_swap_work();
        load_current_world_actors(room_id);
    room_shutter_state=(world_actor_count&128)?2:0;room_shutter_direction=0;room_script_coordinate_pending=1;
        if(world_actor_tiles)
            VDP_loadTileData(md_patterns+256*8,16+256,world_actor_tiles,DMA_QUEUE);
        game_state=(transition_direction==3 && !SYS_isPAL())?10:12;
        if(game_state==10) transition_stage=5;
        if(world_actor_load_tstates || world_graphics_class==2)
        {
            /* Even a cleared dungeon executes 24C5/1780/2C63/5B20/1CAF:
             * empty graphics do not mean zero foreground work.
             * 1780/032A/1D0D: preserve the foreground graphics work skipped by
             * preconverted assets. Quantize source T states to video frames.
             * 3420 master cycles/line, 15 master cycles per Z80 T; reserve 3072 T for
             * interrupt work and 20000 T for loader control flow. The dynamic
             * PSG/VDP contention model is still approximate outside tested paths. */
            u32 budget=(SYS_isPAL()?71364UL:59736UL)-3072;
            transition_loading_frames=(world_actor_load_tstates+20000+budget-1)/budget;
            transition_stage=4;game_state=10;
        }
        if(transition_stage!=4)
        {
            prepare_arrival_pose();
            if(hero_pattern_wait_frames) { transition_stage=6;game_state=10; }
        }
        map_queue=FALSE;return;
    }
    transition_step++;
    if(transition_direction>=2)
    {
        s16 scroll=(transition_direction==2?8:-8)*transition_step;
        for(y=16;y<176;y++) world_hscroll[y]=scroll;
        VDP_setHorizontalScrollLine(BG_A,0,world_hscroll,224,DMA_QUEUE);
        hero_scroll_x=(transition_direction==2?8:-8)*min(transition_step,28);
        if(transition_step==32)
        {
            /* Both planes' visible copies are now the destination. Reset the
             * scroll and map origin together on the following VBlank. */
            memcpy(sms_vram+0x3800,animation_map,0x500);
        }
        return;
    }
    for(y=0;y<20;y++)
    {
        const u16 *source;
        u16 source_y;
        if(transition_direction==0)
        {
            if(y<transition_step) { source=world_new_md;source_y=20-transition_step+y; }
            else { source=world_old_md;source_y=y-transition_step; }
        }
        else
        {
            if(y>=20-transition_step) { source=world_new_md;source_y=y+transition_step-20; }
            else { source=world_old_md;source_y=y+transition_step; }
        }
        memcpy(md_map+y*32,source+source_y*32,64);
    }
    hero_scroll_y=(transition_direction==0?8:-8)*min(transition_step,18);
    VDP_setTileMapDataRect(BG_A,md_map,0,2,32,20,32,DMA_QUEUE);
    if(transition_step==20) memcpy(sms_vram+0x3800,animation_map,0x500);
}

/* 6594/65D0: matched village doorway and interior exit. The room loader
 * is native; interaction scripts are handled separately from this transition. */
extern const u8 world_music_rooms[];
static void update_world_music(void)
{
    u16 n,track=world_graphics_class==1?(room_id==0xbf?0x8b:0x87):0x82;
    if(world_graphics_class==2)
    {
        track=0x83;
        for(n=0;n<8;n++) if(world_actor_state[n*0x30+3]&0x40) track=0x86;
    }
    if(!world_graphics_class) for(n=0;n<11;n++) if(room_id==world_music_rooms[n]) track=0x84;
    if(sound_current_track!=track) sound_music(track);
}

static void check_house_talk(u16 old_x,u16 old_y,u8 flags);
static void check_house_service(u16 old_x,u16 old_y);
static void save_reset_new_game(void);
static void save_init(void);
static void save_prepare_checkpoint_resume(void);

static void load_house_room(u16 number,u16 graphics_class)
{
    const u8 *extra=graphics_class==2?world_dungeon_extra_meta:graphics_class==1?world_house_extra_meta:world_extra_meta;
    const u8 *source,*palette=graphics_class==2?world_dungeon_palette:graphics_class==1?world_house_palette:world_palette;
    const u8 *background=graphics_class==2?world_dungeon_background_rle:graphics_class==1?world_house_background_rle:world_background_rle;
    u16 n,destination=0x400;
    world_dungeon_dark=0;
    if(graphics_class==2)
    {
        for(n=0;n<38;n++) if((number&255)==world_dungeon_dark_rooms[n]) world_dungeon_dark=1;
        palette=world_dungeon_palettes+((world_dungeon_dark || world_dungeon_number>10)?0:world_dungeon_number*16);
    }
    if(number!=room_id) save_room_actor_mask(room_id);
    world_graphics_class=graphics_class;room_id=number;house_animation_scan=0;house_animation_patterns_pending=0;
    if(!save_service_phase) VDP_setEnable(FALSE);
    memset(scratch,0,0x800);
    source=decode_planes(background,sms_vram,4);
    decode_planes(source,scratch,2);
    if(!graphics_class) { memcpy(scratch+0x1c0,scratch+0x98,8);memcpy(scratch+0x1f0,scratch+0x98,8); }
    while(*extra<128) { memcpy(scratch+destination,scratch+*extra++*8,8);destination+=8; }
    extra++;
    for(n=0x401;n<destination;n+=2) scratch[n]=(scratch[n]&31)|*extra++;
    for(n=0;n<0x220;n++)
    {
        u16 word=scratch[n*2]|((u16)scratch[n*2+1]<<8);
        world_metatiles_md[n]=TILE_ATTR_FULL((word>>11)&1,(word>>12)&1,(word>>10)&1,(word>>9)&1,16+(word&511));
    }
    decode_room_map(number,sms_vram+0x3800,world_new_md);
    if(graphics_class==2) game_save_state[0x50+(number&255)]|=0x10; /* 1BCD: visited */
    dungeon_animation_scan=dungeon_animation_phase=0;dungeon_bitmap_pending=0;
        load_current_world_actors(number);
    room_shutter_state=(world_actor_count&128)?2:0;room_shutter_direction=0;room_script_coordinate_pending=1;
    for(n=0;n<16;n++) sms_palette[n]=palette[n];
    hero_direction=graphics_class?0:1;hero_state=0;hero_animation=hero_counter=hero_pending=hero_hurt=hero_casting=0;
    hero_dx=hero_dy=0;hero_flags=3;hero_loaded_pose=65535;prepare_hero_patterns();
    convert_patterns(512);
    if(save_service_phase)
    {
        /* Room is hidden but the HUD remains live: bounded VBlank transfers. */
        for(n=0;n<512;n+=128) { VDP_loadTileData(md_patterns+n*8,16+n,128,DMA_QUEUE);wait_frame(); }
        hero_patterns_pending=FALSE;world_palette_pending=FALSE;set_world_palette();
        map_origin=0x3800;map_queue=TRUE;draw_map();wait_frame();map_queue=FALSE;
    }
    else
    {
        VDP_loadTileData(md_patterns,16,512,CPU);
        hero_patterns_pending=FALSE;world_palette_pending=FALSE;set_world_palette();
        map_origin=0x3800;draw_map();if(!door_transition_loading) VDP_setEnable(TRUE);
    }
    update_hero_sprites();game_state=12;
}

/* Consecutive portal waits must each advance the emulated frame counter. */
static void portal_wait_frame(void)
{
    u32 before=vtimer;
    do { wait_frame(); } while(vtimer==before);
}

/* 5CFB..5D4B: a successful portal skips the remaining room script.
 * Stage preserves whether the original clear handler precedes this call. */
static bool check_dungeon_portal(u8 flags,u16 stage,bool prefix_redraw)
{
    u16 n,word,arrival_x=128,arrival_y=88,fraction_x=hero_x&255,fraction_y=hero_y&255;
    u32 started,budget,loading_frames;
    const u16 *record;
    if(world_graphics_class!=2 || (flags&0x30)!=0x30) return FALSE;
    for(n=0;n<36;n++) if(world_room_portals[n][0]==room_id) break;
    if(n==36) return FALSE;
    record=world_room_portals[n];
    if(record[3]!=stage || record[1]!=room_script_coordinate) return FALSE;
    save_room_actor_mask(room_id);room_id=record[2];
    sound_effect_main(0xa6);map_queue=FALSE;
    /* Foreground work following a preceding redraw can cross the next IRQ.
     * This phase allowance remains approximate outside measured fixtures. */
    if(prefix_redraw && !SYS_isPAL()) portal_wait_frame();
    for(n=0;n<20;n++)
    {
        portal_wait_frame();
        for(word=n;word<=768;word+=20)
            VDP_setTileMapXY(BG_A,TILE_ATTR_FULL(1,1,0,0,16+255),word&31,(word>>5)+2);
    }
    VDP_setEnable(FALSE);hide_world_objects();
    /* 2260/190B/2279 execute before the arrival position is written. */
    started=vtimer;
    decode_room_map(room_id,sms_vram+0x3800,world_new_md);
    while(vtimer-started<3) portal_wait_frame();
    for(n=0;n<160;n++) if(scratch[0x800+n]==12)
    { arrival_x=(n&15)*16+8;arrival_y=(n&240)+16;break; }
    hero_x=(arrival_x<<8)|fraction_x;hero_y=(arrival_y<<8)|fraction_y;hero_direction=1;
    game_state=8;started=vtimer;
    /* The dungeon background is unchanged. Reuse its converted patterns;
     * loading every pattern through the generic house loader adds MD work
     * that the original asset-cost model does not describe. */
    dungeon_animation_scan=dungeon_animation_phase=0;dungeon_bitmap_pending=0;
    prepare_dungeon_palette(room_id);set_world_palette();world_palette_pending=FALSE;
    load_current_world_actors(room_id);
    room_shutter_state=(world_actor_count&128)?2:0;room_shutter_direction=0;room_script_coordinate_pending=1;
    if(world_actor_tiles) VDP_loadTileData(md_patterns+256*8,16+256,world_actor_tiles,CPU);
    hero_state=hero_animation=hero_counter=hero_pending=hero_hurt=hero_casting=0;
    hero_dx=hero_dy=0;hero_flags=3;hero_scroll_x=hero_scroll_y=0;
    hero_loaded_pose=65535;prepare_hero_patterns();map_origin=0x3800;draw_map();
    /* Dynamic source graphics work survives preconversion. The shared state-8
     * preparation/IRQ allowance is approximate; no per-room frame table. */
    budget=(SYS_isPAL()?71364UL:59736UL)-3072;
    loading_frames=(world_actor_load_tstates+(SYS_isPAL()?365000UL:420000UL)+budget-1)/budget;
    while(vtimer-started<loading_frames) portal_wait_frame();
    update_hero_sprites();VDP_setEnable(TRUE);game_state=12;
    return TRUE;
}

extern const u8 world_door_records[][4],world_standard_house_exit[256];
extern const u16 world_door_count;
extern const u16 world_dungeon_door_records[][5],world_dungeon_door_count;
extern const u8 world_standard_dungeon_exit[256];
static void load_door_room(u16 number,u16 graphics_class);
static void check_village_door(u16 old_x,u16 old_y)
{
    u16 x=hero_x>>8,y=hero_y>>8,n;
    if(world_graphics_class==2)
    {
        /* 2CF8: source contact coordinate, including sub-tile positions.
         * 654D masks its low three bits; unlike 65D0 it has no grid guard. */
        /* C060 is built before the common movement tail, so use the
         * position from the beginning of this gameplay iteration. */
        u16 coordinate=(((u8)(old_y-12)&248)<<3)+(((u8)(old_x-12)>>2)&62)+126;
        if(world_standard_dungeon_exit[room_id&255] && (coordinate&0xfff8)==0x0518)
        {
            save_room_actor_mask(room_id);world_dungeon_number=0;
            memset(game_save_state+0x150,255,256); /* 1C97 after 65E1 */
            room_id=house_return_room;hero_x=house_return_x;hero_y=house_return_y;
            load_door_room(room_id,0);
        }
        return;
    }
    if((x|y)&7 || (x==old_x && y==old_y)) return;
    if(!world_graphics_class)
    {
        for(n=0;n<world_dungeon_door_count;n++)
        {
            const u16 *door=world_dungeon_door_records[n];
            if(door[0]!=room_id || door[1]!=x || door[2]!=y) continue;
            save_room_actor_mask(room_id);
            house_return_room=room_id;house_return_x=hero_x;house_return_y=hero_y;
            world_dungeon_number=door[4];
            game_save_state[0x14]=door[3];game_save_state[0x15]=door[3]>>8; /* C0C4 */
            memset(game_save_state+0x150,255,256); /* 1C97 */
            room_id=door[3];hero_x=0x8000;hero_y=0x9800;
            load_door_room(room_id,2);return;
        }
        for(n=0;n<world_door_count;n++)
        {
            const u8 *door=world_door_records[n];
            if(door[0]!=room_id || door[1]!=x || door[2]!=y) continue;
            house_return_room=room_id;house_return_x=hero_x;house_return_y=hero_y;
            hero_x=0x8800;hero_y=0x9800;load_door_room(door[3],1);break;
        }
    }
    else if(world_graphics_class==1 && room_id<256 && world_standard_house_exit[room_id] && x==136 && y==160)
    {
        hero_x=house_return_x;hero_y=house_return_y;
        load_door_room(house_return_room,0);
    }
}

/* 6A08/6D54: scan five indoor cells, toggle portrait poses and queue 2x2. */
static void animate_house_room(void)
{
    u16 n,row,column;
    house_animation_scan+=5;if(house_animation_scan>=160) house_animation_scan=0;
    for(n=house_animation_scan;n<house_animation_scan+5;n++)
    {
        u16 tile=scratch[0x800+n],x=(n&15)*2,y=(n>>4)*2;
        u16 words[4];
        if(tile<0x24 || tile>=0x30) continue;
        tile^=1;scratch[0x800+n]=tile;
        for(row=0;row<2;row++) for(column=0;column<2;column++)
        {
            u16 p=(y+row)*32+x+column,address=tile*8+row*4+column*2;
            sms_vram[0x3800+p*2]=scratch[address];sms_vram[0x3801+p*2]=scratch[address+1];
            md_map[p]=world_new_md[p]=world_metatiles_md[address/2];words[row*2+column]=md_map[p];
        }
        VDP_setTileMapDataRect(BG_A,words,x,y+2,2,2,2,DMA_QUEUE_COPY);
    }
    if(!(world_clock()&1))
    {
        u16 tile=scratch[0xe0]; /* 6A41: C9E0 relative to C900 metatiles. */
        memcpy(sms_vram+tile*32,world_house_animation_bitmaps+((world_clock()&2)?128:0),128);
        convert_patterns_range(tile,4);house_animation_patterns_pending=tile+1;
    }
}

/* 1DF6: curse changes armor colors on clock-bit1 zero, without replacing
 * the equipment level or its inventory icon. */
static void prepare_hero_armor_palette(void)
{
    if(hero_armor_level<5)
    {
        sms_palette[22]=world_armor_colors[hero_armor_level*2];
        sms_palette[23]=world_armor_colors[hero_armor_level*2+1];
    }
    if(game_save_state[15] && !(world_clock()&2)) { sms_palette[22]=0x16;sms_palette[23]=1; }
}

/* 699C -> bank 5 BD9B, 1DF6: palette animation in normal exteriors. */
static void animate_world_palette(void)
{
    u16 n;
    if(world_graphics_class==1) animate_house_room();
    if(world_graphics_class==2 && !world_dungeon_dark && !(world_clock()&3))
    {
        u16 boss=0;
        for(n=0;n<8;n++) boss|=world_actor_state[n*0x30+3]&0x40;
        for(n=0;n<3;n++) sms_palette[13+n]=boss?0:world_dungeon_color_cycle[((world_clock()>>2)&3)*3+n];
    }
    if(!world_graphics_class && !(world_clock()&7)) for(n=0;n<4;n++) sms_palette[12+n]=world_water_cycle[((world_clock()&24)>>3)+n];
    prepare_hero_armor_palette();
    sms_palette[31]=(world_clock()&2)?2:1;
    world_palette_pending=TRUE;
}

static void draw_death_selection(void)
{
    u16 first=world_gameover_words[18]|((u16)world_gameover_words[19]<<8);
    u16 second=world_gameover_words[36]|((u16)world_gameover_words[37]<<8);
    if(!death_menu_selection) { u16 temporary=first;first=second;second=temporary; }
    sms_vram[0x3a98]=first;sms_vram[0x3a99]=first>>8;
    sms_vram[0x3ad8]=second;sms_vram[0x3ad9]=second>>8;
    /* Original IRQ command 2 updates only the 11-by-6 menu rectangle. */
    {
        u16 rectangle[66],x,y;
        for(y=0;y<6;y++) for(x=0;x<11;x++)
        {
            u16 p=0x39d6+y*64+x*2;
            u16 word=sms_vram[p]|((u16)sms_vram[p+1]<<8);
            rectangle[y*11+x]=TILE_ATTR_FULL((word>>11)&1,(word>>12)&1,(word>>10)&1,(word>>9)&1,16+(word&511));
            md_map[(7+y)*32+11+x]=rectangle[y*11+x];
        }
        VDP_setTileMapDataRect(BG_A,rectangle,11,9,11,6,11,CPU);
    }
}

/* 257D/263E/0ACE: grayscale fade, original font/frame and Continue/End. */
static bool death_menu(void)
{
    u16 target[32],n,step,previous;
    bool changed,hide_pending=TRUE,selection_pending=FALSE;
    for(n=0;n<32;n++) target[n]=sms_palette[n];
    for(n=0;n<16;n++)
    {
        u16 color=sms_palette[n];
        target[n]=world_gray_tones[(color&3)+((color>>2)&3)+((color>>4)&3)];
    }
    for(step=16;step;step>>=2)
    {
        do
        {
            changed=FALSE;
            for(n=0;n<32;n++)
            {
                u16 current=sms_palette[n]&(step*3),desired=target[n]&(step*3);
                if(current!=desired) { sms_palette[n]+=current<desired?step:-step;changed=TRUE; }
            }
            if(changed)
            {
                wait_frame();
                if(hide_pending) { VDP_resetSprites();VDP_setSpriteFull(0,0,0,SPRITE_SIZE(1,1),0,0);VDP_updateSprites(1,CPU);hide_pending=FALSE; }
                set_world_palette();wait_frame(); /* 0B92 falls through a second 0B95. */
            }
        } while(changed);
    }
    load_mono(0x3600,world_gameover_font,13*8,3,TRUE);
    convert_patterns_range(432,13);VDP_loadTileData(md_patterns+432*8,16+432,13,CPU);
    draw_frame(0x39d6,11,6);
    memcpy(sms_vram+0x3a18,world_gameover_words,18);
    memcpy(sms_vram+0x3a98,world_gameover_words+18,18);
    memcpy(sms_vram+0x3ad8,world_gameover_words+36,8);
    wait_frame();wait_frame(); /* Match glyph construction and command-2 presentation IRQs. */
    VDP_fillTileMapRect(BG_B,TILE_ATTR_FULL(PAL3,0,0,0,1),11,9,11,6);
    death_menu_selection=1;draw_death_selection();
    previous=input;
    while(TRUE)
    {
        u16 pressed;
        wait_frame();
        if(selection_pending) { draw_death_selection();selection_pending=FALSE; }
        pressed=input&~previous;previous=input;
        if((pressed&BUTTON_UP) && !death_menu_selection) { death_menu_selection=1;selection_pending=TRUE; }
        if((pressed&BUTTON_DOWN) && death_menu_selection) { death_menu_selection=0;selection_pending=TRUE; }
        if(selection_pending) sound_effect(0x95);
        if(pressed&(BUTTON_A|BUTTON_B|BUTTON_C|BUTTON_START))
        {
            sound_effect(0xab);
            if(death_menu_selection) { hero_health=hero_magic=24;hero_gold=(hero_gold>>2)*3;save_prepare_checkpoint_resume();game_state=6;return TRUE; }
            return FALSE;
        }
    }
}

/* 0AD1/0ADE: compare one two-bit component, then wait two IRQs per change.
 * 0B12 uses red/green/blue; 0AA4 uses blue/green/red. */
static void fade_world_palette(const u16 *target,bool fade_in)
{
    u16 step=fade_in?16:1,n;
    bool changed;
    resume_fade_step=0;
    while(step && step<=16)
    {
        do
        {
            changed=FALSE;
            for(n=0;n<32;n++)
            {
                u16 current=sms_palette[n]&(step*3),desired=target[n]&(step*3);
                if(current!=desired) { sms_palette[n]+=current<desired?step:-step;changed=TRUE; }
            }
            if(changed) { resume_fade_step++;set_world_palette();wait_frame();wait_frame(); }
        } while(changed);
        step=fade_in?step>>2:step<<2;
    }
}

/* 2003 translated into four short VDP transfers per contour side. */
static void reveal_world_side(u16 address,u16 length,u16 stride)
{
    u16 foreground[32],background[32],n,index=(address-0x7800)>>1;
    u16 x=index&31,y=(index>>5)+2;
    for(n=0;n<length;n++)
    {
        u16 offset=(index+n*stride)*2;
        u16 word=sms_vram[0x3800+offset]|((u16)sms_vram[0x3801+offset]<<8);
        foreground[n]=md_map[index+n*stride];
        background[n]=TILE_ATTR_FULL((word&0x800)?PAL3:PAL2,0,0,0,1);
    }
    if(stride==1)
    {
        VDP_setTileMapDataRow(BG_A,foreground,y,x,length,CPU);
        VDP_setTileMapDataRow(BG_B,background,y,x,length,CPU);
    }
    else
    {
        VDP_setTileMapDataColumnFast(BG_A,foreground,x,y,length,CPU);
        VDP_setTileMapDataColumnFast(BG_B,background,x,y,length,CPU);
    }
}

static void reveal_world(void)
{
    u16 target[32],n,address,height,width;
    u32 wait_started;
    memcpy(target,sms_palette,sizeof(target));memset(sms_palette,0,sizeof(sms_palette));set_world_palette();
    /* 1FA7 clears hardware VRAM, preserving the fully decoded D600 map. */
    VDP_fillTileMapRect(BG_A,TILE_ATTR_FULL(PAL1,1,0,0,16+255),0,2,32,24);
    VDP_fillTileMapRect(BG_B,TILE_ATTR_FULL(PAL3,0,0,0,1),0,2,32,24);
    VDP_resetSprites();VDP_setSpriteFull(0,0,0,SPRITE_SIZE(1,1),0,0);VDP_updateSprites(1,CPU);
    /* 0BA7..0BB3 waits for a fresh IRQ even while display is disabled. */
    wait_started=vtimer;wait_frame();while(vtimer==wait_started);
    VDP_setEnable(TRUE);
    resume_phase=3;fade_world_palette(target,TRUE);
    resume_phase=4;resume_contour=0;
    for(n=0;n<16;n++)
    {
        const u8 *contour=world_reveal_contours+n*4;
        wait_frame();wait_frame();
        address=contour[0]|((u16)contour[1]<<8);height=contour[2];width=contour[3];
        /* Commit the left edge before the next visible top scanlines. */
        reveal_world_side(address,height,32);
        reveal_world_side(address+2,width,1);
        reveal_world_side(address+width*2+64,height,32);
        reveal_world_side(address+height*64,width,1);resume_contour=n+1;
    }
    resume_phase=0;
}

/* 722A: selected icon is shared with the world HUD; apply ROM remap 30h. */
#include "door_transition.inc"

static void inventory_hud_icon(void)
{
    u16 n,x,y,icon=hero_selected_item==0?hero_basic_level:hero_selected_item==1?hero_weapon_level+3:hero_selected_item+4;
    memcpy(sms_vram+0x1d80,inventory_icons+icon*128,128);
    for(n=0x1d80;n<0x1e00;n+=4)
    {
        u8 converted[4]={0,0,0,0};
        for(x=0;x<8;x++)
        {
            u16 color=0;
            for(y=0;y<4;y++) color|=((sms_vram[n+y]>>x)&1)<<y;
            color=world_icon_remap[color];
            for(y=0;y<4;y++) converted[y]|=((color>>y)&1)<<x;
        }
        memcpy(sms_vram+n,converted,4);
    }
    convert_patterns_range(236,4);VDP_loadTileData(md_patterns+236*8,252,4,CPU);
}

static void inventory_text(u16 destination,const u8 *text)
{
    u16 line=destination,n;u8 value;
    while((value=*text++)!=0)
    {
        if(value==255) { line+=64;destination=line;continue; }
        for(n=0;n<80;n++) if(inventory_charset[n]==value) break;
        sms_vram[destination++]=0xb0+n;sms_vram[destination++]=8;
    }
}

static void inventory_quad(u16 destination,u16 tile)
{
    sms_vram[destination]=tile;sms_vram[destination+1]=8;
    sms_vram[destination+2]=tile+1;sms_vram[destination+3]=8;
    sms_vram[destination+64]=tile+2;sms_vram[destination+65]=8;
    sms_vram[destination+66]=tile+3;sms_vram[destination+67]=8;
}

static void inventory_sprites(void)
{
    u16 count;
    VDP_resetSprites();
    count=add_sms_sprite_frame(0,inventory_positions[inventory_slot*2+1],inventory_positions[inventory_slot*2],inventory_cursor_frame,0);
    if((u8)(world_clock()-1)&4)
    {
        u16 cell=(room_id-16)&255;
        count=add_sms_sprite_frame(count,0xaa+(cell&15)*4,0x1a+(cell>>4)*3,inventory_marker_frame,0);
    }
    VDP_setSpriteLink(count-1,0);VDP_updateSprites(count,CPU);
}

/* 20DA clears only the twenty playfield rows; the HUD remains displayed. */
static void blank_inventory_playfield(void)
{
    VDP_resetSprites();VDP_updateSprites(0,CPU);
    VDP_fillTileMapRect(BG_A,TILE_ATTR_FULL(PAL3,1,0,0,1),0,2,32,20);
}

/* 70F2..7218/72C4: twelve-slot menu, with source-owned item validation.
 * Restore the current graphics class when the menu releases its patterns. */
static void show_inventory(void)
{
    const u8 *source;u16 n,row,tile=48,previous=input;
    u32 menu_started=vtimer,budget=(SYS_isPAL()?71364UL:59736UL)-3072UL,work,frames;
    hero_items[0]=hero_basic_level;hero_items[1]=hero_weapon_level;
    memcpy(animation_map,sms_vram+0x3800,0x500);
    blank_inventory_playfield();
    for(n=0x3800;n<0x3d00;n+=2) { sms_vram[n]=255;sms_vram[n+1]=8; }
    load_mono(0x1600,normal_font,256,3,TRUE);
    load_mono(0x3e00,inventory_cursor_bitmap,40,3,FALSE);
    source=decode_planes(inventory_header_rle,sms_vram,4);decode_planes(source,sms_vram+0x3840,2);
    source=decode_planes(inventory_map_rle,sms_vram+0x100,4);decode_planes(source,title_map,2);
    for(row=0;row<8;row++) memcpy(sms_vram+0x38a4+row*64,title_map+row*28,28);
    for(n=0;n<19;n++)
    {
        u16 icon=n==0?hero_basic_level:n==1?(hero_weapon_level?hero_weapon_level+3:0):n<17?(hero_items[n]?n+4:0):n==17?hero_armor_level+20:hero_shield_level+23;
        if(icon) memcpy(sms_vram+0x600+n*128,inventory_icons+icon*128,128);
        else memset(sms_vram+0x600+n*128,0,128);
    }
    for(n=0;n<12;n++)
    { inventory_quad(0x3886+(n/4)*192+(n%4)*6,tile);tile+=4; }
    /* Row four contains five reserved icons, including equipment resources. */
    for(n=0;n<5;n++) { inventory_quad(0x3b06+n*6,tile);tile+=4; }
    inventory_quad(0x3c06,tile);tile+=4;inventory_quad(0x3c24,tile);
    inventory_text(0x3c0c,inventory_equipment_words+(inventory_equipment_words[hero_armor_level*2]|((u16)inventory_equipment_words[hero_armor_level*2+1]<<8))-0xbe3c);
    inventory_text(0x3c2a,inventory_equipment_words+(inventory_equipment_words[8+hero_shield_level*2]|((u16)inventory_equipment_words[9+hero_shield_level*2]<<8))-0xbe3c);
    sms_vram[0x3b2c]=0x96;sms_vram[0x3b2d]=0x19;sms_vram[0x3b6c]=0x97;sms_vram[0x3b6d]=0x19;
    sms_vram[0x3b6e]=0xdb;sms_vram[0x3b6f]=0x18;
    for(n=0;n<3;n++) { sms_vram[0x3b70+n*2]=0xf0+(n==0?hero_keys/100:n==1?(hero_keys/10)%10:hero_keys%10);sms_vram[0x3b71+n*2]=0x18; }
    inventory_slot=hero_selected_item;map_origin=0x3800;map_queue=FALSE;
    convert_patterns_range(0,124);convert_patterns_range(176,32);convert_patterns_range(496,5);
    VDP_loadTileData(md_patterns,16,124,CPU);VDP_loadTileData(md_patterns+176*8,192,32,CPU);VDP_loadTileData(md_patterns+496*8,512,5,CPU);
    if(world_palette_pending) { set_world_palette();world_palette_pending=FALSE; }
    VDP_fillTileMapRect(BG_B,TILE_ATTR_FULL(PAL3,0,0,0,1),0,2,32,24);
    /* 70F5..71D2: source font, maps and icons take 537891 foreground T states
     * with initial ownership; 20DA adds the first blank upload frame. Native
     * conversion/upload frames already spent count toward this budget. */
    frames=(537891UL+budget-1)/budget+2;
    while(vtimer-menu_started<frames-(SYS_isPAL()?1:2)) wait_frame();
    draw_map();inventory_sprites();
    while(TRUE)
    {
        u16 pressed,column,row_index,cursor;
        wait_frame();inventory_sprites();
        prepare_hero_armor_palette();sms_palette[31]=((u8)(world_clock()-1)&2)?2:1;set_world_palette();
        pressed=input&~previous;previous=input;
        cursor=inventory_slot;column=cursor&3;
        if((pressed&BUTTON_LEFT) && column) cursor--;
        if((pressed&BUTTON_RIGHT) && column!=3) cursor++;
        row_index=(cursor&12)>>2;
        if((pressed&BUTTON_UP) && row_index) cursor-=4;
        if((pressed&BUTTON_DOWN) && row_index!=2) cursor+=4;
        if(inventory_slot!=cursor) sound_effect(0x95); /* 7303 */
        inventory_slot=cursor;
        if((pressed&BUTTON_C) && hero_items[cursor])
        {
            hero_selected_item=cursor;inventory_hud_icon();sound_effect(0xab); /* 7349 */
            /* 1D0D consumes two additional display frames. C02F advances
             * through 0B95, so these frames do not advance menu logic. */
            wait_frame();wait_frame();world_clock_shift+=2;
            inventory_sprites();prepare_hero_armor_palette();sms_palette[31]=((u8)(world_clock()-1)&2)?2:1;set_world_palette();
        }
        if(pressed&BUTTON_B) break; /* 71F2..71F9: closing has no sound command. */
    }
    /* 71F9 ->20DA publishes a blank map on the following IRQ. */
    menu_started=vtimer;wait_frame();
    blank_inventory_playfield();memcpy(sms_vram+0x3800,animation_map,0x500);
    decode_planes(world_graphics_class==2?world_dungeon_background_rle:
        world_graphics_class==1?world_house_background_rle:world_background_rle,sms_vram,4);
    inventory_hud_icon();hero_loaded_pose=65535;prepare_hero_patterns();
    convert_patterns_range(0,193);VDP_loadTileData(md_patterns,16,193,CPU);
    VDP_fillTileMapRect(BG_B,TILE_ATTR_FULL(PAL2,0,0,0,1),0,2,32,20);
    VDP_fillTileMapRect(BG_B,TILE_ATTR_FULL(PAL3,0,0,0,1),0,22,32,4);
    /* 16EF reloads class-specific background, metatiles and animation data.
     * Costs count original compressed-resource loops. The remaining room/HUD
     * reconstruction reserve is approximate; natural village/exterior routes
     * verify the actual blank frames in both regions. */
    work=(world_graphics_class==2?693284UL:world_graphics_class==1?664703UL:995861UL)+290000UL;
    frames=(work+budget-1)/budget+1;
    while(vtimer-menu_started<frames-(SYS_isPAL()?1:2)) wait_frame();
    draw_map();update_hero_sprites();
    /* 722A icon/remap and hero upload finish after the map becomes visible. */
    frames+=SYS_isPAL()?2:3;
    while(vtimer-menu_started<frames) wait_frame();
    world_previous_input=input;game_state=12;
}

static bool tick_world_simulation(void)
{
    world_object_tick_count=1; /* 26B6 counts the hero before spell/loot/actor visits. */
    if(!boss_death_music_hold) update_world_music();
    s16 contact=-1,damage=0;
    u16 old_x=hero_x>>8,old_y=hero_y>>8,old_direction=hero_direction;
    u8 cache[12];u16 row,column,hero_hit_box=hero_collision_index(1);
    u16 offset=(((hero_y>>8)-12)&248)*8+((((hero_x>>8)-12)>>2)&62);
    for(row=0;row<3;row++) for(column=0;column<4;column++)
    {
        u16 p=offset+row*64+column*2;
        u8 high=p+1<0x600?sms_vram[0x3801+p]:128;
        if(!hero_items[12] && (high&32)) high|=128;
        cache[row*4+column]=high;
    }
    apply_water_collision_cache(cache);
    world_set_hero_floor(offset+66<0x600?sms_vram[0x3800+offset+66]:255,
                         offset+68<0x600?sms_vram[0x3800+offset+68]:255);
    if(!hero_hurt && hero_health && (hero_flags&2))
        contact=find_world_actor_contact(hero_x>>8,hero_y>>8,
                    hero_collision_index(0),world_clock());
    if(contact>=0 && world_actor_state[contact*0x30]>=0x10)
    {
        damage=(s16)world_actor_state[contact*0x30+0x19]-(s16)hero_defense;
        if(damage<=0) damage=2;
    }
    hero_terrain_context=classify_hero_terrain();
    prepare_hero_defense();
    hero_attack=world_attack_strength[hero_selected_item*4+(hero_selected_item==0?hero_basic_level:hero_selected_item==1?hero_weapon_level:hero_items[hero_selected_item])];
    if((input&~world_previous_input&BUTTON_C) && hero_state==1 && hero_health && hero_selected_item<12) activate_hero_item();
    if(hero_state==8)
    {
        sound_effect_main(0x9a); /* 371D */
        hero_dx=hero_dy=0;hero_counter=90;hero_state=9;hero_casting=0;
        hero_hurt=hero_animation=0;hero_flags=(hero_flags|1)&253;
    }
    if(hero_state==9)
    {
        hero_hurt=hero_animation=0;
        if(!hero_counter) { hero_flags&=254;game_state=20; }
    }
    else
    {
        if(!hero_state) { hero_state=1;hero_casting=0; }
        if(hero_state==12) { hero_animation=0;hero_flags|=1;hero_casting=0; } /* 2F0D/369F */
        else if(hero_state==1) move_hero();
        else if(hero_state>=2 && hero_state<=5) attack_hero();
        else if(hero_state==10 || hero_state==11)
        {
            if(hero_state==10) { hero_state=11;hero_attack_phase=255;hero_animation=0; }
            hero_casting=1;hero_attack_phase=(hero_attack_phase+1)&255;
            if(hero_attack_phase==3) hero_state=0;
        }
        if(!hero_health) hero_state=8;
    }
    if(contact>=0 && damage && !(hero_state==1 && reflect_world_actor(contact,hero_direction,hero_shield_level)))
    {
        u8 *entity=world_actor_state+contact*0x30;
        u16 is_projectile=entity[3]&16;
        hurt_hero(contact,cache,damage);
        if(is_projectile) memset(entity,0,0x30);
    }
    integrate_hero();
    if(hero_hurt && hero_hurt<=128)
    {
        hero_hurt--;hero_flags|=1;
        if(hero_hurt&2) hero_flags&=254;
    }
    tick_world_spell(sms_vram+0x3800,world_spell_state[0]==5?hero_basic_level:world_spell_state[0]==4?hero_items[5]:hero_items[4]);
    tick_world_loot(hero_state,&hero_gold,&hero_health,hero_max_health,&hero_magic,hero_max_magic,&hero_keys);
    prepare_hero_health_bar(FALSE);prepare_hero_magic_bar();
    set_world_hero_attack(hero_x>>8,hero_y>>8,hero_direction,hero_hit_box,hero_attack,&hero_flags);
    tick_world_actors(sms_vram+0x3800,scratch+0x800,hero_x>>8,hero_y>>8,world_clock(),room_id);
    prepare_hero_gold_bar(); /* 1EA1/1F4B follows actor gold mutations. */
    if(hero_health)
    {
        u32 script_started=vtimer;
        u8 script_flags=room_script_flags(old_x,old_y,old_direction);
        check_dungeon_key_door();check_dungeon_item_reward(script_flags);check_room_puzzle(script_flags,0);check_room_contact(script_flags);check_room_shutter(script_flags);
        if(check_dungeon_portal(script_flags,0,vtimer!=script_started)) return TRUE;
        check_dungeon_room_clear();check_room_puzzle(script_flags,1);
        if(check_dungeon_portal(script_flags,1,vtimer!=script_started)) return TRUE;
        check_village_door(old_x,old_y);check_house_service(old_x,old_y);check_house_talk(old_x,old_y,script_flags);begin_room_transition();
    }
    animate_dungeon_bitmaps();animate_dungeon_cells();animate_world_palette();
    if(game_state==12 && hero_health && (input&~world_previous_input&BUTTON_B)) game_state=16;
    return FALSE;
}

#include "ending.inc"

static void enter_initial_room(void)
{
    const u8 *source,*extra=world_extra_meta;
    u16 n,x,y,destination=0x400,count;
    bool resuming=FALSE;
    u32 load_clock=0;
reload_world:
    if(resuming) { load_clock=vtimer;resume_phase=2; }
    else { world_clock_shift=0;resume_phase=resume_contour=0; }
    destination=0x400;extra=world_extra_meta;
    hero_casting=0;ending_hero_descriptor=0;
    if(!resuming && !save_resume_pending) { save_reset_new_game();forest_maze_progress=0;hero_fire_charge=0;memset(hero_items,0,sizeof(hero_items));hero_keys=0;hero_shield_level=hero_armor_level=1;hero_gold=0;hero_selected_item=hero_weapon_level=hero_attack_speed=0;hero_basic_level=1;hero_max_health=24;hero_magic=hero_max_magic=24; }
    VDP_setEnable(FALSE);
    memset(sms_vram,0,sizeof(sms_vram)); memset(scratch,0,sizeof(scratch));
    decode_planes(menu_rle,sms_vram+0x3040,4);
    decode_planes(number_font_rle,sms_vram+0x1e00,4);
    decode_planes(world_hud_font_rle,sms_vram+0x1a00,4);
    decode_planes(world_hud_patterns_rle,sms_vram+0x3600,4);
    memcpy(sms_vram+0x1d80,world_item_icon,128);
    /* 1D0D remaps the item icon's color indices through the ROM table. */
    for(n=0x1d80;n<0x1e00;n+=4)
    {
        u8 converted[4]={0,0,0,0};
        for(x=0;x<8;x++)
        {
            u16 color=0;
            for(y=0;y<4;y++) color|=((sms_vram[n+y]>>x)&1)<<y;
            color=world_icon_remap[color];
            for(y=0;y<4;y++) converted[y]|=((color>>y)&1)<<x;
        }
        memcpy(sms_vram+n,converted,4);
    }
    source=decode_planes(world_background_rle,sms_vram,4);
    decode_planes(source,scratch,2);
    memcpy(scratch+0x1c0,scratch+0x98,8); memcpy(scratch+0x1f0,scratch+0x98,8);
    while(*extra<128) { memcpy(scratch+destination,scratch+*extra++*8,8); destination+=8; }
    extra++;
    for(n=0x401;n<destination;n+=2) scratch[n]=(scratch[n]&31)|*extra++;
    for(n=0;n<0x220;n++)
    {
        u16 sms=scratch[n*2]|((u16)scratch[n*2+1]<<8);
        world_metatiles_md[n]=TILE_ATTR_FULL((sms>>11)&1,(sms>>12)&1,(sms>>10)&1,(sms>>9)&1,16+(sms&511));
    }
    decode_planes(world_room_rle,scratch+0x800,1);
    for(y=0;y<20;y++) for(x=0;x<32;x++)
    {
        u16 tile=scratch[0x800+(y/2)*16+x/2];
        u16 offset=tile*8+(y&1)*4+(x&1)*2;
        memcpy(sms_vram+0x3800+(y*32+x)*2,scratch+offset,2);
    }
    decode_planes(world_hud_rle,sms_vram+0x3d00,2);
    for(n=0x3d00;n<0x3e00;n+=2) { sms_vram[n]+=0xd0; sms_vram[n+1]|=0x18; }
    memcpy(sms_vram+0x3d58,world_hud_icon_words,4);
    memcpy(sms_vram+0x3d98,world_hud_icon_words+4,4);
    for(n=0x3d01;n<0x3e00;n+=2) sms_vram[n]|=0x40;
    for(n=0;n<(hero_max_health>>3);n++)
    { sms_vram[0x3d5e + n*2]=n<3?0x8b:0x8f;sms_vram[0x3d5f+n*2]=0x19; }
    for(n=0;n<(hero_max_magic>>3);n++)
    { sms_vram[0x3dde + n*2]=hero_magic>=(n+1)*8?0x90:0x91;sms_vram[0x3ddf+n*2]=0x19; }
    for(n=0;n<3;n++)
    { sms_vram[0x3dd0+n*2]=0xf0+(n==0?hero_gold/100:n==1?(hero_gold/10)%10:hero_gold%10);sms_vram[0x3dd1+n*2]=0x18; }
    source=world_hero_bitmap+1;
    for(n=0;n<world_hero_bitmap[0]*8;n++)
    {
        memcpy(sms_vram+0x3e00+n*4,source,3);source+=3;
        sms_vram[0x3e03+n*4]=0;
    }
    dungeon_animation_scan=dungeon_animation_phase=0;dungeon_bitmap_pending=0;
        load_current_world_actors(0x95);
    room_shutter_state=(world_actor_count&128)?2:0;room_shutter_direction=0;room_script_coordinate_pending=1;
    for(n=0;n<16;n++) { sms_palette[n]=world_palette[n];sms_palette[n+16]=menu_palette[n]; }
    /* Initial equipment C0F1=1; table $1E30 selects $38,$30. */
    sms_palette[22]=0x38;sms_palette[23]=0x30;sms_palette[31]=1;
    convert_patterns(512);VDP_loadTileData(md_patterns,16,512,CPU);
    map_origin=0x3800;draw_map();set_palette(sms_palette);
    memcpy(world_new_md,md_map,sizeof(world_new_md));
    /* SMS background palette 0 color 0 is grass, while HUD palette 1
     * color 0 is black. MD transparent index 0 needs those two backdrops. */
    {
        static const u16 levels[4]={0,3,5,7};
        u16 color=world_palette[0];
        PAL_setColor(33,(levels[color&3]<<1)|(levels[(color>>2)&3]<<5)|(levels[(color>>4)&3]<<9));
        PAL_setColor(49,0);
        VDP_fillTileMapRect(BG_B,TILE_ATTR_FULL(PAL2,0,0,0,1),0,2,32,20);
        VDP_fillTileMapRect(BG_B,TILE_ATTR_FULL(PAL3,0,0,0,1),0,22,32,4);
    }
    VDP_resetSprites();
    count=add_sms_sprite_frame(0,0x88,0x70,world_hero_frame,0);
    if(count && count<=64) { VDP_setSpriteLink(count-1,0);VDP_updateSprites(count,CPU); }
    if(!resuming) VDP_setEnable(TRUE);
    hero_y=0x7000;hero_x=0x8800;hero_direction=1;hero_animation=0;
    hero_counter=hero_pending=0;hero_dy=hero_dx=0;
    hero_loaded_pose=8;hero_pattern_tiles=4;hero_gold_drawn=hero_gold;hero_gold_pending=FALSE;hero_magic_drawn=hero_magic;hero_magic_capacity_drawn=hero_max_magic;hero_magic_pending=FALSE;hero_magic_delay=0;hero_patterns_pending=FALSE;hero_attack_phase=0;world_previous_input=input;
    hero_health=hero_health_drawn=24;hero_health_capacity_drawn=hero_max_health;hero_hurt=0;hero_flags=3;hero_state=1;hero_defense=0;hero_health_pending=FALSE;
    world_graphics_class=0;room_id=0x95;game_state=12;hero_scroll_x=hero_scroll_y=0;world_palette_pending=FALSE;
    if(save_resume_pending)
    {
        save_resume_pending=FALSE;hero_health=save_resume_health;
        /* Reload setup temporarily uses room 95; it is not a room departure
         * and must not overwrite mask C295 after the dungeon reset. */
        if(save_resume_room>=256) room_id=save_resume_room;
        load_house_room(save_resume_room,save_resume_room>=256?2:(save_resume_room<16 || (save_resume_room&15)==15)?1:0);hero_health_drawn=65535;prepare_hero_health_bar(TRUE);
        if(save_resume_room>=256) hero_direction=1; /* Continue uses 88/70, unlike doorway entry. */
        hero_health_pending=TRUE;inventory_hud_icon();
    }
    if(resuming) { world_clock_shift+=vtimer-load_clock;hero_state=0;reveal_world(); }
    /* Original IRQ commits the previous iteration's sprite list. Keep that
     * one-frame presentation delay without delaying the simulation state. */
    while(TRUE)
    {
        if(game_state==14) { run_ending();return_to_title=TRUE;return; }
        if(game_state==16) { show_inventory();continue; }
        if(game_state==20)
        {
            if(!death_menu()) { return_to_title=TRUE;return; }
            { u16 black[32]={0};resume_phase=1;fade_world_palette(black,FALSE); }
            resuming=TRUE;goto reload_world;
        }
        { u16 order_phase=world_clock();bool order_overflow=world_sms_sprite_overflow;
          wait_frame();update_hero_sprites_for_frame(order_phase,order_overflow); }
        if(game_state==12) { if(tick_world_simulation()) continue; }
        else step_room_transition();
        if(transition_pose_prepared) transition_pose_prepared=FALSE;
        else prepare_hero_patterns();
        world_previous_input=input;
    }
}

/* 0709: current service supplies the unsigned number used by #. */
static u16 dialogue_number;
/* 0786 publication boundary. Native transfer/IRQ ordering remains to align. */
static void publish_dialog_word(void)
{
    sound_effect(0x9f);
    upload_dialog_bitmap();
    wait_frame();
}
static void render_dialogue_text(const u8 *source,bool overlay)
{
    u8 expanded[512];
    u8 substitution_end[512]={0};
    const u8 *cursor;
    u16 n,out=0,x=0,y=0,line=0;
    bool small=TRUE;
    if(!overlay) VDP_setEnable(FALSE);
    if(!overlay)
    {
        VDP_resetSprites();
        VDP_setSpriteFull(0,0,0,SPRITE_SIZE(1,1),0,0);VDP_updateSprites(1,CPU);
    }
    /* $119D..11A5 restores $A74C at $1E00, including the dialogue border tiles. */
    if(overlay)
    {
        decode_planes(number_font_rle,sms_vram+0x1e00,4);
        convert_patterns_range(240,16);
        VDP_loadTileData(md_patterns+240*8,16+240,16,CPU);
    }
    /* $779B and $0524: clear the window, build its border and 130 bitmap tiles. */
    if(!overlay) for(n=0x3800;n<0x3e00;n+=2) { sms_vram[n]=0xfa; sms_vram[n+1]=1; }
    for(n=0x3b40;n<0x3d00;n+=2) { sms_vram[n]=0xff; sms_vram[n+1]=0x18; }
    draw_frame(0x3b44,28,7);
    for(x=0;x<26;x++)
        for(y=0;y<5;y++)
        {
            u16 address=0x3b86+x*2+y*64,word=0x1900+x*5+y;
            sms_vram[address]=word; sms_vram[address+1]=word>>8;
        }
    memset(scratch,0,0x410);
    upload_dialog_bitmap(); draw_map(); if(!overlay) VDP_setEnable(TRUE);
    while(*source)
    {
        if(*source=='%')
        {
            /* 06F3 forces small glyphs inside %, then 075E restores the mode. */
            for(n=0;character_name[n];n++)
            { expanded[out]=character_name[n];substitution_end[out++]=2; }
            if(out) substitution_end[out-1]|=1;
            source++;
        }
        else if(*source=='#')
        {
            u16 divisor=10000,number=dialogue_number;
            while(divisor>1 && number<divisor) divisor/=10;
            do { expanded[out++]='0'+number/divisor;number%=divisor;divisor/=10; } while(divisor);
            substitution_end[out-1]=1;
            source++;
        }
        else expanded[out++]=*source++;
    }
    expanded[out]=0; cursor=expanded; x=0; y=0;
    /* 0621/0666 and 066B/06D6 publish punctuation and the following space
     * separately. 0756 also publishes the end of each substituted string. */
    while(TRUE)
    {
        const u8 *end=cursor;
        u16 width=0;
        bool boundary=FALSE,scrolled=FALSE,finished,look_small=small;
        while(*end && *end!=' ' && *end!=255 && *end!='$')
        {
            u8 value=*end;
            if(value=='\\') { look_small=!look_small;end++;continue; } /* 0631 */
            width+=dialog_widths[dialog_glyph(value,look_small || (substitution_end[end-expanded]&2))]+1;
            boundary=(substitution_end[end-expanded]&1) || value==0xa1 || value==0xa4 || value==0xa5 ||
                value==0xb0 || value=='!' || value=='+' || value==',' || value=='-' || value=='.' || value=='/' || value=='?';
            end++;
            if(boundary) break;
        }
        /* 063C retries the entire word after moving to the next line. */
        while(x+width>=208)
        {
            x=0; y+=10; line++;
            if(y>=40)
            {
                if((line&3)==0) wait_dialog_continue();
                scroll_dialog_bitmap();
                y=30;
            }
            else publish_dialog_word();
        }
        while(cursor<end)
        {
            u16 index;
            if(*cursor=='\\') { small=!small;cursor++;continue; }
            index=dialog_glyph(*cursor,small || (substitution_end[cursor-expanded]&2));cursor++;
            draw_dialog_glyph(x,y,index);
            x+=dialog_widths[index]+1;
        }
        finished=FALSE;
        if(!boundary)
        {
            /* 076B publishes and waits in 07EE, then resumes the same text. */
            if(*cursor=='$')
            { publish_dialog_word();wait_dialog_continue();cursor++;continue; }
            else if(*cursor==' ') { x+=6;cursor++; }
            else if(*cursor==255)
            {
                cursor++;x=0;y+=10;line++;
                if(y>=40)
                {
                    if((line&3)==0) wait_dialog_continue();
                    scroll_dialog_bitmap();y=30;scrolled=TRUE;
                }
            }
            else finished=TRUE;
        }
        if(!scrolled) publish_dialog_word();
        if(finished) break;
    }
}

static void show_dialogue_text(const u8 *source,bool overlay)
{
    render_dialogue_text(source,overlay);wait_dialog_end();
}

#include "save.inc"
#include "merchant.inc"
#include "healer.inc"

/* 0AD1/0B92: prepared opening colors become visible on the next IRQ. */
static void fade_opening_palette(const u16 *target,bool fade_in)
{
    u16 step=fade_in?16:1,n;
    while(step && step<=16)
    {
        bool changed;
        do
        {
            changed=FALSE;
            for(n=0;n<32;n++)
            {
                u16 current=sms_palette[n]&(step*3),desired=target[n]&(step*3);
                if(current!=desired)
                { sms_palette[n]+=current<desired?step:-step;changed=TRUE; }
            }
            if(changed) { wait_frame();set_world_palette();wait_frame(); }
        } while(changed);
        step=fade_in?step>>2:step<<2;
    }
}

static void opening_dialogue(void)
{
    u16 n,colors[32],black[32]={0};
    u32 load_started;
    /* 1197 -> 0B48/0B53: fade music and the name screen, then blank it. */
    sound_ram[0xb]=12;sound_ram[0xc]=sound_ram[0xd]=4;
    fade_opening_palette(black,FALSE);VDP_setEnable(FALSE);
    VDP_resetSprites();VDP_updateSprites(0,CPU);
    for(n=0x3800;n<0x3e00;n+=2) { sms_vram[n]=0xfa;sms_vram[n+1]=1; }
    map_origin=0x3800;draw_map();
    /* 1DEB restores the original menu/equipment colors before 0AA4. */
    for(n=0;n<16;n++) { colors[n]=0;colors[16+n]=menu_palette[n]; }
    colors[22]=0x2a;colors[23]=0;colors[31]=(world_clock()&2)?2:1;
    /* 119D..11A5 restores A74C before revealing the text window. */
    load_started=vtimer;
    decode_planes(number_font_rle,sms_vram+0x1e00,4);
    convert_patterns_range(240,16);VDP_loadTileData(md_patterns+240*8,256,16,CPU);
    /* Source decompression/upload: 70986 Z80 T states with IRQs masked. */
    while(vtimer-load_started<(SYS_isPAL()?1:2)) wait_frame();
    world_clock_shift+=vtimer-load_started;
    /* 0AA4 waits one IRQ before enabling display and starting the ramp. */
    if(SYS_isPAL())
    { load_started=vtimer;do { wait_frame(); } while(vtimer==load_started); }
    else wait_frame();
    VDP_setEnable(TRUE);fade_opening_palette(colors,TRUE);
    show_dialogue_text(opening_text,FALSE);enter_initial_room();
}

#include "house_quest.inc"
#include "house_gold.inc"
#include "minigame.inc"
#include "conditional_house.inc"
#include "fairy.inc"
#include "paid_passage.inc"

extern const u8 plain_house_text[];
extern const u16 plain_house_dialogues[][5],plain_house_dialogue_count;
/* Original667E: exact stationary-UP coordinate and previous-room context. */
static u16 select_plain_house_dialogue(u16 room,u16 outside,u16 coordinate,u8 flags)
{
    u16 n;
    if((flags&0x77)!=0x14) return 65535;
    for(n=0;n<plain_house_dialogue_count;n++)
        if(plain_house_dialogues[n][0]==room && plain_house_dialogues[n][1]==coordinate && plain_house_dialogues[n][2]==(outside&255)) return n;
    return 65535;
}
static void check_house_talk(u16 old_x,u16 old_y,u8 flags)
{
    u16 coordinate,number;
    if(check_minigame(old_x,old_y,flags)) return;
    if(check_fairy(old_x,old_y,flags)) return;
    if(check_paid_passage(old_x,old_y,flags)) return;
    if(!(input&BUTTON_UP)) { house_talk_latch=0;return; }
    if(check_conditional_house(old_x,old_y,flags)) return;
    if(check_house_gold(old_x,old_y,flags)) return;
    if(check_house_quest(old_x,old_y,flags)) return;
    if(world_graphics_class!=1 || house_talk_latch) return;
    coordinate=(((u8)(old_y-12)&248)<<3)+(((u8)(old_x-12)>>2)&62)+126;
    number=select_plain_house_dialogue(room_id,house_return_room,coordinate,flags);
    if(number==65535) return;
    house_dialogue_index=plain_house_dialogues[number][4];house_dialogue_active=1;
    number=plain_house_dialogues[number][3];
    /* Keep the live room and actors while the bitmap window uses their tiles. */
    memcpy(house_dialogue_backup,sms_vram+0x2000,0x1040);
    memcpy(house_dialogue_backup+0x1040,sms_vram+0x1e00,0x200);
    memcpy(house_dialogue_backup+0x1240,sms_vram+0x3800,0x600);
    memcpy(house_dialogue_backup+0x1840,scratch,0x410);
    show_dialogue_text(plain_house_text+number,TRUE);
    memcpy(sms_vram+0x2000,house_dialogue_backup,0x1040);
    memcpy(sms_vram+0x1e00,house_dialogue_backup+0x1040,0x200);
    memcpy(sms_vram+0x3800,house_dialogue_backup+0x1240,0x600);
    memcpy(scratch,house_dialogue_backup+0x1840,0x410);
    convert_patterns_range(256,130);VDP_loadTileData(md_patterns+256*8,272,130,CPU);
    convert_patterns_range(240,16);VDP_loadTileData(md_patterns+240*8,256,16,CPU);
    draw_map();
    house_talk_latch=1;house_dialogue_active=0;world_previous_input=input;
}

/* $1214..125F: translate typed tile IDs back to name bytes and trim spaces. */
static bool finish_name(void)
{
    u16 n,index,length=8;
    for(n=0;n<8;n++)
    {
        u8 tile=sms_vram[0x3a1c+n*2];
        for(index=0;index<40;index++) if(name_typed_tiles[index]==tile) break;
        character_name[n]=index<40?name_ascii[index]:' ';
    }
    while(length && character_name[length-1]==' ') length--;
    character_name[length]=0;
    return length!=0;
}

static void enter_character_name(void)
{
    const u8 *text=name_text,*glyphs=name_grid;
    u16 n,previous=input,held=0;
    VDP_setEnable(FALSE);
    /* $1114 calls $1260 again: restore cursor tiles overwritten by menu RLE. */
    load_mono(0x3000,menu_cursor_bitmap,0x38,3,FALSE);
    convert_patterns(512);
    VDP_loadTileData(md_patterns+384*8,16+384,7,CPU);
    for(n=0x3800;n<0x3e00;n+=2) { sms_vram[n]=0xfa; sms_vram[n+1]=1; }
    draw_frame(0x39ce,17,3);
    draw_frame(0x3b04,27,11);
    draw_text(0x3890,text); while(*text++) {}
    draw_text(0x3910,text); while(*text++) {}
    draw_text(0x3a12,text);
    glyphs=draw_raw_glyphs(0x3b88,glyphs,12,TRUE);
    glyphs=draw_raw_glyphs(0x3c08,glyphs,12,TRUE);
    glyphs=draw_raw_glyphs(0x3c88,glyphs,12,TRUE);
    glyphs=draw_raw_glyphs(0x3d08,glyphs,4,TRUE);
    glyphs=draw_raw_glyphs(0x3d26,glyphs,4,FALSE);
    draw_raw_glyphs(0x3d30,glyphs,3,FALSE);
    for(n=0x3801;n<0x3e00;n+=2) sms_vram[n]&=~16;
    name_cursor=0; name_position=0;
    memset(character_name,0,sizeof(character_name));
    draw_map(); update_name_sprites();
    VDP_setEnable(TRUE);
    while(TRUE)
    {
        u16 pressed,move,old_cursor=name_cursor,old_position=name_position;
        wait_frame();
        pressed=input&~previous;
        move=pressed&15;
        if((input&15)==0) held=0;
        else if((input&15)!=(previous&15)) held=0;
        else if(++held>=24 && ((held-24)&7)==0) move=input&15;
        previous=input;
        /* 12C1..133B: original cursor movement including the uneven last row. */
        if((move&BUTTON_LEFT) && name_cursor>0) name_cursor--;
        else if((move&BUTTON_RIGHT) && name_cursor<41) name_cursor++;
        else
        {
            if((move&BUTTON_UP) && name_cursor>=12)
                name_cursor=name_cursor<40?name_cursor-12:name_cursor==40?32:34;
            if((move&BUTTON_DOWN) && name_cursor<36)
                name_cursor=name_cursor<28?name_cursor+12:name_cursor<31?39:name_cursor<34?40:41;
        }
        /* SMS button 1 -> MD B: backspace. SMS button 2 -> MD C: type/select. */
        if(name_cursor!=old_cursor) sound_effect(0x95); /* 1341 */
        if(pressed&BUTTON_B) { if(name_position) name_position--; }
        if(pressed&(BUTTON_C|BUTTON_START))
        {
            if(name_cursor==40) { if(name_position) name_position--; }
            else if(name_cursor<40)
            {
                sms_vram[0x3a1c+name_position*2]=name_typed_tiles[name_cursor];
                sms_vram[0x3a1d+name_position*2]=8;
                character_name[name_position]=name_ascii[name_cursor];
                if(name_position<7) name_position++;
                else name_cursor=41;
                sound_effect(0x96); /* 11EE */
                draw_map();
            }
            else if(finish_name()) { sound_effect(0xab);opening_dialogue(); }
            else sound_effect(0x96); /* 1253: empty name refused. */
        }
        if(name_position<old_position) sound_effect(0x96); /* 11EE */
        if(return_to_title) return;
        update_name_sprites();
    }
}

static void start_menu(void)
{
    u16 n,previous;
reset_start_menu:
    title_phase=FALSE; title_requested=FALSE;return_to_title=FALSE;
    sound_stop();sound_music(0x89); /* 14F3..14F5: New Game / Continue theme. */
    VDP_setEnable(FALSE);
    memset(sms_vram,0,sizeof(sms_vram));
    /* 1260: original shared cursor, font and numeric/symbol glyph loaders. */
    load_mono(0x1400,font_bitmap,0x180,2,FALSE);
    load_mono(0x1a00,normal_font,0x100,3,TRUE);
    load_mono(0x3000,menu_cursor_bitmap,0x38,3,FALSE);
    decode_planes(number_font_rle,sms_vram+0x1e00,4);
    decode_planes(symbol_font_rle,sms_vram+0x1f40,4);
    decode_planes(menu_rle,sms_vram+0x3040,4);
    convert_patterns(512);
    VDP_loadTileData(md_patterns,16,512,CPU);
    /* 0B53: blank name table word $01FA, scroll zero. */
    for(n=0x3800;n<0x3e00;n+=2) { sms_vram[n]=0xfa; sms_vram[n+1]=1; }
    map_origin=0x3800;
    draw_frame(0x3a52,14,4);
    draw_text(0x3a98,menu_text);
    for(n=0;n<16;n++) { sms_palette[n]=0; sms_palette[16+n]=menu_palette[n]; }
    /* 1DEB: palette slots selected by current inventory (empty new game). */
    sms_palette[22]=0x2a; sms_palette[23]=0; sms_palette[31]=2;
    set_palette(sms_palette);
    menu_selection=save_last_slot?1:0;
    update_menu_selection();
    VDP_setEnable(TRUE);
    previous=input;
    while(TRUE)
    {
        u16 pressed;
        wait_frame(); pressed=input&~previous; previous=input;
        if(pressed&BUTTON_UP) { menu_selection=0; update_menu_selection(); }
        if(pressed&BUTTON_DOWN) { menu_selection=1; update_menu_selection(); }
        if((pressed&(BUTTON_A|BUTTON_B|BUTTON_C|BUTTON_START)) && menu_selection==0) enter_character_name();
        if(return_to_title) return;
        if((pressed&(BUTTON_A|BUTTON_B|BUTTON_C|BUTTON_START)) && menu_selection==1)
        {
            if(show_continue_selection()) enter_initial_room();
            if(return_to_title) return;
            goto reset_start_menu;
        }
    }
}

int main(bool hardReset)
{
    u32 solid[8]={0x11111111,0x11111111,0x11111111,0x11111111,
                  0x11111111,0x11111111,0x11111111,0x11111111};
    const u16 green=0x06a6; /* SMS $19: R=1,G=2,B=1 => MD 3,5,3. */
    (void)hardReset;
    /* Only indoor 2x2 tile updates copy data into the DMA staging buffer.
       2 KiB leaves room for the live dialogue snapshot in the 64 KiB RAM. */
    DMA_setBufferSize(2048);
    VDP_setEnable(FALSE);
    VDP_setScreenWidth256();
    VDP_setScreenHeight224();
    VDP_setPlaneSize(64,32,TRUE);
    VDP_setBackgroundColor(0);
    VDP_loadTileData(solid,1,1,CPU);
    PAL_setColor(33,green);
    VDP_fillTileMapRect(BG_B,TILE_ATTR_FULL(PAL2,0,0,0,1),0,2,32,24);
    JOY_init();save_init();
    sound_stop();sound_ram[3]=SYS_isPAL()?0:0x80;SYS_setVIntCallback(sound_tick);
    while(TRUE)
    {
        title_phase=TRUE; title_requested=FALSE;
        intro_sequence();
        title_sequence();
        if(title_requested) start_menu();
    }
    return 0;
}
