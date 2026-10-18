"""Every horizontal deadline phase,including max bursts and line crossings."""
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

MAIN=r'''
#include <genesis.h>
#include "source_md_psg_plan.h"
volatile u16 gaw_sweep_done;
volatile u32 gaw_sweep_cases,gaw_sweep_failures,gaw_sweep_bytes;
SourceMdPsgReplayClock gaw_sweep_clock;
static SourcePsgEvent events[16];static SourceMdPsgBlock blocks[16];
int main(bool hard_reset) {
 u16 row,n,count,kind,phase,used,hv,lines;u32 epoch;
 (void)hard_reset;lines=SYS_isPAL()?313:262;
 SYS_disableInts();VDP_setScreenWidth256();VDP_setScreenHeight224();VDP_setEnable(FALSE);
 SYS_enableInts();SYS_doVBlankProcess();SYS_doVBlankProcess();SYS_doVBlankProcess();SYS_disableInts();
 for(row=0;row<10260;row++) {
  kind=row%3;phase=row/3;count=kind==0?1:kind==1?16:8;epoch=(row&1)?0xffff0000UL:0;
  for(n=0;n<count;n++) {events[n].due=epoch+10260UL+phase+(u32)n*(kind==2?630:315);events[n].value=(u8)(n*13+row);}
  if(source_md_psg_plan(events,count,blocks,16,&used) || used!=1 || source_md_psg_plan_beam(blocks,used,lines,100,epoch)) gaw_sweep_failures++;
  while((*(volatile u16*)0xc00008>>8)!=90) {}
  *(volatile u16*)0xc00010=0x55;
  while((*(volatile u16*)0xc00008>>8)!=100) {}
  hv=*(volatile u16*)0xc00008;
  if(source_md_psg_replay_seed(&gaw_sweep_clock,lines,hv,epoch) || source_md_psg_replay_planned(&gaw_sweep_clock,blocks,used)) gaw_sweep_failures++;
  gaw_sweep_cases++;gaw_sweep_bytes+=count;
 }
 gaw_sweep_done=1;while(TRUE) {}return 0;
}
'''


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    folder=ROOT/'validation/md-psg-beam-sweep';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    (src/'main.c').write_text(MAIN)
    for name in ['source_md_psg_plan.c','source_md_psg_replay_seed.c']:(src/name).write_text('#include "../../../megadrive/src/'+name+'"\n')
    (src/'source_md_psg_plan.h').write_text('#include "../../../megadrive/src/source_md_psg_plan.h"\n')
    (src/'source_md_psg_replay.s').write_bytes((ROOT/'megadrive/src/source_md_psg_replay.s').read_bytes())
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH']
    temporary=folder/'compiler-tmp';temporary.mkdir(exist_ok=True)
    for key in ['TMPDIR','TMP','TEMP']:env[key]=temporary.resolve().as_posix()
    path=sdk.as_posix();unix='/'+path[0].lower()+path[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True)
    (folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2000:]
    symbols={m[2]:int(m[1],16) for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};sample_pc=symbols['source_md_psg_replay_sample']+6
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_io_libretro.dll';dll=c.CDLL(str(core))
    dll.gaw_io_reset.argtypes=[c.c_uint];dll.gaw_io_reset.restype=None;dll.gaw_io_size.restype=dll.gaw_io_errors.restype=c.c_uint;dll.gaw_io_data.restype=c.POINTER(c.c_uint)
    results=[]
    for region,lines in [('ntsc',262),('pal',313)]:
        period=lines*3420;events=[];rows=[];observed={};clocked=[0];last_samples={};previous=[None];seed_last=[None];poll_gaps=[];seed_gaps=[];current=[-1];origins={};dll.gaw_io_reset(0)
        def observe(frame,ram):
            count=dll.gaw_io_size();assert not dll.gaw_io_errors();ptr=dll.gaw_io_data()
            for n in range(count):
                kind=int(ptr[n*4]);master=(frame-1)*period+int(ptr[n*4+1]);value=int(ptr[n*4+2]);pc=int(ptr[n*4+3])
                if kind!=1:
                    events.append([kind,master,value,pc])
                    if kind==3 and value==85:
                        current[0]+=1;previous[0]=None
                        assert (master//3420+224)%lines==90
                        origins[current[0]]=(master//3420+10)*3420
                elif pc==sample_pc and current[0]>=0:
                    if previous[0] is None:seed_gaps.append(master-seed_last[0])
                    else:poll_gaps.append(master-previous[0])
                    previous[0]=master;last_samples[current[0]]=(master,value)
                if kind==1:seed_last[0]=master
            dll.gaw_io_reset(1)
            def value(name,width,offset=0):return int.from_bytes(bytes(ram[(((symbols[name]&65535)+offset+i)&65535)^1] for i in range(width)),'big')
            observed.update(frame=frame,done=value('gaw_sweep_done',2),cases=value('gaw_sweep_cases',4),failures=value('gaw_sweep_failures',4),bytes=value('gaw_sweep_bytes',4))
            if observed['cases']>clocked[0]:
                assert observed['cases']==clocked[0]+1
                index=clocked[0];master,hv=last_samples[index];epoch=0xffff0000 if index&1 else 0
                expected=(epoch+(master//20)*20-origins[index])&0xffffffff
                assert [value('gaw_sweep_clock',4),value('gaw_sweep_clock',2,4),value('gaw_sweep_clock',2,6)]==[expected,hv&0xff00,(master%3420)//20*20],(region,index,'clock')
                clocked[0]+=1
            if observed['done']:observed['ram_sha256']=sha(bytes(ram))
        with contextlib.redirect_stdout(io.StringIO()):
            run(folder/'out/release/rom.bin',10400,folder/region,set(),[],skip_intro=False,ram_observer=observe,core=core,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        raw=json.dumps(events,separators=(',',':')).encode();(folder/(region+'-events.json')).write_bytes(raw)
        assert observed.get('done') and observed['cases']==clocked[0]==10260 and observed['bytes']==85500 and not observed['failures'],observed
        assert max(poll_gaps)<10260 and max(seed_gaps)<10260
        markers=[i for i,e in enumerate(events) if e[0]==3 and e[2]==85];assert len(markers)==10260
        for n,index in enumerate(markers):
            kind=n%3;phase=n//3;count=1 if kind==0 else 16 if kind==1 else 8;spacing=630 if kind==2 else 315
            writes=events[index+1:markers[n+1] if n+1<10260 else len(events)]
            assert len(writes)==count and all(e[0]==2 for e in writes) and [e[2] for e in writes]==[(i*13+n)&255 for i in range(count)]
            errors=[e[1]-origins[n]-10260-phase-i*spacing for i,e in enumerate(writes)]
            relative=[error-errors[0] for error in errors]
            assert all(0<=error<3420 for error in errors),(region,n,phase,errors)
            assert all(-49<=error<=14 for error in relative),(region,n,relative)
            rows.append(dict(kind=kind,phase=phase,errors_master=errors,relative_errors_master=relative))
        rows_raw=json.dumps(rows,separators=(',',':')).encode();(folder/(region+'-rows.json')).write_bytes(rows_raw)
        plain={}
        def observe_plain(frame,ram):
            done=int.from_bytes(bytes(ram[(((symbols['gaw_sweep_done']&65535)+i)&65535)^1] for i in range(2)),'big');plain.update(frame=frame,done=done)
            if done:plain['ram_sha256']=sha(bytes(ram))
        with contextlib.redirect_stdout(io.StringIO()):
            run(folder/'out/release/rom.bin',10400,folder/(region+'-plain'),set(),[],skip_intro=False,ram_observer=observe_plain,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(plain.get('done')))
        assert plain=={k:observed[k] for k in plain},(plain,observed)
        result=dict(region=region,**observed,plain_core_identical=True,poll_gap_master=[min(poll_gaps),max(poll_gaps)],seed_gap_master=[min(seed_gaps),max(seed_gaps)],
            first_errors_master=[min(r['errors_master'][0] for r in rows),max(r['errors_master'][0] for r in rows)],
            all_errors_master=[min(e for r in rows for e in r['errors_master']),max(e for r in rows for e in r['errors_master'])],
            relative_errors_master=[min(e for r in rows for e in r['relative_errors_master']),max(e for r in rows for e in r['relative_errors_master'])],
            events_sha256=sha(raw),rows_sha256=sha(rows_raw));results.append(result);print(result,flush=True)
    report=dict(kernel_sha256=sha((folder/'out/release/rom.bin').read_bytes()),observer_core_sha256=sha(core.read_bytes()),sources={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['source_md_psg_plan.c','source_md_psg_plan.h','source_md_psg_replay.s','source_md_psg_replay.h','source_md_psg_replay_seed.c']},results=results,
        limits=['Every physical deadline phase0..3419 at seedline100+3lines,three kinds(single,315x16,630x8),bothregions,alternating0/FFFF0000logicalepoch. All bytes and every final native clock independently checked against bus observations.',
                'Prepared producer before seed;masked IRQs/displayoff/noDMA. Frame marker onV90 determines exact physical epoch. Relative burst errors measured across bus refresh;not real hardware/fullgame/asyncproducer proof.'])
    (ROOT/'analysis/md_psg_beam_sweep_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
