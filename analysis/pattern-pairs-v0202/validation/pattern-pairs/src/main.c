#include <genesis.h>
#include "../../../megadrive/src/pattern_convert.h"
u32 sweep(void);u32 check(const u8*,const u32*,u16);void old_convert(const u8*,u32*,u16,u16);
static u8 pixels[16384] __attribute__((aligned(2)));static u32 output[4096];
volatile u32 gaw_pair_failures,gaw_pair_old,gaw_pair_new;volatile u16 gaw_pair_done;
int main(bool hard_reset)
{
 u16 n,repeat;u32 start;VDP_setEnable(FALSE);VDP_setVInterrupt(TRUE);SYS_enableInts();
 gaw_pair_failures=sweep();
 for(n=0;n<16384;n++) pixels[n]=(n*73+(n>>7))&255;
 SYS_doVBlankProcess();start=vtimer;
 for(repeat=0;repeat<32;repeat++) {old_convert(pixels,output,0,512);__asm__ volatile("":::"memory");}
 gaw_pair_old=vtimer-start;gaw_pair_failures+=check(pixels,output,4096);
 SYS_doVBlankProcess();start=vtimer;
 for(repeat=0;repeat<32;repeat++) {pattern_convert(pixels,output,4096);__asm__ volatile("":::"memory");}
 gaw_pair_new=vtimer-start;gaw_pair_failures+=check(pixels,output,4096);
 gaw_pair_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
