/* 30A7,37B3/37BD,6AFB..6EAD: both full-screen magic levels. */
#include "screen_spell_assets.inc"
extern const u8 actor_flying_sine[];
_Static_assert(6400<=sizeof(house_dialogue_storage.dialogue),"Screen spell exceeds modal workspace");

#include "screen_spell_pacing.inc"
static u32 screen_spell_last_publication,screen_spell_previous_irq,screen_spell_loop_work;

static void screen_spell_sprites(u8 *phases,bool particles)
{
    u16 n,count=screen_spell_sprite_count;u8 *sat=sms_vram+0x1d40;
    VDP_resetSprites();
    for(n=0;n<count;n++)
    {
        s16 y=sat[n]<208?(s16)sat[n]:(s16)sat[n]-256;
        VDP_setSpriteFull(n,sat[64+n*2],y+17,SPRITE_SIZE(1,1),
            TILE_ATTR_FULL(PAL1,0,0,0,272+sat[65+n*2]),n+1);
    }
    prepare_world_sms_sprite_overflow(count);
    if(count) VDP_setSpriteLink(count-1,0);
    if(particles) for(n=0;n<8;n++) phases[n]+=9;
}

static void screen_spell_present(void)
{
    u32 period=SYS_isPAL()?71364UL:59736UL,work,gap=1,audio;
    if(screen_spell_iteration)
    {
        /* Previous fullIRQ/0BB3 restore, previous22C6 transfer/loop tail,
         * current foreground, then CALL0B95 and its174T save/arm prefix. */
        work=screen_spell_previous_irq+149+37289+(screen_spell_level==2?40:39)+screen_spell_loop_work+17+174;
        audio=524+sound_source_work.tstates;
        if(audio>=period) screen_spell_pacing_error=2;
        else if(work>period) gap=(work-audio+(period-audio)-1)/(period-audio);
    }
    screen_spell_model_gap=gap;
    while(vtimer-screen_spell_last_publication+1<gap) portal_wait_frame();
    __asm__ volatile ("" ::: "memory");
    if(screen_spell_iteration && vtimer-screen_spell_last_publication+1>gap) screen_spell_late_publications++;
    __asm__ volatile ("" ::: "memory");
    screen_spell_video_pending=1;
    while(screen_spell_video_pending) __asm__ volatile ("nop");
    __asm__ volatile ("" ::: "memory");
    SYS_doVBlankProcessEx(IMMEDIATELY);input=JOY_readJoypad(JOY_1);
    screen_spell_last_publication=vtimer;screen_spell_previous_irq=screen_spell_irq_cost();
    screen_spell_clock=(screen_spell_clock+1)&255;world_clock_shift=vtimer-screen_spell_clock;
}

static void run_screen_spell(void)
{
    u8 *work=house_dialogue_backup,*saved=work+1024;
    const u8 *source,*extra;u16 destination;
    u8 phases[8];u16 level=screen_spell_level,n,row,col;
    const u8 *patterns=level==1?screen_spell_patterns1:screen_spell_patterns2;
    u16 bytes=level==1?sizeof(screen_spell_patterns1):sizeof(screen_spell_patterns2);
    u32 started,budget,frames;
    if(level<1 || level>2) { screen_spell_level=0;return; }
    screen_spell_active=1;screen_spell_iteration=0;screen_spell_pacing_error=screen_spell_late_publications=0;
    memcpy(saved,sms_vram+0x3800,1280);memcpy(work+2304,sms_vram+4096,4096);memset(work,0,1024);
    memset(world_spell_state,0,48);memset(world_loot_state,0,336);
    memset(world_actor_state+8*48,0,8*48); /* 6E21: the upper actor half is temporary. */
    for(n=0;n<8;n++) phases[n]=n*32;
    for(n=0;n<16;n++) sms_palette[n]=world_palette[n];
    if(level==2) { for(n=0;n<16;n++) sms_palette[n]=sms_palette[16+n];sms_palette[2]=0x17; }
    for(n=0x3800;n<0x3d00;n+=2) { sms_vram[n]=255;sms_vram[n+1]=level==1?8:0;md_map[(n-0x3800)/2]=(level==1?0x2000:0)+16+255; }
    memcpy(sms_vram,patterns,bytes);convert_patterns_range_fast(0,bytes/32);
    VDP_loadTileData(md_patterns,16,bytes/32,CPU);
    for(n=0;n<48;n++) { memcpy(sms_vram+0x3e00+n*4,screen_spell_hero_bitmap+1+n*3,3);sms_vram[0x3e03+n*4]=0; }
    convert_patterns_range_fast(496,6);VDP_loadTileData(md_patterns+496*8,512,6,CPU);hero_patterns_pending=FALSE;
    set_world_palette();map_origin=0x3800;draw_map();
    if(level==1) for(n=0;n<22;n++)
    {
        work[n*32]=22;work[n*32+1]=255-n;
        work[n*32+2]=screen_spell_grid[n*2];work[n*32+3]=screen_spell_grid[n*2+1];
    }
    else for(n=0;n<4;n++) { work[n*32]=4;work[n*32+1]=n*16; }
    /*20DF/20E4 performs one full0B95 wait; decoding itself freezes C02F. */
    screen_spell_clock=(screen_spell_clock+1)&255;world_clock_shift=vtimer-screen_spell_clock;
    screen_spell_active=2;screen_spell_last_publication=vtimer;
    do
    {
        screen_spell_loop_work=screen_spell_map_cost(work,level);
        if(level==1) for(n=0;n<22;n++)
        {
            u8 *e=work+n*32;u16 address=e[2]|((u16)e[3]<<8);
            const u8 *cells=e[1]<14?screen_spell_cells1+e[1]*12:0;
            if(!e[0]) continue;
            for(row=0;row<4;row++) for(col=0;col<3;col++)
            { u16 offset=(address-0xd600)+row*64+col*2;if(offset<1280) { sms_vram[0x3800+offset]=cells?cells[row*3+col]:255;md_map[offset/2]=0x2000+16+sms_vram[0x3800+offset]; } }
            e[1]++;
            if(e[1]==22) { e[1]=0;if(++e[4]==3) e[0]=0; }
        }
        else for(n=0;n<4;n++)
        {
            u8 *e=work+n*32;const u8 *b=screen_spell_blocks+e[2]*6;
            u16 address=(b[0]|((u16)b[1]<<8))+e[1];
            u16 source=(b[2]|((u16)b[3]<<8))-0xa800;
            for(row=0;row<b[4];row++)
            {
                u16 offset=(address-0xd600)+row*64;
                if(offset<1280)
                {
                    memcpy(sms_vram+0x3800+offset,screen_spell_cells2+source,b[5]*2);
                    memcpy(md_map+offset/2,screen_spell_cells2_md+source/2,b[5]*2);
                }
                source+=b[5]*2;
            }
            if(++e[8]==1) { e[8]=0;if(++e[2]>=10) { e[2]=7;e[9]++; } }
        }
        if(level==2) sms_palette[1]=(screen_spell_clock&3)?0:3;
        screen_spell_loop_work+=screen_spell_sprite_cost(phases,level==2 || work[11*32]!=0,level);
        screen_spell_sprites(phases,level==2 || work[11*32]!=0);
        /* 22C3 waits for a fresh IRQ then publishes all 1280 name bytes. */
        screen_spell_present();screen_spell_iteration++;
    } while(level==1?work[21*32]!=0:work[9]!=7);
    screen_spell_active=3;
    for(n=0;n<16;n++)
    {
        u8 *e=world_actor_state+n*48;u8 damage;
        if(!e[0] || !e[0x1b] || !(e[3]&2)) continue;
        damage=world_attack_strength[hero_selected_item*4+hero_items[hero_selected_item]];
        damage=damage<e[0x1a]?1:damage-e[0x1a];
        e[0x1d]+=damage;e[0x1e]=0;e[0x1f]=0xc3;
    }
    screen_spell_level=0;hero_selected_item=0;
    /*6BEA clears the old effect before16EF replaces its patterns. */
    VDP_resetSprites();VDP_updateSprites(0,CPU);
    VDP_fillTileMapRect(BG_A,TILE_ATTR_FULL(PAL1,0,0,0,16+255),0,2,32,20);
    memset(world_spell_state,0,48);memset(world_loot_state,0,336);
    memcpy(sms_vram+0x3800,saved,1280);
    started=vtimer;memcpy(sms_vram+4096,work+2304,4096);
    source=decode_planes(world_graphics_class==2?world_dungeon_background_rle:world_graphics_class==1?world_house_background_rle:world_background_rle,sms_vram,4);
    decode_planes(source,scratch,2);apply_ice_bell_metatiles(room_id);
    extra=world_graphics_class==2?world_dungeon_extra_meta:world_graphics_class==1?world_house_extra_meta:world_extra_meta;
    destination=0x400;
    while(*extra<128) { memcpy(scratch+destination,scratch+*extra++*8,8);destination+=8; }
    extra++;
    for(n=0x401;n<destination;n+=2) scratch[n]=(scratch[n]&31)|*extra++;
    for(n=0;n<0x220;n++)
    {
        u16 word=scratch[n*2]|((u16)scratch[n*2+1]<<8);
        world_metatiles_md[n]=TILE_ATTR_FULL((word>>11)&1,(word>>12)&1,(word>>10)&1,(word>>9)&1,16+(word&511));
    }
    build_room_map(sms_vram+0x3800,world_new_md);
    inventory_hud_icon();hero_loaded_pose=65535;prepare_hero_patterns();
    convert_patterns_range_fast(0,193);VDP_loadTileData(md_patterns,16,193,CPU);
    if(world_graphics_class==2) prepare_dungeon_palette(room_id);
    else for(n=0;n<16;n++) sms_palette[n]=world_graphics_class?world_house_palette[n]:world_palette[n];
    VDP_fillTileMapRect(BG_B,TILE_ATTR_FULL(PAL2,0,0,0,1),0,2,32,20);
    budget=(SYS_isPAL()?71364UL:59736UL)-3072UL;
    frames=((world_graphics_class==2?693284UL:world_graphics_class?664703UL:995861UL)+290000UL+budget-1)/budget+1;
    while(vtimer-started<frames) portal_wait_frame();
    /*20DF then1DE2 contribute two further full waits, not one tick for
     * every physical VBlank spent reloading/decompressing the room. */
    screen_spell_clock=(screen_spell_clock+2)&255;world_clock_shift=vtimer-screen_spell_clock;
    screen_spell_active=0;set_world_palette();draw_map();world_clock_shift=vtimer-screen_spell_clock;
}
