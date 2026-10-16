"""Native82C5 T/M1/state/HL/DE/unwind against original-instruction models."""
import ctypes as c,hashlib,json,os,subprocess
from actor_reference import ROOT
from audio_pitch_refresh import pitch_refresh
from validate_audio_pitch_refresh import fixtures
from validate_native_audio_prefix import Work

FIELDS=[0,6,11,12,0x10,0x11,0x12,0x13,0x14,0x15,0x16,0x17]
INPUT_FIELDS=[6,11,12,0x12,0x13,0x14,0x15,0x16,0x17,0x10,0x11,0]
class Output(c.Structure):_fields_=[('hl',c.c_uint16),('unwind',c.c_uint8)]

def make_cases():
    rom=(ROOT/'input/original.sms').read_bytes();records,_,_=fixtures();rows=[]
    for number,record in enumerate(records):
        offset=0x40+(number%7)*0x30;salt=(number*19+17)&255
        initial=bytearray((i*37+salt)&255 for i in range(400))
        for field,value in zip(INPUT_FIELDS,record):initial[offset+field]=value
        de=(number*257)&65535;return_address=[0x8507,0x3003,0,65535][number%4]
        expected=pitch_refresh(rom,initial,offset,return_address,de);reconstructed=bytearray(initial)
        for field in FIELDS:reconstructed[offset+field]=expected['state'][offset+field]
        assert reconstructed==expected['state'],'Sparse fixture lost mutation'
        rows.append(dict(offset=offset,salt=salt,de=de,return_address=return_address,
            input=[initial[offset+i] for i in FIELDS],expected=[expected['state'][offset+i] for i in FIELDS],
            tstates=expected['tstates'],fetches=expected['m1_fetches'],expected_de=expected['de'],
            hl=expected['hl'],unwind=int(expected['unwind']),accepted=1))
    # Vibrato read outside supplied RAM; failure must roll back counters/delta.
    for pointer,rate,phase in [(0xc000,1,2),(0xc000,2,1),(0xdfff,1,1),(0xffff,1,1)]:
        initial=bytearray(400);initial[0x46]=128;initial[0x54]=1;initial[0x55]=rate;initial[0x57]=phase
        initial[0x50]=pointer&255;initial[0x51]=pointer>>8
        # FFFF+1 wraps into available fixed ROM, so it is a valid boundary.
        if pointer==0xffff:
            expected=pitch_refresh(rom,initial,0x40,0x8507,0x9123)
            rows.append(dict(offset=0x40,salt=0,de=0x9123,return_address=0x8507,
                input=[initial[0x40+i] for i in FIELDS],expected=[expected['state'][0x40+i] for i in FIELDS],
                tstates=expected['tstates'],fetches=expected['m1_fetches'],expected_de=expected['de'],
                hl=expected['hl'],unwind=int(expected['unwind']),accepted=1,zero_baseline=True))
        else:
            rows.append(dict(offset=0x40,salt=0,de=0x9123,return_address=0x8507,
                input=[initial[0x40+i] for i in FIELDS],expected=[initial[0x40+i] for i in FIELDS],
                tstates=0,fetches=0,expected_de=0x9123,hl=0,unwind=0,accepted=0,zero_baseline=True))
    return rows

def main():
    folder=ROOT/'validation/native-audio-pitch';folder.mkdir(exist_ok=True);sdk=(ROOT.parents[1]/'work/sgdk').resolve()
    env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),
          str(ROOT/'megadrive/src/source_audio_pitch.c'),str(ROOT/'megadrive/src/source_audio_memory.c'),'-o',str(folder/'source_audio_pitch.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'source_audio_pitch.dll'));function=dll.source_audio_pitch
    function.argtypes=[c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint16),c.POINTER(Work),c.POINTER(Output)];function.restype=c.c_uint8
    rom=(ROOT/'input/original.sms').read_bytes();bank=(c.c_uint8*16384).from_buffer_copy(rom[0x18000:0x1c000]);low=(c.c_uint8*32768).from_buffer_copy(rom[:32768]);rows=make_cases()
    for index,row in enumerate(rows):
        initial=bytearray(400) if row.get('zero_baseline') else bytearray((i*37+row['salt'])&255 for i in range(400));offset=row['offset']
        for field,value in zip(FIELDS,row['input']):initial[offset+field]=value
        expected=bytearray(initial)
        for field,value in zip(FIELDS,row['expected']):expected[offset+field]=value
        state=(c.c_uint8*400).from_buffer_copy(initial);de=c.c_uint16(row['de']);work=Work();output=Output()
        accepted=function(state,offset,low,32768,bank,row['return_address'],c.byref(de),c.byref(work),c.byref(output))
        assert bytes(state)==expected,(index,'state')
        assert (work.tstates,work.fetches,de.value)==(row['tstates'],row['fetches'],row['expected_de']),(index,'work',work.tstates,work.fetches,de.value,row)
        assert (accepted,output.hl,output.unwind)==(row['accepted'],row['hl'],row['unwind']),(index,'outputs',row)
    (folder/'cases.json').write_text(json.dumps(dict(fields=FIELDS,cases=rows),separators=(',',':'))+'\n')
    report=dict(cases=len(rows),rejected_cases=sum(not r['accepted'] for r in rows),caller_unwind_cases=sum(r['unwind'] for r in rows),
                compared_RAM_bytes=400,helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_pitch.c').read_bytes()).hexdigest(),
                limits=['Host native C vs source82C5 state/T/M1/HL/DE/unwind model; seven channel positions.',
                        'Includes mirrored modulation-table RAM, signed/wrap/counter boundaries, four return addresses and synthetic81/82 modes.',
                        'Other source RAM remains uncaptured; no full reader clock or waveform proof.'])
    (ROOT/'analysis/native_audio_pitch_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(len(rows),'native pitch cases passed',flush=True)

if __name__=='__main__':main()
