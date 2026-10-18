"""Measure H32 HV reads and real byte/word PSG port writes on native 68000."""
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
#include "source_md_hclock.h"
volatile u16 gaw_io_done;
volatile u32 gaw_io_samples,gaw_io_failures;
volatile u32 gaw_io_clock[8192];
static SourceMdHClock clock_state;
static const u8 burst_bytes[4]={0x9f,0xbf,0xdf,0xff};
extern void gaw_burst315(const u8 *bytes);
extern void gaw_burst630(const u8 *bytes);
int main(bool hard_reset) {
 u16 n,hv;
 (void)hard_reset;
 SYS_disableInts();VDP_setScreenWidth256();VDP_setScreenHeight224();VDP_setEnable(FALSE);
 SYS_enableInts();SYS_doVBlankProcess();SYS_doVBlankProcess();SYS_doVBlankProcess();
 SYS_disableInts();
 /* VC100 is unambiguous in both regions. VC224 is duplicated during PAL
  * blanking and cannot establish a physical line without an epoch. */
 while((*(volatile u16*)0xc00008>>8)!=100) {}
 for(n=0;n<8192;n++) {
  hv=*(volatile u16*)0xc00008;
  if(n==0) {
   if(source_md_hclock_seed(&clock_state,SYS_isPAL(),hv>>8,hv,0xffff0000UL)) gaw_io_failures++;
  } else if(source_md_hclock_sample(&clock_state,hv)) gaw_io_failures++;
  gaw_io_clock[n]=clock_state.master;
  *(volatile u8*)0xc00011=(u8)hv;
  *(volatile u16*)0xc00010=hv>>8;
  gaw_io_samples++;
 }
 for(n=0;n<512;n++) {gaw_burst315(burst_bytes);gaw_burst630(burst_bytes);}
 gaw_io_done=1;
 while(TRUE) {}
 return 0;
}
'''

BURSTS=r'''
    .text
    .align 2
    .global gaw_burst315
gaw_burst315:
    move.l 4(%sp),%a0
    move.l #0xc00011,%a1
    move.b (%a0)+,(%a1)
    .rept 8
    nop
    .endr
    move.b (%a0)+,(%a1)
    .rept 8
    nop
    .endr
    move.b (%a0)+,(%a1)
    .rept 8
    nop
    .endr
    move.b (%a0)+,(%a1)
    rts
    .align 2
    .global gaw_burst630
gaw_burst630:
    move.l 4(%sp),%a0
    move.l #0xc00011,%a1
    move.b (%a0)+,(%a1)
    .rept 19
    nop
    .endr
    move.b (%a0)+,(%a1)
    rts
'''


def sha(raw):return hashlib.sha256(raw).hexdigest()


def host_clock(folder,sdk):
    env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    source=ROOT/'megadrive/src/source_md_hclock.c';target=folder/'host-clock.dll'
    built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),str(source),'-o',str(target)],env=env,capture_output=True,text=True)
    (folder/'host-build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
    class Clock(c.Structure):_fields_=[('master',c.c_uint32),('phase',c.c_uint32),('lines',c.c_uint16)]
    dll=c.CDLL(str(target));seed=dll.source_md_hclock_seed;sample=dll.source_md_hclock_sample
    seed.argtypes=[c.POINTER(Clock),c.c_uint8,c.c_uint16,c.c_uint16,c.c_uint32];seed.restype=c.c_uint8
    sample.argtypes=[c.POINTER(Clock),c.c_uint16];sample.restype=c.c_uint8
    checks=0
    def hv_at(ticks,lines):
        line=(ticks//3420)%lines;v=line if line<=(258 if lines==313 else 234) else line-lines
        h=(ticks%3420)//20+133;h=h-171 if h>=171 else h+85 if h>=148 else h
        return (v&255)<<8|h
    for pal,lines in [(0,262),(1,313)]:
        period=lines*3420;bound=(lines-256)*3420
        for phase in range(0,period,20):
            clock=Clock();assert seed(c.byref(clock),pal,phase//3420,hv_at(phase,lines),0xffff0000)==0
            assert clock.phase==phase and clock.master==(0xffff0000+phase)&0xffffffff;checks+=1
            for gap in [0,1,19,20,3419,3420,17100,bound-21]:
                copy=Clock.from_buffer_copy(clock)
                assert sample(c.byref(copy),hv_at(phase+gap,lines))==0
                expected=(phase+gap)//20*20
                assert copy.phase==expected%period and copy.master==(0xffff0000+expected)&0xffffffff,(pal,phase,gap,copy.master,expected)
                checks+=1
        # Impossible H codes,corrupt state,unsupported seed and plausible but
        # out-of-window forward samples must leave the object bytewise intact.
        clock=Clock();assert seed(c.byref(clock),pal,100,hv_at(342000,lines),0)==0
        for h in range(148,233):
            before=bytes(clock);assert sample(c.byref(clock),100<<8|h)==1 and bytes(clock)==before;checks+=1
        before=bytes(clock);assert sample(c.byref(clock),hv_at(342000+bound+40,lines))==2 and bytes(clock)==before;checks+=1
        for bad_pal,bad_line,bad_hv in [(2,100,hv_at(342000,lines)),(pal,lines,0),(pal,100,0)]:
            before=bytes(clock);assert seed(c.byref(clock),bad_pal,bad_line,bad_hv,0)==1 and bytes(clock)==before;checks+=1
    assert seed(None,0,0,0x85,0)==1 and sample(None,0)==1;checks+=2
    print('Host clock checks',checks,flush=True)
    return dict(checks=checks)


def main():
    folder=ROOT/'validation/md-io-clock';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    (src/'main.c').write_text(PROBE)
    (src/'bursts.s').write_text(BURSTS)
    (src/'source_md_hclock.h').write_text('#include "../../../megadrive/src/source_md_hclock.h"\n')
    (src/'source_md_hclock.c').write_text('#include "../../../megadrive/src/source_md_hclock.c"\n')
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH']
    host=host_clock(folder,sdk)
    temporary=folder/'compiler-tmp';temporary.mkdir(exist_ok=True)
    for key in ['TMPDIR','TMP','TEMP']:env[key]=temporary.resolve().as_posix()
    path=sdk.as_posix();unix='/'+path[0].lower()+path[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True)
    (folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2000:]
    symbols={m[2]:int(m[1],16)&65535 for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_io_libretro.dll';dll=c.CDLL(str(core))
    dll.gaw_io_reset.argtypes=[c.c_uint];dll.gaw_io_reset.restype=None
    dll.gaw_io_size.restype=dll.gaw_io_errors.restype=c.c_uint;dll.gaw_io_data.restype=c.POINTER(c.c_uint)
    # Derive every H32 tick interval from the authoritative local core table.
    table_raw=(ROOT.parents[1]/'work/genesis-plus-gx/core/hvc.h').read_bytes()
    text=table_raw.decode().split('static const uint8 cycle2hc32[3420] =')[1].split('};')[0]
    table=[int(x,16) for x in re.findall(r'0x([0-9a-fA-F]+)',text)];assert len(table)==3420
    assert all(table[t]==((t//20+133) if t//20+133<148 else (t//20+133+85) if t//20+133<171 else (t//20+133-171)) for t in range(3420))
    results=[]
    for region,lines in [('ntsc',262),('pal',313)]:
        period=lines*3420;events=[];observed={};dll.gaw_io_reset(0)
        def observe(frame,ram):
            count=dll.gaw_io_size();assert not dll.gaw_io_errors()
            ptr=dll.gaw_io_data()
            events.extend([[int(ptr[n*4]),(frame-1)*period+int(ptr[n*4+1]),int(ptr[n*4+2]),int(ptr[n*4+3])] for n in range(count)])
            dll.gaw_io_reset(1)
            def value(name,width):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(width)),'big')
            observed.update(frame=frame,done=value('gaw_io_done',2),samples=value('gaw_io_samples',4),failures=value('gaw_io_failures',4))
            if observed['done']:
                clock_values[:]=[int.from_bytes(bytes(ram[((symbols['gaw_io_clock']+n*4+i)&65535)^1] for i in range(4)),'big') for n in range(8192)]
                observed['ram_sha256']=sha(bytes(ram))
        clock_values=[]
        with contextlib.redirect_stdout(io.StringIO()):
            run(folder/'out/release/rom.bin',100,folder/region,set(),[],skip_intro=False,ram_observer=observe,core=core,
                core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        (folder/(region+'-diagnostic.json')).write_text(json.dumps(dict(observed=observed,events=events,clock=clock_values),separators=(',',':')))
        assert observed.get('done') and observed['samples']==8192 and not observed['failures'],observed
        plain={}
        def observe_plain(frame,ram):
            done=int.from_bytes(bytes(ram[(symbols['gaw_io_done']+i)^1] for i in range(2)),'big')
            plain.update(frame=frame,done=done)
            if done:plain['ram_sha256']=sha(bytes(ram))
        with contextlib.redirect_stdout(io.StringIO()):
            run(folder/'out/release/rom.bin',100,folder/(region+'-plain'),set(),[],skip_intro=False,ram_observer=observe_plain,
                core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(plain.get('done')))
        assert plain=={key:observed[key] for key in plain},(plain,observed)
        # Boot/SGDK reads can precede the probe. Each probe HV read is followed
        # by exactly one byte and one word write of its low/high result.
        triples=[]
        for n in range(len(events)-2):
            a,b,d=events[n:n+3]
            if a[0]==1 and b[0]==2 and d[0]==3:
                assert b[2]==(a[2]&255) and d[2]==a[2]>>8
                triples.append((a,b,d))
        assert len(triples)==8192,len(triples)
        last_clock_write=triples[-1][2]
        burst_events=[event for event in events if event[1]>last_clock_write[1]]
        assert len(burst_events)==512*6 and all(event[0]==2 for event in burst_events)
        burst_errors={315:[],630:[]};burst_intervals={315:set(),630:set()}
        for n in range(512):
            group=burst_events[n*6:n*6+6]
            assert [e[2] for e in group]==[0x9f,0xbf,0xdf,0xff,0x9f,0xbf]
            for target,part in [(315,group[:4]),(630,group[4:])]:
                for index,event in enumerate(part):burst_errors[target].append(event[1]-part[0][1]-index*target)
                burst_intervals[target].update(b[1]-a[1] for a,b in zip(part,part[1:]))
        # The core models a14-master-tick 68000 bus refresh penalty. It must
        # remain enabled: nominal instruction sums alone are not delivery proof.
        assert burst_intervals[315]=={308,322} and burst_intervals[630]=={616,630},burst_intervals
        assert all(abs(error)<=21 for error in burst_errors[315])
        assert all(abs(error)<=14 for error in burst_errors[630])
        quantization=[];byte_latency=[];word_latency=[];v_seen=set()
        first_master=triples[0][0][1];first_line=(first_master//3420+224)%lines
        assert first_line==100,first_line
        origin=(0xffff0000+first_line*3420+(first_master%3420)//20*20)&0xffffffff
        for index,(a,b,d) in enumerate(triples):
            kind,master,hv,pc=a
            phase=master%3420;assert (hv&255)==table[phase],(region,master,hv,phase)
            ordinal=(hv&255)-85 if (hv&255)>=233 else hv&255
            decoded=((ordinal-133)%171)*20
            error=phase-decoded;assert 0<=error<20
            physical_line=(master//3420+224)%lines
            vc=physical_line if physical_line<=(258 if region=='pal' else 234) else physical_line-lines
            assert hv>>8==vc&255,(region,master,hv,physical_line)
            expected=(origin+master//20*20-first_master//20*20)&0xffffffff
            assert clock_values[index]==expected,(region,index,clock_values[index],expected)
            quantization.append(error);byte_latency.append(b[1]-master);word_latency.append(d[1]-master)
            v_seen.add(hv>>8)
            assert master<b[1]<d[1]
        raw=json.dumps(events,separators=(',',':')).encode();(folder/(region+'-events.json')).write_bytes(raw)
        results.append(dict(region=region,**observed,plain_core_identical=True,events=len(events),probe_reads=len(triples),quantization_master=[min(quantization),max(quantization)],
            byte_write_latency_master=sorted(set(byte_latency)),word_write_latency_master=sorted(set(word_latency)),
            burst_writes=len(burst_events),burst_intervals_master={k:sorted(v) for k,v in burst_intervals.items()},
            burst_relative_error_master={k:[min(v),max(v)] for k,v in burst_errors.items()},
            vertical_values=sorted(v_seen),events_sha256=sha(raw)))
        print(region,results[-1],flush=True)
    report=dict(host=host,kernel_sha256=sha((folder/'out/release/rom.bin').read_bytes()),observer_core_sha256=sha(core.read_bytes()),hvc_table_sha256=sha(table_raw),
        clock_sources={name:sha((ROOT/'megadrive/src'/name).read_bytes()) for name in ['source_md_hclock.c','source_md_hclock.h']},results=results,
        limits=['Actual emulated H32 bus reads and byte/word PSG writes,8192 samples per physical region. Observer never changes CPU state or cycles. HV read result independently echoed through both bus widths.',
                'Native clock values match every physical sample across horizontal/vertical wraps and uint32 rollover. Explicit first-line seed is checked against core physical position. Reads are frequent enough to resolve duplicated V values; this clock cannot detect all undersampling failures.',
                'Horizontal decode is quantized to20 master ticks; line starts atHC85,93->E9 discontinuity. The explicit seed is not an automatic boot epoch.',
                '512 four-byte315-tick and512 two-byte630-tick assembly burst candidates per region have relative errors at most21/14master ticks from the first port write. Only two fixed spacings; the first-write deadline/absolute phase is not established. Candidates remain in the diagnostic,not the playable ROM.',
                'Interrupts/display disabled during the measured loop. Not queued audio deadline pacing,real hardware verification,or full-game fidelity.'])
    (ROOT/'analysis/md_io_clock_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
