/* 30E8..3123: the magic feather returns to C0C2 (last written save),
 * preserves hero resources and consumes itself only in the exterior. */
static void use_return_feather(void)
{
    u16 n,word,number=save_runtime_checkpoint;
    u32 started,budget,frames;
    save_room_actor_mask(room_id);room_id=number;
    resume_phase=1;sound_effect(0xa6);map_queue=FALSE;
    /* 1F78: twenty interleaved columns, one fresh IRQ per column.
     * Its final 7E00 byte is SAT storage on SMS, outside the visible map. */
    for(n=0;n<20;n++)
    {
        portal_wait_frame();
        for(word=n;word<768;word+=20)
            VDP_setTileMapXY(BG_A,TILE_ATTR_FULL(PAL1,1,0,0,16+255),word&31,(word>>5)+2);
    }
    /* 1F78 jumps to 0B24, bypassing the palette fade in 0B12. */
    VDP_setEnable(FALSE);hide_world_objects();
    memset(world_spell_state,0,sizeof(world_spell_state));
    memset(world_loot_state,0,sizeof(world_loot_state));
    memset(world_actor_state,0,sizeof(world_actor_state));
    /* 190B reconstructs the destination with the already loaded exterior
     * metatiles. State8 does not reload/decompress the background graphics. */
    decode_room_map(number,sms_vram+0x3800,world_new_md);
    game_state=8;hero_items[9]=0;hero_selected_item=0;inventory_hud_icon();
    wait_frame();wait_frame();world_clock_shift+=2;
    /* 3112 supplies the same arrival position as a fresh start/Continue. */
    hero_x=136<<8;hero_y=112<<8;hero_direction=1;
    /* The source still executes the hero's 26E5..2753 tail after 3112.
     * Keep one remaining movement step and hurt decrement before 2C63
     * clears the position fractions/counter for the destination room. */
    integrate_hero();
    if(hero_hurt && hero_hurt<=128) hero_hurt--;
    hero_x&=0xff00;hero_y&=0xff00;
    world_dungeon_number=world_dungeon_dark=0;resume_phase=2;started=vtimer;
    house_animation_scan=house_animation_patterns_pending=0;
    dungeon_animation_scan=dungeon_animation_phase=dungeon_bitmap_pending=0;
    load_current_world_actors(number);
    room_shutter_state=(world_actor_count&128)?2:0;
    room_shutter_direction=0;room_script_coordinate_pending=1;
    if(world_actor_tiles) VDP_loadTileData(md_patterns+256*8,16+256,world_actor_tiles,CPU);
    hero_state=hero_animation=hero_counter=hero_pending=hero_casting=0;
    hero_dx=hero_dy=0;hero_flags=3;hero_scroll_x=hero_scroll_y=0;
    hero_loaded_pose=65535;prepare_hero_patterns();
    if(hero_patterns_pending)
    { VDP_loadTileData(md_patterns+496*8,16+496,hero_pattern_tiles,CPU);hero_patterns_pending=FALSE; }
    map_origin=0x3800;draw_map();update_world_music();
    /* The shared actor budget is instruction-derived; its IRQ reserve and
     * the remaining state8 control work are still approximate. */
    budget=(SYS_isPAL()?71364UL:59736UL)-3072;
    frames=(world_actor_load_tstates+20000UL+budget-1)/budget;
    while(vtimer-started<frames) portal_wait_frame();
    world_clock_shift+=vtimer-started-1;game_state=12;
    reveal_world();world_previous_input=input;
}
