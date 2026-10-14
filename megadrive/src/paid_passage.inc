extern const u8 paid_passage_towns[],paid_passage_prices[],paid_passage_text[],paid_passage_routes[][4];
static u16 paid_passage_cost,paid_passage_steps,paid_passage_pc,paid_passage_target,paid_passage_y,paid_passage_x;
static bool begin_paid_passage(u16 room,u16 outside,u16 coordinate,u8 flags,const u8 *cells)
{
    u16 n;paid_passage_cost=paid_passage_steps=paid_passage_pc=0;
    if(room!=0x9f || (flags&0x77)!=0x14 || coordinate!=0x25c || cells[0x38]==1) return FALSE;
    for(n=0;n<6;n++) if((outside&255)==paid_passage_towns[n])
    { paid_passage_cost=paid_passage_prices[n];paid_passage_pc=0x911e;return TRUE; }
    return FALSE;
}
static bool pay_paid_passage(bool accepted,u8 *cells)
{
    if(!accepted) return FALSE;
    if(hero_gold<paid_passage_cost) { paid_passage_pc=0x8bcd;return FALSE; }
    paid_passage_steps=paid_passage_cost;
    return TRUE;
}
static void open_paid_passage_cells(u8 *cells)
{
    cells[0x37]=cells[0x38];cells[0x38]=cells[0x39];
    cells[0x47]=cells[0x48];cells[0x48]=cells[0x49];
}
static bool select_paid_passage_exit(u16 room,u16 outside,u16 coordinate,u8 flags)
{
    u16 n;paid_passage_target=paid_passage_y=paid_passage_x=0;
    if(room!=0x9f || (flags&0x30)!=0x30 || coordinate!=0x19c) return FALSE;
    for(n=0;n<6;n++) if((outside&255)==paid_passage_routes[n][0])
    { paid_passage_target=paid_passage_routes[n][1];paid_passage_y=paid_passage_routes[n][2];paid_passage_x=paid_passage_routes[n][3];return TRUE; }
    return FALSE;
}
static void load_paid_passage_room(void)
{
    u32 started=vtimer;
    sound_music(0xb0); /*16D0:fade the previous room music while loading. */
    door_transition_loading=TRUE;
    load_house_room(paid_passage_target,0);
    update_world_music(); /*1CAF runs before1FA7 reveals the destination. */
    /* 16D0..1FA7: only the 1DE2/229C wait advances SMS C02F.
     * Conversion interrupts keep audio running without advancing game time. */
    world_clock_shift+=vtimer-started-1;
    door_transition_loading=FALSE;
}
static bool check_paid_passage(u16 old_x,u16 old_y,u8 flags)
{
    u16 coordinate;bool paid;
    if(world_graphics_class!=1 || room_id!=0x9f) return FALSE;
    coordinate=(((u8)(old_y-12)&248)<<3)+(((u8)(old_x-12)>>2)&62)+126;
    if(select_paid_passage_exit(room_id,house_return_room,coordinate,flags))
    {
        u16 black[32]={0},n;
        house_return_room=paid_passage_target;house_return_y=paid_passage_y<<8;house_return_x=paid_passage_x<<8;
        hero_y=(hero_y&255)|house_return_y;hero_x=(hero_x&255)|house_return_x;world_dungeon_number=0;
        /* 65E1 fades;616F marks the destination flag before state8 reloads. */
        resume_phase=1;fade_world_palette(black,FALSE);resume_phase=2;
        game_save_state[0x50+(paid_passage_target&255)]|=1;
        load_paid_passage_room();
        /* State8 ->1DE2 falls through1DEB and restores all sprite colors. */
        for(n=0;n<16;n++) sms_palette[16+n]=menu_palette[n];
        prepare_hero_armor_palette();sms_palette[31]=(world_clock()&2)?2:1;
        reveal_world();return TRUE;
    }
    if(house_talk_latch || !begin_paid_passage(room_id,house_return_room,coordinate,flags,scratch+0x800)) return FALSE;
    minigame_overlay_begin();house_dialogue_index=paid_passage_pc;dialogue_number=paid_passage_cost;
    render_dialogue_text(paid_passage_text,TRUE);paid=pay_paid_passage(minigame_confirm(TRUE),scratch+0x800);
    if(paid) { minigame_money(-1,paid_passage_steps);open_paid_passage_cells(scratch+0x800); }
    else if(paid_passage_pc==0x8bcd) { render_dialogue_text(merchant_poor,TRUE);wait_dialog_end(); }
    minigame_overlay_end();build_room_map(sms_vram+0x3800,world_new_md);draw_map();
    house_talk_latch=1;world_previous_input=input;return TRUE;
}
