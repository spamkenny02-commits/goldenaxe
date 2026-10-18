"""Source-checked native loader/IRQ/reader/FIFO -> continuous physical PSG."""
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
#include "source_md_psg_replay.h"
u8 queued_loading_case(const u32*,u8,u8,u8*,u8*,const u8*,const u8*,u16,const u8*,const u8*,const u8*,const u8*,const u8*,const u8*,u32*,u32*,u32*,u8*,u32*,u8*,u32*);
volatile u16 gaw_replay_done;
volatile u32 gaw_replay_cases,gaw_replay_failures,gaw_replay_bytes;
volatile u32 gaw_replay_extra_cases;
volatile u32 gaw_replay_clocks[48][3];
static u8 ram[336],audio[400],states[11776],values[128];
static u32 output[41],events[384],points[288],due[128],stats[6];
static SourcePsgEvent stream[128];static SourceMdPsgReplayClock physical;
static u16 physical_lines;
static void synthetic(void) {
 u16 row,n,hv,count,status;u32 epoch,before;
 SourceMdPsgReplayClock copy;
 for(row=0;row<7;row++) {
  epoch=row?0xffff0000UL:0;count=row==0?4:8;
  for(n=0;n<count;n++) {
   stream[n].due=epoch+20000UL+(u32)n*315;
   stream[n].value=(u8)(0x9f+(n%4)*0x20);
  }
  if(row==2) {
   stream[4].due=epoch+26615UL;stream[5].due=epoch+27245UL;
   stream[6].due=epoch+33785UL;stream[7].due=epoch+34415UL;
  }
  while((*(volatile u16*)0xc00008>>8)!=90) {}
  *(volatile u16*)0xc00010=0x40+row;
  while((*(volatile u16*)0xc00008>>8)!=100) {}
  hv=*(volatile u16*)0xc00008;
  if(source_md_psg_replay_seed(&physical,physical_lines,hv,epoch)) gaw_replay_failures++;
  if(row==3) {
   copy=physical;
   if(source_md_psg_replay(&physical,stream,0) || memcmp(&copy,&physical,sizeof(copy))) gaw_replay_failures++;
  } else if(row==4 || row==5) {
   if(row==4) physical.lines=0;else physical.error=1;
   before=physical.master;status=source_md_psg_replay(&physical,stream,count);
   if(status!=1 || physical.error!=1 || physical.master!=before) gaw_replay_failures++;
  } else if(row==6) {
   copy=physical;
   if(source_md_psg_replay_seed(&physical,262,0x6494,0)!=1 || memcmp(&copy,&physical,sizeof(copy)) || source_md_psg_replay_seed(0,262,0x6485,0)!=1) gaw_replay_failures++;
  } else if(source_md_psg_replay(&physical,stream,count)) gaw_replay_failures++;
  gaw_replay_extra_cases++;
 }
}
int main(bool hard_reset) {
 u16 row,mode,n,hv;u32 epoch;
 (void)hard_reset;
 physical_lines=SYS_isPAL()?313:262;
 SYS_disableInts();VDP_setScreenWidth256();VDP_setScreenHeight224();VDP_setEnable(FALSE);
 SYS_enableInts();SYS_doVBlankProcess();SYS_doVBlankProcess();SYS_doVBlankProcess();SYS_disableInts();
 synthetic();
 for(row=0;row<24;row++) for(mode=0;mode<2;mode++) {
  epoch=mode?0xffff0000UL:0;
  for(n=0;n<336;n++) ram[n]=cases[row].ram[n];
  for(n=0;n<400;n++) audio[n]=cases[row].audio[n];
  if(!queued_loading_case(cases[row].phase,cases[row].refresh,0,ram,audio,low,bank6,cases[row].room,(cases[row].room&128)?bank9:bank8,patterns,bank2,bank11,bank4,cases[row].hud,output,events,points,states,due,values,stats)) {gaw_replay_failures++;continue;}
  for(n=0;n<41;n++) if(output[n]!=cases[row].expected[n]) gaw_replay_failures++;
  for(n=0;n<288;n++) if(points[n]!=cases[row].points[n]) gaw_replay_failures++;
  for(n=0;n<11776;n++) if(states[n]!=cases[row].states[n]) gaw_replay_failures++;
  for(n=0;n<output[7]*6;n++) if(events[n]!=cases[row].events[n]) gaw_replay_failures++;
  if(stats[0]!=psg_counts[row] || stats[1] || stats[2] || stats[3]!=stats[4] || stats[5]) gaw_replay_failures++;
  for(n=0;n<psg_counts[row];n++) {
   if(due[n]!=psg_due[row][n] || values[n]!=psg_values[row][n]) gaw_replay_failures++;
   stream[n].due=due[n]+epoch;stream[n].value=values[n];
  }
  while((*(volatile u16*)0xc00008>>8)!=90) {}
  *(volatile u16*)0xc00010=0x80+row*2+mode;
  while((*(volatile u16*)0xc00008>>8)!=100) {}
  hv=*(volatile u16*)0xc00008;
  if(source_md_psg_replay_seed(&physical,physical_lines,hv,epoch)) gaw_replay_failures++;
  if(source_md_psg_replay(&physical,stream,psg_counts[row])) gaw_replay_failures++;
  gaw_replay_clocks[row*2+mode][0]=physical.master;
  gaw_replay_clocks[row*2+mode][1]=physical.vertical;
  gaw_replay_clocks[row*2+mode][2]=physical.horizontal;
  gaw_replay_cases++;gaw_replay_bytes+=psg_counts[row];
 }
 gaw_replay_done=1;while(TRUE) {}return 0;
}
'''


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    beam='--beam' in sys.argv
    compat='--compat' in sys.argv
    planned='--planned' in sys.argv or beam
    extra_count=33 if planned else 7
    folder=ROOT/('validation/md-psg-replay-beam' if beam else 'validation/md-psg-replay-planned' if planned else 'validation/md-psg-replay-compat' if compat else 'validation/md-psg-replay');src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    archive=ROOT/'analysis/native-copy-pointers-v0203';manifest=json.loads((archive/'manifest.json').read_text())
    item=manifest['compressed']['validation/native-planned-room-finish/kernel/src/expected.h'];stored=(archive/item['stored']).read_bytes();assert sha(stored)==item['stored_sha256']
    raw=gzip.decompress(stored);assert sha(raw)==item['raw_sha256'];(src/'expected.h').write_bytes(raw)
    oracle=ROOT/'analysis/loading-psg-v0203';original=json.loads((oracle/'manifest.json').read_text());name='validation/loading-psg-deadlines/inputs.json'
    raw=(oracle/name).read_bytes();assert sha(raw)==original['files'][name];inputs=json.loads(raw);fixture_sha=sha(raw)
    dates_raw=(ROOT/'analysis/loading_psg_deadlines_report.json').read_bytes();dates=json.loads(dates_raw)['results'][0]['rows']
    expected=[]
    for case in range(24):
        times=[t for row in dates if row['case']==case for t in row['source_psg_master']]
        values=[v for row in inputs if row['case']==case for v in row['writes']]
        assert len(times)==len(values)<=128;expected.append((times,values))
    (src/'psg.h').write_text('static const u16 psg_counts[]={'+','.join(str(len(t)) for t,_ in expected)+'};\n'+
        'static const u32 psg_due[24][128]={'+','.join('{'+','.join(str(t)+'UL' for t in times)+'}' for times,_ in expected)+'};\n'+
        'static const u8 psg_values[24][128]={'+','.join('{'+','.join(map(str,values))+'}' for _,values in expected)+'};\n')
    modules=list(dict.fromkeys([n for n in MODULES if n!='source_irq_context']+TIMED_MODULES+['source_audio_fast_timed','source_irq_queue_context','source_psg_queue','source_psg_stream','source_md_psg_replay_seed']))
    main=MAIN
    if planned:
        modules+=['source_md_psg_plan']
        main=main.replace('#include "source_md_psg_replay.h"','#include "source_md_psg_replay.h"\n#include "source_md_psg_plan.h"')
        main=main.replace('static u16 physical_lines;','static u16 physical_lines;static SourceMdPsgBlock blocks[128];static u16 block_count;')
        main=main.replace('row<7','row<33').replace('count=row==0?4:8;','count=row==0?4:row==7?16:row>=25?row-24:row>=9?row-8:8;')
        main=main.replace('(u32)n*315;','(u32)n*((row==8 || row>=25)?630:315);')
        main=main.replace('(u8)(0x9f+(n%4)*0x20);','(u8)(row>=9?n*13+row*7:0x9f+(n%4)*0x20);')
        needle='  while((*(volatile u16*)0xc00008>>8)!=90) {}'
        first=main.index(needle)
        main=main[:first]+'  if(source_md_psg_plan(stream,count,blocks,128,&block_count)) gaw_replay_failures++;\n'+main[first:]
        second=main.index(needle,first+len(needle)+100)
        main=main[:second]+'  if(source_md_psg_plan(stream,psg_counts[row],blocks,128,&block_count)) gaw_replay_failures++;\n'+main[second:]
        main=main.replace('source_md_psg_replay(&physical,stream,count)','source_md_psg_replay_planned(&physical,blocks,block_count)')
        main=main.replace('source_md_psg_replay(&physical,stream,0)','source_md_psg_replay_planned(&physical,blocks,0)')
        main=main.replace('source_md_psg_replay(&physical,stream,psg_counts[row])','source_md_psg_replay_planned(&physical,blocks,block_count)')
        main=main.replace('physical_lines=SYS_isPAL()?313:262;','physical_lines=SYS_isPAL()?313:262;\n if(sizeof(SourceMdPsgBlock)!=28) gaw_replay_failures++;')
        if beam:
            for expression in ['count','psg_counts[row]']:
                needle='  if(source_md_psg_plan(stream,'+expression+',blocks,128,&block_count)) gaw_replay_failures++;'
                assert main.count(needle)==1
                main=main.replace(needle,needle+'\n  if(source_md_psg_plan_beam(blocks,block_count,physical_lines,100,epoch)) gaw_replay_failures++;')
    (src/'wrapper.c').write_text(wrapper());(src/'main.c').write_text(main)
    for module in modules:
        prefix='#define source_irq_interrupt source_irq_queue_interrupt\n' if module!='source_irq_queue_context' else ''
        (src/(module+'.c')).write_text(prefix+'#include "../../../megadrive/src/'+module+'.c"\n')
    for name in ['source_room_finish.h','source_irq_queue_context.h','source_pattern_plan_generated.h','source_md_psg_replay.h']+(['source_md_psg_plan.h'] if planned else []):
        (src/name).write_text('#include "../../../megadrive/src/'+name+'"\n')
    (src/'source_md_psg_replay.s').write_bytes((ROOT/'megadrive/src/source_md_psg_replay.s').read_bytes())
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH']
    temporary=folder/'compiler-tmp';temporary.mkdir(exist_ok=True)
    for key in ['TMPDIR','TMP','TEMP']:env[key]=temporary.resolve().as_posix()
    path=sdk.as_posix();unix='/'+path[0].lower()+path[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True)
    (folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2500:]
    (folder/'disassembly.txt').write_text(subprocess.check_output([str(sdk/'bin/objdump.exe'),'-d',str(folder/'out/release/rom.out')],text=True))
    symbols={m[2]:int(m[1],16) for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    # The IO observer records PC after the absolute-address MOVE.W operand.
    sample_pc=symbols['source_md_psg_replay_sample']+6
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_io_libretro.dll';dll=c.CDLL(str(core))
    dll.gaw_io_reset.argtypes=[c.c_uint];dll.gaw_io_reset.restype=None
    dll.gaw_io_size.restype=dll.gaw_io_errors.restype=c.c_uint;dll.gaw_io_data.restype=c.POINTER(c.c_uint)
    results=[]
    for region,lines in [('ntsc',262),('pal',313)]:
        period=lines*3420;events=[];observed={};last_reads={};poll_gaps=[];seed_gaps=[];current=[-1];previous=[None];last_any=[None];clocks=[];dll.gaw_io_reset(0)
        def observe(frame,ram):
            count=dll.gaw_io_size();assert not dll.gaw_io_errors();ptr=dll.gaw_io_data()
            for n in range(count):
                kind=ptr[n*4];master=(frame-1)*period+int(ptr[n*4+1]);value=int(ptr[n*4+2]);pc=int(ptr[n*4+3])
                if kind!=1:
                    events.append([int(kind),master,value,pc])
                    if kind==3 and 128<=value<176:current[0]=value-128;previous[0]=None
                    if kind==3 and 64<=value<64+extra_count:current[0]=48+value-64;previous[0]=None
                elif pc==sample_pc and current[0]>=0:
                    if previous[0] is not None:poll_gaps.append(master-previous[0])
                    elif last_any[0] is not None:seed_gaps.append(master-last_any[0])
                    previous[0]=master;last_reads[current[0]]=[master,value]
                if kind==1:last_any[0]=master
            dll.gaw_io_reset(1)
            def value(name,width,offset=0):return int.from_bytes(bytes(ram[(((symbols[name]&65535)+offset+i)&65535)^1] for i in range(width)),'big')
            observed.update(frame=frame,done=value('gaw_replay_done',2),cases=value('gaw_replay_cases',4),extra_cases=value('gaw_replay_extra_cases',4),failures=value('gaw_replay_failures',4),bytes=value('gaw_replay_bytes',4))
            if observed['done']:
                observed['ram_sha256']=sha(bytes(ram));clocks[:]=[[value('gaw_replay_clocks',4,k*12+i*4) for i in range(3)] for k in range(48)]
        with contextlib.redirect_stdout(io.StringIO()):
            run(folder/'out/release/rom.bin',10000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core=core,
                core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        raw=json.dumps(events,separators=(',',':')).encode();(folder/(region+'-events.json')).write_bytes(raw)
        (folder/(region+'-clock.json')).write_text(json.dumps(dict(observed=observed,clocks=clocks,last_reads=last_reads,seed_gaps=seed_gaps,poll_gaps=poll_gaps)))
        assert observed.get('done') and observed['cases']==48 and observed['extra_cases']==extra_count and not observed['failures'] and observed['bytes']==2976,observed
        expected_clocks=48+extra_count-4;gap_bound=10260
        assert len(last_reads)==expected_clocks and len(seed_gaps)==expected_clocks and max(seed_gaps)<gap_bound and max(poll_gaps)<gap_bound,(len(last_reads),seed_gaps,max(poll_gaps))
        markers=[n for n,event in enumerate(events) if event[0]==3 and 128<=event[2]<176];assert len(markers)==48
        extras=[n for n,event in enumerate(events) if event[0]==3 and 64<=event[2]<64+extra_count];assert len(extras)==extra_count
        extra_rows=[]
        for n,index in enumerate(extras):
            marker=events[index];assert marker[2]==64+n and (marker[1]//3420+224)%lines==90
            origin=(marker[1]//3420+10)*3420
            writes=events[index+1:extras[n+1] if n+1<extra_count else markers[0]]
            count=4 if n==0 else n-24 if n>=25 else n-8 if n>=9 else 8 if n<3 or n==8 else 16 if n==7 else 0
            assert len(writes)==count and all(e[0]==2 for e in writes),(region,n,writes)
            assert [e[2] for e in writes]==[(i*13+n*7)&255 if n>=9 else 0x9f+(i%4)*0x20 for i in range(count)]
            times=[20000+i*(630 if n==8 or n>=25 else 315) for i in range(count)]
            if n==2:times[4:]=[26615,27245,33785,34415]
            errors=[event[1]-origin-t for event,t in zip(writes,times)]
            assert all(0<=error<10000 for error in errors),(region,n,errors)
            extra_rows.append(dict(case=n,bytes=count,errors_master=errors))
        rows=[]
        for n,index in enumerate(markers):
            marker=events[index];assert marker[2]==128+n and (marker[1]//3420+224)%lines==90
            origin=(marker[1]//3420+10)*3420;case=n//2;epoch=0xffff0000 if n&1 else 0
            writes=events[index+1:markers[n+1] if n+1<48 else len(events)];times,values=expected[case]
            assert len(writes)==len(times) and [e[2] for e in writes]==values and all(e[0]==2 for e in writes),(region,n,len(writes),len(times))
            errors=[event[1]-origin-due for event,due in zip(writes,times)]
            assert all(0<=error<3420 for error in errors),(region,n,errors)
            master,hv=last_reads[n];logical=(epoch+(master//20)*20-origin)&0xffffffff
            assert clocks[n]==[logical,hv&0xff00,(master%3420)//20*20],(region,n,clocks[n],logical,hv,master)
            rows.append(dict(case=case,wrapped=bool(n&1),bytes=len(times),errors_master=errors))
        plain={}
        def observe_plain(frame,ram):
            done=int.from_bytes(bytes(ram[(((symbols['gaw_replay_done']&65535)+i)&65535)^1] for i in range(2)),'big');plain.update(frame=frame,done=done)
            if done:plain['ram_sha256']=sha(bytes(ram))
        with contextlib.redirect_stdout(io.StringIO()):
            run(folder/'out/release/rom.bin',10000,folder/(region+'-plain'),set(),[],skip_intro=False,ram_observer=observe_plain,
                core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(plain.get('done')))
        assert plain=={k:observed[k] for k in plain},(plain,observed)
        result=dict(region=region,**observed,plain_core_identical=True,poll_gap_master=[min(poll_gaps),max(poll_gaps)],seed_gap_master=[min(seed_gaps),max(seed_gaps)],
            errors_master=[min(e for row in rows for e in row['errors_master']),max(e for row in rows for e in row['errors_master'])],events_sha256=sha(raw),rows=rows,synthetic=extra_rows)
        results.append(result);print(region,{k:v for k,v in result.items() if k!='rows'},flush=True)
    report=dict(planned=planned,beam=beam,compat=compat,kernel_sha256=sha((folder/'out/release/rom.bin').read_bytes()),observer_core_sha256=sha(core.read_bytes()),fixture_sha256=fixture_sha,source_dates_sha256=sha(dates_raw),
        helpers={n:sha((ROOT/'megadrive/src'/(n+'.c')).read_bytes()) for n in modules},
        replay_sources={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['source_md_psg_replay.s','source_md_psg_replay.h']+(['source_md_psg_plan.h'] if planned else [])},results=results,
        limits=['All24 source loader cases produce actual timed IRQ/reader/FIFO bytes;16checkpoints,R/M1/RAM/audio/IRQ/data hashes still compared with frozen source vectors before output. Two logical epochs per case,normal/u32wrap,on both physical regions.',
                'Producer completes before replay. FIFO is drained to stable contiguous events,then native assembly blocks while continuously reading HV and emitting real PSG writes. No producer/consumer overlap,backpressure,or graphics DMA during output.',
                'Explicit physical line100 seed from marker line90. This is a relative test epoch,not boot alignment. Every final native master/V/H value is compared against the independently observed physical read. Poll/seed gaps are checked against the three-line contract.',
                'Seven native synthetic/fault cases:onequad,twoadjacentquads,mixedquad/pairs,empty,noIOoninvalidlines/stickyfault,invalidseedatomic/nullseed. Eight315tick writes reveal dispatch delay between quads; this remains a known pacing limitation.',
                'First-write and spacing latency remain measured,not exact source deadlines. IRQs/display disabled;not real hardware or playable integration.'])
    if planned:
        report['limits'][-2]='33 native synthetic/fault cases include every315count1..16 and630count1..8 with distinct bytes,and contiguous315x16/630x8 caps. Metadata prepared before seed. Longer runs still split at these caps and are not proven accurately paced.'
    if beam:report['limits'].append('Absolute coarse clock hands over to precomputed rounded-up H32 beam targets within3420master of due. Fresh V classification detects a passed target before entering its wait. Planned mode refreshes the clock after final IO.')
    (ROOT/('analysis/md_psg_replay_beam_report.json' if beam else 'analysis/md_psg_replay_planned_report.json' if planned else 'analysis/md_psg_replay_compat_report.json' if compat else 'analysis/md_psg_replay_report.json')).write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
