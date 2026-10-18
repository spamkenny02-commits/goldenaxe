"""Native FIFO -> absolute H32 beam wait -> real PSG writes,including bursts."""
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

PROBE=r'''
#include <genesis.h>
#include "source_psg_queue.h"
#include "source_md_psg_wait.h"
#include "cases.h"
volatile u16 gaw_wait_done;
volatile u32 gaw_wait_failures,gaw_wait_groups,gaw_wait_bytes;
static SourcePsgQueue queue;
static SourcePsgEvent storage[8];
static u32 due[4];static u8 values[4];
int main(bool hard_reset) {
 u16 n,i,count,kind,phase;u32 period,base;
 SourcePsgEvent event;
 (void)hard_reset;
 SYS_disableInts();VDP_setScreenWidth256();VDP_setScreenHeight224();VDP_setEnable(FALSE);
 SYS_enableInts();SYS_doVBlankProcess();SYS_doVBlankProcess();SYS_doVBlankProcess();SYS_disableInts();
 period=(SYS_isPAL()?313UL:262UL)*3420;
 if(source_psg_queue_init(&queue,storage,8)) gaw_wait_failures++;
 queue.read=queue.write=65530;
 for(n=0;n<WAIT_CASES;n++) {
  kind=wait_cases[n][0];phase=wait_cases[n][1];count=kind==0?1:kind==1?2:4;
  base=0xffff0000UL+(u32)n*period+100UL*3420+phase;
  for(i=0;i<count;i++) {values[i]=wait_cases[n][2+i];due[i]=base+(u32)i*(kind==1?630:315);}
  if(source_psg_queue_push_bytes(&queue,values,due,count)) gaw_wait_failures++;
  /* Single consumer prefetches at logical due time. Physical IO is still
   * withheld until the assembly wait. No producer runs during this probe. */
  for(i=0;i<count;i++) {
   if(source_psg_queue_take(&queue,due[i],&event) || event.due!=due[i] || event.value!=values[i]) gaw_wait_failures++;
   values[i]=event.value;
  }
  if(queue.read!=queue.write) gaw_wait_failures++;
  while((*(volatile u16*)0xc00008>>8)!=90) {}
  *(volatile u16*)0xc00010=0x55;
  source_md_psg_wait_emit(100,phase,values,kind);
  gaw_wait_groups++;gaw_wait_bytes+=count;
 }
 gaw_wait_done=1;
 while(TRUE) {}
 return 0;
}
'''


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    folder=ROOT/'validation/md-psg-wait';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    oracle=ROOT/'analysis/loading-psg-v0203';manifest=json.loads((oracle/'manifest.json').read_text())
    fixture_name='validation/loading-psg-deadlines/inputs.json';fixture_raw=(oracle/fixture_name).read_bytes()
    assert sha(fixture_raw)==manifest['files'][fixture_name]
    fixture=json.loads(fixture_raw);dates_raw=(ROOT/'analysis/loading_psg_deadlines_report.json').read_bytes();dates=json.loads(dates_raw)
    # Every retained source frequency pair used below comes from one original
    # SMS reader invocation,with the independently captured630tick spacing.
    pairs=[]
    for source,row in zip(fixture,dates['results'][0]['rows']):
        assert (source['case'],source['irq'])==(row['case'],row['irq'])
        assert len(source['writes'])==len(row['source_psg_master'])
        for n,(a,b) in enumerate(zip(row['source_psg_master'],row['source_psg_master'][1:])):
            if b-a==630:pairs.append(source['writes'][n:n+2])
    assert pairs
    phases=range(3420);cases=[]
    for phase in phases:
        pair=pairs[len(cases)%len(pairs)]
        cases.extend([[0,phase,pair[0],0,0,0],[1,phase,*pair,0,0],[2,phase,0x9f,0xbf,0xdf,0xff]])
    (src/'cases.h').write_text('#define WAIT_CASES '+str(len(cases))+'\nstatic const u16 wait_cases[WAIT_CASES][6]={\n'+',\n'.join('{'+','.join(map(str,row))+'}' for row in cases)+'\n};\n')
    (src/'main.c').write_text(PROBE)
    for name in ['source_psg_queue.h','source_md_psg_wait.h']:(src/name).write_text('#include "../../../megadrive/src/'+name+'"\n')
    (src/'source_psg_queue.c').write_text('#include "../../../megadrive/src/source_psg_queue.c"\n')
    (src/'source_md_psg_wait.s').write_bytes((ROOT/'megadrive/src/source_md_psg_wait.s').read_bytes())
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH']
    temporary=folder/'compiler-tmp';temporary.mkdir(exist_ok=True)
    for key in ['TMPDIR','TMP','TEMP']:env[key]=temporary.resolve().as_posix()
    path=sdk.as_posix();unix='/'+path[0].lower()+path[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True)
    (folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2000:]
    symbols={m[2]:int(m[1],16)&65535 for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_io_libretro.dll';dll=c.CDLL(str(core))
    dll.gaw_io_reset.argtypes=[c.c_uint];dll.gaw_io_reset.restype=None
    dll.gaw_io_size.restype=dll.gaw_io_errors.restype=c.c_uint;dll.gaw_io_data.restype=c.POINTER(c.c_uint)
    results=[]
    for region,lines in [('ntsc',262),('pal',313)]:
        period=lines*3420;events=[];observed={};dll.gaw_io_reset(0)
        recent=[];detail=[];group_index=[-1]
        def observe(frame,ram):
            count=dll.gaw_io_size();assert not dll.gaw_io_errors();ptr=dll.gaw_io_data()
            for index in range(count):
                if ptr[index*4]==1 and (group_index[0]<0 or cases[group_index[0]][0]!=0 or cases[group_index[0]][1] not in [0,19,250,260,300,760,3419]):continue
                record=[int(ptr[index*4]),(frame-1)*period+int(ptr[index*4+1]),int(ptr[index*4+2]),int(ptr[index*4+3])]
                if record[0]==1:recent.append(record);recent[:]=recent[-16:]
                if record[0]==3 and record[2]==0x55:group_index[0]+=1
                if record[0]==2 and group_index[0]>=0 and cases[group_index[0]][0]==0 and cases[group_index[0]][1] in [0,19,250,260,300,760,3419]:
                    detail.append(dict(case=cases[group_index[0]],write=record,reads=list(recent)))
            # Keep actual writes only; reads are diagnostic traffic that would
            # otherwise dwarf the evidence. IO hooks still observe every read.
            events.extend([[int(ptr[n*4]),(frame-1)*period+int(ptr[n*4+1]),int(ptr[n*4+2]),int(ptr[n*4+3])] for n in range(count) if ptr[n*4]!=1])
            dll.gaw_io_reset(1)
            def value(name,width):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(width)),'big')
            observed.update(frame=frame,done=value('gaw_wait_done',2),failures=value('gaw_wait_failures',4),groups=value('gaw_wait_groups',4),bytes=value('gaw_wait_bytes',4))
            if observed['done']:observed['ram_sha256']=sha(bytes(ram))
        with contextlib.redirect_stdout(io.StringIO()):
            run(folder/'out/release/rom.bin',len(cases)+100,folder/region,set(),[],skip_intro=False,ram_observer=observe,core=core,
                core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        (folder/(region+'-events.json')).write_text(json.dumps(events,separators=(',',':')))
        (folder/(region+'-detail.json')).write_text(json.dumps(detail,indent=2))
        assert observed.get('done') and not observed['failures'] and observed['groups']==len(cases),observed
        # Marker is emitted on physical line90 before each requested line100.
        markers=[n for n,e in enumerate(events) if e[0]==3 and e[2]==0x55]
        assert len(markers)==len(cases),(region,len(markers),observed)
        rows=[];previous=None
        for n,(index,case) in enumerate(zip(markers,cases)):
            kind,phase,*values=case;count=1 if kind==0 else 2 if kind==1 else 4
            marker=events[index];assert (marker[1]//3420+224)%lines==90
            target=(marker[1]//3420+10)*3420+phase
            if previous is not None:assert target-phase-previous==period,(region,n,'missed frame')
            previous=target-phase
            writes=events[index+1:markers[n+1] if n+1<len(markers) else len(events)]
            assert len(writes)==count and all(e[0]==2 for e in writes),(region,n,writes)
            assert [e[2] for e in writes]==values[:count]
            spacing=630 if kind==1 else 315
            errors=[e[1]-target-i*spacing for i,e in enumerate(writes)]
            assert 0<=errors[0]<1000,(region,n,phase,errors)
            relative=[e[1]-writes[0][1]-i*spacing for i,e in enumerate(writes)]
            assert all(-14<=error<=7 for error in relative)
            rows.append(dict(kind=kind,phase=phase,target=target,errors_master=errors,relative_errors_master=[e[1]-writes[0][1]-i*spacing for i,e in enumerate(writes)]))
        plain={}
        def observe_plain(frame,ram):
            done=int.from_bytes(bytes(ram[(symbols['gaw_wait_done']+i)^1] for i in range(2)),'big');plain.update(frame=frame,done=done)
            if done:plain['ram_sha256']=sha(bytes(ram))
        with contextlib.redirect_stdout(io.StringIO()):
            run(folder/'out/release/rom.bin',len(cases)+100,folder/(region+'-plain'),set(),[],skip_intro=False,ram_observer=observe_plain,
                core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(plain.get('done')))
        assert plain=={key:observed[key] for key in plain},(plain,observed)
        rows_raw=json.dumps(rows,separators=(',',':')).encode();(folder/(region+'-rows.json')).write_bytes(rows_raw)
        result=dict(region=region,**observed,plain_core_identical=True,first_error_master=[min(r['errors_master'][0] for r in rows),max(r['errors_master'][0] for r in rows)],
            all_error_master=[min(e for r in rows for e in r['errors_master']),max(e for r in rows for e in r['errors_master'])],rows_sha256=sha(rows_raw),
            relative_error_master=[min(e for r in rows for e in r['relative_errors_master']),max(e for r in rows for e in r['relative_errors_master'])],
            worst_rows=sorted(rows,key=lambda r:r['errors_master'][0],reverse=True)[:8],
            by_kind=[dict(kind=kind,groups=sum(row['kind']==kind for row in rows),first_error_master=[min(row['errors_master'][0] for row in rows if row['kind']==kind),max(row['errors_master'][0] for row in rows if row['kind']==kind)]) for kind in range(3)])
        results.append(result);print(region,{k:v for k,v in result.items() if k!='rows'},flush=True)
    report=dict(kernel_sha256=sha((folder/'out/release/rom.bin').read_bytes()),observer_core_sha256=sha(core.read_bytes()),fixture_sha256=sha(fixture_raw),source_dates_sha256=sha(dates_raw),
        sources={name:sha((ROOT/'megadrive/src'/name).read_bytes()) for name in ['source_md_psg_wait.s','source_md_psg_wait.h','source_psg_queue.c','source_psg_queue.h']},results=results,
        limits=['Real queued bytes are prefetched at logical due time; actual writes wait for physical line100 and the requested horizontal phase. FIFO cursor/u32 due wrap included. Single blocked producer/consumer; no pressure or reader execution during output.',
                'Fixed line100 is unambiguous in both regions. Every master-tick phase0..3419 and three output kinds; one group per frame,marker verified on physical line90 and no skipped frames.',
                'Source630tick frequency pairs use retained original SMS bytes/dates. Four-byte315tick mute bursts are synthetic bus cadence cases. This is not a full original audio stream replay.',
                'Interrupts/display disabled; first-write poll/IO latency is additional to source deadlines. Not integrated into playable ROM,global epoch,full graphics load,or real hardware.'])
    (ROOT/'analysis/md_psg_wait_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
