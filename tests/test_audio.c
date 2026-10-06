#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_audio.h"
#include "gaw_host.h"
#include "gaw_platform.h"
#include "gaw_ram.h"
#include "gaw_sms_compat.h"

static uint8_t before[0x2000],expected[0x1F90],entropy[64];
static uint16_t reference_sound[256],native_sound[256];
static unsigned case_now,frame;
static void setup(unsigned command,unsigned mode){
    gaw_platform_init();gaw_sms_compat_reset();gaw_audio_reset_diagnostics();memset(gaw_ram,0,sizeof gaw_ram);
    gaw_ram_write8(0xDE05u,0x80);gaw_ram_write8(0xDE06u,(uint8_t)command);gaw_ram_write8(0xDE03u,(uint8_t)mode);
}
static void tick(void){
    memcpy(before,gaw_ram,sizeof before);gaw_host_clear_sound_trace();
    assert(gaw_sms_compat_raw_call_args(6,0x8000,0,0,0,0));assert(gaw_sms_compat_faults()==0);
    memcpy(expected,gaw_ram,sizeof expected);unsigned reference_count=gaw_host_sound_trace(reference_sound,256);assert(reference_count<=256u);
    unsigned random=gaw_sms_compat_refresh_trace(entropy,64);assert(random<=64u);
    memcpy(gaw_ram,before,sizeof before);gaw_host_clear_sound_trace();gaw_host_set_entropy_sequence(entropy,random);gaw_audio_tick();
    unsigned native_count=gaw_host_sound_trace(native_sound,256);assert(native_count<=256u);
    unsigned differences=0;
    for(unsigned i=0;i<sizeof expected;++i)if(expected[i]!=gaw_ram[i]){if(differences++<15u)fprintf(stderr,"audio case%u frame%u RAM%04X ref%02X native%02X\n",case_now,frame,0xC000u+i,expected[i],gaw_ram[i]);}
    if(reference_count!=native_count)fprintf(stderr,"audio case%u frame%u PSG count ref%u native%u\n",case_now,frame,reference_count,native_count);
    for(unsigned i=0;i<reference_count&&i<native_count;++i)if(reference_sound[i]!=native_sound[i]){
        fprintf(stderr,"audio case%u frame%u PSG%u ref%04X native%04X\n",case_now,frame,i,reference_sound[i],native_sound[i]);
        for(unsigned c=0;c<7u;++c){unsigned at=0x1E40u+c*0x30u;if(before[at]&0x80u){fprintf(stderr,"channel%04X",0xC000u+at);for(unsigned j=0;j<0x30u;++j)fprintf(stderr," %02X",before[at+j]);fputc('\n',stderr);}}
    }
    assert(!differences);assert(reference_count==native_count);assert(memcmp(reference_sound,native_sound,reference_count*sizeof *reference_sound)==0);assert(gaw_audio_faults()==0);
}
int main(void){
    unsigned ticks=0;
    for(unsigned mode=0;mode<2u;++mode)for(unsigned command=0x81u;command<=0xACu;++command){
        if(command>0x8Du&&command<0x90u)continue;
        case_now=command+mode*256u;setup(command,mode);
        unsigned length=command<0x90u?4096u:512u;
        for(frame=0;frame<length;++frame){tick();++ticks;}
    }
    for(unsigned mode=0;mode<2u;++mode){
        case_now=0x1000u+mode;setup(0x81,mode);
        for(frame=0;frame<4096u;++frame){
            if(frame%32u==16u)gaw_ram_write8(0xDE08u,(uint8_t)(0x90u+(frame/32u)%29u));
            if(frame==72u)gaw_ram_write8(0xDE09u,0x90);
            if(frame==96u)gaw_ram_write8(0xDE09u,0x80);
            if(frame==128u)gaw_ram_write8(0xDE0Au,0x80);
            if(frame==160u)gaw_ram_write8(0xDE0Au,0);
            if(frame==200u)gaw_ram_write8(0xDE06u,0xB0);
            if(frame==400u)gaw_ram_write8(0xDE06u,0xB2);
            if(frame==420u)gaw_ram_write8(0xDE06u,0xB3);
            if(frame==500u)gaw_ram_write8(0xDE06u,0xB1);
            if(frame==520u)gaw_ram_write8(0xDE06u,0x89);
            if(frame>=1024u&&frame%128u==0u){
                gaw_ram_write8(0xDE06u,(uint8_t)(0x90u+(frame/128u)%29u));
                gaw_ram_write8(0xDE07u,(uint8_t)(0x90u+(frame/128u+7u)%29u));
                gaw_ram_write8(0xDE09u,(uint8_t)(0x90u+(frame/128u+13u)%29u));
            }
            if(frame>=1024u&&frame%128u==64u)gaw_ram_write8(0xDE09u,0x80);
            if(frame==3072u)gaw_ram_write8(0xDE06u,0xB5);
            tick();++ticks;
        }
    }
    printf("native audio differential tests: OK (%u ticks, RAM and ordered PSG/stereo writes)\n",ticks);return 0;
}
