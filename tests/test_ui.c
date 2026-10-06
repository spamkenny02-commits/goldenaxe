#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_core.h"
#include "gaw_host.h"
#include "gaw_platform.h"
#include "gaw_ram.h"
#include "gaw_sms_compat.h"
#include "gaw_ui.h"

static uint8_t reference_ram[GAW_RAM_SIZE],reference_vram[0x4000],reference_cram[32],reference_regs[16];
static unsigned reference_frames;
static void setup(void){
    memset(gaw_ram,0,sizeof gaw_ram);gaw_platform_init();gaw_sms_compat_reset();
    gaw_ram_write8(0xC311,0x58);gaw_ram_write8(0xC313,0x88);
    gaw_ram_write16le(0xDCE0,0xDCE4);gaw_ram_write16le(0xDCE4,10);
    gaw_sms_vdp_control_write(0);gaw_sms_vdp_control_write(0x40);
    for(unsigned i=0;i<0x4000u;++i)gaw_sms_vdp_data_write((uint8_t)(i*17u+7u));
}
static void capture(void){
    assert(gaw_sms_compat_faults()==0);memcpy(reference_ram,gaw_ram,sizeof reference_ram);
    memcpy(reference_vram,gaw_sms_vram(),sizeof reference_vram);memcpy(reference_cram,gaw_sms_cram(),sizeof reference_cram);memcpy(reference_regs,gaw_sms_vdp_regs(),sizeof reference_regs);reference_frames=gaw_host_frame_count();
}
static void compare(const char *what){
    /* DF80-DFFF is original Z80 call-stack workspace, not persistent game state. */
    for(unsigned i=0;i<0x1F80u;++i)if(reference_ram[i]!=gaw_ram[i]){fprintf(stderr,"%s RAM %04X native=%02X reference=%02X\n",what,0xC000u+i,gaw_ram[i],reference_ram[i]);assert(0);}
    for(unsigned i=0;i<0x4000u;++i)if(reference_vram[i]!=gaw_sms_vram()[i]){fprintf(stderr,"%s VRAM %04X native=%02X reference=%02X\n",what,i,gaw_sms_vram()[i],reference_vram[i]);assert(0);}
    assert(memcmp(reference_cram,gaw_sms_cram(),sizeof reference_cram)==0);
    assert(memcmp(reference_regs,gaw_sms_vdp_regs(),sizeof reference_regs)==0);
    if(reference_frames!=gaw_host_frame_count()){fprintf(stderr,"%s frames native=%u reference=%u\n",what,gaw_host_frame_count(),reference_frames);assert(0);}
}
static void input(unsigned scenario){
    if(scenario==0)gaw_host_queue_pad(1,0x20);
    else{
        uint8_t first=scenario==1?0x10u:2u;
        gaw_host_queue_pad(1,first);gaw_host_queue_pad(2,0);
        if(scenario==3){gaw_host_queue_pad(3,1);gaw_host_queue_pad(4,0);}
        gaw_host_queue_pad(5,0x20);
    }
}
static void test_menu(void){
    for(unsigned fixed=0;fixed<3u;++fixed)for(unsigned scenario=0;scenario<4u;++scenario){
        setup();input(scenario);assert(gaw_sms_compat_call(1,fixed==2u?0x60B1:fixed?0x6093:0x60BC));capture();
        setup();input(scenario);uint8_t result=fixed==2u?gaw_ui_yes_no_card():fixed?gaw_ui_yes_no_fixed():gaw_ui_yes_no();
        assert(result==((scenario==0||scenario==3)?0xFFu:0));compare("choice");
    }
}
static void paginate(void){for(unsigned f=8;f<1000u;f+=8u){gaw_host_queue_pad(f,0x20);gaw_host_queue_pad(f+1u,0);}}
static void test_text(void){
    const uint16_t resources[]={0xB90E,0xB930,0x911E,0xBA4D,0xBA8E,0xB9D7,0xB95F,0xB982};
    for(unsigned i=0;i<sizeof resources/sizeof resources[0];++i){
        setup();paginate();assert(gaw_sms_compat_call_args(3,0x050C,resources[i],0,0,0));capture();
        setup();paginate();gaw_ui_show_message(resources[i]);compare("dialogue");
    }
}

typedef struct {uint16_t target,position;uint8_t flags,saved,card_state,currency,modifier;} ScriptCase;
static void script_setup(const ScriptCase *c,int choose_no){
    setup();gaw_ram_write16le(RAM_WORLD_CELL_ID,0x0142);
    gaw_ram_write16le(0xC060,c->position);gaw_ram_write8(0xC0A6,c->flags);
    gaw_ram_write8(0xC0BB,c->saved);gaw_ram_write8(0xC0BD,0x58);gaw_ram_write8(0xC0BE,0x88);
    gaw_ram_write8(0xC073,c->card_state);gaw_ram_write8(0xC0DD,c->currency);
    gaw_ram_write8(0xC040,0);gaw_ram_write8(0xC0DA,0x20);gaw_ram_write8(0xC0DC,0x20);gaw_ram_write8(0xC318,0x18);
    gaw_ram_write16le(0xC034,0xDD00);memset(gaw_ram_ptr(0xC200),0xFF,0x100);
    for(unsigned i=0;i<0x300u;++i)gaw_ram_write8((uint16_t)(0xC900u+i),(uint8_t)(i*17u+3u));
    gaw_ram_write8(0xDC38,0x35);gaw_ram_write8(0xDC39,0x3F);gaw_ram_write8(0xDC48,0x36);gaw_ram_write8(0xDC49,0x3E);
    if(c->target==0xADEE){
        for(unsigned i=0;i<10u;++i)gaw_ram_write8((uint16_t)(0xDC33u+i),0x34u+i%4u);
        gaw_ram_write16le(0xDC03,0x3F35);gaw_ram_write16le(0xDC06,0x3E36);gaw_ram_write16le(0xDC09,0x3B34);
        gaw_ram_write8(0xDC0C,c->modifier);
        if(c->card_state==3u&&c->modifier)for(unsigned i=0;i<3u;++i)gaw_ram_write8((uint16_t)(0xDC03u+i*3u),c->modifier);
    }
    for(unsigned f=8;f<1000u;f+=8u){gaw_host_queue_pad(f,(uint8_t)(choose_no&&f%32u?0x10u:0x20u));gaw_host_queue_pad(f+1u,0);}
}
static void test_scripts(void){
    const ScriptCase cases[]={
        {0xB19E,0x019C,0x30,0x1A,0,50,0},{0xB19E,0x019C,0x30,0x36,0,50,0},
        {0xB19E,0x019C,0x30,0x6D,0,50,0},{0xB19E,0x019C,0x30,0x3C,0,50,0},
        {0xB19E,0x019C,0x30,0x87,0,50,0},{0xB19E,0x019C,0x30,0x96,0,50,0},
        {0xB19E,0x025C,0x14,0x1A,0,50,0},{0xB19E,0x025C,0x14,0x1A,0,5,0},
        {0xB19E,0x051C,0x30,0x1A,0,50,0},{0xB19E,0x1111,0,0x1A,0,50,0},
        {0xB00A,0x02DC,0x14,0x1A,0,50,0},{0xB00A,0x02DC,0x14,0x1A,0,5,0},
        {0xB00A,0x051C,0x30,0x1A,0,50,0},{0xB00A,0x1111,0,0x1A,0,50,0},
        {0xADEE,0x1111,0,0x1A,0,50,0},
        {0xADEE,0x1111,0,0x1A,2,50,0},{0xADEE,0x1111,0,0x1A,2,50,0x38},
        {0xADEE,0x1111,0,0x1A,2,50,0x39},
        {0xADEE,0x1111,0,0x1A,3,50,0},{0xADEE,0x1111,0,0x1A,3,250,0x34},
        {0xADEE,0x1111,0,0x1A,3,255,0x34},
        {0xADEE,0x1111,0,0x1A,3,50,0x37},{0xADEE,0x1111,0,0x1A,3,5,0x37},
    };
    for(unsigned i=0;i<sizeof cases/sizeof cases[0];++i)for(int no=0;no<2;++no){
        char label[64];snprintf(label,sizeof label,"script %04X case=%u no=%d",cases[i].target,i,no);
        script_setup(&cases[i],no);assert(gaw_sms_compat_world_call(2,cases[i].target));capture();
        script_setup(&cases[i],no);assert(gaw_world_native_callback(cases[i].target));compare(label);
    }
}

static void test_card_draws(void){
    const ScriptCase base={0xADEE,0x0248,0x14,0x1A,1,50,0};
    unsigned kinds=0;
    for(unsigned seed=1;seed<96u;++seed)for(unsigned full=0;full<3u;++full){
        uint8_t entropy[64];
        script_setup(&base,0);gaw_ram_write16le(0xC028,(uint16_t)(seed*683u));
        if(full==0){gaw_ram_write8(0xDC03,0x3A);gaw_ram_write8(0xDC06,0x3A);gaw_ram_write8(0xDC09,0x3A);}
        else if(full==1){gaw_ram_write8(0xDC09,0x3A);}
        else {gaw_ram_write8(0xDC09,0x3A);gaw_ram_write8(0xDC0C,0x38);}
        gaw_ram_write8(0xDC33,0x3A);
        assert(gaw_sms_compat_world_call(2,0xADEE));capture();
        unsigned n=gaw_sms_compat_refresh_trace(entropy,64);assert(n>0&&n<=64u);
        uint8_t face=gaw_ram_read8(0xDC33);assert(face>=0x34u&&face<=0x39u);kinds|=1u<<(face-0x34u);
        script_setup(&base,0);gaw_ram_write16le(0xC028,(uint16_t)(seed*683u));
        if(full==0){gaw_ram_write8(0xDC03,0x3A);gaw_ram_write8(0xDC06,0x3A);gaw_ram_write8(0xDC09,0x3A);}
        else if(full==1){gaw_ram_write8(0xDC09,0x3A);}
        else {gaw_ram_write8(0xDC09,0x3A);gaw_ram_write8(0xDC0C,0x38);}
        gaw_ram_write8(0xDC33,0x3A);gaw_host_set_entropy_sequence(entropy,n);
        assert(gaw_world_native_callback(0xADEE));compare("card draw");
    }
    assert(kinds==0x3Fu);
}

static void embedded_text_setup(unsigned number){
    const char text[]="Salut \\minuscules\\. % # # $ Suite - fin!";
    const char inserted[]="Arthur";
    setup();paginate();memcpy(gaw_ram_ptr(0xD540),text,sizeof text);memcpy(gaw_ram_ptr(0xD580),inserted,sizeof inserted);
    gaw_ram_write16le(0xDCE0,0xD580);gaw_ram_write16le(0xDCE2,0xD590);gaw_ram_write16le(0xDCE4,0xD592);
    gaw_ram_write16le(0xD590,(uint16_t)number);gaw_ram_write16le(0xD592,0);
}
static void test_text_commands(void){
    const unsigned numbers[]={0,1,10,99,999,10000,65535};
    for(unsigned i=0;i<sizeof numbers/sizeof numbers[0];++i){
        embedded_text_setup(numbers[i]);assert(gaw_sms_compat_call_args(3,0x050C,0xD540,0,0,0));capture();
        embedded_text_setup(numbers[i]);gaw_ui_show_message(0xD540);compare("embedded text");
    }
}

static void test_message_tables(void){
    const uint16_t targets[]={0xAD19,0xAD19,0xB102};
    const uint16_t positions[]={0x02EC,0x0248,0x025C};
    const uint16_t tables[]={0xAD2F,0xAD38,0xB10F};
    for(unsigned i=0;i<3u;++i){
        ScriptCase c={targets[i],positions[i],0x14,gaw_sms_rom_bank_read(2,tables[i]),0,50,0};
        script_setup(&c,0);assert(gaw_sms_compat_world_call(2,c.target));capture();
        script_setup(&c,0);assert(gaw_world_native_callback(c.target));compare("message table");
    }
}
int main(void){test_menu();test_text();test_text_commands();test_scripts();test_card_draws();test_message_tables();puts("native UI/script differential tests: OK");return 0;}
