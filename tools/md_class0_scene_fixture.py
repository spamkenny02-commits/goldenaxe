"""Native class0 background pipeline, with ROM-derived resident HUD assets."""
from extract_title import rle_planes
from md_z80_source_video_fixture import convert_sms_patterns

def resident_sms(rom):
    data=bytearray(16384)
    for source,destination in [(0x13701,0x3040),(0x1274c,0x1e00),(0x13db0,0x1a00),(0x122d2,0x3600)]:
        rle_planes(rom,source,data,destination,4)
    data[0x1d80:0x1e00]=rom[0x12881:0x12901]
    remap=rom[0x1dd2:0x1de2]
    for offset in range(0x1d80,0x1e00,4):
        planes=data[offset:offset+4];out=[0]*4
        for bit in range(8):
            color=remap[sum(((v>>bit)&1)<<p for p,v in enumerate(planes))]
            for p in range(4):out[p]|=((color>>p)&1)<<bit
        data[offset:offset+4]=bytes(out)
    return bytes(data)

def assets(rom):
    packed=convert_sms_patterns(resident_sms(rom))
    return 'static const u32 scene_resident[]={'+','.join('0x'+packed[n:n+4].hex()+'UL' for n in range(0,len(packed),4))+'};\n'

VIDEO=r'''
static void fault(u32);static void work(void);
static MdClass0VideoStream scene;
volatile u32 gaw_video_updates,gaw_video_requests,gaw_video_dma_attempts,gaw_video_service_calls;
volatile u32 gaw_scene_sources,gaw_scene_maps,gaw_scene_palettes,gaw_scene_pattern_commits,gaw_scene_map_commits,gaw_scene_palette_commits;
volatile u32 gaw_scene_readback_words,gaw_scene_readback_errors;
volatile u8 gaw_scene_upper[16];
static void video_pump(void) {
 u8 status;u32 before;
 if(gaw_video_updates-1>=gaw_video_requests || session_failed) return;
 gaw_video_dma_attempts++;before=scene.readback_words;
 status=md_class0_video_stream_step(&scene,&mailbox);
 gaw_scene_readback_words+=scene.readback_words-before;gaw_scene_readback_errors=scene.readback_errors;
 if(status==MD_Z80_PSG_OK) {
  gaw_video_updates++;
  if(scene.last_kind==1) gaw_scene_pattern_commits++;
  else if(scene.last_kind==2) gaw_scene_map_commits++;
  else if(scene.last_kind==3) gaw_scene_palette_commits++;
  else fault(0xf60);
 } else if(status!=MD_Z80_PSG_WAIT) fault(0xf00|status);
}
static void video_flush(void) {
 u32 spins=0;
 while(gaw_video_updates-1<gaw_video_requests && !session_failed && ++spins<1000000UL) {video_pump();work();}
 if(gaw_video_updates-1!=gaw_video_requests || !scene.done) fault(0xf10);
}
void cooperative_scene_phase(u16 pc,const u8 *sms,const u8 *upper) {
 u16 n;u8 status=0;
 if(pc==0x1706) {
  *(volatile u16*)0xc00010=0x38;
  status=md_class0_video_stream_begin(&scene,SCENE_VERIFY);
  gaw_scene_sources++;gaw_video_requests+=49;
 }
 if(pc==0x1deb) {
  *(volatile u16*)0xc00010=0x39;
  status=md_class0_video_stream_map(&scene,sms);gaw_scene_maps++;gaw_video_requests+=24;
 }
 if(pc==0x24bf) {
  *(volatile u16*)0xc00010=0x3a;
  for(n=0;n<16;n++) gaw_scene_upper[n]=upper[n];
  status=md_class0_video_stream_palette(&scene,upper);gaw_scene_palettes++;gaw_video_requests++;
 }
 if(status) fault(0xf70|status);
 video_pump();
}
void cooperative_video_service(void) {gaw_video_service_calls++;video_pump();}
static void video_setup(void) {
 static const u32 blank[8]={0},solid[8]={0x11111111,0x11111111,0x11111111,0x11111111,0x11111111,0x11111111,0x11111111,0x11111111};
 VDP_setPlaneSize(64,32,TRUE);VDP_loadTileData(blank,0,1,CPU);VDP_loadTileData(solid,1,1,CPU);
 VDP_loadTileData(scene_resident,16,512,CPU);
 PAL_setColor(33,source_class0_video_background());
 VDP_fillTileMapRect(BG_A,0,0,0,64,32);
 VDP_fillTileMapRect(BG_B,TILE_ATTR_FULL(PAL2,0,0,0,1),0,2,32,24);
 gaw_video_updates=1;VDP_setEnable(TRUE);
}
'''

def instrument(main,body,verify=True,proof=False,hidden=False):
    # Existing observer copies reserve11776bytes even in bare kernels.
    # Full proof compares each live state directly to immutable reference ROM.
    main=main.replace('states[11776]','states[1]')
    if proof:
        needle='points,states,due,values,stats)'
        assert main.count(needle)==1
        main=main.replace(needle,'points,(u8*)cases[row].states,due,values,stats)')
        needle='  for(n=0;n<11776;n++) if(states[n]!=cases[row].states[n]) gaw_replay_failures++;'
        assert main.count(needle)==1
        main=main.replace(needle,'')
        body='volatile unsigned long gaw_scene_state_checks;\n'+body
        needle=' for(n=0;n<336;n++) state[n]=ctx->ram[n];\n for(n=0;n<400;n++) state[336+n]=ctx->audio[n];'
        assert body.count(needle)==1
        body=body.replace(needle,' for(n=0;n<336;n++) if(state[n]!=ctx->ram[n]) return 0;\n for(n=0;n<400;n++) if(state[336+n]!=ctx->audio[n]) return 0;\n gaw_scene_state_checks++;')
    main=main.replace('#include "md_z80_psg.h"','#include "md_z80_psg.h"\n#include "md_class0_video_stream.h"\n#include "source_class0_video.h"\n#include "scene-resident.h"')
    needle='static void work(void)'
    assert main.count(needle)==1
    main=main.replace(needle,VIDEO.replace('SCENE_VERIFY','1' if verify else '0')+'\n'+needle)
    needle='VDP_setEnable(FALSE);';assert main.count(needle)==1
    main=main.replace(needle,needle+'video_setup();')
    needle=' spins=0;do {status=md_z80_psg_stop(&mailbox);';assert main.count(needle)==1
    main=main.replace(needle,' video_flush();\n'+needle)
    body='void cooperative_scene_phase(unsigned short,const unsigned char *,const unsigned char *);\n'+body
    needle='u8 *states;SourceIrqContext *irq;';assert body.count(needle)==1
    body=body.replace(needle,'u8 *states;const u8 *scene_map,*scene_upper;SourceIrqContext *irq;')
    needle=' data.patterns=pixels;';assert body.count(needle)==1
    body=body.replace(needle,' log.scene_map=tilemap;log.scene_upper=cells+0xb0;'+needle)
    needle=' p->points++;return 1;';assert body.count(needle)==1
    body=body.replace(needle,' cooperative_scene_phase(pc,p->scene_map,p->scene_upper);\n'+needle)
    if hidden:
        main=main.replace('md_class0_video_stream_begin(&scene,','md_class0_video_stream_begin_hidden(&scene,')
        needle='*(volatile u16*)0xc00010=0x80+gaw_replay_cases;'
        assert main.count(needle)==1
        main=main.replace(needle,needle+'VDP_setEnable(FALSE);*(volatile u16*)0xc00010=0x3d;')
        needle=' video_flush();\n spins=0;do'
        assert main.count(needle)==1
        main=main.replace(needle,' video_flush();\n if(!session_failed) {VDP_setEnable(TRUE);*(volatile u16*)0xc00010=0x3e;}\n spins=0;do')
    return main,body

def validate(folder,region,frame,observed,vram,regs,rom,proof=False,verify=True):
    import hashlib
    from pathlib import Path
    source=(folder/(region+'-source-patterns.bin')).read_bytes()
    wanted=bytearray(convert_sms_patterns(resident_sms(rom)))
    wanted[:193*32]=convert_sms_patterns(source)[:193*32]
    assert bytes(vram[(512+n)^1] for n in range(16384))==wanted
    plane=(regs[2]&0x38)<<10
    for n in range(768):
        sms=int.from_bytes(source[0x3800+n*2:0x3802+n*2],'little')
        md=16+(sms&511)|((sms&0x200)<<2)|((sms&0x400)<<2)|((sms&0x800)<<2)|((sms&0x1000)<<3)
        row,col=divmod(n,32);address=plane+(row+2)*128+col*2
        assert int.from_bytes(vram[address:address+2],'little')==md,(region,n)
    levels=[0,3,5,7]
    def color(v):return levels[v&3]<<1|levels[(v>>2)&3]<<5|levels[(v>>4)&3]<<9
    values=[color(v) for v in rom[0x3c000:0x3c010]]+[color(v) for v in observed['scene_upper']];values[0]=0
    cram=(folder/(region+'-plain')/f'cram_{frame:05d}.bin').read_bytes()
    packed=lambda v:((v&0xe00)>>3)|((v&0xe0)>>2)|((v&0xe)>>1)
    assert [int.from_bytes(cram[n*2:n*2+2],'little') for n in range(32)]==[packed(v) for v in values]
    assert observed['scene_sources']==observed['scene_maps']==observed['scene_palettes']==48
    assert observed['scene_state_checks']==(768 if proof else 0)
    assert observed['scene_pattern_commits']==2352 and observed['scene_map_commits']==1152 and observed['scene_palette_commits']==48
    assert observed['video_requests']==3552 and observed['video_updates']==3553
    assert observed['scene_readback_words']==(186624 if verify else 0) and not observed['scene_readback_errors']
    return dict(resident_patterns_preserved=319,map_words=768,palette_colors=32,cram_sha256=hashlib.sha256(cram).hexdigest())
