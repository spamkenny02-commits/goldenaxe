"""Native complete-wait bridge and independent source return-record comparisons."""
import ctypes as c
import hashlib
import os
import struct
import subprocess
from actor_reference import ROOT
from validate_native_source_wait import MODULES as BASE_MODULES,WRAPPER as BASE_WRAPPER

MODULES=['source_wait_restore',*BASE_MODULES]
WRAPPER=BASE_WRAPPER.replace('"source_wait.h"','"source_wait_restore.h"').replace('u8 wait_case(','u8 wait_return_case(')
WRAPPER=WRAPPER.replace('u16 tile_count,u32 *out','u16 tile_count,u8 tail,u32 *out')
WRAPPER=WRAPPER.replace('if(!source_wait(&clock,&ctx,&result) || log.count>16) return 0;',
    'result.taken=result.error=0;\n if(!(tail?source_wait_restore(&clock,&ctx):source_wait_complete(&clock,&ctx,&result)) || log.count>16) return 0;')
CHAIN_FUNCTION=WRAPPER[WRAPPER.index('u8 wait_return_case('):].replace('wait_return_case(','wait_chain_case(').replace('u8 tail,u32 *out','u16 repetitions,u32 *out')
CHAIN_FUNCTION=CHAIN_FUNCTION.replace('SourceClock clock;','u32 total_taken=0;SourceClock clock;')
CHAIN_FUNCTION=CHAIN_FUNCTION.replace('result.taken=result.error=0;\n if(!(tail?source_wait_restore(&clock,&ctx):source_wait_complete(&clock,&ctx,&result)) || log.count>16) return 0;',
    'for(n=0;n<repetitions;n++) {if(!source_wait_complete(&clock,&ctx,&result)) return 0;total_taken+=result.taken;}\n if(log.count>16) return 0;')
CHAIN_FUNCTION=CHAIN_FUNCTION.replace('out[15]=result.taken;','out[15]=total_taken;')


def compile_helper():
    folder=ROOT/'validation/native-wait-return';folder.mkdir(exist_ok=True)
    (folder/'wrapper.c').write_text(WRAPPER+CHAIN_FUNCTION);sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ)
    env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(folder/'wrapper.c')]
    args.extend(str(ROOT/'megadrive/src'/f'{name}.c') for name in MODULES);args.extend(['-o',str(folder/'wait_return.dll')])
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'wait_return.dll'));function=dll.wait_return_case
    function.argtypes=[c.POINTER(c.c_uint32),c.c_uint8,c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),
                       c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),c.c_uint16,c.c_uint8,c.POINTER(c.c_uint32),c.POINTER(c.c_uint32)]
    function.restype=c.c_uint8;return folder,dll,function


def prepare_core():
    path=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_waitcomplete_libretro.dll';dll=c.CDLL(str(path))
    for name in ['gaw_wait_return_samples','gaw_wait_return_stride','gaw_audio_irq_count','gaw_wait_samples']:getattr(dll,name).restype=c.c_uint
    dll.gaw_wait_return_events.restype=dll.gaw_wait_events.restype=c.POINTER(c.c_uint8)
    dll.gaw_audio_irq_events.restype=c.POINTER(c.c_uint64)
    assert dll.gaw_wait_return_stride()==2464
    return path,dll


def validate_record(function,image,record,events,tag):
    first=record[:800];restore=record[800:1600];last=record[1600:2400]
    first_meta=struct.unpack_from('<Q2I',record,2400);restore_meta=struct.unpack_from('<Q2I',record,2416);last_meta=struct.unpack_from('<Q2I',record,2432)
    pc,start=struct.unpack_from('<2Q',first);caller,end=struct.unpack_from('<2Q',last)
    return_pc,bank_saved,bank_final=struct.unpack_from('<3I',record,2448)
    assert pc in [0xb95,0xbb3] and struct.unpack_from('<Q',restore)[0]==0xbb3 and caller==return_pc and bank_saved==bank_final,(tag,'source return/bank')
    phase=struct.unpack_from('<12I',first,16);end_phase=struct.unpack_from('<12I',last,16)
    before=first[64:400];sound=first[400:800];tile_count=0
    if before[0x42]:
        pointer=int.from_bytes(before[0x43:0x45],'little');asset=pointer if pointer<0x8000 else before[0x42]*0x4000+(pointer&0x3fff);tile_count=image[asset] or 256
    state=(c.c_uint8*336).from_buffer_copy(before);audio=(c.c_uint8*400).from_buffer_copy(sound)
    low=(c.c_uint8*32768).from_buffer_copy(image[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(image[0x18000:0x1c000])
    output=(c.c_uint32*18)();trace=(c.c_uint32*96)();tail=pc==0xbb3
    assert function((c.c_uint32*12)(*phase),first_meta[1],state,audio,low,bank,tile_count,tail,output,trace),(tag,'native rejected')
    assert bytes(audio)==last[400:800] and all(state[i]==last[64+i] for i in range(336) if i not in [0x1b,0x20,0x21,0x22,0x23]),(tag,'RAM/audio')
    delta=((end_phase[0]-end_phase[2]+0x80000000)&0xffffffff)-0x80000000
    assert output[0]==(end_phase[1]*3420+delta)%(phase[3]*3420) and output[2]==end-start,(tag,'phase/time',list(output),end-start)
    assert output[10]==last_meta[1] and output[4]+output[6]==last_meta[0]-first_meta[0],(tag,'M1/R')
    assert (output[11],output[13],output[14])==(end_phase[8],end_phase[10],1) and not output[12] and not output[16],(tag,'latches')
    actual=[(time-start,full) for time,full in events if start<time<end]
    predicted=[(trace[n*6],bool(trace[n*6+5])) for n in range(output[7])]
    assert predicted==actual,(tag,'IRQ entries',predicted,actual)
    assert output[3]==(149 if tail else 347+29*output[15]),(tag,'foreground work')
    assert output[4]==(17 if tail else 39+3*output[15]),(tag,'foreground M1')
    return dict(phase=list(phase),refresh=first_meta[1],ram=list(before),audio=list(sound),tile_count=tile_count,tail=int(tail),
                expected_ram=list(state),expected_audio=list(audio),expected=list(output),events=list(trace[:output[7]*6]),
                caller=caller,source_bank=bank_saved,restore_time=struct.unpack_from('<Q',restore,8)[0],restore_M1=restore_meta[0])


def irq_events(dll):
    pointer=dll.gaw_audio_irq_events();count=dll.gaw_audio_irq_count();assert count<32768,'IRQ observer capacity reached'
    return [(pointer[i*14+1],bool(pointer[i*14+4])) for i in range(count) if pointer[i*14]==0x137]


def helpers():
    return {name:hashlib.sha256((ROOT/'megadrive/src'/f'{name}.c').read_bytes()).hexdigest() for name in MODULES}
