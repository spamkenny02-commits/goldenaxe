#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_video.h"

static uint8_t input[16417];
typedef struct {
    uint8_t vram[0x4000],cram[32],regs[16],tiles[512],reads[4],status,sat;
    uint32_t names;
} Snapshot;
static Snapshot scalar,block;
static unsigned cases;

static void control(unsigned at,unsigned code){
    gaw_sms_vdp_control_write((uint8_t)at);
    gaw_sms_vdp_control_write((uint8_t)((at>>8)|(code<<6)));
}
static void reg(unsigned r,uint8_t v){
    gaw_sms_vdp_control_write(v);gaw_sms_vdp_control_write((uint8_t)(0x80u|r));
}
static void fixture(unsigned at,unsigned code,int pending){
    gaw_video_reset();
    reg(0,4);reg(1,0x42);reg(2,0x0E);reg(5,0x7E);reg(6,4);
    for(unsigned a=0;a<0x4000;++a)gaw_video_write_at((uint16_t)a,(uint8_t)(a*17u+(a>>5)));
    for(unsigned a=0;a<32;++a){control(a,3);gaw_sms_vdp_data_write((uint8_t)(a*3u));}
    for(unsigned a=0;a<512;++a)(void)gaw_sms_take_tile_dirty(a);
    (void)gaw_sms_take_name_rows_dirty();(void)gaw_sms_take_sat_dirty();
    gaw_video_vblank_pending();(void)gaw_video_status_read();
    control(at,1);control(at,code);
    if(pending)gaw_sms_vdp_control_write(0xBA);
}
static void snapshot(Snapshot *out,int rows,int pending){
    memset(out,0,sizeof *out);
    /* Probe command latch, final address/code and read buffer indirectly. */
    if(pending){gaw_sms_vdp_control_write(0xAA);gaw_sms_vdp_control_write(0x41);}
    gaw_sms_vdp_data_write(0xA9);
    for(unsigned i=0;i<4;++i)out->reads[i]=gaw_sms_vdp_data_read();
    memcpy(out->vram,gaw_sms_vram(),sizeof out->vram);
    memcpy(out->cram,gaw_sms_cram(),sizeof out->cram);
    memcpy(out->regs,gaw_sms_vdp_regs(),sizeof out->regs);
    for(unsigned i=0;i<512;++i)out->tiles[i]=(uint8_t)gaw_sms_take_tile_dirty(i);
    out->names=rows?gaw_sms_take_name_rows_dirty():(uint32_t)gaw_sms_take_name_dirty();
    out->sat=(uint8_t)gaw_sms_take_sat_dirty();
    gaw_video_vblank_pending();out->status=gaw_video_status_read();
}
static void compare(unsigned at,unsigned code,unsigned count,int pending,int rows,int alias){
    fixture(at,code,pending);
    const uint8_t *source=alias==1?gaw_sms_vram()+0x100u:alias==2?gaw_sms_cram()+8u:input;
    for(unsigned i=0;i<count;++i)gaw_sms_vdp_data_write(source[i]);
    snapshot(&scalar,rows,pending);
    fixture(at,code,pending);
    source=alias==1?gaw_sms_vram()+0x100u:alias==2?gaw_sms_cram()+8u:input;
    gaw_sms_vdp_data_write_block(source,count);
    snapshot(&block,rows,pending);
    if(memcmp(&scalar,&block,sizeof scalar)){
        fprintf(stderr,"block case %u: address %04X code %u count %u pending %d rows %d alias %d\n",
                cases,at,code,count,pending,rows,alias);
        assert(!memcmp(&scalar,&block,sizeof scalar));
    }
    ++cases;
}
int main(void){
    static const unsigned lengths[]={0,1,2,31,32,33,63,64,65,127,128,129,255,256,257,1280,8192,16384,16417};
    static const unsigned starts[]={0,1,0x1F,0x20,0x3F,0x800,0x37FF,0x3800,0x3EFF,0x3F00,0x3F7F,0x3F80,0x3FFE,0x3FFF};
    for(unsigned i=0;i<sizeof input;++i)input[i]=(uint8_t)(i*31u+(i>>3));
    for(unsigned a=0;a<sizeof starts/sizeof starts[0];++a)
        for(unsigned n=0;n<sizeof lengths/sizeof lengths[0];++n)
            for(unsigned code=0;code<4;++code)for(int rows=0;rows<2;++rows)
                for(int pending=0;pending<2;++pending)
                    compare(starts[a],code,lengths[n],pending,rows,0);
    /* Sequential overlapping copies must observe prior writes, not memmove. */
    for(unsigned at=0xFF;at<0x103;++at)for(int rows=0;rows<2;++rows)
        compare(at,1,128,0,rows,1);
    for(unsigned at=6;at<11;++at)for(int rows=0;rows<2;++rows)
        compare(at,3,16,0,rows,2);
    /* Identical bytes leave exact dirty flags clear, including partial tiles. */
    fixture(0x3801,1,0);
    memcpy(input,gaw_sms_vram()+0x3801u,128);
    gaw_sms_vdp_data_write_block(input,128);
    for(unsigned i=0;i<512;++i)assert(!gaw_sms_take_tile_dirty(i));
    assert(!gaw_sms_take_name_rows_dirty());assert(!gaw_sms_take_sat_dirty());
    puts("ROM-free VDP block writes: scalar port/state/dirty equivalence OK");
    printf("%u block comparisons\n",cases);
    return 0;
}
