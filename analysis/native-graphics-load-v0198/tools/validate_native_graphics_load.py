"""Chain native16D0..24B9 across six source checkpoints with one clock/state."""
import ctypes as c
import hashlib
import json
import os
import struct
import subprocess
from actor_reference import ROOT
from validate_native_graphics_prefix import MODULES as PREFIX_MODULES

MODULES=['source_graphics_load',*PREFIX_MODULES]
PCS=[0x1706,0x170e,0x1720,0x1733,0x1748,0x24b9]
WRAPPER='''#include "source_graphics_load.h"
typedef struct {u32 count,points;u32 *events,*snapshots;u8 *states;SourceIrqContext *irq;} LoadTrace;
static void snapshot(const SourceClock *clock,const SourceIrqContext *ctx,u32 *out)
{
 out[0]=clock->raster;out[1]=clock->until_vint;out[2]=clock->elapsed;
 out[3]=clock->foreground_tstates;out[4]=clock->foreground_m1;out[5]=clock->irq_tstates;out[6]=clock->irq_m1;
 out[7]=clock->irq_count;out[8]=clock->status_suppressions;out[9]=clock->vector_coalescences;
 out[10]=clock->refresh;out[11]=clock->iff;out[12]=clock->blocked;out[13]=clock->pending;out[14]=clock->first;
 out[15]=0;out[16]=ctx->error;out[17]=ctx->audio_de;
}
static void trace(void *context,const SourceClockIrq *entry,const SourceClockWork *work)
{
 LoadTrace *p=(LoadTrace *)context;u32 *row;if(p->count>=64) {p->count++;return;}
 row=p->events+p->count++*6;row[0]=entry->entry_elapsed;row[1]=entry->entry_raster;
 row[2]=entry->entry_refresh;row[3]=work->tstates;row[4]=work->fetches;
 row[5]=p->irq->last_irq.stages[SOURCE_IRQ_SAT64].tstates!=0;
}
static u8 point(void *context,u16 pc,const SourceClock *clock,const SourceIrqContext *ctx)
{
 static const u16 pcs[]={0x1706,0x170e,0x1720,0x1733,0x1748,0x24b9};
 LoadTrace *p=(LoadTrace *)context;u8 *state;u16 n;
 if(p->points>=6 || pc!=pcs[p->points]) return 0;
 snapshot(clock,ctx,p->snapshots+p->points*18);state=p->states+p->points*736;
 for(n=0;n<336;n++) state[n]=ctx->ram[n];
 for(n=0;n<400;n++) state[336+n]=ctx->audio[n];
 p->points++;return 1;
}
static u32 hash_more(const u8 *bytes,u16 count,u32 value)
{
 u16 n;for(n=0;n<count;n++) value=(value^bytes[n])*16777619UL;return value;
}
static u32 hash(const u8 *bytes,u16 count) { return hash_more(bytes,count,2166136261UL); }
u8 graphics_load_case(const u32 *phase,u8 refresh,u8 *ram,u8 *audio,const u8 *low,
                      const u8 *bank6,const u8 *patterns,const u8 *bank2,const u8 *bank11,
                      u32 *out,u32 *events,u32 *points,u8 *states)
{
 SourceClock clock;SourceIrqContext ctx={0};LoadTrace log={0};SourceGraphicsData data;
 static u8 pixels[16384],meta[2048],backup[16],terrain[1024],saved[1024];u16 n;
 s32 raster=(s32)(phase[1]*3420)+(s32)(phase[0]-phase[2]);u32 period=phase[3]*3420;
 if((phase[3]!=262 && phase[3]!=313) || phase[5] || (phase[6]&4) || !(phase[6]&32) ||
    (phase[7]!=32 && phase[7]!=33) || (phase[11]&16)) return 0;
 while(raster<0) raster+=period;
 while((u32)raster>=period) raster-=period;
 if(!source_clock_init(&clock,phase[3],raster,refresh,phase[8],phase[9],phase[10])) return 0;
 ctx.ram=ram;ctx.audio=audio;ctx.low=low;ctx.bank6=bank6;ctx.low_bytes=32768;
 ctx.input.lines=phase[3];ctx.input.reset_mask=16;
 ctx.trace=trace;ctx.trace_context=&log;log.irq=&ctx;
 log.events=events;log.snapshots=points;log.states=states;
 for(n=0;n<sizeof(pixels);n++) pixels[n]=0xa7;
 for(n=0;n<sizeof(meta);n++) meta[n]=0xa7;
 for(n=0;n<sizeof(terrain);n++) terrain[n]=0xa7;
 data.patterns=pixels;data.metatiles=meta;data.backup=backup;data.terrain=terrain;data.saved_terrain=saved;
 if(!source_graphics_load_class0(&clock,&ctx,patterns,bank2,bank11,&data,point,&log) || log.count>64 || log.points!=6) return 0;
 snapshot(&clock,&ctx,out);out[18]=hash(pixels,sizeof(pixels));out[19]=hash(meta,sizeof(meta));
 out[20]=hash(backup,sizeof(backup));out[21]=hash(terrain,sizeof(terrain));out[22]=hash(saved,sizeof(saved));
 out[23]=hash(pixels,6176);out[24]=hash_more(meta+0x400,56,hash(meta,912));
 out[25]=hash(backup,16);out[26]=hash(terrain,512);out[27]=hash(saved,512);
 return 1;
}
'''

def decode(stream,stride,size):
    out=bytearray([0xa7])*size;src=0
    for plane in range(stride):
        dst=plane
        while stream[src]:
            command=stream[src];src+=1
            for n in range((command&127) or 256):
                out[dst]=stream[src];dst+=stride
                if command&128:src+=1
            if not command&128:src+=1
        src+=1
    return out,src

def data_buffers(rom):
    pixels,used=decode(rom[0x3c010:],4,16384);meta,_=decode(rom[0x3c010+used:],2,2048)
    backup=meta[0x1c0:0x1c8]+meta[0x1f0:0x1f8]
    meta[0x1c0:0x1c8]=meta[0x1f0:0x1f8]=meta[0x98:0xa0]
    table=int.from_bytes(rom[0x8259:0x825b],'little');count=0
    while rom[table+count]<128:
        offset=rom[table+count]*8;meta[0x400+count*8:0x408+count*8]=meta[offset:offset+8];count+=1
    for n in range(count*4):meta[0x401+n*2]=(meta[0x401+n*2]&31)|rom[table+count+1+n]
    terrain_pc=int.from_bytes(rom[0x1759:0x175b],'little');terrain,_=decode(rom[11*0x4000+(terrain_pc&0x3fff):],4,1024)
    return [pixels,meta,backup,terrain,terrain]

def fnv(data):
    result=2166136261
    for value in data:result=((result^value)*16777619)&0xffffffff
    return result

def data_hashes(rom):return [fnv(data) for data in data_buffers(rom)]

def source_data_hashes(rom):
    pixels,meta,backup,terrain,saved=data_buffers(rom)
    return [fnv(pixels[:6176]),fnv(meta[:912]+meta[0x400:0x438]),fnv(backup),fnv(terrain[:512]),fnv(saved[:512])]

def compile_helper():
    folder=ROOT/'validation/native-graphics-load';folder.mkdir(exist_ok=True)
    (folder/'wrapper.c').write_text(WRAPPER);sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ)
    env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(folder/'wrapper.c')]
    args.extend(str(ROOT/'megadrive/src'/f'{name}.c') for name in MODULES);args.extend(['-o',str(folder/'load.dll')])
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr)
    assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'load.dll'));fn=dll.graphics_load_case
    fn.argtypes=[c.POINTER(c.c_uint32),c.c_uint8,*([c.POINTER(c.c_uint8)]*7),*([c.POINTER(c.c_uint32)]*3),c.POINTER(c.c_uint8)]
    fn.restype=c.c_uint8;return folder,dll,fn

def main():
    folder,dll,fn=compile_helper();rom=(ROOT/'input/original.sms').read_bytes();rows=[];cases=[]
    low=(c.c_uint8*32768).from_buffer_copy(rom[:32768])
    banks=[(c.c_uint8*16384).from_buffer_copy(rom[n*16384:(n+1)*16384]) for n in [6,2,11]]
    patterns=(c.c_uint8*(len(rom)-0x3c010)).from_buffer_copy(rom[0x3c010:]);hashes=data_hashes(rom)+source_data_hashes(rom)
    source_data=json.loads((ROOT/'analysis/graphics_source_data_report.json').read_text())
    assert source_data['cases']==24 and source_data['source_sha256']==hashlib.sha256(rom).hexdigest()
    for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
        for mask in [0,255]:
            base=ROOT/f'validation/graphics-load-refresh/{town:02x}-{mask:02x}'
            if not base.exists():continue
            for region in ['auto','pal']:
                cycles=json.loads((base/f'{region}-cycle-events.json').read_text())
                assert cycles==json.loads((ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json').read_text())
                raw=(base/f'{region}-foreground-phase-records.bin').read_bytes()
                assert raw==(ROOT/f'validation/graphics-load-phase/{town:02x}-{mask:02x}/{region}-foreground-phase-records.bin').read_bytes()
                meta=(base/f'{region}-foreground-m1-records.bin').read_bytes();assert len(meta)==len(raw)//800*16
                records=[]
                for n in range(len(raw)//800):
                    pc,time=struct.unpack_from('<2Q',raw,n*800);m1,refresh,_=struct.unpack_from('<Q2I',meta,n*16)
                    records.append(dict(pc=pc,time=time,phase=struct.unpack_from('<12I',raw,n*800+16),ram=raw[n*800+64:n*800+400],sound=raw[n*800+400:n*800+800],m1=m1,refresh=refresh))
                start=next(e[2] for e in cycles if e[1]==0x16d0 and e[4]==target)
                first=next(r for r in records if r['pc']==0x16d0 and r['time']==start);phase=first['phase'];tag=(town,mask,region)
                ram=(c.c_uint8*336).from_buffer_copy(first['ram']);audio=(c.c_uint8*400).from_buffer_copy(first['sound'])
                output=(c.c_uint32*28)();events=(c.c_uint32*384)();points=(c.c_uint32*108)();states=(c.c_uint8*4416)()
                assert fn((c.c_uint32*12)(*phase),first['refresh'],ram,audio,low,banks[0],patterns,banks[1],banks[2],output,events,points,states),(tag,'rejected')
                observed=json.loads((base/f'{region}-audio-irq-events.json').read_text())
                for n,pc in enumerate(PCS):
                    last=next(r for r in records if r['pc']==pc and r['time']>start);p=list(points[n*18:(n+1)*18]);state=bytes(states[n*736:(n+1)*736]);ep=last['phase']
                    delta=((ep[0]-ep[2]+0x80000000)&0xffffffff)-0x80000000
                    assert state[336:]==last['sound'] and all(state[i]==last['ram'][i] for i in range(336) if i not in [0x1b,0x20,0x21,0x22,0x23]),(tag,hex(pc),'RAM/audio')
                    assert p[0]==(ep[1]*3420+delta)%(phase[3]*3420) and p[2]==last['time']-start,(tag,hex(pc),'phase/time',p)
                    assert p[10]==last['refresh'] and p[4]+p[6]==last['m1']-first['m1'],(tag,hex(pc),'M1/R')
                    assert (p[11],p[13],p[14])==(ep[8],ep[10],1) and not p[12] and not p[16],(tag,hex(pc),'latches')
                    accepted=[(e[2]-start,False) for e in observed if e[1]==0x137 and start<e[2]<last['time']]
                    actual=[(events[j*6],bool(events[j*6+5])) for j in range(p[7])]
                    assert accepted==actual,(tag,hex(pc),'IRQ schedule')
                assert list(output[18:])==hashes,(tag,'decoded buffers',list(output[18:]),hashes)
                captured=next(r['hashes'] for r in source_data['rows'] if (r['town'],r['mask'],r['region'])==tag)
                assert list(output[23:])==captured,(tag,'native/source buffer hashes')
                cases.append(dict(phase=list(phase),refresh=first['refresh'],ram=list(first['ram']),audio=list(first['sound']),expected=list(output),events=list(events[:output[7]*6]),points=list(points),states=list(states)))
                rows.append(dict(town=town,mask=mask,region=region,checkpoints=6,foreground_tstates=output[3],foreground_M1=output[4],IRQs=output[7],wall_master_cycles=output[2]))
                print(tag,'native16D0..24B9 six source checkpoints exact',flush=True)
    assert len(cases)==24
    (folder/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    report=dict(cases=len(cases),rows=rows,helpers={name:hashlib.sha256((ROOT/'megadrive/src'/f'{name}.c').read_bytes()).hexdigest() for name in MODULES},
                source_sha256=hashlib.sha256(rom).hexdigest(),production_clock_wired=False,
                limits=['Six source checkpoints from one captured16D0 entry each: phase/R/M1/331RAM/400audio/IRQ offsets. No intermediate injection.',
                        'Native buffer hashes checked directly against new source observer over defined written ranges; full buffers/1024-byte copy also checked against separate decoder.',
                        'Changed class0/C0AC0 only; physical VRAM/mapper, global entry propagation and other graphics classes remain pending.'])
    (ROOT/'analysis/native_graphics_load_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
