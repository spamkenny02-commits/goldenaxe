#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "gaw_md_video.h"

static uint8_t vram[0x4000];
static uint32_t random=0xC01DFACEu;
static uint32_t next(void){random=random*1664525u+1013904223u;return random;}

static uint32_t reference_mask(uint8_t sy,unsigned height,uint8_t counts[192]){
    if(sy==208u)return 0;
    int top=(int)sy+1;if(sy>208u)top-=256;
    uint32_t mask=0;
    /* Scan visible lines rather than sprite rows; no packed pattern helper. */
    for(int line=0;line<192;++line){
        int row=line-top;
        if(row>=0&&row<(int)height&&counts[line]<8u){
            ++counts[line];mask|=(uint32_t)1u<<(unsigned)row;
        }
    }
    return mask;
}
int main(void){
    unsigned masks=0,pixels=0;
    static const unsigned heights[]={8,16,32};
    for(unsigned h=0;h<3u;++h)
    for(unsigned y=0;y<256u;++y)
    for(unsigned seed=0;seed<3u;++seed){
        uint8_t actual[192],expected[192];
        for(unsigned line=0;line<192u;++line)
            actual[line]=expected[line]=(uint8_t)(seed==0u?0u:(seed==1u?7u:next()%9u));
        assert(gaw_md_sprite_line_mask((uint8_t)y,heights[h],actual)==
               reference_mask((uint8_t)y,heights[h],expected));
        assert(memcmp(actual,expected,sizeof actual)==0);++masks;
    }
    for(unsigned test=0;test<256u;++test){
        uint8_t actual[192]={0},expected[192]={0};
        for(unsigned sprite=0;sprite<64u;++sprite){
            uint8_t y=(uint8_t)(test&1u?40u+(next()&15u):next());
            unsigned height=heights[next()%3u];
            assert(gaw_md_sprite_line_mask(y,height,actual)==reference_mask(y,height,expected));
            assert(memcmp(actual,expected,sizeof actual)==0);++masks;
        }
    }
    uint8_t counts[192]={0};
    for(unsigned i=0;i<8u;++i)assert(gaw_md_sprite_line_mask(49,8,counts)==0xFFu);
    assert(gaw_md_sprite_line_mask(53,8,counts)==0xF0u);
    assert(gaw_md_sprite_line_mask(49,8,counts)==0);
    memset(counts,0,sizeof counts);
    assert(gaw_md_sprite_line_mask(0xE0,32,counts)==0x80000000u);
    for(unsigned a=0;a<sizeof vram;++a)vram[a]=(uint8_t)(next()>>24);
    for(unsigned trial=0;trial<4096u;++trial){
        unsigned tile=next()&0x1FEu,row=(next()>>16)&15u;
        unsigned at=tile*32u+row*4u;
        for(unsigned zoom=0;zoom<2u;++zoom){
            uint32_t left=gaw_md_sprite_pattern_row(vram,tile,row,zoom,0);
            uint32_t right=zoom?gaw_md_sprite_pattern_row(vram,tile,row,zoom,1):0;
            for(unsigned x=0;x<(zoom?16u:8u);++x){
                unsigned shift=7u-(x>>zoom),want=0;
                for(unsigned plane=0;plane<4u;++plane)
                    want|=((vram[at+plane]>>shift)&1u)<<plane;
                unsigned actual=((x<8u?left:right)>>(28u-4u*(x&7u)))&15u;
                assert(actual==want);++pixels;
            }
        }
    }
    printf("ROM-free MD sprite masks/patterns: OK (%u mask/count cases, %u independent pixels)\n",masks,pixels);
    return 0;
}
