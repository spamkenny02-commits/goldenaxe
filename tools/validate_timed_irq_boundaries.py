"""Timed IRQ publication/error parity, absent sinks and modular master epochs."""
import ctypes as c
import hashlib
import json
import os
import subprocess
from actor_reference import ROOT
from validate_native_irq_context_boundaries import WRAPPER, MODULES
from validate_reader_timing import MODULES as TIMED_MODULES


def wrapper(mode):
    code=WRAPPER.replace('u32 writes,traces;', 'u32 writes,traces,dates[1024];u8 values[1024];')
    code=code.replace('u8 context_case(u8 kind,', 'u8 context_'+mode+'(u8 kind,u32 epoch,u8 with_sink,')
    code=code.replace('ram[0x2e]=1;', 'entry.entry_elapsed=epoch;ram[0x2e]=1;',1)
    code=code.replace(' accepted=source_irq_interrupt',
        ' if(kind==11 || kind==12) {audio[10]=128;ram[0x2e]=kind==12;}\n accepted=source_irq_interrupt')
    code=code.replace('ctx.sink=sink;', 'ctx.sink=with_sink?sink:0;')
    code=code.replace(' return 1;', '''
 out[13]=ctx.audio_de;out[14]=out[15]=2166136261UL;
 {u16 n;for(n=0;n<336;n++) out[14]=(out[14]^ram[n])*16777619UL;
 for(n=0;n<400;n++) out[15]=(out[15]^audio[n])*16777619UL;}
 return 1;''')
    if mode=='base':
        return code
    code=code.replace('#include "source_irq_context.h"', '#include "source_irq_timed_context.h"')
    code=code.replace('const u8 *writes,u16 count)', 'const u8 *writes,const u32 *master,u16 count)')
    code=code.replace('(void)writes;p->writes+=count;',
        'u16 n;for(n=0;n<count;n++) {if(p->writes<1024) {p->values[p->writes]=writes[n];p->dates[p->writes]=master[n];}p->writes++;}')
    code=code.replace('SourceIrqContext ctx={0};', 'SourceTimedIrqContext timed={0};')
    code=code.replace('ctx.', 'timed.core.').replace('(&ctx,', '(&timed,')
    code=code.replace('timed.core.sink=', 'timed.sink=').replace('timed.core.sink_context=', 'timed.sink_context=')
    code=code.replace('accepted=source_irq_interrupt',
        'accepted=source_irq_'+('master' if mode=='master' else 'fast_timed' if mode=='fast' else 'timed')+'_interrupt')
    code=code.replace(' return 1;', '''
 out[12]=timed.reader_entry_master;
 {u16 n;for(n=0;n<observer.writes && n<1024;n++) {out[16+n*2]=observer.values[n];out[17+n*2]=observer.dates[n];}}
 return 1;''')
    return code


def main():
    folder=ROOT/'validation/timed-irq-boundaries';folder.mkdir(exist_ok=True)
    for mode in ['base','normal','fast','master']:(folder/(mode+'.c')).write_text(wrapper(mode))
    modules=list(dict.fromkeys(MODULES+TIMED_MODULES+['source_irq_timed_context','source_irq_fast_timed_context','source_audio_fast_timed','source_audio_reader_master','source_irq_master_context']))
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src')]
    args += [str(folder/(mode+'.c')) for mode in ['base','normal','fast','master']]
    args += [str(ROOT/'megadrive/src'/(n+'.c')) for n in modules]+['-o',str(folder/'boundaries.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
    dll=c.CDLL(str(folder/'boundaries.dll'));source=(ROOT/'input/original.sms').read_bytes()
    low=(c.c_uint8*32768).from_buffer_copy(source[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(source[0x18000:0x1c000]);rows=[]
    def call(mode,kind,epoch,sink):
        fn=getattr(dll,'context_'+mode);fn.restype=c.c_uint8
        fn.argtypes=[c.c_uint8,c.c_uint32,c.c_uint8,c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),c.POINTER(c.c_uint32)]
        out=(c.c_uint32*2064)();assert fn(kind,epoch,sink,low,bank,out);assert out[4]<=1024
        return list(out[:16]),list(zip(out[16:16+out[4]*2:2],out[17:17+out[4]*2:2])) if mode!='base' else []
    for kind in range(13):
        for epoch in [0,0xfffffff0]:
            for sink in [0,1]:
                base,_=call('base',kind,epoch,sink);normal,events=call('normal',kind,epoch,sink);fast,fast_events=call('fast',kind,epoch,sink)
                master,master_events=call('master',kind,epoch,sink)
                assert master==fast and master_events==fast_events,(kind,epoch,sink,'fused master mismatch')
                assert normal[:12]==fast[:12]==base[:12],(kind,epoch,sink,base,normal,fast)
                assert normal[13:16]==fast[13:16]==base[13:16],(kind,'DE/state digest mismatch')
                assert events==fast_events and normal[12]==fast[12]
                if not sink:assert not events and not normal[4]
                if events:
                    _,origin=call('normal',kind,0,sink)
                    assert events==[(byte,(time+epoch)&0xffffffff) for byte,time in origin]
                if kind==11 and sink:
                    # Audited audio-only0137->8000 =247T; mute OTIR first116T,
                    # then21T between port writes. Independent fixed source path.
                    assert [t for _,t in events]==[(epoch+(247+116+n*21)*15)&0xffffffff for n in range(10)]
                    assert [b for b,_ in events]==list(source[0x18412:0x1841c])
                rows.append(dict(kind=kind,epoch=epoch,sink=bool(sink),result=normal,events=events))
    report=dict(cases=rows,adapter_calls=len(rows)*4,helpers={n:hashlib.sha256((ROOT/'megadrive/src'/(n+'.c')).read_bytes()).hexdigest() for n in modules},
        limits=['Host diagnostics compare canonical, timed and fast timed adapters: invalid graphics/region, unsupported audio, reset/nested, full/audio-only, absent sinks, timer boundaries and32-bit epoch wrap.',
                'Fixed audio-only mute dates derive from source247T entry prefix and116T first OUT/21T stride. Loading source oracle and compiled68000 reader tests cover general source times separately. No physical scheduling or full-game proof.'])
    (ROOT/'analysis/timed_irq_boundaries_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(len(rows),'timed IRQ cases;',report['adapter_calls'],'adapter calls passed')


if __name__=='__main__':main()
