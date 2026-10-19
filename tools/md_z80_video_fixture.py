"""Diagnostic visible-raster fixture; no game renderer substitution."""
VIDEO=r'''
volatile u32 gaw_video_updates;
static u32 video_pattern[8];
static void video_step(void) {
 u16 n;u32 mask;
 gaw_video_updates++;mask=(gaw_video_updates&1)?0x11111111UL:0;
 for(n=0;n<8;n++) video_pattern[n]=((n&1)?0x76543210UL:0x01234567UL)^mask;
 VDP_loadTileData(video_pattern,1,1,CPU);
}
static void video_setup(void) {
 static const u16 colors[]={0x000,0x00e,0x0e0,0xe00,0x0ee,0xe0e,0xee0,0xeee,
                            0x666,0x006,0x060,0x600,0x066,0x606,0x660,0xaaa};
 gaw_video_updates=0;
 PAL_setColors(0,colors,16,CPU);video_step();
 VDP_fillTileMapRect(BG_A,TILE_ATTR_FULL(0,0,0,0,1),0,0,32,28);
 VDP_setEnable(TRUE);
}
'''


def instrument(main, cpu_writes):
    needle='static void work(void)'
    assert main.count(needle)==1
    main=main.replace(needle,VIDEO+'\n'+needle)
    needle='VDP_setEnable(FALSE);'
    assert main.count(needle)==1
    main=main.replace(needle,needle+'video_setup();')
    if cpu_writes:
        needle=' *(volatile u16*)0xc00010=0x31;'
        assert main.count(needle)==1
        main=main.replace(needle,' video_step();\n'+needle)
    return main


def expected_pattern(updates):
    mask=0x11111111 if updates&1 else 0
    return b''.join(((0x76543210 if n&1 else 0x01234567)^mask).to_bytes(4,'big') for n in range(8))
