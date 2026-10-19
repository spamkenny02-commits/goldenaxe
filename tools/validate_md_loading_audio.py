"""Measure live native loader -> source IRQ/FIFO -> physical PSG, per IRQ."""
import contextlib
import ctypes as c
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from actor_reference import ROOT
from run_core import run
from validate_queued_loading import wrapper
from validate_native_room_finish import MODULES
from validate_reader_timing import MODULES as TIMED_MODULES

MAIN=r'''
#include <genesis.h>
#include "expected.h"
#include "psg.h"
#include "driver.h"
#include "md_service_clock.h"
#include "source_md_psg_plan.h"
#include "source_irq_queue_context.h"
u8 queued_loading_case(const u32*,u8,u8,u8*,u8*,const u8*,const u8*,u16,const u8*,const u8*,const u8*,const u8*,const u8*,const u8*,u32*,u32*,u32*,u8*,u32*,u8*,u32*);
volatile u16 gaw_live_done;
volatile u32 gaw_live_cases,gaw_live_failures,gaw_live_bytes,gaw_live_callbacks;
volatile u32 gaw_live_times[48][2];
static MdServiceStamp stamp;static MdServiceClock service;static SourceMdPsgReplayClock physical;
static SourcePsgEvent stream[128],captured[128];static SourceMdPsgBlock blocks[128];
static u16 captured_count,physical_lines;static u32 epoch;
static u8 ram[336],audio[400],states[11776],values[128];
static u32 output[41],events[384],points[288],due[128],stats[6];
static u8 fresh(void) {
 u32 spins=0;u8 status;
 do {status=md_service_clock_now(&service,&physical);} while(status==MD_SERVICE_WAIT && ++spins<100000UL);
 if(status!=MD_SERVICE_OK) {gaw_live_failures++;return 0;}return 1;
}
void cooperative_audio(SourceQueuedIrqContext *queued) {
 SourcePsgQueue *q=queued->stream.queue;u16 n=0,count;u32 cutoff;
 gaw_live_callbacks++;
 if(q->read==q->write) return;
 cutoff=q->events[(q->write-1)&q->mask].due;
 while(n<128 && source_psg_queue_take(q,cutoff,stream+n)==0) n++;
 if(q->read!=q->write || captured_count+n>128) {gaw_live_failures++;return;}
 for(count=0;count<n;count++) captured[captured_count++]=stream[count];
 if(source_md_psg_plan(stream,n,blocks,128,&count) || source_md_psg_plan_beam(blocks,count,physical_lines,100,epoch)) {gaw_live_failures++;return;}
 if(fresh() && source_md_psg_replay_planned(&physical,blocks,count)) gaw_live_failures++;
}
u16 cooperative_collect(u32 *dates,u8 *bytes) {
 u16 n;for(n=0;n<captured_count;n++) {dates[n]=captured[n].due;bytes[n]=captured[n].value;}return captured_count;
}
void cooperative_begin(void) {
 Z80_requestBus(TRUE);
 *(volatile u16*)0xc00010=0x80+gaw_live_cases;
 if(md_service_clock_start(&stamp,physical_lines,driver,sizeof(driver)) || md_service_clock_init(&service,&stamp,physical_lines,epoch)) gaw_live_failures++;
 SYS_disableInts();fresh();
}
void cooperative_finish(void) {
 if(fresh()) gaw_live_times[gaw_live_cases][0]=physical.master-epoch;
}
int main(bool hard_reset) {
 u16 row,mode,n;
 (void)hard_reset;physical_lines=SYS_isPAL()?313:262;
 SYS_disableInts();VDP_setScreenWidth256();VDP_setScreenHeight224();VDP_setEnable(FALSE);
 for(row=0;row<24;row++) for(mode=0;mode<2;mode++) {
  epoch=mode?0xffff0000UL:0;captured_count=0;
  for(n=0;n<336;n++) ram[n]=cases[row].ram[n];
  for(n=0;n<400;n++) audio[n]=cases[row].audio[n];
  if(!queued_loading_case(cases[row].phase,cases[row].refresh,mode?2:0,ram,audio,low,bank6,cases[row].room,(cases[row].room&128)?bank9:bank8,patterns,bank2,bank11,bank4,cases[row].hud,output,events,points,states,due,values,stats)) gaw_live_failures++;
  gaw_live_times[row*2+mode][1]=output[2];
  for(n=0;n<41;n++) if(output[n]!=cases[row].expected[n]) gaw_live_failures++;
  for(n=0;n<288;n++) if(points[n]!=cases[row].points[n]) gaw_live_failures++;
  for(n=0;n<11776;n++) if(states[n]!=cases[row].states[n]) gaw_live_failures++;
  for(n=0;n<output[7]*6;n++) if(events[n]!=cases[row].events[n]) gaw_live_failures++;
  if(stats[0]!=psg_counts[row] || stats[1] || stats[2] || stats[3]!=stats[4] || stats[5]) gaw_live_failures++;
  for(n=0;n<psg_counts[row];n++) if(due[n]!=(u32)(psg_due[row][n]+epoch) || values[n]!=psg_values[row][n]) gaw_live_failures++;
  gaw_live_cases++;gaw_live_bytes+=psg_counts[row];
 }
 gaw_live_done=1;while(TRUE) {}return 0;
}
'''


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    bare='--bare' in sys.argv
    folder=ROOT/('validation/md-loading-audio-bare' if bare else 'validation/md-loading-audio-prepared');src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    archive=ROOT/'analysis/native-copy-pointers-v0203';manifest=json.loads((archive/'manifest.json').read_text())
    item=manifest['compressed']['validation/native-planned-room-finish/kernel/src/expected.h'];stored=(archive/item['stored']).read_bytes();assert sha(stored)==item['stored_sha256']
    raw=gzip.decompress(stored);assert sha(raw)==item['raw_sha256'];(src/'expected.h').write_bytes(raw)
    oracle=ROOT/'analysis/loading-psg-v0203';original=json.loads((oracle/'manifest.json').read_text());name='validation/loading-psg-deadlines/inputs.json'
    raw=(oracle/name).read_bytes();assert sha(raw)==original['files'][name];inputs=json.loads(raw)
    dates_raw=(ROOT/'analysis/loading_psg_deadlines_report.json').read_bytes();dates=json.loads(dates_raw)['results'][0]['rows']
    expected=[]
    for case in range(24):
        times=[t for row in dates if row['case']==case for t in row['source_psg_master']]
        values=[v for row in inputs if row['case']==case for v in row['writes']]
        assert len(times)==len(values)<=128;expected.append((times,values))
    (src/'psg.h').write_text('static const u16 psg_counts[]={'+','.join(str(len(t)) for t,_ in expected)+'};\n'+
        'static const u32 psg_due[24][128]={'+','.join('{'+','.join(str(t)+'UL' for t in times)+'}' for times,_ in expected)+'};\n'+
        'static const u8 psg_values[24][128]={'+','.join('{'+','.join(map(str,values))+'}' for _,values in expected)+'};\n')
    body=wrapper().replace('static void snapshot(', 'void cooperative_begin(void);void cooperative_finish(void);\nvoid cooperative_audio(SourceQueuedIrqContext *queued);\nu16 cooperative_collect(u32 *dates,u8 *bytes);\nstatic void snapshot(',1)
    needle=' row[5]=p->irq->last_irq.stages[SOURCE_IRQ_SAT64].tstates!=0;'
    assert body.count(needle)==1;body=body.replace(needle,needle+'\n cooperative_audio((SourceQueuedIrqContext *)p->irq);')
    needle=' n=0;\n while(source_psg_queue_take(&fifo,clock.elapsed,&event)==0)\n {if(n>=128) return 0;due[n]=event.due;values[n++]=event.value;}'
    assert body.count(needle)==1;body=body.replace(needle,' n=cooperative_collect(due,values);')
    body=body.replace('QueuePump pump={0};SourcePsgEvent event;','QueuePump pump={0};')
    needle=' if(!source_graphics_load_class0_planned('
    assert body.count(needle)==1;body=body.replace(needle,' cooperative_begin();\n'+needle)
    needle=' snapshot(&clock,&queued.timed.core,out);'
    assert body.count(needle)==1;body=body.replace(needle,' cooperative_finish();\n'+needle)
    main_source=MAIN
    if bare:
        first=body.index(' snapshot(clock,ctx,p->snapshots+p->points*18);')
        last=body.index(' p->points++;return 1;',first)
        body=body[:first]+body[last:]
        main_source=main_source.replace('  for(n=0;n<288;n++) if(points[n]!=cases[row].points[n]) gaw_live_failures++;','')
        main_source=main_source.replace('  for(n=0;n<11776;n++) if(states[n]!=cases[row].states[n]) gaw_live_failures++;',
            '  for(n=0;n<336;n++) if(ram[n]!=cases[row].states[15*736+n]) gaw_live_failures++;\n  for(n=0;n<400;n++) if(audio[n]!=cases[row].states[15*736+336+n]) gaw_live_failures++;')
    (folder/'validator.py.snapshot').write_bytes((ROOT/'tools/validate_md_loading_audio.py').read_bytes())
    (src/'wrapper.c').write_text(body);(src/'main.c').write_text(main_source)
    modules=list(dict.fromkeys([n for n in MODULES if n!='source_irq_context']+TIMED_MODULES+['source_audio_fast_timed','source_irq_queue_context','source_psg_queue','source_psg_stream','source_md_psg_plan','md_service_clock','md_service_clock_start']))
    for module in modules:
        prefix='#define source_irq_interrupt source_irq_queue_interrupt\n' if module!='source_irq_queue_context' else ''
        (src/(module+'.c')).write_text(prefix+'#include "../../../megadrive/src/'+module+'.c"\n')
    for name in ['source_room_finish.h','source_irq_queue_context.h','source_pattern_plan_generated.h','source_md_psg_replay.h','source_md_psg_plan.h','md_service_clock.h']:
        (src/name).write_text('#include "../../../megadrive/src/'+name+'"\n')
    for name in ['source_md_psg_replay.s','md_service_clock_hv.s']:(src/name).write_bytes((ROOT/'megadrive/src'/name).read_bytes())
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH']
    driver_source=(ROOT/'megadrive/z80/md_service_clock_z80.asm').read_bytes();(folder/'driver-source.asm.snapshot').write_bytes(driver_source)
    built=subprocess.run([str(sdk/'bin/sjasm.exe'),str(ROOT/'megadrive/z80/md_service_clock_z80.asm'),str(folder/'driver.bin'),str(folder/'driver.lst')],env=env,capture_output=True,text=True)
    (folder/'z80-build.log').write_text(built.stdout+built.stderr);assert not built.returncode and 'Errors: 0' in built.stdout,built.stdout+built.stderr
    driver=(folder/'driver.bin').read_bytes();(src/'driver.h').write_text('static const u8 driver[]={'+','.join(map(str,driver))+'};\n')
    temporary=folder/'compiler-tmp';temporary.mkdir(exist_ok=True)
    for key in ['TMPDIR','TMP','TEMP']:env[key]=temporary.resolve().as_posix()
    path=sdk.as_posix();unix='/'+path[0].lower()+path[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True)
    (folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stdout[-2000:]+built.stderr[-2500:]
    symbols={m[2]:int(m[1],16) for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_service_io_libretro.dll';dll=c.CDLL(str(core))
    dll.gaw_io_reset.argtypes=[c.c_uint];dll.gaw_io_reset.restype=None;dll.gaw_io_size.restype=dll.gaw_io_errors.restype=c.c_uint;dll.gaw_io_data.restype=c.POINTER(c.c_uint)
    results=[]
    for region,lines in [('ntsc',262),('pal',313)]:
        period=lines*3420;events=[];observed={};records=[];dll.gaw_io_reset(0)
        def observe(frame,ram):
            count=dll.gaw_io_size();assert not dll.gaw_io_errors();ptr=dll.gaw_io_data()
            events.extend([[int(ptr[n*4]),(frame-1)*period+int(ptr[n*4+1]),int(ptr[n*4+2]),int(ptr[n*4+3])] for n in range(count)]);dll.gaw_io_reset(1)
            def value(name,width,offset=0):return int.from_bytes(bytes(ram[(((symbols[name]&65535)+offset+i)&65535)^1] for i in range(width)),'big')
            observed.update(frame=frame,done=value('gaw_live_done',2),cases=value('gaw_live_cases',4),failures=value('gaw_live_failures',4),bytes=value('gaw_live_bytes',4),callbacks=value('gaw_live_callbacks',4))
            if observed['done']:
                records[:]=[[value('gaw_live_times',4,n*8+i*4) for i in range(2)] for n in range(48)];observed['ram_sha256']=sha(bytes(ram))
        with contextlib.redirect_stdout(io.StringIO()):
            run(folder/'out/release/rom.bin',20000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core=core,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        raw=json.dumps(dict(events=events,records=records,observed=observed),separators=(',',':')).encode();(folder/(region+'-events.json')).write_bytes(raw)
        assert observed.get('done') and observed['cases']==48 and observed['bytes']==2976 and not observed['failures'],observed
        markers=[i for i,e in enumerate(events) if e[0]==3 and 128<=e[2]<176];assert len(markers)==48
        rows=[]
        for n,index in enumerate(markers):
            subset=events[index+1:markers[n+1] if n+1<48 else len(events)];zreads=[]
            for k,e in enumerate(subset):
                if e[0]!=1:continue
                native=k+1<len(subset) and subset[k+1][0]==4 and subset[k+1][1:]==e[1:]
                if not native:zreads.append(e)
            seed=next(e for e in zreads if e[2]>>8==100);assert (seed[1]//3420+224)%lines==100
            origin=seed[1]//3420*3420;writes=[e for e in subset if e[0]==2 and e[1]>=seed[1]];times,values=expected[n//2]
            assert [e[2] for e in writes]==values,(region,n,len(writes),len(values))
            errors=[e[1]-origin-t for e,t in zip(writes,times)]
            assert min(errors)>=0,(region,n,errors)
            gaps=[b[1]-a[1] for a,b in zip(zreads,zreads[1:])];assert max(gaps)<5*3420,(region,n,max(gaps))
            samples=[e for e in subset if e[0]==4 and e[3]==symbols['md_service_clock_hv']+6];assert samples
            assert records[n][0]==samples[-1][1]//20*20-origin,(region,n,records[n][0],samples[-1],origin)
            rows.append(dict(case=n//2,wrapped=bool(n&1),errors_master=errors,z80_sample_gap_master=[min(gaps),max(gaps)],finish_master=records[n][0],source_finish_master=records[n][1],finish_delta=records[n][0]-records[n][1]))
        plain={}
        def plain_observe(frame,ram):
            done=int.from_bytes(bytes(ram[(((symbols['gaw_live_done']&65535)+i)&65535)^1] for i in range(2)),'big');plain.update(frame=frame,done=done)
            if done:plain['ram_sha256']=sha(bytes(ram))
        with contextlib.redirect_stdout(io.StringIO()):
            run(folder/'out/release/rom.bin',20000,folder/(region+'-plain'),set(),[],skip_intro=False,ram_observer=plain_observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(plain.get('done')))
        assert plain=={k:observed[k] for k in plain},(plain,observed)
        result=dict(region=region,**observed,plain_core_identical=True,errors_master=[min(e for r in rows for e in r['errors_master']),max(e for r in rows for e in r['errors_master'])],rows=rows,events_sha256=sha(raw));results.append(result)
        print(region,{k:v for k,v in result.items() if k!='rows'},flush=True)
    report=dict(bare=bare,kernel_sha256=sha((folder/'out/release/rom.bin').read_bytes()),observer_core_sha256=sha(core.read_bytes()),source_dates_sha256=sha(dates_raw),driver_source_sha256=sha(driver_source),driver_sha256=sha(driver),assembly_sources={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['source_md_psg_replay.s','md_service_clock_hv.s']},sources={n:sha((ROOT/'megadrive/src'/(n+'.c')).read_bytes()) for n in modules},results=results,
                limits=['Actual source-checked loader publishes FIFO events during each source IRQ; its trace callback prepares and physically emits those bytes before foreground loading resumes. No precomputed replay values. All16 source checkpoints/IRQ traces/final states remain exact.',
                        'Blocking cooperative scheduling experiment,not an asynchronous IRQ consumer. Delay metrics intentionally not gated to a passing deadline: measure feasibility first. No graphics transfers/DMA/live input/boot phase/whole-game integration.'])
    if bare:report['limits'][0]='Actual source-checked loader publishes FIFO events during each source IRQ; callback prepares/physically emits bytes before foreground resumes. No precomputed output. Full IRQ traces/final hashes/RAM/audio checked; intermediate diagnostic copies omitted during measurement. Separate proof kernel checks all16 source checkpoints.'
    (ROOT/('analysis/md_loading_audio_bare_report.json' if bare else 'analysis/md_loading_audio_report.json')).write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
