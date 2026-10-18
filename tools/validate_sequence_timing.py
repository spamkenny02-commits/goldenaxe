"""Per-OUT timestamps from shared8357 semantics vs the original port handler."""
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
import sys
from actor_reference import ROOT
from run_core import run
from validate_native_audio_prefix import Work
from validate_native_audio_sequence import Output

class TimedOutput(c.Structure):
    _fields_=Output._fields_+[('write_tstates',c.c_uint32*512)]
MODULES=['source_audio_sequence_timed','source_audio_sequence','source_audio_priority','source_audio_memory','source_psg_queue']

def check_rejection_capacity(timed,plain):
    class Guarded(c.Structure):_fields_=[('before',c.c_uint32),('output',TimedOutput),('after',c.c_uint32)]
    streams=[(bytes([control]),False,0) for control in [0xe3,0xec,0xef,0xfe,0xff]]
    streams += [(bytes([0xf3,0,0xe3]),False,0),(bytes([0xf3,0])*256,False,0),(bytes([0xf3,3])*256,False,0),(bytes([0xf3,3])*255+bytes([7]),True,510)]
    image=(ROOT/'input/original.sms').read_bytes();bank=(c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000])
    for stream,valid,count in streams:
        raw=bytearray(image[:32768]);raw[0x3c00:0x3c00+len(stream)]=stream;low=(c.c_uint8*32768).from_buffer_copy(raw)
        initial=bytearray((i*37+17)&255 for i in range(400));initial[0x40:0x45]=bytes([128,128,1,0,0x3c]);initial[14]=0;initial[15]=128
        state=(c.c_uint8*400).from_buffer_copy(initial);state2=(c.c_uint8*400).from_buffer_copy(initial);work=Work();work2=Work();guard=Guarded();guard.before=0x12345678;guard.after=0xabcdef01;out2=Output()
        ok=timed(state,0x40,low,32768,bank,c.byref(work),c.byref(guard.output));ok2=plain(state2,0x40,low,32768,bank,c.byref(work2),c.byref(out2))
        out=guard.output
        assert bool(ok)==valid and ok==ok2 and out.count==out2.count==count
        assert bytes(state)==bytes(state2) and bytes(work)==bytes(work2) and (guard.before,guard.after)==(0x12345678,0xabcdef01)
        if not valid:assert bytes(state)==initial and not work.tstates and not work.fetches and not out.unwind
        else:assert list(out.writes[:count])==list(out2.writes[:count]) and list(out.write_tstates[:count])==sorted(out.write_tstates[:count]) and all(0<=t<=work.tstates for t in out.write_tstates[:count])
    return len(streams)

def main():
    base=ROOT/'validation/sequence-timing';base.mkdir(exist_ok=True)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src')]+[str(ROOT/'megadrive/src'/(name+'.c')) for name in MODULES]+['-o',str(base/'timed.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True);(base/'compile.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
    native=c.CDLL(str(base/'timed.dll'));timed=native.source_audio_sequence_timed;plain=native.source_audio_sequence
    arguments=[c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.POINTER(Work)]
    timed.argtypes=arguments+[c.POINTER(TimedOutput)];plain.argtypes=arguments+[c.POINTER(Output)];timed.restype=plain.restype=c.c_uint8
    boundary_cases=check_rejection_capacity(timed,plain)
    fixture=json.loads((ROOT/'validation/native-audio-sequence/cases.json').read_text());suites=fixture['suites']
    for suite in suites:
        for row in suite['cases']:row['patches']=[(fixture['fields'][row['patches'][n]],row['patches'][n+1]) for n in range(0,len(row['patches']),2)]
    suites+=json.loads((ROOT/'validation/native-audio-sequence/extension-cases.json').read_text())
    if '--compiled-only' in sys.argv:
        compiled=compiled_check(base,suites,json.loads((base/'events.json').read_text()),sdk,env)
        path=ROOT/'analysis/sequence_timing_report.json';report=json.loads(path.read_text());report['compiled']=compiled;report['host_rejection_capacity_cases']=boundary_cases
        report['limits'][1]='Compiled68000 PAL/NTSC also checks retained state/work and source-observed byte/timestamp lists, then native queue roundtrips. Noise8655 variant still needs its source oracle. No complete timed8000 reader or physical clock/pacing proof.'
        path.write_text(json.dumps(report,indent=2)+'\n');return
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_sequenceports_libretro.dll';dll=c.CDLL(str(core))
    for name in ['gaw_port_samples','gaw_port_write_samples']:getattr(dll,name).restype=c.c_uint
    for name in ['gaw_port_call_data','gaw_port_write_data']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
    dll.gaw_port_meta_data.restype=c.POINTER(c.c_uint32)
    results=[];all_cases=[]
    for suite in suites:
        kind=suite['kind'];image=(ROOT/suite['fixture']).read_bytes();assert hashlib.sha256(image).hexdigest()==suite['fixture_sha256']
        modified=bytearray(image);at=modified.find(bytes.fromhex('0603dbbfe680'),0x3100,0x3430)
        assert at>=0 and modified[at+9]==5 and modified[at+10]==0xc2
        modified[at:at+13]=bytes(13);cartridge=base/(kind+'.sms');cartridge.write_bytes(modified)
        low=(c.c_uint8*32768).from_buffer_copy(image[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000])
        first=None
        for region in ['auto','pal']:
            dll.gaw_timing_reset();done=[]
            def observe(frame,ram):
                if ram[4]:done.append(frame)
            with contextlib.redirect_stdout(io.StringIO()):run(cartridge,len(suite['cases'])*4+100,base/(kind+'-'+region),set(),[],skip_intro=False,core=core,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(done))
            assert done and dll.gaw_port_samples()==len(suite['cases']) and dll.gaw_port_write_samples()<32768,(kind,region,dll.gaw_port_samples(),len(suite['cases']))
            calls=c.string_at(dll.gaw_port_call_data(),len(suite['cases'])*824);ports=c.string_at(dll.gaw_port_write_data(),dll.gaw_port_write_samples()*16);meta=dll.gaw_port_meta_data();hashes={}
            for name,raw in [('calls',calls),('ports',ports),('meta',c.string_at(meta,len(suite['cases'])*8))]:
                packed=gzip.compress(raw,mtime=0);assert gzip.decompress(packed)==raw;(base/(kind+'-'+region+'-'+name+'.bin.gz')).write_bytes(packed);hashes[name]=hashlib.sha256(raw).hexdigest()
            grouped=[[] for _ in suite['cases']]
            for pos in range(0,len(ports),16):
                time,index,value=struct.unpack_from('<QII',ports,pos);grouped[index].append((time,value))
            cases=[]
            for n,row in enumerate(suite['cases']):
                begin,end,_,de_after=struct.unpack_from('<2Q2I',calls,n*824);before=calls[n*824+24:n*824+424];after=calls[n*824+424:n*824+824]
                expected=bytearray(before)
                for index,value in row['patches']:expected[index]=value
                assert after==expected and end-begin==row['tstates']*15 and de_after==row['de'] and meta[n*2+1]==row['unwind'],(kind,region,n,'source semantics')
                state=(c.c_uint8*400).from_buffer_copy(before);work=Work();output=TimedOutput()
                assert timed(state,0x40,low,32768,bank,c.byref(work),c.byref(output))
                assert bytes(state)==after and (work.tstates,work.fetches,output.de,output.unwind,output.error)==(row['tstates'],row['fetches'],row['de'],row['unwind'],0)
                writes=grouped[n];assert list(output.writes[:output.count])==[v for t,v in writes],(kind,region,n,'PSG bytes')
                times=list(output.write_tstates[:output.count]);assert times==[(t-begin)//15 for t,v in writes] and all((t-begin)%15==0 for t,v in writes),(kind,region,n,'PSG times',times,[(t-begin)//15 for t,v in writes])
                assert all(0<=t<=work.tstates for t in times) and times==sorted(times)
                if region=='auto':
                    state2=(c.c_uint8*400).from_buffer_copy(before);work2=Work();out2=Output()
                    assert plain(state2,0x40,low,32768,bank,c.byref(work2),c.byref(out2))
                    assert bytes(state2)==after and bytes(work2)==bytes(work) and (out2.de,out2.count,out2.unwind,out2.error,list(out2.writes[:out2.count]))==(output.de,output.count,output.unwind,output.error,list(output.writes[:output.count]))
                cases.append(dict(writes=[v for t,v in writes],times=times))
            if first is None:first=cases
            else:assert cases==first
            results.append(dict(kind=kind,region=region,cases=len(cases),writes=len(ports)//16,frames=done[0],raw_sha256=hashes,fixture_sha256=hashlib.sha256(modified).hexdigest()))
            print(kind,region,len(cases),'source8357 state/work/DE/unwind/PSG bytes/times pass;',len(ports)//16,'writes',flush=True)
        all_cases.append(dict(kind=kind,events=first))
    (base/'events.json').write_text(json.dumps(all_cases,separators=(',',':'))+'\n')
    compiled=compiled_check(base,suites,all_cases,sdk,env)
    report=dict(results=results,compiled=compiled,host_rejection_capacity_cases=boundary_cases,core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),sources={name:hashlib.sha256((ROOT/'megadrive/src'/(name+'.c')).read_bytes()).hexdigest() for name in MODULES},limits=['Original8357 fixtures with only custom caller hold removed. All400 bytes,T,DE/unwind and every completed-OUT cycle/data compared; M1 uses retained source vectors. Separate timed composition reuses authoritative C with optional sidecar stores; default semantic outputs also compared.','Compiled68000 PAL/NTSC also checks retained state/work and source-observed byte/timestamp lists, then native queue roundtrips. Noise8655 variant still needs its source oracle. No complete timed8000 reader or physical clock/pacing proof.'])
    (ROOT/'analysis/sequence_timing_report.json').write_text(json.dumps(report,indent=2)+'\n')

def compiled_check(base,suites,events,sdk,env,noise=False,modules=None):
    modules=MODULES if modules is None else modules
    rows=[(index,row,event) for index,suite in enumerate(suites) for row,event in zip(suite['cases'],events[index]['events'])]
    assert all(len(s['cases'])==len(events[n]['events']) and s['kind']==events[n]['kind'] for n,s in enumerate(suites))
    fields=sorted({offset for _,row,_ in rows for offset,value in row['patches']});assert len(fields)<=255
    lows=[(ROOT/s['fixture']).read_bytes()[:32768] for s in suites];bank=(ROOT/'input/original.sms').read_bytes()[0x18000:0x1c000]
    seeds=[bytes(s.get('seed',[(i*37+17)&255 for i in range(400)])) for s in suites]
    max_events=max(1,max(len(event['writes']) for _,_,event in rows));queue_capacity=1
    while queue_capacity<max_events:queue_capacity*=2
    results=[]
    for part,start in enumerate(range(0,len(rows),25000)):
        selected=rows[start:start+25000];kernel=base/f'kernel-{part}';src=kernel/'src';src.mkdir(parents=True,exist_ok=True)
        max_patches=max(len(row['patches']) for _,row,_ in selected)
        lines=['static const u8 low[][32768]={'+','.join('{'+','.join(map(str,raw))+'}' for raw in lows)+'};','static const u8 seed[][400]={'+','.join('{'+','.join(map(str,raw))+'}' for raw in seeds)+'};','static const u8 bank6[]={'+','.join(map(str,bank))+'};','static const u16 fields[]={'+','.join(map(str,fields))+'};','static const u8 offset_count[]={'+','.join(str(len(s['offsets'])) for s in suites)+'};','static const u16 offsets[][16]={'+','.join('{'+','.join(map(str,s['offsets']))+'}' for s in suites)+'};',f'typedef struct {{u8 suite,patch_count,unwind,count,input[16],patches[{max_patches*2}],writes[{max_events}];u16 de_in,de;u32 tstates,fetches,times[{max_events}];}} TimedCase;','static const TimedCase cases[]={']
        for index,row,event in selected:
            patches=[v for offset,value in row['patches'] for v in [fields.index(offset),value]]
            lines.append('{'+','.join(map(str,[index,len(row['patches']),row['unwind'],len(event['writes'])]))+',{'+','.join(map(str,row['input']))+'},{'+','.join(map(str,patches))+'},{'+','.join(map(str,event['writes']))+'},'+str(row.get('de_in',0))+','+str(row['de'])+','+str(row['tstates'])+'UL,'+str(row['fetches'])+'UL,{'+','.join(str(t)+'UL' for t in event['times'])+'}},')
        lines.append('};');(src/'expected.h').write_text('\n'.join(lines)+'\n')
        for name in modules:(src/(name+'.c')).write_text('#include "../../../../megadrive/src/'+name+'.c"\n')
        main='''#include <genesis.h>
#include "../../../../megadrive/src/source_audio_timed.h"
#include "expected.h"
volatile u32 gaw_sequence_cases,gaw_sequence_failures,gaw_sequence_writes;volatile u16 gaw_sequence_done;
static SourceAudioTimedSequenceOutput output;
int main(bool hard_reset)
{
 u32 row,epoch;u16 n,de;u8 state[400],expected[400];SourceClockWork work;SourcePsgQueue queue;SourcePsgEvent storage[QUEUE_CAPACITY],pending[MAX_EVENTS],delivered;VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  const TimedCase *p=cases+row;epoch=0xffff0000UL+row*225;de=p->de_in;(void)de;
  for(n=0;n<400;n++) state[n]=seed[p->suite][n];
  for(n=0;n<offset_count[p->suite];n++) state[offsets[p->suite][n]]=p->input[n];
  for(n=0;n<400;n++) expected[n]=state[n];
  for(n=0;n<p->patch_count;n++) expected[fields[p->patches[n*2]]]=p->patches[n*2+1];
  if(!TIMED_CALL || output.error || output.count!=p->count || output.de!=p->de || output.unwind!=p->unwind || work.tstates!=p->tstates || work.fetches!=p->fetches EXTRA_CHECK) gaw_sequence_failures++;
  for(n=0;n<400;n++) if(state[n]!=expected[n]) gaw_sequence_failures++;
  for(n=0;n<p->count;n++)
  {
   if(output.writes[n]!=p->writes[n] || output.write_tstates[n]!=p->times[n]) gaw_sequence_failures++;
   pending[n].due=epoch+output.write_tstates[n]*15;pending[n].value=output.writes[n];
  }
  source_psg_queue_init(&queue,storage,QUEUE_CAPACITY);
  if(source_psg_queue_push(&queue,pending,p->count)!=SOURCE_PSG_QUEUE_OK) gaw_sequence_failures++;
  for(n=0;n<p->count;n++)
  {
   if(source_psg_queue_take(&queue,pending[n].due-1,&delivered)!=SOURCE_PSG_QUEUE_WAIT) gaw_sequence_failures++;
   if(source_psg_queue_take(&queue,pending[n].due,&delivered)!=SOURCE_PSG_QUEUE_OK || delivered.value!=p->writes[n] || delivered.due!=epoch+p->times[n]*15) gaw_sequence_failures++;
   gaw_sequence_writes++;
  }
  if(source_psg_queue_take(&queue,epoch,&delivered)!=SOURCE_PSG_QUEUE_EMPTY) gaw_sequence_failures++;
  gaw_sequence_cases++;
 }
 gaw_sequence_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
'''
        call='source_audio_noise_timed(state,0xd0,low[p->suite],32768,bank6,&de,&work,&output)' if noise else 'source_audio_sequence_timed(state,0x40,low[p->suite],32768,bank6,&work,&output)'
        main=main.replace('TIMED_CALL',call).replace('EXTRA_CHECK','|| de!=p->de' if noise else '').replace('QUEUE_CAPACITY',str(queue_capacity)).replace('MAX_EVENTS',str(max_events));(src/'main.c').write_text(main)
        path=str(sdk).replace('\\','/');unix='/'+path[0].lower()+path[2:];env=dict(env);env['PATH']=str(sdk/'bin')+';'+env['PATH']
        built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=kernel,env=env,capture_output=True,text=True)
        (kernel/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2000:]
        sy={m[2]:int(m[1],16)&65535 for line in (kernel/'out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};cartridge=kernel/'out/release/rom.bin';assert cartridge.stat().st_size<=4*1024*1024
        for region in ['auto','pal']:
            observed={}
            def observe(frame,ram):
                def value(name,width):return int.from_bytes(bytes(ram[(sy[name]+i)^1] for i in range(width)),'big')
                observed.update(frame=frame,done=value('gaw_sequence_done',2),cases=value('gaw_sequence_cases',4),writes=value('gaw_sequence_writes',4),failures=value('gaw_sequence_failures',4))
            with contextlib.redirect_stdout(io.StringIO()):run(cartridge,30000,kernel/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
            assert observed.get('done') and observed['cases']==len(selected) and not observed['failures'] and observed['writes']==sum(len(event['writes']) for _,_,event in selected),(part,region,observed)
            results.append(dict(part=part,region=region,kernel_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),**observed));print('68000',results[-1],flush=True)
    return results

if __name__=='__main__':main()
