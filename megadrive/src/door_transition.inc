/* 6594/6509/65D0/654D ->0B12,state8,1FA7 for standard doors. */
static void load_door_room(u16 number,u16 graphics_class)
{
    u16 black[32]={0},n;
    u32 started;
    bool changed=world_graphics_class!=graphics_class;
    if(number!=room_id) save_room_actor_mask(room_id);
    room_id=number; /*18E2 publishes the destination before the old scene fades. */
    resume_phase=1;fade_world_palette(black,FALSE);
    resume_phase=2;started=vtimer;
    if(changed) sound_music(0xb0);
    door_transition_loading=TRUE;
    load_house_room(number,graphics_class);
    update_world_music();
    world_clock_shift+=vtimer-started-1; /*Only229C advances C02F while loading. */
    door_transition_loading=FALSE;
    for(n=0;n<16;n++) sms_palette[16+n]=menu_palette[n];
    prepare_hero_armor_palette();sms_palette[31]=(world_clock()&2)?2:1;
    reveal_world();
}
