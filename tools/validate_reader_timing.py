"""Full8000 timed stream versus original PSG port timestamps and saved states."""
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
from validate_native_audio_reader import Output
from validate_loading_psg_deadlines import fixture

MODULES=['source_audio_reader_timed','source_audio_prefix_timed','source_audio_tone_timed','source_audio_noise_timed','source_audio_sequence_timed','source_audio_reader','source_audio_prefix','source_audio_dispatch','source_audio_priority','source_audio_tone','source_audio_noise','source_audio_sequence','source_audio_memory','source_audio_envelope','source_audio_pitch']
class Status(c.Structure):_fields_=[('count',c.c_uint16),('error',c.c_uint16),('track',c.c_uint8)]
SINK=c.CFUNCTYPE(None,c.c_void_p,c.POINTER(c.c_uint8),c.POINTER(c.c_uint32),c.c_uint16)

def main():
    base=ROOT/'validation/reader-timing';base.mkdir(exist_ok=True)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src')]+[str(ROOT/'megadrive/src'/(name+'.c')) for name in MODULES]+['-o',str(base/'timed.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True);(base/'compile.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
    native=c.CDLL(str(base/'timed.dll'));timed=native.source_audio_reader_stream_timed;plain=native.source_audio_reader
    arguments=[c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.POINTER(c.c_uint16),c.POINTER(Work)]
    timed.argtypes=arguments+[c.POINTER(Status),SINK,c.c_void_p];plain.argtypes=arguments+[c.POINTER(Output)];timed.restype=plain.restype=c.c_uint8
    inputs=[ROOT/'validation/native-audio-reader/cases.json',ROOT/'validation/native-audio-reader/extension-cases.json'];suites=[s for path in inputs for s in json.loads(path.read_text())]
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_readerports_libretro.dll';dll=c.CDLL(str(core))
    for name in ['gaw_port_samples','gaw_port_write_samples']:getattr(dll,name).restype=c.c_uint
    for name in ['gaw_port_call_data','gaw_port_write_data']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
    results=[];events=[]
    for suite in suites:
        kind=suite['kind'];original=(ROOT/suite['fixture']).read_bytes();assert hashlib.sha256(original).hexdigest()==suite['fixture_sha256'];low=(c.c_uint8*32768).from_buffer_copy(original[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(original[0x18000:0x1c000]);all_events=[]
        for part,start in enumerate(range(0,len(suite['cases']),4096)):
            rows=suite['cases'][start:start+4096];folder=base/(kind+'-'+str(part));folder.mkdir(exist_ok=True)
            cartridge=fixture(folder,[dict(before=row['before'],de=row['de_in']) for row in rows]);image=bytearray(cartridge.read_bytes());caller=bytes(image[:32768]);image[:32768]=original[:32768];image[:3]=caller[:3];image[0x3000:0x3004]=caller[0x3000:0x3004];image[0x3100:0x3400]=caller[0x3100:0x3400];image.extend(bytes(0x400000-len(image)));cartridge.write_bytes(image)
            assert image[0x18000:0x1c000]==original[0x18000:0x1c000]
            first=None
            for region in ['auto','pal']:
                dll.gaw_timing_reset();done=[]
                def observe(frame,ram):
                    if ram[4]:done.append(frame)
                with contextlib.redirect_stdout(io.StringIO()):run(cartridge,len(rows)*8+100,folder/region,set(),[],skip_intro=False,core=core,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(done))
                assert done and dll.gaw_port_samples()==len(rows) and dll.gaw_port_write_samples()<262144,(kind,part,region,dll.gaw_port_samples(),len(rows))
                calls=c.string_at(dll.gaw_port_call_data(),len(rows)*824);ports=c.string_at(dll.gaw_port_write_data(),dll.gaw_port_write_samples()*16);hashes={}
                for artifact,raw in [('calls',calls),('ports',ports)]:
                    packed=gzip.compress(raw,mtime=0);assert gzip.decompress(packed)==raw;(folder/(region+'-'+artifact+'.bin.gz')).write_bytes(packed);hashes[artifact]=hashlib.sha256(raw).hexdigest()
                grouped=[[] for _ in rows]
                for pos in range(0,len(ports),16):
                    time,index,value=struct.unpack_from('<QII',ports,pos);grouped[index].append((time,value))
                part_events=[]
                for n,row in enumerate(rows):
                    begin,end,de_before,de_after=struct.unpack_from('<2Q2I',calls,n*824);before=calls[n*824+24:n*824+424];after=calls[n*824+424:n*824+824]
                    assert before==bytes(row['before']) and after==bytes(row['after']) and (end-begin,de_before,de_after)==(row['tstates']*15,row['de_in'],row['de']),(kind,start+n,region,'source state/work/DE')
                    state=(c.c_uint8*400).from_buffer_copy(before);de=c.c_uint16(de_before);work=Work();status=Status();writes=[];times=[]
                    @SINK
                    def sink(context,p,t,count):writes.extend(p[i] for i in range(count));times.extend(t[i] for i in range(count))
                    assert timed(state,low,32768,bank,c.byref(de),c.byref(work),c.byref(status),sink,None)
                    assert bytes(state)==after and (work.tstates,work.fetches,de.value,status.error,status.count)==(row['tstates'],row['fetches'],row['de'],0,len(writes)),(kind,start+n,'timed semantics')
                    actual=grouped[n];assert writes==[v for t,v in actual],(kind,start+n,'PSG bytes')
                    assert times==[(t-begin)//15 for t,v in actual] and all((t-begin)%15==0 for t,v in actual),(kind,start+n,'PSG times',times,[(t-begin)//15 for t,v in actual])
                    assert times==sorted(times) and all(0<=t<=work.tstates for t in times)
                    if region=='auto':
                        state2=(c.c_uint8*400).from_buffer_copy(before);de2=c.c_uint16(de_before);work2=Work();out=Output()
                        assert plain(state2,low,32768,bank,c.byref(de2),c.byref(work2),c.byref(out))
                        assert bytes(state2)==after and bytes(work2)==bytes(work) and de2.value==de.value and (out.count,out.error,out.track,list(out.writes[:out.count]))==(status.count,status.error,status.track,writes)
                    part_events.append(dict(writes=writes,times=times,track=status.track))
                if first is None:first=part_events
                else:assert part_events==first
                results.append(dict(kind=kind,part=part,region=region,cases=len(rows),writes=len(ports)//16,frames=done[0],raw_sha256=hashes,fixture_sha256=hashlib.sha256(image).hexdigest()))
                print(kind,part,region,len(rows),'source8000 state/work/DE/PSG bytes/times pass;',len(ports)//16,'writes',flush=True)
            all_events.extend(first)
        events.append(dict(kind=kind,events=all_events))
    (base/'events.json').write_text(json.dumps(events,separators=(',',':'))+'\n')
    report=dict(results=results,core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),sources={name:hashlib.sha256((ROOT/'megadrive/src'/(name+'.c')).read_bytes()).hexdigest() for name in MODULES},limits=['Original8000/bank6 intact. Custom DI caller replays retained full400-byte inputs and DE; low fixture streams preserved apart from bootstrap/caller. Every output byte,T,DE and actual PSG byte/time compared. M1 uses retained source vectors. Legacy capture API/status also compared.','Host timed full-reader composition only until compiled proof is recorded. Stream publishes successful lists; no physical clock/pacing/waveform,global boot phase,production budget or full-game proof.'])
    (ROOT/'analysis/reader_timing_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
