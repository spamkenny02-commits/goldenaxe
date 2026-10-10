#include <string.h>
#include "include/gaw_ui.h"
#include "include/gaw_core.h"
#include "include/gaw_platform.h"
#include "include/gaw_ram.h"
#include "include/gaw_video.h"
#include "include/gaw_assets.h"

#define R(a) gaw_ram_read8((uint16_t)(a))
#define W(a,v) gaw_ram_write8((uint16_t)(a),(uint8_t)(v))
#define R16(a) gaw_ram_read16le((uint16_t)(a))
#define W16(a,v) gaw_ram_write16le((uint16_t)(a),(uint16_t)(v))
static uint8_t rom(uint16_t a){return gaw_sms_rom_bank_read(a<0x4000u?0u:a<0x8000u?1u:3u,a);}
static uint8_t text_byte(uint16_t a){return a>=0xC000u?R(0xC000u+(a&0x1FFFu)):rom(a);}
static void video_address(uint16_t a){gaw_platform_video_command(a);}
static void video_byte(uint16_t a,uint8_t v){video_address((uint16_t)(0x4000u|(a&0x3FFFu)));gaw_sms_vdp_data_write(v);}

void gaw_ui_upload_name_table(void){
    video_address(0x7800u);
    gaw_sms_vdp_data_write_block(gaw_ram_ptr(0xD600u),0x600u);
}

/* $0877 writes a width x height border using the three rows at $0902. */
void gaw_ui_box(uint16_t dst,uint8_t width,uint8_t height){
    for(unsigned y=0;y<height;++y){
        unsigned row=y==0?0u:(y+1u==height?12u:6u);
        for(unsigned x=0;x<width;++x){
            unsigned col=x==0?0u:(x+1u==width?4u:2u);
            for(unsigned b=0;b<2u;++b)W(dst+y*0x40u+x*2u+b,rom((uint16_t)(0x0902u+row+col+b)));
        }
    }
}

/* $0C68 loads the O/U/I/N font patterns used by the contextual choice box.
   Reads in $0C51 intentionally skip the remaining three planes. */
uint16_t gaw_ui_load_choice_font_next(uint16_t src){
    uint16_t dst=(uint16_t)(rom(src)|(uint16_t)rom(src+1u)<<8);src+=2u;
    for(uint8_t ch=rom(src++);ch;ch=rom(src++)){
        uint16_t glyph=(uint16_t)(0x87C6u+(uint16_t)(uint8_t)(ch-0x41u)*8u);
        W(0xC01Fu,3);
        video_address(dst);
        for(unsigned y=0;y<8u;++y){uint8_t v=rom((uint16_t)(glyph+y));for(unsigned p=0;p<4u;++p)gaw_sms_vdp_data_write(p<2u?v:0);}
        video_address(dst);
        for(unsigned y=0;y<8u;++y){gaw_sms_vdp_data_write(0xFF);for(unsigned p=0;p<3u;++p)(void)gaw_sms_vdp_data_read();}
        dst=(uint16_t)(dst+0x20u);
    }
    return src;
}
void gaw_ui_load_choice_font(uint16_t src){(void)gaw_ui_load_choice_font_next(src);}

static uint8_t choose_loop(void){
    W(0xDCC2u,0xFF);
    for(;;){
        uint16_t cursor=R16(0xDCC0u),src=R(0xDCC2u)==0xFFu?0x615Cu:0x615Au;
        for(unsigned y=0;y<2u;++y)for(unsigned b=0;b<2u;++b)W(cursor+y*0x40u+b,rom((uint16_t)(src+y*2u+b)));
        gaw_wait_frame();gaw_ui_upload_name_table();
        uint8_t pressed=R(RAM_INPUT_PRESSED),old=R(0xDCC2u),choice=old;
        if(pressed&0x20u){W(0xDE08u,0xAB);return old;}
        if(pressed&0x10u)choice=0;
        else if((pressed&1u)&&old!=0xFFu)choice=0xFF;
        else if(pressed&2u)choice=0;
        if(choice!=old){W(0xDCC2u,choice);W(0xDE08u,0x95);}
    }
}

static uint8_t choice_at(uint16_t box){
    gaw_ui_box(box,6,4);W16(0xDCC0u,box+0x42u);
    for(unsigned y=0;y<2u;++y)for(unsigned b=0;b<6u;++b)W(box+0x44u+y*0x40u+b,rom((uint16_t)(0x614Eu+y*6u+b)));
    return choose_loop();
}
uint8_t gaw_ui_yes_no(void){
    gaw_ui_load_choice_font(0x6160u);
    uint8_t e=(uint8_t)(R(0xC313u)+0x10u);e=(uint8_t)((e>>2)|(e<<6));
    return choice_at((uint16_t)(0xD600u+(uint16_t)(uint8_t)(R(0xC311u)-0x18u)*8u+e));
}
uint8_t gaw_ui_yes_no_card(void){gaw_ui_load_choice_font(0x6160u);return choice_at(0xD9F2u);}

/* $0818 text mapping used by the fixed-position Oui/Non variant. */
uint8_t gaw_ui_yes_no_fixed(void){
    uint16_t box=0xD9F2u,dst=box+0x44u,line=dst,src=0x6167u;
    gaw_ui_box(box,6,4);W16(0xDCC0u,dst);
    uint16_t end=(uint16_t)(rom(0x8AE4u)|(uint16_t)rom(0x8AE5u)<<8);
    unsigned count=(unsigned)rom(0x8AE6u)|((unsigned)rom(0x8AE7u)<<8);
    for(uint8_t ch=rom(src++);ch;ch=rom(src++)){
        if(ch==0xFFu){line=(uint16_t)(line+0x40u);dst=line;W16(0xDCC0u,line);continue;}
        unsigned n=count;uint16_t at=end;
        while(n){uint8_t v=rom(at--);--n;if(v==ch)break;}
        W(dst++,(uint8_t)(n+rom(0x8AE8u)));W(dst++,rom(0x8AE9u));
    }
    W16(0xDCC0u,box+0x42u);return choose_loop();
}

/* Dialogue bitmap plane, $07CD. x/y follow the original DE convention:
   D is the pixel column, E is the scanline within the column-major buffer. */
static void pixel(uint8_t x,uint8_t y,int set){
    uint16_t at=(uint16_t)(0xD100u+(unsigned)(x&0xF8u)*5u+y);
    uint8_t bit=rom((uint16_t)(0x0045u+(x&7u)));
    W(at,set?(uint8_t)(R(at)|bit):(uint8_t)(R(at)&(uint8_t)~bit));
}
static void frozen_frame(void){W(0xC033u,1);gaw_wait_frame();W(0xC033u,0);}
void gaw_ui_wipe_name_table(void){
    W(0xDE08u,0xA6);
    for(unsigned column=0;column<20u;++column){
        frozen_frame();
        for(uint16_t dst=(uint16_t)(0x7800u+column*2u);dst<=0x7E00u;dst=(uint16_t)(dst+40u)){
            video_address(dst);gaw_sms_vdp_data_write(0xFF);gaw_sms_vdp_data_write(0x18);
        }
    }
    gaw_ui_display_reset();
}
void gaw_ui_display_reset(void){
    W(0xC010u,R(0xC010u)&0xEFu);W(0xC011u,R(0xC011u)&0xBFu);
    video_address((uint16_t)(0x8000u|R(0xC010u)));video_address((uint16_t)(0x8100u|R(0xC011u)));
    W(0xDD40u,0xD0);video_address(0x7F00u);gaw_sms_vdp_data_write(0xD0);
}
/* $0AD1/$0ADE adjusts one two-bit RGB component at a time. The original
   waits twice only after a pass that changes at least one palette entry. */
unsigned gaw_ui_palette_step(uint8_t step){
    uint8_t mask=(uint8_t)(step*3u);unsigned changed=0;
    for(unsigned i=0;i<32u;++i){
        uint16_t at=(uint16_t)(0xDCA0u+i);
        uint8_t current=R(at),target=(uint8_t)(R(at+32u)&mask),component=(uint8_t)(current&mask);
        if(component!=target){W(at,component<target?current+step:current-step);++changed;}
    }
    return changed;
}
static void palette_transition(uint16_t steps){
    for(uint8_t step=rom(steps);step;step=rom(++steps)){
        for(;;){
            unsigned changed=gaw_ui_palette_step(step);
            if(!changed)break;
            gaw_wait_frame();gaw_wait_frame();
        }
    }
}
void gaw_ui_transition_palette(void){palette_transition(0x0B0Au);}
void gaw_ui_fade_in(void){
    memcpy(gaw_ram_ptr(0xDCC0u),gaw_ram_ptr(0xDCA0u),32);
    memset(gaw_ram_ptr(0xDCA0u),0,32);
    uint8_t reg=(uint8_t)(R(0xC011u)|0x20u);
    video_address((uint16_t)(0x8100u|reg));(void)gaw_video_status_read();gaw_wait_frame();
    reg|=0x40u;video_address((uint16_t)(0x8100u|reg));W(0xC011u,reg);
    video_address((uint16_t)(0x8000u|R(0xC010u)));palette_transition(0x0B0Au);
}
void gaw_ui_fade_out(void){
    memset(gaw_ram_ptr(0xDCC0u),0,32);palette_transition(0x0B0Eu);gaw_ui_display_reset();
}
void gaw_ui_fade_grayscale(void){
    W(0xDD40u,0xD0);video_address(0x7F00u);gaw_sms_vdp_data_write(0xD0);
    memcpy(gaw_ram_ptr(0xDCC0u),gaw_ram_ptr(0xDCA0u),32);
    for(unsigned i=0;i<16u;++i){uint8_t color=R(0xDCC0u+i);unsigned intensity=(color&3u)+((color>>2)&3u)+((color>>4)&3u);W(0xDCC0u+i,rom((uint16_t)(0x2670u+intensity)));}
    palette_transition(0x0B0Au);
}
/* $1FA7/$2003 reveals sixteen rectangular rings, preserving the exact
   order of writes and the two-frame barrier preceding each ring. */
void gaw_ui_reveal_world(void){
    video_address(0x7800u);
    for(unsigned i=0;i<0x300u;++i){gaw_sms_vdp_data_write(0xFF);gaw_sms_vdp_data_write(0x18);}
    gaw_ui_fade_in();
    for(unsigned ring=0;ring<16u;++ring){
        uint16_t table=(uint16_t)(0x2011u+ring*4u),dst=(uint16_t)(rom(table)|((uint16_t)rom(table+1u)<<8));
        unsigned rows=rom(table+2u),columns=rom(table+3u);
        gaw_wait_frame();gaw_wait_frame();
        for(unsigned side=0;side<4u;++side){
            unsigned count=(side&1u)?rows:columns;if(!count)count=256u;
            int delta=side==0?2:side==1?64:side==2?-2:-64;
            while(count--){dst=(uint16_t)(dst+delta);video_address(dst);gaw_sms_vdp_data_write(R((uint16_t)(dst+0x5E00u)));gaw_sms_vdp_data_write(R((uint16_t)(dst+0x5E01u)));}
        }
    }
}
static void dialogue_flush(void){
    W(0xDE08u,0x9F);frozen_frame();
    for(unsigned i=0;i<0x410u;++i)video_byte((uint16_t)(0x2001u+i*4u),R(0xD100u+i));
}
static void page_cursor(void){video_byte(0x3CDEu,(R(RAM_FRAME_COUNTER)&8u)?0xFCu:0xFDu);}
static void dialogue_pause(void){
    dialogue_flush();W(RAM_FRAME_COUNTER,0);
    do{frozen_frame();page_cursor();}while((R(RAM_INPUT_PRESSED)&0x30u)==0);
    W(RAM_FRAME_COUNTER,0xFF);page_cursor();
}
static void new_line(void){
    W(0xDCCDu,(uint8_t)(R(0xDCCDu)+1u));
    unsigned y=(uint8_t)(R(0xDCC8u)+10u);
    if(y<0x28u)W(0xDCC8u,y);
    else{
        if((R(0xDCCDu)&3u)==0)dialogue_pause();
        for(unsigned i=0;i<4u;++i){
            unsigned shift=rom((uint16_t)(0x06B8u+i));
            /* Overlapping LDIR consumes a few bytes beyond the plane buffer. */
            for(unsigned k=0;k<0x410u;++k)W(0xD100u+k,R(0xD100u+shift+k));
            for(unsigned tail=0;tail<shift;++tail)for(unsigned k=0;k<26u;++k)W(0xD127u-tail+k*0x28u,0);
            dialogue_flush();
        }
    }
    W(0xDCC9u,0);
}
static void commit_cursor(void){
    uint8_t c=R(0xDCC6u);W(0xDCC6u,(uint8_t)((c<<1)|(c&1u)));
    W16(0xDCC4u,R16(0xDCC0u));
}
static uint16_t next_argument(void){uint16_t p=R16(0xDCC2u);uint16_t v=R16(p);W16(0xDCC2u,p+2u);return v;}
static void text_run(void);
static void insert_text(int numeric){
    W16(0xDCC8u,R16(0xDCCAu));
    uint16_t old_src=R16(0xDCC0u),old_flags=R16(0xDCC6u),argument=next_argument();
    if(!numeric){W(0xDCC6u,(uint8_t)old_flags|1u);W16(0xDCC0u,argument);}
    else{
        uint16_t value=R16(argument);unsigned digits=0;int started=0;
        const unsigned scale[]={10000,1000,100,10,1};
        for(unsigned i=0;i<5u;++i){unsigned d=value/scale[i];value=(uint16_t)(value%scale[i]);if(d||started||i==4u){W(0xD510u+digits++,0x30u+d);started=1;}}
        W(0xD510u+digits,0);W16(0xDCC0u,0xD510u);
    }
    text_run();W16(0xDCC0u,old_src);W16(0xDCC6u,old_flags);W16(0xDCC8u,R16(0xDCCAu));
}
static void text_run(void){
    W16(0xDCCAu,R16(0xDCC8u));
    for(;;){
        uint16_t src=R16(0xDCC0u);uint8_t ch=text_byte(src);W16(0xDCC0u,src+1u);
        if(ch==0xB0u)ch=0x2D;
        W(0xDCC7u,ch);
        if(ch==0){dialogue_flush();return;}
        if(ch==0xFFu){new_line();commit_cursor();dialogue_flush();W16(0xDCCAu,R16(0xDCC8u));continue;}
        if(ch==0x20u){W16(0xDCC8u,(uint16_t)(R16(0xDCCAu)+0x0600u));commit_cursor();dialogue_flush();W16(0xDCCAu,R16(0xDCC8u));continue;}
        if(ch==0x5Cu){W(0xDCC6u,R(0xDCC6u)^1u);continue;}
        if(ch==0x25u||ch==0x23u){insert_text(ch==0x23u);continue;}
        if(ch==0x24u){dialogue_pause();continue;}
        unsigned count=0xBFu;uint16_t map=0x8994u;
        while(count){uint8_t v=rom(map--);--count;if(v==ch)break;}
        if((R(0xDCC6u)&1u)&&count>=0x88u&&count<0xBFu)count-=0x37u;
        uint8_t ox=R(0xDCCBu),oy=R(0xDCCAu);
        unsigned width=rom((uint16_t)(0x8995u+count));
        W(0xDCCBu,(uint8_t)(R(0xDCCBu)+width+1u));
        if(R(0xDCCBu)>=0xD0u){
            W(0xDCC7u,0xFF);uint8_t flags=R(0xDCC6u);W(0xDCC6u,(flags>>1)|(flags<<7));W16(0xDCC0u,R16(0xDCC4u));
            uint8_t y=R(0xDCC8u),x=R(0xDCC9u);
            for(unsigned col=x;col<0xD0u;++col)for(unsigned row=0;row<10u;++row)pixel((uint8_t)col,(uint8_t)(y+row),0);
            new_line();commit_cursor();dialogue_flush();W16(0xDCCAu,R16(0xDCC8u));continue;
        }
        for(unsigned y=0;y<10u;++y){uint8_t row=rom((uint16_t)(0x8000u+count*10u+y));for(unsigned bit=0;bit<8u;++bit)if(row&(0x80u>>bit))pixel((uint8_t)(ox+bit),(uint8_t)(oy+y),1);}
        int punct=0;for(unsigned i=0;i<10u;++i)if(ch==rom((uint16_t)(0x8A54u+i)))punct=1;
        if(punct){W16(0xDCC8u,R16(0xDCCAu));commit_cursor();dialogue_flush();W16(0xDCCAu,R16(0xDCC8u));}
    }
}
void gaw_ui_show_message(uint16_t resource){
    frozen_frame();
    memcpy(gaw_ram_ptr(0xD600u),gaw_sms_vram()+0x3800u,0x600u);
    gaw_ui_show_prepared_message(resource);
}
void gaw_ui_show_prepared_message(uint16_t resource){
    W16(0xDCC0u,resource);W16(0xDCC4u,resource);W16(0xDCC2u,0xDCE0u);
    W16(0xDCC8u,0);W16(0xDCCAu,0);W(0xDCCDu,0);W(0xDCC6u,0xFF);
    memset(gaw_ram_ptr(0xD100u),0,0x410u);gaw_ui_box(0xD944u,28,7);
    uint16_t tile=0x1900u;
    for(unsigned x=0;x<26u;++x)for(unsigned y=0;y<5u;++y)W16(0xD986u+x*2u+y*0x40u,tile++);
    video_address(0x6000u);
    for(unsigned i=0;i<0x410u;++i){gaw_sms_vdp_data_write(0xFF);for(unsigned p=0;p<3u;++p)gaw_sms_vdp_data_write(0);}
    frozen_frame();gaw_ui_upload_name_table();text_run();
}

/* $638D/$6398: modal strip and its original font setup. */
void gaw_ui_status_box(void){
    for(unsigned i=0;i<0x100u;i+=2u)W16(0xDB00u+i,0x18FFu);
    gaw_ui_box(0xDAC2u,30,5);gaw_wait_frame();
    gaw_ui_upload_name_table();
}
void gaw_ui_status_font(void){
    W(0xC01Fu,3);video_address(0x5A00u);
    for(unsigned i=0;i<28u*8u;++i){uint8_t bits=rom((uint16_t)(0x87C6u+i));gaw_sms_vdp_data_write(bits);gaw_sms_vdp_data_write(bits);gaw_sms_vdp_data_write(0);gaw_sms_vdp_data_write(0);}
    video_address(0x5A00u);
    for(unsigned i=0;i<28u*8u;++i){gaw_sms_vdp_data_write(0xFFu);(void)gaw_sms_vdp_data_read();(void)gaw_sms_vdp_data_read();(void)gaw_sms_vdp_data_read();}
}
/* $0812: fixed-width text using the bank-3 character descriptor. */
static uint16_t fixed_text(uint16_t source,uint16_t destination,uint16_t descriptor){
    W16(0xDCC0u,destination);
    for(uint8_t ch=text_byte(source++);ch;ch=text_byte(source++)){
        if(ch==0xFFu){destination=(uint16_t)(R16(0xDCC0u)+0x40u);W16(0xDCC0u,destination);continue;}
        uint16_t p=(uint16_t)(rom(descriptor)|(uint16_t)rom(descriptor+1u)<<8);
        uint16_t count=(uint16_t)(rom(descriptor+2u)|(uint16_t)rom(descriptor+3u)<<8);
        do{uint8_t found=rom(p--);--count;if(found==ch)break;}while(count);
        W(destination++,(uint8_t)((uint8_t)count+rom(descriptor+4u)));W(destination++,rom(descriptor+5u));
    }
    return source;
}
void gaw_ui_fixed_text(uint16_t source,uint16_t destination){fixed_text(source,destination,0x8A8Eu);}
uint16_t gaw_ui_fixed_text_next(uint16_t source,uint16_t destination){return fixed_text(source,destination,0x8A8Eu);}
void gaw_ui_inventory_text(uint16_t source,uint16_t destination){fixed_text(source,destination,0x8AE4u);}
uint16_t gaw_ui_inventory_text_next(uint16_t source,uint16_t destination){return fixed_text(source,destination,0x8AE4u);}
void gaw_ui_decimal(uint8_t value,uint16_t destination){
    const uint8_t digits[3]={(uint8_t)(value/100u),(uint8_t)(value%100u/10u),(uint8_t)(value%10u)};
    for(unsigned i=0;i<3u;++i){W(destination++,0xF0u+digits[i]);W(destination++,0x18);}
}
void gaw_ui_load_font(uint8_t characters,uint16_t destination){
    unsigned count=(unsigned)characters*8u;if(!count)count=65536u;
    gaw_assets_load_masked(3,0x87C6u,destination,(uint16_t)count,3);
    video_address(destination);
    while(count--){gaw_sms_vdp_data_write(0xFF);for(unsigned p=0;p<3u;++p)(void)gaw_sms_vdp_data_read();}
}
void gaw_ui_clear_playfield(void){
    W(0xDD40u,0xD0);
    for(unsigned i=0;i<0x500u;i+=2u)W16(0xD600u+i,0x08FFu);
    gaw_ui_upload_playfield();
}
void gaw_ui_upload_playfield(void){
    frozen_frame();video_address(0x7800u);
    gaw_sms_vdp_data_write_block(gaw_ram_ptr(0xD600u),0x500u);
}
void gaw_ui_menu_reset(void){
    gaw_ui_fade_out();video_address(0x8800u);video_address(0x8900u);W16(0xC018u,0);
    video_address(0x7F40u);for(unsigned i=0;i<64u;++i)gaw_sms_vdp_data_write(0);
    video_address(0x7800u);for(unsigned i=0;i<0x380u;++i){gaw_sms_vdp_data_write(0xFA);gaw_sms_vdp_data_write(1);}
    for(unsigned i=0;i<0x600u;i+=2u)W16(0xD600u+i,0x01FA);
    memset(gaw_ram_ptr(0xDCA0u),0,32);
}
void gaw_ui_load_inventory_font(void){gaw_ui_load_font(32,0x5600u);gaw_assets_load_masked(4,0xA4D4u,0x7E00u,40,3);}
uint16_t gaw_ui_icon_tiles(uint16_t tile,uint16_t destination,unsigned count){
    if(!count)count=256u;
    for(unsigned i=0;i<count;++i){W16(destination,tile++);W16(destination+2u,tile++);W16(destination+64u,tile++);W16(destination+66u,tile++);destination=(uint16_t)(destination+6u);}
    return tile;
}
/* $0A78: append a fixed sprite descriptor with cumulative X/Y deltas. */
void gaw_ui_sprite(uint8_t bank,uint16_t source,uint16_t entity){
    uint8_t fixed=source<0x4000u?0u:source<0x8000u?1u:bank;
    unsigned count=gaw_sms_rom_bank_read(fixed,source++);if(!count)count=256u;
    uint16_t dst=R16(0xC024u);uint8_t position=R(entity+0x11u);
    for(unsigned i=0;i<count;++i){position=(uint8_t)(position+gaw_sms_rom_bank_read(fixed,source++));W(dst++,position);}
    W(dst,0xD0);W16(0xC024u,dst);dst=R16(0xC026u);position=R(entity+0x13u);
    for(unsigned i=0;i<count;++i){position=(uint8_t)(position+gaw_sms_rom_bank_read(fixed,source++));W(dst++,position);W(dst++,gaw_sms_rom_bank_read(fixed,source++));}
    W16(0xC026u,dst);
}
