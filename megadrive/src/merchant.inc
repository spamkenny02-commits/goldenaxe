/* 7452: native translation of normal goods, potion-only and magic merchants. */
extern const u8 merchant_portrait_rle[],merchant_portrait_map[];
extern const u8 merchant_prompt[],merchant_thanks[],merchant_poor[],merchant_owned[],merchant_full[],merchant_better[];
extern const u8 merchant_potion_prompt[],merchant_magic_prompt[],merchant_extra_icons[];
extern const u8 merchant_goods[6][3][3],merchant_towns[][3],merchant_magic_counts[],merchant_magic_prices[];
extern const u8 * const merchant_labels[],* const merchant_group_prompts[];
extern const u16 merchant_towns_count,merchant_potion_label;
static volatile u16 merchant_selection,merchant_phase,merchant_mode;

static void merchant_number(u16 address,u16 number)
{
    u16 n;
    for(n=0;n<3;n++)
    {
        sms_vram[address+n*2]=0xf0+(n==0?number/100:n==1?(number/10)%10:number%10);
        sms_vram[address+n*2+1]=0x18;
    }
}

/* 74A8/61E7: no text for price zero; otherwise one unit per two waits. */
static bool merchant_pay(u16 cost)
{
    u16 count;
    if(!cost) return TRUE;
    if(hero_gold<cost) { render_dialogue_text(merchant_poor,TRUE);return FALSE; }
    render_dialogue_text(merchant_thanks,TRUE);
    for(count=0;count<cost;count++)
    {
        u16 n;
        hero_gold--;sound_effect(0x95);merchant_number(0x3dd0,hero_gold); /* 61E7/1E41 */
        for(n=0;n<3;n++) md_map[23*32+8+n]=TILE_ATTR_FULL(PAL1,1,0,0,16+sms_vram[0x3dd0+n*2]);
        VDP_setTileMapDataRect(BG_A,md_map+23*32+8,8,25,3,1,3,CPU);
        wait_frame();wait_frame();
    }
    hero_gold_drawn=hero_gold;hero_gold_pending=FALSE;return TRUE;
}

/* 74C6..752D; return TRUE only after a successful purchase. */
static bool merchant_buy(u16 item,u16 cost)
{
    u16 n;
    const u8 *refusal=0;
    if(item==0x19 && hero_shield_level>=2) refusal=hero_shield_level==2?merchant_owned:merchant_better;
    else if(item==0x1b && hero_health==hero_max_health) refusal=merchant_full;
    else if(item==0x1e && hero_keys>=99) refusal=merchant_full;
    else if((item==6 && hero_items[2]) || (item==13 && hero_items[9]) || (item==12 && hero_items[8])) refusal=merchant_owned;
    if(refusal) { render_dialogue_text(refusal,TRUE);return FALSE; }
    if(!merchant_pay(cost)) return FALSE;
    if(item==0x19) hero_shield_level=2;
    else if(item==0x1b)
    {
        while(hero_health<hero_max_health)
        {
            hero_health++;prepare_hero_health_bar(TRUE);
            VDP_setTileMapDataRect(BG_A,md_map+21*32+15,15,23,hero_max_health>>3,1,hero_max_health>>3,CPU);
            wait_frame();wait_frame();
        }
    }
    else if(item==0x1e) hero_keys++;
    else { n=item==6?2:item==13?9:8;hero_items[n]=1; }
    return TRUE;
}

static void merchant_load_icon(u16 tile,u16 item)
{
    u16 address=tile*32;
    if(item==0x1e)
    {
        /* 2B1D: key reads permanent HUD tiles196/197, blank right tiles. */
        memcpy(sms_vram+address,sms_vram+0x32c0,32);memset(sms_vram+address+32,0,32);
        memcpy(sms_vram+address+64,sms_vram+0x32e0,32);memset(sms_vram+address+96,0,32);
    }
    else memcpy(sms_vram+address,item>=27?merchant_extra_icons+(item-27)*128:inventory_icons+item*128,128);
}

static void show_merchant_service(void)
{
    u16 n,p,group=0,potion_cost=0,previous,pressed,count,item,cost,magic;
    const u8 *prompt;
    merchant_mode=65535;
    for(n=0;n<merchant_towns_count;n++) if(house_return_room==merchant_towns[n][0])
    {
        merchant_mode=merchant_towns[n][1];group=merchant_towns[n][2];potion_cost=group;break;
    }
    if(merchant_mode==65535) return;
    count=merchant_mode==1?1:3;
    prompt=merchant_mode==0?merchant_group_prompts[group]:merchant_mode==1?merchant_potion_prompt:merchant_magic_prompt;
    save_service_phase=6;merchant_phase=1;game_state=22;house_dialogue_active=1;
    service_begin(merchant_portrait_rle,merchant_portrait_map);
    /* 78CE calls 779B before building the goods and displaying them at 7719. */
    render_dialogue_text(prompt,TRUE);
    for(n=0;n<count;n++)
    {
        if(merchant_mode==2)
        {
            merchant_load_icon(0x90,28);save_icon(0x385a+n*0xc0,0x90);
            for(p=0;p<merchant_magic_counts[n];p++)
            {
                sms_vram[0x3860+n*0xc0+p*2]=0x90;sms_vram[0x3861+n*0xc0+p*2]=0x19;
            }
            cost=merchant_magic_prices[n];
        }
        else
        {
            item=merchant_mode==1?12:merchant_goods[group][n][0];
            cost=merchant_mode==1?potion_cost:merchant_goods[group][n][1];
            merchant_load_icon(0x90+n*4,item);save_icon(0x385a+n*0xc0,0x90+n*4);
            save_draw_text(0x3860+n*0xc0,merchant_labels[merchant_mode==1?merchant_potion_label:merchant_goods[group][n][2]]);
        }
        merchant_number(0x38b4+n*0xc0,cost);save_draw_text(0x38ba+n*0xc0,(const u8 *)"C");
    }
    save_icon(0x385a+count*0xc0,0xa0);
    convert_patterns_range(144,12);VDP_loadTileData(md_patterns+144*8,160,12,DMA_QUEUE);
    map_queue=TRUE;draw_map();wait_frame();map_queue=FALSE;
    merchant_selection=0;previous=input;
    while(TRUE)
    {
        save_slot_selection=merchant_selection;save_update_cursor();wait_frame();
        pressed=input&~previous;previous=input;
        n=merchant_selection;
        if((pressed&BUTTON_UP) && merchant_selection) merchant_selection--;
        if((pressed&BUTTON_DOWN) && merchant_selection<count) merchant_selection++;
        if(n!=merchant_selection) sound_effect(0x95);
        if((pressed&BUTTON_B) && !(pressed&BUTTON_C)) { merchant_selection=count;break; }
        if(!(pressed&BUTTON_C)) continue;
        sound_effect(0xab); /* 776C */
        if(merchant_selection==count) break;
        merchant_phase=2;
        if(merchant_mode==2)
        {
            if(hero_magic==hero_max_magic)
            {
                render_dialogue_text(merchant_full,TRUE);wait_dialog_end();break;
            }
            if(merchant_pay(merchant_magic_prices[merchant_selection]))
            {
                magic=hero_magic+merchant_magic_counts[merchant_selection]*8;
                hero_magic=magic>hero_max_magic?hero_max_magic:magic;
                /* 1E4E updates the whole magic HUD after buying. */
                for(n=0;n<(hero_max_magic>>3);n++)
                {
                    sms_vram[0x3dde + n*2]=hero_magic>=(n+1)*8?0x90:0x91;sms_vram[0x3ddf+n*2]=0x19;
                }
                hero_magic_drawn=hero_magic;hero_magic_pending=FALSE;draw_map();
            }
        }
        else
        {
            item=merchant_mode==1?12:merchant_goods[group][merchant_selection][0];
            cost=merchant_mode==1?potion_cost:merchant_goods[group][merchant_selection][1];
            if(merchant_buy(item,cost) && merchant_mode==1) break;
        }
        merchant_phase=1;previous=input;
    }
    VDP_resetSprites();VDP_updateSprites(0,CPU);service_finish();merchant_phase=0;
}
