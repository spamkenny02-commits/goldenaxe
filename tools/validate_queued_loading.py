"""Real source-checked loader -> timed reader -> bounded FIFO, host and68000."""
import contextlib
import ctypes as c
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
from actor_reference import ROOT
from run_core import run
from validate_native_room_finish import WRAPPER, MODULES
from validate_reader_timing import MODULES as TIMED_MODULES

EXTRA=r'''
typedef struct {SourcePsgQueue *queue;u32 origin,remaining,drained;} QueuePump;
static u8 progress(void *user)
{
 QueuePump *p=(QueuePump *)user;SourcePsgEvent event;
 if(!p->remaining || source_psg_queue_take(p->queue,p->origin,&event)!=SOURCE_PSG_QUEUE_OK || event.value!=0xed || event.due!=p->origin-1) return 0;
 p->remaining--;p->drained++;return 1;
}
'''


def wrapper():
    text=WRAPPER
    if 'source_pattern_plan_generated.h' not in text:text=text.replace('#include "source_room_finish.h"','#include "source_room_finish.h"\n#include "source_pattern_plan_generated.h"')
    text=text.replace('source_graphics_load_class0(&clock,&ctx,patterns,bank2,bank11,&data,point,&log)','source_graphics_load_class0_planned(&clock,&ctx,patterns,bank2,bank11,&data,point,&log,&gaw_class0_pattern_plan)')
    text=text.replace('#include "source_room_finish.h"','#include "source_room_finish.h"\n#include "source_irq_queue_context.h"\n'+EXTRA)
    text=text.replace('u8 room_finish_case(', 'u8 queued_loading_case(').replace('const u32 *phase,u8 refresh,','const u32 *phase,u8 refresh,u8 mode,')
    text=text.replace('u32 *out,u32 *events,u32 *points,u8 *states)','u32 *out,u32 *events,u32 *points,u8 *states,u32 *due,u8 *values,u32 *stats)')
    text=text.replace('SourceIrqContext ctx={0};','SourceQueuedIrqContext queued={0};SourcePsgQueue fifo;QueuePump pump={0};SourcePsgEvent event;u32 epoch=(mode&2)?0xffff0000UL:0;static SourcePsgEvent fifo_storage[512];')
    text=text.replace('ctx.','queued.timed.core.').replace('&ctx','&queued.timed.core')
    needle=' queued.timed.core.ram=ram;'
    assert needle in text
    text=text.replace(needle,''' clock.elapsed=epoch;
 if(source_psg_queue_init(&fifo,fifo_storage,512)!=0) return 0;
 if(mode&2) fifo.read=fifo.write=65530;
 pump.queue=&fifo;pump.origin=epoch;pump.remaining=(mode&1)?512:0;
 if(source_irq_queue_bind(&queued,&fifo,progress,&pump)!=0) return 0;
 if(mode&1) {SourcePsgEvent old[512];for(n=0;n<512;n++) {old[n].due=epoch-1;old[n].value=0xed;}
 if(source_psg_queue_push(&fifo,old,512)!=0) return 0;}
 queued.timed.core.ram=ram;''',1)
    text=text.replace(' return 1;\n}\n', ' return 1;\n}\n')
    end=' out[37]=hash(pixels+0x3800,1536);out[38]=hash(cells+0xb0,16);out[39]=finish.wait_taken;out[40]=finish.error;'
    assert end in text
    text=text.replace(end,end+'''
 while(pump.remaining) if(!progress(&pump)) return 0;
 n=0;
 while(source_psg_queue_take(&fifo,clock.elapsed,&event)==0)
 {if(n>=128) return 0;due[n]=event.due;values[n++]=event.value;}
 if(fifo.read!=fifo.write || queued.stream.error || n!=queued.stream.published) return 0;
 stats[0]=n;stats[1]=queued.stream.waits;stats[2]=queued.stream.error;stats[3]=fifo.write;stats[4]=fifo.read;stats[5]=pump.drained;
 out[2]-=epoch;
 {u16 k;for(k=0;k<log.count;k++) events[k*6]-=epoch;
 for(k=0;k<16;k++) points[k*18+2]-=epoch;}
''')
    return text


def main():
    folder=ROOT/'validation/queued-loading';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    cases=json.loads((ROOT/'validation/native-planned-room-finish/cases.json').read_text())
    oracle=json.loads((ROOT/'analysis/loading_psg_deadlines_report.json').read_text())['results'][0]['rows']
    archive=ROOT/'analysis/loading-psg-v0203';manifest=json.loads((archive/'manifest.json').read_text());name='validation/loading-psg-deadlines/inputs.json';raw=(archive/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==manifest['files'][name];inputs=json.loads(raw)
    expected=[]
    for n in range(len(cases)):
        times=[t for row in oracle if row['case']==n for t in row['source_psg_master']]
        values=[v for row in inputs if row['case']==n for v in row['writes']]
        assert len(times)==len(values)<=128;expected.append((times,values))
    modules=list(dict.fromkeys([n for n in MODULES if n!='source_irq_context']+TIMED_MODULES+['source_audio_fast_timed','source_irq_queue_context','source_psg_queue','source_psg_stream']))
    body=wrapper();(src/'wrapper.c').write_text(body)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    for name in modules:
        prefix='#define source_irq_interrupt source_irq_queue_interrupt\n' if name!='source_irq_queue_context' else ''
        (src/(name+'.c')).write_text(prefix+'#include "../../../megadrive/src/'+name+'.c"\n')
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(src/'wrapper.c')]+[str(src/(n+'.c')) for n in modules]+['-o',str(folder/'queued.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'host-build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
    dll=c.CDLL(str(folder/'queued.dll'));fn=dll.queued_loading_case;p8=c.POINTER(c.c_uint8);p32=c.POINTER(c.c_uint32)
    fn.argtypes=[p32,c.c_uint8,c.c_uint8,p8,p8,p8,p8,c.c_uint16,p8,p8,p8,p8,p8,p8,p32,p32,p32,p8,p32,p8,p32];fn.restype=c.c_uint8
    rom=(ROOT/'input/original.sms').read_bytes();banks={n:(c.c_uint8*16384).from_buffer_copy(rom[n*16384:(n+1)*16384]) for n in [2,4,6,8,9,11]};low=(c.c_uint8*32768).from_buffer_copy(rom[:32768]);patterns=(c.c_uint8*(len(rom)-0x3c010)).from_buffer_copy(rom[0x3c010:]);host_rows=[]
    for index,row in enumerate(cases):
        for mode in range(4):
            epoch=0xffff0000 if mode&2 else 0;ram=(c.c_uint8*336)(*row['ram']);audio=(c.c_uint8*400)(*row['audio']);out=(c.c_uint32*41)();events=(c.c_uint32*384)();points=(c.c_uint32*288)();states=(c.c_uint8*11776)();due=(c.c_uint32*128)();values=(c.c_uint8*128)();stats=(c.c_uint32*6)()
            assert fn((c.c_uint32*12)(*row['phase']),row['refresh'],mode,ram,audio,low,banks[6],row['room'],banks[9 if row['room']&128 else 8],patterns,banks[2],banks[11],banks[4],(c.c_uint8*16)(*row['hud']),out,events,points,states,due,values,stats),(index,mode,'rejected')
            assert list(out)==row['expected'] and list(points)==row['points'] and list(states)==row['states']
            assert list(events[:len(row['events'])])==row['events']
            n=len(expected[index][0]);assert list(due[:n])==[(t+epoch)&0xffffffff for t in expected[index][0]] and list(values[:n])==expected[index][1]
            assert stats[0]==n and not stats[2] and stats[3]==stats[4] and stats[1]==(n if mode&1 else 0) and stats[5]==(512 if mode&1 else 0)
            host_rows.append(dict(case=index,mode=mode,bytes=n,waits=stats[1]))
    print(len(host_rows),'host queued loader cases; source checkpoints and PSG dates/bytes exact',flush=True)
    # Restore the independently source-checked vector header, without rerunning
    # the source capture or substituting queue-generated expected states.
    frozen=ROOT/'analysis/native-copy-pointers-v0203';record=json.loads((frozen/'manifest.json').read_text())['compressed']['validation/native-planned-room-finish/kernel/src/expected.h'];raw=gzip.decompress((frozen/record['stored']).read_bytes());assert hashlib.sha256(raw).hexdigest()==record['raw_sha256'];(src/'expected.h').write_bytes(raw)
    lines=['static const u16 psg_counts[]={'+','.join(str(len(t)) for t,_ in expected)+'};',
        'static const u32 psg_due[24][128]={'+','.join('{'+','.join(str(t)+'UL' for t in times)+'}' for times,_ in expected)+'};',
        'static const u8 psg_values[24][128]={'+','.join('{'+','.join(map(str,values))+'}' for _,values in expected)+'};']
    (src/'psg.h').write_text('\n'.join(lines)+'\n')
    (src/'main.c').write_text('''#include <genesis.h>
#include "expected.h"
#include "psg.h"
u8 queued_loading_case(const u32*,u8,u8,u8*,u8*,const u8*,const u8*,u16,const u8*,const u8*,const u8*,const u8*,const u8*,const u8*,u32*,u32*,u32*,u8*,u32*,u8*,u32*);
volatile u32 gaw_queued_cases,gaw_queued_failures,gaw_queued_bytes;volatile u16 gaw_queued_done;
static u8 ram[336],audio[400],states[11776],values[128];static u32 output[41],events[384],points[288],due[128],stats[6];
int main(bool hard_reset)
{
 u16 row,mode,n;u32 epoch;VDP_setEnable(FALSE);
 for(row=0;row<24;row++) for(mode=0;mode<4;mode++)
 {
  epoch=(mode&2)?0xffff0000UL:0;
  for(n=0;n<336;n++) ram[n]=cases[row].ram[n];
  for(n=0;n<400;n++) audio[n]=cases[row].audio[n];
  if(!queued_loading_case(cases[row].phase,cases[row].refresh,mode,ram,audio,low,bank6,cases[row].room,(cases[row].room&128)?bank9:bank8,patterns,bank2,bank11,bank4,cases[row].hud,output,events,points,states,due,values,stats)) {gaw_queued_failures++;continue;}
  for(n=0;n<41;n++) if(output[n]!=cases[row].expected[n]) gaw_queued_failures++;
  for(n=0;n<288;n++) if(points[n]!=cases[row].points[n]) gaw_queued_failures++;
  for(n=0;n<11776;n++) if(states[n]!=cases[row].states[n]) gaw_queued_failures++;
  for(n=0;n<output[7]*6;n++) if(events[n]!=cases[row].events[n]) gaw_queued_failures++;
  if(stats[0]!=psg_counts[row] || stats[1]!=((mode&1)?psg_counts[row]:0) || stats[2] || stats[3]!=stats[4] || stats[5]!=((mode&1)?512:0)) gaw_queued_failures++;
  for(n=0;n<psg_counts[row];n++) if(due[n]!=(u32)(psg_due[row][n]+epoch) || values[n]!=psg_values[row][n]) gaw_queued_failures++;
  gaw_queued_bytes+=psg_counts[row];gaw_queued_cases++;
 }
 gaw_queued_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
    # Make includes for the generated wrapper resolvable without changing its
    # canonical host text or using target-specific C type layouts on host.
    for name in ['source_room_finish.h','source_irq_queue_context.h','source_pattern_plan_generated.h']:(src/name).write_text('#include "../../../megadrive/src/'+name+'"\n')
    env['PATH']=str(sdk/'bin')+';'+env['PATH'];temporary=folder/'compiler-tmp';temporary.mkdir(exist_ok=True)
    for key in ['TMPDIR','TMP','TEMP']:env[key]=temporary.resolve().as_posix()
    path=sdk.as_posix();unix='/'+path[0].lower()+path[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True)
    (folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2500:]
    symbols={m[2]:int(m[1],16)&65535 for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};cartridge=folder/'out/release/rom.bin';results=[]
    for region in ['auto','pal']:
        observed={}
        def observe(frame,ram):
            def value(name,width):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(width)),'big')
            observed.update(frame=frame,done=value('gaw_queued_done',2),cases=value('gaw_queued_cases',4),failures=value('gaw_queued_failures',4),bytes=value('gaw_queued_bytes',4))
        with contextlib.redirect_stdout(io.StringIO()):run(cartridge,60000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        assert observed.get('done') and observed['cases']==96 and not observed['failures'] and observed['bytes']==sum(len(t) for t,_ in expected)*4,observed
        results.append(dict(region=region,**observed));print(results[-1],flush=True)
    report=dict(host_cases=host_rows,results=results,kernel_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),helpers={n:hashlib.sha256((ROOT/'megadrive/src'/(n+'.c')).read_bytes()).hexdigest() for n in modules},
        limits=['24 source-checked loading inputs times four queue modes: empty/full,normal/wrapped epoch and cursor. Every original16-point state/phase/R/M1/IRQ trace remains checked,with source-observed byte/deadline lists.',
                'Full modes prefill512 older sentinel events and pump them one at a time; this forces whole-packet retry without discarding source events. Pump uses a supplied logical clock. No physical PSG pacing,real port latency or current production CPU-budget proof.'])
    (ROOT/'analysis/queued_loading_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
