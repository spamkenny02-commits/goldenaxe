/* Original6497: once-only gold gifts/losses, marked before the frontend. */
extern const u8 house_gold_towns[],house_gold_amounts[],house_gold_gain_text[],house_gold_loss_text[];
extern const u16 house_gold_town_count;
static u16 house_gold_remaining,house_gold_text_pc;
static s16 house_gold_delta;
static bool begin_house_gold(u16 room,u16 outside,u16 coordinate,u8 flags)
{
    u16 n;u8 *saved=game_save_state+0x50+(outside&255);
    house_gold_remaining=house_gold_text_pc=0;house_gold_delta=0;
    if(room!=0x3f || coordinate!=0x2dc || (flags&0x77)!=0x14) return FALSE;
    if(*saved&2) return FALSE;
    *saved|=2;
    for(n=0;n<house_gold_town_count;n++) if(house_gold_towns[n]==(outside&255))
    {
        s16 amount=(s8)house_gold_amounts[n];
        house_gold_delta=amount<0?-1:1;house_gold_text_pc=amount<0?0x8df6:0x8e30;
        house_gold_remaining=amount<0?min((u16)-amount,hero_gold):min((u16)amount,255-hero_gold);
        return TRUE;
    }
    return FALSE;
}
static void apply_house_gold_unit(void)
{
    if(!house_gold_remaining) return;
    house_gold_remaining--;hero_gold=(u8)(hero_gold+house_gold_delta);sound_effect(0x95);
}
static bool check_house_gold(u16 old_x,u16 old_y,u8 flags)
{
    u16 coordinate,n;
    if(world_graphics_class!=1 || house_talk_latch) return FALSE;
    coordinate=(((u8)(old_y-12)&248)<<3)+(((u8)(old_x-12)>>2)&62)+126;
    if(!begin_house_gold(room_id,house_return_room,coordinate,flags)) return FALSE;
    house_dialogue_active=1;house_dialogue_index=house_gold_text_pc;
    memcpy(house_dialogue_backup,sms_vram+0x2000,0x1040);
    memcpy(house_dialogue_backup+0x1040,sms_vram+0x1e00,0x200);
    memcpy(house_dialogue_backup+0x1240,sms_vram+0x3800,0x600);
    memcpy(house_dialogue_backup+0x1840,scratch,0x410);
    dialogue_number=house_gold_remaining;
    render_dialogue_text(house_gold_delta<0?house_gold_loss_text:house_gold_gain_text,TRUE);
    while(house_gold_remaining)
    {
        apply_house_gold_unit();merchant_number(0x3dd0,hero_gold);
        for(n=0;n<3;n++) md_map[23*32+8+n]=TILE_ATTR_FULL(PAL1,1,0,0,16+sms_vram[0x3dd0+n*2]);
        VDP_setTileMapDataRect(BG_A,md_map+23*32+8,8,25,3,1,3,CPU);wait_frame();wait_frame();
    }
    wait_dialog_end();
    memcpy(house_dialogue_backup+0x1810,sms_vram+0x3dd0,6); /* 1240+5D0: keep updated HUD. */
    memcpy(sms_vram+0x2000,house_dialogue_backup,0x1040);
    memcpy(sms_vram+0x1e00,house_dialogue_backup+0x1040,0x200);
    memcpy(sms_vram+0x3800,house_dialogue_backup+0x1240,0x600);
    memcpy(scratch,house_dialogue_backup+0x1840,0x410);
    convert_patterns_range(256,130);VDP_loadTileData(md_patterns+256*8,272,130,CPU);
    convert_patterns_range(240,16);VDP_loadTileData(md_patterns+240*8,256,16,CPU);draw_map();
    hero_gold_drawn=hero_gold;hero_gold_pending=FALSE;house_dialogue_active=0;house_talk_latch=1;world_previous_input=input;return TRUE;
}
