"""Upload the actual source-checked SMS pattern mirror as an MD tile atlas."""
from md_z80_video_fixture import instrument

def instrument_source(main,body):
    main=instrument(main,False,True,0,True,True)
    main=main.replace('#include "md_z80_video_dma.h"','#include "md_z80_video_dma.h"\n#include "pattern_convert.h"')
    main=main.replace('static u8 video_pattern_prepared;', '''static const u8 *video_source;static u16 video_cursor;
volatile u32 gaw_video_sources,gaw_video_readback_words,gaw_video_readback_errors;
static u8 video_pattern_prepared;''')
    needle=' mask=((gaw_video_updates+1)&1)?0x11111111UL:0;\n for(n=0;n<8;n++) video_pattern[n]=((n&1)?0x76543210UL:0x01234567UL)^mask;'
    assert main.count(needle)==1
    main=main.replace(needle,' pattern_convert(video_source+(u32)video_cursor*32,video_pattern,8);')
    needle='md_z80_video_dma_prepare(&video_job,video_pattern,1)'
    assert main.count(needle)==1
    main=main.replace(needle,'md_z80_video_dma_prepare(&video_job,video_pattern,16+video_cursor)')
    needle='if(status==MD_Z80_PSG_OK) {gaw_video_updates++;video_pattern_prepared=0;}'
    assert main.count(needle)==1
    main=main.replace(needle,'''if(status==MD_Z80_PSG_OK) {
  /* Read actual VDP RAM after the DMA, while the immutable payload remains. */
  const u16 *wanted=(const u16*)video_pattern;
  *(volatile u32*)VDP_CTRL_PORT=VDP_READ_VRAM_ADDR((u32)(16+video_cursor)*32);
  for(n=0;n<16;n++) {if(*(volatile u16*)VDP_DATA_PORT!=wanted[n]) gaw_video_readback_errors++;gaw_video_readback_words++;}
  if(gaw_video_readback_errors) fault(0xf30);
  gaw_video_updates++;video_cursor++;video_pattern_prepared=0;
 }''')
    needle='static void video_request(void) {gaw_video_requests++;video_pump();}'
    assert main.count(needle)==1
    main=main.replace(needle,'''static void video_request(void) {}
void cooperative_video_source(const u8 *source) {
 if(gaw_video_updates-1!=gaw_video_requests || video_pattern_prepared) {fault(0xf40);return;}
 video_source=source;video_cursor=0;gaw_video_requests+=512;gaw_video_sources++;
}''')
    needle=' VDP_setEnable(TRUE);'
    assert main.count(needle)==1
    main=main.replace(needle,''' {u16 x,y;for(y=0;y<16;y++) for(x=0;x<32;x++) VDP_setTileMapXY(BG_A,16+y*32+x,x,y);}
'''+needle)
    needle=' cooperative_finish();'
    assert body.count(needle)==1
    body=body.replace(needle,' cooperative_video_source(pixels);\n'+needle)
    body='void cooperative_video_source(const unsigned char *);\n'+body
    return main,body

def convert_sms_patterns(source):
    assert len(source)==16384
    result=bytearray()
    for start in range(0,len(source),4):
        planes=source[start:start+4];word=0
        for bit in range(7,-1,-1):
            pixel=sum(((p>>bit)&1)<<plane for plane,p in enumerate(planes))
            word=(word<<4)|pixel
        result.extend(word.to_bytes(4,'big'))
    return bytes(result)
