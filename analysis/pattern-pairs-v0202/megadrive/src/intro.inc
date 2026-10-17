/* Native translation of the pre-title story, Z80 0C98..10BE.
 * All graphics, text, relative sprite frames and color sequences come from ROM. */
extern const u8 intro_bank6[],intro_fixed[],intro_mono_font[],intro_symbols_rle[];
extern const u8 intro_fire_colors[],intro_lightning_colors[];
static u16 intro_scene,intro_counter,intro_abort;
static volatile u16 intro_line,intro_running;
static u16 intro_actor_state[16],intro_actor_pose[16];
static const u8 *intro_actor_templates;

static const u8 *intro_address(u16 address) { return intro_fixed+address-0x0f95; }
static void intro_init_actors(u16 address)
{
    intro_actor_templates=intro_address(address);intro_counter=0;
    memset(intro_actor_state,0,sizeof(intro_actor_state));
    memset(intro_actor_pose,0,sizeof(intro_actor_pose));
}

static void intro_tick(void)
{
    u16 clock=(u8)vtimer,n,count=0;
    if(intro_scene==1)
    {
        if(!(clock&7))
        {
            intro_counter=(intro_counter+1)%6;
            for(n=0;n<3;n++) sms_palette[1+n]=intro_fire_colors[intro_counter*3+n];
        }
    }
    else if(intro_scene>=2)
    {
        const u8 *p=intro_actor_templates,*colors;
        if(intro_scene==2) sms_palette[18]=intro_address(0x10bf)[clock&3];
        if(!(clock&3)) intro_counter=(intro_counter+1)&255;
        VDP_resetSprites();
        for(n=0;n<16 && p[0];n++,p+=6)
        {
            u16 descriptor=p[4]|((u16)p[5]<<8),pose=intro_actor_pose[n];
            if(!intro_actor_state[n] && intro_counter==p[2]) intro_actor_state[n]=1;
            if(!intro_actor_state[n]) continue;
            {
                const u8 *table=intro_address(descriptor)+pose*2;
                u16 address=table[0]|((u16)table[1]<<8);
                count=add_sms_sprite_frame(count,p[1],(s8)p[0],intro_address(address),0);
            }
            if(!(clock&3))
            {
                pose++;
                if(pose==p[3]) { pose=0;intro_actor_state[n]=0; }
                intro_actor_pose[n]=pose;
            }
        }
        if(count) VDP_setSpriteLink(count-1,0);
        /* 1061/108B builds DD40/DD80 after the frame wait. The source IRQ
         * uploads that buffer at 015E..016A on the following VBlank. */
        VDP_updateSprites(count,DMA_QUEUE);
        colors=intro_lightning_colors+(count?6+((clock>>1)&7)*3:0);
        for(n=0;n<3;n++) sms_palette[1+n]=colors[n];
        for(n=0;n<4;n++) { sms_palette[4+n]=colors[3];sms_palette[8+n]=colors[4]; }
    }
    set_palette(sms_palette);
}

static void intro_wait(u16 frames)
{
    while(frames-- && !intro_abort)
    {
        wait_frame();
        if(input&(BUTTON_A|BUTTON_B|BUTTON_C|BUTTON_START)) intro_abort=1;
        intro_tick();
    }
}

static void intro_upload_patterns(void)
{
    convert_patterns_range_fast(0,288);VDP_loadTileData(md_patterns,16,288,CPU);
}

static void intro_reveal(void)
{
    u16 mask=127;
    do
    {
        u16 row=0,chunk=0;
        u16 phase;
        u8 masks[4];
        u32 planes[4];
        u8 rotated=(u8)((mask<<2)|(mask>>6));
        for(phase=0;phase<4;phase++)
        {
            rotated=(u8)((rotated>>2)|(rotated<<6));
            masks[phase]=rotated;planes[phase]=plane_spread[rotated]<<3;
        }
        /* 0E8B..0E9D changes only plane 3, at 100 Z80 T-states/row.
         * The first visible slice starts at V-counter 112 (0F21) and ends
         * at line 192. Subsequent slices reserve time for the source IRQ.
         * These slices restore the five-frame pass cadence; exact per-row
         * IRQ contention/scanline equivalence still needs verification. */
        while(row<0x900)
        {
            u16 first=row;
            u16 count=chunk?((SYS_isPAL()?71364UL:59736UL)-3600)/100:
                ((192-112)*228)/100;
            count&=0xfffc;
            if(count>0x900-row) count=0x900-row;
            {
                u8 *sms=sms_vram+row*4+3;
                u32 *md=md_patterns+row;
                u16 groups=count>>2;
                while(groups--)
                {
                    sms[0]=masks[0];sms[4]=masks[1];sms[8]=masks[2];sms[12]=masks[3];
                    md[0]=(md[0]&0x77777777UL)|planes[0];
                    md[1]=(md[1]&0x77777777UL)|planes[1];
                    md[2]=(md[2]&0x77777777UL)|planes[2];
                    md[3]=(md[3]&0x77777777UL)|planes[3];
                    sms+=16;md+=4;
                }
                row+=count;
            }
            DMA_queueDma(DMA_VRAM,md_patterns+first,512+first*4,(row-first)*2,2);
            if(!chunk) intro_wait(1);
            else
            {
                /* 0F09 runs actor/palette behavior once per pass, not once
                 * per transfer slice. Music still runs in the VBlank IRQ. */
                wait_frame();
                if(input&(BUTTON_A|BUTTON_B|BUTTON_C|BUTTON_START)) { intro_abort=1;return; }
            }
            if(intro_abort) return;
            chunk++;
        }
        /* SRL 01 carries into one final iteration with mask zero. */
        if(!mask) break;
        mask>>=1;
    } while(!intro_abort);
}

static void intro_load_scene(u16 scene)
{
    u16 n,row,column;
    const u8 *src=intro_bank6+(scene==1?0x1d70:scene==2?0x2655:0x2f1f);
    intro_scene=0;VDP_resetSprites();VDP_updateSprites(0,CPU);
    for(n=0x3800;n<0x3b00;n+=2) { sms_vram[n]=0xfa;sms_vram[n+1]=9; }
    draw_map();intro_wait(1);
    for(n=0;n<16;n++) sms_palette[n]=n<4?*src++:0;
    set_palette(sms_palette);
    if(scene<3)
    {
        src=decode_planes(src,sms_vram,4);
        decode_map(src,title_map);
    }
    else
    {
        src=decode_planes(src,scratch,1);
        /* Scene three contains 2304 monochrome rows per plane. */
        for(n=0;n<0x900;n++) sms_vram[n*4]=scratch[n];
        decode_planes(src,scratch,1);
        for(n=0;n<0x900;n++) sms_vram[n*4+1]=scratch[n];
        for(row=0;row<12;row++) for(column=0;column<24;column++)
        {
            n=row+column*12;title_map[(row*24+column)*2]=n;title_map[(row*24+column)*2+1]=n>>8;
        }
    }
    for(n=3;n<0x2400;n+=4) sms_vram[n]=255;
    intro_upload_patterns();
    for(row=0;row<12;row++) memcpy(sms_vram+0x3808+row*64,title_map+row*48,48);
    draw_map();intro_wait(1);
    if(scene==2) intro_init_actors(0x0f95);
    intro_scene=scene==3?0:scene;
    intro_reveal();
}

static void intro_fade(void)
{
    u16 step,n;bool changed;
    intro_scene=0;
    for(step=1;step<=16;step*=4)
    {
        do
        {
            changed=FALSE;
            for(n=0;n<16;n++) if(sms_palette[n]&(step*3)) { sms_palette[n]-=step;changed=TRUE; }
            if(changed) { set_palette(sms_palette);intro_wait(4); }
        } while(changed && !intro_abort);
    }
}

static void intro_start_third_animation(void)
{
    u16 n,mask=1;
    decode_planes(intro_bank6+0x3595,scratch,2);
    do
    {
        u8 rotated=mask;
        for(n=0;n<0x600;n++)
        {
            sms_vram[n*4+2]=scratch[n]&rotated;
            if(n&1) rotated=(u8)((rotated<<2)|(rotated>>6));
        }
        intro_upload_patterns();intro_wait(1);mask=(mask<<1)|1;
    } while(mask<256 && !intro_abort);
    intro_init_actors(0x0fe4);intro_scene=3;
}

static void intro_scroll_text(void)
{
    u16 n;
    for(n=0;n<0x2c0;n++) sms_vram[0x3b00+n]=sms_vram[0x3b40+n];
    for(n=0x3dc0;n<0x3e00;n+=2) { sms_vram[n]=0xfa;sms_vram[n+1]=1; }
}

static void intro_sequence(void)
{
    u16 n,destination;const u8 *text=intro_bank6+0x39ce,*patch=intro_address(0x10c3);
    intro_scene=intro_abort=intro_timer=intro_counter=intro_line=0;intro_running=1;
    title_phase=FALSE;VDP_setEnable(FALSE);map_origin=0x3800;
    memset(sms_vram,0,sizeof(sms_vram));
    decode_planes(number_font_rle,sms_vram+0x2600,4);
    load_mono(0x2820,intro_mono_font,256,3,TRUE);
    decode_planes(intro_symbols_rle,sms_vram+0x3400,4);
    for(n=0;n<7;n++)
    {
        u16 address=(patch[0]|((u16)patch[1]<<8))&0x3fff;patch+=2;
        while(*patch) { load_mono(address,intro_mono_font+(*patch++-65)*8,8,3,TRUE);address+=32; }
        patch++;
    }
    for(n=0x3800;n<0x3e00;n+=2) { sms_vram[n]=0xfa;sms_vram[n+1]=1; }
    for(n=0;n<16;n++) { sms_palette[n]=0;sms_palette[16+n]=menu_palette[n]; }
    sms_palette[22]=0x2a;sms_palette[23]=0;sms_palette[31]=2;
    convert_patterns_range_fast(0,512);VDP_loadTileData(md_patterns,16,512,CPU);
    set_palette(sms_palette);draw_map();VDP_setEnable(TRUE);
    sound_music(0x85);
    intro_load_scene(1);
    while(*text && !intro_abort)
    {
        do { intro_wait(1); } while(intro_timer && !intro_abort);
        intro_timer=90;intro_scroll_text();intro_wait(2);draw_map();
        intro_scroll_text();destination=0x3dc2;
        while(*text!=255 && *text) { sms_vram[destination++]=*text++;sms_vram[destination++]=9; }
        if(*text==255) text++;
        intro_line++;intro_wait(2);draw_map();
        if(intro_line==18 || intro_line==39) intro_fade();
        else if(intro_line==19) intro_load_scene(2);
        else if(intro_line==40) intro_load_scene(3);
        else if(intro_line==44) intro_start_third_animation();
    }
    /* 0D10 checks the terminating zero only after the final 90-IRQ timer. */
    while(intro_timer && !intro_abort) intro_wait(1);
    VDP_resetSprites();VDP_updateSprites(0,CPU);
    /* A press skips only the intro; release before accepting a title press. */
    while(input&(BUTTON_A|BUTTON_B|BUTTON_C|BUTTON_START)) wait_frame();
    intro_running=0;title_phase=TRUE;title_requested=FALSE;
}
