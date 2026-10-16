"""Compare native 80FF state/T/M1 and explicit PSG side effects to audited paths."""
import ctypes as c, hashlib, itertools, json, os, subprocess
from actor_reference import ROOT
from audio_dispatch_refresh import dispatch_refresh
from validate_native_audio_prefix import Work

class Output(c.Structure): _fields_=[('mute',c.c_uint8),('count',c.c_uint8),('writes',c.c_uint8*4)]
UNSUPPORTED=[0x8e,0x8f,0xad,0xae,0xaf,0xb4]

def make_cases():
    rom=(ROOT/'input/original.sms').read_bytes();rows=[]
    def add(command,latch,flags,salt):
        initial=bytearray((i*37+salt)&255 for i in range(400))
        initial[5]=command;initial[15]=latch;initial[0x160]=flags
        if command in UNSUPPORTED:
            expected=dict(state=initial,tstates=0,m1_fetches=0);mute=0;writes=[]
        else:
            expected=dispatch_refresh(rom,initial);writes=[]
            mute=int(command<128 or 0x81<=command<=0x8d or command==0xb1 or command>=0xb5)
            if 0x90<=command<=0xac:
                bank=rom[0x18000:0x1c000];index=0xb30+(command-0x90)*2
                header=(bank[index]|bank[index+1]<<8)-0x8000;state=bytearray(initial)
                for n in range(bank[header]):
                    h=header+1+n*9;channel=bank[h+1]
                    if channel==0xc0 and not state[0x160]&64:
                        state[0x160]|=4;writes.append(255)
                    target=0x100 if channel==0xa0 else 0x130 if channel==0xc0 else 0x160
                    state[target:target+9]=bank[h:h+9]
            elif command==0xb3 and not latch&128:
                writes=[(initial[(0x160 if latch else 0x130)+1]+31)&255]
        rows.append(dict(command=command,latch=latch,flags=flags,salt=salt,
                         accepted=int(command not in UNSUPPORTED),mute=mute,writes=writes,
                         expected=list(expected['state']),tstates=expected['tstates'],fetches=expected['m1_fetches']))
    for command,variant in itertools.product(range(256),range(8)):
        add(command,[0,1,127,128,255,64,3,129][variant],
            [0,64,128,192,255,4,16,132][variant],(command*19+variant*17)&255)
    for latch in range(256): add(0xb3,latch,(latch*3)&255,(latch*7)&255)
    return rows

def main():
    folder=ROOT/'validation/native-audio-dispatch';folder.mkdir(exist_ok=True)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),
          str(ROOT/'megadrive/src/source_audio_dispatch.c'),str(ROOT/'megadrive/src/source_audio_prefix.c'),'-o',str(folder/'source_audio_dispatch.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'source_audio_dispatch.dll'));function=dll.source_audio_dispatch
    function.argtypes=[c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),c.POINTER(Work),c.POINTER(Output)];function.restype=c.c_uint8
    bank=(c.c_uint8*16384).from_buffer_copy((ROOT/'input/original.sms').read_bytes()[0x18000:0x1c000]);rows=make_cases()
    for index,row in enumerate(rows):
        initial=bytearray((i*37+row['salt'])&255 for i in range(400))
        initial[5]=row['command'];initial[15]=row['latch'];initial[0x160]=row['flags']
        state=(c.c_uint8*400).from_buffer_copy(initial);work=Work();output=Output()
        accepted=function(state,bank,c.byref(work),c.byref(output))
        assert list(state)==row['expected'],(index,'state',hex(row['command']))
        assert (work.tstates,work.fetches)==(row['tstates'],row['fetches']),(index,'work',hex(row['command']),work.tstates,work.fetches,row['tstates'],row['fetches'])
        assert (accepted,output.mute,list(output.writes[:output.count]))==(row['accepted'],row['mute'],row['writes']),(index,'PSG')
    (folder/'cases.json').write_text(json.dumps(rows,separators=(',',':'))+'\n')
    report=dict(cases=len(rows),rejected_cases=sum(not r['accepted'] for r in rows),compared_RAM_bytes=400,
                helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_audio_dispatch.c').read_bytes()).hexdigest(),
                original_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),
                production_integrated=False,limits=['Host compiled C vs previously audited Python source state/T/M1 models.',
                'PSG mute/write decisions derived from source branches; waveforms and full reader clock not covered.',
                'Six unaudited commands reject without mutation; their source paths remain to be implemented.'])
    (ROOT/'analysis/native_audio_dispatch_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(len(rows),'native dispatch state/work/PSG cases passed',flush=True)

if __name__=='__main__':main()
