/* 7685/7700: free and paid nights; restore life, preserve magic. */
extern const u8 healer_portrait_rle[],healer_portrait_map[];
extern const u8 healer_free_prompt[],healer_paid_prompt[],healer_decline[],healer_done[];
extern const u8 healer_prices[][2];
extern const u16 healer_prices_count;
static volatile u16 healer_phase;
static void show_healer_service(void)
{
    u16 n,cost=0,colors[32],black[32]={0};bool accepted;
    for(n=0;n<healer_prices_count;n++) if(house_return_room==healer_prices[n][0]) { cost=healer_prices[n][1];break; }
    save_service_phase=7;healer_phase=1;game_state=22;house_dialogue_active=1;
    service_begin(healer_portrait_rle,healer_portrait_map);
    dialogue_number=cost;
    render_dialogue_text(cost?healer_paid_prompt:healer_free_prompt,TRUE);
    accepted=save_confirm_yes_no();
    if(accepted && cost)
    {
        if(hero_gold<cost)
        {
            render_dialogue_text(merchant_poor,TRUE);wait_dialog_continue();accepted=FALSE;
        }
        else
        {
            render_dialogue_text(merchant_thanks,TRUE);
            /* 74A8/61E7: paid nights use the same per-unit deduction as shops. */
            for(n=0;n<cost;n++)
            {
                hero_gold--;sound_effect(0x95);merchant_number(0x3dd0,hero_gold);draw_map();wait_frame();wait_frame();
            }
            hero_gold_drawn=hero_gold;hero_gold_pending=FALSE;
        }
    }
    if(accepted)
    {
        u32 fade_started=vtimer,night_started;
        healer_phase=2;
        memcpy(colors,sms_palette,sizeof(colors));
        /* 0B12 intentionally fades to black for the night, then waits 60 IRQs. */
        fade_world_palette(black,FALSE);
        /* Free-service palette, source 76C3 -> 0B24: 19 NTSC frames,
         * 18 PAL. Preserve its control-work interval after the fast fade. */
        if(!cost && !SYS_isPAL()) while(vtimer-fade_started<19) wait_frame();
        VDP_setEnable(FALSE);
        night_started=vtimer;
        for(n=0;n<60;n++) { VDP_waitVInt();input=JOY_readJoypad(JOY_1); }
        hero_health=hero_max_health;prepare_hero_health_bar(TRUE);
        for(n=0x3b40;n<0x3d00;n+=2) { sms_vram[n]=0xff;sms_vram[n+1]=0x18; }
        VDP_resetSprites();VDP_updateSprites(0,CPU);draw_map();
        /* 60 IRQs plus the source HUD/map restore: 62 displayed-off frames. */
        if(!cost) while(vtimer-night_started<62) wait_frame();
        VDP_setEnable(TRUE);fade_world_palette(colors,TRUE);
        healer_phase=3;render_dialogue_text(healer_done,TRUE);
    }
    else { healer_phase=3;render_dialogue_text(healer_decline,TRUE); }
    wait_dialog_continue();service_finish();healer_phase=0;
}
