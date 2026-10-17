"""Original1E4E output bytes and foreground work across byte-valued HUD inputs."""
import contextlib
import ctypes as c
import hashlib
import io
import json
import os
import struct
import subprocess
from actor_reference import ROOT
from run_core import run
from validate_hud_loading_cost import ROWS,generate
from validate_native_room_hud import MODULES
from validate_native_patterns import Trace
from map_hud_phase import hud as model_hud

FORMAT=struct.Struct('<16s2I768s768s')
WRAPPER='''#include "source_room_hud.h"
u8 hud_value_case(const u8 *hud,const u8 *bank4,const u8 *low,u8 *memory,u32 *out)
{
 SourceClock clock;SourceIrqContext ctx={0};SourceWorldMapData map;
 static u8 tilemap[1536],ram[336],audio[400];u16 n;
 if(!source_clock_init(&clock,262,0,0,0,0,0)) return 0;
 for(n=0;n<80;n++) ram[n]=0;
 for(n=0;n<256;n++) {tilemap[1280+n]=memory[n];ram[80+n]=memory[512+n];}
 ctx.ram=ram;ctx.audio=audio;ctx.low=low;ctx.low_bytes=32768;ctx.input.lines=262;ctx.input.reset_mask=16;
 map.tilemap=tilemap;map.cells=memory+256;
 if(!source_hud_prepare(&clock,&ctx,&map,bank4,hud)) return 0;
 for(n=0;n<256;n++) {memory[n]=tilemap[1280+n];memory[512+n]=ram[80+n];}
 out[0]=clock.foreground_tstates;out[1]=clock.foreground_m1;return 1;
}
'''

def compile_helper():
    folder=ROOT/'validation/native-hud-values';folder.mkdir(exist_ok=True);(folder/'wrapper.c').write_text(WRAPPER)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(folder/'wrapper.c')]
    args.extend(str(ROOT/'megadrive/src'/f'{name}.c') for name in MODULES);args.extend(['-o',str(folder/'hud.dll')])
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'hud.dll'));fn=dll.hud_value_case
    fn.argtypes=[*([c.POINTER(c.c_uint8)]*4),c.POINTER(c.c_uint32)];fn.restype=c.c_uint8
    return folder,dll,fn

def main():
    folder,dll,fn=compile_helper();fixture,_=generate();rom=(ROOT/'input/original.sms').read_bytes()
    low=(c.c_uint8*32768).from_buffer_copy(rom[:32768]);bank4=(c.c_uint8*16384).from_buffer_copy(rom[0x10000:0x14000])
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_loader_libretro.dll';observer=c.CDLL(str(core))
    observer.gaw_timing_count.restype=c.c_uint;observer.gaw_timing_events.restype=c.POINTER(c.c_uint64)
    vectors=bytearray();regions=[]
    for region in ['auto','pal']:
        observer.gaw_timing_reset();previous=[0];starts={};costs={};checked={};done=[];memory=(c.c_uint8*768)()
        def observe(frame,ram):
            case=int.from_bytes(ram[:2],'little');count=observer.gaw_timing_count();events=observer.gaw_timing_events()
            for n in range(previous[0],count):
                pc,time,irq=[events[n*8+j] for j in range(3)]
                if pc==0x1de5:starts[case]=(time,irq)
                elif pc==0x1de8:
                    a=starts[case];costs[case]=((time-a[0])-(irq-a[1]))//15-17
            previous[0]=count
            if ram[4]:done.append(frame)
            if ram[2] and case not in checked:
                assert case==len(checked) and case<len(ROWS),(region,case,len(checked))
                row=ROWS[case];inputs=bytes([*row[:5],*[128 if row[5]&(1<<n) else 0 for n in range(9)],0,0])
                before=bytes(memory);out=(c.c_uint32*2)();hud=(c.c_uint8*16).from_buffer_copy(inputs)
                assert fn(hud,bank4,low,memory,out),(region,case,'native failed')
                actual=bytes(ram[0x1b00:0x1e00]);assert bytes(memory)==actual,(region,case,row,'HUD/DC/DD bytes')
                trace=Trace(rom);model_hud(trace,inputs)
                assert out[0]==costs[case]==trace.foreground_tstates and out[1]==trace.fetches,(region,case,row,'T/M1',list(out),costs[case],trace.foreground_tstates,trace.fetches)
                record=FORMAT.pack(inputs,out[0],out[1],before,actual)
                if region=='auto':vectors.extend(record)
                else:assert record==vectors[case*FORMAT.size:(case+1)*FORMAT.size],(case,'region output/work differs')
                checked[case]=dict(inputs=row,tstates=out[0],m1=out[1],memory_sha256=hashlib.sha256(actual).hexdigest())
            if count>24000 and ram[2]:observer.gaw_timing_reset();previous[0]=0
        with contextlib.redirect_stdout(io.StringIO()):
            run(fixture,len(ROWS)*5+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,
                core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(done))
        assert done and len(checked)==len(ROWS),(region,len(checked),len(ROWS))
        regions.append(dict(region=region,cases=len(checked),done_frame=done[0]));print(regions[-1],flush=True)
    (folder/'vectors.bin').write_bytes(vectors)
    report=dict(cases=len(ROWS),regions=regions,record_bytes=FORMAT.size,vector_sha256=hashlib.sha256(vectors).hexdigest(),
                module_sha256=hashlib.sha256((ROOT/'megadrive/src/source_room_hud.c').read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256(rom).hexdigest(),fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
                limits=['Original1E4E unchanged; custom boot supplies cases,1DE8 RET is a post-call marker. Exact768 DB/DC/DD bytes and foreground T compared with source.',
                        'M1 compared to audited instruction model; disabledIRQ isolated HUD fixture. Live phase/R/IRQ proofs are separate24-entry chain tests.',
                        'All byte health/magic for capacities8..128 step8, selected boundaries0,7,129,255; all256 gold and512 gem masks independently, not Cartesian product.'])
    (ROOT/'analysis/native_hud_values_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
