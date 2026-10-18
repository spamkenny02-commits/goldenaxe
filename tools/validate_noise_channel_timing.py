"""Original864F port-time oracle for the complete timed native noise channel."""
import contextlib
import ctypes as c
import gzip
import hashlib
import io
import json
import os
import struct
import subprocess
from actor_reference import ROOT
from run_core import run
from validate_native_audio_prefix import Work
from validate_native_audio_sequence import Output
from validate_sequence_timing import TimedOutput,compiled_check

MODULES=['source_audio_noise_timed','source_audio_noise','source_audio_sequence_timed','source_audio_sequence','source_audio_priority','source_audio_memory','source_audio_envelope','source_psg_queue']
TONE_MODULES=['source_audio_tone_timed','source_audio_tone','source_audio_sequence_timed','source_audio_sequence','source_audio_priority','source_audio_memory','source_audio_envelope','source_audio_pitch','source_psg_queue']

def check_boundaries(timed,plain,tone=False):
    class Guarded(c.Structure):_fields_=[('before',c.c_uint32),('output',TimedOutput),('after',c.c_uint32)]
    streams=[(bytes([x]),False,0) for x in [0xe3,0xec,0xef,0xfe,0xff]]
    streams += [(bytes([0xf3,0,0xe3]),False,0),(bytes([0xf3,0])*256,False,0),(bytes([0xf3,3])*256,False,0),(bytes([0xf3,3])*255+bytes([7]),True,510)]
    if tone:streams[-1]=(streams[-1][0],False,0);streams.append((bytes([0xf3,3])*254+bytes([7]),True,511))
    image=(ROOT/'input/original.sms').read_bytes();bank=(c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000])
    for stream,valid,count in streams:
        raw=bytearray(image[:32768]);raw[0x3c00:0x3c00+len(stream)]=stream;low=(c.c_uint8*32768).from_buffer_copy(raw)
        slot=0x40 if tone else 0xd0
        initial=bytearray((i*37+17)&255 for i in range(400));initial[slot:slot+5]=bytes([128,128 if tone else 224,1,0,0x3c]);initial[slot+10]=1;initial[14]=0;initial[15]=128
        if tone:initial[slot+6:slot+9]=bytes(3);initial[slot+11:slot+13]=bytes([128,0]);initial[slot+37]=0
        state=(c.c_uint8*400).from_buffer_copy(initial);state2=(c.c_uint8*400).from_buffer_copy(initial);de=c.c_uint16(0x8a0b);de2=c.c_uint16(0x8a0b);work=Work();work2=Work();out=Guarded();out.before=0x12345678;out.after=0xabcdef01;out2=Output()
        ok=timed(state,slot,low,32768,bank,c.byref(de),c.byref(work),c.byref(out.output));ok2=plain(state2,slot,low,32768,bank,c.byref(de2),c.byref(work2),c.byref(out2))
        assert bool(ok)==valid and ok==ok2 and out.output.count==out2.count==count
        assert bytes(state)==bytes(state2) and de.value==de2.value and bytes(work)==bytes(work2) and (out.before,out.after)==(0x12345678,0xabcdef01)
        if not valid:assert bytes(state)==initial and de.value==0x8a0b and not work.tstates and not work.fetches and not out.output.unwind
        else:assert list(out.output.writes[:count])==list(out2.writes[:count]) and list(out.output.write_tstates[:count])==sorted(out.output.write_tstates[:count]) and all(0<=t<=work.tstates for t in out.output.write_tstates[:count])
    return len(streams)

def main(tone=False):
    channel_name='tone' if tone else 'noise';modules=TONE_MODULES if tone else MODULES
    base=ROOT/('validation/'+channel_name+'-channel-timing');base.mkdir(exist_ok=True)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src')]+[str(ROOT/'megadrive/src'/(module+'.c')) for module in modules]+['-o',str(base/'timed.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True);(base/'compile.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
    native=c.CDLL(str(base/'timed.dll'));timed=getattr(native,'source_audio_'+channel_name+'_timed');plain=getattr(native,'source_audio_'+channel_name)
    arguments=[c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.POINTER(c.c_uint16),c.POINTER(Work)]
    timed.argtypes=arguments+[c.POINTER(TimedOutput)];plain.argtypes=arguments+[c.POINTER(Output)];timed.restype=plain.restype=c.c_uint8
    boundary_cases=check_boundaries(timed,plain,tone=tone)
    paths=[ROOT/('validation/native-audio-'+channel_name+'/cases.json'),ROOT/('validation/native-audio-'+channel_name+'/extension-cases.json')]
    suites=[s for path in paths for s in json.loads(path.read_text()) if s.get('api',0)==0]
    core=ROOT.parents[1]/('work/genesis-plus-gx/genesis_plus_gx_'+channel_name+'channelports_libretro.dll');dll=c.CDLL(str(core))
    for name in ['gaw_port_samples','gaw_port_write_samples']:getattr(dll,name).restype=c.c_uint
    for name in ['gaw_port_call_data','gaw_port_write_data']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
    dll.gaw_port_meta_data.restype=c.POINTER(c.c_uint32)
    results=[];events=[]
    for suite in suites:
        kind=suite['kind'];slot=suite.get('offset',0xd0);image=(ROOT/suite['fixture']).read_bytes();assert hashlib.sha256(image).hexdigest()==suite['fixture_sha256']
        modified=bytearray(image);at=modified.find(bytes.fromhex('0603dbbfe680'),0x3100,0x3430)
        assert at>=0 and modified[at+9]==5 and modified[at+10]==0xc2
        modified[at:at+13]=bytes(13);cartridge=base/(kind+'.sms');cartridge.write_bytes(modified)
        low=(c.c_uint8*32768).from_buffer_copy(image[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000]);first=None
        for region in ['auto','pal']:
            dll.gaw_timing_reset();done=[]
            def observe(frame,ram):
                if ram[4]:done.append(frame)
            with contextlib.redirect_stdout(io.StringIO()):run(cartridge,len(suite['cases'])*4+100,base/(kind+'-'+region),set(),[],skip_intro=False,core=core,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(done))
            assert done and dll.gaw_port_samples()==len(suite['cases']) and dll.gaw_port_write_samples()<32768,(kind,region,dll.gaw_port_samples(),len(suite['cases']))
            calls=c.string_at(dll.gaw_port_call_data(),len(suite['cases'])*824);ports=c.string_at(dll.gaw_port_write_data(),dll.gaw_port_write_samples()*16);meta=dll.gaw_port_meta_data();hashes={}
            for artifact,raw in [('calls',calls),('ports',ports),('meta',c.string_at(meta,len(suite['cases'])*8))]:
                packed=gzip.compress(raw,mtime=0);assert gzip.decompress(packed)==raw;(base/(kind+'-'+region+'-'+artifact+'.bin.gz')).write_bytes(packed);hashes[artifact]=hashlib.sha256(raw).hexdigest()
            grouped=[[] for _ in suite['cases']]
            for pos in range(0,len(ports),16):
                time,index,value=struct.unpack_from('<QII',ports,pos);grouped[index].append((time,value))
            cases=[]
            for n,row in enumerate(suite['cases']):
                begin,end,de_before,de_after=struct.unpack_from('<2Q2I',calls,n*824);before=calls[n*824+24:n*824+424];after=calls[n*824+424:n*824+824]
                initial=bytearray(suite['seed'])
                for index,value in zip(suite['offsets'],row['input']):initial[index]=value
                assert before==initial and de_before==row['de_in'],(kind,region,n,'source input')
                expected=bytearray(before)
                for index,value in row['patches']:expected[index]=value
                assert after==expected and end-begin==row['tstates']*15 and de_after==row['de'] and bool(meta[n*2+1])==(row['unwind']==2),(kind,region,n,'source semantics')
                state=(c.c_uint8*400).from_buffer_copy(before);work=Work();output=TimedOutput();de=c.c_uint16(de_before)
                assert timed(state,slot,low,32768,bank,c.byref(de),c.byref(work),c.byref(output))
                assert bytes(state)==after and (work.tstates,work.fetches,de.value,output.unwind,output.error)==(row['tstates'],row['fetches'],row['de'],row['unwind'],0)
                writes=grouped[n];assert list(output.writes[:output.count])==[v for t,v in writes],(kind,region,n,'PSG bytes')
                times=list(output.write_tstates[:output.count]);assert times==[(t-begin)//15 for t,v in writes] and all((t-begin)%15==0 for t,v in writes),(kind,region,n,'PSG times',times,[(t-begin)//15 for t,v in writes])
                assert times==sorted(times) and all(0<=t<=work.tstates for t in times)
                if region=='auto':
                    state2=(c.c_uint8*400).from_buffer_copy(before);work2=Work();out2=Output();de2=c.c_uint16(de_before)
                    assert plain(state2,slot,low,32768,bank,c.byref(de2),c.byref(work2),c.byref(out2))
                    assert bytes(state2)==after and bytes(work2)==bytes(work) and de2.value==de.value and (out2.de,out2.count,out2.unwind,out2.error,list(out2.writes[:out2.count]))==(output.de,output.count,output.unwind,output.error,list(output.writes[:output.count]))
                cases.append(dict(writes=[v for t,v in writes],times=times))
            if first is None:first=cases
            else:assert cases==first
            results.append(dict(kind=kind,region=region,cases=len(cases),writes=len(ports)//16,frames=done[0],raw_sha256=hashes,fixture_sha256=hashlib.sha256(modified).hexdigest()))
            print(kind,region,len(cases),'source'+('84C7' if tone else '864F')+' state/work/DE/exit/PSG bytes/times pass;',len(ports)//16,'writes',flush=True)
        events.append(dict(kind=kind,events=first))
    (base/'events.json').write_text(json.dumps(events,separators=(',',':'))+'\n')
    compiled=compiled_check(base,suites,events,sdk,env,noise=not tone,modules=modules,api='tone' if tone else 'sequence')
    report=dict(results=results,compiled=compiled,host_rejection_capacity_cases=boundary_cases,core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),sources={module:hashlib.sha256((ROOT/'megadrive/src'/(module+'.c')).read_bytes()).hexdigest() for module in modules},limits=['Original'+('84C7' if tone else '864F')+' fixtures with only caller hold removed. Full source input/all400 output bytes,T,DE/reader exit and actual PSG handler byte/timestamp list compared. M1 uses existing source-verified vectors. Normal native channel also compared to the timed composition.','Compiled68000 PAL/NTSC checks state/work and source byte/timestamp lists, then queue roundtrips. No full timed8000 reader or physical clock/pacing/waveform proof.'])
    assert channel_name in ['tone','noise']
    (ROOT/('analysis/'+channel_name+'_channel_timing_report.json')).write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
