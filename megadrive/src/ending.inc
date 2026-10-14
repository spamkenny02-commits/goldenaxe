/* Native ending orchestration6EBE..70E6, using the real world simulation. */
#include "ending_credits.inc"
extern const u8 ending_held_bitmap[],ending_gem_bitmap[],actor_flying_sine[];
static u16 ending_stage,ending_counter,ending_sprites_pending;
static EndingCredits ending_credits;
static void ending_palette_wait(void)
{
    u16 n;
    if(!world_dungeon_dark && !(world_clock()&3))
        for(n=0;n<3;n++) sms_palette[13+n]=world_dungeon_color_cycle[((world_clock()>>2)&3)*3+n];
    set_world_palette();wait_frame();
    if(ending_sprites_pending) { update_hero_sprites();ending_sprites_pending=0; }
}
static void ending_wait(u16 count)
{ for(ending_counter=count;ending_counter;ending_counter--) ending_palette_wait(); }
static bool ending_objects_active(void)
{
    u16 n;
    if(world_spell_state[0]) return TRUE;
    for(n=0;n<7;n++) if(world_loot_state[n*48]) return TRUE;
    for(n=0;n<16;n++) if(world_actor_state[n*48]) return TRUE;
    return FALSE;
}
static void ending_world_tick(u16 buttons)
{
    u16 phase=world_clock();bool overflow=world_sms_sprite_overflow;
    wait_frame();update_hero_sprites_for_frame(phase,overflow);
    input=buttons;tick_world_simulation();prepare_hero_patterns();world_previous_input=input;
}
static void ending_center(u16 axis,u16 target)
{
    while(TRUE)
    {
        u16 phase=world_clock(),position;bool overflow=world_sms_sprite_overflow;
        ending_palette_wait();update_hero_sprites_for_frame(phase,overflow);
        position=(axis?hero_x:hero_y)>>8;if(position==target) break;
        input=axis?(position>=target?BUTTON_LEFT:BUTTON_RIGHT):(position>=target?BUTTON_UP:BUTTON_DOWN);
        tick_world_simulation();prepare_hero_patterns();world_previous_input=input;
    }
}
static u16 ending_map_top=65535,ending_virtual_top,ending_last_row[32];
static void ending_credit_map(void)
{
    u16 column,top=ending_credits.vscroll>>3;
    if(top!=ending_map_top)
    {
        const u8 *source=sms_vram+0x3800+((top+24)%28)*64;
        if(ending_map_top!=65535) ending_virtual_top++;
        for(column=0;column<32;column++)
        {
            u16 word=source[column*2]|((u16)source[column*2+1]<<8);
            ending_last_row[column]=TILE_ATTR_FULL((word>>11)&1,(word>>12)&1,(word>>10)&1,(word>>9)&1,16+(word&511));
        }
        VDP_setTileMapDataRect(BG_A,ending_last_row,0,(ending_virtual_top+26)&31,32,1,32,CPU);ending_map_top=top;
    }
    VDP_setVerticalScroll(BG_A,(ending_virtual_top*8+(ending_credits.vscroll&7))&255);
}
static void ending_emit_credit_row(u8 *line,u16 address)
{
    memcpy(sms_vram+(address&0x3fff),line,64);
}
static void run_ending(void)
{
    u16 n,tick;u8 line[64];u16 previous;
    ending_stage=1;hero_hurt=0;
    do { ending_world_tick(0); } while(ending_objects_active());
    ending_stage=2;world_boss_state=0;hero_casting=0;ending_wait(216);hero_state=0;
    ending_stage=3;ending_center(0,80);
    ending_stage=4;ending_center(1,128);
    sound_music(0x8d);
    memcpy(sms_vram+0x3780,ending_gem_bitmap,128);convert_patterns_range(444,4);VDP_loadTileData(md_patterns+444*8,460,4,CPU);
    for(n=0;n<48;n++)
    { memcpy(sms_vram+0x3e00+n*4,ending_held_bitmap+1+n*3,3);sms_vram[0x3e03+n*4]=0; }
    convert_patterns_range(496,6);VDP_loadTileData(md_patterns+496*8,512,6,CPU);hero_patterns_pending=FALSE;
    ending_hero_descriptor=0x8495;hero_animation=1;hero_flags|=1;ending_sprites_pending=1;
    memset(world_actor_state,0,9*48);
    for(n=0;n<9;n++)
    {
        u8 *e=world_actor_state+n*48;u16 phase=(n*16+128)&255;
        s16 dx=(s8)actor_flying_sine[(phase+64)&255]*80,dy=(s8)actor_flying_sine[phase]*80;
        e[0]=6;e[2]=gem_tile_table[n*2];e[8]=0xcd;e[9]=0x2a;
        e[0x13]=((hero_x>>8)+((u16)dx>>8))&255;e[0x11]=((hero_y>>8)+((u16)dy>>8))&255;
    }
    ending_stage=5;
    for(n=0;n<9;n++)
    { ending_wait(4);world_actor_state[n*48+3]=1;ending_sprites_pending=1;ending_palette_wait(); }
    ending_wait(240);ending_wait(120);sound_music(0x88);
    ending_stage=6;
    {
        static const u8 indices[]={0,2,3,4,5,6,7,12,13,14,15};
        for(n=0;n<11;n++)
        { sms_palette[indices[n]]=0;set_world_palette();for(tick=0;tick<30;tick++) wait_frame(); }
    }
    for(n=0x3800;n<0x3e00;n+=2) { sms_vram[n]=255;sms_vram[n+1]=8; }
    map_origin=0x3800;draw_map();
    load_mono(0x1600,normal_font,256,3,TRUE);convert_patterns_range(176,32);VDP_loadTileData(md_patterns+176*8,192,32,CPU);
    ending_hero_descriptor=0x84e1;hero_animation=0;ending_sprites_pending=1;
    wait_frame();update_hero_sprites();ending_sprites_pending=0;
    ending_stage=7;ending_map_top=65535;ending_virtual_top=0;memset(&ending_credits,0,sizeof(ending_credits));ending_credits.row=0x7e00;ending_credits.vscroll=0;
    VDP_fillTileMapRect(WINDOW,0,0,0,32,2);VDP_setWindowHPos(FALSE,0);VDP_setWindowVPos(FALSE,2);
    { u16 address=ending_credits.row;ending_credit_row(&ending_credits,line);ending_emit_credit_row(line,address); }
    while(!ending_credits.done)
    {
        u16 address=ending_credits.row;
        if(ending_credit_tick(&ending_credits,line)) ending_emit_credit_row(line,address);
        ending_credit_map();wait_frame();
    }
    ending_stage=8;previous=input;
    do { wait_frame();tick=input&~previous;previous=input; } while(!(tick&(BUTTON_B|BUTTON_C)));
    VDP_setWindowVPos(FALSE,0);VDP_setVerticalScroll(BG_A,0);ending_hero_descriptor=0;ending_stage=0;game_state=0;
}
