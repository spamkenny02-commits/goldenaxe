#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_video.h"

static uint8_t vram[0x4000],regs[16];
static unsigned comparisons;

/* Independent, scanline-first oracle: parse the SAT anew for each line and
 * compare individual nontransparent pixels. No bitmap packing or cache. */
static uint8_t reference_status(void){
    uint8_t flags=0;
    unsigned sat=(unsigned)(regs[5]&0x7E)<<7;
    unsigned scale=(regs[1]&1)?2u:1u;
    unsigned height=(regs[1]&2)?16u:8u;
    if(!(regs[0]&4)||!(regs[1]&0x40))return 0;
    for(int line=0;line<192;++line){
        uint8_t pixels[256]={0};
        unsigned count=0;
        for(unsigned i=0;i<64;++i){
            unsigned y=vram[sat+i];
            if(y==208)break;
            int top=(int)y+1;
            if(y>208u)top-=256;
            int dy=line-top;
            if(dy<0||dy>=(int)(height*scale))continue;
            if(++count>8){flags|=0x40;break;}
            unsigned tile=vram[sat+0x81u+2u*i];
            if(height==16)tile&=254u;
            tile+=(regs[6]&4)?256u:0u;
            unsigned row=(unsigned)dy/scale;
            unsigned address=(tile+row/8u)*32u+(row%8u)*4u;
            int left=(int)vram[sat+0x80u+2u*i]-((regs[0]&8)?8:0);
            for(unsigned px=0;px<8u*scale;++px){
                int x=left+(int)px;
                if(x<0||x>=256)continue;
                uint8_t mask=(uint8_t)(0x80u>>(px/scale));
                int opaque=0;
                for(unsigned plane=0;plane<4;++plane)
                    if(vram[address+plane]&mask)opaque=1;
                if(opaque){if(pixels[x])flags|=0x20;pixels[x]=1;}
            }
        }
        if(flags==0x60)return flags;
    }
    return flags;
}
static void reg_write(unsigned r,uint8_t value){
    gaw_sms_vdp_control_write(value);
    gaw_sms_vdp_control_write((uint8_t)(0x80u|r));
}
static void upload_shadow(void){
    gaw_video_reset();
    for(unsigned a=0;a<0x4000;++a)gaw_video_write_at((uint16_t)a,vram[a]);
    for(unsigned r=0;r<16;++r)reg_write(r,regs[r]);
}
static void check(int shadow){
    uint8_t want=reference_status();
    uint8_t got=gaw_video_sprite_status(vram,regs);
    if(got!=want){
        fprintf(stderr,"sprite comparison %u: got %02X expected %02X\n",comparisons,got,want);
        assert(got==want);
    }
    ++comparisons;
    if(shadow){
        upload_shadow();
        gaw_video_status_pending(8);
        gaw_video_vblank_pending();
        assert(gaw_video_status_read()==(uint8_t)(0x88u|want));
        assert(gaw_video_status_read()==0);
        gaw_video_vblank_pending();
        assert(gaw_video_status_read()==(uint8_t)(0x80u|want));
        assert(gaw_video_status_read()==0);
    }
}
static void fixture(void){
    memset(vram,0,sizeof vram);memset(regs,0,sizeof regs);
    regs[0]=4;regs[1]=0x40;regs[5]=0x7E;
    vram[0x3F00]=0xD0;
}
static void sprite(unsigned i,uint8_t y,uint8_t x,uint8_t tile){
    unsigned sat=(unsigned)(regs[5]&0x7E)<<7;
    vram[sat+i]=y;vram[sat+0x80+2*i]=x;vram[sat+0x81+2*i]=tile;
}
static void terminate(unsigned n){
    if(n<64)vram[((unsigned)(regs[5]&0x7E)<<7)+n]=0xD0;
}
static void opaque_tile(unsigned tile,uint8_t bits){
    for(unsigned row=0;row<8;++row)vram[tile*32u+row*4u]=bits;
}
static uint32_t entropy=0xC0FFEE19u;
static uint8_t next_byte(void){
    entropy^=entropy<<13;entropy^=entropy>>17;entropy^=entropy<<5;
    return (uint8_t)entropy;
}
static uint8_t next_status(void){
    gaw_video_vblank_pending();return gaw_video_status_read();
}
int main(void){
    /* Overflow counts transparent/off-screen sprites too, on active Y lines. */
    for(unsigned mode=0;mode<4;++mode)for(unsigned y=0;y<256;++y){
        fixture();regs[1]=(uint8_t)(0x40u|mode);
        for(unsigned i=0;i<9;++i)sprite(i,(uint8_t)y,(uint8_t)(i*24u),1);
        terminate(9);
        check((y&63u)==0);
        assert(!(gaw_video_sprite_status(vram,regs)&0x20));
        /* Exactly eight visible entries cannot overflow. */
        terminate(8);check(0);assert(gaw_video_sprite_status(vram,regs)==0);
    }
    /* Zoomed 16-high E0 sprites expose their final pixel row on line zero.
       DF ends just before the viewport; E1 exposes two rows. Odd tile indices
       are masked to the even first pattern, including the second tile row. */
    for(unsigned y=0xDFu;y<=0xE1u;++y){
        fixture();regs[1]=0x43;opaque_tile(2,0xFF);opaque_tile(3,0xFF);
        sprite(0,(uint8_t)y,24,3);sprite(1,(uint8_t)y,24,2);terminate(2);
        check(1);
        assert(gaw_video_sprite_status(vram,regs)==(y>=0xE0u?0x20u:0u));
    }
    /* The ninth entry is never drawn and cannot create a collision. */
    fixture();opaque_tile(1,0xFF);
    for(unsigned i=0;i<8;++i)sprite(i,40,(uint8_t)(i*24u),1);
    sprite(8,40,0,1);terminate(9);check(1);
    assert(gaw_video_sprite_status(vram,regs)==0x40);
    /* Same coordinates are harmless with transparent patterns. */
    fixture();sprite(0,40,24,1);sprite(1,40,24,1);terminate(2);
    check(1);assert(gaw_video_sprite_status(vram,regs)==0);
    opaque_tile(1,0xFF);check(1);assert(gaw_video_sprite_status(vram,regs)==0x20);
    /* Only a nonzero plane matters; clipped pixels never collide. */
    static const uint8_t edge_x[]={0,1,7,8,15,31,32,63,248,255};
    for(unsigned mode=0;mode<4;++mode)for(unsigned shift=0;shift<2;++shift)
        for(unsigned a=0;a<sizeof edge_x;++a)for(unsigned b=0;b<sizeof edge_x;++b){
            fixture();regs[0]=(uint8_t)(4u|shift*8u);regs[1]=(uint8_t)(0x40u|mode);
            for(unsigned row=0;row<16;++row)vram[64u+row*4u+3u]=(uint8_t)(0x81u>>(row&3u));
            sprite(0,255,edge_x[a],2);sprite(1,255,edge_x[b],3);terminate(2);check(0);
        }
    /* A marker stops traversal even when later entries would overflow. */
    fixture();opaque_tile(1,0xFF);sprite(0,20,16,1);terminate(1);
    for(unsigned i=2;i<20;++i)sprite(i,20,16,1);
    check(1);assert(gaw_video_sprite_status(vram,regs)==0);
    /* Pattern edits and register/SAT writes invalidate frame status cache. */
    fixture();sprite(0,40,24,1);sprite(1,40,24,1);terminate(2);opaque_tile(1,0xFF);
    upload_shadow();assert(next_status()==0xA0);
    gaw_video_write_at(0x3F82,64);assert(next_status()==0x80);
    gaw_video_write_at(0x3F82,24);assert(next_status()==0xA0);
    for(unsigned row=0;row<8;++row)gaw_video_write_at((uint16_t)(32u+4u*row),0);
    assert(next_status()==0x80);
    gaw_video_write_at(32,0x80);assert(next_status()==0xA0);
    reg_write(1,0);assert(next_status()==0x80);
    reg_write(1,0x40);assert(next_status()==0xA0);
    reg_write(6,4);assert(next_status()==0x80);
    gaw_video_write_at(0x2020,0x80);assert(next_status()==0xA0);
    reg_write(5,0x7C);gaw_video_write_at(0x3E00,0xD0);assert(next_status()==0x80);
    reg_write(5,0x7E);assert(next_status()==0xA0);
    reg_write(0,0);assert(next_status()==0x80);
    reg_write(0,4);assert(next_status()==0xA0);
    /* Every mode, all four planes, both pattern banks, SAT bases, terminators,
     * wrap/clipping and dense sprite rows; reproducible synthetic input only. */
    for(unsigned c=0;c<4096;++c){
        fixture();
        for(unsigned a=0;a<0x4000;++a)vram[a]=(next_byte()&3u)?0:next_byte();
        regs[0]=(uint8_t)(4u|(next_byte()&8u));
        regs[1]=(uint8_t)(0x40u|(next_byte()&3u));
        regs[5]=(uint8_t)(next_byte()&0x7Eu);
        regs[6]=(uint8_t)(next_byte()&4u);
        unsigned n=next_byte()%65u;
        for(unsigned i=0;i<n;++i){
            uint8_t y=(c&1u)?(uint8_t)(next_byte()%32u+60u):next_byte();
            if(y==0xD0)y=0xD1;
            sprite(i,y,next_byte(),next_byte());
        }
        terminate(n);
        if((c%17u)==0)regs[1]&=(uint8_t)~0x40u;
        if((c%19u)==0)regs[0]&=(uint8_t)~4u;
        check(c<64u);
    }
    gaw_video_reset();assert(next_status()==0x80);
    puts("ROM-free SMS sprite status: pixel/scanline oracle, cache and status latch OK");
    printf("%u independent synthetic comparisons\n",comparisons);
    return 0;
}
