"""Native81F8/8211 against source-verified queue and standalone models."""
import ctypes as c,hashlib,itertools,json,os,subprocess
from actor_reference import ROOT
from audio_priority_effect_refresh import priority_effect_refresh
from audio_restore_effect_refresh import restore_effect_refresh
from validate_native_audio_prefix import Work
from validate_native_audio_dispatch import Output

FIELDS=[9,16,14,15,0x1a,0x1b,0xa0,0xd0]+list(range(0x130,0x13b))+list(range(0x157,0x15a))+list(range(0x160,0x16b))+list(range(0x187,0x18a))

def make_cases():
    rom=(ROOT/'input/original.sms').read_bytes();rows=[]
    def add(kind,updates,salt,de=0x9123,accepted=1):
        initial=bytearray((i*37+salt)&255 for i in range(400))
        for offset,value in updates.items():initial[offset]=value
        if not accepted:expected=dict(state=initial,tstates=0,m1_fetches=0,de=de,writes=[])
        elif kind:expected=restore_effect_refresh(rom,initial,initial[14],de)
        else:
            expected=priority_effect_refresh(rom,initial)
            expected['writes']=([] if (not initial[9] or initial[15]&128) else
                                [(initial[(0x160 if initial[15] else 0x130)+1]+31)&255])
        reconstructed=bytearray(initial)
        for offset in FIELDS:reconstructed[offset]=expected['state'][offset]
        assert reconstructed==expected['state'],'Sparse fixture lost mutation'
        rows.append(dict(kind=kind,salt=salt,de=de,accepted=accepted,input=[initial[i] for i in FIELDS],
                         expected=[expected['state'][i] for i in FIELDS],tstates=expected['tstates'],
                         fetches=expected['m1_fetches'],expected_de=expected['de'],writes=expected['writes']))
    for request,priority,current,latch,tone,noise in itertools.product([0,128]+list(range(0x90,0xad)),[0,1,127,255],
            [0x90,0x94,0xac],[0,1,127,128,255],[0,128,192],[0,128,192]):
        add(0,{9:request,16:priority,14:current,15:latch,0x130:tone,0x160:noise},(request*7+priority+latch+noise)&255)
    for command,latch,tone,noise,de in itertools.product(range(0x90,0xad),[0,1,127,128,255],[0,128,192],[0,128,192],[0,0x9123,0xde0a,65535]):
        add(1,{14:command,15:latch,0x130:tone,0x160:noise},(command*11+latch+noise)&255,de)
    for value in [1,127,129,143,173,176,255]:
        add(0,{9:value,14:0x90},value,accepted=0)
        add(1,{14:value},value,accepted=0)
    add(0,{9:0x90,16:255,14:0},255,accepted=0)
    return rows

def main():
    folder=ROOT/'validation/native-audio-priority';folder.mkdir(exist_ok=True);sdk=(ROOT.parents[1]/'work/sgdk').resolve()
    env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(ROOT/'megadrive/src/source_audio_priority.c'),'-o',str(folder/'source_audio_priority.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'source_audio_priority.dll'));functions=[dll.source_audio_priority,dll.source_audio_restore]
    for kind,function in enumerate(functions):
        function.argtypes=[c.POINTER(c.c_uint8),c.POINTER(c.c_uint8)]+([c.c_uint8] if kind else [])+[c.POINTER(c.c_uint16),c.POINTER(Work),c.POINTER(Output)];function.restype=c.c_uint8
    bank=(c.c_uint8*16384).from_buffer_copy((ROOT/'input/original.sms').read_bytes()[0x18000:0x1c000]);rows=make_cases()
    for index,row in enumerate(rows):
        initial=bytearray((i*37+row['salt'])&255 for i in range(400))
        for offset,value in zip(FIELDS,row['input']):initial[offset]=value
        expected=bytearray(initial)
        for offset,value in zip(FIELDS,row['expected']):expected[offset]=value
        state=(c.c_uint8*400).from_buffer_copy(initial);de=c.c_uint16(row['de']);work=Work();output=Output();kind=row['kind']
        accepted=functions[kind](state,bank,*([initial[14]] if kind else []),c.byref(de),c.byref(work),c.byref(output))
        assert bytes(state)==expected,(index,kind,'state')
        assert (work.tstates,work.fetches,de.value)==(row['tstates'],row['fetches'],row['expected_de']),(index,kind,'work',work.tstates,work.fetches,de.value,row)
        assert (accepted,output.mute,list(output.writes[:output.count]))==(row['accepted'],0,row['writes']),(index,'PSG')
    (folder/'cases.json').write_text(json.dumps(dict(fields=FIELDS,cases=rows),separators=(',',':'))+'\n')
    report=dict(cases=len(rows),queue_cases=sum(r['kind']==0 for r in rows),restore_cases=sum(r['kind']==1 for r in rows),
                rejected_cases=sum(not r['accepted'] for r in rows),compared_RAM_bytes=400,
                helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_priority.c').read_bytes()).hexdigest(),
                limits=['Host C state/T/M1/DE and explicit PSG-write decisions; sparse fixtures losslessly reconstruct all400 bytes.',
                        'Queue uses existing source-verified model; standalone8211 requires its separate direct source validation.',
                        'Invalid requests reject; no full reader or physical waveform claim.'])
    (ROOT/'analysis/native_audio_priority_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(len(rows),'native priority/restoration host cases passed',flush=True)

if __name__=='__main__':main()
