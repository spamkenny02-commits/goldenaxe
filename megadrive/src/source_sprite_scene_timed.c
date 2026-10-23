#include "source_sprite_scene_timed.h"
#ifdef GAW_SCENE_COST_ONLY
#define GAW_SCENE_INLINE inline __attribute__((always_inline))
#else
#define GAW_SCENE_INLINE
#endif
typedef struct {
 SourceClock *clock;u8 *ram;const u8 *bank;SourceClockInterrupt interrupt;void *context;
 SourceSpriteSceneTrace trace;void *trace_context;u16 total;u8 error;
#ifdef GAW_SCENE_COST_ONLY
 u32 cost_tstates,cost_fetches;
#endif
} Scene;
static GAW_SCENE_INLINE u8 step(Scene *s,u16 pc,u16 t,u8 m)
{
#ifdef GAW_SCENE_COST_ONLY
 (void)pc;s->cost_tstates+=t;s->cost_fetches+=m;return 1;
#else
 if(s->error) return 0;
 if(s->trace) {
  if(!s->clock->first && !source_clock_checkpoint(s->clock,s->interrupt,s->context)) return 0;
  if(!s->trace(s->trace_context,pc,s->clock,s->ram)) return 0;
 }
 return source_clock_plain(s->clock,t,m,s->interrupt,s->context);
#endif
}
#define S(pc,t,m) do {if(!step(s,pc,t,m)) return 0;} while(0)
static GAW_SCENE_INLINE u8 get(Scene *s,u16 address)
{
#ifdef GAW_SCENE_COST_ONLY
 if(address<0x8000) return ((const u8 *)s->trace_context)[address];
#endif
 if(address>=0x8000 && address<0xc000) return s->bank[address-0x8000];
 if(address>=0xc000 && address<0xe000) return s->ram[address-0xc000];
 s->error=1;return 0;
}
static GAW_SCENE_INLINE u16 getword(Scene *s,u16 address)
{u16 value=get(s,address);return value|((u16)get(s,address+1)<<8);}
static GAW_SCENE_INLINE void put(Scene *s,u16 address,u8 value)
{
 if(address>=0xc000 && address<0xe000) s->ram[address-0xc000]=value;
 else if(address==0xffff) s->ram[0x1fff]=value;
 else s->error=1;
}
static GAW_SCENE_INLINE void putword(Scene *s,u16 address,u16 value)
{put(s,address,value);put(s,address+1,value>>8);}
static u8 emit(Scene *s,u16 ix)
{
 u16 hl,de,sum,j,count;u8 h,a,l,flag,c,x,y,base;
 S(0x09ee,19,2);h=get(s,ix+9);
 S(0x09f1,19,2);a=get(s,ix+10);
 S(0x09f4,4,1);a*=2;
 S(0x09f5,19,2);sum=(u16)a+get(s,ix+8);a=sum;
 S(0x09f8,sum<256?12:7,1);
 if(sum>=256) {S(0x09fa,4,1);h++;}
 S(0x09fb,4,1);l=a;hl=((u16)h<<8)|l;
 S(0x09fc,7,1);a=get(s,hl);
 S(0x09fd,6,1);hl++;
 S(0x09fe,7,1);h=get(s,hl);
 S(0x09ff,4,1);l=a;hl=((u16)h<<8)|l;
 S(0x0a00,19,2);a=get(s,ix+11);
 S(0x0a03,4,1);a*=2;
 S(0x0a04,4,1);sum=(u16)a+l;a=sum;
 S(0x0a05,4,1);l=a;
 S(0x0a06,sum<256?12:7,1);
 if(sum>=256) {S(0x0a08,4,1);h++;}
 hl=((u16)h<<8)|l;
 S(0x0a09,7,1);a=get(s,hl);
 S(0x0a0a,6,1);hl++;
 S(0x0a0b,7,1);h=get(s,hl);
 S(0x0a0c,4,1);l=a;hl=((u16)h<<8)|l;
 S(0x0a0d,7,1);a=get(s,hl);
 S(0x0a0e,4,1);c=a;
 S(0x0a0f,8,2);c&=127;count=c;
 if(!count || count>64-s->total) return 0;
 S(0x0a11,4,1);flag=a;
 S(0x0a12,6,1);hl++;
 S(0x0a13,7,1);a=get(s,hl);
 S(0x0a14,6,1);hl++;
 S(0x0a15,19,2);put(s,ix+0x1b,a);
 S(0x0a18,7,1);a=get(s,hl);
 S(0x0a19,6,1);hl++;
 S(0x0a1a,19,2);put(s,ix+0x1c,a);
 S(0x0a1d,20,2);de=getword(s,0xc024);
 if(de!=0xdd40+s->total) return 0;
 S(0x0a21,19,2);y=get(s,ix+0x11);
 S(0x0a24,4,1);
 for(j=0;j<count;j++) {
  S(0x0a25,7,1);y+=get(s,hl);
  S(0x0a26,7,1);put(s,de,y);
  S(0x0a27,6,1);hl++;
  S(0x0a28,6,1);de++;
  S(0x0a29,j+1<count?13:8,1);
 }
 S(0x0a2b,20,2);putword(s,0xc024,de);
 S(0x0a2f,20,2);de=getword(s,0xc026);
 if(de!=0xdd80+s->total*2) return 0;
 S(0x0a33,4,1);
 S(0x0a34,4,1);
 S(0x0a35,4,1);
 S(0x0a36,flag&128?12:7,1);
 if(flag&128) {
  S(0x0a50,19,2);x=get(s,ix+0x13);
  for(j=0;j<count;j++) {
   S(0x0a53,7,1);x+=get(s,hl);
   S(0x0a54,7,1);put(s,de,x);
   S(0x0a55,6,1);hl++;
   S(0x0a56,6,1);de++;
   S(0x0a57,16,2);put(s,de++,get(s,hl++));
   S(0x0a59,j+1<count?13:8,1);
  }
  S(0x0a5b,20,2);putword(s,0xc026,de);
  S(0x0a5f,10,1);
 } else {
  S(0x0a38,19,2);x=get(s,ix+0x13);
  S(0x0a3b,19,2);base=get(s,ix+2);
  for(j=0;j<count;j++) {
   S(0x0a3e,7,1);x+=get(s,hl);
   S(0x0a3f,7,1);put(s,de,x);
   S(0x0a40,6,1);hl++;
   S(0x0a41,6,1);de++;
   S(0x0a42,4,1);
   S(0x0a43,7,1);a=get(s,hl);
   S(0x0a44,4,1);a+=base;
   S(0x0a45,7,1);put(s,de,a);
   S(0x0a46,4,1);
   S(0x0a47,6,1);hl++;
   S(0x0a48,6,1);de++;
   S(0x0a49,j+1<count?13:8,1);
  }
  S(0x0a4b,20,2);putword(s,0xc026,de);
  S(0x0a4f,10,1);
 }
 s->total+=count;return !s->error;
}
u8 source_sprite_scene_timed(SourceClock *clock,u8 *ram,const u8 *bank,
 SourceSpriteSceneOutput *output,SourceClockInterrupt interrupt,void *context,
 SourceSpriteSceneTrace trace,void *trace_context)
{
 Scene state,*s=&state;u16 hl,de,ix,iy,n,slot;u8 a,b,c,e,h,l,carry,zero,rotating;
 if(!clock || !ram || !bank || !output) return 0;
 s->clock=clock;s->ram=ram;s->bank=bank;s->interrupt=interrupt;s->context=context;
 s->trace=trace;s->trace_context=trace_context;s->total=s->error=0;
#ifdef GAW_SCENE_COST_ONLY
 s->cost_tstates=s->cost_fetches=0;
#endif
 S(0x0938,13,1);a=get(s,0xc303);
 S(0x093b,7,1);a|=1;
 S(0x093d,13,1);put(s,0xc303,a);
 S(0x0940,17,1);
 S(0x0a60,10,1);hl=0xdd40;
 S(0x0a63,16,1);putword(s,0xc024,hl);
 S(0x0a66,10,1);hl=0xdd80;
 S(0x0a69,16,1);putword(s,0xc026,hl);
 S(0x0a6c,7,1);a=12;
 S(0x0a6e,13,1);put(s,0xffff,a);
 S(0x0a71,10,1);
 S(0x0943,13,1);a=get(s,0xc047);
 S(0x0946,7,1);carry=a<8;
 S(0x0948,!carry?12:7,1);
 rotating=!carry;
 if(carry) {
  S(0x094a,13,1);a=get(s,0xc01b);
  S(0x094d,7,1);a&=64;
  S(0x094f,!a?12:7,1);rotating=a!=0;
 }
 if(rotating) {
  S(0x0951,13,1);a=get(s,0xc02f);
  S(0x0954,7,1);a&=3;
  S(0x0956,4,1);a=(a>>1)|(a<<7);
  S(0x0957,4,1);a=(a>>1)|(a<<7);
  S(0x0958,4,1);a=(a>>1)|(a<<7);
  S(0x0959,4,1);l=a;
  S(0x095a,7,1);h=128;hl=((u16)h<<8)|l;
  S(0x095c,7,1);b=32;
  for(n=0;n<32;n++) {
   S(0x095e,7,1);e=get(s,hl);
   S(0x095f,6,1);hl++;
   S(0x0960,7,1);de=((u16)get(s,hl)<<8)|e;
   S(0x0961,6,1);hl++;
   if(de<0xc300 || de>0xc8d0 || (de-0xc300)%48) return 0;
   S(0x0962,7,1);a=get(s,de);
   S(0x0963,4,1);zero=!a;
   S(0x0964,zero?12:7,1);
   if(!zero) {
    S(0x0966,11,1);
    S(0x0967,14,2);ix=de;
    S(0x0969,20,2);zero=!(get(s,ix+3)&1);
    S(0x096d,zero?12:7,1);
    if(!zero) {
     S(0x096f,11,1);S(0x0970,11,1);S(0x0971,17,1);
     if(!emit(s,ix)) return 0;
     S(0x0974,10,1);S(0x0975,10,1);
    }
   }
   S(0x0976,--b?13:8,1);
  }
 } else {
  S(0x097e,14,2);ix=0xc8d0;
  S(0x0982,14,2);iy=0xd100;
  S(0x0986,10,1);de=0xffd0;
  S(0x0989,10,1);h=0;l=31;
  do {
   S(0x098c,20,2);zero=!(get(s,ix+3)&1);
   S(0x0990,zero?12:7,1);
   if(!zero) {
    S(0x0992,4,1);a=h;
    S(0x0993,4,1);zero=!a;
    S(0x0994,19,2);a=get(s,ix+0x11);
    S(0x0997,4,1);c=l;
    S(0x0998,zero?12:7,1);
    if(!zero) {
     S(0x099a,14,2);iy=0xd100;
     S(0x099e,4,1);b=h;
     do {
      S(0x099f,19,2);carry=a<get(s,iy+64);
      S(0x09a2,carry?12:7,1);
      if(!carry) {
       S(0x09a4,19,2);e=get(s,iy+64);
       S(0x09a7,19,2);put(s,iy+64,a);
       S(0x09aa,4,1);a=e;
       S(0x09ab,19,2);e=get(s,iy);
       S(0x09ae,19,2);put(s,iy,c);
       S(0x09b1,4,1);c=e;
      }
      S(0x09b2,10,2);iy++;
      S(0x09b4,--b?13:8,1);
     } while(b);
    }
    S(0x09b6,4,1);h++;
    S(0x09b7,19,2);put(s,iy+64,a);
    S(0x09ba,19,2);put(s,iy,c);
    S(0x09bd,10,2);iy++;
   }
   S(0x09bf,7,1);e=208;
   S(0x09c1,15,2);ix+=0xff00|e;
   S(0x09c3,4,1);l--;
   S(0x09c4,10,1);
  } while(!(l&128));
  S(0x09c7,19,2);put(s,iy,255);
  S(0x09cb,14,2);iy=0xd100;
  for(n=0;n<=32;n++) {
   S(0x09cf,19,2);a=get(s,iy);
   S(0x09d2,4,1);l=a;
   S(0x09d3,4,1);carry=a&128;a*=2;
   S(0x09d4,10,1);
   if(carry) break;
   if(l>=32) return 0;
   S(0x09d7,4,1);a+=l;
   S(0x09d8,4,1);a*=2;
   S(0x09d9,4,1);l=a;
   S(0x09da,7,1);h=0;hl=l;
   S(0x09dc,11,1);hl*=2;
   S(0x09dd,11,1);hl*=2;
   S(0x09de,11,1);hl*=2;
   S(0x09df,4,1);de=hl;
   S(0x09e0,14,2);ix=0xc300;
   S(0x09e4,15,2);ix+=de;
   S(0x09e6,17,1);
   if(!emit(s,ix)) return 0;
   S(0x09e9,10,2);iy++;
   S(0x09eb,10,1);
  }
  if(n==33) return 0;
 }
 S(0x0978,16,1);hl=getword(s,0xc024);
 S(0x097b,10,1);put(s,hl,208);
 S(0x097d,10,1);
 if(s->error) return 0;
 slot=s->total;output->count=slot;output->y_end=hl;output->xy_end=getword(s,0xc026);
 output->rotating=rotating;output->bank=12;
#ifdef GAW_SCENE_COST_ONLY
 clock->foreground_tstates=s->cost_tstates;clock->foreground_m1=s->cost_fetches;
#endif
 return !s->error;
}
