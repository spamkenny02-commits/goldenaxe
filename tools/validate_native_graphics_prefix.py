"""Native16D0..1706 clock, IRQ/audio, RAM and R from captured SMS entries."""
import ctypes as c
import hashlib
import json
import os
import struct
import subprocess
from actor_reference import ROOT
from validate_native_source_wait import MODULES as BASE_MODULES,WRAPPER as BASE_WRAPPER
from validate_native_patterns import decode,Trace,pattern_rle

MODULES=['source_pattern_clock',*BASE_MODULES]
WRAPPER=BASE_WRAPPER.replace('"source_wait.h"','"source_pattern_clock.h"')
WRAPPER=WRAPPER.replace('u8 wait_case(','u8 graphics_prefix_case(')
WRAPPER=WRAPPER.replace('const u8 *bank6,u16 tile_count','const u8 *bank6,const u8 *patterns,u16 tile_count')
WRAPPER=WRAPPER.replace('SourceWaitOutput result;','const u8 *end;static u8 pixels[16384];u32 hash=2166136261UL;')
WRAPPER=WRAPPER.replace('if(!source_wait(&clock,&ctx,&result) || log.count>16) return 0;',
    'for(n=0;n<sizeof(pixels);n++) pixels[n]=0xa7;\n if(!source_graphics_prefix_class0(&clock,&ctx,patterns,pixels,&end) || log.count>16) return 0;\n for(n=0;n<sizeof(pixels);n++) hash=(hash^pixels[n])*16777619UL;')
WRAPPER=WRAPPER.replace('out[15]=result.taken;','out[15]=end-patterns;out[18]=hash;')

def compile_helper():
    folder=ROOT/'validation/native-graphics-prefix';folder.mkdir(exist_ok=True)
    (folder/'wrapper.c').write_text(WRAPPER);sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ)
    env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared',
          '-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(folder/'wrapper.c')]
    args.extend(str(ROOT/'megadrive/src'/f'{name}.c') for name in MODULES)
    args.extend(['-o',str(folder/'prefix.dll')]);built=subprocess.run(args,env=env,capture_output=True,text=True)
    (folder/'compile.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'prefix.dll'));fn=dll.graphics_prefix_case
    fn.argtypes=[c.POINTER(c.c_uint32),c.c_uint8,*([c.POINTER(c.c_uint8)]*5),c.c_uint16,
                 c.POINTER(c.c_uint32),c.POINTER(c.c_uint32)]
    fn.restype=c.c_uint8;return folder,dll,fn

def main():
    folder,dll,fn=compile_helper();rom=(ROOT/'input/original.sms').read_bytes()
    low=(c.c_uint8*32768).from_buffer_copy(rom[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(rom[0x18000:0x1c000])
    # Decode from the real first class0 pattern resource; retain consumed bytes only.
    expected,used=decode(rom[0x3c010:]);stream=rom[0x3c010:0x3c010+used]
    pattern_work=Trace(stream);assert pattern_rle(pattern_work,0,0x4000)==used
    packed=(c.c_uint8*used).from_buffer_copy(stream);pixel_hash=2166136261
    for value in expected:pixel_hash=((pixel_hash^value)*16777619)&0xffffffff
    cases=[];rows=[]
    for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
        for mask in [0,255]:
            base=ROOT/f'validation/graphics-prefix-refresh/{town:02x}-{mask:02x}'
            if not base.exists():continue
            for region in ['auto','pal']:
                cycles=json.loads((base/f'{region}-cycle-events.json').read_text())
                assert cycles==json.loads((ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json').read_text())
                raw=(base/f'{region}-foreground-phase-records.bin').read_bytes()
                assert raw==(ROOT/f'validation/graphics-prefix-phase/{town:02x}-{mask:02x}/{region}-foreground-phase-records.bin').read_bytes()
                meta=(base/f'{region}-foreground-m1-records.bin').read_bytes();assert len(meta)==len(raw)//800*16
                records=[]
                for n in range(len(raw)//800):
                    pc,time=struct.unpack_from('<2Q',raw,n*800);m1,refresh,_=struct.unpack_from('<Q2I',meta,n*16)
                    records.append(dict(pc=pc,time=time,phase=struct.unpack_from('<12I',raw,n*800+16),
                        ram=raw[n*800+64:n*800+400],sound=raw[n*800+400:n*800+800],m1=m1,refresh=refresh))
                start=next(e[2] for e in cycles if e[1]==0x16d0 and e[4]==target)
                first=next(r for r in records if r['pc']==0x16d0 and r['time']==start)
                last=next(r for r in records if r['pc']==0x1706 and r['time']>start)
                phase=first['phase'];ram=(c.c_uint8*336).from_buffer_copy(first['ram']);audio=(c.c_uint8*400).from_buffer_copy(first['sound'])
                output=(c.c_uint32*19)();events=(c.c_uint32*96)();tag=(town,mask,region)
                assert fn((c.c_uint32*12)(*phase),first['refresh'],ram,audio,low,bank,packed,0,output,events),(tag,'rejected')
                assert bytes(audio)==last['sound'],(tag,'audio')
                assert all(ram[i]==last['ram'][i] for i in range(336) if i not in [0x1b,0x20,0x21,0x22,0x23]),(tag,'RAM')
                end_phase=last['phase'];delta=((end_phase[0]-end_phase[2]+0x80000000)&0xffffffff)-0x80000000
                assert output[0]==(end_phase[1]*3420+delta)%(phase[3]*3420) and output[2]==last['time']-start,(tag,'phase/time',list(output))
                assert output[10]==last['refresh'] and output[4]+output[6]==last['m1']-first['m1'],(tag,'M1/R',list(output),last['m1']-first['m1'])
                assert (output[11],output[13],output[14])==(end_phase[8],end_phase[10],1) and not output[12] and not output[16],(tag,'latches')
                observed=json.loads((base/f'{region}-audio-irq-events.json').read_text())
                accepted=[(e[2]-start,False) for e in observed if e[1]==0x137 and start<e[2]<last['time']]
                actual=[(events[n*6],bool(events[n*6+5])) for n in range(output[7])]
                assert accepted==actual,(tag,'IRQ entries',accepted,actual)
                assert output[15]==used and output[18]==pixel_hash,(tag,'pixels/end')
                # 69 M1 precede032A, independently counted from prefix opcodes.
                assert output[4]==pattern_work.fetches+69,(tag,'pattern/prefix M1')
                cases.append(dict(phase=list(phase),refresh=first['refresh'],ram=list(first['ram']),audio=list(first['sound']),
                                  expected_ram=list(ram),expected_audio=list(audio),expected=list(output),events=list(events[:output[7]*6])))
                rows.append(dict(town=town,mask=mask,region=region,foreground_tstates=output[3],foreground_M1=output[4],IRQ_M1=output[6],
                                 IRQs=output[7],wall_master_cycles=output[2],entry_R=first['refresh'],exit_R=output[10],pattern_M1=pattern_work.fetches))
                print(tag,'native 16D0..1706 source phase/R/IRQ/state exact',flush=True)
    assert len(cases)==24
    (folder/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    report=dict(cases=len(cases),rows=rows,source_sha256=hashlib.sha256(rom).hexdigest(),
                helpers={name:hashlib.sha256((ROOT/'megadrive/src'/f'{name}.c').read_bytes()).hexdigest() for name in MODULES},
                md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),production_clock_wired=False,
                limits=['One captured16D0 entry per route; subsequent1706 phase/R/M1,331RAM,400audio,IRQ entry offsets checked against original source records.',
                        'Pixels/end independently decoded; physical VRAM upload timing/contention, other graphics classes and global entry-phase propagation remain pending.'])
    (ROOT/'analysis/native_graphics_prefix_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
