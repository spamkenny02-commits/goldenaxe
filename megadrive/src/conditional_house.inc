/* ACB9/AD55 ->6603 ->6614/661C/6624/6634. */
extern const u8 conditional_house_text[];
extern const u16 conditional_house_pcs[],conditional_house_offsets[];
static u16 conditional_house_pc,conditional_house_count,conditional_house_steps;
static void conditional_house_choose(u16 room,u16 outside,u16 coordinate,u8 flags)
{
    static const u16 coordinates[]={0x25c,0x2e0,0x344};
    u16 n;
    conditional_house_pc=conditional_house_count=conditional_house_steps=0;
    if((flags&0x77)!=0x14) return;
    if(room==2 && (outside&255)==0xce)
    {
        for(n=0;n<3;n++) if(coordinate==coordinates[n])
        { conditional_house_pc=conditional_house_pcs[n*2+((game_save_state[0x27]&128)?1:0)];return; }
    }
    if(room!=7 || (outside&255)!=0x22 || coordinate!=0x2d4) return;
    if(!game_save_state[0x22]) { conditional_house_pc=0xa077;return; }
    if(game_save_state[0x47]) { conditional_house_pc=0xa17f;return; }
    game_save_state[0x47]=1;conditional_house_pc=0xa0e6;
    conditional_house_count=min((u16)100,255-hero_gold);
    /* 666D DJNZ with initial B=0 executes256 original increments. */
    conditional_house_steps=conditional_house_count?conditional_house_count:256;
}
static void conditional_house_gold_unit(void)
{ hero_gold=(u8)(hero_gold+1);sound_effect(0x95); }
static bool check_conditional_house(u16 old_x,u16 old_y,u8 flags)
{
    u16 coordinate,n,index;
    if(world_graphics_class!=1 || house_talk_latch) return FALSE;
    coordinate=(((u8)(old_y-12)&248)<<3)+(((u8)(old_x-12)>>2)&62)+126;
    conditional_house_choose(room_id,house_return_room,coordinate,flags);
    if(!conditional_house_pc) return FALSE;
    for(index=0;index<9;index++) if(conditional_house_pcs[index]==conditional_house_pc) break;
    house_dialogue_active=1;house_dialogue_index=conditional_house_pc;
    memcpy(house_dialogue_backup,sms_vram+0x2000,0x1040);
    memcpy(house_dialogue_backup+0x1040,sms_vram+0x1e00,0x200);
    memcpy(house_dialogue_backup+0x1240,sms_vram+0x3800,0x600);
    memcpy(house_dialogue_backup+0x1840,scratch,0x410);
    dialogue_number=conditional_house_count;
    render_dialogue_text(conditional_house_text+conditional_house_offsets[index],TRUE);
    for(index=0;index<conditional_house_steps;index++)
    {
        conditional_house_gold_unit();merchant_number(0x3dd0,hero_gold);
        for(n=0;n<3;n++) md_map[23*32+8+n]=TILE_ATTR_FULL(PAL1,1,0,0,16+sms_vram[0x3dd0+n*2]);
        VDP_setTileMapDataRect(BG_A,md_map+23*32+8,8,25,3,1,3,CPU);wait_frame();wait_frame();
    }
    wait_dialog_end();
    memcpy(house_dialogue_backup+0x1810,sms_vram+0x3dd0,6);
    memcpy(sms_vram+0x2000,house_dialogue_backup,0x1040);
    memcpy(sms_vram+0x1e00,house_dialogue_backup+0x1040,0x200);
    memcpy(sms_vram+0x3800,house_dialogue_backup+0x1240,0x600);
    memcpy(scratch,house_dialogue_backup+0x1840,0x410);
    convert_patterns_range(256,130);VDP_loadTileData(md_patterns+256*8,272,130,CPU);
    convert_patterns_range(240,16);VDP_loadTileData(md_patterns+240*8,256,16,CPU);draw_map();
    hero_gold_drawn=hero_gold;hero_gold_pending=FALSE;house_dialogue_active=0;house_talk_latch=1;world_previous_input=input;return TRUE;
}
