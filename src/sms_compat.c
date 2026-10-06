#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "include/gaw_sms_compat.h"
#include "include/gaw_platform.h"
#include "include/gaw_ram.h"

/* Instruction-compatible C fallback for not-yet-high-level-lifted Z80 paths.
   The opcode stream is immutable source data; all mutable machine state lives
   in this C structure and SMS hardware I/O is routed through the platform API.
   This is deliberately a correctness bridge, not the final high-level form. */
static const uint8_t rom[0x40000] = {
#include "original_rom.inc"
};

enum { FS=0x80,FZ=0x40,FY=0x20,FH=0x10,FX=0x08,FP=0x04,FN=0x02,FC=0x01 };
typedef struct {
    uint8_t a,f,b,c,d,e,h,l,a2,f2,b2,c2,d2,e2,h2,l2,i,r;
    uint16_t ix,iy,sp,pc;
    uint8_t p0,p1,p2,mapper,iff1,iff2,im,halted;
} Z;
static uint32_t faults;
static uint16_t last_fault_pc;
static uint8_t refresh_trace[64];
static unsigned refresh_count;
static uint8_t vdp_ctrl_latch, vdp_ctrl_low;
static uint16_t vdp_addr;
static uint8_t vdp_code;
static uint8_t vdp_regs[16], vdp_vram[0x4000], vdp_cram[0x20], vdp_readbuf, vdp_status;
static uint8_t vdp_tile_dirty[512];
static uint8_t vdp_name_dirty, vdp_sat_dirty;

#if defined(__BYTE_ORDER__) && __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
#define U16_HI_PTR(p) ((uint8_t *)(void *)(p))
#define U16_LO_PTR(p) (((uint8_t *)(void *)(p))+1)
#else
#define U16_HI_PTR(p) (((uint8_t *)(void *)(p))+1)
#define U16_LO_PTR(p) ((uint8_t *)(void *)(p))
#endif

static uint8_t parity(uint8_t v){v^=v>>4;v&=15;return (uint8_t)((0x6996u>>v)&1u)^1u;}
static uint8_t szp(uint8_t v){return (uint8_t)((v&0xA8u)|(v?0:FZ)|(parity(v)?FP:0));}
static uint16_t bc(const Z*z){return (uint16_t)(z->b<<8)|z->c;} static uint16_t de(const Z*z){return (uint16_t)(z->d<<8)|z->e;} static uint16_t hl(const Z*z){return (uint16_t)(z->h<<8)|z->l;}
static void sbc16(Z*z,uint16_t v){z->b=(uint8_t)(v>>8);z->c=(uint8_t)v;} static void sde16(Z*z,uint16_t v){z->d=(uint8_t)(v>>8);z->e=(uint8_t)v;} static void shl16(Z*z,uint16_t v){z->h=(uint8_t)(v>>8);z->l=(uint8_t)v;}
static uint32_t map_phys(const Z*z,uint16_t a){uint8_t bank;uint16_t o;if(a<0x400){bank=0;o=a;}else if(a<0x4000){bank=z->p0;o=a;}else if(a<0x8000){bank=z->p1;o=(uint16_t)(a-0x4000);}else{bank=z->p2;o=(uint16_t)(a-0x8000);}return (uint32_t)bank*0x4000u+o;}
static uint8_t mr(Z*z,uint16_t a){
    if(a>=0xC000u){ if(a>=0xE000u)a=(uint16_t)(0xC000u+(a&0x1FFFu)); return gaw_ram_read8(a); }
    if(a>=0x8000u && (z->mapper&0x08u)){ unsigned page=(z->mapper&0x04u)?0x4000u:0; return gaw_platform_sram_read((uint16_t)(page+(a-0x8000u))); }
    return rom[map_phys(z,a)];
}
static void mw(Z*z,uint16_t a,uint8_t v){
    if(a>=0xFFFCu){ if(a==0xFFFC)z->mapper=v;else if(a==0xFFFD)z->p0=(uint8_t)(v&15u);else if(a==0xFFFE)z->p1=(uint8_t)(v&15u);else z->p2=(uint8_t)(v&15u); return; }
    if(a>=0xC000u){ if(a>=0xE000u)a=(uint16_t)(0xC000u+(a&0x1FFFu)); gaw_ram_write8(a,v); return; }
    if(a>=0x8000u && (z->mapper&0x08u)){unsigned page=(z->mapper&0x04u)?0x4000u:0;gaw_platform_sram_write((uint16_t)(page+(a-0x8000u)),v);}
}
static uint16_t mr16(Z*z,uint16_t a){uint8_t lo=mr(z,a);return (uint16_t)lo|((uint16_t)mr(z,(uint16_t)(a+1u))<<8);} static void mw16(Z*z,uint16_t a,uint16_t v){mw(z,a,(uint8_t)v);mw(z,(uint16_t)(a+1u),(uint8_t)(v>>8));}
static void push(Z*z,uint16_t v){mw(z,--z->sp,(uint8_t)(v>>8));mw(z,--z->sp,(uint8_t)v);} static uint16_t pop(Z*z){uint8_t lo=mr(z,z->sp++);uint8_t hi=mr(z,z->sp++);return (uint16_t)lo|((uint16_t)hi<<8);}

static void vdp_ctrl(uint8_t v){ if(!vdp_ctrl_latch){vdp_ctrl_low=v;vdp_ctrl_latch=1;return;} vdp_ctrl_latch=0; vdp_code=(uint8_t)(v>>6); if(vdp_code==2){unsigned r=v&15u;vdp_regs[r]=vdp_ctrl_low;if(r==2u)vdp_name_dirty=1;if(r==0u||r==1u||r==5u||r==6u)vdp_sat_dirty=1;return;} vdp_addr=(uint16_t)(((uint16_t)(v&0x3Fu)<<8)|vdp_ctrl_low); if(vdp_code==0){vdp_readbuf=vdp_vram[vdp_addr&0x3FFFu];vdp_addr=(uint16_t)((vdp_addr+1u)&0x3FFFu);} }
static void vdp_data_w(uint8_t v){vdp_ctrl_latch=0;if(vdp_code==3)vdp_cram[vdp_addr&31u]=v;else {uint16_t a=(uint16_t)(vdp_addr&0x3FFFu);vdp_vram[a]=v;vdp_tile_dirty[a>>5]=1;uint16_t nt=(uint16_t)((vdp_regs[2]&0x0Eu)<<10);if(a>=nt&&a<(uint16_t)(nt+0x0700u))vdp_name_dirty=1;uint16_t sat=(uint16_t)((vdp_regs[5]&0x7Eu)<<7);if(a>=sat&&a<(uint16_t)(sat+0x0100u))vdp_sat_dirty=1;}vdp_addr=(uint16_t)((vdp_addr+1u)&0x3FFFu);}
static uint8_t vdp_data_r(void){uint8_t v=vdp_readbuf;vdp_readbuf=vdp_vram[vdp_addr&0x3FFFu];vdp_addr=(uint16_t)((vdp_addr+1u)&0x3FFFu);vdp_ctrl_latch=0;return v;}
void gaw_sms_vdp_control_write(uint8_t value){vdp_ctrl(value);}
void gaw_sms_vdp_data_write(uint8_t value){vdp_data_w(value);}
uint8_t gaw_sms_vdp_data_read(void){return vdp_data_r();}
static uint8_t inport(Z*z,uint8_t p){(void)z;if(p==0xBE)return vdp_data_r();if(p==0xBF){
    /* SMS VDP status is hardware state, not RAM_C01B. Reading $BF
       acknowledges/clears the pending status flags; the IRQ handler itself
       copies the returned value to C01B. */
    uint8_t status=vdp_status; vdp_status=0; vdp_ctrl_latch=0; return status;
}if(p==0xDC)return (uint8_t)(~gaw_platform_read_pad_sms_bits());if(p==0xDD)return 0xFF;if(p==0x7E)return 0x78;if(p==0x7F)return 0x40;return 0xFF;}
static void outport(Z*z,uint8_t p,uint8_t v){(void)z;if(p==0xBE)vdp_data_w(v);else if(p==0xBF)vdp_ctrl(v);else if(p==0x7F)gaw_platform_audio_command(v);}

static uint8_t add8(Z*z,uint8_t a,uint8_t b,uint8_t cy){uint16_t r=(uint16_t)a+b+cy;uint8_t q=(uint8_t)r;z->f=(uint8_t)((q&0xA8u)|(q?0:FZ)|(((a^b^q)&0x10)?FH:0)|((~(a^b)&(a^q)&0x80)?FP:0)|(r>255?FC:0));return q;}
static uint8_t sub8(Z*z,uint8_t a,uint8_t b,uint8_t cy){uint16_t r=(uint16_t)a-b-cy;uint8_t q=(uint8_t)r;z->f=(uint8_t)(FN|(q&0xA8u)|(q?0:FZ)|(((a^b^q)&0x10)?FH:0)|(((a^b)&(a^q)&0x80)?FP:0)|((r&0x100)?FC:0));return q;}
static uint8_t inc8(Z*z,uint8_t a){uint8_t c=z->f&FC,q=(uint8_t)(a+1u);z->f=(uint8_t)(c|(q&0xA8u)|(q?0:FZ)|((a&15u)==15u?FH:0)|(a==0x7F?FP:0));return q;}
static uint8_t dec8(Z*z,uint8_t a){uint8_t c=z->f&FC,q=(uint8_t)(a-1u);z->f=(uint8_t)(c|FN|(q&0xA8u)|(q?0:FZ)|((a&15u)==0?FH:0)|(a==0x80?FP:0));return q;}
static int cond(const Z*z,unsigned y){switch(y&7u){case 0:return !(z->f&FZ);case 1:return !!(z->f&FZ);case 2:return !(z->f&FC);case 3:return !!(z->f&FC);case 4:return !(z->f&FP);case 5:return !!(z->f&FP);case 6:return !(z->f&FS);default:return !!(z->f&FS);}}
static uint8_t *r8p(Z*z,unsigned n,uint16_t *memaddr,int idxmode,int8_t disp){*memaddr=0;switch(n){case 0:return &z->b;case 1:return &z->c;case 2:return &z->d;case 3:return &z->e;case 4:if(idxmode==1)return U16_HI_PTR(&z->ix);if(idxmode==2)return U16_HI_PTR(&z->iy);return &z->h;case 5:if(idxmode==1)return U16_LO_PTR(&z->ix);if(idxmode==2)return U16_LO_PTR(&z->iy);return &z->l;case 6:*memaddr=(uint16_t)((idxmode==1?z->ix:idxmode==2?z->iy:hl(z))+(idxmode?disp:0));return NULL;default:return &z->a;}}
static uint16_t get16(Z*z,unsigned p,int idx){if(p==0)return bc(z);if(p==1)return de(z);if(p==2)return idx==1?z->ix:idx==2?z->iy:hl(z);return z->sp;}
static void set16(Z*z,unsigned p,int idx,uint16_t v){if(p==0)sbc16(z,v);else if(p==1)sde16(z,v);else if(p==2){if(idx==1)z->ix=v;else if(idx==2)z->iy=v;else shl16(z,v);}else z->sp=v;}
static uint8_t fetch(Z*z){uint8_t v=mr(z,z->pc);z->pc++;z->r=(uint8_t)((z->r&0x80u)|((z->r+1u)&0x7Fu));return v;} static uint16_t fetch16(Z*z){uint8_t lo=fetch(z),hi=fetch(z);return (uint16_t)lo|((uint16_t)hi<<8);}

static void cbop(Z*z,uint8_t op,int idx,int8_t disp){unsigned x=op>>6,y=(op>>3)&7u,r=op&7u;uint16_t ma=0;uint8_t *rp;uint8_t v;if(idx){ma=(uint16_t)((idx==1?z->ix:z->iy)+disp);v=mr(z,ma);}else{rp=r8p(z,r,&ma,0,0);v=rp?*rp:mr(z,ma);}if(x==0){uint8_t c=0,q=v;switch(y){case 0:c=v>>7;q=(uint8_t)((v<<1)|c);break;case 1:c=v&1;q=(uint8_t)((v>>1)|(c<<7));break;case 2:c=v>>7;q=(uint8_t)((v<<1)|((z->f&FC)?1:0));break;case 3:c=v&1;q=(uint8_t)((v>>1)|((z->f&FC)?0x80:0));break;case 4:c=v>>7;q=(uint8_t)(v<<1);break;case 5:c=v&1;q=(uint8_t)((v>>1)|(v&0x80));break;case 6:c=v>>7;q=(uint8_t)((v<<1)|1);break;default:c=v&1;q=(uint8_t)(v>>1);break;}z->f=(uint8_t)(szp(q)|(c?FC:0));if(ma)mw(z,ma,q);else *r8p(z,r,&ma,0,0)=q;if(idx&&r!=6){uint16_t dummy=0;uint8_t *d=r8p(z,r,&dummy,0,0);if(d)*d=q;}}else if(x==1){z->f=(uint8_t)((z->f&FC)|FH|(v&(FY|FX))|((v&(1u<<y))?0:(FZ|FP))|((y==7&&(v&0x80))?FS:0));}else{uint8_t q=(x==2)?(uint8_t)(v&~(1u<<y)):(uint8_t)(v|(1u<<y));if(ma)mw(z,ma,q);else *r8p(z,r,&ma,0,0)=q;if(idx&&r!=6){uint16_t dummy=0;uint8_t*d=r8p(z,r,&dummy,0,0);if(d)*d=q;}}}

static void edop(Z*z,uint8_t op){unsigned x=op>>6,y=(op>>3)&7u,zz=op&7u,p=y>>1,q=y&1u;if(x==1){if(zz==0){uint8_t v=inport(z,z->c);if(y!=6){uint16_t m=0;uint8_t*r=r8p(z,y,&m,0,0);if(r)*r=v;}z->f=(uint8_t)((z->f&FC)|szp(v));}else if(zz==1){uint8_t v=0;if(y!=6){uint16_t m=0;uint8_t*r=r8p(z,y,&m,0,0);v=r?*r:mr(z,m);}outport(z,z->c,v);}else if(zz==2){uint16_t a=hl(z),b=get16(z,p,0);uint32_t r;if(q){r=(uint32_t)a+b+((z->f&FC)?1:0);uint16_t w=(uint16_t)r;z->f=(uint8_t)((w>>8)&0xA8u);if(!w)z->f|=FZ;if(((a^b^w)&0x1000u))z->f|=FH;if((~(a^b)&(a^w)&0x8000u))z->f|=FP;if(r>0xFFFFu)z->f|=FC;shl16(z,w);}else{r=(uint32_t)a-b-((z->f&FC)?1:0);uint16_t w=(uint16_t)r;z->f=(uint8_t)(FN|((w>>8)&0xA8u));if(!w)z->f|=FZ;if((a^b^w)&0x1000u)z->f|=FH;if((a^b)&(a^w)&0x8000u)z->f|=FP;if(r&0x10000u)z->f|=FC;shl16(z,w);}}else if(zz==3){uint16_t a=fetch16(z);if(q){set16(z,p,0,mr16(z,a));}else mw16(z,a,get16(z,p,0));}else if(zz==4){z->a=sub8(z,0,z->a,0);}else if(zz==5){z->pc=pop(z);z->iff1=z->iff2;}else if(zz==6){static const uint8_t imv[8]={0,0,1,2,0,0,1,2};z->im=imv[y];}else{switch(y){case 0:z->i=z->a;break;case 1:z->r=z->a;break;case 2:z->a=z->i;z->f=(uint8_t)((z->f&FC)|(z->a&0xA8u)|(z->a?0:FZ)|(z->iff2?FP:0));break;case 3:z->a=z->r;if(refresh_count<64u)refresh_trace[refresh_count++]=z->r;z->f=(uint8_t)((z->f&FC)|(z->a&0xA8u)|(z->a?0:FZ)|(z->iff2?FP:0));break;default:break;}}return;}
 if(x==2 && y>=4 && zz<=3){int dec=(y&1u);int rep=(y>=6);uint16_t h=hl(z),d=de(z),b=bc(z);uint8_t v;if(zz==0){v=mr(z,h);mw(z,d,v);h=(uint16_t)(h+(dec?-1:1));d=(uint16_t)(d+(dec?-1:1));b--;shl16(z,h);sde16(z,d);sbc16(z,b);z->f=(uint8_t)((z->f&(FS|FZ|FC))|(b?FP:0)|(((z->a+v)&2)?FY:0)|(((z->a+v)&8)?FX:0));if(rep&&b)z->pc=(uint16_t)(z->pc-2u);}else if(zz==1){v=mr(z,h);uint8_t r=sub8(z,z->a,v,0);uint8_t c=z->f&FC;h=(uint16_t)(h+(dec?-1:1));b--;shl16(z,h);sbc16(z,b);z->f=(uint8_t)((z->f&~FP)|(b?FP:0)|c);(void)r;if(rep&&b&&!(z->f&FZ))z->pc=(uint16_t)(z->pc-2u);}else if(zz==2){v=inport(z,z->c);mw(z,h,v);h=(uint16_t)(h+(dec?-1:1));z->b--;shl16(z,h);z->f=(uint8_t)((z->b?0:FZ)|FN);if(rep&&z->b)z->pc=(uint16_t)(z->pc-2u);}else{v=mr(z,h);outport(z,z->c,v);h=(uint16_t)(h+(dec?-1:1));z->b--;shl16(z,h);z->f=(uint8_t)((z->b?0:FZ)|FN);if(rep&&z->b)z->pc=(uint16_t)(z->pc-2u);} }
}

static void daa(Z*z){uint8_t a=z->a,adj=0,c=z->f&FC;if((z->f&FH)||(!(z->f&FN)&&(a&15u)>9))adj|=6;if(c||(!(z->f&FN)&&a>0x99)){adj|=0x60;c=FC;}uint8_t old=a;a=(z->f&FN)?(uint8_t)(a-adj):(uint8_t)(a+adj);z->a=a;z->f=(uint8_t)((z->f&FN)|c|(a&0xA8u)|(a?0:FZ)|(parity(a)?FP:0)|(((old^a)&0x10)?FH:0));}

static void step(Z*z){int idx=0;uint8_t op=fetch(z);while(op==0xDD||op==0xFD){idx=(op==0xDD)?1:2;op=fetch(z);}if(op==0xCB){int8_t d=0;if(idx)d=(int8_t)fetch(z);cbop(z,fetch(z),idx,d);return;}if(op==0xED){edop(z,fetch(z));return;}unsigned x=op>>6,y=(op>>3)&7u,zz=op&7u,p=y>>1,q=y&1u;int8_t disp=0;int needdisp=idx && ((x==1&&(y==6||zz==6))||(x==2&&zz==6)||(x==0&&zz>=4&&zz<=6&&y==6));if(needdisp)disp=(int8_t)fetch(z);
 if(x==0){if(zz==0){if(y==0)return;if(y==1){uint8_t a=z->a,f=z->f;z->a=z->a2;z->f=z->f2;z->a2=a;z->f2=f;return;}if(y==2){int8_t d=(int8_t)fetch(z);z->b--;if(z->b)z->pc=(uint16_t)(z->pc+d);return;}if(y==3){int8_t d=(int8_t)fetch(z);z->pc=(uint16_t)(z->pc+d);return;}int8_t d=(int8_t)fetch(z);if(cond(z,y-4))z->pc=(uint16_t)(z->pc+d);return;}if(zz==1){if(!q)set16(z,p,idx,fetch16(z));else{uint16_t a=idx==1?z->ix:idx==2?z->iy:hl(z),b=get16(z,p,idx);uint32_t r=(uint32_t)a+b;uint16_t w=(uint16_t)r;z->f=(uint8_t)((z->f&(FS|FZ|FP))|((w>>8)&0x28u)|(((a^b^w)&0x1000u)?FH:0)|(r>0xFFFFu?FC:0));if(idx==1)z->ix=w;else if(idx==2)z->iy=w;else shl16(z,w);}return;}if(zz==2){if(!q){if(p==0)mw(z,bc(z),z->a);else if(p==1)mw(z,de(z),z->a);else if(p==2){uint16_t a=fetch16(z);mw16(z,a,get16(z,2,idx));}else{uint16_t a=fetch16(z);mw(z,a,z->a);}}else{if(p==0)z->a=mr(z,bc(z));else if(p==1)z->a=mr(z,de(z));else if(p==2){uint16_t a=fetch16(z);set16(z,2,idx,mr16(z,a));}else{uint16_t a=fetch16(z);z->a=mr(z,a);}}return;}if(zz==3){uint16_t v=get16(z,p,idx);set16(z,p,idx,(uint16_t)(v+(q?-1:1)));return;}if(zz>=4&&zz<=6){uint16_t ma=0;uint8_t*rp=r8p(z,y,&ma,idx,disp);if(zz==4){uint8_t v=rp?*rp:mr(z,ma);v=inc8(z,v);if(rp)*rp=v;else mw(z,ma,v);}else if(zz==5){uint8_t v=rp?*rp:mr(z,ma);v=dec8(z,v);if(rp)*rp=v;else mw(z,ma,v);}else{uint8_t v=fetch(z);if(rp)*rp=v;else mw(z,ma,v);}return;}switch(y){case 0:{uint8_t c=z->a>>7;z->a=(uint8_t)((z->a<<1)|c);z->f=(uint8_t)((z->f&(FS|FZ|FP))|(z->a&0x28u)|(c?FC:0));break;}case 1:{uint8_t c=z->a&1;z->a=(uint8_t)((z->a>>1)|(c<<7));z->f=(uint8_t)((z->f&(FS|FZ|FP))|(z->a&0x28u)|(c?FC:0));break;}case 2:{uint8_t c=z->a>>7;z->a=(uint8_t)((z->a<<1)|((z->f&FC)?1:0));z->f=(uint8_t)((z->f&(FS|FZ|FP))|(z->a&0x28u)|(c?FC:0));break;}case 3:{uint8_t c=z->a&1;z->a=(uint8_t)((z->a>>1)|((z->f&FC)?0x80:0));z->f=(uint8_t)((z->f&(FS|FZ|FP))|(z->a&0x28u)|(c?FC:0));break;}case 4:daa(z);break;case 5:z->a^=0xFF;z->f=(uint8_t)((z->f&(FS|FZ|FP|FC))|FH|FN|(z->a&0x28u));break;case 6:z->f=(uint8_t)((z->f&(FS|FZ|FP))|FC|(z->a&0x28u));break;default:{uint8_t c=z->f&FC;z->f=(uint8_t)((z->f&(FS|FZ|FP))|(z->a&0x28u)|(c?FH:0)|(c?0:FC));break;}}return;}
 if(x==1){if(y==6&&zz==6){z->halted=1;gaw_platform_wait_vblank();z->halted=0;return;}uint16_t ma1=0,ma2=0;uint8_t*dst,*src;uint8_t v;if(idx&&(y==6||zz==6)){uint16_t ma=(uint16_t)((idx==1?z->ix:z->iy)+disp);if(zz==6)v=mr(z,ma);else{src=r8p(z,zz,&ma2,0,0);v=src?*src:mr(z,ma2);}if(y==6)mw(z,ma,v);else{dst=r8p(z,y,&ma1,0,0);if(dst)*dst=v;else mw(z,ma1,v);}}else{src=r8p(z,zz,&ma2,idx,0);v=src?*src:mr(z,ma2);dst=r8p(z,y,&ma1,idx,0);if(dst)*dst=v;else mw(z,ma1,v);}return;}
 if(x==2){uint16_t ma=0;uint8_t*rp=r8p(z,zz,&ma,idx,disp);uint8_t v=rp?*rp:mr(z,ma);switch(y){case 0:z->a=add8(z,z->a,v,0);break;case 1:z->a=add8(z,z->a,v,(z->f&FC)?1:0);break;case 2:z->a=sub8(z,z->a,v,0);break;case 3:z->a=sub8(z,z->a,v,(z->f&FC)?1:0);break;case 4:z->a&=v;z->f=(uint8_t)(szp(z->a)|FH);break;case 5:z->a^=v;z->f=szp(z->a);break;case 6:z->a|=v;z->f=szp(z->a);break;default:(void)sub8(z,z->a,v,0);break;}return;}
 if(zz==0){if(cond(z,y))z->pc=pop(z);return;}if(zz==1){if(!q){uint16_t v=pop(z);if(p==0)sbc16(z,v);else if(p==1)sde16(z,v);else if(p==2){if(idx==1)z->ix=v;else if(idx==2)z->iy=v;else shl16(z,v);}else{z->a=(uint8_t)(v>>8);z->f=(uint8_t)v;}}else{if(p==0)z->pc=pop(z);else if(p==1){uint8_t b=z->b,c=z->c,d=z->d,e=z->e,h=z->h,l=z->l;z->b=z->b2;z->c=z->c2;z->d=z->d2;z->e=z->e2;z->h=z->h2;z->l=z->l2;z->b2=b;z->c2=c;z->d2=d;z->e2=e;z->h2=h;z->l2=l;}else if(p==2)z->pc=idx==1?z->ix:idx==2?z->iy:hl(z);else z->sp=idx==1?z->ix:idx==2?z->iy:hl(z);}return;}if(zz==2){uint16_t a=fetch16(z);if(cond(z,y))z->pc=a;return;}if(zz==3){if(y==0){z->pc=fetch16(z);return;}if(y==2){uint8_t p8=fetch(z);outport(z,p8,z->a);return;}if(y==3){uint8_t p8=fetch(z);z->a=inport(z,p8);return;}if(y==4){uint16_t t=mr16(z,z->sp),v=idx==1?z->ix:idx==2?z->iy:hl(z);mw16(z,z->sp,v);if(idx==1)z->ix=t;else if(idx==2)z->iy=t;else shl16(z,t);return;}if(y==5){uint16_t t=de(z);sde16(z,hl(z));shl16(z,t);return;}if(y==6){z->iff1=z->iff2=0;return;}if(y==7){z->iff1=z->iff2=1;return;}}
 if(zz==4){uint16_t a=fetch16(z);if(cond(z,y)){push(z,z->pc);z->pc=a;}return;}if(zz==5){if(!q){uint16_t v=p==0?bc(z):p==1?de(z):p==2?(idx==1?z->ix:idx==2?z->iy:hl(z)):(uint16_t)((z->a<<8)|z->f);push(z,v);}else if(p==0){uint16_t a=fetch16(z);push(z,z->pc);z->pc=a;}return;}if(zz==6){uint8_t v=fetch(z);switch(y){case 0:z->a=add8(z,z->a,v,0);break;case 1:z->a=add8(z,z->a,v,(z->f&FC)?1:0);break;case 2:z->a=sub8(z,z->a,v,0);break;case 3:z->a=sub8(z,z->a,v,(z->f&FC)?1:0);break;case 4:z->a&=v;z->f=(uint8_t)(szp(z->a)|FH);break;case 5:z->a^=v;z->f=szp(z->a);break;case 6:z->a|=v;z->f=szp(z->a);break;default:(void)sub8(z,z->a,v,0);break;}return;}push(z,z->pc);z->pc=(uint16_t)(y*8u);
}

/* Native lift of $0327/$032A: four-plane resource decompressor used heavily
   during boot and scene changes.  Expressing it directly avoids carrying the
   original routine's temporary stack discipline into the compatibility core. */
static void native_032a(Z *z,int set_bank){
    if(set_bank) z->p2=(uint8_t)(z->a&15u);
    uint16_t src=hl(z),base=de(z),last=base;
    for(unsigned plane=0;plane<4u;++plane){
        uint16_t dst=(uint16_t)(base+plane);
        for(;;){
            uint8_t cmd=mr(z,src++); if(cmd==0) break;
            unsigned n=cmd&0x7Fu; int literal=(cmd&0x80u)!=0; uint8_t value=0;
            if(!literal) value=mr(z,src++);
            while(n--){
                if(literal) value=mr(z,src++);
                vdp_addr=(uint16_t)(dst&0x3FFFu); vdp_code=1; vdp_data_w(value);
                dst=(uint16_t)(dst+4u);
            }
        }
        last=dst;
    }
    shl16(z,src); z->b=0; z->c=4; uint16_t rv=(uint16_t)(last+1u); uint8_t lo=sub8(z,(uint8_t)rv,4,0); z->a=lo; z->d=(uint8_t)((rv>>8)-((uint8_t)rv<4u?1u:0u)); z->e=lo;
}

static int run(uint8_t bank,uint16_t addr,uint16_t ix,uint8_t world,
               uint16_t arg_hl,uint16_t arg_de,uint16_t arg_bc,uint8_t arg_a){
    Z z; memset(&z,0,sizeof z); z.p0=0; z.p1=1; z.p2=bank; z.sp=0xDFF0; z.pc=addr; z.ix=ix;
    refresh_count=0;
    shl16(&z,arg_hl);sde16(&z,arg_de);sbc16(&z,arg_bc);z.a=arg_a;
    if(world) z.e=gaw_ram_read8(0xC0A6);
    push(&z,0xFFFF);
    unsigned steps_since_sync=0;
    for(;;){
        if(z.pc==0xFFFF) return 1;
        if(++steps_since_sync>2000000u){ last_fault_pc=z.pc; faults++; return 0; }
        if(z.pc==0x0327u || z.pc==0x032Au){ int sb=(z.pc==0x0327u); native_032a(&z,sb); z.pc=pop(&z); continue; }
        /* $0B95 is the game's synchronous VBlank barrier.  The portable
           platform boundary already performs the frame tick, so executing
           the original IRQ body as well would double-apply the interrupt
           side effects and corrupt its saved-register stack. */
        if(z.pc==0x0B95u){
            gaw_platform_wait_vblank(); vdp_status|=0x80u; steps_since_sync=0; z.pc=pop(&z); continue;
        }
        step(&z);
    }
}
void gaw_sms_compat_reset(void){memset(vdp_regs,0,sizeof vdp_regs);memset(vdp_vram,0,sizeof vdp_vram);memset(vdp_cram,0,sizeof vdp_cram);memset(vdp_tile_dirty,1,sizeof vdp_tile_dirty);vdp_name_dirty=vdp_sat_dirty=1;vdp_ctrl_latch=0;vdp_addr=0;vdp_code=0;vdp_status=0;faults=0;last_fault_pc=0;}
int gaw_sms_compat_call(uint8_t bank,uint16_t addr){return run(bank,addr,0,0,0,0,0,0);}
int gaw_sms_compat_call_args(uint8_t bank,uint16_t addr,uint16_t h,uint16_t d,uint16_t b,uint8_t a){return run(bank,addr,0,0,h,d,b,a);}
int gaw_sms_compat_entity_call(uint8_t bank,uint16_t addr,GawEntity*e){return run(bank,addr,gaw_entity_addr(e),0,0,0,0,0);}
int gaw_sms_compat_world_call(uint8_t bank,uint16_t addr){return run(bank,addr,0,1,0,0,0,0);}
uint32_t gaw_sms_compat_faults(void){return faults;}
uint16_t gaw_sms_compat_last_pc(void){return last_fault_pc;}
unsigned gaw_sms_compat_refresh_trace(uint8_t *values,unsigned capacity){unsigned n=refresh_count<capacity?refresh_count:capacity;if(n)memcpy(values,refresh_trace,n);return refresh_count;}
const uint8_t *gaw_sms_vram(void){return vdp_vram;}
const uint8_t *gaw_sms_cram(void){return vdp_cram;}
const uint8_t *gaw_sms_vdp_regs(void){return vdp_regs;}
int gaw_sms_take_tile_dirty(unsigned tile){if(tile>=512||!vdp_tile_dirty[tile])return 0;vdp_tile_dirty[tile]=0;return 1;}
void gaw_sms_mark_all_tiles_dirty(void){memset(vdp_tile_dirty,1,sizeof vdp_tile_dirty);}

int gaw_sms_take_name_dirty(void){int v=vdp_name_dirty;vdp_name_dirty=0;return v;}
int gaw_sms_take_sat_dirty(void){int v=vdp_sat_dirty;vdp_sat_dirty=0;return v;}

uint8_t gaw_sms_rom_bank_read(uint8_t bank,uint16_t cpu_addr){return rom[(uint32_t)(bank&15u)*0x4000u+(cpu_addr&0x3FFFu)];}
