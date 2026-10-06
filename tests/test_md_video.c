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
    }
    for(unsigned y=0;y<256u;++y){
        int expected=(int)y+1+(y>=224u?-256:0);
        assert((int)gaw_md_sprite_y((uint8_t)y)-128==expected);
    }
    puts("MD video conversion tests: OK (5120 rows, 64 colors, 8192 descriptors, 256 sprite positions)");
    return 0;
}
