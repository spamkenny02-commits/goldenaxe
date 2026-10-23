/* 3124..31E6: ice bell, including the original eight rotating bit masks. */
#include "ice_bell_assets.inc"

static void apply_ice_bell_metatiles(u16 number)
{
    u16 n,offset;
    if(world_graphics_class) return;
    memcpy(scratch+0x1c0,ice_bell_state?ice_bell_metatiles:scratch+0x98,8);
    memcpy(scratch+0x1f0,ice_bell_state?ice_bell_metatiles+8:scratch+0x98,8);
    for(n=0;n<8;n++)
    {
        u16 word;
        offset=(n<4?0x1c0:0x1f0)+(n&3)*2;
        word=scratch[offset]|((u16)scratch[offset+1]<<8);
        world_metatiles_md[offset/2]=TILE_ATTR_FULL((word>>11)&1,(word>>12)&1,(word>>10)&1,(word>>9)&1,16+(word&511));
    }
    if(!ice_bell_state) return;
    for(n=0;n<3;n++) if((number&255)==ice_bell_passages[n])
    { game_save_state[0x50+(number&255)]|=1;prepare_room_transformation();break; }
}

static void activate_ice_bell(void)
{
    u16 n,water=0,step,water_tile,ice_tile;
    u32 started,budget;
    u8 ice[32],mask=0x7f;
    sound_effect_main(0xa4); /* 3124 rings even in an interior. */
    if(world_graphics_class) return;
    for(n=0;n<160;n++) if(scratch[0x800+n]==0x3f)
    { scratch[0x800+n]=0x3a;water++; }
    if(!water && ice_bell_state) return;
    if(water)
    {
        ice_tile=(scratch[0x1d0]|((u16)scratch[0x1d1]<<8))&511;
        water_tile=(scratch[0x1f8]|((u16)scratch[0x1f9]<<8))&511;
        memcpy(ice,sms_vram+ice_tile*32,32);
        for(step=0;step<8;step++)
        {
            u8 row_mask=mask;
            portal_wait_frame();portal_wait_frame();
            for(n=0;n<128;n++)
            {
                u16 address=water_tile*32+n;
                sms_vram[address]=(sms_vram[address]&row_mask)|(ice[n&31]&(u8)~row_mask);
                if((n&3)==3) row_mask=(row_mask>>4)|(row_mask<<4);
            }
            convert_patterns_range_fast(water_tile,4);
            VDP_loadTileData(md_patterns+water_tile*8,16+water_tile,4,CPU);
            mask=(mask>>1)|(mask<<7);
        }
        for(n=0;n<16;n++)
        {
            u8 *entity=world_actor_state+n*48;
            if(!entity[0]) continue;
            if(!(entity[3]&1)) memset(entity,0,48); /* 57EB */
            else
            {
                entity[7]=entity[0];entity[0]=1;entity[6]=entity[1]=0;
                memset(entity+0x14,0,4);sound_effect(0xa0); /* 27A7 */
            }
        }
    }
    ice_bell_state=1;started=vtimer;
    apply_ice_bell_metatiles(room_id);
    build_room_map(sms_vram+0x3800,world_new_md);
    budget=(SYS_isPAL()?71364UL:59736UL)-3072;
    while(vtimer-started<WORLD_REDRAW_PREPARE_TSTATES/budget) portal_wait_frame();
    portal_wait_frame();map_origin=0x3800;draw_map();
}
