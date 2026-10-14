/* Native translation of 7390/73E5/6093/7716/782C. SRAM offsets preserve
 * the SMS slot spacing and 592-byte payload; no source CPU is executed. */
extern const u8 save_font_rle[],save_portrait_rle[],save_portrait_map[];
extern const u8 save_text_charset[],save_cursor_frame[],save_colors[];
extern const u8 save_prompt[],save_select_text[],save_done_text[],save_continue_text[],save_decline_text[];
static u16 save_last_slot,save_checkpoint_room,save_runtime_checkpoint;
static volatile u16 save_slot_selection,save_yes;

static void save_init(void)
{
    SRAM_enableRO();save_last_slot=SRAM_readByte(0x30);SRAM_disable();
    if(save_last_slot>3) save_last_slot=0;
}

static void save_reset_new_game(void)
{
    memset(game_save_state,0,sizeof(game_save_state));
    /* 1C97 initializes the persistent visited/room bytes to FF. */
    memset(game_save_state+0x150,255,256);save_checkpoint_room=save_runtime_checkpoint=0x95;
    /* Initial 95 and the reached village 94 have empty enemy masks. */
    game_save_state[0x150+0x95]=0;
}

/* 18E9: slot zero becomes the high bit, slot seven the low bit. */
static void save_room_actor_mask(u16 number)
{
    u16 slot;u8 mask=0;
    for(slot=0;slot<8;slot++) mask=(mask<<1)|(world_actor_state[slot*0x30]!=0);
    game_save_state[0x150+(number&255)]=mask;
}
static u8 saved_room_actor_mask(u16 number)
{
    return game_save_state[0x150+(number&255)];
}

static void save_word(u16 offset,u16 value)
{
    game_save_state[offset]=value;game_save_state[offset+1]=value>>8;
}

static void serialize_game_save(void)
{
    u16 n;
    memset(game_save_state,0,9);memcpy(game_save_state,character_name,strlen(character_name));
    save_word(9,room_id);save_word(11,house_return_room);
    game_save_state[13]=house_return_y>>8;game_save_state[14]=house_return_x>>8;
    save_word(16,save_checkpoint_room);save_word(18,house_return_room);
    game_save_state[0x16]=hero_fire_charge;
    game_save_state[0x29]=hero_health;game_save_state[0x2a]=hero_max_health;
    game_save_state[0x2b]=hero_magic;game_save_state[0x2c]=hero_max_magic;
    game_save_state[0x2d]=hero_gold;game_save_state[0x2e]=hero_keys;game_save_state[0x2f]=hero_selected_item;
    for(n=0;n<17;n++) game_save_state[0x30+n]=hero_items[n];
    game_save_state[0x30]=hero_basic_level;game_save_state[0x31]=hero_weapon_level;
    game_save_state[0x41]=hero_armor_level;game_save_state[0x42]=hero_shield_level;
}

static void save_write_slot(u16 slot)
{
    u16 n;u32 base=0x400+slot*0x400;
    serialize_game_save();SRAM_enable();
    for(n=0;n<sizeof(game_save_state);n++) SRAM_writeByte(base+n,game_save_state[n]);
    save_runtime_checkpoint=house_return_room;
    save_last_slot=slot+1;SRAM_writeByte(0x30,save_last_slot);SRAM_disable();
}

/* 0818: uppercase/number font descriptor B008, 80-byte charset. */
static void save_draw_text(u16 address,const u8 *text)
{
    u16 line=address,index;
    while(*text)
    {
        u8 value=*text++;
        if(value==255) { line+=64;address=line;continue; }
        for(index=80;index>0;index--) if(save_text_charset[index-1]==value) break;
        sms_vram[address++]=(0xb0+index-1)&255;sms_vram[address++]=8;
    }
}

static void save_icon(u16 address,u16 tile)
{
    u16 row,col;
    for(row=0;row<2;row++) for(col=0;col<2;col++)
    {
        sms_vram[address+row*64+col*2]=tile+row*2+col;
        sms_vram[address+row*64+col*2+1]=8;
    }
}

static void save_draw_slots(u16 icon)
{
    u16 slot,n,length;u8 label[11]="JEU NO. 1 ",name[9],aligned[9];
    for(slot=0;slot<3;slot++)
    {
        save_icon(0x385a+slot*0xc0,icon);label[8]='1'+slot;
        save_draw_text(0x3860+slot*0xc0,label);
        SRAM_enableRO();
        for(n=0;n<8;n++) name[n]=SRAM_readByte(0x400+slot*0x400+n);
        SRAM_disable();name[8]=0;
        /* Empty slots (00 or erased FF) remain blank; valid names use the font. */
        if(name[0] && name[0]!=255)
        {
            for(length=0;length<8 && name[length];length++) {}
            memset(aligned,' ',8-length);memcpy(aligned+8-length,name,length);aligned[8]=0;
            save_draw_text(0x38ac+slot*0xc0,aligned);
        }
    }
    save_icon(0x3a9a,0xa0);draw_map();
}

static void save_update_cursor(void)
{
    u16 count;
    VDP_resetSprites();count=add_sms_sprite_frame(0,104,8+save_slot_selection*24,save_cursor_frame,0);
    if(count) VDP_setSpriteLink(count-1,0);
    VDP_updateSprites(count,CPU);
}

static bool save_confirm_yes_no(void)
{
    u16 previous=input,pressed,n;save_yes=1;
    draw_frame(0x3bf2,6,4);save_draw_text(0x3c36,(const u8 *)"OUI\xffNON");
    while(TRUE)
    {
        for(n=0;n<2;n++)
        {
            u16 word=((n==0)==(save_yes!=0))?0x1982:0x18ff;
            sms_vram[0x3c34+n*64]=word;sms_vram[0x3c35+n*64]=word>>8;
        }
        draw_map();wait_frame();pressed=input&~previous;previous=input;
        if(pressed&BUTTON_C) { sound_effect(0xab);return save_yes!=0; }
        /* 6123: confirmation wins; Up changes No to Yes before examining Down. */
        n=save_yes;
        if((pressed&BUTTON_UP) && !save_yes) save_yes=1;
        else if(pressed&(BUTTON_DOWN|BUTTON_B)) save_yes=0;
        if(n!=save_yes) sound_effect(0x95);
    }
}

static void service_begin(const u8 *portrait_rle,const u8 *portrait_map)
{
    u16 n;
    /* Hide the room before reusing its tiles (77B7/7809); retain the HUD. */
    for(n=0x3800;n<0x3d00;n+=2) { sms_vram[n]=0xff;sms_vram[n+1]=0x18; }
    VDP_resetSprites();VDP_setSpriteFull(0,0,0,SPRITE_SIZE(1,1),0,0);
    VDP_updateSprites(1,DMA_QUEUE);map_queue=TRUE;draw_map();wait_frame();map_queue=FALSE;
    decode_planes(portrait_rle,sms_vram,4);
    decode_planes(save_font_rle,sms_vram+0x1400,4);
    load_mono(0x1600,normal_font,256,3,TRUE);
    load_mono(0x3e00,inventory_cursor_bitmap,40,3,FALSE);
    draw_frame(0x3844,10,10);
    for(n=0;n<64;n++)
    {
        u16 address=0x3886+(n/8)*64+(n%8)*2;
        sms_vram[address]=portrait_map[n*2];sms_vram[address+1]=portrait_map[n*2+1];
    }
    for(n=0;n<8;n++) sms_palette[n]=save_colors[n];
    /* 77F5: color plane 2 initially hides the 64 portrait tiles. */
    for(n=2;n<0x800;n+=4) sms_vram[n]=255;
    convert_patterns_range(0,64);convert_patterns_range(160,48);convert_patterns_range(496,5);
    VDP_loadTileData(md_patterns,16,64,DMA_QUEUE);
    VDP_loadTileData(md_patterns+160*8,176,48,DMA_QUEUE);
    VDP_loadTileData(md_patterns+496*8,512,5,DMA_QUEUE);
    /* The room is already hidden, so changing its unused palette is safe. */
    set_world_palette();map_queue=TRUE;draw_map();wait_frame();map_queue=FALSE;
    /* 780C..782B: rotated plane masks 7F,3F,1F,0F,07,03,01,00. */
    for(n=0x7f;;n>>=1)
    {
        u16 offset;u8 rotated=n;
        for(offset=2;offset<0x800;offset+=4)
        {
            sms_vram[offset]=rotated;rotated=(u8)((rotated>>2)|(rotated<<6));
        }
        convert_patterns_range(0,64);VDP_loadTileData(md_patterns,16,64,DMA_QUEUE);wait_frame();
        if(!n) break;
    }
}

static void service_finish(void)
{
    u16 n;
    /* Keep the HUD visible while replacing the service portrait with the room. */
    for(n=0x3800;n<0x3d00;n+=2) { sms_vram[n]=0xff;sms_vram[n+1]=0x08; }
    map_queue=TRUE;draw_map();wait_frame();map_queue=FALSE;
    decode_planes(world_hud_font_rle,sms_vram+0x1a00,4);
    decode_planes(number_font_rle,sms_vram+0x1e00,4);
    decode_planes(world_hud_patterns_rle,sms_vram+0x3600,4);
    load_house_room(room_id,1);house_talk_latch=1;house_dialogue_active=0;
    save_service_phase=0;world_previous_input=input;
}

static void show_merchant_service(void);
static void show_healer_service(void);

static void show_save_service(void)
{
    u16 previous,pressed;save_service_phase=1;game_state=22;house_dialogue_active=1;
    service_begin(save_portrait_rle,save_portrait_map);
    save_draw_slots(0xa4);VDP_setEnable(TRUE);
    render_dialogue_text(save_prompt,TRUE);
    if(save_confirm_yes_no())
    {
        save_service_phase=2;render_dialogue_text(save_select_text,TRUE);
        save_slot_selection=save_last_slot?save_last_slot-1:0;previous=input;
        while(TRUE)
        {
            u16 old_slot=save_slot_selection;
            save_update_cursor();wait_frame();pressed=input&~previous;previous=input;
            if((pressed&BUTTON_UP) && save_slot_selection) save_slot_selection--;
            if((pressed&BUTTON_DOWN) && save_slot_selection<3) save_slot_selection++;
            if(old_slot!=save_slot_selection) sound_effect(0x95);
            if((pressed&BUTTON_B) && !(pressed&BUTTON_C)) { save_slot_selection=3;break; }
            if(pressed&BUTTON_C) { sound_effect(0xab);break; }
        }
        if(save_slot_selection<3)
        {
            save_write_slot(save_slot_selection);save_draw_slots(0xa4);save_service_phase=3;
            VDP_resetSprites();VDP_updateSprites(0,CPU);
            render_dialogue_text(save_done_text,TRUE);wait_dialog_continue();
        }
    }
    else
    {
        save_service_phase=5;render_dialogue_text(save_decline_text,TRUE);wait_dialog_continue();
    }
    service_finish();
}

static void check_house_service(u16 old_x,u16 old_y)
{
    extern const u8 healer_nodes[][3],healer_prices[][2];
    extern const u16 healer_nodes_count,healer_prices_count;
    extern const u8 merchant_nodes[][3];
    extern const u16 merchant_nodes_count;
    extern const u8 save_nodes[][3];
    extern const u16 save_nodes_count;
    u16 x=hero_x>>8,y=hero_y>>8,n,p;
    if(world_graphics_class==1 && !hero_direction && x==old_x && y==old_y &&
       !((x|y)&7) && (input&BUTTON_UP) && !house_talk_latch)
    {
        for(n=0;n<healer_nodes_count;n++)
            if(room_id==healer_nodes[n][0] && x==healer_nodes[n][1] && y==healer_nodes[n][2])
                for(p=0;p<healer_prices_count;p++)
                    if(house_return_room==healer_prices[p][0]) { show_healer_service();return; }
        for(n=0;n<merchant_nodes_count;n++)
            if(room_id==merchant_nodes[n][0] && x==merchant_nodes[n][1] && y==merchant_nodes[n][2])
            { show_merchant_service();return; }
        for(n=0;n<save_nodes_count;n++)
            if(room_id==save_nodes[n][0] && x==save_nodes[n][1] && y==save_nodes[n][2])
            { show_save_service();return; }
    }
}


/* 15F6: restore the source-layout record; gameplay loads its checkpoint room. */
static bool save_load_slot(u16 slot)
{
    u16 n;u32 base=0x400+slot*0x400;u8 first;
    SRAM_enableRO();first=SRAM_readByte(base);
    if(!first || first==255) { SRAM_disable();return FALSE; }
    for(n=0;n<sizeof(game_save_state);n++) game_save_state[n]=SRAM_readByte(base+n);
    SRAM_disable();
    for(n=0;n<8;n++) character_name[n]=game_save_state[n];character_name[8]=0;
    save_resume_health=game_save_state[0x29];hero_max_health=game_save_state[0x2a];
    hero_magic=game_save_state[0x2b];hero_max_magic=game_save_state[0x2c];
    hero_gold=game_save_state[0x2d];hero_keys=game_save_state[0x2e];hero_selected_item=game_save_state[0x2f];
    for(n=0;n<17;n++) hero_items[n]=game_save_state[0x30+n];
    hero_armor_level=game_save_state[0x41];hero_basic_level=game_save_state[0x30];hero_shield_level=game_save_state[0x42];
    hero_weapon_level=hero_items[1];hero_fire_charge=game_save_state[0x16];hero_attack_speed=hero_items[14];
    save_resume_room=game_save_state[0x12]|((u16)game_save_state[0x13]<<8);
    save_checkpoint_room=save_runtime_checkpoint=save_resume_room;save_last_slot=slot+1;
    house_return_room=game_save_state[11]|((u16)game_save_state[12]<<8);
    house_return_y=(u16)game_save_state[13]<<8;house_return_x=(u16)game_save_state[14]<<8;
    save_resume_pending=TRUE;return TRUE;
}

static bool show_continue_selection(void)
{
    u16 n,previous,pressed;save_service_phase=4;
    VDP_setEnable(FALSE);VDP_resetSprites();VDP_updateSprites(0,CPU);
    for(n=0x3800;n<0x3e00;n+=2) { sms_vram[n]=0xff;sms_vram[n+1]=0x18; }
    decode_planes(save_font_rle,sms_vram+0x1400,4);
    load_mono(0x1600,normal_font,256,3,TRUE);
    load_mono(0x3e00,inventory_cursor_bitmap,40,3,FALSE);
    convert_patterns(512);VDP_loadTileData(md_patterns,16,512,CPU);
    save_draw_slots(0xa8);save_slot_selection=save_last_slot?save_last_slot-1:3;
    draw_text(0x3bce,save_continue_text);draw_map();VDP_setEnable(TRUE);previous=input;
    while(TRUE)
    {
        u16 old_slot=save_slot_selection;
        save_update_cursor();wait_frame();pressed=input&~previous;previous=input;
        if((pressed&BUTTON_UP) && save_slot_selection) save_slot_selection--;
        if((pressed&BUTTON_DOWN) && save_slot_selection<3) save_slot_selection++;
        if(old_slot!=save_slot_selection) sound_effect(0x95);
        if(pressed&BUTTON_B) break;
        if(pressed&BUTTON_C)
        {
            sound_effect(0xab);
            if(save_slot_selection==3) break;
            if(save_load_slot(save_slot_selection)) { save_service_phase=0;return TRUE; }
        }
    }
    save_service_phase=0;return FALSE;
}


/* 2614: death Continue uses C0C2, including a newly written village save. */
static void save_prepare_checkpoint_resume(void)
{
    if(room_id>=256)
    {
        save_resume_room=game_save_state[0x14]|((u16)game_save_state[0x15]<<8);
        save_resume_health=24;save_resume_pending=TRUE;
        memset(game_save_state+0x150,255,256);
        return;
    }
    save_checkpoint_room=save_runtime_checkpoint;
    if(save_runtime_checkpoint!=0x95)
    {
        save_resume_room=save_runtime_checkpoint;save_resume_health=24;save_resume_pending=TRUE;
    }
}
