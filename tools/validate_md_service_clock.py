"""Hardware Z80 coarse stamp -> native68000 clock during long computation."""
import contextlib
import ctypes as c
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from actor_reference import ROOT
from run_core import run

MAIN=r'''
#include <genesis.h>
#include "md_service_clock.h"
#include "driver.h"
volatile MdServiceStamp gaw_service_stamp;
MdServiceClock gaw_service_clock;
volatile u16 gaw_service_done;
volatile u32 gaw_service_failures,gaw_service_count,gaw_service_progress;
volatile u32 gaw_service_records[1200][4];
volatile u32 gaw_service_hash_a,gaw_service_hash_b;
static u8 scratch[512];
static __attribute__((noinline)) u32 foreground(u16 n,u32 value) {
 u16 k,count=(n*97)&8191;
 for(k=0;k<count;k++) {value=(value<<1)^((value&0x80000000UL)?0x04c11db7UL:0);scratch[k&511]=(u8)value;}
 return value+scratch[n&511];
}
int main(bool hard_reset) {
 u16 n,lines;u32 value,spins;u8 status;SourceMdPsgReplayClock now;
 (void)hard_reset;lines=SYS_isPAL()?313:262;
 SYS_disableInts();VDP_setScreenWidth256();VDP_setScreenHeight224();VDP_setEnable(FALSE);
 for(n=0;n<512;n++) scratch[n]=0;
 value=0x8123905;
 *(volatile u16*)0xc00010=0x60;
 for(n=0;n<1200;n++) {value=foreground(n,value);gaw_service_progress=n;}
 *(volatile u16*)0xc00010=0x61;gaw_service_hash_a=value;
 for(n=0;n<512;n++) scratch[n]=0;
 *(volatile u16*)0xc00010=0x55;
 if(md_service_clock_start((MdServiceStamp *)&gaw_service_stamp,lines,driver,sizeof(driver)) || md_service_clock_init(&gaw_service_clock,(MdServiceStamp *)&gaw_service_stamp,lines,0xffff0000UL)) gaw_service_failures++;
 SYS_disableInts();spins=0;
 do {status=md_service_clock_now(&gaw_service_clock,&now);} while(status==MD_SERVICE_WAIT && ++spins<100000UL);
 if(status!=MD_SERVICE_OK) gaw_service_failures++;
 value=0x8123905;
 *(volatile u16*)0xc00010=0x62;
 for(n=0;n<1200;n++) {
  value=foreground(n,value);gaw_service_progress=n;spins=0;
  do {status=md_service_clock_now(&gaw_service_clock,&now);} while(status==MD_SERVICE_WAIT && ++spins<100000UL);
  if(status!=MD_SERVICE_OK) {gaw_service_failures++;break;}
  gaw_service_records[n][0]=now.master;gaw_service_records[n][1]=now.vertical;
  gaw_service_records[n][2]=now.horizontal;gaw_service_records[n][3]=gaw_service_clock.counter;
  gaw_service_count++;
 }
 *(volatile u16*)0xc00010=0x63;gaw_service_hash_b=value;
 if(gaw_service_hash_a!=gaw_service_hash_b) gaw_service_failures++;
 gaw_service_done=1;while(TRUE) {}return 0;
}
'''


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    candidate='--candidate' in sys.argv
    folder=ROOT/('validation/md-service-clock-candidate' if candidate else 'validation/md-service-clock');src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH']
    driver_source=(ROOT/'megadrive/z80/md_service_clock_z80.asm').read_bytes();(folder/'driver-source.asm.snapshot').write_bytes(driver_source)
    built=subprocess.run([str(sdk/'bin/sjasm.exe'),str(ROOT/'megadrive/z80/md_service_clock_z80.asm'),str(folder/'driver.bin'),str(folder/'driver.lst')],env=env,capture_output=True,text=True)
    (folder/'z80-build.log').write_text(built.stdout+built.stderr);assert not built.returncode and 'Errors: 0' in built.stdout,built.stdout+built.stderr
    driver=(folder/'driver.bin').read_bytes();(src/'driver.h').write_text('static const u8 driver[]={'+','.join(map(str,driver))+'};\n')
    (src/'main.c').write_text(MAIN)
    modules=['md_service_clock.c','md_service_clock_start.c']
    for name in modules:(src/name).write_text('#include "../../../megadrive/src/'+name+'"\n')
    (src/'md_service_clock.h').write_text('#include "../../../megadrive/src/md_service_clock.h"\n')
    (src/'md_service_clock_hv.s').write_bytes((ROOT/'megadrive/src/md_service_clock_hv.s').read_bytes())
    temporary=folder/'compiler-tmp';temporary.mkdir(exist_ok=True)
    for key in ['TMPDIR','TMP','TEMP']:env[key]=temporary.resolve().as_posix()
    path=sdk.as_posix();unix='/'+path[0].lower()+path[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True)
    (folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2000:]
    symbols={m[2]:int(m[1],16) for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};read_pc=symbols['md_service_clock_hv']+6
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_service_io_libretro.dll';dll=c.CDLL(str(core))
    dll.gaw_io_reset.argtypes=[c.c_uint];dll.gaw_io_reset.restype=None;dll.gaw_io_size.restype=dll.gaw_io_errors.restype=c.c_uint;dll.gaw_io_data.restype=c.POINTER(c.c_uint)
    results=[]
    for region,lines in [('ntsc',262),('pal',313)]:
        period=lines*3420;events=[];observed={};records=[];dll.gaw_io_reset(0)
        def observe(frame,ram):
            count=dll.gaw_io_size();assert not dll.gaw_io_errors();ptr=dll.gaw_io_data()
            events.extend([[int(ptr[n*4]),(frame-1)*period+int(ptr[n*4+1]),int(ptr[n*4+2]),int(ptr[n*4+3])] for n in range(count)])
            dll.gaw_io_reset(1)
            def value(name,width,offset=0):return int.from_bytes(bytes(ram[(((symbols[name]&65535)+offset+i)&65535)^1] for i in range(width)),'big')
            observed.update(frame=frame,done=value('gaw_service_done',2),count=value('gaw_service_count',4),failures=value('gaw_service_failures',4),progress=value('gaw_service_progress',4),hash_a=value('gaw_service_hash_a',4),hash_b=value('gaw_service_hash_b',4),
                ready=value('gaw_service_stamp',1,4),error=value('gaw_service_stamp',1,5),client_reads=value('gaw_service_clock',4,8),client_retries=value('gaw_service_clock',4,12))
            if observed['done']:
                records[:]=[[value('gaw_service_records',4,n*16+i*4) for i in range(4)] for n in range(1200)];observed['ram_sha256']=sha(bytes(ram))
        with contextlib.redirect_stdout(io.StringIO()):
            run(folder/'out/release/rom.bin',20000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core=core,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        raw=json.dumps(dict(events=events,records=records,observed=observed),separators=(',',':')).encode();(folder/(region+'-events.json')).write_bytes(raw)
        assert observed.get('done') and observed['count']==1200 and not observed['failures'] and observed['hash_a']==observed['hash_b'] and observed['ready'] and not observed['error'],observed
        markers={e[2]:e[1] for e in events if e[0]==3 and e[2] in [0x55,0x60,0x61,0x62,0x63]};assert len(markers)==5
        zreads=[]
        for n,event in enumerate(events):
            if event[0]!=1:continue
            native=n+1<len(events) and events[n+1][0]==4 and events[n+1][1:]==event[1:]
            if not native and event[1]>markers[0x55]:zreads.append(event)
        seed=next(e for e in zreads if e[2]>>8==100);assert (seed[1]//3420+224)%lines==100
        origin=(seed[1]//3420)*3420
        reads=[e for e in events if e[0]==4 and e[3]==read_pc]
        actual={((0xffff0000+(e[1]//20)*20-origin)&0xffffffff,e[2]&0xff00,(e[1]%3420)//20*20):e[1] for e in reads}
        times=[]
        for n,record in enumerate(records):
            key=tuple(record[:3]);assert key in actual,(region,n,record,origin)
            times.append(actual[key])
        assert all(a<=b for a,b in zip(times,times[1:]));wraps=sum(b[3]<a[3] for a,b in zip(records,records[1:]));assert wraps>0,wraps
        gaps=[b[1]-a[1] for a,b in zip(zreads,zreads[1:])];assert max(gaps)<5*3420,(region,max(gaps))
        baseline=markers[0x61]-markers[0x60];active=markers[0x63]-markers[0x62]
        plain={}
        def observe_plain(frame,ram):
            done=int.from_bytes(bytes(ram[(((symbols['gaw_service_done']&65535)+i)&65535)^1] for i in range(2)),'big');plain.update(frame=frame,done=done)
            if done:plain['ram_sha256']=sha(bytes(ram))
        with contextlib.redirect_stdout(io.StringIO()):
            run(folder/'out/release/rom.bin',20000,folder/(region+'-plain'),set(),[],skip_intro=False,ram_observer=observe_plain,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(plain.get('done')))
        assert plain=={k:observed[k] for k in plain},(plain,observed)
        result=dict(region=region,**observed,plain_core_identical=True,counter_wraps=wraps,z80_sample_gap_master=[min(gaps),max(gaps)],
            client_gap_master=[min(b-a for a,b in zip(times,times[1:])),max(b-a for a,b in zip(times,times[1:]))],baseline_master=baseline,service_master=active,overhead_percent=(active/baseline-1)*100,events_sha256=sha(raw))
        results.append(result);print(result,flush=True)
    report=dict(candidate=candidate,sample_delay=int(re.search(rb'loop:\s+ld b,(\d+)',driver_source)[1]),kernel_sha256=sha((folder/'out/release/rom.bin').read_bytes()),driver_sha256=sha(driver),observer_core_sha256=sha(core.read_bytes()),sources={n:sha((ROOT/('megadrive/z80' if n.endswith('.asm') else 'megadrive/src')/n).read_bytes()) for n in ['md_service_clock.c','md_service_clock.h','md_service_clock_start.c','md_service_clock_hv.s','md_service_clock_z80.asm']},results=results,
        limits=['Hardware Z80 publishes a separate byte-sequenced coarse timestamp in68000RAM;native client reads RAM and atomicHV without requesting the Z80 bus after startup. All1200returned times/region match independent native bus reads during longforegroundcalculation,including16bitlinecounter/u32masterwrap.',
                'Measured wholeloop overhead includes clock client calls,record stores and Z80 bus contention;not the timer cost alone or a whole-game budget. Baseline/service foreground hashes identical.',
                'Explicit seed on unambiguousV100;not game boot alignment. Exclusive custom Z80 driver. DMA/BUSREQ stalls reaching5lines are unsupported and may alias undetectably;client reads must occur at least once per65535lines,seqlock snapshot below128publications. No source IRQ/PSG producer integration yet.'])
    (ROOT/('analysis/md_service_clock_candidate_report.json' if candidate else 'analysis/md_service_clock_report.json')).write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
