#include "minigame_core.inc"
extern const u8 minigame_text[],minigame_confirm_font[],minigame_confirm_words[];
extern const u16 minigame_text_index[];
static u16 minigame_active,minigame_confirm_selection;
static void minigame_overlay_begin(void)
{
    house_dialogue_active=1;
    memcpy(house_dialogue_backup,sms_vram+0x2000,0x1040);
    memcpy(house_dialogue_backup+0x1040,sms_vram+0x1e00,0x200);
    memcpy(house_dialogue_backup+0x1240,sms_vram+0x3800,0x600);
    memcpy(house_dialogue_backup+0x1840,scratch,0x410);
}
static void minigame_overlay_end(void)
{
    memcpy(house_dialogue_backup+0x1810,sms_vram+0x3dd0,6);
    memcpy(sms_vram+0x2000,house_dialogue_backup,0x1040);
    memcpy(sms_vram+0x1e00,house_dialogue_backup+0x1040,0x200);
    memcpy(sms_vram+0x3800,house_dialogue_backup+0x1240,0x600);
    memcpy(scratch,house_dialogue_backup+0x1840,0x410);
    convert_patterns_range(256,130);VDP_loadTileData(md_patterns+256*8,272,130,CPU);
    convert_patterns_range(240,16);VDP_loadTileData(md_patterns+240*8,256,16,CPU);draw_map();
    house_dialogue_active=0;hero_gold_drawn=hero_gold;hero_gold_pending=FALSE;world_previous_input=input;
}
static void minigame_text_render(u16 index)
{ house_dialogue_index=index;render_dialogue_text(minigame_text+minigame_text_index[index],TRUE); }
static void minigame_message(u16 index)
{ minigame_overlay_begin();minigame_text_render(index);wait_dialog_end();minigame_overlay_end(); }
/* 60BC uses a hero-relative frame; replay60B1 uses fixed D9F2. */
static bool minigame_confirm(bool relative)
{
    u16 address=relative?0x3800+((u8)((hero_y>>8)-24))*8+((u8)((hero_x>>8)+16)>>2):0x3bf2;
    u16 cursor=address+0x42,n,previous=input,pressed;
    load_mono(0x1960,minigame_confirm_font,32,3,TRUE);
    convert_patterns_range(203,4);VDP_loadTileData(md_patterns+203*8,219,4,CPU);
    draw_frame(address,6,4);
    memcpy(sms_vram+cursor+2,minigame_confirm_words,6);
    memcpy(sms_vram+cursor+66,minigame_confirm_words+6,6);
    minigame_confirm_selection=1;
    while(TRUE)
    {
        const u8 *words=minigame_confirm_words+12+(minigame_confirm_selection?2:0);
        memcpy(sms_vram+cursor,words,2);memcpy(sms_vram+cursor+64,words+2,2);
        draw_map();wait_frame();pressed=input&~previous;previous=input;
        if(pressed&BUTTON_C) { sound_effect(0xab);return minigame_confirm_selection!=0; }
        n=minigame_confirm_selection;
        if((pressed&BUTTON_UP) && !n) minigame_confirm_selection=1;
        else if(pressed&(BUTTON_DOWN|BUTTON_B)) minigame_confirm_selection=0;
        if(n!=minigame_confirm_selection) sound_effect(0x95);
    }
}
static void minigame_money(s16 delta,u16 count)
{
    u16 n;
    while(count--)
    {
        hero_gold=(u8)(hero_gold+delta);sound_effect(0x95);merchant_number(0x3dd0,hero_gold);
        for(n=0;n<3;n++) md_map[23*32+8+n]=TILE_ATTR_FULL(PAL1,1,0,0,16+sms_vram[0x3dd0+n*2]);
        VDP_setTileMapDataRect(BG_A,md_map+23*32+8,8,25,3,1,3,CPU);wait_frame();wait_frame();
    }
    hero_gold_drawn=hero_gold;hero_gold_pending=FALSE;
}
static void minigame_grid(void)
{
    sound_effect(0x95);build_room_map(sms_vram+0x3800,world_new_md);draw_map();wait_frame();
}
/* 1F78 wipes20 interleaved columns, then normal state8 reveals the room. */
static void minigame_change_room(u16 room)
{
    u16 n,p;u8 hud[256];memcpy(hud,sms_vram+0x3d00,256);sound_effect(0xa6);
    for(n=0;n<20;n++)
    {
        wait_frame();
        for(p=n;p<768;p+=20) { sms_vram[0x3800+p*2]=255;sms_vram[0x3801+p*2]=0x18; }
        draw_map();
    }
    VDP_setEnable(FALSE);memcpy(sms_vram+0x3d00,hud,256);
    load_house_room(room,1);reveal_world();world_previous_input=input;
}
static bool check_minigame(u16 old_x,u16 old_y,u8 flags)
{
    u16 coordinate,cell,n;u8 *cells=scratch+0x800;bool accepted;
    if(world_graphics_class!=1) return FALSE;
    coordinate=(((u8)(old_y-12)&248)<<3)+(((u8)(old_x-12)>>2)&62)+126;
    if(room_id==0x5f && !house_talk_latch && (flags&0x77)==0x14 && coordinate==0x2dc)
    {
        minigame_overlay_begin();minigame_text_render(0);accepted=minigame_confirm(TRUE);
        if(!accepted) { minigame_text_render(1);wait_dialog_end(); }
        else if(hero_gold<10) { render_dialogue_text(merchant_poor,TRUE);wait_dialog_end();accepted=FALSE; }
        else minigame_money(-1,10);
        minigame_overlay_end();house_talk_latch=1;
        if(accepted) { minigame_active=1;minigame_stage=0;minigame_change_room(11); }
        return TRUE;
    }
    if(room_id!=11 || !minigame_active) return FALSE;
    if(!minigame_stage) { minigame_message(2);minigame_stage=1;return TRUE; }
    if(minigame_stage==1)
    {
        cell=minigame_select(coordinate,flags,cells);if(cell==65535) return TRUE;
        /* Provisional engine RNG; mapping/rejection are original671E..6762. */
        while(!minigame_draw(cells,cell,(u8)random()));
        minigame_grid();if(cells[cell]>=0x38) minigame_message(cells[cell]==0x38?6:7);
        return TRUE;
    }
    if(minigame_stage==2)
    {
        if(cells[12])
        {
            for(n=0x33;n<0x3d;n++) if(minigame_flip(cells,n))
            { u16 f;for(f=0;f<15;f++) wait_frame();minigame_grid(); }
            for(n=3;n<=9;n+=3)
            {
                bool changed=minigame_flip(cells,n);changed=minigame_flip(cells,n+1)||changed;
                if(changed) { u16 f;for(f=0;f<15;f++) wait_frame();minigame_grid(); }
            }
        }
        minigame_stage=3;return TRUE;
    }
    minigame_prepare_reward(hero_gold,cells);minigame_overlay_begin();dialogue_number=minigame_reward_count;
    minigame_text_render(minigame_reward_delta<0?4:3);minigame_money(minigame_reward_delta,minigame_reward_steps);
    wait_dialog_end();minigame_overlay_end();accepted=FALSE;
    if(hero_gold>=10)
    {
        minigame_overlay_begin();minigame_text_render(5);accepted=minigame_confirm(FALSE);minigame_overlay_end();
    }
    if(accepted)
    {
        decode_room_map(11,sms_vram+0x3800,world_new_md);minigame_overlay_begin();minigame_text_render(8);
        minigame_money(-1,10);wait_dialog_end();minigame_overlay_end();minigame_stage=1;
    }
    else
    {
        minigame_message(1);hero_y=0x5800;hero_x=0x8800;
        minigame_active=0;minigame_change_room(0x5f);house_talk_latch=1;
    }
    return TRUE;
}
