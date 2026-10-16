"""Native8000 composition against retained source gates and live reader captures."""
import ctypes as c
import hashlib
import json
import os
import struct
import subprocess
from actor_reference import ROOT
from audio_reader_refresh import reader_refresh
from validate_native_audio_prefix import Work

MODULES=['source_audio_reader','source_audio_prefix','source_audio_dispatch','source_audio_priority',
         'source_audio_tone','source_audio_noise','source_audio_sequence','source_audio_memory',
         'source_audio_envelope','source_audio_pitch']


class Output(c.Structure):
    _fields_=[('count',c.c_uint16),('error',c.c_uint16),('track',c.c_uint8),('writes',c.c_uint8*(7*512+32))]


def compile_helper():
    folder=ROOT/'validation/native-audio-reader';folder.mkdir(exist_ok=True)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ)
    env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared',
          '-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src')]
    args.extend(str(ROOT/'megadrive/src'/f'{name}.c') for name in MODULES)
    args.extend(['-o',str(folder/'source_audio_reader.dll')])
    built=subprocess.run(args,env=env,capture_output=True,text=True)
    (folder/'compile.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'source_audio_reader.dll'));function=dll.source_audio_reader
    function.argtypes=[c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),
                       c.POINTER(c.c_uint16),c.POINTER(Work),c.POINTER(Output)]
    function.restype=c.c_uint8;return folder,dll,function


def check(function,image,before,de_in,after,cost,fetches,de_after,label):
    low=(c.c_uint8*32768).from_buffer_copy(image[:32768])
    bank=(c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000])
    state=(c.c_uint8*400).from_buffer_copy(before);de=c.c_uint16(de_in)
    work=Work();output=Output()
    assert function(state,low,32768,bank,c.byref(de),c.byref(work),c.byref(output)) and not output.error,(label,'rejected',output.error)
    assert (bytes(state),work.tstates,work.fetches,de.value)==(after,cost,fetches,de_after),(
        label,'source/native',work.tstates,cost,work.fetches,fetches,de.value,de_after,
        [(i,a,b) for i,(a,b) in enumerate(zip(state,after)) if a!=b][:10])
    return output


def main():
    folder,dll,function=compile_helper();rows=[]
    reference=json.loads((ROOT/'analysis/audio_reader_refresh_report.json').read_text())
    path=ROOT/'validation/audio-reader-gates/gates/source.sms';image=path.read_bytes()
    assert hashlib.sha256(image).hexdigest()==reference['fixture_sha256']
    seed=image[0x3430:0x3430+400];gate_cases=[]
    for number in range(reference['cases']//2):
        inputs=image[0x80000+number*16:0x80000+(number+1)*16];before=bytearray(seed)
        for offset,value in zip([10,3,4,5],inputs):before[offset]=value
        prediction=reader_refresh(image,before,0x8a0b)
        check(function,image,before,0x8a0b,prediction['state'],prediction['tstates'],prediction['m1_fetches'],prediction['de'],('gates',number))
        gate_cases.append(dict(before=list(before),after=list(prediction['state']),de_in=0x8a0b,
                               de=prediction['de'],tstates=prediction['tstates'],fetches=prediction['m1_fetches']))
    suites=[dict(kind='gates',fixture=str(path.relative_to(ROOT)),fixture_sha256=reference['fixture_sha256'],cases=gate_cases)]
    source=(ROOT/'input/original.sms').read_bytes();live_cases=[]
    live_reference=json.loads((ROOT/'analysis/live_audio_reader_refresh_report.json').read_text())
    for row in live_reference['rows']:
        base=ROOT/f"validation/reader-refresh-live/{row['town']:02x}-{row['mask']:02x}"
        raw=(base/f"{row['region']}-live-envelope-records.bin").read_bytes()
        m1=(base/f"{row['region']}-live-envelope-m1-records.bin").read_bytes()
        assert hashlib.sha256(raw).hexdigest()==row['state_cost_sha256']
        assert hashlib.sha256(m1).hexdigest()==row['M1_R_sha256']
        for n in range(len(raw)//824):
            _,de_in,de_after,_,cost,unwind=struct.unpack_from('<6I',raw,n*824)
            before=raw[n*824+24:n*824+424];after=raw[n*824+424:n*824+824]
            fetches=struct.unpack_from('<I',m1,n*12)[0];assert not unwind
            check(function,source,before,de_in,after,cost,fetches,de_after,(row['town'],row['mask'],row['region'],n))
            live_cases.append(dict(before=list(before),after=list(after),de_in=de_in,de=de_after,tstates=cost,fetches=fetches))
        rows.append(dict(town=row['town'],mask=row['mask'],region=row['region'],cases=len(raw)//824))
    suites.append(dict(kind='live',fixture='input/original.sms',fixture_sha256=hashlib.sha256(source).hexdigest(),cases=live_cases))
    (folder/'cases.json').write_text(json.dumps(suites,separators=(',',':'))+'\n')
    report=dict(gate_cases=len(gate_cases),live_cases=len(live_cases),rows=rows,
                reader_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_reader.c').read_bytes()).hexdigest(),
                limits=['Retained source-verified gates plus exact hashed paid-exit captures, full400/T/M1/DE.',
                        'Other commands/channel boundaries, native68000 and production PSG require further checks.'])
    (ROOT/'analysis/native_audio_reader_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(len(gate_cases),'gate cases and',len(live_cases),'live source reader calls passed',flush=True)


if __name__=='__main__':main()
