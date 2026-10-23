/* 31E7..3291, bank2 837C/83EC/844D: exterior world overview. */
#include "world_overview_assets.inc"
_Static_assert(6624<=sizeof(house_dialogue_storage.dialogue),"Overview backup exceeds modal workspace");
static volatile u16 world_overview_active;

static u8 overview_cell_color(u8 cell)
{
    u8 pair=overview_colors[cell>>1];
    return (cell&1)?pair&15:pair>>4;
}

static void overview_sprites(void)
{
    u16 count=0,x,y;
    VDP_resetSprites();
    /* SMS IRQ displays the sprite list built by the previous menu loop.
     * The native SAT copy is immediate, so use that previous phase. */
    if((u8)(world_clock()-1)&16)
    {
        x=0x48+(room_id&15)*8+((hero_x>>13)&7);
        y=0x10+(((room_id-16)&240)>>4)*5+((((hero_y>>8)-16)&224)>>5);
        count=add_sms_sprite_frame(0,x,y,overview_hero_frame,0);
    }
    else if(game_save_state[0x45])
        count=add_sms_sprite_frame(0,0x90,0x30,overview_treasure_frame,0);
    if(count) VDP_setSpriteLink(count-1,0);
    VDP_updateSprites(count,CPU);
}

static void show_world_overview(void)
{
    /* World video jobs are consumed before simulation. Its 7248-byte union
     * is available throughout this blocking modal; no extra permanent RAM. */
    u8 *saved=house_dialogue_backup;
    u16 number=room_id,n,row,col,plane,tile,previous=input,original31=sms_palette[31];
    u32 closed_at,budget,frames,work=33;
    u8 metadata[3];
    world_overview_active=1;
    memcpy(saved,sms_vram,5120);memcpy(saved+5120,sms_vram+0x3f40,64);
    memcpy(saved+5184,sms_vram+0x3800,1280);memcpy(saved+6464,scratch+0x800,160);
    memcpy(metadata,room_metadata,3);
    blank_inventory_playfield();
    for(n=0x3800;n<0x3d00;n+=2) { sms_vram[n]=255;sms_vram[n+1]=8; }
    draw_frame(0x380e,19,13);
    for(row=0;row<10;row++) for(col=0;col<15;col++)
    {
        u16 offset=0x3892+row*64+col*2;
        sms_vram[offset]=row*16+col;sms_vram[offset+1]=0;
    }
    for(n=0x3801;n<0x3d00;n+=2) sms_vram[n]&=~16;
    memset(sms_vram,0,5120);
    for(tile=144;tile<159;tile++) for(row=3;row<8;row++) sms_vram[tile*32+row*4]=255;
    for(n=0;n<4;n++) sms_palette[12+n]=overview_palette[n];
    decode_planes(overview_markers_rle,sms_vram+0x3f40,4);
    /* 837C publishes the frame and empty pattern grid before 31E7 walks
     * the rooms. Publish the two affected tiles as each room is sampled. */
    convert_patterns_range_fast(0,160);convert_patterns_range_fast(506,2);
    VDP_loadTileData(md_patterns,16,160,CPU);VDP_loadTileData(md_patterns+506*8,522,2,CPU);
    set_world_palette();map_origin=0x3800;draw_map();
    overview_work_budget=0;overview_pacing_error=0;overview_pacing=1;
    for(room_id=0x10;room_id<256;room_id++)
    {
        if((room_id&15)==15) continue;
        u16 cost_index=room_id*4+(ice_bell_state?2:0)+(game_save_state[0x50+room_id]&1);
        u16 offset=world_room_index[room_id*2]|((u16)world_room_index[room_id*2+1]<<8);
        /*190B prepares cells, not the unused640-word full room map. */
        decode_planes(world_room_streams+offset,scratch+0x800,1);prepare_room_cells(room_id);
        work+=11+17+overview_decode_tstates[cost_index]+7+5*(7+4+4+7+12)-5;
        for(row=0;row<5;row++) for(col=0;col<8;col++)
        {
            u16 cell=row*32+col*2,y=(((room_id-16)&240)>>4)*5+row;
            u16 address=(y>>3)*512+(room_id&15)*32+(y&7)*4;
            u8 color=0,k;
            work+=7+13+overview_pixel_tstates[col]+4+4+7+(col<7?12:7);
            static const u8 offsets[4]={0,1,16,17};
            for(k=0;k<4;k++)
            {
                u8 value=scratch[0x800+cell+offsets[k]],next=overview_cell_color(value);
                if(!(value&1)) work+=11;
                if(value>=68) work--;
                if(next<color) work-=8;
                if(next>color) color=next;
            }
            for(plane=0;plane<4;plane++) if(color&(1<<plane)) sms_vram[address+plane]|=0x80>>col;
        }
        work+=10+16+6+16+((room_id&15)==14?8:13);
        if((room_id&15)==14) work+=16+6+16+4+4+(room_id==254?7:19);
        /* Cumulative source instruction work, with live audio-only IRQ debit.
         * Native decode/projection time already spent consumes this deadline. */
        while(overview_work_budget<work && !overview_pacing_error) __asm__ volatile ("nop");
        {
            u16 first=(((room_id-16)&240)>>4)*5;
            u16 last=(first+4)>>3;
            for(tile=first>>3;tile<=last;tile++)
            {
                u16 pattern=tile*16+(room_id&15);
                convert_patterns_range_fast(pattern,1);
                VDP_loadTileData(md_patterns+pattern*8,16+pattern,1,CPU);
            }
        }
    }
    overview_pacing=0;
    room_id=number;memcpy(scratch+0x800,saved+6464,160);memcpy(room_metadata,metadata,3);
    convert_patterns_range_fast(0,160);convert_patterns_range_fast(506,2);
    VDP_loadTileData(md_patterns,16,160,CPU);VDP_loadTileData(md_patterns+506*8,522,2,CPU);
    sms_palette[31]=3;set_world_palette();map_origin=0x3800;draw_map();
    /* 326A resumes input sampling after construction. Retain activation's
     * previous input: a different button held during generation is fresh. */
    world_overview_active=2;
    while(TRUE)
    {
        wait_frame();overview_sprites();
        if((input&~previous)&(BUTTON_B|BUTTON_C)) break;
        previous=input;
    }
    world_overview_active=3;closed_at=vtimer;blank_inventory_playfield();
    memcpy(sms_vram,saved,5120);memcpy(sms_vram+0x3f40,saved+5120,64);
    memcpy(sms_vram+0x3800,saved+5184,1280);
    build_room_map(sms_vram+0x3800,world_new_md);
    for(n=0;n<16;n++) sms_palette[n]=world_palette[n];
    sms_palette[31]=original31;hero_selected_item=0;inventory_hud_icon();
    convert_patterns_range_fast(0,160);convert_patterns_range_fast(506,2);
    VDP_loadTileData(md_patterns,16,160,CPU);VDP_loadTileData(md_patterns+506*8,522,2,CPU);
    VDP_fillTileMapRect(BG_B,TILE_ATTR_FULL(PAL2,0,0,0,1),0,2,32,20);
    /* 3286..3291 shares 16EF/1DE2 restoration with the inventory. Retain
     * the original compressed-background work while reusing restored tiles.
     * The shared room/HUD and IRQ reserve remain approximate. */
    budget=(SYS_isPAL()?71364UL:59736UL)-3072UL;
    frames=(995861UL+290000UL+budget-1)/budget+1;
    while(vtimer-closed_at<frames-2) wait_frame();
    set_world_palette();draw_map();update_hero_sprites();
    frames+=SYS_isPAL()?2:3;
    while(vtimer-closed_at<frames) wait_frame();
    world_clock_shift+=2;
    world_overview_active=0;world_previous_input=input;
}
