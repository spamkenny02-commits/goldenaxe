"""Actual native source loader/reader/FIFO -> independently paced Z80 PSG IO."""
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
from validate_md_psg_replay import MAIN
from validate_queued_loading import wrapper
from validate_native_room_finish import MODULES
from validate_reader_timing import MODULES as TIMED_MODULES

OUTPUT=r'''
static MdZ80PsgMailbox mailbox;static MdServiceClock timer;static MdZ80PsgProducer producer;
volatile u32 gaw_z80_failure_code;
static SourceMdPsgBlock blocks[128];static u32 full_waits;
volatile u32 gaw_z80_foreground,gaw_z80_work_count;
volatile u32 gaw_z80_queue_full,gaw_z80_grant_wait,gaw_z80_wrap_head,gaw_z80_wrap_tail,gaw_z80_refresh_counter;
static void work(void) {gaw_z80_foreground=(gaw_z80_foreground<<1)^((gaw_z80_foreground&0x80000000UL)?0x04c11db7UL:0);gaw_z80_work_count++;}
static void run_z80(u16 count,u16 marker,u32 epoch) {
 u16 n,used;u8 status;u32 spins=0;
 if(marker==88) used=512;
 else if(source_md_psg_plan(stream,count,blocks,128,&used)) {gaw_replay_failures++;return;}
 Z80_requestBus(TRUE);*(volatile u16*)0xc00010=marker;
 status=md_z80_psg_start(&mailbox,physical_lines,driver,sizeof(driver));if(status) {gaw_z80_failure_code=0x100|status;gaw_replay_failures++;return;}
 status=md_service_clock_init(&timer,&mailbox.stamp,physical_lines,epoch);if(status) {gaw_z80_failure_code=0x200|status;gaw_replay_failures++;return;}
 status=md_z80_psg_init(&producer,&mailbox,&timer);if(status) {gaw_z80_failure_code=0x300|status;gaw_replay_failures++;return;}
 SYS_disableInts();full_waits=0;
 while(!mailbox.stamp.ready && !mailbox.stamp.error && ++spins<100000UL) work();
 if(!mailbox.stamp.ready || mailbox.stamp.error) {gaw_z80_failure_code=0x400|mailbox.stamp.error;gaw_replay_failures++;return;}
 for(n=0;n<used;n++) {
  u16 one;SourceMdPsgBlock *next=blocks;
  if(marker!=88) next+=n;
  if(marker==88) {
   stream[0].due=epoch+(u32)physical_lines*6840+(u32)n*547200UL;stream[0].value=(u8)(99+n*13);
   if(source_md_psg_plan(stream,1,blocks,128,&one) || one!=1) {gaw_replay_failures++;break;}next=blocks;
  }
  spins=0;
  do {
   status=md_z80_psg_push(&producer,next,1);work();
   if(status==MD_Z80_PSG_FULL || status==MD_Z80_PSG_WAIT) full_waits++;
   if(status==MD_Z80_PSG_FULL) gaw_z80_queue_full++;
   if(status==MD_Z80_PSG_WAIT) gaw_z80_grant_wait++;
  } while((status==MD_Z80_PSG_FULL || status==MD_Z80_PSG_WAIT) && ++spins<100000UL);
  if(status) {gaw_z80_failure_code=0x500|status;gaw_replay_failures++;break;}
 }
 spins=0;
 while((mailbox.head!=mailbox.tail || mailbox.busy) && !mailbox.stamp.error && ++spins<1000000UL) work();
 if(mailbox.head!=mailbox.tail || mailbox.busy || mailbox.stamp.error || producer.error || producer.published!=used) {gaw_z80_failure_code=0x600|(mailbox.stamp.error<<4)|producer.error;gaw_replay_failures++;}
 if(marker==88) {gaw_z80_wrap_head=mailbox.head;gaw_z80_wrap_tail=mailbox.tail;gaw_z80_refresh_counter=producer.counter;if(mailbox.head || mailbox.tail || producer.counter==100) gaw_replay_failures++;}
 spins=0;while(md_z80_psg_stop(&mailbox)==MD_Z80_PSG_WAIT && ++spins<100000UL) work();spins=0;
 while(mailbox.stamp.ready && ++spins<100000UL) work();
 if(mailbox.stamp.ready) {gaw_z80_failure_code=0x700;gaw_replay_failures++;}
}
static void synthetic(void) {
 u16 row,n,count,spacing;u32 epoch;
 for(row=0;row<24;row++) {
  count=row<16?row+1:row-15;spacing=row<16?315:630;epoch=(row&1)?0xffff0000UL:0;
  for(n=0;n<count;n++) {stream[n].due=epoch+(u32)physical_lines*6840+(u32)row*133%3420+(u32)n*spacing;stream[n].value=(u8)(row*7+n*13);}
  run_z80(count,64+row,epoch);gaw_replay_extra_cases++;
 }
 run_z80(0,88,0xffff0000UL);gaw_replay_extra_cases++;
}
'''


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    folder=ROOT/'validation/md-z80-psg';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    frozen=ROOT/'analysis/native-copy-pointers-v0203';m=json.loads((frozen/'manifest.json').read_text());item=m['compressed']['validation/native-planned-room-finish/kernel/src/expected.h']
    encoded=(frozen/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'];(src/'expected.h').write_bytes(raw)
    oracle=ROOT/'analysis/loading-psg-v0203';m=json.loads((oracle/'manifest.json').read_text());name='validation/loading-psg-deadlines/inputs.json';raw=(oracle/name).read_bytes();assert sha(raw)==m['files'][name];inputs=json.loads(raw)
    dates_raw=(ROOT/'analysis/loading_psg_deadlines_report.json').read_bytes();dates=json.loads(dates_raw)['results'][0]['rows'];expected=[]
    for case in range(24):
        times=[t for row in dates if row['case']==case for t in row['source_psg_master']];values=[v for row in inputs if row['case']==case for v in row['writes']];assert len(times)==len(values)<=128;expected.append((times,values))
    (src/'psg.h').write_text('static const u16 psg_counts[]={'+','.join(str(len(t)) for t,_ in expected)+'};\n'+'static const u32 psg_due[24][128]={'+','.join('{'+','.join(str(t)+'UL' for t in times)+'}' for times,_ in expected)+'};\n'+'static const u8 psg_values[24][128]={'+','.join('{'+','.join(map(str,v))+'}' for _,v in expected)+'};\n')
    main=MAIN.replace('#include "source_md_psg_replay.h"','#include "source_md_psg_replay.h"\n#include "md_z80_psg.h"\n#include "driver.h"')
    first=main.index('static void synthetic(void)');last=main.index('int main(bool hard_reset)',first);main=main[:first]+OUTPUT+main[last:]
    first=main.index('  while((*(volatile u16*)0xc00008>>8)!=90) {}');last=main.index('  gaw_replay_cases++;',first)
    main=main[:first]+'''  run_z80(psg_counts[row],128+row*2+mode,epoch);
  gaw_replay_clocks[row*2+mode][0]=mailbox.head;
  gaw_replay_clocks[row*2+mode][1]=mailbox.tail;
  gaw_replay_clocks[row*2+mode][2]=full_waits;
'''+main[last:]
    main=main.replace(' synthetic();',' gaw_z80_foreground=0x8123905UL;synthetic();')
    (src/'main.c').write_text(main);(src/'wrapper.c').write_text(wrapper());(folder/'validator.py.snapshot').write_bytes((ROOT/'tools/validate_md_z80_psg.py').read_bytes())
    modules=list(dict.fromkeys([n for n in MODULES if n!='source_irq_context']+TIMED_MODULES+['source_audio_fast_timed','source_irq_queue_context','source_psg_queue','source_psg_stream','source_md_psg_plan','md_service_clock','md_service_clock_start','md_z80_psg','md_z80_psg_start']))
    for module in modules:
        prefix='#define source_irq_interrupt source_irq_queue_interrupt\n' if module!='source_irq_queue_context' else ''
        (src/(module+'.c')).write_text(prefix+'#include "../../../megadrive/src/'+module+'.c"\n')
    for name in ['source_room_finish.h','source_irq_queue_context.h','source_pattern_plan_generated.h','source_md_psg_replay.h','md_z80_psg.h']:(src/name).write_text('#include "../../../megadrive/src/'+name+'"\n')
    (src/'md_service_clock_hv.s').write_bytes((ROOT/'megadrive/src/md_service_clock_hv.s').read_bytes())
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH']
    asm=ROOT/'megadrive/z80/md_psg_output_z80.asm';(folder/'driver-source.asm.snapshot').write_bytes(asm.read_bytes())
    built=subprocess.run([str(sdk/'bin/sjasm.exe'),str(asm),str(folder/'driver.bin'),str(folder/'driver.lst')],env=env,capture_output=True,text=True);(folder/'z80-build.log').write_text(built.stdout+built.stderr);assert not built.returncode and 'Errors: 0' in built.stdout,built.stdout+built.stderr
    driver=(folder/'driver.bin').read_bytes();(src/'driver.h').write_text('static const u8 driver[]={'+','.join(map(str,driver))+'};\n')
    clock_pc=int(re.search(r'^\d+\s+([0-9A-F]+)[^\n]*clock:\s+ld a,\(0x7f08\)',(folder/'driver.lst').read_text(),re.M)[1],16)+3
    temporary=folder/'compiler-tmp';temporary.mkdir(exist_ok=True)
    for key in ['TMPDIR','TMP','TEMP']:env[key]=temporary.resolve().as_posix()
    path=sdk.as_posix();unix='/'+path[0].lower()+path[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True);(folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2500:]
    symbols={m[2]:int(m[1],16) for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_z80_psg_io_libretro.dll';dll=c.CDLL(str(core));dll.gaw_io_reset.argtypes=[c.c_uint];dll.gaw_io_reset.restype=None;dll.gaw_io_size.restype=dll.gaw_io_errors.restype=c.c_uint;dll.gaw_io_data.restype=c.POINTER(c.c_uint);results=[]
    dll.gaw_z80_ram.restype=c.POINTER(c.c_uint8);dll.gaw_z80_pc.restype=c.c_uint
    for region,lines in [('ntsc',262),('pal',313)]:
        events=[];observed={};records=[];publications=[];active=[None];dll.gaw_io_reset(0);period=lines*3420
        mb=next(v for k,v in symbols.items() if k.split('.')[0]=='mailbox')&65535
        def observe(frame,ram):
            size=dll.gaw_io_size();assert not dll.gaw_io_errors();ptr=dll.gaw_io_data();events.extend([[int(ptr[n*4]),(frame-1)*period+int(ptr[n*4+1]),int(ptr[n*4+2]),int(ptr[n*4+3])] for n in range(size)]);dll.gaw_io_reset(1)
            def value(name,width,offset=0):return int.from_bytes(bytes(ram[(((symbols[name]&65535)+offset+i)&65535)^1] for i in range(width)),'big')
            observed.update(frame=frame,done=value('gaw_replay_done',2),cases=value('gaw_replay_cases',4),extra_cases=value('gaw_replay_extra_cases',4),failures=value('gaw_replay_failures',4),bytes=value('gaw_replay_bytes',4),failure_code=value('gaw_z80_failure_code',4),foreground=value('gaw_z80_foreground',4),work_count=value('gaw_z80_work_count',4),queue_full=value('gaw_z80_queue_full',4),grant_wait=value('gaw_z80_grant_wait',4),wrap_head=value('gaw_z80_wrap_head',4),wrap_tail=value('gaw_z80_wrap_tail',4),refresh_counter=value('gaw_z80_refresh_counter',4))
            for e in events[-size:] if size else []:
                if e[0]==3 and (64<=e[2]<=88 or 128<=e[2]<176):active[0]=e[2]
            stamp=[ram[(mb+i)^1] for i in range(6)]
            if active[0] is not None and stamp[4] and not stamp[0]&1:publications.append(dict(tag=active[0],frame=frame,counter=stamp[2]*256+stamp[3],v=stamp[1]))
            if observed['done']:
                observed['z80_pc']=dll.gaw_z80_pc();observed['z80_variables']=list(dll.gaw_z80_ram()[0x100:0x121]);observed['ram_sha256']=sha(bytes(ram));records[:]=[[value('gaw_replay_clocks',4,n*12+i*4) for i in range(3)] for n in range(48)]
        with contextlib.redirect_stdout(io.StringIO()):run(folder/'out/release/rom.bin',20000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core=core,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        raw=json.dumps(dict(events=events,observed=observed,records=records,publications=publications),separators=(',',':')).encode();(folder/(region+'-events.json')).write_bytes(raw)
        assert observed.get('done') and not observed['failures'] and observed['cases']==48 and observed['bytes']==2976 and observed['extra_cases']==25 and not observed['wrap_head'] and not observed['wrap_tail'] and observed['refresh_counter']!=100 and observed['queue_full'] and observed['grant_wait'],observed
        markers=[i for i,e in enumerate(events) if e[0]==3 and 64<=e[2]<=88 or e[0]==3 and 128<=e[2]<176];assert len(markers)==73
        work=0x8123905
        for _ in range(observed['work_count']):work=((work<<1)^(0x04c11db7 if work&0x80000000 else 0))&0xffffffff
        assert observed['work_count']>0 and work==observed['foreground'],observed
        rows=[]
        for ordinal,index in enumerate(markers):
            marker=events[index];part=events[index+1:markers[ordinal+1] if ordinal+1<len(markers) else len(events)]
            reads=[e for e in part if e[0]==6];seed=next(e for e in reads if e[2]>>8==100);assert (seed[1]//3420+224)%lines==100;origin=seed[1]//3420*3420
            writes=[e for e in part if e[0]==5];tag=marker[2]
            if tag==88:times=[period*2+n*547200 for n in range(512)];values=[(99+n*13)&255 for n in range(512)]
            elif tag<128:
                n=tag-64;count=n+1 if n<16 else n-15;spacing=315 if n<16 else 630;times=[period*2+n*133%3420+k*spacing for k in range(count)];values=[(n*7+k*13)&255 for k in range(count)]
            else:times,values=expected[(tag-128)//2]
            assert [e[2] for e in writes]==values,(region,tag,len(writes),len(values))
            errors=[e[1]-origin-t for e,t in zip(writes,times)];assert min(errors)>=0,(region,tag,errors)
            gaps=[b[1]-a[1] for a,b in zip(reads,reads[1:])];assert max(gaps)<17100,(region,tag,max(gaps))
            clocks=[e for e in part if e[0]==6 and e[3]==clock_pc];assert clocks
            advances=[b[1]//3420-a[1]//3420 for a,b in zip(clocks,clocks[1:])];assert min(advances)>=0 and max(advances)<=5,(region,tag,min(advances),max(advances))
            counter_values=[(100+e[1]//3420-origin//3420)&65535 for e in clocks];counter_wraps=sum(b<a for a,b in zip(counter_values,counter_values[1:]))
            if tag==88:assert counter_wraps>=1,(region,tag,counter_wraps)
            checks=0
            for pub in (p for p in publications if p['tag']==tag):
                candidates=[e for e in clocks if e[1]//period+1<=pub['frame']][-2:]
                assert any(pub['counter']==(100+e[1]//3420-origin//3420)&65535 and pub['v']==e[2]>>8 for e in candidates),(region,tag,pub,candidates)
                checks+=1
            first=0;spacing_checks=0;bursts=[]
            while first<len(times):
                spacing=times[first+1]-times[first] if first+1<len(times) else 0;limit=16 if spacing==315 else 8 if spacing==630 else 1;count=1
                while first+count<len(times) and count<limit and times[first+count]-times[first+count-1]==spacing:count+=1
                for k in range(1,count):assert writes[first+k][1]-writes[first+k-1][1]==spacing,(region,tag,first,k,spacing);spacing_checks+=1
                if count>1:bursts.append((writes[first][1],writes[first+count-1][1]))
                first+=count
            holds=[];held_ranges=[];start=None
            for e in part:
                if e[0]!=7 or e[1]<origin:continue
                if e[2] and start is None:start=e[1]
                if not e[2] and start is not None:holds.append(e[1]-start);held_ranges.append((start,e[1]));start=None
            # The next session requests the bus immediately before its marker;
            # that unmatched final request belongs to the following startup.
            assert (start is None or start>=writes[-1][1]) and holds and max(holds)<6840,(region,tag,start,holds)
            assert not any(a<end and b>begin for a,b in held_ranges for begin,end in bursts),(region,tag,'BUSREQ overlaps burst')
            rows.append(dict(marker=tag,errors_master=errors,sample_gap_master=[min(gaps),max(gaps)],clock_line_advance=[min(advances),max(advances)],counter_wraps=counter_wraps,clock_publication_checks=checks,spacing_checks=spacing_checks,bus_holds_master=[min(holds),max(holds)]))
        plain={}
        def plain_observe(frame,ram):
            done=int.from_bytes(bytes(ram[(((symbols['gaw_replay_done']&65535)+i)&65535)^1] for i in range(2)),'big');plain.update(frame=frame,done=done)
            if done:plain['ram_sha256']=sha(bytes(ram))
        with contextlib.redirect_stdout(io.StringIO()):run(folder/'out/release/rom.bin',20000,folder/(region+'-plain'),set(),[],skip_intro=False,ram_observer=plain_observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(plain.get('done')))
        assert plain=={k:observed[k] for k in plain},(plain,observed)
        result=dict(region=region,**observed,plain_core_identical=True,errors_master=[min(e for r in rows for e in r['errors_master']),max(e for r in rows for e in r['errors_master'])],rows=rows,events_sha256=sha(raw));results.append(result);print(region,{k:v for k,v in result.items() if k!='rows'},flush=True)
    report=dict(kernel_sha256=sha((folder/'out/release/rom.bin').read_bytes()),driver_sha256=sha(driver),driver_source_sha256=sha(asm.read_bytes()),observer_core_sha256=sha(core.read_bytes()),headers={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['md_z80_psg.h','md_service_clock.h','source_md_psg_plan.h']},sources={n+'.c':sha((ROOT/'megadrive/src'/(n+'.c')).read_bytes()) for n in modules},results=results,
                limits=['Actual native source loader/IRQ/reader/FIFO checked against all16source checkpoints before output. Producer completes before timed replay; foreground polynomial work runs while native publisher/Z80consumer communicate. No actual loader/audio overlap or full-game/DMA/input/boot proof.',
                        'Separate32descriptor ring in Z80RAM;Z80 cannot read68000RAM. Native writer takes bounded BUSREQ only under a Z80grant;one descriptor per grant,grant revoked by native writer before release. Z80 copies values locally before releasing tail;busy excludes in-flight command from drain. Status/timestamps written to68000RAM. Critical wait/burst keeps publication sequence odd. Internal timer must not advance more than5physical lines between samples;rawVC alias at6is unsupported.',
                        'Every315/630intraburst interval exact for original streams and24partial-burst synthetics. Long512command session forces32slot/full-queue pressure,two8bitcursorwraps,16bitlinecounterwrap androlling clock epoch refresh,withu32sourcewrap. Native volatile foreground polynomial checked independently from counted iterations. Every visible even clock stamp checked against last two physically sampled counters. No maximum lateness acceptance gate: initial backend measurement,not production success.'])
    (ROOT/'analysis/md_z80_psg_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
