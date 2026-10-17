"""Original1DEB palette bytes/T/M1/R across blink,selection and all counters."""
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
from validate_native_room_finish import MODULES,palette_bytes
ROWS=[(blink,slot,counter) for blink in [0,1] for slot in range(4) for counter in range(256)]
WRAPPER='''#include "source_room_finish.h"
u8 palette_case(u8 blink,u8 slot,u8 counter,u8 refresh,const u8 *low,u8 *palette,u32 *out)
{
 SourceClock clock;SourceIrqContext ctx={0};SourceWorldMapData map;u8 ram[336]={0},audio[400]={0},hud[16]={0},cells[256];u16 n;
 source_clock_init(&clock,262,0,refresh,0,0,0);ram[0x2f]=counter;hud[14]=blink;hud[15]=slot;
 ctx.ram=ram;ctx.audio=audio;ctx.low=low;ctx.low_bytes=32768;ctx.input.lines=262;ctx.input.reset_mask=16;map.cells=cells;
 if(!source_room_palette(&clock,&ctx,&map,hud,0,0)) return 0;
 for(n=0;n<16;n++) palette[n]=cells[0xb0+n];
 out[0]=clock.foreground_tstates;out[1]=clock.foreground_m1;out[2]=clock.refresh;return 1;
}
'''

def generate():
    image=bytearray((ROOT/'input/original.sms').read_bytes())+bytearray(0xc0000);code=bytearray();labels={};fix=[]
    def emit(h):code.extend(bytes.fromhex(h))
    def label(n):labels[n]=0x3000+len(code)
    def call(op,n):emit(op);fix.append((len(code),n));emit('0000')
    emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c0')
    label('case');emit('af3202c03e2032ffffdd2a06c0')
    for n,address in enumerate([0xc0bf,0xc0f1,0xc02f]):emit(f'dd7e{n:02x}32'+address.to_bytes(2,'little').hex())
    call('cd','palette');emit('3e013202c00603');label('hold');emit('dbbfe680');call('ca','hold');emit('05');call('c2','hold')
    emit('2a06c0110400192206c02a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');call('c2','case')
    emit('af3202c03e013204c0');label('done');call('c3','done')
    label('palette');emit('21bf24e5c3eb1d')
    for offset,name in fix:code[offset:offset+2]=labels[name].to_bytes(2,'little')
    image[:3]=bytes.fromhex('c30030');image[0x3000:0x3000+len(code)]=code;image[0x24bf]=0xc9
    data=b''.join(bytes([*row,0]) for row in ROWS);image[0x80000:0x80000+len(data)]=data
    folder=ROOT/'validation/native-palette';folder.mkdir(exist_ok=True);fixture=folder/'source.sms';fixture.write_bytes(image)
    return folder,fixture

def main():
    folder,fixture=generate();sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    (folder/'wrapper.c').write_text(WRAPPER)
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(folder/'wrapper.c')]
    args.extend(str(ROOT/'megadrive/src'/f'{name}.c') for name in MODULES);args.extend(['-o',str(folder/'palette.dll')])
    built=subprocess.run(args,env=env,capture_output=True,text=True);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'palette.dll'));fn=dll.palette_case
    fn.argtypes=[*([c.c_uint8]*4),c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),c.POINTER(c.c_uint32)];fn.restype=c.c_uint8
    rom=(ROOT/'input/original.sms').read_bytes();low=(c.c_uint8*32768).from_buffer_copy(rom[:32768])
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_roomfinishdata_libretro.dll';observer=c.CDLL(str(core))
    observer.gaw_foreground_phase_samples.restype=c.c_uint
    observer.gaw_foreground_phase_events.restype=observer.gaw_foreground_m1_events.restype=c.POINTER(c.c_uint8)
    regions=[];cases=[]
    for region in ['auto','pal']:
        observer.gaw_timing_reset();previous=[0];starts={};checked={};done=[]
        def observe(frame,ram):
            case=int.from_bytes(ram[:2],'little');count=observer.gaw_foreground_phase_samples()
            raw=c.string_at(observer.gaw_foreground_phase_events(),count*800);meta=c.string_at(observer.gaw_foreground_m1_events(),count*16)
            for n in range(previous[0],count):
                pc,time=struct.unpack_from('<2Q',raw,n*800);m1,refresh,_=struct.unpack_from('<Q2I',meta,n*16)
                if pc==0x1deb:starts[case]=(time,m1,refresh)
                elif pc==0x24bf:
                    assert case==len(checked);first=starts[case];blink,slot,counter=ROWS[case]
                    output=(c.c_uint8*16)();work=(c.c_uint32*3)()
                    assert fn(blink,slot,counter,first[2],low,output,work)
                    checked[case]=dict(blink=blink,slot=slot,counter=counter,entry_R=first[2],palette=list(output),work=list(work))
                    assert (work[0]*15,work[1],work[2])==(time-first[0],m1-first[1],refresh),(region,case,'T/M1/R')
                    assert bytes(output)==bytes(ram[0x1cb0:0x1cc0])==palette_bytes(rom,bytes(14)+bytes([blink,slot]),counter),(region,case,'palette')
                    if region=='auto':cases.append(checked[case])
                    else:
                        assert checked[case]['palette']==cases[case]['palette'] and checked[case]['work'][:2]==cases[case]['work'][:2]
            previous[0]=count
            if ram[4]:done.append(frame)
        with contextlib.redirect_stdout(io.StringIO()):
            run(fixture,len(ROWS)*5+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,
                core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(done))
        assert done and len(checked)==len(ROWS),(region,len(checked))
        regions.append(dict(region=region,cases=len(checked)));print(regions[-1],flush=True)
    (folder/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    (ROOT/'analysis/native_palette_report.json').write_text(json.dumps(dict(cases=len(cases),regions=regions,
        source_sha256=hashlib.sha256(rom).hexdigest(),fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
        limits=['Original palette instructions1DEB unchanged; controlled return to24BF RET marker. Direct16-byte palette and foreground T/M1/R source comparisons.',
                '2048 blink/selection/counter combinations,IRQ disabled; full live IRQ and preceding loading covered separately by24-entry chain.']),indent=2)+'\n')

if __name__=='__main__':main()
