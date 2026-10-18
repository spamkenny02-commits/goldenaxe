"""Legacy/timed stream parity, including partial state/output on rejection."""
import ctypes as c
import hashlib
import json
import os
import random
import struct
import subprocess
import sys
from actor_reference import ROOT
from validate_reader_timing import MODULES,Status,SINK
from validate_native_audio_prefix import Work

PLAIN_SINK=c.CFUNCTYPE(None,c.c_void_p,c.POINTER(c.c_uint8),c.c_uint16)

def main():
    master='--master' in sys.argv;fast='--fast' in sys.argv or master;modules=MODULES+(['source_audio_fast_timed','source_audio_fast'] if fast else [])+(['source_audio_reader_master'] if master else [])
    base=ROOT/('validation/master-timed-reader-failures' if master else 'validation/fast-timed-reader-failures' if fast else 'validation/timed-reader-failures');base.mkdir(exist_ok=True);sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-shared','-Wall','-Wextra','-Werror','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src')]+[str(ROOT/'megadrive/src'/(name+'.c')) for name in modules]+['-o',str(base/'reader.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True);assert not built.returncode,built.stderr
    dll=c.CDLL(str(base/'reader.dll'));plain=getattr(dll,'source_audio_reader_stream_fast' if fast else 'source_audio_reader_stream');timed=getattr(dll,'source_audio_reader_stream_fast_master' if master else 'source_audio_reader_stream_fast_timed' if fast else 'source_audio_reader_stream_timed')
    common=[c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.POINTER(c.c_uint16),c.POINTER(Work),c.POINTER(Status)]
    plain.argtypes=common+[PLAIN_SINK,c.c_void_p];timed.argtypes=common+([c.c_uint32] if master else [])+[SINK,c.c_void_p];plain.restype=timed.restype=c.c_uint8
    image=(ROOT/'input/original.sms').read_bytes();low=(c.c_uint8*32768).from_buffer_copy(image[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000]);suites=json.loads((ROOT/'validation/native-audio-reader/extension-cases.json').read_text());seed=bytes(suites[-1]['cases'][0]['before']);rng=random.Random(0x800084c7);accepted=rejected=partial=0;digest=hashlib.sha256()
    for n in range(3000):
        initial=bytearray(seed)
        for k in range(1+n%19):initial[rng.randrange(400)]=rng.randrange(256)
        initial[10]=0;de_in=rng.randrange(65536);outputs=[]
        for with_times in [False,True]:
            state=(c.c_uint8*400).from_buffer_copy(initial);de=c.c_uint16(de_in);work=Work();status=Status();writes=[];times=[]
            @PLAIN_SINK
            def ordinary(context,p,count):writes.extend(p[i] for i in range(count))
            @SINK
            def dated(context,p,t,count):writes.extend(p[i] for i in range(count));times.extend(t[i] for i in range(count))
            epoch=(0xffffff00+n*553)&0xffffffff
            extra=[epoch] if master and with_times else []
            ok=(timed if with_times else plain)(state,low,32768,bank,c.byref(de),c.byref(work),c.byref(status),*extra,dated if with_times else ordinary,None)
            outputs.append((ok,bytes(state),de.value,work.tstates,work.fetches,status.count,status.error,status.track,bytes(writes)))
            if with_times:
                if master:
                    delta=[(time-epoch)&0xffffffff for time in times];assert all(t%15==0 for t in delta)
                    times=[t//15 for t in delta]
                assert len(times)==len(writes) and times==sorted(times)
                if ok:assert all(0<=t<=work.tstates for t in times)
        assert outputs[0]==outputs[1],(n,'partial stream semantics mismatch')
        out=outputs[1]
        if out[0]:accepted+=1
        else:
            rejected+=1;assert out[3]==out[4]==0
            if out[8]:partial+=1
        digest.update(out[1]);digest.update(struct.pack('<7I',out[0],*out[2:8]));digest.update(out[8])
    assert rejected and partial
    report=dict(fast=fast,fused_master=master,cases=3000,accepted=accepted,rejected=rejected,rejections_after_published_writes=partial,result_digest=digest.hexdigest(),sources={name:hashlib.sha256((ROOT/'megadrive/src'/(name+'.c')).read_bytes()).hexdigest() for name in modules},limits=['Deterministic mutations compare matching timed/untimed stream snapshot contracts,including earlier committed state/PSG lists on a later failure. The fast contract allows failed-channel state changes. No outer transactional rollback is promised.','No source-oracle execution of rejected arbitrary contexts,hardware pacing or waveform proof. Successful source vectors and compiled68000 checks are separate.'])
    (ROOT/('analysis/master_timed_reader_failures_report.json' if master else 'analysis/fast_timed_reader_failures_report.json' if fast else 'analysis/timed_reader_failures_report.json')).write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ['sources','limits']},flush=True)

if __name__=='__main__':main()
