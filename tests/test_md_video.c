#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "gaw_md_video.h"

static uint32_t pixels(uint8_t a,uint8_t b,uint8_t c,uint8_t d) {
    uint32_t row=0;
    for(unsigned x=0;x<8u;++x){
        unsigned bit=7u-x;
        row=(row<<4)|((a>>bit)&1u)|(((b>>bit)&1u)<<1)|
                      (((c>>bit)&1u)<<2)|(((d>>bit)&1u)<<3);
    }
    return row;
}

int main(void) {
    uint32_t random=0x13579BDFu;
    for(unsigned i=0;i<256u;++i)
    for(unsigned p=0;p<4u;++p){
        uint8_t plane[4]={0,0,0,0};plane[p]=(uint8_t)i;
        assert(gaw_md_pattern_row(plane[0],plane[1],plane[2],plane[3])==pixels(plane[0],plane[1],plane[2],plane[3]));
    }
    for(unsigned i=0;i<4096u;++i){
        random=random*1664525u+1013904223u;
        uint8_t a=(uint8_t)random,b=(uint8_t)(random>>8),c=(uint8_t)(random>>16),d=(uint8_t)(random>>24);
        assert(gaw_md_pattern_row(a,b,c,d)==pixels(a,b,c,d));
    }
    static const unsigned levels[]={0,2,5,7};
    for(unsigned color=0;color<64u;++color){
        uint16_t actual=gaw_md_color((uint8_t)color);
        assert(((actual>>1)&7u)==levels[color&3u]);
        assert(((actual>>5)&7u)==levels[(color>>2)&3u]);
        assert(((actual>>9)&7u)==levels[(color>>4)&3u]);
    }
    for(unsigned descriptor=0;descriptor<8192u;++descriptor){
        uint16_t actual=gaw_md_descriptor((uint16_t)descriptor);
        assert((actual&511u)==(descriptor&511u));
        assert(((actual>>11)&1u)==((descriptor>>9)&1u));
        assert(((actual>>12)&1u)==((descriptor>>10)&1u));
        assert(((actual>>13)&1u)==((descriptor>>11)&1u));
        assert(((actual>>15)&1u)==((descriptor>>12)&1u));
        uint16_t zero=gaw_md_zero_descriptor((uint16_t)descriptor);
        assert((zero&0x07FFu)==0x500u);
        assert(((zero>>13)&3u)==2u+((descriptor>>11)&1u));
        assert((zero&0x9800u)==0); /* no priority or flips */
    }
    /* Independently compose indexed colours for all background/sprite pixels.
       SMS priority applies only to nonzero background pixels. MD transparent
       Plane A exposes the low-priority palette-zero filler beneath sprites. */
    for(unsigned palette=0;palette<2u;++palette)
    for(unsigned priority=0;priority<2u;++priority)
    for(unsigned bg=0;bg<16u;++bg)
    for(unsigned sprite=0;sprite<16u;++sprite){
        unsigned sms=(sprite&&(!priority||!bg))?16u+sprite:palette*16u+bg;
        uint16_t descriptor=(uint16_t)((palette<<11)|(priority<<12));
        uint16_t a=gaw_md_descriptor(descriptor),b=gaw_md_zero_descriptor(descriptor);
        unsigned md;
        if(bg&&(a&0x8000u))md=((a>>13)&1u)*16u+bg;
        else if(sprite)md=16u+sprite;
        else if(bg)md=((a>>13)&1u)*16u+bg;
        else md=(((b>>13)&3u)-2u)*16u;
        assert(md==sms);
    }
    for(unsigned scroll=0;scroll<256u;++scroll){
        for(unsigned line=0;line<192u;++line){
            unsigned physical=line+(scroll&31u);
            unsigned logical=gaw_md_scroll_row((uint8_t)scroll,physical/8u)*8u+physical%8u;
            assert(logical==(line+scroll)%224u);
            /* The right-locked pairs use VSRAM zero and the original row. */
            assert(gaw_md_scroll_row(0,line/8u)*8u+line%8u==line);
        }
        for(unsigned locked=0;locked<2u;++locked)
        for(unsigned dirty=0;dirty<30u;++dirty){
            uint32_t input=dirty<28u?(uint32_t)1u<<dirty:(dirty==28u?0xFFFFFFFFu:0x0A55AA55u);
            uint32_t expected=0;
            for(unsigned row=0;row<28u;++row){
                unsigned source=(row+4u*(scroll/32u))%28u;
                if((input&((uint32_t)1u<<source))||
                   (locked&&(input&((uint32_t)1u<<row))))expected|=(uint32_t)1u<<row;
            }
            assert(gaw_md_scroll_dirty_rows(input,(uint8_t)scroll,(uint8_t)locked)==expected);
        }
    }
    for(unsigned y=0;y<256u;++y){
        int expected=(int)y+1+(y>=224u?-256:0);
        assert((int)gaw_md_sprite_y((uint8_t)y)-128==expected);
    }
    puts("MD video conversion tests: OK (5120 rows, 64 colors, 8192 descriptors and zero layers, 1024 priority cases, 49152 scroll lines, 15360 dirty-row cases, 256 sprite positions)");
    return 0;
}
