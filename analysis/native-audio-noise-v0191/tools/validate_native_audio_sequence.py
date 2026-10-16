"""Native8357 vs retained source-verified notes/commands/termination/ownership."""
import ctypes as c,hashlib,json,os,subprocess
from actor_reference import ROOT
from audio_note_sequence_refresh import note_sequence_refresh
from validate_native_audio_prefix import Work

SPECS={
 'notes':('audio-note-sequence',[0x43,0x44,0x40,0x42,0x45,0x47,0x4d,0x49,0x67,0x6e,0x6f]),
 'commands':('audio-note-commands',[0x43,0x44,0x40,0x41,0x42,0xb,0x12,0x66]),
 'termination':('audio-note-sequence',[0x43,0x44,0x40,0x41,0x160,0x130,0x0e]),
 'ownership':('audio-note-sequence',[0x43,0x44,0x40,0x41,0xf,0x130])}
class Output(c.Structure):_fields_=[('de',c.c_uint16),('count',c.c_uint16),('unwind',c.c_uint8),('error',c.c_uint8),('writes',c.c_uint8*512)]

def compile_helper():
    folder=ROOT/'validation/native-audio-sequence';folder.mkdir(exist_ok=True);sdk=(ROOT.parents[1]/'work/sgdk').resolve()
    env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src')]
    args.extend(str(ROOT/'megadrive/src'/f'{name}.c') for name in ['source_audio_sequence','source_audio_priority','source_audio_memory'])
    args.extend(['-o',str(folder/'source_audio_sequence.dll')])
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'source_audio_sequence.dll'));function=dll.source_audio_sequence
    function.argtypes=[c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.POINTER(Work),c.POINTER(Output)];function.restype=c.c_uint8
    return folder,dll,function

def main():
    folder,dll,function=compile_helper();suites=[];dirty=set();total=0
    original=(ROOT/'input/original.sms').read_bytes()
    for kind,(directory,offsets) in SPECS.items():
        reference=json.loads((ROOT/f'analysis/audio_note_{kind}_refresh_report.json').read_text())
        image=(ROOT/f'validation/{directory}/{kind}/source.sms').read_bytes()
        assert hashlib.sha256(image).hexdigest()==reference['fixture_sha256'] and image[0x18000:0x1c000]==original[0x18000:0x1c000]
        low=(c.c_uint8*32768).from_buffer_copy(image[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000]);seed=image[0x3430:0x3430+400];cases=[]
        for number in range(reference['cases']//2):
            inputs=image[0x80000+number*16:0x80000+(number+1)*16];initial=bytearray(seed)
            for offset,value in zip(offsets,inputs):initial[offset]=value
            prediction=note_sequence_refresh(image,initial);state=(c.c_uint8*400).from_buffer_copy(initial);work=Work();output=Output()
            accepted=function(state,0x40,low,32768,bank,c.byref(work),c.byref(output))
            assert accepted and not output.error,(kind,number,'rejected',output.error)
            assert bytes(state)==prediction['state'],(kind,number,'state',[(i,a,b) for i,(a,b) in enumerate(zip(bytes(state),prediction['state'])) if a!=b][:10])
            assert (work.tstates,work.fetches,output.de,bool(output.unwind))==(prediction['tstates'],prediction['m1_fetches'],prediction['de'],prediction.get('unwind',False)),(kind,number,'work',work.tstates,work.fetches,prediction)
            assert output.count<=512
            patches=[(i,value) for i,value in enumerate(prediction['state']) if value!=initial[i]];dirty.update(i for i,_ in patches)
            expected=bytearray(initial)
            for i,value in patches:expected[i]=value
            assert expected==prediction['state']
            cases.append(dict(input=list(inputs),patches=patches,tstates=work.tstates,fetches=work.fetches,de=output.de,unwind=output.unwind))
        suites.append(dict(kind=kind,fixture=str((ROOT/f'validation/{directory}/{kind}/source.sms').relative_to(ROOT)),
                           fixture_sha256=reference['fixture_sha256'],offsets=offsets,cases=cases))
        total+=len(cases);print(kind,len(cases),'native8357 state/T/M1/DE/unwind exact',flush=True)
    fields=sorted(dirty);assert len(fields)<=255
    for suite in suites:
        for row in suite['cases']:row['patches']=[item for offset,value in row['patches'] for item in [fields.index(offset),value]]
    (folder/'cases.json').write_text(json.dumps(dict(fields=fields,suites=suites),separators=(',',':'))+'\n')
    report=dict(cases=total,suites={s['kind']:len(s['cases']) for s in suites},compared_RAM_bytes=400,
                helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_sequence.c').read_bytes()).hexdigest(),
                limits=['Host native C vs retained source-verified8357 models/fixtures; all400 bytes,T/M1,DE/unwind.',
                        'PSG write lists are not independently compared in this component test; actual production PSG regressions required.',
                        'R-dependent commands andsource-restoration nonzero require separate evidence; no full native clock claim.'])
    (ROOT/'analysis/native_audio_sequence_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
