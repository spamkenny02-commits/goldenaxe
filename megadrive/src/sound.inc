/* Native PSG music reader, bank 6:8000..897D. Original sequence/envelope
 * data are read directly; this is not a Z80 CPU or a recorded audio stream. */
extern const u8 intro_bank6[],sound_low_rom[];
static u8 sound_ram[0x190];
static volatile u16 sound_unhandled_command;
static u16 sound_current_track;
static volatile u16 sound_request;
static volatile u16 sound_effect_request;
static u8 sound_read(u16 address) { return address<=0x400?sound_low_rom[address]:intro_bank6[(address-0x8000)&0x3fff]; }
static u16 sound_word(u16 address) { return sound_read(address)|((u16)sound_read(address+1)<<8); }
static u16 sound_ch_word(u8 *c,u16 offset) { return c[offset]|((u16)c[offset+1]<<8); }
static void sound_ch_set(u8 *c,u16 offset,u16 value) { c[offset]=value;c[offset+1]=value>>8; }
static void sound_mute(void)
{
    u16 n;
    for(n=0;n<10;n++) PSG_write(sound_read(0x8412+n));
}
static void sound_stop(void)
{
    memset(sound_ram+5,0,0x18b);sound_ram[5]=0x80;sound_mute();
}
static void sound_start(u16 command)
{
    u16 index,header,n;
    sound_stop();sound_current_track=command;
    if(command<0x81 || command>0x8d) return;
    index=command-0x81;sound_ram[1]=sound_ram[2]=sound_read(0x8b09+index);
    header=sound_word(0x8b16+index*2);
    for(n=0;n<sound_read(header) && n<4;n++)
    {
        u8 *c=sound_ram+0x40+n*0x30;u16 j;
        for(j=0;j<9;j++) c[j]=sound_read(header+1+n*9+j);
        c[9]=0x30;c[10]=1;
    }
}
/* 8097/80A8: three source queues share a priority latch; later ties win. */
static void sound_arbitrate(void)
{
    u16 n;
    for(n=6;n<9;n++)
    {
        u16 command=sound_ram[n],index=command&127,priority;
        if(index && index<=0x34)
        {
            priority=sound_read(0x8ad5+index-1);
            if(priority>=sound_ram[0x11])
            { sound_ram[0x11]=priority&127;sound_ram[5]=command; }
        }
        sound_ram[n]=0;
    }
}
static void sound_load_channel(u16 offset,u16 header)
{
    u8 *c=sound_ram+offset;u16 n;
    for(n=0;n<9;n++) c[n]=sound_read(header+n);
    c[9]=0x30;c[10]=1;c[0x27]=c[0x28]=c[0x29]=0;
}
/* 817C..81F7: effects borrow music channels; tone3 can also own noise. */
static void sound_start_effect(u16 command)
{
    u16 header=sound_word(0x8b30+(command-0x90)*2),n,count=sound_read(header++);
    sound_ram[0xf]=command;
    for(n=0;n<count && n<3;n++,header+=9)
    {
        u16 channel=sound_read(header+1),offset,background;
        if(channel==0xa0) { offset=0x100;background=0x70; }
        else if(channel==0xc0)
        {
            if(!(sound_ram[0x160]&64)) { sound_ram[0x160]|=4;PSG_write(0xff); }
            offset=0x130;background=0xa0;
        }
        else { offset=0x160;background=0xd0; }
        sound_ram[background]|=4;sound_load_channel(offset,header);
    }
    sound_ram[5]=0x80;
}
static void sound_dispatch(void)
{
    u16 command=sound_ram[5],n;
    if(command==0x80) return;
    if(command>=0x81 && command<=0x8d) { sound_start(command);return; }
    if(command>=0x90 && command<=0xac) { sound_start_effect(command);return; }
    if(command==0xb0) { sound_ram[0xb]=12;sound_ram[0xc]=sound_ram[0xd]=18;sound_ram[5]=0x80;return; }
    if(command==0xb2)
    {
        for(n=0;n<3;n++) sound_ch_set(sound_ram+0x100+n*0x30,3,0x814e);
        return;
    }
    if(command==0xb3)
    {
        u16 offset=sound_ram[0xf]?0x160:0x130;
        sound_ram[0xe]=0;
        if(!(sound_ram[0xf]&128)) { sound_ram[offset]=sound_ram[0xf];PSG_write(sound_ram[offset+1]+31); }
        sound_ram[5]=0x80;return;
    }
    sound_stop();
}
void sound_effect(u16 command) { sound_effect_request=command; }
void sound_effect_main(u16 command) { sound_request=command; }
static void sound_release(u8 *c)
{
    if(c[0]&2) return;
    if(c[7]&128) c[0x1d]=(c[0x1d]&15)|128;
    else { c[0]|=16;if(!(c[0]&4)) PSG_write(c[1]+31); }
}
static u8 sound_envelope(u8 *c)
{
    u16 value,table,index,guard;
    if(!c[7]) return 0;
    if(c[7]&128)
    {
        value=c[0x1f];
        if(c[0x1d]&16)
        {
            value=value<c[0x20]?0:value-c[0x20];
            if(!value) c[0x1d]^=0x30;
        }
        else if(c[0x1d]&32)
        {
            value+=c[0x21];if(value>c[0x22]) value=c[0x22];
            if(value==c[0x22]) c[0x1d]^=(c[0x1d]&8)?0x30:0x60;
        }
        else if(c[0x1d]&64)
        {
            value+=c[0x23];if(value>255) value=255;
            if(value==255) c[0x1d]&=0x8f;
        }
        else
        {
            value+=c[0x24];
            if(value>255)
            {
                value=255;c[0x1d]&=15;c[0]|=16;
                if(!(c[0]&4)) PSG_write(c[1]+31);
            }
        }
        c[0x1f]=value;return value>>4;
    }
    table=sound_word(0x897f+(c[7]-1)*2);
    for(guard=0;guard<64;guard++)
    {
        index=c[0x1f];value=sound_read(table+index);
        if(value<128) { c[0x1f]++;return value; }
        if(value==0x80) c[0x1f]=0;
        else if(value==0x81 || value==0x82)
        {
            c[0]|=16;
            if(value==0x82 && !(c[0]&4)) PSG_write(c[1]+31);
            return value;
        }
        else c[0x1f]=sound_read(table+index+1);
    }
    sound_unhandled_command=0x100;return 15;
}
static u16 sound_pitch(u8 *c)
{
    u16 base=sound_ch_word(c,11),table,index,guard;
    u8 mode=c[6],value;
    if(!mode) return base;
    if(mode&128)
    {
        s16 delta=(s16)sound_ch_word(c,0x12);
        if(--c[0x14]) return base;
        c[0x14]++;table=sound_ch_word(c,0x10);
        if(!--c[0x15]) { c[0x15]=sound_read(table+1);delta+=(s8)c[0x16];sound_ch_set(c,0x12,delta); }
        base+=delta;
        if(!--c[0x17]) { c[0x17]=sound_read(table+3);c[0x16]=-c[0x16]; }
        return base;
    }
    table=sound_word(0x8a52+(mode-1)*2);
    for(guard=0;guard<64;guard++)
    {
        index=c[0x15];value=sound_read(table+index);
        if(value==0x83) { base++;c[0x15]=sound_read(base); }
        else if(value==0x80) c[0x15]=0;
        else if(value==0x81 || value==0x82) { c[0]|=32;return table; }
        else { c[0x15]++;return base+(s8)value; }
    }
    sound_unhandled_command=0x101;return base;
}
static void sound_noise_note(u8 *c,u8 note)
{
    u16 mode=0,volume=0,noise=0;
    if(note&1) { mode=1;volume=4;noise=0xe4; }
    else if(note&2) { mode=3;volume=6;noise=0xe4; }
    else if(note&4) { mode=1;volume=1;noise=0xe6; }
    else if(note&8) { mode=2;volume=3;noise=0xe5; }
    else if(note&16) { mode=3;volume=3;noise=0xe6; }
    else if(note&32) { mode=4;volume=4;noise=0xe4; }
    else { c[0]|=16;PSG_write(c[1]+31);return; }
    c[7]=mode;c[8]=sound_ram[0x18]+volume;
    if(!(c[0]&4)) { sound_ram[0x13]=noise+sound_ram[0x17];PSG_write(sound_ram[0x13]); }
}
static bool sound_sequence(u8 *c,bool noise)
{
    u16 cursor=sound_ch_word(c,3),guard;
    c[0]&=noise?~16:~18;
    for(guard=0;guard<256;guard++)
    {
        u8 note=sound_read(cursor++),value;
        u16 frequency;
        if(note>=0xe0)
        {
            value=sound_read(cursor);
            switch(note)
            {
                case 0xe0:case 0xe9:
                    c[7]=128;for(frequency=0;frequency<5;frequency++) c[0x20+frequency]=sound_read(cursor+frequency);cursor+=5;break;
                case 0xe1:c[0x25]=value;cursor++;break;
                case 0xe2:c[0x26]=value;cursor++;break; /* GG stereo has no MD PSG equivalent. */
                case 0xe4:sound_ram[0x18]=(sound_ram[0x18]+value)&15;cursor++;break;
                case 0xe5:c[0x1e]=value?8:0;cursor++;break;
                case 0xe6:if(!sound_ram[0xb]) c[8]=(c[8]+value)&15;cursor++;break;
                case 0xe7:c[0]|=2;break;
                case 0xe8:c[14]=c[15]=(u8)(value*c[2]);cursor++;break;
                case 0xeb:case 0xfc:cursor++;break;
                case 0xed:sound_ram[1]=sound_ram[2]=value;cursor++;break;
                case 0xee:c[0x1c]=value;cursor++;break;
                case 0xf0:sound_ch_set(c,0x10,cursor);c[6]=128;cursor+=4;break;
                case 0xf1:case 0xf2:
                {
                    u16 offset;
                    if(c[1]==0xa0) offset=0x70;
                    else if(c[1]==0xc0) offset=(sound_ram[0x160]&128)?0x160:0xa0;
                    else
                    {
                        if(!(c[0]&64) && !(sound_ram[0x130]&128))
                        { sound_ram[0xa0]=(sound_ram[0xa0]&~68)|16;sound_ram[0x130]=0; }
                        offset=0xd0;
                    }
                    sound_ram[offset]=(sound_ram[offset]&~4)|16;
                    c[0]=0;sound_ram[0x11]=0;PSG_write(c[1]|31);return FALSE;
                }
                case 0xf3:
                    PSG_write(value);
                    if((value&3)==3)
                    { PSG_write(0xdf);c[0]&=~64;sound_ram[0xa0]|=4;sound_ram[0x130]|=4; }
                    else
                    {
                        c[0]|=64;
                        if(sound_ram[0x130]&128) sound_ram[0x130]&=~4;else sound_ram[0xa0]&=~4;
                    }
                    cursor++;break;
                case 0xf4:c[6]=value;cursor++;break;
                case 0xf5:c[7]=value;cursor++;break;
                case 0xf6:cursor=sound_word(cursor);break;
                case 0xf7:
                {
                    u16 index=0x27+value;cursor++;
                    if(index>=0x30) { sound_unhandled_command=note;return FALSE; }
                    if(!c[index]) c[index]=sound_read(cursor);
                    cursor++;
                    if(--c[index]) cursor=sound_word(cursor);else cursor+=2;
                    break;
                }
                case 0xf8:
                    frequency=sound_word(cursor);cursor++;c[9]-=2;
                    if(c[9]<0x2a) { sound_unhandled_command=note;return FALSE; }
                    sound_ch_set(c,c[9],cursor);cursor=frequency;break;
                case 0xf9:cursor=sound_ch_word(c,c[9])+1;c[9]+=2;break;
                case 0xfa:c[2]=value;cursor++;break;
                case 0xfb:c[5]+=value;cursor++;break;
                case 0xfd:c[0]=(c[0]&~8)|(value==1?8:0);cursor++;break;
                default:sound_unhandled_command=note;c[0]=0;PSG_write(c[1]|31);return FALSE;
            }
            continue;
        }
        if(noise)
        {
            if(note>=128) { sound_noise_note(c,note);note=sound_read(cursor++); }
        }
        else if(c[0]&8)
        {
            frequency=(note<<8)|sound_read(cursor++);
            if(frequency) frequency+=(s8)c[5];sound_ch_set(c,11,frequency);note=sound_read(cursor++);
        }
        else if(note>=128)
        {
            if(note==128) sound_release(c);
            else
            {
                c[0x1d]&=127;frequency=sound_word(0x843d+(u8)((note&127)+c[5])*2);sound_ch_set(c,11,frequency);
            }
            note=sound_read(cursor++);
        }
        /* 83EC always sends raw16-bit note durations through839B. */
        if((note&128) && (noise || !(c[0]&8))) { c[10]=c[13];cursor--; }
        else c[10]=c[13]=(u8)(note*c[2]);
        sound_ch_set(c,3,cursor);
        if(!(c[0]&2))
        {
            if(!(c[0]&64)) c[0]&=~32;
            c[14]=c[15];c[0x15]=0;
            if(!(c[7]&128)) c[0x1f]=0;
        }
        return TRUE;
    }
    sound_unhandled_command=0x102;return FALSE;
}
static void sound_channel(u8 *c,bool noise)
{
    u16 frequency,volume,n,table;bool new_note=FALSE;
    if(!--c[10])
    {
        new_note=TRUE;
        if(!sound_sequence(c,noise) || noise || (c[0]&20)) return;
        if(!noise)
        {
            if((c[6]&128) && !(c[0]&2))
            {
                table=sound_ch_word(c,0x10);for(n=0;n<3;n++) c[0x14+n]=sound_read(table+n);
                c[0x17]=sound_read(table+3)>>1;c[0x12]=c[0x13]=0;
            }
            if((c[7]&128) && !(c[0]&2) && !(c[0x1d]&128)) { c[0x1f]=255;c[0x1d]=16|c[0x1e]; }
        }
    }
    else if(!noise)
    {
        if(c[0]&4) return;
        if(c[14] && !--c[14]) sound_release(c);
    }
    if(!noise && (new_note || c[6]) && !(c[0]&96))
    {
        frequency=sound_pitch(c)+(s8)c[0x25];
        PSG_write((c[1]==0xe0?0xc0:c[1])|(frequency&15));
        PSG_write((u8)(((frequency&0xf0)|(frequency>>8))<<4 | ((frequency&0xf0)|(frequency>>8))>>4));
    }
    volume=sound_envelope(c);
    if(c[0]&20) return;
    volume=(u8)(volume+c[8]);if(volume&16) volume=15;
    PSG_write((volume|c[1])+16);
}
static void sound_music(u16 command) { sound_request=command;sound_current_track=command; }
static void sound_tick(void)
{
    u16 n;
    /* Source IRQ reads status before uploading the next prepared SAT. */
    world_sms_sprite_overflow=world_sms_sprite_display_overflow;
    world_sms_sprite_display_overflow=world_sms_sprite_prepared_overflow;
    if(intro_timer) intro_timer--;
    if(sound_request) { sound_ram[6]=sound_request;sound_request=0; }
    if(sound_effect_request) { sound_ram[8]=sound_effect_request;sound_effect_request=0; }
    if(sound_ram[0xa])
    {
        if(sound_ram[0xa]&128) { sound_ram[0xa]--;sound_mute();sound_ram[5]=0x80; }
        return;
    }
    sound_arbitrate();
    if(sound_ram[1] && !--sound_ram[1])
    {
        sound_ram[1]=sound_ram[2];for(n=0;n<4;n++) sound_ram[0x4a+n*0x30]++;
    }
    if(sound_ram[0xb] && !--sound_ram[0xc])
    {
        sound_ram[0xc]=sound_ram[0xd];
        if(!--sound_ram[0xb]) sound_stop();
        else
        {
            for(n=0;n<3;n++) if(sound_ram[0x48+n*0x30]<11) sound_ram[0x48+n*0x30]++;
            if(sound_ram[0x18]<11) sound_ram[0x18]++;
        }
    }
    sound_dispatch();
    if(sound_ram[3]) { sound_ram[4]=(sound_ram[4]+1)%6;if(!sound_ram[4]) return; }
    for(n=0;n<7;n++)
    {
        u8 *c=sound_ram+0x40+n*0x30;
        if(c[0]&128) sound_channel(c,n==3);
    }
}
