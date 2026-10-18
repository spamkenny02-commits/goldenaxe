"""Original854B envelope port timestamps, including caller-unwind exits."""
import contextlib
import ctypes as c
import gzip
import hashlib
import io
import json
import os
import re
import struct
import subprocess
from actor_reference import ROOT
from audio_envelope_refresh import adsr_refresh,table_envelope_refresh
from run_core import run
from validate_audio_envelope_refresh import fixtures
from validate_audio_prefix_cost import generate,SOURCE
from validate_native_audio_envelope import FIELDS,Output,make_cases
from validate_native_audio_prefix import Work

class Event(c.Structure):_fields_=[('due',c.c_uint32),('value',c.c_uint8)]
MODULES=['source_audio_timed','source_audio_envelope','source_audio_sequence','source_audio_priority','source_audio_memory','source_psg_queue']

def check_boundaries(fn,low,bank):
    for missing in ['state','low','bank','de','work','output','event','offset']:
        state=(c.c_uint8*400)(*([0xa7]*400));before=bytes(state);de=c.c_uint16(0x8a0b);work=Work(123,456);out=Output(1,2,3,4);event=Event(0x12345678,0x5a)
        assert not fn(None if missing=='state' else state,353 if missing=='offset' else 0x40,None if missing=='low' else low,32768,None if missing=='bank' else bank,None if missing=='de' else c.byref(de),0,None if missing=='work' else c.byref(work),None if missing=='output' else c.byref(out),None if missing=='event' else c.byref(event))
        assert bytes(state)==before and de.value==0x8a0b and (event.due,event.value)==(0x12345678,0x5a)
        if missing!='work':assert not work.tstates and not work.fetches
        if missing!='output':assert (out.accumulator,out.unwind,out.write,out.psg)==(0,0,0,0)
    return 8

def main():
    base=ROOT/'validation/envelope-timing';base.mkdir(exist_ok=True)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src')]+[str(ROOT/'megadrive/src'/(name+'.c')) for name in MODULES]+['-o',str(base/'timed.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True);assert not built.returncode,built.stderr
    native=c.CDLL(str(base/'timed.dll'));fn=native.source_audio_envelope_timed
    fn.argtypes=[c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.POINTER(c.c_uint16),c.c_uint32,c.POINTER(Work),c.POINTER(Output),c.POINTER(Event)];fn.restype=c.c_uint8
    low=(c.c_uint8*32768).from_buffer_copy(SOURCE[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(SOURCE[0x18000:0x1c000])
    boundary_cases=check_boundaries(fn,low,bank)
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_envelopeports_libretro.dll';dll=c.CDLL(str(core))
    for name in ['gaw_port_samples','gaw_port_write_samples']:getattr(dll,name).restype=c.c_uint
    for name in ['gaw_port_call_data','gaw_port_write_data']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
    dll.gaw_port_meta_data.restype=c.POINTER(c.c_uint32)
    results=[]
    for table in [False,True]:
        kind='table' if table else 'adsr';records,offsets=fixtures(table)
        fixture,_=generate(kind,records,offsets,0x854b,'envelope-timing-source',0xde40,True,0xde3e)
        image=bytearray(fixture.read_bytes());start=image.find(bytes.fromhex('0603dbbfe680'),0x3100,0x3430)
        assert start>=0 and image[start+9]==5 and image[start+10]==0xc2
        image[start:start+13]=bytes(13);fixture.write_bytes(image)
        assert image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000]
        first_cases=None
        for region in ['auto','pal']:
            dll.gaw_timing_reset();done=[]
            def observe(frame,ram):
                if ram[4]:done.append(frame)
            with contextlib.redirect_stdout(io.StringIO()):run(fixture,len(records)*4+100,base/(kind+'-'+region),set(),[],skip_intro=False,core=core,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(done))
            assert done and dll.gaw_port_samples()==len(records) and dll.gaw_port_write_samples()<32768
            calls=c.string_at(dll.gaw_port_call_data(),len(records)*824);ports=c.string_at(dll.gaw_port_write_data(),dll.gaw_port_write_samples()*16);meta=dll.gaw_port_meta_data()
            hashes={}
            for name,raw in [('calls',calls),('ports',ports),('meta',c.string_at(meta,len(records)*8))]:
                packed=gzip.compress(raw,mtime=0);assert gzip.decompress(packed)==raw
                (base/(kind+'-'+region+'-'+name+'.bin.gz')).write_bytes(packed);hashes[name]=hashlib.sha256(raw).hexdigest()
            grouped=[[] for _ in records]
            for pos in range(0,len(ports),16):
                time,index,value=struct.unpack_from('<QII',ports,pos);grouped[index].append((time,value))
            cases=[];unwinds=0
            for n in range(len(records)):
                begin,end,de_before,de_after=struct.unpack_from('<2Q2I',calls,n*824)
                before=calls[n*824+24:n*824+424];after=calls[n*824+424:n*824+824]
                prediction=table_envelope_refresh(SOURCE,before,de=de_before) if table else adsr_refresh(before,de=de_before)
                assert prediction['state']==after and prediction['tstates']*15==end-begin and prediction['de']==de_after,(kind,region,n,'source state/work/DE')
                assert (meta[n*2],bool(meta[n*2+1]))==(prediction['accumulator'],bool(prediction.get('unwind',False))),(kind,region,n,'source A/unwind')
                state=(c.c_uint8*400).from_buffer_copy(before);de=c.c_uint16(de_before);work=Work();out=Output();event=Event(0x12345678,0x5a);epoch=(0xffff0000+n*225)&0xffffffff
                assert fn(state,0x40,low,32768,bank,c.byref(de),epoch,c.byref(work),c.byref(out),c.byref(event))
                assert bytes(state)==after and (work.tstates,work.fetches,de.value,out.accumulator,out.unwind)==(prediction['tstates'],prediction['m1_fetches'],de_after,meta[n*2],meta[n*2+1])
                writes=grouped[n];assert len(writes)==out.write and len(writes)<=1
                if writes:
                    time,value=writes[0];assert begin<=time<=end
                    assert (event.due,event.value)==((epoch+time-begin)&0xffffffff,value),(kind,region,n,'source PSG timestamp')
                    relative=time-begin
                else:
                    assert (event.due,event.value)==(0x12345678,0x5a);relative=0
                unwinds+=out.unwind
                cases.append(dict(tstates=work.tstates,relative=relative,write=out.write,psg=out.psg,unwind=out.unwind))
            if first_cases is None:first_cases=cases
            else:assert cases==first_cases
            results.append(dict(kind=kind,region=region,cases=len(records),writes=len(ports)//16,unwinds=unwinds,frames=done[0],raw_sha256=hashes,fixture_sha256=hashlib.sha256(image).hexdigest()))
            print(kind,region,len(records),'original854B timestamps/state/T/M1/A/DE/unwind pass;',len(ports)//16,'writes',flush=True)
    # Shifted seven-slot semantic vectors also cover rejected memory reads.
    rows=make_cases()
    for n,row in enumerate(rows):
        initial=bytearray((i*37+row['salt'])&255 for i in range(400));offset=row['offset']
        for field,value in zip(FIELDS,row['input']):initial[offset+field]=value
        after=bytearray(initial)
        for field,value in zip(FIELDS,row['expected']):after[offset+field]=value
        state=(c.c_uint8*400).from_buffer_copy(initial);de=c.c_uint16(row['de']);work=Work();out=Output();event=Event(0x12345678,0x5a);epoch=(0xffff0000+n*225)&0xffffffff
        accepted=fn(state,offset,low,32768,bank,c.byref(de),epoch,c.byref(work),c.byref(out),c.byref(event))
        assert bytes(state)==after and (accepted,work.tstates,work.fetches,de.value,out.accumulator,out.unwind,out.write,out.psg)==tuple(row[k] for k in ['accepted','tstates','fetches','expected_de','accumulator','unwind','write','psg'])
        assert (event.due,event.value)==(((epoch+(row['tstates']-10)*15)&0xffffffff,row['psg']) if row['write'] else (0x12345678,0x5a))
    compiled=compiled_check(base,rows,sdk,env)
    report=dict(source_regions=results,shifted_host_cases=len(rows),invalid_host_cases=boundary_cases,compiled_regions=compiled,kernel_sha256=hashlib.sha256((base/'kernel/out/release/rom.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),sources={name:hashlib.sha256((ROOT/'megadrive/src'/(name+'.c')).read_bytes()).hexdigest() for name in MODULES},limits=['Original854B ADSR/table fixtures,all400 state bytes,fullT/A/DE/unwind and actual PSG handler time/data compared. M1 is compared against the previously source-verified model, not a new instruction counter in this observer. Custom DI caller,IXDE40; hold removed only from caller. Table POP unwind closes at3053; normal return at3003.','Host and compiled68000 also use shifted seven-slot semantic vectors including rejected reads. Timed mute is helperT-10 before final RET. Queue roundtrip uses supplied logical time; no complete timed8000 reader,physical subframe clock,paced PSG writes or full-game proof.'])
    (base/'cases.json').write_text(json.dumps(dict(fields=FIELDS,cases=rows),separators=(',',':'))+'\n')
    (ROOT/'analysis/envelope_timing_report.json').write_text(json.dumps(report,indent=2)+'\n')

def compiled_check(base,rows,sdk,env):
    kernel=base/'kernel';src=kernel/'src';src.mkdir(parents=True,exist_ok=True)
    lines=['static const u8 low[]={'+','.join(map(str,SOURCE[:32768]))+'};','static const u8 bank6[]={'+','.join(map(str,SOURCE[0x18000:0x1c000]))+'};','static const u16 fields[]={'+','.join(map(str,FIELDS))+'};','typedef struct {u16 offset,de,expected_de;u8 salt,accepted,accumulator,unwind,write,psg,input[10],expected[10];u32 tstates,fetches;} EnvelopeCase;','static const EnvelopeCase cases[]={']
    for row in rows:
        lines.append('{'+','.join(str(row[k]) for k in ['offset','de','expected_de','salt','accepted','accumulator','unwind','write','psg'])+',{'+','.join(map(str,row['input']))+'},{'+','.join(map(str,row['expected']))+'},'+str(row['tstates'])+'UL,'+str(row['fetches'])+'UL},')
    lines.append('};');(src/'expected.h').write_text('\n'.join(lines)+'\n')
    for name in MODULES:(src/(name+'.c')).write_text('#include "../../../../megadrive/src/'+name+'.c"\n')
    (src/'main.c').write_text('''#include <genesis.h>
#include "../../../../megadrive/src/source_audio_timed.h"
#include "expected.h"
volatile u32 gaw_envelope_cases,gaw_envelope_failures,gaw_envelope_queued;volatile u16 gaw_envelope_done;
int main(bool hard_reset)
{
 u32 row,epoch;u16 n,de;u8 state[400],expected[400],accepted;SourceClockWork work;SourceAudioEnvelopeOutput out;SourcePsgEvent event,storage[1],delivered;SourcePsgQueue queue;VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  const EnvelopeCase *p=cases+row;de=p->de;epoch=0xffff0000UL+row*225;
  for(n=0;n<400;n++) state[n]=expected[n]=(u8)(n*37+p->salt);
  for(n=0;n<10;n++) {state[p->offset+fields[n]]=p->input[n];expected[p->offset+fields[n]]=p->expected[n];}
  event.due=0x12345678;event.value=0x5a;
  accepted=source_audio_envelope_timed(state,p->offset,low,32768,bank6,&de,epoch,&work,&out,&event);
  if(accepted!=p->accepted || work.tstates!=p->tstates || work.fetches!=p->fetches || de!=p->expected_de || out.accumulator!=p->accumulator || out.unwind!=p->unwind || out.write!=p->write || out.psg!=p->psg) gaw_envelope_failures++;
  for(n=0;n<400;n++) if(state[n]!=expected[n]) gaw_envelope_failures++;
  source_psg_queue_init(&queue,storage,1);
  if(out.write)
  {
   if(event.due!=epoch+(p->tstates-10)*15 || event.value!=p->psg) gaw_envelope_failures++;
   if(source_psg_queue_push(&queue,&event,1)!=SOURCE_PSG_QUEUE_OK) gaw_envelope_failures++;
   if(source_psg_queue_take(&queue,event.due-1,&delivered)!=SOURCE_PSG_QUEUE_WAIT) gaw_envelope_failures++;
   if(source_psg_queue_take(&queue,event.due,&delivered)!=SOURCE_PSG_QUEUE_OK || delivered.value!=event.value || delivered.due!=event.due) gaw_envelope_failures++;
   gaw_envelope_queued++;
  }
  else if(event.due!=0x12345678 || event.value!=0x5a) gaw_envelope_failures++;
  if(source_psg_queue_take(&queue,epoch,&delivered)!=SOURCE_PSG_QUEUE_EMPTY) gaw_envelope_failures++;
  gaw_envelope_cases++;
 }
 gaw_envelope_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
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
            result.update(frame=frame,done=value('gaw_envelope_done',2),cases=value('gaw_envelope_cases',4),queued=value('gaw_envelope_queued',4),failures=value('gaw_envelope_failures',4))
        with contextlib.redirect_stdout(io.StringIO()):run(kernel/'out/release/rom.bin',30000,kernel/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(result.get('done')))
        assert result.get('done') and result['cases']==len(rows) and not result['failures'] and result['queued']==sum(row['write'] for row in rows),(region,result)
        results.append(dict(region=region,**result));print('68000',results[-1],flush=True)
    return results

if __name__=='__main__':main()
