"""Upload the actual source-checked SMS pattern mirror as an MD tile atlas."""
from md_z80_video_fixture import instrument

def instrument_source(main,body,tiles=1,readback=True,during_delivery=False,refresh=False,grant_backoff=False):
    assert 1<=tiles<=8
    main=instrument(main,False,True,0,True,True)
    main=main.replace('#include "md_z80_video_dma.h"','#include "md_z80_video_dma.h"\n#include "pattern_convert.h"')
    main=main.replace('static u8 video_pattern_prepared;', '''static const u8 *video_source;static u16 video_cursor,video_batch;
volatile u32 gaw_video_sources,gaw_video_readback_words,gaw_video_readback_errors,gaw_video_dma_commits;
static u8 video_pattern_prepared;''')
    needle=' mask=((gaw_video_updates+1)&1)?0x11111111UL:0;\n for(n=0;n<8;n++) video_pattern[n]=((n&1)?0x76543210UL:0x01234567UL)^mask;'
    assert main.count(needle)==1
    main=main.replace(needle,' video_batch=512-video_cursor;if(video_batch>'+str(tiles)+') video_batch='+str(tiles)+';\n pattern_convert(video_source+(u32)video_cursor*32,video_pattern,video_batch*8);')
    if tiles==8:
        main=main.replace('static u16 video_cursor,video_batch;', 'static u16 video_cursor,video_batch;\nvolatile u32 gaw_video_span_sizes[9];')
        main=main.replace(' pattern_convert(video_source+(u32)video_cursor*32,video_pattern,video_batch*8);',' if((mailbox.busy || mailbox.head!=mailbox.tail) && video_batch>4) video_batch=4;\n pattern_convert(video_source+(u32)video_cursor*32,video_pattern,video_batch*8);')
    if tiles==3:
        needle=' pattern_convert(video_source+(u32)video_cursor*32,video_pattern,video_batch*8);'
        main=main.replace(needle,' if(video_cursor==0) video_batch=1;else if(video_cursor==1) video_batch=2;\n'+needle)
    needle='md_z80_video_dma_prepare(&video_job,video_pattern,1)'
    assert main.count(needle)==1
    main=main.replace(needle,'md_z80_video_dma_prepare(&video_job,video_pattern,16+video_cursor)')
    needle='if(status==MD_Z80_PSG_OK) {gaw_video_updates++;video_pattern_prepared=0;}'
    assert main.count(needle)==1
    main=main.replace(needle,'''if(status==MD_Z80_PSG_OK) {
  /* Read actual VDP RAM after the DMA, while the immutable payload remains. */
  const u16 *wanted=(const u16*)video_pattern;
  *(volatile u32*)VDP_CTRL_PORT=VDP_READ_VRAM_ADDR((u32)(16+video_cursor)*32);
  for(n=0;n<16*video_batch;n++) {if(*(volatile u16*)VDP_DATA_PORT!=wanted[n]) gaw_video_readback_errors++;gaw_video_readback_words++;}
  if(gaw_video_readback_errors) fault(0xf30);
  gaw_video_updates+=video_batch;video_cursor+=video_batch;gaw_video_dma_commits++;video_pattern_prepared=0;
 }''')
    if tiles==8:main=main.replace('gaw_video_dma_commits++;video_pattern_prepared=0;', 'gaw_video_dma_commits++;gaw_video_span_sizes[video_batch]++;video_pattern_prepared=0;')
    if not readback:
        a=main.index('  /* Read actual VDP RAM after the DMA,')
        b=main.index('  gaw_video_updates+=video_batch;',a)
        main=main[:a]+main[b:]
        main=main.replace(' gaw_video_updates=0;', ' gaw_video_readback_words=gaw_video_readback_errors=0;gaw_video_updates=0;')
    needle='static void video_request(void) {gaw_video_requests++;video_pump();}'
    assert main.count(needle)==1
    main=main.replace(needle,'''static void video_request(void) {}
void cooperative_video_source(const u8 *source) {
 if(gaw_video_updates-1!=gaw_video_requests || video_pattern_prepared) {fault(0xf40);return;}
 video_source=source;video_cursor=0;gaw_video_requests+=512;gaw_video_sources++;
}''')
    if tiles>1:
        main=main.replace('static u32 video_pattern[8];','static u32 video_pattern['+str(tiles*8)+'];')
        main=main.replace('MdZ80VideoDmaJob video_job;','MdZ80VideoSpan video_job;')
        main=main.replace('#include "md_z80_video_dma.h"','#include "md_z80_video_dma.h"\n#include "md_z80_video_span.h"')
        main=main.replace('md_z80_video_dma_prepare(&video_job,video_pattern,16+video_cursor)','md_z80_video_span_prepare(&video_job,video_pattern,16+video_cursor,video_batch)')
        main=main.replace('md_z80_video_dma_try_prepared(&mailbox,&video_job)','md_z80_video_span_try(&mailbox,&video_job)')
    if refresh:
        main=main.replace('md_z80_video_span_try(&mailbox,&video_job)','md_z80_video_span_try_refresh(&mailbox,&video_job)')
        main=main.replace('md_z80_video_span_prepare(&video_job,video_pattern,16+video_cursor,video_batch)','md_z80_video_span_prepare_refresh(&video_job,video_pattern,16+video_cursor,video_batch)')
    if grant_backoff:
        main=main.replace('static u8 video_pattern_prepared;', 'static u8 video_pattern_prepared;static u8 video_wait_grant,video_last_grant;\nvolatile u32 gaw_video_grant_skips;')
        needle=' if(gaw_video_updates-1>=gaw_video_requests || session_failed) return;'
        assert main.count(needle)==1
        main=main.replace(needle,needle+'\n if(video_wait_grant && video_last_grant==mailbox.grant && !mailbox.stamp.error) {gaw_video_grant_skips++;return;}\n video_wait_grant=0;')
        needle=' else if(status!=MD_Z80_PSG_WAIT) fault(0xf00|status);'
        assert main.count(needle)==1
        main=main.replace(needle,' else if(status==MD_Z80_PSG_WAIT) {video_last_grant=mailbox.grant;video_wait_grant=1;}\n else fault(0xf00|status);')
    needle=' VDP_setEnable(TRUE);'
    assert main.count(needle)==1
    main=main.replace(needle,''' {u16 x,y;for(y=0;y<16;y++) for(x=0;x<32;x++) VDP_setTileMapXY(BG_A,16+y*32+x,x,y);}
'''+needle)
    if during_delivery:
        needle=' while((mailbox.head!=mailbox.tail || mailbox.busy) && !mailbox.stamp.error && ++spins<1000000UL) work();'
        assert main.count(needle)==1
        main=main.replace(needle,needle.replace(' work();',' {video_pump();work();}'))
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


def jobs_per_case(tiles):
    return 172 if tiles==3 else (512+tiles-1)//tiles
