#include <string.h>
#include "include/gaw_video.h"

/* Collision coverage is frame scratch, not persistent game state. Keep it out
 * of the 68000 interrupt stack: the VBlank trampoline already saves all CPU
 * registers before entering C, and a 6144-byte automatic bitmap here made the
 * worst-case IRQ stack needlessly large. The engine is single-threaded and the
 * workspace is fully initialized per touched scanline before it is read. */
static uint8_t sprite_occupied[192][32];

/* 192-line Mode 4, as used by Golden Axe Warrior. Sprite positions, the
 * eight-per-line limit and nonzero pattern pixels belong to the SMS shadow,
 * independently of the host console's sprite limits. No ROM data is read.
 * This is frame-level status, not a scanline/cycle-accurate VDP emulator. */
uint8_t gaw_video_sprite_status(const uint8_t *vram,const uint8_t *regs){
    uint8_t counts[192]={0};
    static const uint8_t doubled[16]={
        0x00,0x03,0x0C,0x0F,0x30,0x33,0x3C,0x3F,
        0xC0,0xC3,0xCC,0xCF,0xF0,0xF3,0xFC,0xFF
    };
    uint8_t flags=0;
    unsigned sat=(unsigned)(regs[5]&0x7Eu)<<7;
    unsigned zoom=regs[1]&1u;
    unsigned height=(regs[1]&2u)?16u:8u;
    unsigned bank=(unsigned)(regs[6]&4u)<<6;
    if(!(regs[0]&4u)||!(regs[1]&0x40u))return 0;
    for(unsigned i=0;i<64u;++i){
        unsigned sy=vram[sat+i];
        if(sy==0xD0u)break;
        int top=sy>0xE0u?(int)sy-255:(int)sy+1;
        int first=top<0?0:top;
        int last=top+(int)(height<<zoom);
        if(last>192)last=192;
        int x=(int)vram[sat+0x80u+2u*i]-(int)(regs[0]&8u);
        unsigned tile=vram[sat+0x81u+2u*i];
        if(height==16u)tile&=0xFEu;
        tile|=bank;
        for(int y=first;y<last;++y){
            if(counts[y]>=8u){flags|=0x40u;continue;}
            if(!counts[y]&&!(flags&0x20u))memset(sprite_occupied[y],0,32);
            ++counts[y];
            if(flags&0x20u)continue;
            unsigned row=(unsigned)(y-top)>>zoom;
            unsigned a=(tile<<5)+(row<<2);
            uint8_t opaque=(uint8_t)(vram[a]|vram[a+1u]|vram[a+2u]|vram[a+3u]);
            uint16_t bits=zoom?(uint16_t)(((unsigned)doubled[opaque>>4]<<8)|doubled[opaque&15u]):(uint16_t)((unsigned)opaque<<8);
            int left=x;
            if(left<0){bits=(uint16_t)((unsigned)bits<<(-left));left=0;}
            uint32_t packed=(uint32_t)bits<<(8u-(unsigned)(left&7));
            unsigned byte=(unsigned)left>>3;
            for(unsigned j=0;j<3u&&byte+j<32u;++j){
                uint8_t part=(uint8_t)(packed>>(16u-8u*j));
                if(sprite_occupied[y][byte+j]&part)flags|=0x20u;
                sprite_occupied[y][byte+j]|=part;
            }
        }
        if(flags==0x60u)break;
    }
    return flags;
}
