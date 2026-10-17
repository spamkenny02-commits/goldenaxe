"""Batched032A against immutable scalar C: complete clocks,IRQ logs,bytes/state."""
import ctypes as c
import hashlib
import json
import os
import subprocess
from actor_reference import ROOT
from validate_native_graphics_prefix import MODULES,WRAPPER
from validate_native_patterns import vectors

def main():
    folder=ROOT/'validation/pattern-clock-batch';folder.mkdir(exist_ok=True)
    reference=ROOT/'analysis/native-room-finish-v0198/megadrive/src/source_pattern_clock.c'
    text=reference.read_text().replace('source_graphics_prefix_class0(','source_graphics_prefix_scalar(')
    (folder/'reference.c').write_text(text)
    for name,function in [('fast','source_graphics_prefix_class0'),('scalar','source_graphics_prefix_scalar'),('planned','source_graphics_prefix_class0_planned')]:
        wrapper=WRAPPER.replace('graphics_prefix_case(',f'prefix_{name}_case(').replace('events[16][6]','events[64][6]').replace('>=16','>=64').replace('>16','>64')
        wrapper=wrapper.replace('u32 *out,u32 *events)','u32 *out,u32 *events,u8 *pixel_output)')
        wrapper=wrapper.replace('return 1;\n}', 'for(n=0;n<16384;n++) pixel_output[n]=pixels[n];\n return 1;\n}')
        if name=='planned':
            wrapper=wrapper.replace('#include "source_pattern_clock.h"','#include "source_pattern_clock.h"\n#include "source_pattern_plan_generated.h"').replace('source_graphics_prefix_class0(&clock,&ctx,patterns,pixels,&end)','source_graphics_prefix_class0_planned(&clock,&ctx,patterns,pixels,&end,&gaw_class0_pattern_plan)')
        if name=='scalar':
            wrapper=wrapper.replace('source_graphics_prefix_class0(',function+'(')
            anchor='#include "source_pattern_clock.h"'
            wrapper=wrapper.replace(anchor,anchor+'\nu8 source_graphics_prefix_scalar(SourceClock*,SourceIrqContext*,const u8*,u8*,const u8**);')
        (folder/f'{name}.c').write_text(wrapper)
    sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src')]
    args.extend(str(folder/f'{name}.c') for name in ['reference','fast','scalar','planned'])
    args.extend(str(ROOT/'megadrive/src'/f'{name}.c') for name in MODULES);args.extend(['-o',str(folder/'batch.dll')])
    built=subprocess.run(args,env=env,capture_output=True,text=True);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'batch.dll'));functions=[dll.prefix_fast_case,dll.prefix_scalar_case,dll.prefix_planned_case]
    for function in functions:
        function.argtypes=[c.POINTER(c.c_uint32),c.c_uint8,*([c.POINTER(c.c_uint8)]*5),c.c_uint16,c.POINTER(c.c_uint32),c.POINTER(c.c_uint32),c.POINTER(c.c_uint8)]
        function.restype=c.c_uint8
    rom=(ROOT/'input/original.sms').read_bytes();low=(c.c_uint8*32768).from_buffer_copy(rom[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(rom[0x18000:0x1c000])
    contexts=json.loads((ROOT/'analysis/native-room-finish-v0198/validation/native-room-finish/cases.json').read_text())
    live=contexts[:];stress=[]
    for lines in [262,313]:
        base=next(row for row in contexts if row['phase'][3]==lines)
        for raster in [0,193*3420-1,193*3420,193*3420+1,lines*3420-1,lines*3420-1000]:
            for refresh in [0,127,128,255]:
                for iff,pending,blocked in [(1,0,0),(1,1,0),(0,1,0),(1,1,1)]:
                    phase=base['phase'][:];phase[0]=raster%3420;phase[1]=raster//3420;phase[2]=0;phase[8:11]=[iff,blocked,pending]
                    stress.append(dict(base,phase=phase,refresh=refresh))
    streams=list(vectors());real=streams[0][0];checked=0;digest=hashlib.sha256()
    # Long sequences of short commands exercise windows around the NTSC
    # frame budget and the65535T PAL cap, with literal/repeat alternation.
    window_streams=[]
    for length in [2,127,294,295,296,324,325,512,1024]:
        for mode in [0,1,2]:
            packed=bytearray()
            for plane in range(4):
                for n in range(length):
                    literal=mode==1 or (mode==2 and n&1)
                    packed.extend([0x81 if literal else 1,(n*37+plane)&255])
                packed.append(0)
            window_streams.append(bytes(packed))
    def check(row,stream,planned=False):
        nonlocal checked
        packed=(c.c_uint8*len(stream)).from_buffer_copy(stream);results=[]
        for function in (functions if planned else functions[:2]):
            ram=(c.c_uint8*336)(*row['ram']);audio=(c.c_uint8*400)(*row['audio']);out=(c.c_uint32*19)();events=(c.c_uint32*384)();pixels=(c.c_uint8*16384)()
            assert function((c.c_uint32*12)(*row['phase']),row['refresh'],ram,audio,low,bank,packed,0,out,events,pixels),('rejected',checked)
            results.append((bytes(ram),bytes(audio),list(out),list(events[:out[7]*6]),bytes(pixels)))
        assert all(result==results[0] for result in results[1:]),('batch/scalar mismatch',checked,row['phase'],row['refresh'])
        digest.update(results[0][-1]);checked+=1
    for row in live+stress:check(row,real,planned=True)
    for n,(stream,address) in enumerate(streams[1:]):
        for lines in [262,313]:
            row=next(r for r in stress if r['phase'][3]==lines and r['phase'][8]==1 and r['phase'][10]==0)
            phase=row['phase'][:];phase[0]=(193*3420-(n%29+1))%3420;phase[1]=(193*3420-(n%29+1))//3420
            check(dict(row,phase=phase,refresh=n&255),stream)
    for number,stream in enumerate(window_streams):
        for lines in [262,313]:
            base=next(row for row in contexts if row['phase'][3]==lines)
            for raster in [0,193*3420-1,193*3420,lines*3420-1]:
                phase=base['phase'][:];phase[0]=raster%3420;phase[1]=raster//3420;phase[2]=0
                check(dict(base,phase=phase,refresh=number*9&255),stream)
    report=dict(planned_asset_cases=len(live)+len(stress),plan_sha256=hashlib.sha256((ROOT/'megadrive/src/source_pattern_plan_generated.h').read_bytes()).hexdigest(),cases=checked,live=len(live),phase_stress=len(stress),command_window_cases=len(window_streams)*8,synthetic_streams=len(streams)-1,
                reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),module_sha256=hashlib.sha256((ROOT/'megadrive/src/source_pattern_clock.c').read_bytes()).hexdigest(),
                output_digest=digest.hexdigest(),limits=['Host pairwise comparison with immutable pre-batch scalar C, all16384 pixel bytes,336RAM,400audio,full clock andIRQ log.',
                'Real class0 input plus generated RLE, page crossings/count256, shifted VINT/pending/IFF/EI-delay/R; long2..1024-command planes test frame/window caps and alternating modes. Full source/68000 chain proof is separate.'])
    (ROOT/'analysis/pattern_clock_batch_report.json').write_text(json.dumps(report,indent=2)+'\n');print(report)

if __name__=='__main__':main()
