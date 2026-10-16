"""Native864F/8679 vs retained original-instruction noise/envelope models."""
import ctypes as c,hashlib,json,os,subprocess
from actor_reference import ROOT
from audio_noise_channel_refresh import noise_channel_refresh
from audio_noise_note_refresh import noise_note_refresh
from validate_audio_noise_note import records
from validate_native_audio_sequence import Output
from validate_native_audio_prefix import Work

MODULES=['source_audio_noise','source_audio_sequence','source_audio_priority','source_audio_memory','source_audio_envelope']
OFFSETS=[0xd3,0xd4,0xd0,0xd2,0xda,0xd7,0xef,0x3e,0x3f,0xf7]

def compile_helper():
    folder=ROOT/'validation/native-audio-noise';folder.mkdir(exist_ok=True);sdk=(ROOT.parents[1]/'work/sgdk').resolve()
    env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src')]
    args.extend(str(ROOT/'megadrive/src'/f'{name}.c') for name in MODULES);args.extend(['-o',str(folder/'source_audio_noise.dll')])
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'source_audio_noise.dll'));channel=dll.source_audio_noise;selector=dll.source_audio_noise_note
    channel.argtypes=[c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.POINTER(c.c_uint16),c.POINTER(Work),c.POINTER(Output)]
    selector.argtypes=[c.POINTER(c.c_uint8),c.c_uint16,c.c_uint8,c.POINTER(Work),c.POINTER(Output)]
    channel.restype=selector.restype=c.c_uint8;return folder,dll,channel,selector

def main():
    folder,dll,channel,selector=compile_helper();suites=[]
    reference=json.loads((ROOT/'analysis/audio_noise_channel_refresh_report.json').read_text());path=ROOT/'validation/audio-noise-channel/noise-channel/source.sms';image=path.read_bytes()
    assert hashlib.sha256(image).hexdigest()==reference['fixture_sha256']
    low=(c.c_uint8*32768).from_buffer_copy(image[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000]);seed=image[0x3430:0x3430+400];rows=[]
    for number in range(reference['cases']//2):
        inputs=image[0x80000+number*16:0x80000+(number+1)*16];initial=bytearray(seed)
        for offset,value in zip(OFFSETS,inputs):initial[offset]=value
        prediction=noise_channel_refresh(image,initial,0xd0,0x8a0b);state=(c.c_uint8*400).from_buffer_copy(initial);work=Work();output=Output();de=c.c_uint16(0x8a0b)
        assert channel(state,0xd0,low,32768,bank,c.byref(de),c.byref(work),c.byref(output)) and not output.error
        assert bytes(state)==prediction['state'],(number,'state')
        assert (work.tstates,work.fetches,de.value,output.unwind)==(prediction['tstates'],prediction['m1_fetches'],prediction['de'],0),(number,'work',work.tstates,work.fetches,prediction)
        rows.append(dict(input=list(inputs),patches=[(i,v) for i,v in enumerate(prediction['state']) if v!=initial[i]],tstates=work.tstates,fetches=work.fetches,de_in=0x8a0b,de=de.value,unwind=0))
    suites.append(dict(kind='channel',api=0,fixture=str(path.relative_to(ROOT)),fixture_sha256=reference['fixture_sha256'],seed=list(seed),offsets=OFFSETS,cases=rows))
    rows=[];seed=bytearray((i*37+17)&255 for i in range(400));seed[0xd1]=0xe0
    for note,flags,volume,bias in records():
        initial=bytearray(seed);inputs=[note,flags,volume,bias]
        for offset,value in zip([0x3e,0xd0,0x18,0x17],inputs):initial[offset]=value
        prediction=noise_note_refresh(initial,note,0xd0);state=(c.c_uint8*400).from_buffer_copy(initial);work=Work();output=Output()
        assert selector(state,0xd0,note,c.byref(work),c.byref(output)) and not output.error
        assert bytes(state)==prediction['state'] and (work.tstates,work.fetches)==(prediction['tstates'],prediction['m1_fetches'])
        expected=[] if flags&4 else [prediction['state'][19] if note&63 else 255]
        assert list(output.writes[:output.count])==expected
        rows.append(dict(input=inputs+[0]*12,patches=[(i,v) for i,v in enumerate(prediction['state']) if v!=initial[i]],tstates=work.tstates,fetches=work.fetches,de_in=0,de=0,unwind=0,writes=expected))
    original=ROOT/'input/original.sms'
    suites.append(dict(kind='selector',api=1,fixture=str(original.relative_to(ROOT)),fixture_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),seed=list(seed),offsets=[0x3e,0xd0,0x18,0x17],cases=rows))
    (folder/'cases.json').write_text(json.dumps(suites,separators=(',',':'))+'\n')
    report=dict(cases=sum(len(s['cases']) for s in suites),suites={s['kind']:len(s['cases']) for s in suites},compared_RAM_bytes=400,
                noise_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_noise.c').read_bytes()).hexdigest(),
                sequence_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_sequence.c').read_bytes()).hexdigest(),
                limits=['Retained source-verified864F matrix and8679 models; state/T/M1/DE/unwind; selector PSG decisions.',
                        'New noise commands/whole-reader exits require fresh source evidence; waveform/full native clock not covered.'])
    (ROOT/'analysis/native_audio_noise_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['cases'],'native noise cases passed',report['suites'],flush=True)

if __name__=='__main__':main()
