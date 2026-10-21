/* Native PSG music reader, bank 6:8000..897D. Original sequence/envelope
 * data are read directly; this is not a Z80 CPU or a recorded audio stream. */
#include "source_audio_prefix.h"
#include "source_audio_memory.h"
#include "source_audio_reader.h"
extern const u8 intro_bank6[],sound_low_rom[];
static u8 sound_ram[0x190];
static volatile u16 sound_unhandled_command;
static u16 sound_current_track;
static u16 sound_source_de; /* Original reader DE, carried between channels. */
static SourceAudioReaderStatus sound_reader_status;
static volatile SourceClockWork sound_source_work; /* Complete8000 T/M1, excludes CALL. */
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
void sound_effect(u16 command) { sound_effect_request=command; }
void sound_effect_main(u16 command) { sound_request=command; }
static void sound_music(u16 command) { sound_request=command;sound_current_track=command; }
static void sound_reader_emit(void *context,const u8 *writes,u16 count)
{
    u16 n;(void)context;for(n=0;n<count;n++) PSG_write(writes[n]);
}
static void sound_tick(void)
{
    u8 accepted;SourceClockWork work;
    /* Source status is latched by world_vint before video and audio. */
    if(intro_timer) intro_timer--;
    if(sound_request) { sound_ram[6]=sound_request;sound_request=0; }
    if(sound_effect_request) { sound_ram[8]=sound_effect_request;sound_effect_request=0; }
    accepted=source_audio_reader_stream(sound_ram,sound_low_rom,0x8000,intro_bank6,
                                        &sound_source_de,&work,&sound_reader_status,
                                        sound_reader_emit,0);
    sound_source_work.tstates=work.tstates;sound_source_work.fetches=work.fetches;
    if(!accepted) {sound_unhandled_command=sound_reader_status.error;return;}
    if(sound_reader_status.track) sound_current_track=sound_reader_status.track;
}
