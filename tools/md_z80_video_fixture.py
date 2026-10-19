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


def instrument(main, cpu_writes, dma=False, service_stride=0, cache_pattern=False):
    video=VIDEO
    if dma:
        video=video.replace('volatile u32 gaw_video_updates;', 'volatile u32 gaw_video_updates,gaw_video_requests,gaw_video_dma_attempts;')
        video+='''
static void video_pump(void) {
 u16 n;u32 mask;u8 status;
 if(gaw_video_updates-1>=gaw_video_requests || session_failed) return;
 mask=((gaw_video_updates+1)&1)?0x11111111UL:0;
 for(n=0;n<8;n++) video_pattern[n]=((n&1)?0x76543210UL:0x01234567UL)^mask;
 gaw_video_dma_attempts++;
 status=md_z80_video_dma_try(&mailbox,video_pattern,1);
 if(status==MD_Z80_PSG_OK) gaw_video_updates++;
 else if(status!=MD_Z80_PSG_WAIT) fault(0xf00|status);
}
static void video_request(void) {gaw_video_requests++;video_pump();}
static void video_flush(void) {
 u32 spins=0;
 while(gaw_video_updates-1<gaw_video_requests && !session_failed && ++spins<1000000UL) {video_pump();work();}
 if(gaw_video_updates-1!=gaw_video_requests) fault(0xf10);
}
'''
        # Helpers call the later kernel functions, whose bodies remain intact.
        video='static void fault(u32);static void work(void);\n'+video
        if cache_pattern:
            video=video.replace('volatile u32 gaw_video_updates,gaw_video_requests,gaw_video_dma_attempts;', 'volatile u32 gaw_video_updates,gaw_video_requests,gaw_video_dma_attempts,gaw_video_pattern_preparations;\nstatic u8 video_pattern_prepared;')
            needle=' mask=((gaw_video_updates+1)&1)?0x11111111UL:0;\n for(n=0;n<8;n++) video_pattern[n]=((n&1)?0x76543210UL:0x01234567UL)^mask;'
            assert video.count(needle)==1
            video=video.replace(needle,' if(!video_pattern_prepared) {\n'+needle+'\n video_pattern_prepared=1;gaw_video_pattern_preparations++;\n }')
            video=video.replace(' if(status==MD_Z80_PSG_OK) gaw_video_updates++;', ' if(status==MD_Z80_PSG_OK) {gaw_video_updates++;video_pattern_prepared=0;}')
        if service_stride:
            video+='''
volatile u32 gaw_video_service_calls;
static u16 video_service_phase;
void cooperative_video_service(void) {
 gaw_video_service_calls++;
 if((++video_service_phase&'''+str(service_stride-1)+''')==0) video_pump();
}
'''
        main=main.replace('#include "md_z80_psg.h"','#include "md_z80_psg.h"\n#include "md_z80_video_dma.h"')
    needle='static void work(void)'
    assert main.count(needle)==1
    main=main.replace(needle,video+'\n'+needle)
    needle='VDP_setEnable(FALSE);'
    assert main.count(needle)==1
    main=main.replace(needle,needle+'video_setup();')
    if cpu_writes or dma:
        needle=' *(volatile u16*)0xc00010=0x31;'
        assert main.count(needle)==1
        main=main.replace(needle,(' video_request();\n' if dma else ' video_step();\n')+needle)
    if dma:
        needle=' spins=0;do {status=md_z80_psg_stop(&mailbox);'
        assert main.count(needle)==1
        main=main.replace(needle,' video_flush();\n'+needle)
    return main


def expected_pattern(updates):
    mask=0x11111111 if updates&1 else 0
    return b''.join(((0x76543210 if n&1 else 0x01234567)^mask).to_bytes(4,'big') for n in range(8))
