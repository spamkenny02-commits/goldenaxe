#include <string.h>
#include "include/gaw_audio.h"
#include "include/gaw_platform.h"
#include "include/gaw_ram.h"
#include "include/gaw_video.h"

#define R(a) gaw_ram_read8((uint16_t)(a))
#define W(a,v) gaw_ram_write8((uint16_t)(a),(uint8_t)(v))
#define R16(a) gaw_ram_read16le((uint16_t)(a))
#define W16(a,v) gaw_ram_write16le((uint16_t)(a),(uint16_t)(v))
static uint32_t faults;
static uint8_t byte(uint16_t a){return a>=0xC000u?R(0xC000u+(a&0x1FFFu)):gaw_sms_rom_bank_read(a<0x4000u?0u:a<0x8000u?1u:6u,a);}
static uint16_t word(uint16_t a){return (uint16_t)(byte(a)|((uint16_t)byte(a+1u)<<8));}
static uint8_t rol(uint8_t a){return (uint8_t)((a<<1)|(a>>7));}
static void psg(uint8_t a){gaw_platform_sound_write(0x7F,a);}
static uint8_t duration(uint16_t channel,uint8_t a){return (uint8_t)(a*R(channel+2u));}
static void silence(void){for(unsigned i=0;i<10u;++i)psg(byte((uint16_t)(0x8412u+i)));W(0xDE05u,0x80);}
static void clear_tracks(void){memset(gaw_ram_ptr(0xDE05u),0,0x18B);silence();}
static void priority(uint16_t request,uint16_t level,uint16_t destination){
    uint8_t command=R(request),index=command&0x7Fu;
    if(index){uint8_t p=byte((uint16_t)(0x8AD5u+index-1u));if(p>=R(level)){W(level,p&0x7Fu);W(destination,command);}}
    W(request,0);
}
static uint16_t track_init(uint16_t channel,uint16_t source){
    for(unsigned i=0;i<9u;++i)W(channel+i,byte(source++));
    W(channel+9u,0x30);W(channel+10u,1);W(channel+0x27u,0);W(channel+0x28u,0);W(channel+0x29u,0);return source;
}
static void overlay_stop(uint8_t command){
    W(0xDE0Eu,command);uint8_t which=R(0xDE0Fu);if(which&0x80u)return;
    uint16_t c=which?0xDF60u:0xDF30u;W(c,which);psg((uint8_t)(R(c+1u)+0x1Fu));
}
static uint16_t effect_record(uint16_t source,uint8_t command){
    W(0xDE0Fu,command);uint8_t tone=byte(source+1u);uint16_t c,music;
    if(tone==0xA0u){c=0xDF00u;music=0xDE70u;}
    else if(tone==0xC0u){
        if(!(R(0xDF60u)&0x40u)){W(0xDF60u,R(0xDF60u)|4u);psg(0xFF);}
        c=0xDF30u;music=0xDEA0u;
    }else{c=0xDF60u;music=0xDED0u;}
    W(music,R(music)|4u);return track_init(c,source);
}
static void select_command(void){
    uint8_t command=R(0xDE05u);
    if(!(command&0x80u)){clear_tracks();return;}
    if(command<0x90u){
        if(command<0x81u)return;
        uint8_t index=(uint8_t)(command-0x81u);clear_tracks();
        uint8_t tempo=byte((uint16_t)(0x8B09u+index));W(0xDE01u,tempo);W(0xDE02u,tempo);uint16_t p=word((uint16_t)(0x8B16u+index*2u));unsigned n=byte(p++);
        for(unsigned i=0;i<n;++i){p=track_init((uint16_t)(0xDE40u+i*0x30u),p);}W(0xDE05u,0x80);return;
    }
    if(command<0xADu){uint16_t p=word((uint16_t)(0x8B30u+(command-0x90u)*2u));unsigned n=byte(p++);for(unsigned i=0;i<n;++i)p=effect_record(p,command);W(0xDE05u,0x80);return;}
    if(command==0xB0u){W(0xDE0Bu,12);W(0xDE0Cu,18);W(0xDE0Du,18);W(0xDE05u,0x80);}
    else if(command==0xB1u||command>=0xB5u)clear_tracks();
    else if(command==0xB2u){for(unsigned i=0;i<3u;++i)W16(0xDF03u+i*0x30u,0x814E);}
    else if(command==0xB3u){overlay_stop(0);W(0xDE05u,0x80);}
    else if(command==0xADu||command==0xAEu||command==0xAFu){++faults;clear_tracks();}
    else{++faults;clear_tracks();} /* B4 points outside the driver's table. */
}
static void overlay_start(void){
    uint8_t request=R(0xDE09u);if(request==0x80u){W(0xDE09u,0);overlay_stop(0);return;}if(!(request&0x7Fu))return;
    priority(0xDE09u,0xDE10u,0xDE0Eu);uint8_t command=R(0xDE0Eu);overlay_stop(command);
    uint16_t p=(uint16_t)(word((uint16_t)(0x8B30u+(uint8_t)(command-0x90u)*2u))+1u);uint8_t tone=byte(p+1u);
    uint16_t c,music;uint8_t which;
    if(tone!=0xC0u){c=0xDF60u;music=0xDED0u;which=1;}
    else{
        if((R(0xDF60u)&0xC0u)==0x80u){W(0xDE0Fu,0x80);return;}
        c=0xDF30u;music=0xDEA0u;which=0;
    }
    if(R(c)&0x80u){W(0xDE0Fu,R(c));return;}
    W(0xDE0Fu,which);W(music,R(music)|4u);(void)track_init(c,p);
}
static void volume_stop(uint16_t c){W(c,R(c)|0x10u);if(!(R(c)&4u))psg((uint8_t)(R(c+1u)+0x1Fu));}
static void release(uint16_t c){if(R(c)&2u)return;if(R(c+7u)&0x80u)W(c+0x1Du,(R(c+0x1Du)&15u)|0x80u);else volume_stop(c);}
static void mod_start(uint16_t c){
    if((R(c+6u)&0x80u)&&!(R(c)&2u)){
        uint16_t p=R16(c+0x10u);for(unsigned i=0;i<3u;++i)W(c+0x14u+i,byte(p+i));W(c+0x17u,byte(p+3u)>>1);W16(c+0x12u,0);
    }
    if((R(c+7u)&0x80u)&&!(R(c)&2u)&&!(R(c+0x1Du)&0x80u)){W(c+0x1Fu,0xFF);W(c+0x1Du,R(c+0x1Eu)|0x10u);}
}
/* One sequencer command. Cursor is the original parameter address; most
   commands consume it, while jumps/calls replace it explicitly. */
static int stream_command(uint16_t c,uint8_t opcode,uint16_t *cursor){
    uint16_t p=*cursor;uint8_t a=byte(p);unsigned index=opcode-0xE0u;
    switch(index){
        case 0:case 9:
            W(c+7u,0x80);for(unsigned i=0;i<5u;++i)W(c+0x20u+i,byte(p+i));*cursor=(uint16_t)(p+5u);return 1;
        case 1:W(c+0x25u,a);break;
        case 2:{
            uint8_t previous=R(c+0x26u),mask=(uint8_t)~a;W(c+0x26u,a);uint8_t tone=R(c+1u);
            unsigned shift=tone==0x80u?0u:tone==0xA0u?1u:tone==0xC0u?2u:3u;
            while(shift--){previous=rol(previous);mask=rol(mask);}a=(uint8_t)((R(0xDE12u)|previous)&mask);W(0xDE12u,a);gaw_platform_sound_write(6,a);break;
        }
        case 3:a=(uint8_t)((gaw_platform_entropy8()+R(c+3u))&7u);W(c+7u,a);W(c+0x1Au,0xE5);break;
        case 4:W(0xDE18u,(R(0xDE18u)+a)&15u);break;
        case 5:W(c+0x1Eu,a?8:0);break;
        case 6:if(!R(0xDE0Bu))W(c+8u,(R(c+8u)+a)&15u);break;
        case 7:W(c,R(c)|2u);return 1; /* parameter is the next note byte */
        case 8:a=duration(c,a);W(c+0x0Eu,a);W(c+0x0Fu,a);break;
        case 10:
            if(a&0x80u){W(c,R(c)|1u);W(c+0x18u,a);a=byte(++p);W(c+0x19u,a);W(c+0x1Au,a);}
            else{W(c,R(c)&0xFEu);W(c+0x1Au,0);++p;}break;
        case 11:case 28:break;
        case 12:
            if(a){a=(uint8_t)(gaw_platform_entropy8()+R(c+3u));a=(a&1u)?(uint8_t)(a|0xFCu):(uint8_t)(a&3u);W(c+0x25u,a);W(c+0x1Au,0xE6);}
            else{W(c+0x25u,0);W(c+0x1Au,0);}break;
        case 13:W(0xDE01u,a);W(0xDE02u,a);break;
        case 14:W(c+0x1Cu,a);break;
        case 16:W16(c+0x10u,p);W(c+6u,0x80);*cursor=(uint16_t)(p+4u);return 1;
        case 17:W(0xDE12u,0x80); /* fall through */
        case 18:{
            uint8_t tone=R(c+1u);uint16_t music;
            if(tone==0xA0u)music=0xDE70u;
            else if(tone==0xC0u)music=R(0xDF60u)&0x80u?0xDF60u:0xDEA0u;
            else{
                if(!(R(c)&0x40u)&&!(R(0xDF30u)&0x80u)){W(0xDEA0u,(R(0xDEA0u)&0xBBu)|0x10u);W(0xDF30u,0);}
                music=0xDED0u;
            }
            W(music,(R(music)&0xFBu)|0x10u);psg(tone|0x1Fu);W(0xDE11u,0);W(c,0);
            if(R(0xDE0Eu)){W(0xDE09u,R(0xDE0Eu));overlay_start();}return 0;
        }
        case 19:{
            if(!(R(0xDE0Fu)&0x80u)&&((a|0xFCu)==0xFFu)&&(R(0xDF30u)&0x80u)){
                W(0xDED0u,(R(0xDED0u)&0xFBu)|0x10u);W(c,0);psg(0xFF);W(0xDE0Fu,0xFF);return 0;
            }
            psg(a);
            if((a|0xFCu)==0xFFu){psg(0xDF);W(c,R(c)&0xBFu);W(0xDEA0u,R(0xDEA0u)|4u);W(0xDF30u,R(0xDF30u)|4u);}
            else{W(c,R(c)|0x40u);uint16_t other=R(0xDF30u)&0x80u?0xDF30u:0xDEA0u;W(other,R(other)&0xFBu);}break;
        }
        case 20:W(c+6u,a);break;
        case 21:W(c+7u,a);break;
        case 22:*cursor=word(p);return 1;
        case 23:{
            uint16_t counter=(uint16_t)(c+(uint8_t)(a+0x27u));++p;if(!R(counter))W(counter,byte(p));++p;W(counter,R(counter)-1u);
            *cursor=R(counter)?word(p):(uint16_t)(p+2u);return 1;
        }
        case 24:{uint8_t stack=(uint8_t)(R(c+9u)-2u);W(c+9u,stack);W16(c+stack,p+1u);*cursor=word(p);return 1;}
        case 25:{uint8_t stack=R(c+9u);*cursor=(uint16_t)(R16(c+stack)+1u);W(c+9u,stack+2u);return 1;}
        case 26:W(c+2u,a);break;
        case 27:W(c+5u,R(c+5u)+a);break;
        case 29:W(c,a==1u?R(c)|8u:R(c)&0xF7u);break;
        case 30:case 31:
            if(a){uint8_t entropy;do{entropy=gaw_platform_entropy8();}while(!entropy);a=duration(c,a&entropy);}W(c+0x0Eu,a);W(c+0x0Fu,a);break;
        default:++faults;W(c,0);return 0;
    }
    *cursor=(uint16_t)(p+1u);return 1;
}
static void noise_note(uint16_t c,uint8_t note){
    uint8_t envelope,volume,control;
    if(note&1u){envelope=1;volume=4;control=0xE4;}
    else if(note&2u){envelope=3;volume=6;control=0xE4;}
    else if(note&4u){envelope=1;volume=1;control=0xE6;}
    else if(note&8u){envelope=2;volume=3;control=0xE5;}
    else if(note&16u){envelope=3;volume=3;control=0xE6;}
    else if(note&32u){envelope=4;volume=4;control=0xE4;}
    else{volume_stop(c);return;}
    W(c+7u,envelope);W(c+8u,R(0xDE18u)+volume);if(R(c)&4u)return;
    control=(uint8_t)(control+R(0xDE17u));W(0xDE13u,control);psg(control);
}
static int parse_note(uint16_t c,int noise,uint16_t *work_cursor){
    W(c,R(c)&(noise?0xEFu:0xEDu));uint16_t p=R16(c+3u);
    for(unsigned commands=0;commands<256u;++commands){
        uint8_t token=byte(p++);
        if(token>=0xE0u){if(!stream_command(c,token,&p))return 0;continue;}
        if(noise){
            if(token&0x80u){noise_note(c,token);token=byte(p++);if(token&0x80u){token=R(c+0x0Du);--p;}else{token=duration(c,token);W(c+0x0Du,token);}}
            else{token=duration(c,token);W(c+0x0Du,token);}
        }else if(R(c)&8u){
            uint16_t pitch=(uint16_t)((uint16_t)token<<8|byte(p++));if(pitch)pitch=(uint16_t)(pitch+(int8_t)R(c+5u));W16(c+0x0Bu,pitch);token=duration(c,byte(p++));W(c+0x0Du,token);
        }else if(token&0x80u){
            if(token==0x80u)release(c);
            else{W(c+0x1Du,R(c+0x1Du)&0x7Fu);uint8_t key=(uint8_t)((token&0x7Fu)+R(c+5u));W16(c+0x0Bu,word((uint16_t)(0x843Du+key*2u)));}
            token=byte(p++);if(token&0x80u){token=R(c+0x0Du);--p;}else{token=duration(c,token);W(c+0x0Du,token);}
        }else{token=duration(c,token);W(c+0x0Du,token);}
        W(c+0x0Au,token);W16(c+3u,p);*work_cursor=p;
        if(!(R(c)&2u)){
            if(!(R(c)&0x40u))W(c,R(c)&0xDFu);
            W(c+0x0Eu,R(c+0x0Fu));W(c+0x15u,0);if(!(R(c+7u)&0x80u))W(c+0x1Fu,0);
        }
        return 1;
    }
    ++faults;W(c,0);return 0;
}
static int pitch_frame(uint16_t c,uint16_t *pitch){
    uint8_t mode=R(c+6u);*pitch=R16(c+0x0Bu);if(!mode)return 1;
    if(mode&0x80u){
        uint8_t delay=(uint8_t)(R(c+0x14u)-1u);W(c+0x14u,delay);if(delay)return 1;W(c+0x14u,1);
        uint16_t phase=R16(c+0x12u),source=R16(c+0x10u);W(c+0x15u,R(c+0x15u)-1u);
        if(!R(c+0x15u)){W(c+0x15u,byte(source+1u));phase=(uint16_t)(phase+(int8_t)R(c+0x16u));W16(c+0x12u,phase);}
        *pitch=(uint16_t)(*pitch+phase);W(c+0x17u,R(c+0x17u)-1u);
        if(!R(c+0x17u)){W(c+0x17u,byte(source+3u));W(c+0x16u,0u-R(c+0x16u));}return 1;
    }
    uint16_t wave=word((uint16_t)(0x8A52u+(mode-1u)*2u));
    for(unsigned n=0;n<256u;++n){
        uint8_t value=byte((uint16_t)(wave+R(c+0x15u)));
        if(value==0x80u){W(c+0x15u,0);continue;}
        if(value==0x83u){*pitch=(uint16_t)(*pitch+1u);W(c+0x15u,byte(*pitch));continue;}
        if(value==0x81u||value==0x82u){W(c,R(c)|0x20u);return 0;}
        *pitch=(uint16_t)(*pitch+(int8_t)value);W(c+0x15u,R(c+0x15u)+1u);return 1;
    }
    ++faults;return 0;
}
static int volume_frame(uint16_t c,uint16_t work_cursor,uint8_t *volume){
    uint8_t mode=R(c+7u);*volume=mode;if(!mode)return 1;
    if(mode&0x80u){
        uint8_t phase=R(c+0x1Du),value=R(c+0x1Fu);unsigned sum;
        if(phase&0x10u){uint8_t delta=R(c+0x20u);value=value<delta?0:(uint8_t)(value-delta);if(!value)W(c+0x1Du,phase^0x30u);}
        else if(phase&0x20u){sum=value+R(c+0x21u);uint8_t limit=R(c+0x22u);value=sum>=limit?limit:(uint8_t)sum;if(value==limit)W(c+0x1Du,phase^((phase&8u)?0x30u:0x60u));}
        else if(phase&0x40u){sum=value+R(c+0x23u);value=sum>=255u?255:(uint8_t)sum;if(value==255u)W(c+0x1Du,phase&0x8Fu);}
        else{sum=value+R(c+0x24u);if(sum>255u){W(c+0x1Du,phase&15u);W(c+0x1Fu,255);volume_stop(c);return 0;}value=(uint8_t)sum;}
        W(c+0x1Fu,value);*volume=value>>4;return 1;
    }
    uint16_t wave=word((uint16_t)(0x897Fu+(mode-1u)*2u));
    for(unsigned n=0;n<256u;++n){
        uint8_t value=byte((uint16_t)(wave+R(c+0x1Fu)));
        if(value<0x80u){W(c+0x1Fu,R(c+0x1Fu)+1u);*volume=value;return 1;}
        if(value==0x80u){W(c+0x1Fu,0);continue;}
        if(value==0x81u){W(c,R(c)|0x10u);return 0;}
        if(value==0x82u){volume_stop(c);return 0;}
        W(c+0x1Fu,byte((uint16_t)(work_cursor+1u)));
    }
    ++faults;return 0;
}
static void channel_frame(uint16_t c,int noise,uint16_t *work_cursor){
    W(c+0x0Au,R(c+0x0Au)-1u);int new_note=!R(c+0x0Au),tone=0;
    if(new_note){if(!parse_note(c,noise,work_cursor)||noise)return;if(R(c)&0x14u)return;mod_start(c);tone=1;}
    else if(!noise){
        if(R(c)&4u)return;
        if(R(c+0x0Eu)){W(c+0x0Eu,R(c+0x0Eu)-1u);if(!R(c+0x0Eu))release(c);}
        tone=R(c+6u)&&!(R(c)&0x20u);
    }
    if(tone&&!(R(c)&0x40u)){
        uint16_t pitch;if(pitch_frame(c,&pitch)){
            *work_cursor=(uint16_t)(int16_t)(int8_t)R(c+0x25u);pitch=(uint16_t)(pitch+*work_cursor);uint8_t latch=R(c+1u);if(latch==0xE0u)latch=0xC0;
            uint8_t low=(uint8_t)pitch,high=(uint8_t)(pitch>>8);psg((uint8_t)((low&15u)|latch));uint8_t packed=(uint8_t)((low&0xF0u)|high);psg((uint8_t)((packed>>4)|(packed<<4)));
        }
    }
    uint8_t volume;if(!volume_frame(c,*work_cursor,&volume))return;if(R(c)&0x14u)return;
    volume=(uint8_t)(volume+R(c+8u));if(volume&16u)volume=15;psg((uint8_t)((volume|R(c+1u))+0x10u));
}
void gaw_audio_tick(void){
    uint8_t pause=R(0xDE0Au);if(pause){if(pause&0x80u){W(0xDE0Au,pause-1u);silence();}return;}
    for(unsigned i=0;i<3u;++i)priority((uint16_t)(0xDE06u+i),0xDE11u,0xDE05u);
    if(R(0xDE01u)){W(0xDE01u,R(0xDE01u)-1u);if(!R(0xDE01u)){W(0xDE01u,R(0xDE02u));for(unsigned i=0;i<4u;++i)W(0xDE4Au+i*0x30u,R(0xDE4Au+i*0x30u)+1u);}}
    if(R(0xDE0Bu)){
        uint8_t countdown=(uint8_t)(R(0xDE0Cu)-1u);
        if(countdown)W(0xDE0Cu,countdown);
        else{W(0xDE0Cu,R(0xDE0Du));W(0xDE0Bu,R(0xDE0Bu)-1u);if(!R(0xDE0Bu))clear_tracks();else{for(unsigned i=0;i<3u;++i){uint16_t at=(uint16_t)(0xDE48u+i*0x30u);uint8_t value=(uint8_t)(R(at)+1u);if(value<12u)W(at,value);}if(R(0xDE18u)+1u<12u)W(0xDE18u,R(0xDE18u)+1u);}}
    }
    select_command();overlay_start();
    if(R(0xDE03u)){uint8_t frame=(uint8_t)(R(0xDE04u)+1u);if(frame>=6u)frame=0;W(0xDE04u,frame);if(!frame)return;}
    uint16_t cursor=0xDE09u;
    for(unsigned i=0;i<7u;++i){uint16_t c=(uint16_t)(0xDE40u+i*0x30u);if(R(c)&0x80u)channel_frame(c,i==3u,&cursor);}
}
uint32_t gaw_audio_faults(void){return faults;}
void gaw_audio_reset_diagnostics(void){faults=0;}
