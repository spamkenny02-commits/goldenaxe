#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_core.h"
#include "gaw_entity.h"
#include "gaw_player.h"
#include "gaw_host.h"
#include "gaw_platform.h"
#include "gaw_ram.h"
#include "gaw_recompiled.h"
#include "gaw_sms_compat.h"
#include "gaw_world.h"

static void reset_full(void){ memset(gaw_ram,0,sizeof gaw_ram); gaw_sms_compat_reset(); gaw_host_set_entropy(0x5A); }





static void compare_native_world_callback_full(uint16_t target,uint16_t cell){uint8_t n[sizeof gaw_ram],c[sizeof gaw_ram];
 reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,cell);gaw_ram_write8(0xC040,0);gaw_ram_write8(0xC0A2,0);gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC0F1,1);gaw_ram_write8(0xC318,0x18);assert(gaw_world_native_callback(target)==1);memcpy(n,gaw_ram,sizeof n);
 reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,cell);gaw_ram_write8(0xC040,0);gaw_ram_write8(0xC0A2,0);gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC0F1,1);gaw_ram_write8(0xC318,0x18);gaw_recompiled_world_call(2,target);memcpy(c,gaw_ram,sizeof c);n[0x2F]=c[0x2F];memset(n+0x1FC0,0,0x40);memset(c+0x1FC0,0,0x40);if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"world full cb %04X mismatch\\n",target);for(unsigned i=0;i<sizeof n;++i)if(n[i]!=c[i])fprintf(stderr," %04X n=%02X c=%02X\\n",(unsigned)(0xC000u+i),n[i],c[i]);assert(0);}}
static void test_native_world_callbacks_5e75_5e9c(void){compare_native_world_callback_full(0x5E75,0x0002);compare_native_world_callback_full(0x5E9C,0x0002);compare_native_world_callback_full(0x5ECD,0x0002);}

static void compare_world_return_callback(uint16_t target,int trigger){uint8_t n[GAW_RAM_SIZE],c[GAW_RAM_SIZE];
 for(unsigned pass=0;pass<2u;++pass){
  reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,0x0042);gaw_ram_write16le(0xC0BB,0x00A5);gaw_ram_write16le(0xC0BD,0x8877);gaw_ram_write8(0xC010,0xFF);gaw_ram_write8(0xC011,0xFF);memset(gaw_ram_ptr(0xC200),0xAA,0x100);memset(gaw_ram_ptr(0xDCF0),0x55,0x10);gaw_entity(16)->raw[ENT_TYPE]=1;gaw_entity(18)->raw[ENT_TYPE]=2;
  if(target==0x654D)gaw_ram_write16le(0xC060,(uint16_t)(trigger?0x051B:0x0508));else{gaw_ram_write8(0xC0A6,(uint8_t)(trigger?0x30:0x20));gaw_ram_write16le(0xC060,0x051C);}
  if(pass==0){assert(gaw_world_native_callback(target)==1);memcpy(n,gaw_ram,sizeof n);}else{gaw_recompiled_world_call(2,target);memcpy(c,gaw_ram,sizeof c);}
 }
 /* Compatibility execution also updates internal VDP state, but every RAM
    byte touched by these callbacks must be identical. */
 memset(n+0x1FC0,0,0x40);memset(c+0x1FC0,0,0x40);
 if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"world return cb %04X trigger=%d mismatch\\n",target,trigger);for(unsigned i=0;i<sizeof n;++i)if(n[i]!=c[i])fprintf(stderr," %04X n=%02X c=%02X\\n",(unsigned)(0xC000u+i),n[i],c[i]);assert(0);}
}
static void test_native_world_return_callbacks(void){compare_world_return_callback(0x654D,0);compare_world_return_callback(0x654D,1);compare_world_return_callback(0x65D0,0);compare_world_return_callback(0x65D0,1);}

typedef struct {uint16_t target,pos;uint8_t cell;} TestWorldLink;
static const TestWorldLink test_world_links[]={
 {0xB3EB,0x01B0,0x38},{0xB402,0x0184,0x4E},{0xB444,0x0298,0x1C},{0xB45F,0x01B0,0x69},{0xB47A,0x0318,0x7B},{0xB486,0x0318,0x6A},{0xB4B5,0x0398,0x6C},{0xB4C1,0x029C,0x19},{0xB4D6,0x028C,0x62},{0xB4F4,0x0290,0x4B},{0xB51F,0x0184,0x88},{0xB528,0x029C,0x38},{0xB57D,0x0218,0x3C},{0xB59E,0x0430,0xA3},{0xB5B1,0x0184,0xA8},{0xB5DE,0x032C,0x92},{0xB5ED,0x0408,0xD7},{0xB60A,0x0298,0x98},{0xB61A,0x042C,0xE8},{0xB656,0x029C,0xCB},{0xB6A6,0x0184,0xEB},{0xB6AF,0x0318,0x9E},{0xB6C9,0x0298,0xA6},{0xB6D2,0x0298,0xFA},{0xB6E9,0x02A8,0xE7},{0xB719,0x0298,0xE2},{0xB722,0x031C,0xAA}
};
static void setup_world_link_test(const TestWorldLink*w,int trigger){
 reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,0x0105);gaw_ram_write8(0xC040,2);gaw_ram_write8(0xC0A2,0);gaw_ram_write8(0xC0A6,(uint8_t)(trigger?0x30:0));gaw_ram_write16le(0xC060,(uint16_t)(trigger?w->pos:(w->pos+8u)));gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC0F1,1);gaw_ram_write8(0xC318,0x18);gaw_ram_write8(0xC010,0xFF);gaw_ram_write8(0xC011,0xFF);gaw_entity(16)->raw[ENT_TYPE]=1;gaw_entity(19)->raw[ENT_TYPE]=2;
}







static const uint16_t test_temp_gate_targets[]={0xB433,0xB468,0xB566,0xB595,0xB5F9,0xB640,0xB686};
static void setup_temp_gate_test(void){reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,2);gaw_ram_write8(0xC040,0);gaw_ram_write8(0xC0A6,0xB0);gaw_ram_write8(0xC0A2,1);gaw_ram_write8(0xC0A8,0);gaw_ram_write16le(0xC060,0);gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC318,0x18);}
static void test_native_temp_gate_callbacks(void){for(unsigned i=0;i<sizeof test_temp_gate_targets/sizeof test_temp_gate_targets[0];++i){uint8_t n[GAW_RAM_SIZE],c[GAW_RAM_SIZE];uint16_t t=test_temp_gate_targets[i];setup_temp_gate_test();assert(gaw_world_native_callback(t)==1);memcpy(n,gaw_ram,sizeof n);setup_temp_gate_test();gaw_recompiled_world_call(2,t);memcpy(c,gaw_ram,sizeof c);memset(n+0x1FC0,0,0x40);memset(c+0x1FC0,0,0x40);if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"temp gate %04X mismatch\\n",t);for(unsigned k=0;k<sizeof n;++k)if(n[k]!=c[k])fprintf(stderr," %04X n=%02X c=%02X\\n",(unsigned)(0xC000u+k),n[k],c[k]);assert(0);}}}
typedef struct {uint16_t target,pos;} TestProgressBits;
static const TestProgressBits test_progress_bits[]={{0xB5BA,0x014C},{0xB62F,0x014C},{0xB740,0x0168},{0xB679,0x0168},{0xB506,0x014C},{0xB707,0x014C}};
static void test_native_progress_bits_callbacks(void){for(unsigned i=0;i<sizeof test_progress_bits/sizeof test_progress_bits[0];++i){uint8_t n[GAW_RAM_SIZE],c[GAW_RAM_SIZE];const TestProgressBits*w=&test_progress_bits[i];
 reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,2);gaw_ram_write8(0xC040,0);gaw_ram_write8(0xC0A6,0x14);gaw_ram_write16le(0xC060,w->pos);gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC318,0x18);assert(gaw_world_native_callback(w->target)==1);memcpy(n,gaw_ram,sizeof n);
 reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,2);gaw_ram_write8(0xC040,0);gaw_ram_write8(0xC0A6,0x14);gaw_ram_write16le(0xC060,w->pos);gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC318,0x18);gaw_recompiled_world_call(2,w->target);memcpy(c,gaw_ram,sizeof c);
 memset(n+0x1FC0,0,0x40);memset(c+0x1FC0,0,0x40);if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"progress bits %04X mismatch\\n",w->target);for(unsigned k=0;k<sizeof n;++k)if(n[k]!=c[k])fprintf(stderr," %04X n=%02X c=%02X\\n",(unsigned)(0xC000u+k),n[k],c[k]);assert(0);}
}}
typedef struct {uint16_t target,pos;uint8_t flags;} TestComposed;
static const TestComposed test_composed[]={{0xB40B,0x01B0,0x30},{0xB4A6,0x0168,0x14},{0xB4CA,0x0168,0x14},{0xB531,0x0184,0x30},{0xB53D,0x0424,0x30},{0xB5CB,0x029C,0x30},{0xB65F,0x0168,0x14},{0xB732,0x014C,0x14}};
static void setup_composed(const TestComposed*w,int active){reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,2);gaw_ram_write8(0xC040,0);gaw_ram_write8(0xC0A2,0);gaw_ram_write8(0xC0A6,(uint8_t)(active?w->flags:0));gaw_ram_write16le(0xC060,w->pos);gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC318,0x18);gaw_ram_write8(0xC010,0xFF);gaw_ram_write8(0xC011,0xFF);}
static void test_native_composed_callbacks(void){for(unsigned i=0;i<sizeof test_composed/sizeof test_composed[0];++i)for(int active=0;active<2;++active){uint8_t n[GAW_RAM_SIZE],c[GAW_RAM_SIZE];const TestComposed*w=&test_composed[i];setup_composed(w,active);assert(gaw_world_native_callback(w->target)==1);memcpy(n,gaw_ram,sizeof n);setup_composed(w,active);gaw_recompiled_world_call(2,w->target);memcpy(c,gaw_ram,sizeof c);n[0x2F]=c[0x2F];memset(n+0x1FC0,0,0x40);memset(c+0x1FC0,0,0x40);if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"composed %04X active=%d mismatch\\n",w->target,active);for(unsigned k=0;k<sizeof n;++k)if(n[k]!=c[k])fprintf(stderr," %04X n=%02X c=%02X\\n",(unsigned)(0xC000u+k),n[k],c[k]);assert(0);}}}
typedef struct {uint16_t target;uint8_t gate;} TestDirectGate;
static const TestDirectGate test_direct_gates[]={{0xB427,2},{0xB58F,0},{0xB5E7,0},{0xB649,3}};
static void setup_direct_gate(const TestDirectGate*w){reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,2);gaw_ram_write8(0xC040,0);gaw_ram_write8(0xC0A2,0);gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC318,0x18);if(w->gate<2){gaw_ram_write8(0xDC18,1);}else if(w->gate==2){gaw_ram_write8(0xDC41,1);}else{gaw_ram_write8(0xDC4E,1);}}
static void test_native_direct_gate_callbacks(void){for(unsigned i=0;i<sizeof test_direct_gates/sizeof test_direct_gates[0];++i){uint8_t n[GAW_RAM_SIZE],c[GAW_RAM_SIZE];const TestDirectGate*w=&test_direct_gates[i];setup_direct_gate(w);assert(gaw_world_native_callback(w->target)==1);memcpy(n,gaw_ram,sizeof n);setup_direct_gate(w);gaw_recompiled_world_call(2,w->target);memcpy(c,gaw_ram,sizeof c);memset(n+0x1FC0,0,0x40);memset(c+0x1FC0,0,0x40);if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"direct gate %04X mismatch\\n",w->target);for(unsigned k=0;k<sizeof n;++k)if(n[k]!=c[k])fprintf(stderr," %04X n=%02X c=%02X\\n",(unsigned)(0xC000u+k),n[k],c[k]);assert(0);}}}
typedef struct {uint16_t target,pos;uint8_t gate;} TestFinalizeGate;
static const TestFinalizeGate test_finalize_gates[]={{0xB450,0x0168,3},{0xB54E,0x0358,2},{0xB557,0x0168,0},{0xB670,0x014C,3},{0xB6F5,0x0358,0}};
static void setup_finalize_gate(const TestFinalizeGate*w){reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,2);gaw_ram_write8(0xC040,0);gaw_ram_write8(0xC0A6,0x14);gaw_ram_write16le(0xC060,w->pos);gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC318,0x18);if(w->gate<2){gaw_ram_write8(0xDC17,0x3D);gaw_ram_write8(0xDC18,1);}else if(w->gate==2){gaw_ram_write8(0xDC31,0x33);gaw_ram_write8(0xDC41,1);}else{gaw_ram_write8(0xDC3E,0x38);gaw_ram_write8(0xDC4E,1);}}
static void test_native_finalize_gate_callbacks(void){for(unsigned i=0;i<sizeof test_finalize_gates/sizeof test_finalize_gates[0];++i){uint8_t n[GAW_RAM_SIZE],c[GAW_RAM_SIZE];const TestFinalizeGate*w=&test_finalize_gates[i];setup_finalize_gate(w);assert(gaw_world_native_callback(w->target)==1);memcpy(n,gaw_ram,sizeof n);setup_finalize_gate(w);gaw_recompiled_world_call(2,w->target);memcpy(c,gaw_ram,sizeof c);n[0x2F]=c[0x2F];memset(n+0x1FC0,0,0x40);memset(c+0x1FC0,0,0x40);if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"finalize gate %04X mismatch\\n",w->target);for(unsigned k=0;k<sizeof n;++k)if(n[k]!=c[k])fprintf(stderr," %04X n=%02X c=%02X\\n",(unsigned)(0xC000u+k),n[k],c[k]);assert(0);}}}
typedef struct {uint16_t target,pos;} TestFinalizeCb;
static const TestFinalizeCb test_finalize_cbs[]={{0xB420,0x0168},{0xB49F,0x014C},{0xB4DF,0x0168},{0xB691,0x034C},{0xB6BB,0x0168}};
static void test_native_finalize_callbacks(void){for(unsigned i=0;i<sizeof test_finalize_cbs/sizeof test_finalize_cbs[0];++i)for(int trigger=0;trigger<2;++trigger){uint8_t n[GAW_RAM_SIZE],c[GAW_RAM_SIZE];const TestFinalizeCb*w=&test_finalize_cbs[i];
 reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,2);gaw_ram_write8(0xC040,0);gaw_ram_write8(0xC0A6,(uint8_t)(trigger?0x14:0));gaw_ram_write16le(0xC060,w->pos);gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC318,0x18);assert(gaw_world_native_callback(w->target)==1);memcpy(n,gaw_ram,sizeof n);
 reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,2);gaw_ram_write8(0xC040,0);gaw_ram_write8(0xC0A6,(uint8_t)(trigger?0x14:0));gaw_ram_write16le(0xC060,w->pos);gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC318,0x18);gaw_recompiled_world_call(2,w->target);memcpy(c,gaw_ram,sizeof c);
 n[0x2F]=c[0x2F];memset(n+0x1FC0,0,0x40);memset(c+0x1FC0,0,0x40);if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"finalize cb %04X trigger=%d mismatch\\n",w->target,trigger);for(unsigned k=0;k<sizeof n;++k)if(n[k]!=c[k])fprintf(stderr," %04X n=%02X c=%02X\\n",(unsigned)(0xC000u+k),n[k],c[k]);assert(0);}
}}
typedef struct {uint16_t target,pos;} TestProgressGate;
static const TestProgressGate test_progress_gates[]={{0xB3F4,0x035C},{0xB3FB,0x0168},{0xB48F,0x014C},{0xB4E6,0x0168},{0xB518,0x0168},{0xB5AA,0x014C},{0xB639,0x014C},{0xB669,0x014C},{0xB69F,0x0168},{0xB6DB,0x0168},{0xB6E2,0x014C},{0xB72B,0x014C},{0xB74A,0x014C}};
static void test_native_progress_gate_callbacks(void){for(unsigned i=0;i<sizeof test_progress_gates/sizeof test_progress_gates[0];++i)for(int trigger=0;trigger<2;++trigger){uint8_t n[GAW_RAM_SIZE],c[GAW_RAM_SIZE];const TestProgressGate*w=&test_progress_gates[i];
 reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,2);gaw_ram_write8(0xC040,0);gaw_ram_write8(0xC0A6,(uint8_t)(trigger?0x14:0));gaw_ram_write16le(0xC060,w->pos);gaw_ram_write16le(0xC034,0xDD00);assert(gaw_world_native_callback(w->target)==1);memcpy(n,gaw_ram,sizeof n);
 reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,2);gaw_ram_write8(0xC040,0);gaw_ram_write8(0xC0A6,(uint8_t)(trigger?0x14:0));gaw_ram_write16le(0xC060,w->pos);gaw_ram_write16le(0xC034,0xDD00);gaw_recompiled_world_call(2,w->target);memcpy(c,gaw_ram,sizeof c);
 n[0x2F]=c[0x2F];memset(n+0x1FC0,0,0x40);memset(c+0x1FC0,0,0x40);if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"progress gate %04X trigger=%d mismatch\\n",w->target,trigger);for(unsigned k=0;k<sizeof n;++k)if(n[k]!=c[k])fprintf(stderr," %04X n=%02X c=%02X\\n",(unsigned)(0xC000u+k),n[k],c[k]);assert(0);}
}}
static void test_native_link_callbacks_match_compat(void){
 for(unsigned i=0;i<sizeof test_world_links/sizeof test_world_links[0];++i)for(int trigger=0;trigger<2;++trigger){uint8_t n[GAW_RAM_SIZE],c[GAW_RAM_SIZE];const TestWorldLink*w=&test_world_links[i];
  setup_world_link_test(w,trigger);assert(gaw_world_native_callback(w->target)==1);memcpy(n,gaw_ram,sizeof n);
  setup_world_link_test(w,trigger);gaw_recompiled_world_call(2,w->target);memcpy(c,gaw_ram,sizeof c);
  n[0x2F]=c[0x2F];memset(n+0x1FC0,0,0x40);memset(c+0x1FC0,0,0x40);
  if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"link cb %04X trigger=%d mismatch\\n",w->target,trigger);for(unsigned k=0;k<sizeof n;++k)if(n[k]!=c[k]){fprintf(stderr," %04X n=%02X c=%02X\\n",(unsigned)(0xC000u+k),n[k],c[k]);if(k>0x1000)break;}assert(0);}
 }
}

static void test_hud_rebuild_full_matches_1e4e(void){uint8_t n[0x100],c[0x100];
 reset_full();gaw_ram_write8(0xC318,0x18);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DB,0x10);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC0DD,123);gaw_hud_rebuild_full();memcpy(n,gaw_ram_ptr(0xDB00),sizeof n);
 reset_full();gaw_ram_write8(0xC318,0x18);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DB,0x10);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC0DD,123);gaw_recompiled_call(0,0x1E4E);memcpy(c,gaw_ram_ptr(0xDB00),sizeof c);if(memcmp(n,c,sizeof n)!=0){for(unsigned i=0;i<sizeof n;++i)if(n[i]!=c[i])fprintf(stderr,"1e4e %02X n=%02X c=%02X\\n",i,n[i],c[i]);assert(0);}}

static void test_world_loader_matches_original_0c00(void){const uint16_t ids[]={0,1,0x10,0x55,0x95,0xBF,0x100,0x17F,0x1FF};for(unsigned k=0;k<sizeof ids/sizeof ids[0];++k){uint8_t n[160],c[160];reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,ids[k]);gaw_ram_write16le(0xC034,0xDD00);assert(gaw_world_load_current_cell());memcpy(n,gaw_ram_ptr(0xDC00),160);reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,ids[k]);gaw_ram_write16le(0xC034,0xDD00);gaw_recompiled_call(0,0x190B);memcpy(c,gaw_ram_ptr(0xDC00),160);if(memcmp(n,c,160)!=0){fprintf(stderr,"world decompressor mismatch id=%03X\\n",ids[k]);for(unsigned i=0;i<160;++i)if(n[i]!=c[i]){fprintf(stderr," first @%u n=%02X c=%02X\\n",i,n[i],c[i]);break;}assert(0);}}}


static void compare_5d4c_special(uint8_t gate){uint8_t n[sizeof gaw_ram],c[sizeof gaw_ram];
 reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,0x0105);gaw_ram_write8(0xC040,2);gaw_ram_write8(0xC0A2,0);gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC0F1,1);gaw_ram_write8(0xC318,0x18);if(gate==5){gaw_ram_write8(0xDC17,0x3D);gaw_ram_write8(0xDC18,1);}else if(gate==6){gaw_ram_write8(0xDC31,0x33);gaw_ram_write8(0xDC41,1);}else{gaw_ram_write8(0xDC3E,0x38);gaw_ram_write8(0xDC4E,1);}gaw_world_callback_5d4c_native();memcpy(n,gaw_ram,sizeof n);
 reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,0x0105);gaw_ram_write8(0xC040,2);gaw_ram_write8(0xC0A2,0);gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC0F1,1);gaw_ram_write8(0xC318,0x18);if(gate==5){gaw_ram_write8(0xDC17,0x3D);gaw_ram_write8(0xDC18,1);}else if(gate==6){gaw_ram_write8(0xDC31,0x33);gaw_ram_write8(0xDC41,1);}else{gaw_ram_write8(0xDC3E,0x38);gaw_ram_write8(0xDC4E,1);}gaw_recompiled_world_call(2,0x5D4C);memcpy(c,gaw_ram,sizeof c);n[0x2F]=c[0x2F];memset(n+0x1FC0,0,0x40);memset(c+0x1FC0,0,0x40);if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"5d4c gate%u mismatch\\n",gate);for(unsigned i=0;i<sizeof n;++i)if(n[i]!=c[i])fprintf(stderr," %04X n=%02X c=%02X\\n",(unsigned)(0xC000u+i),n[i],c[i]);assert(0);}}
static void test_native_5d4c_special_gates(void){compare_5d4c_special(5);compare_5d4c_special(6);compare_5d4c_special(7);}

static void test_native_world_callback_5d4c_matches_compat(void){uint8_t n[sizeof gaw_ram],c[sizeof gaw_ram];
 reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,0x0001);gaw_ram_write8(0xC040,0);gaw_ram_write8(0xC0A2,0);gaw_ram_write16le(0xC034,0xDD00);gaw_world_callback_5d4c_native();memcpy(n,gaw_ram,sizeof n);
 reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,0x0001);gaw_ram_write8(0xC040,0);gaw_ram_write8(0xC0A2,0);gaw_ram_write16le(0xC034,0xDD00);gaw_recompiled_world_call(2,0x5D4C);memcpy(c,gaw_ram,sizeof c);if(memcmp(n,c,0x1FE0u)!=0){for(unsigned i=0;i<0x1FE0u;++i)if(n[i]!=c[i])fprintf(stderr,"5d4c %04X n=%02X c=%02X\n",(unsigned)(0xC000u+i),n[i],c[i]);assert(0);}}

static void test_all_active_entity_types_are_native(void){reset_full();for(unsigned type=1;type<128u;++type){GawEntity*e=gaw_entity(16);memset(e->raw,0,GAW_ENTITY_SIZE);e->raw[ENT_TYPE]=(uint8_t)type;e->raw[ENT_MOTION_PHASE]=1;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);assert(gaw_entity_native_handler(e,(uint8_t)type)==1);}}
static void test_high_types_execute_through_real_dispatch(void){
    for(unsigned t=51;t<=124;++t){
        if(t==110||t==111) continue;
        reset_full(); GawEntity *e=gaw_entity(16); e->raw[ENT_TYPE]=(uint8_t)t;
        e->raw[0x11]=0x50; e->raw[0x13]=0x60; gaw_entity(0)->raw[0x11]=0x80; gaw_entity(0)->raw[0x13]=0x80;
        uint32_t f=gaw_sms_compat_faults(); gaw_entities_update_all(); assert(gaw_sms_compat_faults()==f);
    }
}
static void test_compat_core_frame_routines_return(void){
    reset_full(); gaw_ram_write8(RAM_MAIN_STATE,0x0C); gaw_ram_write8(0xC040,0); gaw_ram_write8(0xC318,24);
    uint32_t f=gaw_sms_compat_faults();
    assert(gaw_sms_compat_call(0,0x0940)); assert(gaw_sms_compat_call(0,0x1E99));
    assert(gaw_sms_compat_call(1,0x699C)); assert(gaw_sms_compat_call(0,0x1DF6));
    assert(gaw_sms_compat_faults()==f);
}
static void test_mapper_can_reach_bank5(void){
    reset_full(); gaw_ram_write8(0xC040,0); gaw_ram_write8(RAM_FRAME_COUNTER,0);
    assert(gaw_sms_compat_call(1,0x699C)); assert(gaw_sms_compat_faults()==0);
}

static void test_intro_path_returns_without_reset_divergence(void){
    reset_full();
    assert(gaw_sms_compat_call(0,0x0C98));
    assert(gaw_sms_compat_faults()==0);
    assert(gaw_ram_read8(0xDCE1)==1);
}
static void test_title_state_entry_returns(void){
    reset_full();
    assert(gaw_sms_compat_call(0,0x146D));
    assert(gaw_sms_compat_faults()==0);
}

static void test_title_menu_accepts_live_input(void){
    reset_full();
    gaw_platform_init();
    gaw_host_pulse_pad(20,3,0x10);
    assert(gaw_sms_compat_call(0,0x14ED));
    assert(gaw_sms_compat_faults()==0);
    assert(gaw_ram_read8(RAM_MAIN_STATE)==0x12);
}

static void compare_native_compat_51_52(const uint8_t in[GAW_ENTITY_SIZE]){
    uint8_t native[GAW_ENTITY_SIZE], compat[GAW_ENTITY_SIZE];
    reset_full(); memcpy(gaw_entity(16)->raw,in,GAW_ENTITY_SIZE); gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);
    assert(gaw_entity_native_handler(gaw_entity(16),in[ENT_TYPE])==1); memcpy(native,gaw_entity(16)->raw,GAW_ENTITY_SIZE);
    reset_full(); memcpy(gaw_entity(16)->raw,in,GAW_ENTITY_SIZE); gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);
    gaw_recompiled_entity_call(1,in[ENT_TYPE]==51?0x4CDE:0x4CE4,gaw_entity(16)); memcpy(compat,gaw_entity(16)->raw,GAW_ENTITY_SIZE);
    assert(memcmp(native,compat,GAW_ENTITY_SIZE)==0);
}
static void test_native_51_52_matches_compat(void){
    uint8_t e[GAW_ENTITY_SIZE]={0}; e[ENT_TYPE]=51; e[ENT_STATE]=0; compare_native_compat_51_52(e);
    memset(e,0,sizeof e); e[ENT_TYPE]=52;e[ENT_STATE]=2;compare_native_compat_51_52(e);
    memset(e,0,sizeof e); e[ENT_TYPE]=52;e[ENT_STATE]=0x0C;e[ENT_ANIM_FRAME]=2;e[0x11]=0x70;e[0x13]=0x80;compare_native_compat_51_52(e);
    for(unsigned q=0;q<4;++q){memset(e,0,sizeof e);e[ENT_TYPE]=52;e[ENT_STATE]=0x0E;e[0x2C]=(uint8_t)q;e[0x23]=0x80;e[0x27]=0x70;e[0x2E]=0xC0;e[0x2F]=0xFF;compare_native_compat_51_52(e);}
    memset(e,0,sizeof e);e[ENT_TYPE]=52;e[ENT_STATE]=0x10;compare_native_compat_51_52(e);
}




static void compare_native_compat_61_family(uint8_t type,uint8_t state,uint8_t anim,uint8_t phase){
    uint8_t n[GAW_ENTITY_SIZE],c[GAW_ENTITY_SIZE];uint16_t target=type==64?0x4D1Au:0x4D0Eu;
    reset_full();GawEntity*e=gaw_entity(16);e->raw[ENT_TYPE]=type;e->raw[ENT_STATE]=state;e->raw[ENT_ANIM_FRAME]=anim;e->raw[ENT_MOTION_PHASE]=phase;e->raw[ENT_DIRECTION]=1;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);assert(gaw_entity_native_handler(e,type)==1);memcpy(n,e->raw,sizeof n);
    reset_full();e=gaw_entity(16);e->raw[ENT_TYPE]=type;e->raw[ENT_STATE]=state;e->raw[ENT_ANIM_FRAME]=anim;e->raw[ENT_MOTION_PHASE]=phase;e->raw[ENT_DIRECTION]=1;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);gaw_recompiled_entity_call(1,target,e);memcpy(c,e->raw,sizeof c);assert(memcmp(n,c,sizeof n)==0);
}
static void test_native_61_family_deterministic_states(void){
    const uint8_t types[]={61,62,64};for(unsigned i=0;i<3u;++i){compare_native_compat_61_family(types[i],6,0,0);compare_native_compat_61_family(types[i],8,0,1);compare_native_compat_61_family(types[i],0x0A,0,1);}
}


static uint16_t target_for_new_native_type(uint8_t type){
    if(type==60u) return 0x4D08u;
    if(type==63u) return 0x4D14u;
    if(type==65u) return 0x4D20u;
    if(type==66u) return 0x4D26u;
    if(type==70u) return 0x4D32u;
    if(type>=71u && type<=73u) return 0x4D38u;
    if(type==74u || type==75u) return 0x4F44u;
    if(type==76u) return 0x4FB1u;
    if(type==77u || type==78u) return 0x4FB7u;
    if(type>=79u && type<=81u) return 0x4FD2u;
    if(type==82u) return 0x4FD8u;
    if(type==83u) return 0x4FF3u;
    if(type==84u || type==85u) return 0x5008u;
    if(type==86u) return 0x500Eu;
    if(type==87u || type==88u) return 0x5014u;
    if(type==89u || type==90u) return 0x501Au;
    if(type==91u) return 0x5043u;
    if(type==92u || type==93u) return 0x5049u;
    if(type==94u) return 0x5059u;
    if(type==95u || type==96u) return 0x505Fu;
    if(type==97u || type==98u) return 0x5065u;
    if(type==99u || type==100u || type==120u || type==121u) return 0x506Bu;
    return 0x4D2Cu;
}
static void compare_new_native_state(uint8_t type,uint8_t state,uint8_t anim,uint8_t phase,uint8_t cooldown){
    uint8_t n[GAW_ENTITY_SIZE],c[GAW_ENTITY_SIZE];
    reset_full();GawEntity *e=gaw_entity(16);e->raw[ENT_TYPE]=type;e->raw[ENT_STATE]=state;e->raw[ENT_ANIM_FRAME]=anim;e->raw[ENT_MOTION_PHASE]=phase?phase:cooldown;e->raw[ENT_COOLDOWN]=0;e->raw[ENT_DIRECTION]=1;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_ram_write8(0xC311u,0x88);gaw_ram_write8(0xC313u,0x98);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);assert(gaw_entity_native_handler(e,type)==1);memcpy(n,e->raw,sizeof n);
    reset_full();e=gaw_entity(16);e->raw[ENT_TYPE]=type;e->raw[ENT_STATE]=state;e->raw[ENT_ANIM_FRAME]=anim;e->raw[ENT_MOTION_PHASE]=phase?phase:cooldown;e->raw[ENT_COOLDOWN]=0;e->raw[ENT_DIRECTION]=1;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_ram_write8(0xC311u,0x88);gaw_ram_write8(0xC313u,0x98);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);gaw_recompiled_entity_call(1,target_for_new_native_type(type),e);memcpy(c,e->raw,sizeof c);if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"mismatch type=%u state=%u anim=%u phase=%u cooldown=%u\n",type,state,anim,phase,cooldown);for(unsigned i=0;i<GAW_ENTITY_SIZE;++i)if(n[i]!=c[i])fprintf(stderr,"  %02X: native=%02X compat=%02X\n",i,n[i],c[i]);assert(0);}
}
static void test_new_native_families_deterministic_states(void){
    compare_new_native_state(60,2,3,0,0);compare_new_native_state(60,6,0,0,0);compare_new_native_state(60,0x0C,0,0,0);compare_new_native_state(60,0x0E,0,0,5);
    compare_new_native_state(63,2,0,1,0);compare_new_native_state(63,6,0,0,0);compare_new_native_state(63,8,0,1,0);compare_new_native_state(63,0x0A,0,1,0);compare_new_native_state(63,0x0C,0,0,0);compare_new_native_state(63,0x0E,0,1,0);
    compare_new_native_state(65,2,0,0,0);compare_new_native_state(65,4,0,0,5);
    compare_new_native_state(66,0,0,0,0);compare_new_native_state(66,2,3,0,0);compare_new_native_state(66,6,0,0,5);compare_new_native_state(66,8,0,0,5);
    for(uint8_t t=67;t<=69;++t){compare_new_native_state(t,2,3,0,0);compare_new_native_state(t,6,0,0,0);compare_new_native_state(t,8,0,1,0);}
    compare_new_native_state(70,0,0,0,0);compare_new_native_state(70,2,0,0,0);compare_new_native_state(70,4,0,1,0);compare_new_native_state(70,4,0,0,0);compare_new_native_state(70,8,0,0,0);
    for(uint8_t t=71;t<=73;++t){compare_new_native_state(t,2,0,0,0);compare_new_native_state(t,6,0,1,0);compare_new_native_state(t,8,0,0,0);compare_new_native_state(t,0x0A,0,0,0);}
    for(uint8_t t=74;t<=75;++t){compare_new_native_state(t,2,0,0,0);compare_new_native_state(t,6,0,1,0);compare_new_native_state(t,8,0,1,0);compare_new_native_state(t,0x0A,0,0,0);compare_new_native_state(t,0x0C,0,1,0);}
    compare_new_native_state(76,2,0,0,0);compare_new_native_state(76,6,0,1,0);compare_new_native_state(76,8,0,1,0);
    for(uint8_t t=77;t<=78;++t){compare_new_native_state(t,2,0,0,0);compare_new_native_state(t,2,3,0,0);compare_new_native_state(t,6,0,1,0);}
    for(uint8_t t=79;t<=81;++t){compare_new_native_state(t,2,0,0,0);compare_new_native_state(t,2,3,0,0);compare_new_native_state(t,6,0,0,0);compare_new_native_state(t,8,0,1,0);}
    compare_new_native_state(79,0x0A,0,1,0);compare_new_native_state(80,0x0A,0,0,0);compare_new_native_state(80,0x0C,0,1,0);compare_new_native_state(81,0x0A,0,1,0);
    compare_new_native_state(82,0,0,0,0);compare_new_native_state(82,4,0,0,0);compare_new_native_state(82,6,0,0,0);compare_new_native_state(82,8,0,1,0);compare_new_native_state(82,0x0A,0,1,0);
    compare_new_native_state(83,2,0,0,0);compare_new_native_state(83,6,0,0,0);compare_new_native_state(83,8,0,1,0);compare_new_native_state(83,0x0A,0,1,0);
    for(uint8_t t=84;t<=85;++t){compare_new_native_state(t,2,0,0,0);compare_new_native_state(t,6,0,1,0);compare_new_native_state(t,8,0,1,0);compare_new_native_state(t,0x0A,0,1,0);}
    compare_new_native_state(86,0,0,1,0);compare_new_native_state(86,2,0,1,0);compare_new_native_state(86,4,0,1,0);compare_new_native_state(86,6,0,1,0);compare_new_native_state(86,8,0,1,0);
    for(uint8_t t=87;t<=88;++t){compare_new_native_state(t,2,0,0,0);compare_new_native_state(t,6,0,0,0);compare_new_native_state(t,8,0,1,0);compare_new_native_state(t,0x0A,0,1,0);compare_new_native_state(t,0x0C,0,1,0);}
    for(uint8_t t=89;t<=90;++t){compare_new_native_state(t,0,0,1,0);compare_new_native_state(t,4,0,1,0);compare_new_native_state(t,6,0,1,0);compare_new_native_state(t,8,0,1,0);}
    compare_new_native_state(91,2,0,0,0);compare_new_native_state(91,6,0,0,0);compare_new_native_state(91,8,0,1,0);compare_new_native_state(91,0x0A,0,1,0);
    for(uint8_t t=92;t<=93;++t){compare_new_native_state(t,2,0,0,0);compare_new_native_state(t,6,0,0,0);compare_new_native_state(t,8,0,1,0);compare_new_native_state(t,0x0A,0,1,0);}
    compare_new_native_state(94,2,0,0,0);compare_new_native_state(94,4,0,0,0);compare_new_native_state(94,6,0,1,0);
    for(uint8_t t=95;t<=96;++t){compare_new_native_state(t,2,0,0,0);compare_new_native_state(t,6,0,0,0);compare_new_native_state(t,8,0,1,0);compare_new_native_state(t,0x0A,0,1,0);compare_new_native_state(t,0x0C,0,1,0);}
    for(uint8_t t=97;t<=98;++t){compare_new_native_state(t,2,0,0,0);compare_new_native_state(t,4,0,0,0);compare_new_native_state(t,6,0,1,0);}
    const uint8_t fam99[]={99,100,120,121};for(unsigned i=0;i<4u;++i){uint8_t t=fam99[i];compare_new_native_state(t,0,0,0,0);compare_new_native_state(t,2,0,1,0);compare_new_native_state(t,4,0,0,0);compare_new_native_state(t,6,0,1,0);compare_new_native_state(t,8,0,1,0);compare_new_native_state(t,0x0A,0,1,0);}
}








static void compare_native_aux_116_119(uint8_t type,uint8_t st,uint8_t phase,uint8_t counter){uint8_t n[GAW_ENTITY_SIZE],c[GAW_ENTITY_SIZE];const uint16_t tg[]={0x4457,0x4518,0x46B4,0x47F7};
 reset_full();GawEntity*e=gaw_entity(24);e->raw[ENT_TYPE]=type;e->raw[ENT_STATE]=st;e->raw[ENT_MOTION_PHASE]=phase;e->raw[0x22]=counter;e->raw[0x21]=0;e->raw[0x20]=0;e->raw[ENT_DIRECTION]=2;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_entity(16)->raw[ENT_TYPE]=106;gaw_entity(16)->raw[0x11]=0x58;gaw_entity(16)->raw[0x13]=0x78;gaw_ram_write8(0xC311,0x80);gaw_ram_write8(0xC313,0x90);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,24);assert(gaw_entity_native_handler(e,type)==1);memcpy(n,e->raw,sizeof n);
 reset_full();e=gaw_entity(24);e->raw[ENT_TYPE]=type;e->raw[ENT_STATE]=st;e->raw[ENT_MOTION_PHASE]=phase;e->raw[0x22]=counter;e->raw[0x21]=0;e->raw[0x20]=0;e->raw[ENT_DIRECTION]=2;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_entity(16)->raw[ENT_TYPE]=106;gaw_entity(16)->raw[0x11]=0x58;gaw_entity(16)->raw[0x13]=0x78;gaw_ram_write8(0xC311,0x80);gaw_ram_write8(0xC313,0x90);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,24);gaw_recompiled_entity_call(1,tg[type-116u],e);memcpy(c,e->raw,sizeof c);
 if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"aux mismatch t=%u st=%u phase=%u count=%u\\n",type,st,phase,counter);for(unsigned i=0;i<sizeof n;++i)if(n[i]!=c[i])fprintf(stderr," %02X n=%02X c=%02X\\n",i,n[i],c[i]);assert(0);}}
static void test_native_aux_116_119_matches_compat(void){compare_native_aux_116_119(116,0,0,0);compare_native_aux_116_119(116,2,1,0);compare_native_aux_116_119(116,4,1,2);compare_native_aux_116_119(116,8,1,2);compare_native_aux_116_119(116,0x0A,1,2);compare_native_aux_116_119(117,0,0,0);compare_native_aux_116_119(117,2,1,0x80);compare_native_aux_116_119(117,4,1,0x80);compare_native_aux_116_119(118,0,0,0);compare_native_aux_116_119(118,4,1,0);compare_native_aux_116_119(119,0,0,0);compare_native_aux_116_119(119,2,1,0);}

static void test_native_112_115_matches_compat(void){const uint16_t tg[]={0x438C,0x43AF,0x43D2,0x442B};for(uint8_t type=112;type<=115;++type)for(uint8_t st=0;st<=2;st+=2){uint8_t n[GAW_ENTITY_SIZE],c[GAW_ENTITY_SIZE];
 reset_full();GawEntity*e=gaw_entity(24);e->raw[ENT_TYPE]=type;e->raw[ENT_STATE]=st;e->raw[ENT_DIRECTION]=2;e->raw[ENT_MOTION_PHASE]=1;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_ram_write8(0xC311,0x80);gaw_ram_write8(0xC313,0x90);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,24);assert(gaw_entity_native_handler(e,type)==1);memcpy(n,e->raw,sizeof n);
 reset_full();e=gaw_entity(24);e->raw[ENT_TYPE]=type;e->raw[ENT_STATE]=st;e->raw[ENT_DIRECTION]=2;e->raw[ENT_MOTION_PHASE]=1;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_ram_write8(0xC311,0x80);gaw_ram_write8(0xC313,0x90);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,24);gaw_recompiled_entity_call(1,tg[type-112u],e);memcpy(c,e->raw,sizeof c);if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"112-115 mismatch t=%u st=%u\\n",type,st);for(unsigned i=0;i<sizeof n;++i)if(n[i]!=c[i])fprintf(stderr," %02X n=%02X c=%02X\\n",i,n[i],c[i]);assert(0);}}}

static void compare_native_103_family(uint8_t type,uint8_t st,uint8_t phase){uint8_t n[GAW_ENTITY_SIZE],c[GAW_ENTITY_SIZE];
 reset_full();GawEntity*e=gaw_entity(16);e->raw[ENT_TYPE]=type;e->raw[ENT_STATE]=st;e->raw[ENT_MOTION_PHASE]=phase;e->raw[0x20]=3;e->raw[0x21]=5;e->raw[0x22]=3;e->raw[0x25]=0x0D;e->raw[0x11]=0x50;e->raw[0x13]=0x80;gaw_ram_write8(0xC311,0x80);gaw_ram_write8(0xC313,0xA0);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);assert(gaw_entity_native_handler(e,type)==1);memcpy(n,e->raw,sizeof n);
 reset_full();e=gaw_entity(16);e->raw[ENT_TYPE]=type;e->raw[ENT_STATE]=st;e->raw[ENT_MOTION_PHASE]=phase;e->raw[0x20]=3;e->raw[0x21]=5;e->raw[0x22]=3;e->raw[0x25]=0x0D;e->raw[0x11]=0x50;e->raw[0x13]=0x80;gaw_ram_write8(0xC311,0x80);gaw_ram_write8(0xC313,0xA0);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);gaw_recompiled_entity_call(1,0x51AE,e);memcpy(c,e->raw,sizeof c);
 if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"103-family mismatch t=%u st=%u phase=%u\\n",type,st,phase);for(unsigned i=0;i<sizeof n;++i)if(n[i]!=c[i])fprintf(stderr," %02X n=%02X c=%02X\\n",i,n[i],c[i]);assert(0);}}
static void test_native_103_family_matches_compat(void){const uint8_t ts[]={103,104,105,122,123};for(unsigned j=0;j<5u;++j){uint8_t t=ts[j];compare_native_103_family(t,0,0);compare_native_103_family(t,2,1);compare_native_103_family(t,2,0);compare_native_103_family(t,4,1);compare_native_103_family(t,6,1);compare_native_103_family(t,8,1);compare_native_103_family(t,0x0A,1);compare_native_103_family(t,0x0C,1);compare_native_103_family(t,0x0E,1);compare_native_103_family(t,0x12,1);}}

static void compare_native_108_109(uint8_t type,uint8_t st,uint8_t anim,uint8_t phase){uint8_t n[GAW_ENTITY_SIZE],c[GAW_ENTITY_SIZE];uint16_t target=type==108u?0x54D9u:0x55F1u;
 reset_full();GawEntity*e=gaw_entity(16);e->raw[ENT_TYPE]=type;e->raw[ENT_STATE]=st;e->raw[ENT_ANIM_FRAME]=anim;e->raw[ENT_MOTION_PHASE]=phase;e->raw[0x22]=3;e->raw[0x23]=2;e->raw[0x11]=0x50;e->raw[0x13]=0x80;e->raw[ENT_PENDING_DAMAGE]=7;gaw_ram_write8(0xC311u,0x80);gaw_ram_write8(0xC313u,0xA0);gaw_ram_write8(0xC0DF,1);gaw_ram_write8(0xC0E1,2);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);assert(gaw_entity_native_handler(e,type)==1);memcpy(n,e->raw,sizeof n);
 reset_full();e=gaw_entity(16);e->raw[ENT_TYPE]=type;e->raw[ENT_STATE]=st;e->raw[ENT_ANIM_FRAME]=anim;e->raw[ENT_MOTION_PHASE]=phase;e->raw[0x22]=3;e->raw[0x23]=2;e->raw[0x11]=0x50;e->raw[0x13]=0x80;e->raw[ENT_PENDING_DAMAGE]=7;gaw_ram_write8(0xC311u,0x80);gaw_ram_write8(0xC313u,0xA0);gaw_ram_write8(0xC0DF,1);gaw_ram_write8(0xC0E1,2);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);gaw_recompiled_entity_call(1,target,e);memcpy(c,e->raw,sizeof c);
 if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"108/109 mismatch t=%u st=%u anim=%u phase=%u\\n",type,st,anim,phase);for(unsigned i=0;i<sizeof n;++i)if(n[i]!=c[i])fprintf(stderr," %02X n=%02X c=%02X\\n",i,n[i],c[i]);assert(0);}}
static void test_native_108_109_matches_compat(void){
 compare_native_108_109(108,0,0,0);compare_native_108_109(108,2,0,1);compare_native_108_109(108,2,0,0);compare_native_108_109(108,4,0,1);compare_native_108_109(108,6,0,1);compare_native_108_109(108,8,0,1);compare_native_108_109(108,0x0A,0,1);compare_native_108_109(108,0x0C,0,1);compare_native_108_109(108,0x0E,0,1);compare_native_108_109(108,0x10,1,1);compare_native_108_109(108,0x12,0,1);
 compare_native_108_109(109,0,0,0);compare_native_108_109(109,2,0,1);compare_native_108_109(109,4,0,1);compare_native_108_109(109,6,0,1);compare_native_108_109(109,8,0,1);compare_native_108_109(109,0x0A,0,1);compare_native_108_109(109,0x0C,0,1);compare_native_108_109(109,0x0E,0,1);compare_native_108_109(109,0x10,1,1);compare_native_108_109(109,0x12,0,1);
 uint8_t n,c;reset_full();GawEntity*e=gaw_entity(16);e->raw[ENT_TYPE]=109;e->raw[ENT_STATE]=8;e->raw[ENT_MOTION_PHASE]=1;e->raw[ENT_PENDING_DAMAGE]=9;gaw_ram_write8(0xC0DF,2);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);assert(gaw_entity_native_handler(e,109)==1);n=e->raw[ENT_PENDING_DAMAGE];reset_full();e=gaw_entity(16);e->raw[ENT_TYPE]=109;e->raw[ENT_STATE]=8;e->raw[ENT_MOTION_PHASE]=1;e->raw[ENT_PENDING_DAMAGE]=9;gaw_ram_write8(0xC0DF,2);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);gaw_recompiled_entity_call(1,0x55F1,e);c=e->raw[ENT_PENDING_DAMAGE];assert(n==c&&n==0);
}

static void compare_native_106_family(uint8_t type,uint8_t st,uint8_t anim,uint8_t phase){uint8_t n[0x300],c[0x300];
 reset_full();GawEntity*e=gaw_entity(16);e->raw[ENT_TYPE]=type;e->raw[ENT_STATE]=st;e->raw[ENT_ANIM_FRAME]=anim;e->raw[ENT_MOTION_PHASE]=phase;e->raw[0x11]=0x50;e->raw[0x13]=0x80;gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);assert(gaw_entity_native_handler(e,type)==1);memcpy(n,gaw_ram_ptr(0xC600),sizeof n);
 reset_full();e=gaw_entity(16);e->raw[ENT_TYPE]=type;e->raw[ENT_STATE]=st;e->raw[ENT_ANIM_FRAME]=anim;e->raw[ENT_MOTION_PHASE]=phase;e->raw[0x11]=0x50;e->raw[0x13]=0x80;gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);gaw_recompiled_entity_call(1,0x54D3,e);memcpy(c,gaw_ram_ptr(0xC600),sizeof c);
 if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"106-family mismatch t=%u st=%u anim=%u phase=%u\\n",type,st,anim,phase);for(unsigned i=0;i<sizeof n;++i)if(n[i]!=c[i])fprintf(stderr," %03X n=%02X c=%02X\\n",i,n[i],c[i]);assert(0);}}
static void test_native_106_family_matches_compat(void){const uint8_t ts[]={106,107,124};for(unsigned j=0;j<3u;++j){uint8_t t=ts[j];compare_native_106_family(t,0,0,0);compare_native_106_family(t,2,5,1);compare_native_106_family(t,2,6,1);compare_native_106_family(t,4,0,1);compare_native_106_family(t,6,0,1);compare_native_106_family(t,6,0,0);compare_native_106_family(t,8,0,1);compare_native_106_family(t,8,0,0);compare_native_106_family(t,0x0A,0,1);compare_native_106_family(t,0x0A,0,0);compare_native_106_family(t,0x0C,5,1);compare_native_106_family(t,0x0C,6,1);compare_native_106_family(t,0x0E,0,1);}}

static void test_native_101_orbit_matches_compat(void){
    const uint8_t states[]={0,2,6,8};
    for(unsigned k=0;k<sizeof states;++k){uint8_t n[0x300],c[0x300];uint8_t st=states[k];
        reset_full();GawEntity*e=gaw_entity(16);e->raw[ENT_TYPE]=101;e->raw[ENT_STATE]=st;e->raw[ENT_HIT_FLASH_TIMER]=1;e->raw[ENT_MOTION_PHASE]=1;e->raw[0x2F]=2;e->raw[0x28]=0x18;e->raw[0x29]=0x33;e->raw[0x2A]=0;e->raw[0x2B]=8;e->raw[0x11]=0x50;e->raw[0x13]=0x80;for(unsigned i=0;i<8u;++i)gaw_entity(24u+i)->raw[ENT_TYPE]=102;gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);assert(gaw_entity_native_handler(e,101)==1);memcpy(n,gaw_ram_ptr(0xC600),sizeof n);
        reset_full();e=gaw_entity(16);e->raw[ENT_TYPE]=101;e->raw[ENT_STATE]=st;e->raw[ENT_HIT_FLASH_TIMER]=1;e->raw[ENT_MOTION_PHASE]=1;e->raw[0x2F]=2;e->raw[0x28]=0x18;e->raw[0x29]=0x33;e->raw[0x2A]=0;e->raw[0x2B]=8;e->raw[0x11]=0x50;e->raw[0x13]=0x80;for(unsigned i=0;i<8u;++i)gaw_entity(24u+i)->raw[ENT_TYPE]=102;gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);gaw_recompiled_entity_call(1,0x5071,e);memcpy(c,gaw_ram_ptr(0xC600),sizeof c);
        if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"type101 mismatch state=%u\\n",st);for(unsigned i=0;i<sizeof n;++i)if(n[i]!=c[i])fprintf(stderr," %03X n=%02X c=%02X\\n",i,n[i],c[i]);assert(0);}
    }
}

static void test_native_102_matches_compat(void){for(uint8_t st=0;st<=2;st+=2){uint8_t n[GAW_ENTITY_SIZE],c[GAW_ENTITY_SIZE];
 reset_full();GawEntity*e=gaw_entity(24);e->raw[ENT_TYPE]=102;e->raw[ENT_STATE]=st;e->raw[0x20]=4;e->raw[0x21]=0xFC;gaw_ram_write8(0xC611,0x60);gaw_ram_write8(0xC613,0x70);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,24);assert(gaw_entity_native_handler(e,102)==1);memcpy(n,e->raw,sizeof n);
 reset_full();e=gaw_entity(24);e->raw[ENT_TYPE]=102;e->raw[ENT_STATE]=st;e->raw[0x20]=4;e->raw[0x21]=0xFC;gaw_ram_write8(0xC611,0x60);gaw_ram_write8(0xC613,0x70);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,24);gaw_recompiled_entity_call(1,0x512B,e);memcpy(c,e->raw,sizeof c);assert(memcmp(n,c,sizeof n)==0);}}

static void test_native_91_tether_matches_compat(void){uint8_t n[GAW_ENTITY_SIZE],c[GAW_ENTITY_SIZE];
    reset_full();GawEntity*e=gaw_entity(16);e->raw[ENT_TYPE]=91;e->raw[ENT_STATE]=0x0C;e->raw[0x20]=2;e->raw[0x21]=5;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_ram_write8(0xC318,20);gaw_ram_write8(0xC311,0x80);gaw_ram_write8(0xC313,0x90);gaw_ram_write8(0xC021,0);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);assert(gaw_entity_native_handler(e,91)==1);memcpy(n,e->raw,sizeof n);
    reset_full();e=gaw_entity(16);e->raw[ENT_TYPE]=91;e->raw[ENT_STATE]=0x0C;e->raw[0x20]=2;e->raw[0x21]=5;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_ram_write8(0xC318,20);gaw_ram_write8(0xC311,0x80);gaw_ram_write8(0xC313,0x90);gaw_ram_write8(0xC021,0);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);gaw_recompiled_entity_call(1,0x5043,e);memcpy(c,e->raw,sizeof c);assert(memcmp(n,c,sizeof n)==0);assert(gaw_ram_read8(0xC301)==0x0C);}

static void test_native_92_wrapper_damage_matches_compat(void){uint8_t n[GAW_ENTITY_SIZE],c[GAW_ENTITY_SIZE];
    reset_full();GawEntity*e=gaw_entity(16);e->raw[ENT_TYPE]=92;e->raw[ENT_STATE]=8;e->raw[ENT_MOTION_PHASE]=1;e->raw[ENT_DIRECTION]=0;e->raw[ENT_PENDING_DAMAGE]=7;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_ram_write8(0xC30A,0);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);assert(gaw_entity_native_handler(e,92)==1);memcpy(n,e->raw,sizeof n);
    reset_full();e=gaw_entity(16);e->raw[ENT_TYPE]=92;e->raw[ENT_STATE]=8;e->raw[ENT_MOTION_PHASE]=1;e->raw[ENT_DIRECTION]=0;e->raw[ENT_PENDING_DAMAGE]=7;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_ram_write8(0xC30A,0);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);gaw_recompiled_entity_call(1,0x5049,e);memcpy(c,e->raw,sizeof c);assert(memcmp(n,c,sizeof n)==0);}

static void test_native_82_83_wrappers_match_compat(void){
    for(uint8_t type=82;type<=83;++type){uint8_t n[GAW_ENTITY_SIZE],c[GAW_ENTITY_SIZE];uint16_t target=type==82?0x4FD8u:0x4FF3u;
        reset_full();GawEntity*e=gaw_entity(16);e->raw[ENT_TYPE]=type;e->raw[ENT_STATE]=0x0A;e->raw[ENT_MOTION_PHASE]=1;e->raw[ENT_FLAGS]=4;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_ram_write8(0xC0DB,5);gaw_ram_write8(0xC0BF,0);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);assert(gaw_entity_native_handler(e,type)==1);memcpy(n,e->raw,sizeof n);uint8_t a=gaw_ram_read8(type==82?0xC0DB:0xC0BF);
        reset_full();e=gaw_entity(16);e->raw[ENT_TYPE]=type;e->raw[ENT_STATE]=0x0A;e->raw[ENT_MOTION_PHASE]=1;e->raw[ENT_FLAGS]=4;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_ram_write8(0xC0DB,5);gaw_ram_write8(0xC0BF,0);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);gaw_recompiled_entity_call(1,target,e);memcpy(c,e->raw,sizeof c);assert(memcmp(n,c,sizeof n)==0);assert(a==gaw_ram_read8(type==82?0xC0DB:0xC0BF));}
}

static void test_native_77_wrapper_resource_matches_compat(void){
    uint8_t n[GAW_ENTITY_SIZE],c[GAW_ENTITY_SIZE];
    reset_full();GawEntity*e=gaw_entity(16);e->raw[ENT_TYPE]=77;e->raw[ENT_STATE]=6;e->raw[ENT_MOTION_PHASE]=1;e->raw[ENT_FLAGS]=4;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_ram_write8(0xC0DB,5);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);assert(gaw_entity_native_handler(e,77)==1);memcpy(n,e->raw,sizeof n);uint8_t nv=gaw_ram_read8(0xC0DB);
    reset_full();e=gaw_entity(16);e->raw[ENT_TYPE]=77;e->raw[ENT_STATE]=6;e->raw[ENT_MOTION_PHASE]=1;e->raw[ENT_FLAGS]=4;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_ram_write8(0xC0DB,5);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);gaw_recompiled_entity_call(1,0x4FB7,e);memcpy(c,e->raw,sizeof c);assert(memcmp(n,c,sizeof n)==0);assert(nv==gaw_ram_read8(0xC0DB));
}

static void test_native_75_split_matches_compat(void){
    uint8_t n[0x300],c[0x300];
    reset_full();GawEntity *e=gaw_entity(16);e->raw[ENT_TYPE]=75;e->raw[ENT_STATE]=6;e->raw[ENT_MOTION_PHASE]=1;e->raw[ENT_PENDING_DAMAGE]=2;e->raw[ENT_HP]=10;e->raw[0x20]=1;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);assert(gaw_entity_native_handler(e,75)==1);memcpy(n,gaw_ram_ptr(0xC600),sizeof n);
    reset_full();e=gaw_entity(16);e->raw[ENT_TYPE]=75;e->raw[ENT_STATE]=6;e->raw[ENT_MOTION_PHASE]=1;e->raw[ENT_PENDING_DAMAGE]=2;e->raw[ENT_HP]=10;e->raw[0x20]=1;e->raw[0x11]=0x60;e->raw[0x13]=0x70;gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);gaw_recompiled_entity_call(1,0x4F44,e);memcpy(c,gaw_ram_ptr(0xC600),sizeof c);assert(memcmp(n,c,sizeof n)==0);
}

static void setup_world_anim(unsigned mode,unsigned f){
    gaw_ram_write8(0xC040,(uint8_t)mode);gaw_ram_write8(RAM_FRAME_COUNTER,(uint8_t)f);gaw_ram_write16le(0xC034,0xDD00);
    gaw_ram_write8(0xC0AA,0x20);gaw_ram_write8(0xC0AB,0);gaw_ram_write8(0xC930,4);gaw_ram_write8(0xC9E0,3);
    for(unsigned i=0;i<0xA0u;++i)gaw_ram_write8((uint16_t)(0xDC00u+i),(uint8_t)(mode==1?(0x24u+(i&7u)):(mode>=2?0x41u:(i&0x3Fu))));
    for(unsigned i=0;i<0x300u;++i)gaw_ram_write8((uint16_t)(0xC900u+i),(uint8_t)(i*3u+1u));
}
static void test_native_world_animation_matches_compat(void){
    static const unsigned frames[]={0,1,2,7,8,16,24};
    for(unsigned mode=0;mode<3u;++mode)for(unsigned fi=0;fi<sizeof(frames)/sizeof(frames[0]);++fi){
        uint8_t compat[0x1FE0],native[0x1FE0];
        reset_full();setup_world_anim(mode,frames[fi]);assert(gaw_sms_compat_call(1,0x699C));memcpy(compat,gaw_ram,sizeof compat);
        reset_full();setup_world_anim(mode,frames[fi]);gaw_world_animate_frame();memcpy(native,gaw_ram,sizeof native);
        assert(memcmp(native,compat,sizeof native)==0);
    }
}

static void setup_render_entities(unsigned count){
    for(unsigned i=0;i<count;++i){
        GawEntity *e=gaw_entity(i); memset(e->raw,0,GAW_ENTITY_SIZE);
        e->raw[ENT_TYPE]=(uint8_t)(16u+(i%8u));e->raw[ENT_DIRECTION]=(uint8_t)(i&3u);
        e->raw[0x11]=(uint8_t)(0x28u+i*9u);e->raw[0x13]=(uint8_t)(0x38u+i*7u);
        assert(gaw_entity_native_handler(e,e->raw[ENT_TYPE])==1);
    }
    gaw_ram_write8(RAM_ACTIVE_ENTITY_COUNT,(uint8_t)count);
}
static void test_native_renderer_matches_compat(void){
    for(unsigned mode=0;mode<2u;++mode)for(unsigned f=0;f<4u;++f){
        uint8_t compat[GAW_RAM_SIZE],native[GAW_RAM_SIZE]; unsigned count=mode?4u:8u;
        reset_full();setup_render_entities(count);gaw_ram_write8(RAM_FRAME_COUNTER,(uint8_t)f);gaw_ram_write8(RAM_VDP_STATUS,0);assert(gaw_sms_compat_call(0,0x0940));memcpy(compat,gaw_ram,sizeof compat);
        reset_full();setup_render_entities(count);gaw_ram_write8(RAM_FRAME_COUNTER,(uint8_t)f);gaw_ram_write8(RAM_VDP_STATUS,0);gaw_render_build_sms_sat();memcpy(native,gaw_ram,sizeof native);
        assert(memcmp(native+(0xC024-0xC000),compat+(0xC024-0xC000),4)==0);
        assert(memcmp(native+(0xD100-0xC000),compat+(0xD100-0xC000),0x80)==0);
        assert(memcmp(native+(0xDD40-0xC000),compat+(0xDD40-0xC000),0xC0)==0);
        for(unsigned k=0;k<count;++k){unsigned o=0x300u+k*GAW_ENTITY_SIZE;assert(native[o+0x1B]==compat[o+0x1B]);assert(native[o+0x1C]==compat[o+0x1C]);}
    }
}

static void test_native_hud_matches_compat(void){
    for(unsigned q=0;q<4u;++q){
        uint8_t compat[0x600], native[0x600];
        reset_full();
        gaw_ram_write8(RAM_FRAME_COUNTER,(uint8_t)q);
        for(unsigned i=0;i<9u;++i)gaw_ram_write8((uint16_t)(0xC0CFu+i),(uint8_t)((i&1u)?0x80u:0));
        gaw_ram_write8(0xC318,23);gaw_ram_write8(0xC0DA,32);gaw_ram_write8(0xC0DB,17);gaw_ram_write8(0xC0DC,32);gaw_ram_write8(0xC0DD,237);
        assert(gaw_sms_compat_call(0,0x1E99)); memcpy(compat,gaw_ram_ptr(0xC000),sizeof compat);
        reset_full();
        gaw_ram_write8(RAM_FRAME_COUNTER,(uint8_t)q);
        for(unsigned i=0;i<9u;++i)gaw_ram_write8((uint16_t)(0xC0CFu+i),(uint8_t)((i&1u)?0x80u:0));
        gaw_ram_write8(0xC318,23);gaw_ram_write8(0xC0DA,32);gaw_ram_write8(0xC0DB,17);gaw_ram_write8(0xC0DC,32);gaw_ram_write8(0xC0DD,237);
        gaw_hud_update_quarter_frame(); memcpy(native,gaw_ram_ptr(0xC000),sizeof native);
        assert(memcmp(native,compat,sizeof native)==0);
    }
    for(unsigned idx=0;idx<3u;++idx)for(unsigned f=0;f<16u;f+=2u){
        uint8_t compat[0x100],native[0x100];
        reset_full();gaw_ram_write8(0xC0F1,(uint8_t)idx);gaw_ram_write8(0xC0BF,1);gaw_ram_write8(RAM_FRAME_COUNTER,(uint8_t)f);assert(gaw_sms_compat_call(0,0x1DF6));memcpy(compat,gaw_ram_ptr(0xDC80),sizeof compat);
        reset_full();gaw_ram_write8(0xC0F1,(uint8_t)idx);gaw_ram_write8(0xC0BF,1);gaw_ram_write8(RAM_FRAME_COUNTER,(uint8_t)f);gaw_hud_update_status_descriptor();memcpy(native,gaw_ram_ptr(0xDC80),sizeof native);
        assert(memcmp(native,compat,sizeof native)==0);
    }
}









static void test_native_late_callback_inactive_paths(void){static const uint16_t ts[]={0xAC27,0xAC79,0xACB9,0xAD19,0xAD55,0xAD79,0xADAE,0xAE4A,0xAF4A,0xB0D9,0xB102};for(unsigned i=0;i<sizeof ts/sizeof ts[0];++i){uint8_t n[GAW_RAM_SIZE],c[GAW_RAM_SIZE];reset_full();gaw_ram_write8(0xC0A6,0);gaw_ram_write8(0xC0A2,1);assert(gaw_world_native_callback(ts[i]));memcpy(n,gaw_ram,sizeof n);reset_full();gaw_ram_write8(0xC0A6,0);gaw_ram_write8(0xC0A2,1);gaw_recompiled_world_call(2,ts[i]);memcpy(c,gaw_ram,sizeof c);memset(n+0x1FC0,0,0x40);memset(c+0x1FC0,0,0x40);if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"late inactive %04X mismatch\n",ts[i]);for(unsigned k=0;k<sizeof n;++k)if(n[k]!=c[k])fprintf(stderr," %04X n=%02X c=%02X\n",(unsigned)(0xC000u+k),n[k],c[k]);assert(0);}}}
static void test_native_fixed_item_callbacks_inactive(void){static const uint16_t ts[]={0xB3DD,0xB3E4,0xB419,0xB4ED,0xB5C4,0xB5D7,0xB613,0xB64F,0xB6C2,0xB751};for(unsigned i=0;i<sizeof ts/sizeof ts[0];++i){uint8_t n[GAW_RAM_SIZE],c[GAW_RAM_SIZE];reset_full();gaw_ram_write8(0xC0A6,0);assert(gaw_world_native_callback(ts[i]));memcpy(n,gaw_ram,sizeof n);reset_full();gaw_ram_write8(0xC0A6,0);gaw_recompiled_world_call(2,ts[i]);memcpy(c,gaw_ram,sizeof c);memset(n+0x1FC0,0,0x40);memset(c+0x1FC0,0,0x40);assert(memcmp(n,c,sizeof n)==0);}}

static void test_native_marker_callbacks(void){static const struct{uint16_t t,p;}v[]={{0xAD41,0x02D0},{0xAD41,0x02E4},{0xAED1,0x02DC},{0xB047,0x025C},{0xB08F,0x025C},{0xB263,0x01DC}};for(unsigned i=0;i<sizeof v/sizeof v[0];++i){uint8_t n[GAW_RAM_SIZE],c[GAW_RAM_SIZE];reset_full();gaw_ram_write8(0xC0A6,0x14);gaw_ram_write16le(0xC060,v[i].p);gaw_ram_write16le(RAM_WORLD_CELL_ID,2);gaw_ram_write16le(0xC0BB,3);assert(gaw_world_native_callback(v[i].t));memcpy(n,gaw_ram,sizeof n);reset_full();gaw_ram_write8(0xC0A6,0x14);gaw_ram_write16le(0xC060,v[i].p);gaw_ram_write16le(RAM_WORLD_CELL_ID,2);gaw_ram_write16le(0xC0BB,3);gaw_recompiled_world_call(2,v[i].t);memcpy(c,gaw_ram,sizeof c);memset(n+0x1FC0,0,0x40);memset(c+0x1FC0,0,0x40);if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"marker %04X/%04X mismatch\n",v[i].t,v[i].p);for(unsigned k=0;k<sizeof n;++k)if(n[k]!=c[k])fprintf(stderr," %04X n=%02X c=%02X\n",(unsigned)(0xC000u+k),n[k],c[k]);assert(0);}}}
static void setup_small_remaining(uint16_t t){
 reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,2);gaw_ram_write8(0xC040,0);gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC0F1,1);gaw_ram_write8(0xC318,0x18);
 if(t==0xB42D)gaw_ram_write8(0xDC7B,0);else if(t==0xB459)gaw_ram_write8(0xDC43,0);else if(t==0xB574){gaw_ram_write8(0xDC4A,0);gaw_ram_write8(0xC0A2,1);}
 else if(t==0xB560){gaw_ram_write8(0xC0A6,0x14);gaw_ram_write16le(0xC060,0x0168);gaw_ram_write8(0xDC1B,0);gaw_ram_write8(0xDC4E,1);}
 else {gaw_ram_write8(0xC0A6,0xB0);gaw_ram_write8(0xC0A2,1);gaw_ram_write8(0xC0A8,0);gaw_ram_write8(0xDC18,1);gaw_ram_write8(0xDC41,1);gaw_ram_write8(0xDC4E,1);}
}
static void test_native_small_remaining_callbacks(void){static const uint16_t ts[]={0xB42D,0xB459,0xB574,0xB496,0xB626,0xB758,0xB4FD,0xB6FE,0xB560};for(unsigned i=0;i<sizeof ts/sizeof ts[0];++i){uint8_t n[GAW_RAM_SIZE],c[GAW_RAM_SIZE];setup_small_remaining(ts[i]);assert(gaw_world_native_callback(ts[i]));memcpy(n,gaw_ram,sizeof n);setup_small_remaining(ts[i]);gaw_recompiled_world_call(2,ts[i]);memcpy(c,gaw_ram,sizeof c);memset(n+0x1FC0,0,0x40);memset(c+0x1FC0,0,0x40);if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"small callback %04X mismatch\n",ts[i]);for(unsigned k=0;k<sizeof n;++k)if(n[k]!=c[k])fprintf(stderr," %04X n=%02X c=%02X\n",(unsigned)(0xC000u+k),n[k],c[k]);assert(0);}}}
typedef struct {uint16_t target,position;uint8_t key;} TestKeyRoomCallback;
static const TestKeyRoomCallback test_key_rooms[]={
#include "../src/world_key_room_callbacks.inc"
};
static void test_native_key_room_callbacks(void){
 for(unsigned i=0;i<sizeof test_key_rooms/sizeof test_key_rooms[0];++i)for(int active=0;active<2;++active){const TestKeyRoomCallback*w=&test_key_rooms[i];uint8_t n[GAW_RAM_SIZE],c[GAW_RAM_SIZE];
  reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,0x0144u);gaw_ram_write8(0xC0A6,(uint8_t)(active?0x30u:0));gaw_ram_write16le(0xC060,w->position);gaw_ram_write8(0xC311,0x58);gaw_ram_write8(0xC313,0x98);for(unsigned j=0;j<8u;++j)gaw_entity(16u+j)->raw[ENT_TYPE]=(uint8_t)(j+1u);assert(gaw_world_native_callback(w->target));memcpy(n,gaw_ram,sizeof n);
  reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,0x0144u);gaw_ram_write8(0xC0A6,(uint8_t)(active?0x30u:0));gaw_ram_write16le(0xC060,w->position);gaw_ram_write8(0xC311,0x58);gaw_ram_write8(0xC313,0x98);for(unsigned j=0;j<8u;++j)gaw_entity(16u+j)->raw[ENT_TYPE]=(uint8_t)(j+1u);gaw_recompiled_world_call(2,w->target);memcpy(c,gaw_ram,sizeof c);
  memset(n+0x1FC0u,0,0x40u);memset(c+0x1FC0u,0,0x40u);if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"key room %04X active=%d mismatch\n",w->target,active);for(unsigned k=0;k<sizeof n;++k)if(n[k]!=c[k])fprintf(stderr," %04X n=%02X c=%02X\n",(unsigned)(0xC000u+k),n[k],c[k]);assert(0);}
 }}
typedef struct {uint16_t target,position;uint8_t cell;} TestRoomEntryAction;
static const TestRoomEntryAction test_room_entries[]={
#include "../src/world_room_callbacks.inc"
};
static void setup_room_entry_case(const TestRoomEntryAction*w,int active){
 reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,0x0123u);gaw_ram_write8(0xC0A6,(uint8_t)(active?0x30u:0));gaw_ram_write16le(0xC060,w->position);gaw_ram_write8(0xC311,0x48);gaw_ram_write8(0xC313,0x78);gaw_ram_write8(0xC0A2,1);
 for(unsigned i=0;i<8u;++i)gaw_entity(16u+i)->raw[ENT_TYPE]=(uint8_t)((i&1u)?0:(32u+i));
 gaw_ram_write8(0xC010,0xFF);gaw_ram_write8(0xC011,0xFF);
}
static void test_native_room_entry_callbacks(void){
 for(unsigned i=0;i<sizeof test_room_entries/sizeof test_room_entries[0];++i)for(int active=0;active<2;++active){
  uint8_t n[GAW_RAM_SIZE],c[GAW_RAM_SIZE];const TestRoomEntryAction*w=&test_room_entries[i];
  setup_room_entry_case(w,active);assert(gaw_world_native_callback(w->target)==1);memcpy(n,gaw_ram,sizeof n);
  setup_room_entry_case(w,active);gaw_recompiled_world_call(2,w->target);memcpy(c,gaw_ram,sizeof c);
  memset(n+0x1FE0u,0,0x20u);memset(c+0x1FE0u,0,0x20u);
  if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"room callback %04X pos=%04X active=%d mismatch\n",w->target,w->position,active);for(unsigned k=0;k<sizeof n;++k)if(n[k]!=c[k])fprintf(stderr," %04X n=%02X c=%02X\n",(unsigned)(0xC000u+k),n[k],c[k]);assert(0);}
 }
}

static const uint16_t test_room_finalize_targets[]={
#include "../src/world_room_finalize_targets.inc"
};
static void test_native_room_finalize_tail(void){
 for(unsigned i=0;i<sizeof test_room_finalize_targets/sizeof test_room_finalize_targets[0];++i){uint16_t t=test_room_finalize_targets[i];uint8_t n[GAW_RAM_SIZE],c[GAW_RAM_SIZE];
  reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,2);gaw_ram_write8(0xC0A6,0);gaw_ram_write8(0xC0A2,0);gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC0F1,1);gaw_ram_write8(0xC318,0x18);assert(gaw_world_native_callback(t));memcpy(n,gaw_ram,sizeof n);
  reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,2);gaw_ram_write8(0xC0A6,0);gaw_ram_write8(0xC0A2,0);gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC0F1,1);gaw_ram_write8(0xC318,0x18);gaw_recompiled_world_call(2,t);memcpy(c,gaw_ram,sizeof c);
  memset(n+0x1FC0u,0,0x40u);memset(c+0x1FC0u,0,0x40u);if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"room finalize %04X mismatch\n",t);for(unsigned k=0;k<sizeof n;++k)if(n[k]!=c[k])fprintf(stderr," %04X n=%02X c=%02X\n",(unsigned)(0xC000u+k),n[k],c[k]);assert(0);}
 }}
static void setup_map_entity_init_case(uint16_t cell,uint8_t mask,unsigned variant){
    reset_full();gaw_ram_write16le(RAM_WORLD_CELL_ID,cell);gaw_ram_write8((uint16_t)(0xC200u+(uint8_t)cell),mask);
    gaw_ram_write16le(0xC037u,(uint16_t)(variant&3u));
    if(variant==1u)gaw_ram_write8((uint16_t)(0xC0CEu+(variant&3u)),1u);
    if(variant==2u)gaw_ram_write8((uint16_t)(0xC0CEu+(variant&3u)),0x80u);
}
static void test_native_map_entity_init_1780(void){
    static const uint16_t cells[]={0,16,17,18,20,25,32,41,63,127,191,255,256,383,511};
    static const uint8_t masks[]={0xFF,0xA5,0x3C,0x00};
    for(unsigned ci=0;ci<sizeof cells/sizeof cells[0];++ci)for(unsigned mi=0;mi<sizeof masks/sizeof masks[0];++mi)for(unsigned v=0;v<3u;++v){
        uint8_t n[GAW_RAM_SIZE],c[GAW_RAM_SIZE];
        setup_map_entity_init_case(cells[ci],masks[mi],v);gaw_world_spawn_map_entities_native();memcpy(n,gaw_ram,sizeof n);
        setup_map_entity_init_case(cells[ci],masks[mi],v);gaw_recompiled_call(0,0x1780);memcpy(c,gaw_ram,sizeof c);
        /* $1D0D uses D100-D13F as graphics-conversion scratch and the bridge
           leaves call-stack history at DFE0+. Neither is gameplay state. */
        memset(n+0x1100u,0,0x40u);memset(c+0x1100u,0,0x40u);memset(n+0x1FE0u,0,0x20u);memset(c+0x1FE0u,0,0x20u);
        /* The bridge's accelerated $032A omits original scratch C031/C032;
           native $1780 intentionally preserves the real Z80 side effect. */
        n[0x31]=c[0x31]=0;n[0x32]=c[0x32]=0;
        if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"1780 mismatch cell=%u mask=%02X variant=%u\n",cells[ci],masks[mi],v);for(unsigned i=0;i<sizeof n;++i)if(n[i]!=c[i])fprintf(stderr," %04X n=%02X c=%02X\n",(unsigned)(0xC000u+i),n[i],c[i]);assert(0);}
    }
}
static void setup_player_init_case(unsigned k){
    reset_full();
    GawEntity *p=gaw_entity(0);
    p->raw[0x11]=(uint8_t)(0x38u+k*0x18u); p->raw[0x13]=(uint8_t)(0x58u+k*0x20u);
    gaw_ram_write8(0xC041,(uint8_t)(k%6u));
    gaw_ram_write8(0xC040,(uint8_t)(k%3u));
    gaw_ram_write8(0xC0DF,(uint8_t)(k&1u)); gaw_ram_write8(0xC0E1,(uint8_t)(k%3u));
    gaw_ram_write8(0xC0F1,(uint8_t)(1u+(k%3u))); gaw_ram_write8(0xC0F2,(uint8_t)(1u+(k%4u)));
    gaw_ram_write8(0xC0BF,(uint8_t)(k==4u)); gaw_ram_write8(0xC0EC,(uint8_t)(k==3u)); gaw_ram_write8(0xC0F0,(uint8_t)(k==5u));
    for(unsigned i=0;i<0x500u;++i)gaw_ram_write8((uint16_t)(0xD600u+i),(uint8_t)(i*13u+k*17u));
    /* Make classification inputs deliberate rather than accidental. */
    if(k==1u){gaw_ram_write8(0xC052,0xA0);gaw_ram_write8(0xC054,0xA1);}
    if(k==2u){gaw_ram_write8(0xC052,0x11);gaw_ram_write8(0xC054,0x12);}
}
static void test_native_player_init_2c63(void){
    for(unsigned k=0;k<6u;++k){
        uint8_t n[GAW_RAM_SIZE],c[GAW_RAM_SIZE];
        setup_player_init_case(k); gaw_player_init_from_world(); memcpy(n,gaw_ram,sizeof n);
        setup_player_init_case(k); gaw_recompiled_call(0,0x2C63); memcpy(c,gaw_ram,sizeof c);
        /* Compatibility execution leaves historical call-stack bytes in the
           unused top-of-RAM scratch area; they are not routine side effects. */
        memset(n+0x1FE0u,0,0x20u); memset(c+0x1FE0u,0,0x20u);
        if(memcmp(n,c,sizeof n)!=0){fprintf(stderr,"2C63 init mismatch case=%u\n",k);for(unsigned i=0;i<sizeof n;++i)if(n[i]!=c[i])fprintf(stderr," %04X n=%02X c=%02X\n",(unsigned)(0xC000u+i),n[i],c[i]);assert(0);}
    }
}
int main(void){test_native_late_callback_inactive_paths();test_native_fixed_item_callbacks_inactive();test_native_marker_callbacks();test_native_small_remaining_callbacks();test_native_key_room_callbacks();test_native_room_finalize_tail();test_native_room_entry_callbacks();test_native_map_entity_init_1780();test_native_player_init_2c63();test_native_temp_gate_callbacks();test_native_progress_bits_callbacks();test_native_composed_callbacks();test_native_direct_gate_callbacks();test_native_finalize_gate_callbacks();test_native_finalize_callbacks();test_native_progress_gate_callbacks();test_native_link_callbacks_match_compat();test_native_world_return_callbacks();test_native_5d4c_special_gates();test_native_world_callbacks_5e75_5e9c();test_hud_rebuild_full_matches_1e4e();test_world_loader_matches_original_0c00();test_native_world_callback_5d4c_matches_compat();test_all_active_entity_types_are_native();test_high_types_execute_through_real_dispatch();test_compat_core_frame_routines_return();test_mapper_can_reach_bank5();test_intro_path_returns_without_reset_divergence();test_title_state_entry_returns();test_title_menu_accepts_live_input();test_native_51_52_matches_compat();test_native_61_family_deterministic_states();test_new_native_families_deterministic_states();test_native_aux_116_119_matches_compat();test_native_112_115_matches_compat();test_native_103_family_matches_compat();test_native_108_109_matches_compat();test_native_106_family_matches_compat();test_native_101_orbit_matches_compat();test_native_102_matches_compat();test_native_91_tether_matches_compat();test_native_92_wrapper_damage_matches_compat();test_native_82_83_wrappers_match_compat();test_native_77_wrapper_resource_matches_compat();test_native_75_split_matches_compat();test_native_world_animation_matches_compat();test_native_renderer_matches_compat();test_native_hud_matches_compat();puts("final compatibility tests: OK");return 0;}
