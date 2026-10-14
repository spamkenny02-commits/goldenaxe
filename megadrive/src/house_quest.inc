/* 61F4/621E/62A9 and623F quest-giver dispatch, before modal presentation. */
extern const u8 house_quest_text[],house_quest_text_index[],house_quest_labels[];
extern const u16 house_quest_text_pcs[],house_quest_text_count,house_quest_label_index[];
static u16 house_quest_item,house_quest_text_pc;
static void house_quest_effect(u16 entry)
{
    bool magic=hero_items[4]!=0;
    switch(entry)
    {
        case 0x6301:if(magic && hero_armor_level<2) { game_save_state[15]=0;hero_armor_level=2;house_quest_item=22; }break;
        case 0x640b:if(magic && hero_max_health>=56 && hero_basic_level<2) { hero_basic_level=hero_items[0]=2;house_quest_item=2; }break;
        case 0x6424:if(magic && !hero_items[8]) { hero_items[8]=1;house_quest_item=12; }break;
        case 0x6438:if(magic && hero_armor_level<3) { game_save_state[15]=0;hero_armor_level=3;house_quest_item=23; }break;
        case 0x6451:if(magic) { hero_basic_level=hero_items[0]=3;house_quest_item=3; }break;
        case 0x645e:if(game_save_state[0x24]&128) { hero_shield_level=3;house_quest_item=26; }break;
        case 0x646d:if(!hero_items[2]) { hero_items[2]=1;house_quest_item=6; }else house_quest_text_pc=0x90bf;break;
        case 0x6482:if(!hero_items[8]) { hero_items[8]=1;house_quest_item=12; }else house_quest_text_pc=0x905b;break;
        case 0x625b:if(hero_armor_level<2) house_quest_text_pc=0x8e94;break;
        case 0x6263:house_quest_text_pc=hero_max_health>=56?0x8e94:0x8ed9;break;
        case 0x6287:house_quest_text_pc=hero_items[8]?0x8bea:0x8fe3;break;
        case 0x6299:if(hero_armor_level<3) house_quest_text_pc=0x8e94;break;
        case 0x62a1:if(hero_basic_level<3) house_quest_text_pc=0x8e94;break;
    }
}
static void house_quest_choose(u16 room,u16 outside,u16 coordinate,u8 flags,const u8 *cells)
{
    static const u8 towns[]={0x92,0x50,0x27,0xb1,0x6a};
    static const u16 gifts[]={0x6424,0x640b,0x6301,0x6438,0x6451};
    static const u16 hints[]={0x6287,0x6263,0x625b,0x6299,0x62a1};
    u16 n,cell=(((hero_y>>8)-16)&240)|((hero_x>>12)&15);
    house_quest_item=house_quest_text_pc=0;
    if((flags&0x77)!=0x14) return;
    if(room==9 && coordinate==0x1e0)
    { if(cells[0x2a]!=0x31) house_quest_text_pc=(game_save_state[0x24]&128)?0xac1e:0xa52f;return; }
    if(room==0x4f && coordinate==0x25c)
    {
        if(cells[0x37]==0x31) return;
        if(!hero_items[4]) { house_quest_text_pc=0x8e5c;return; }
        for(n=0;n<5;n++) if((outside&255)==towns[n]) { house_quest_effect(hints[n]);return; }
        return;
    }
    if(!((room==9 && coordinate==0x1e4) || (room==15 && coordinate==0x1d4) || (room==0x4f && coordinate==0x258)) || cell>=160 || cells[cell]==0x31) return;
    if(room==0x4f)
    { if(!hero_items[4]) return;for(n=0;n<5;n++) if((outside&255)==towns[n]) { house_quest_effect(gifts[n]);return; } }
    else if((outside&255)==0x4c) house_quest_effect(0x645e);
    else if((outside&255)==0xc7) house_quest_effect(0x6482);
    else if((outside&255)==0x55) house_quest_effect(0x646d);
}
static const u8 *house_quest_dialogue(u16 pc)
{
    u16 n;
    for(n=0;n<house_quest_text_count;n++) if(house_quest_text_pcs[n]==pc)
        return house_quest_text+(house_quest_text_index[n*2]|((u16)house_quest_text_index[n*2+1]<<8));
    return NULL;
}
static bool check_house_quest(u16 old_x,u16 old_y,u8 flags)
{
    u16 coordinate;
    if(world_graphics_class!=1 || house_talk_latch || hero_x>>8!=old_x || hero_y>>8!=old_y) return FALSE;
    coordinate=(((u8)(old_y-12)&248)<<3)+(((u8)(old_x-12)>>2)&62)+126;
    house_quest_choose(room_id,house_return_room,coordinate,flags,scratch+0x800);
    if(house_quest_item)
    {
        u16 item=house_quest_item;house_dialogue_active=1;
        /* 631A:193D marks the outside town's class1 flag,then1A7C
         * transforms the room before the reward window backs it up. */
        game_save_state[0x50+(house_return_room&255)]|=2;
        prepare_room_cells(room_id);build_room_map(sms_vram+0x3800,world_new_md);
        show_item_reward_text(item,0,house_quest_labels+house_quest_label_index[item]);
        house_dialogue_active=0;house_talk_latch=1;world_previous_input=input;return TRUE;
    }
    if(house_quest_text_pc)
    {
        const u8 *text=house_quest_dialogue(house_quest_text_pc);
        if(!text) return FALSE;
        house_dialogue_active=1;house_dialogue_index=house_quest_text_pc;
        memcpy(house_dialogue_backup,sms_vram+0x2000,0x1040);
        memcpy(house_dialogue_backup+0x1040,sms_vram+0x1e00,0x200);
        memcpy(house_dialogue_backup+0x1240,sms_vram+0x3800,0x600);
        memcpy(house_dialogue_backup+0x1840,scratch,0x410);
        show_dialogue_text(text,TRUE);
        memcpy(sms_vram+0x2000,house_dialogue_backup,0x1040);
        memcpy(sms_vram+0x1e00,house_dialogue_backup+0x1040,0x200);
        memcpy(sms_vram+0x3800,house_dialogue_backup+0x1240,0x600);
        memcpy(scratch,house_dialogue_backup+0x1840,0x410);
        convert_patterns_range(256,130);VDP_loadTileData(md_patterns+256*8,272,130,CPU);
        convert_patterns_range(240,16);VDP_loadTileData(md_patterns+240*8,256,16,CPU);draw_map();
        house_dialogue_active=0;house_talk_latch=1;world_previous_input=input;return TRUE;
    }
    return FALSE;
}
