"""Queued IRQ faults cannot masquerade as successful source-clock work."""
import contextlib
import ctypes as c
import hashlib
import io
import json
import os
import re
import subprocess
from actor_reference import ROOT
from run_core import run
from validate_reader_timing import MODULES as TIMED_MODULES

WRAPPER=r'''
#include "source_irq_queue_context.h"
/*PARTIAL_FIXTURE*/
typedef struct {SourcePsgQueue *queue;u32 origin,popped,limit;u8 cancel;} Pump;
static u8 progress(void *user)
{
 Pump *p=(Pump *)user;SourcePsgEvent event;
 if(p->cancel || (p->limit && p->popped>=p->limit)) return 0;
 if(source_psg_queue_take(p->queue,p->origin,&event)!=0 || event.value!=0xed || event.due!=p->origin-1) return 0;
 p->popped++;return 1;
}
static void trace(void *user,const SourceClockIrq *entry,const SourceClockWork *work)
{u32 *count=(u32 *)user;(void)entry;(void)work;(*count)++;}
u8 fault_case(u8 kind,const u8 *low,const u8 *bank,u32 *out)
{
 SourceQueuedIrqContext ctx={0};SourcePsgQueue queue;static SourcePsgEvent storage[512];
 SourcePsgEvent old;SourceClockWork work={0,0};SourceClockIrq entry={193UL*3420+72UL*15,0xfffffff0UL,7};
 u8 ram[336]={0},audio[400]={0},accepted=0,bind=255;u16 n;u32 traces=0;Pump pump={0};
 source_psg_queue_init(&queue,storage,kind==5?256:512);pump.queue=&queue;pump.origin=entry.entry_elapsed;pump.cancel=kind==1;
 ctx.timed.core.ram=ram;ctx.timed.core.audio=audio;ctx.timed.core.low=low;ctx.timed.core.low_bytes=32768;ctx.timed.core.bank6=bank;
 ctx.timed.core.input.lines=262;ctx.timed.core.input.reset_mask=16;ctx.timed.core.trace=trace;ctx.timed.core.trace_context=&traces;
 ram[0x30]=2;audio[1]=2;audio[5]=128;audio[10]=kind==9?1:128;
 old.due=entry.entry_elapsed-1;old.value=0xed;
 if(kind==5 || kind==7) {ctx.stream.published=123;ctx.timed.sink_context=&pump;}
 if(kind==7 && source_psg_queue_push(&queue,&old,1)!=0) return 0;
 if(kind!=0) bind=source_irq_queue_bind(&ctx,&queue,progress,&pump);
 if(kind!=5 && kind!=7)
 {
  if(kind!=0 && bind!=0) return 0;
  if(kind==10) {for(n=0;n<400;n++) audio[n]=partial_audio[n];ctx.timed.core.audio_de=PARTIAL_DE;pump.limit=PARTIAL_ALLOW;}
  if(kind==1 || kind==4 || kind==10) for(n=0;n<512;n++) if(source_psg_queue_push(&queue,&old,1)!=0) return 0;
  if(kind==2) ctx.stream.error=SOURCE_PSG_QUEUE_ORDER;
  if(kind==3) {old.due=entry.entry_elapsed+1000000UL;if(source_psg_queue_push(&queue,&old,1)!=0) return 0;}
  if(kind==6) {audio[10]=0;audio[5]=0x8e;}
  accepted=source_irq_queue_interrupt(&ctx,&entry,&work);
 }
 out[0]=accepted;out[1]=ctx.timed.core.error;out[2]=work.tstates;out[3]=work.fetches;
 out[4]=ram[0x30];out[5]=audio[10];out[6]=ctx.timed.core.last_audio.count;out[7]=ctx.stream.published;
 out[8]=ctx.stream.error;out[9]=queue.read;out[10]=queue.write;out[11]=pump.popped;
 out[12]=traces;out[13]=ctx.stream.waits;out[14]=bind;out[15]=!ctx.timed.sink && ctx.timed.sink_context==&pump;
 return 1;
}
'''


def main():
    folder=ROOT/'validation/queued-irq-faults';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    archive=ROOT/'analysis/loading-psg-v0203';fixture_name='validation/loading-psg-deadlines/inputs.json';fixture_raw=(archive/fixture_name).read_bytes()
    assert hashlib.sha256(fixture_raw).hexdigest()==json.loads((archive/'manifest.json').read_text())['files'][fixture_name]
    partial=next(row for row in json.loads(fixture_raw) if len(row['batches'])>1)
    fixture='static const u8 partial_audio[]={'+','.join(map(str,partial['before']))+'};\n#define PARTIAL_DE '+str(partial['de'])+'\n#define PARTIAL_ALLOW '+str(partial['batches'][0])+'\n'
    (src/'wrapper.c').write_text(WRAPPER.replace('/*PARTIAL_FIXTURE*/',fixture))
    modules=list(dict.fromkeys(['source_irq_queue_context','source_irq','source_clock','source_rng','source_audio_fast_timed','source_psg_queue','source_psg_stream',*TIMED_MODULES]))
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(src/'wrapper.c')]+[str(ROOT/'megadrive/src'/(n+'.c')) for n in modules]+['-o',str(folder/'faults.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'host-build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
    rom=(ROOT/'input/original.sms').read_bytes();low=(c.c_uint8*32768).from_buffer_copy(rom[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(rom[0x18000:0x1c000]);dll=c.CDLL(str(folder/'faults.dll'));fn=dll.fault_case;fn.argtypes=[c.c_uint8,c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),c.POINTER(c.c_uint32)];fn.restype=c.c_uint8;rows=[]
    for kind in range(11):
        output=(c.c_uint32*16)();assert fn(kind,low,bank,output);r=list(output)
        if kind in [0,1,2,3,6]:
            assert r[:5]==[0,0x18e if kind==6 else 0x900,0,0,2] and not r[6] and not r[7] and not r[12]
            assert r[5]==({0:128,1:127,2:128,3:127,6:0}[kind])
            assert r[8]=={0:1,1:0x100,2:3,3:3,6:0}[kind]
        elif kind in [5,7]:
            assert r[:5]==[0,0,0,0,2] and r[7]==123 and r[14]==1 and r[15]==1
        elif kind==10:
            first=partial['batches'][0]
            assert r[:5]==[0,0x900,0,0,2] and r[6:9]==[first,first,0x100]
            assert r[9:14]==[first,512+first,first,0,first+1]
        else:
            assert r[:7]==[1,0,575 if kind==9 else 901,61 if kind==9 else 94,1,1 if kind==9 else 127,0 if kind==9 else 10]
            assert r[7]==(0 if kind==9 else 10) and not r[8] and r[12]==1
        if kind==1:assert r[9:14]==[0,512,0,0,1]
        if kind==4:assert r[9:14]==[10,522,10,1,10]
        rows.append(r)
    print('11 queued IRQ setup/fault/commit cases passed on host',flush=True)
    header=['static const u8 low[]={'+','.join(map(str,low))+'};','static const u8 bank6[]={'+','.join(map(str,bank))+'};',
        'static const u32 expected[11][16]={'+','.join('{'+','.join(str(n)+'UL' for n in row)+'}' for row in rows)+'};']
    (src/'expected.h').write_text('\n'.join(header)+'\n')
    for n in modules:(src/(n+'.c')).write_text('#include "../../../megadrive/src/'+n+'.c"\n')
    (src/'source_irq_queue_context.h').write_text('#include "../../../megadrive/src/source_irq_queue_context.h"\n')
    (src/'main.c').write_text('''#include <genesis.h>
#include "expected.h"
u8 fault_case(u8,const u8*,const u8*,u32*);
volatile u32 gaw_fault_cases,gaw_fault_failures;volatile u16 gaw_fault_done;
int main(bool hard_reset) {u16 kind,n;u32 output[16];VDP_setEnable(FALSE);
for(kind=0;kind<11;kind++) {if(!fault_case(kind,low,bank6,output)) gaw_fault_failures++;for(n=0;n<16;n++) if(output[n]!=expected[kind][n]) gaw_fault_failures++;gaw_fault_cases++;}
gaw_fault_done=1;while(TRUE) SYS_doVBlankProcess();return 0;}
''')
    env['PATH']=str(sdk/'bin')+';'+env['PATH'];temporary=folder/'compiler-tmp';temporary.mkdir(exist_ok=True)
    for key in ['TMPDIR','TMP','TEMP']:env[key]=temporary.resolve().as_posix()
    path=sdk.as_posix();unix='/'+path[0].lower()+path[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True)
    (folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2000:]
    symbols={m[2]:int(m[1],16)&65535 for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};cartridge=folder/'out/release/rom.bin';results=[]
    for region in ['auto','pal']:
        observed={}
        def observe(frame,ram):
            def v(name,width):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(width)),'big')
            observed.update(frame=frame,done=v('gaw_fault_done',2),cases=v('gaw_fault_cases',4),failures=v('gaw_fault_failures',4))
        with contextlib.redirect_stdout(io.StringIO()):run(cartridge,10000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        assert observed.get('done') and observed['cases']==11 and not observed['failures'],observed
        results.append(dict(region=region,**observed));print(results[-1],flush=True)
    report=dict(cases=rows,results=results,kernel_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),partial_fixture_sha256=hashlib.sha256(fixture_raw).hexdigest(),helpers={n:hashlib.sha256((ROOT/'megadrive/src'/(n+'.c')).read_bytes()).hexdigest() for n in modules},
        limits=['Unbound/small/nonempty setup,sticky/order/cancel faults,valid FULL retry,silent and muted success,original unsupported-reader error and cancellation after a source-derived successful prefix. Queue faults return zero work without IRQ RAM/trace commit and report actual published bytes. Audio mutations before a fatal fault are not rolled back; session reset is required.',
                'Host semantic assertions repeated in compiled68000 PAL/NTSC. Synthetic known gate path and supplied logical pump clock only; no source replay of invalid inputs or physical PSG timing claim.'])
    (ROOT/'analysis/queued_irq_faults_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
