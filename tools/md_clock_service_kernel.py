"""Generate optional native service wrappers without touching source semantics."""
WRAPPERS={
'execute':'''u8 source_clock_execute(SourceClock *c,u16 t,u8 f,u8 e,SourceClockInterrupt irq,void *ctx) {
 u8 ok;cooperative_service();ok=source_clock_execute_unserviced(c,t,f,e,irq,ctx);cooperative_service();return ok;
}
''',
'checkpoint':'''u8 source_clock_checkpoint(SourceClock *c,SourceClockInterrupt irq,void *ctx) {
 u8 ok;cooperative_service();ok=source_clock_checkpoint_unserviced(c,irq,ctx);cooperative_service();return ok;
}
''',
'repeat':'''u16 source_clock_repeat(SourceClock *c,u16 t,u8 f,u16 n) {
 u16 used;cooperative_service();used=source_clock_repeat_unserviced(c,t,f,n);cooperative_service();return used;
}
''',
'repeat_disabled':'''u16 source_clock_repeat_disabled(SourceClock *c,u16 t,u8 f,u16 n) {
 u16 used;cooperative_service();used=source_clock_repeat_disabled_unserviced(c,t,f,n);cooperative_service();return used;
}
'''}


def source(video=False,kind='all',clocked=False):
    assert kind in ('all','repeat-disabled','repeat-batches')
    functions=['execute','repeat','repeat_disabled','checkpoint'] if kind=='all' else (['repeat','repeat_disabled'] if kind=='repeat-batches' else ['repeat_disabled'])
    text=''.join('#define source_clock_'+n+' source_clock_'+n+'_unserviced\n' for n in functions)
    text+='#include "../../../megadrive/src/source_clock.c"\n'
    text+=''.join('#undef source_clock_'+n+'\n' for n in functions)
    text+='void cooperative_service(void);\n'
    text+=''.join(WRAPPERS[n] for n in ['execute','checkpoint','repeat','repeat_disabled'] if n in functions)
    if clocked:
        assert video
        text=text.replace('void cooperative_service(void);','void cooperative_service(const SourceClock *clock);').replace('cooperative_service();','cooperative_service(c);')
    return text.replace('cooperative_service','cooperative_video_service') if video else text
