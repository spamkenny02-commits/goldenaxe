/* Compare portable C flags directly with an independent SMS core's Z80 probe. */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "gaw_video.h"

static uint8_t vram[0x4000],regs[16];
int main(int argc,char **argv){
    if(argc!=2){fprintf(stderr,"Usage: %s observed-status-table\n",argv[0]);return 2;}
    uint8_t observed[1024];
    FILE *input=fopen(argv[1],"rb");
    if(!input){perror(argv[1]);return 2;}
    size_t count=fread(observed,1,sizeof observed,input);
    int extra=fgetc(input);
    int error=ferror(input);
    fclose(input);
    if(count!=sizeof observed||extra!=EOF||error){
        fprintf(stderr,"Expected exactly 1024 observed SMS status bytes\n");return 2;
    }
    regs[0]=4;regs[3]=regs[4]=0xFF;regs[5]=0x7F;
    memset(vram+64,0xFF,64); /* independent fixture's patterns 2/3 */
    vram[0x3F02]=0xD0;
    vram[0x3F80]=vram[0x3F82]=24;
    vram[0x3F81]=3;vram[0x3F83]=2;
    for(unsigned mode=0;mode<4u;++mode)
    for(unsigned y=0;y<256u;++y){
        regs[1]=(uint8_t)(0x40u|mode);
        vram[0x3F00]=vram[0x3F01]=(uint8_t)y;
        uint8_t actual=gaw_video_sprite_status(vram,regs);
        uint8_t expected=observed[mode*256u+y];
        if(actual!=expected){
            fprintf(stderr,"Hardware status mismatch: mode %u, Y %02X, C %02X, SMS %02X\n",
                    mode,y,actual,expected);
            return 1;
        }
    }
    puts("Portable C versus independent SMS hardware collision: OK (1024 observed cases)");
    return 0;
}
