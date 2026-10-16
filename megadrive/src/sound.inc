/* Native PSG music reader, bank 6:8000..897D. Original sequence/envelope
 * data are read directly; this is not a Z80 CPU or a recorded audio stream. */
#include "source_audio_prefix.h"
#include "source_audio_dispatch.h"
#include "source_audio_priority.h"
#include "source_audio_envelope.h"
#include "source_audio_pitch.h"
#include "source_audio_memory.h"
#include "source_audio_sequence.h"
#include "source_audio_noise.h"
extern const u8 intro_bank6[],sound_low_rom[];
static u8 sound_ram[0x190];
static volatile u16 sound_unhandled_command;
static u16 sound_current_track;
static u16 sound_source_de; /* Original reader DE, carried between channels. */
static SourceAudioSequenceOutput sound_sequence_output;
static volatile u16 sound_request;
static volatile u16 sound_effect_request;
static u8 sound_read(u16 address)
{
    u8 value;
    if(source_audio_read(sound_ram,sound_low_rom,0x8000,intro_bank6,address,&value)) return value;
    sound_unhandled_command=0x400;return 0;
}
static u16 sound_ch_word(u8 *c,u16 offset) { return c[offset]|((u16)c[offset+1]<<8); }
static void sound_ch_set(u8 *c,u16 offset,u16 value) { c[offset]=value;c[offset+1]=value>>8; }
static void sound_mute(void)
{
    u16 n;
    for(n=0;n<10;n++) PSG_write(sound_read(0x8412+n));
}
static void sound_stop(void)
{
    SourceClockWork work;source_audio_stop(sound_ram,&work);sound_mute();
}
/* 8097/80A8: three source queues share a priority latch; later ties win. */
static void sound_arbitrate(void)
{
    SourceClockWork work;source_audio_arbitrate(sound_ram,intro_bank6,&work);
}
static void sound_dispatch(void)
{
    u16 command=sound_ram[5],n;SourceClockWork work;SourceAudioDispatchOutput output;
    if(!source_audio_dispatch(sound_ram,intro_bank6,&work,&output))
    { sound_stop();return; } /* Retain existing fallback for unaudited commands. */
    if(command>=0x81 && command<=0x8d) sound_current_track=command;
    if(output.mute) sound_mute();
    for(n=0;n<output.count;n++) PSG_write(output.writes[n]);
}
static void sound_priority_effect(void)
{
    u16 n;SourceClockWork work;SourceAudioDispatchOutput output;
    if(!source_audio_priority(sound_ram,intro_bank6,&sound_source_de,&work,&output))
    { sound_unhandled_command=0x200|sound_ram[9];return; }
    for(n=0;n<output.count;n++) PSG_write(output.writes[n]);
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
    SourceClockWork work;SourceAudioEnvelopeOutput output;
    if(!source_audio_envelope(sound_ram,(u16)(c-sound_ram),sound_low_rom,0x8000,
                              intro_bank6,&sound_source_de,&work,&output))
    { sound_unhandled_command=0x100;return 15; }
    if(output.write) PSG_write(output.psg);
    return output.accumulator;
}
static u16 sound_pitch(u8 *c)
{
    SourceClockWork work;SourceAudioPitchOutput output;
    if(!source_audio_pitch(sound_ram,(u16)(c-sound_ram),sound_low_rom,0x8000,
                           intro_bank6,0x8507,&sound_source_de,&work,&output))
    {sound_unhandled_command=0x101;return sound_ch_word(c,11);}
    return output.hl;
}
static bool sound_sequence(u8 *c)
{
    SourceClockWork work;u16 n;
    if(!source_audio_sequence(sound_ram,(u16)(c-sound_ram),sound_low_rom,0x8000,
                              intro_bank6,&work,&sound_sequence_output))
    {sound_unhandled_command=0x500|sound_sequence_output.error;return FALSE;}
    sound_source_de=sound_sequence_output.de;
    for(n=0;n<sound_sequence_output.count;n++) PSG_write(sound_sequence_output.writes[n]);
    return !sound_sequence_output.unwind;
}
static void sound_channel(u8 *c)
{
    u16 frequency,volume,n,table;bool new_note=FALSE;
    if(!--c[10])
    {
        new_note=TRUE;
        if(!sound_sequence(c) || (c[0]&20)) return;
        if((c[6]&128) && !(c[0]&2))
        {
            table=sound_ch_word(c,0x10);for(n=0;n<3;n++) c[0x14+n]=sound_read(table+n);
            c[0x17]=sound_read(table+3)>>1;c[0x12]=c[0x13]=0;
            sound_source_de=0xde00+(u16)(c-sound_ram)+0x17;
        }
        if((c[7]&128) && !(c[0]&2) && !(c[0x1d]&128)) { c[0x1f]=255;c[0x1d]=16|c[0x1e]; }
    }
    else
    {
        if(c[0]&4) return;
        if(c[14] && !--c[14]) sound_release(c);
    }
    if((new_note || c[6]) && !(c[0]&96))
    {
        frequency=sound_pitch(c);
        if(c[0]&32) return; /* 8334: table termination unwinds its caller. */
        sound_source_de=(u16)(s16)(s8)c[0x25];
        frequency+=(s8)c[0x25];
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
    u16 n;SourceClockWork prefix_work;bool fade_stopping;
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
    source_audio_tempo(sound_ram,&prefix_work);
    fade_stopping=(sound_ram[0xb]==1 && sound_ram[0xc]==1);
    source_audio_fade(sound_ram,&prefix_work);
    if(fade_stopping) sound_mute();
    sound_dispatch();
    sound_priority_effect(); /* 8018: process DE09 before compensation/channels. */
    if(sound_ram[3]) { sound_ram[4]=(sound_ram[4]+1)%6;if(!sound_ram[4]) return; }
    for(n=0;n<7;n++)
    {
        u8 *c=sound_ram+0x40+n*0x30;
        if(!(c[0]&128)) continue;
        if(n==3)
        {
            SourceClockWork work;u16 write;
            if(!source_audio_noise(sound_ram,0xd0,sound_low_rom,0x8000,intro_bank6,
                                   &sound_source_de,&work,&sound_sequence_output))
            {sound_unhandled_command=0x600|sound_sequence_output.error;return;}
            for(write=0;write<sound_sequence_output.count;write++) PSG_write(sound_sequence_output.writes[write]);
            if(sound_sequence_output.unwind==2) return; /* F1/F2/F3 can exit8000. */
        }
        else sound_channel(c);
    }
}
