/* SGDK has no memmove: retain the explicit backward insertion loops. */
#pragma GCC optimize ("O3","no-tree-loop-distribute-patterns")
#include "source_sprite_scene_cost.h"
#ifdef SGDK_GCC
#include <memory.h>
#endif
static inline __attribute__((always_inline)) u8 byte_at(const u8 *ram,const u8 *bank,const u8 *low,u16 address)
{
 if(address<0x8000) return low[address];
 if(address<0xc000) return bank[address-0x8000];
 return address<0xe000?ram[address-0xc000]:0;
}
static inline __attribute__((always_inline)) u16 word_at(const u8 *ram,const u8 *bank,const u8 *low,u16 address)
{return byte_at(ram,bank,low,address)|((u16)byte_at(ram,bank,low,address+1)<<8);}
/* Original entity addresses are48-byte records; avoid software division. */
static const u8 entity_slot_by_16[]={0,255,255,1,255,255,2,255,255,3,255,255,4,255,255,5,255,255,6,255,255,7,255,255,8,255,255,9,255,255,10,255,255,11,255,255,12,255,255,13,255,255,14,255,255,15,255,255,16,255,255,17,255,255,18,255,255,19,255,255,20,255,255,21,255,255,22,255,255,23,255,255,24,255,255,25,255,255,26,255,255,27,255,255,28,255,255,29,255,255,30,255,255,31};
u8 source_sprite_scene_tstates(u8 *ram,const u8 *bank,const u8 *low,
 u32 *tstates,SourceSpriteSceneOutput *output)
{
 u8 order[32],sorted[128],sat[192];u16 active=0,total=0,n,j,k,slot,start;
 u32 cost=152;u8 rotating;
 if(!ram || !bank || !low || !tstates || !output) return 0;
 __builtin_memcpy(sorted,ram+0x1100,128);__builtin_memcpy(sat,ram+0x1d40,192);
 ram[0x303]|=1;ram[0x1fff]=12;
 rotating=ram[0x47]>=8;
 cost+=rotating?12:7;
 if(!rotating) {rotating=(ram[0x1b]&64)!=0;cost+=13+7+(rotating?7:12);}
 if(rotating)
 {
  start=(ram[0x2f]&3)*32;cost+=50+32*62-5;
  for(n=0;n<32;n++)
  {
   u16 address=word_at(ram,bank,low,0x8000+start+n*2);u8 *e;
   if(address<0xc300 || address>0xc8d0 || ((address-0xc300)&15)) return 0;
   slot=entity_slot_by_16[(address-0xc300)>>4];if(slot==255) return 0;e=ram+0x300+slot*48;
   if(!e[0]) continue;
   if(!(e[3]&1)) {cost+=52;continue;}
   cost+=106;order[active++]=slot;
  }
  cost+=36;
 }
 else
 {
  cost+=48+106;
  for(n=32;n>0;n--)
  {
   u8 y;slot=n-1;
   if(!(ram[0x303+slot*48]&1)) {cost+=68;continue;}
   y=ram[0x311+slot*48];j=0;
   while(j<active && y<sorted[64+j]) j++;
   cost+=active?166+(u32)active*54+(u32)(active-j)*79:158;
   for(k=active;k>j;k--) {sorted[k]=sorted[k-1];sorted[64+k]=sorted[63+k];}
   sorted[j]=slot;sorted[64+j]=y;active++;
  }
  sorted[active]=255;
  for(n=0;n<active;n++) order[n]=sorted[n];
  __builtin_memcpy(ram+0x1100,sorted,128);
  cost+=(u32)active*159;
 }
 for(n=0;n<active;n++)
 {
  u8 *e=ram+0x300+order[n]*48;u16 address=e[8]|((u16)e[9]<<8),sum,pointer,count;
  u8 flag,x=e[0x13],y=e[0x11],base;
  sum=(address&255)+(u8)(e[10]*2);if(sum>=256) cost--;
  pointer=word_at(ram,bank,low,address+(u8)(e[10]*2));
  sum=(pointer&255)+(u8)(e[11]*2);if(sum>=256) cost--;
  pointer=word_at(ram,bank,low,pointer+(u8)(e[11]*2));
  if(pointer>=0xe000) return 0;
  flag=byte_at(ram,bank,low,pointer);count=flag&127;
  if(!count || count>64-total || (u32)pointer+3+count*3>0xe000) return 0;
  e[0x1b]=byte_at(ram,bank,low,pointer+1);e[0x1c]=byte_at(ram,bank,low,pointer+2);
  base=(flag&128)?0:e[2];cost+=(flag&128)?407+(u32)count*94:421+(u32)count*116;
  for(j=0;j<count;j++)
  {
   y+=byte_at(ram,bank,low,pointer+3+j);x+=byte_at(ram,bank,low,pointer+3+count+j*2);
   sat[total+j]=y;sat[64+(total+j)*2]=x;
   sat[65+(total+j)*2]=base+byte_at(ram,bank,low,pointer+4+count+j*2);
  }
  total+=count;
 }
 sat[total]=208;__builtin_memcpy(ram+0x1d40,sat,192);
 output->count=total;output->y_end=0xdd40+total;output->xy_end=0xdd80+total*2;
 output->rotating=rotating;output->bank=12;
 ram[0x24]=output->y_end;ram[0x25]=output->y_end>>8;ram[0x26]=output->xy_end;ram[0x27]=output->xy_end>>8;
 *tstates=cost;return 1;
}
