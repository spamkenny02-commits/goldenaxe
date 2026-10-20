#include "source_sms_sprite8.h"
u8 source_sms_sprite8_prepare(SourceSmsSprite8 *f,const u8 *sat,u8 reg0,u8 reg1,u8 reg6,u16 base)
{
    u8 used[192];u16 n,r,c,count=0;u32 columns;s16 x,y,line,column;
    if(!f || !sat || !(reg0&4) || (reg1&0x1b) || base>1984) return SOURCE_SMS_SPRITE8_INVALID;
    for(n=0;n<192;n++) used[n]=0;
    for(n=0;n<64;n++) {
        f->columns[n]=0;f->source_tile[n]=0;f->rows[n]=0;
        for(c=0;c<4;c++) f->sat[n*4+c]=0;
    }
    f->tile_base=base;f->overflow=0;
    for(n=0;n<64 && sat[n]!=208;n++) {
        y=(s16)sat[n]+1;if(sat[n]>208) y-=256;
        x=(s16)sat[64+n*2]-(reg0&8?8:0);columns=0;
        for(c=0;c<8;c++) {column=x+(s16)c;if(column>=0 && column<256 && (!(reg0&32) || column>=8)) columns|=15UL<<((7-c)*4); }
        f->columns[n]=columns;
        f->source_tile[n]=(reg6&4?256:0)+sat[65+n*2];
        for(r=0;r<8;r++) {
            line=y+(s16)r;
            if(line>=0 && line<192) {
                if(used[line]<8) f->rows[n]|=1<<r;else f->overflow=1;
                used[line]++;
            }
        }
        f->sat[n*4]=(y+144)&511;f->sat[n*4+1]=n+1;
        f->sat[n*4+2]=0x2000|(base+n);f->sat[n*4+3]=(x+128)&511;
        count++;
    }
    f->count=count;if(count) f->sat[(count-1)*4+1]=0;
    return SOURCE_SMS_SPRITE8_OK;
}
u8 source_sms_sprite8_tile(const SourceSmsSprite8 *f,const u32 *patterns,u16 index,u32 *out)
{
    u16 row,tile;
    if(!f || !patterns || !out || f->count>64 || index>=f->count) return SOURCE_SMS_SPRITE8_INVALID;
    tile=f->source_tile[index];if(tile>=512) return SOURCE_SMS_SPRITE8_INVALID;
    for(row=0;row<8;row++) out[row]=(f->rows[index]&(1<<row))?patterns[tile*8+row]&f->columns[index]:0;
    return SOURCE_SMS_SPRITE8_OK;
}
