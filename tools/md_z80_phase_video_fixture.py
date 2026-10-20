"""Release immutable prefix/tail atlas extents at actual loader checkpoints."""
def instrument(main,body,stride=1,proof=False):
    assert stride>=1 and not stride&(stride-1)
    main=main.replace('static const u8 *video_source;static u16 video_cursor,video_batch;',
        'static const u8 *video_source;static u16 video_cursor,video_batch,video_frontier;\nvolatile u32 gaw_video_prefix_ready,gaw_video_tail_ready,gaw_video_service_calls;')
    needle=' video_batch=512-video_cursor;'
    assert main.count(needle)==1
    main=main.replace(needle,' video_batch=video_frontier-video_cursor;')
    needle='video_source=source;video_cursor=0;gaw_video_requests+=512;gaw_video_sources++;'
    assert main.count(needle)==1
    main=main.replace(needle,'video_source=source;video_cursor=0;video_frontier=448;gaw_video_requests+=448;gaw_video_sources++;gaw_video_prefix_ready++;')
    needle='static void video_request(void) {}'
    assert main.count(needle)==1
    main=main.replace(needle,needle+'\nstatic u16 video_service_phase;')
    main+='''
void cooperative_video_phase(u16 pc,const u8 *source) {
 if(pc==0x1706) {*(volatile u16*)0xc00010=0x38;cooperative_video_source(source);}
 if(pc==0x1deb) {
  *(volatile u16*)0xc00010=0x39;
  if(source!=video_source || video_frontier!=448) {fault(0xf50);return;}
  video_frontier=512;gaw_video_requests+=64;gaw_video_tail_ready++;
 }
 video_pump();
}
void cooperative_video_service(void) {
 gaw_video_service_calls++;
 if((++video_service_phase&STRIDE)==0) video_pump();
}
'''.replace('STRIDE',str(stride-1))
    needle=' cooperative_video_source(pixels);\n'
    assert body.count(needle)==1
    body=body.replace(needle,'')
    body='void cooperative_video_phase(unsigned short,const unsigned char *);\n'+body
    needle='u8 *states;SourceIrqContext *irq;'
    assert body.count(needle)==1
    body=body.replace(needle,'u8 *states;const u8 *video_source;u32 video_prefix_hash;SourceIrqContext *irq;')
    needle=' data.patterns=pixels;'
    assert body.count(needle)==1
    body=body.replace(needle,' log.video_source=pixels;'+needle)
    needle=' p->points++;return 1;'
    assert body.count(needle)==1
    body=body.replace(needle,' cooperative_video_phase(pc,p->video_source);\n'+needle)
    if proof:
        body='static unsigned long hash(const unsigned char *,unsigned short);\n'+body
        needle=' cooperative_video_phase(pc,p->video_source);'
        body=body.replace(needle,''' if(pc==0x1706) p->video_prefix_hash=hash(p->video_source,0x3800);
 if(pc==0x1deb && p->video_prefix_hash!=hash(p->video_source,0x3800)) return 0;
'''+needle)
    return main,body
