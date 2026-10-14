extern const u8 fairy_towns[],fairy_kinds[],fairy_life_text[],fairy_magic_text[],fairy_life_label[],fairy_magic_label[];
static u16 fairy_item,fairy_text_pc;
static bool begin_fairy(u16 room,u16 outside,u16 coordinate,u8 flags)
{
    u16 n;u8 masked=flags&0x77;u8 *saved=game_save_state+0x50+(outside&255);
    fairy_item=fairy_text_pc=0;
    /* Source5FCE RET Z deliberately excludes stationary-UP flags14. */
    if(room!=0xaf || masked==0x14 || (u16)(coordinate-0x25c-(masked<0x14))!=0) return FALSE;
    if(*saved&2) return FALSE;
    *saved|=2;
    for(n=0;n<8;n++) if((outside&255)==fairy_towns[n])
    { fairy_item=(fairy_kinds[n]&128)?28:42;fairy_text_pc=fairy_item==28?0x9035:0x9021;return TRUE; }
    return FALSE;
}
static void fairy_apply_capacity(void)
{
    u16 capacity=(u8)((fairy_item==28?hero_max_magic:hero_max_health)+8);
    if(capacity>=128) capacity=128;
    if(fairy_item==28) hero_magic=hero_max_magic=capacity;
    else hero_max_health=capacity;
}
static void fairy_health_unit(void)
{ hero_health=(u8)(hero_health+1);sound_effect(0x95); }
/* Original1E4E rebuilds the HUD, including unused capacity slots. */
static void fairy_clear_unused_gauge_cells(void)
{
    u16 n,address;
    for(n=hero_max_health>>3;n<16;n++)
    { address=0x3d5e + n*2;sms_vram[address]=0xd0;sms_vram[address+1]=0x58; }
    for(n=hero_max_magic>>3;n<16;n++)
    { address=0x3dde + n*2;sms_vram[address]=0xd0;sms_vram[address+1]=0x58; }
}
static bool check_fairy(u16 old_x,u16 old_y,u8 flags)
{
    u16 coordinate;
    if(world_graphics_class!=1) return FALSE;
    coordinate=(((u8)(old_y-12)&248)<<3)+(((u8)(old_x-12)>>2)&62)+126;
    if(!begin_fairy(room_id,house_return_room,coordinate,flags)) return FALSE;
    /* Standard bitmap overlay and reward modal are shared with other NPCs. */
    minigame_overlay_begin();house_dialogue_index=fairy_text_pc;
    render_dialogue_text(fairy_item==28?fairy_magic_text:fairy_life_text,TRUE);wait_dialog_end();minigame_overlay_end();
    prepare_room_cells(room_id);build_room_map(sms_vram+0x3800,world_new_md);
    house_dialogue_active=1;
    fairy_clear_unused_gauge_cells();
    show_item_reward_text(fairy_item,0,fairy_item==28?fairy_magic_label:fairy_life_label);
    fairy_apply_capacity();
    if(fairy_item==42) while(hero_health!=hero_max_health)
    {
        fairy_health_unit();prepare_hero_health_bar(TRUE);
        VDP_setTileMapDataRect(BG_A,md_map+21*32+15,15,23,hero_max_health>>3,1,hero_max_health>>3,CPU);wait_frame();wait_frame();
    }
    house_dialogue_active=0;world_previous_input=input;return TRUE;
}
