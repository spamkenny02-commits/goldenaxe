"""Native84C7 composition versus retained source-verified state/T/M1 oracle."""
import ctypes as c
import hashlib
import json
import os
import subprocess
from actor_reference import ROOT
from audio_tone_channel_refresh import tone_channel_refresh
from validate_native_audio_sequence import Output
from validate_native_audio_prefix import Work

MODULES = ['source_audio_tone', 'source_audio_sequence', 'source_audio_priority',
           'source_audio_memory', 'source_audio_envelope', 'source_audio_pitch']
OFFSETS = [0x43,0x44,0x40,0x42,0x4a,0x46,0x47,0x4e,0x65,0x3e,0x3f]


def compile_helper():
    folder = ROOT/'validation/native-audio-tone'
    folder.mkdir(exist_ok=True)
    sdk = (ROOT.parents[1]/'work/sgdk').resolve()
    env = dict(os.environ)
    env['PATH'] = 'C:/msys64/ucrt64/bin;'+env['PATH']
    args = ['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared',
            '-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src')]
    args.extend(str(ROOT/'megadrive/src'/f'{name}.c') for name in MODULES)
    args.extend(['-o',str(folder/'source_audio_tone.dll')])
    built = subprocess.run(args,env=env,capture_output=True,text=True)
    (folder/'compile.log').write_text(built.stdout+built.stderr)
    assert built.returncode == 0,built.stderr
    dll = c.CDLL(str(folder/'source_audio_tone.dll'))
    function = dll.source_audio_tone
    function.argtypes = [c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.c_uint16,
                        c.POINTER(c.c_uint8),c.POINTER(c.c_uint16),c.POINTER(Work),c.POINTER(Output)]
    function.restype = c.c_uint8
    return folder,dll,function


def main():
    folder,dll,function = compile_helper()
    reference = json.loads((ROOT/'analysis/audio_tone_channel_refresh_report.json').read_text())
    path = ROOT/'validation/audio-tone-channel/tone-channel/source.sms'
    image = path.read_bytes()
    assert hashlib.sha256(image).hexdigest() == reference['fixture_sha256']
    low = (c.c_uint8*32768).from_buffer_copy(image[:32768])
    bank = (c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000])
    seed = image[0x3430:0x3430+400]
    rows = []
    for number in range(reference['cases']//2):
        inputs = image[0x80000+number*16:0x80000+(number+1)*16]
        initial = bytearray(seed)
        for offset,value in zip(OFFSETS,inputs):initial[offset] = value
        prediction = tone_channel_refresh(image,initial,0x40,0x8a0b)
        state = (c.c_uint8*400).from_buffer_copy(initial)
        work = Work();output = Output();de = c.c_uint16(0x8a0b)
        assert function(state,0x40,low,32768,bank,c.byref(de),c.byref(work),c.byref(output)) and not output.error,(number,'rejected')
        assert bytes(state) == prediction['state'],(number,'state')
        assert (work.tstates,work.fetches,de.value,output.unwind) == (prediction['tstates'],prediction['m1_fetches'],prediction['de'],0),(number,'work',work.tstates,work.fetches,de.value,prediction)
        rows.append(dict(input=list(inputs),patches=[(i,v) for i,v in enumerate(prediction['state']) if v!=initial[i]],
                         tstates=work.tstates,fetches=work.fetches,de_in=0x8a0b,de=de.value,unwind=0))
    suites = [dict(kind='retained',fixture=str(path.relative_to(ROOT)),fixture_sha256=reference['fixture_sha256'],
                   seed=list(seed),offsets=OFFSETS,offset=64,cases=rows)]
    (folder/'cases.json').write_text(json.dumps(suites,separators=(',',':'))+'\n')
    report = dict(cases=len(rows),tone_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_tone.c').read_bytes()).hexdigest(),
                  compared_RAM_bytes=400,limits=['Retained source-verified84C7 fixture, full state/T/M1/DE and consumed unwinds.',
                  'PSG writes, other slots and fresh command/context boundaries require direct source/production checks.'])
    (ROOT/'analysis/native_audio_tone_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(len(rows),'native tone cases passed',flush=True)


if __name__ == '__main__':main()
