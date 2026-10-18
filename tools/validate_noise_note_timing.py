"""Original8679 per-byte time vs native timed event, host and68000."""
import contextlib
import ctypes as c
import hashlib
import io
import json
import os
import re
import struct
import subprocess
from actor_reference import ROOT
from audio_noise_note_cost import noise_note_cost
from run_core import run
from validate_audio_noise_note import setup
from validate_native_audio_prefix import Work

class Event(c.Structure):_fields_=[('due',c.c_uint32),('value',c.c_uint8)]

def main():
    rows,_,fixture=setup();base=ROOT/'validation/noise-note-timing';base.mkdir(exist_ok=True)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    modules=['source_audio_timed','source_audio_sequence','source_audio_priority','source_audio_memory','source_psg_queue']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src')]+[str(ROOT/'megadrive/src'/(name+'.c')) for name in modules]+['-o',str(base/'timed.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True);assert not built.returncode,built.stderr
    native=c.CDLL(str(base/'timed.dll'));fn=native.source_audio_noise_note_timed
    fn.argtypes=[c.POINTER(c.c_uint8),c.c_uint16,c.c_uint8,c.c_uint32,c.POINTER(Work),c.POINTER(Event),c.POINTER(c.c_uint8)];fn.restype=c.c_uint8
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_noiseports_libretro.dll';dll=c.CDLL(str(core))
    for name in ['gaw_port_samples','gaw_port_write_samples']:getattr(dll,name).restype=c.c_uint
    for name in ['gaw_port_call_data','gaw_port_write_data']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
    results=[];expected=None
    for region in ['auto','pal']:
        dll.gaw_timing_reset();done=[]
        def observe(frame,ram):
            if ram[4]:done.append(frame)
        with contextlib.redirect_stdout(io.StringIO()):
            run(fixture,40000,base/region,set(),[],skip_intro=False,core=core,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(done))
        assert done and dll.gaw_port_samples()==len(rows) and dll.gaw_port_write_samples()<32768
        calls=c.string_at(dll.gaw_port_call_data(),len(rows)*824);ports=c.string_at(dll.gaw_port_write_data(),dll.gaw_port_write_samples()*16)
        (base/(region+'-calls.bin')).write_bytes(calls);(base/(region+'-ports.bin')).write_bytes(ports)
        grouped=[[] for _ in rows]
        for pos in range(0,len(ports),16):
            time,index,value=struct.unpack_from('<QII',ports,pos);grouped[index].append((time,value))
        cases=[]
        for n,row in enumerate(rows):
            begin,end,de_before,de_after=struct.unpack_from('<2Q2I',calls,n*824)
            before=calls[n*824+24:n*824+424];after=calls[n*824+424:n*824+824]
            model=noise_note_cost(before,row[0]);writes=grouped[n];assert len(writes)<=1
            assert model['state']==after and model['tstates']*15==end-begin and de_before==de_after
            state=(c.c_uint8*400).from_buffer_copy(before);work=Work();event=Event(0x12345678,0x5a);has=c.c_uint8(255);epoch=(0xffff0000+n*225)&0xffffffff
            assert fn(state,0xd0,row[0],epoch,c.byref(work),c.byref(event),c.byref(has))
            assert bytes(state)==after and work.tstates==model['tstates'] and has.value==len(writes)
            if writes:
                time,value=writes[0];assert begin<=time<=end
                assert (event.due,event.value)==((epoch+time-begin)&0xffffffff,value),(region,n,'PSG time',event.due,(epoch+time-begin)&0xffffffff)
                relative=time-begin
            else:
                assert (event.due,event.value)==(0x12345678,0x5a);relative=0;value=0
            patches=[after[i] for i in [0x13,0xd0,0xd7,0xd8]];reconstructed=bytearray(before)
            for i,v in zip([0x13,0xd0,0xd7,0xd8],patches):reconstructed[i]=v
            assert reconstructed==after
            cases.append(dict(input=list(row),patches=patches,tstates=work.tstates,relative_master=relative,has=len(writes),value=value))
        if expected is None:expected=cases
        else:assert expected==cases
        results.append(dict(region=region,cases=len(rows),frames=done[0],psg_writes=len(ports)//16,calls_sha256=hashlib.sha256(calls).hexdigest(),ports_sha256=hashlib.sha256(ports).hexdigest()))
        print(region,len(rows),'original8679 state/work/event times pass;',len(ports)//16,'writes',flush=True)
    # Invalid arguments and offset: no event publication or semantic mutation.
    state=(c.c_uint8*400)(*([0xa7]*400));original=bytes(state)
    for missing in ['state','work','event','has','offset']:
        work=Work(123,456);event=Event(0x12345678,0x5a);has=c.c_uint8(255)
        assert not fn(None if missing=='state' else state,353 if missing=='offset' else 0xd0,1,0,None if missing=='work' else c.byref(work),None if missing=='event' else c.byref(event),None if missing=='has' else c.byref(has))
        assert bytes(state)==original and (event.due,event.value)==(0x12345678,0x5a)
        if missing!='work':assert not work.tstates and not work.fetches
        if missing!='has':assert has.value==0
    (base/'cases.json').write_text(json.dumps(expected,separators=(',',':'))+'\n')
    compiled=compiled_check(base,expected,fixture,modules,sdk,env)
    report=dict(source_regions=results,compiled_regions=compiled,invalid_host_cases=5,kernel_sha256=hashlib.sha256((base/'kernel/out/release/rom.bin').read_bytes()).hexdigest(),queue_roundtrip=True,source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),sources={name:hashlib.sha256((ROOT/'megadrive/src'/(name+'.c')).read_bytes()).hexdigest() for name in modules},limits=['Isolated original8679,all256 selectors,flags0/4/128/132,global volume0/15/255 and noise offset0/3/255. Original bank6 unchanged; DI custom caller seeds400 RAM bytes. Actual PSG handler cycles/data,all400 bytes and complete helper work compared.','Timestamp is source-entry plus(helperT-10)*15 because both writing exits consist of OUT followed by a10T RET. Muted paths leave event untouched. Compiled queue roundtrip checks FULL,early WAIT and release exactly at supplied logical time. No timed whole8000 reader,physical clock/pacing,waveform or full-game proof.'])
    (ROOT/'analysis/noise_note_timing_report.json').write_text(json.dumps(report,indent=2)+'\n')

def compiled_check(base,cases,fixture,modules,sdk,env):
    kernel=base/'kernel';src=kernel/'src';src.mkdir(parents=True,exist_ok=True)
    seed=fixture.read_bytes()[0x3430:0x3430+400]
    header=['static const u8 seed[400]={'+','.join(map(str,seed))+'};','typedef struct {u8 input[4],patches[4],has,value;u32 tstates,relative;} TimedCase;','static const TimedCase cases[]={']
    for case in cases:header.append('{{'+','.join(map(str,case['input']))+'},{'+','.join(map(str,case['patches']))+'},'+str(case['has'])+','+str(case['value'])+','+str(case['tstates'])+'UL,'+str(case['relative_master'])+'UL},')
    header.append('};');(src/'expected.h').write_text('\n'.join(header)+'\n')
    for name in modules:(src/(name+'.c')).write_text('#include "../../../../megadrive/src/'+name+'.c"\n')
    (src/'main.c').write_text('''#include <genesis.h>
#include "../../../../megadrive/src/source_audio_timed.h"
#include "expected.h"
volatile u32 gaw_timed_cases,gaw_timed_failures,gaw_timed_queued;volatile u16 gaw_timed_done;
int main(bool hard_reset)
{
 u16 row,n;u8 state[400],expected[400],has;SourceClockWork work;SourcePsgEvent event,storage[1],delivered;SourcePsgQueue queue;u32 epoch;VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  for(n=0;n<400;n++) state[n]=seed[n];
  state[0x3e]=cases[row].input[0];state[0xd0]=cases[row].input[1];state[0x18]=cases[row].input[2];state[0x17]=cases[row].input[3];
  for(n=0;n<400;n++) expected[n]=state[n];
  expected[0x13]=cases[row].patches[0];expected[0xd0]=cases[row].patches[1];expected[0xd7]=cases[row].patches[2];expected[0xd8]=cases[row].patches[3];
  epoch=0xffff0000UL+(u32)row*225;event.due=0x12345678;event.value=0x5a;has=255;
  if(!source_audio_noise_note_timed(state,0xd0,cases[row].input[0],epoch,&work,&event,&has)) gaw_timed_failures++;
  if(work.tstates!=cases[row].tstates || has!=cases[row].has) gaw_timed_failures++;
  if(has) {if(event.due!=epoch+cases[row].relative || event.value!=cases[row].value) gaw_timed_failures++;}
  else if(event.due!=0x12345678 || event.value!=0x5a) gaw_timed_failures++;
  if(source_psg_queue_init(&queue,storage,1)!=SOURCE_PSG_QUEUE_OK) gaw_timed_failures++;
  if(has)
  {
   if(source_psg_queue_push(&queue,&event,1)!=SOURCE_PSG_QUEUE_OK) gaw_timed_failures++;
   if(source_psg_queue_push(&queue,&event,1)!=SOURCE_PSG_QUEUE_FULL) gaw_timed_failures++;
   delivered.due=0x12345678;delivered.value=0x5a;
   if(source_psg_queue_take(&queue,event.due-1,&delivered)!=SOURCE_PSG_QUEUE_WAIT || delivered.due!=0x12345678 || delivered.value!=0x5a) gaw_timed_failures++;
   if(source_psg_queue_take(&queue,event.due,&delivered)!=SOURCE_PSG_QUEUE_OK || delivered.due!=event.due || delivered.value!=event.value) gaw_timed_failures++;
   gaw_timed_queued++;
  }
  if(source_psg_queue_take(&queue,epoch,&delivered)!=SOURCE_PSG_QUEUE_EMPTY) gaw_timed_failures++;
  for(n=0;n<400;n++) if(state[n]!=expected[n]) gaw_timed_failures++;
  gaw_timed_cases++;
 }
 gaw_timed_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
''')
    path=str(sdk).replace('\\','/');unix='/'+path[0].lower()+path[2:];env=dict(env);env['PATH']=str(sdk/'bin')+';'+env['PATH']
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=kernel,env=env,capture_output=True,text=True)
    (kernel/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2000:]
    sy={m[2]:int(m[1],16)&65535 for line in (kernel/'out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};results=[]
    for region in ['auto','pal']:
        result={}
        def observe(frame,ram):
            def value(name,width):return int.from_bytes(bytes(ram[(sy[name]+i)^1] for i in range(width)),'big')
            result.update(frame=frame,done=value('gaw_timed_done',2),cases=value('gaw_timed_cases',4),queued=value('gaw_timed_queued',4),failures=value('gaw_timed_failures',4))
        with contextlib.redirect_stdout(io.StringIO()):run(kernel/'out/release/rom.bin',20000,kernel/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(result.get('done')))
        assert result.get('done') and result['cases']==len(cases) and not result['failures'],(region,result)
        assert result['queued']==sum(case['has'] for case in cases)
        results.append(dict(region=region,**result));print('68000',results[-1],flush=True)
    return results

if __name__=='__main__':main()
