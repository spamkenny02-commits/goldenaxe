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
#include "source_audio_tone.h"
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
static void sound_channel(u8 *c)
{
    SourceClockWork work;u16 n;
    if(!source_audio_tone(sound_ram,(u16)(c-sound_ram),sound_low_rom,0x8000,
                          intro_bank6,&sound_source_de,&work,&sound_sequence_output))
    {sound_unhandled_command=0x700|sound_sequence_output.error;return;}
    for(n=0;n<sound_sequence_output.count;n++) PSG_write(sound_sequence_output.writes[n]);
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
