"""Full native graphics/map/HUD/wait/name-table/palette chain16D0..24BF."""
import ctypes as c
import hashlib,json,os,struct,subprocess
from actor_reference import ROOT
from world_map_loading_cost import world_map_cost
from validate_native_room_hud import MODULES as HUD_MODULES,map_buffers
from validate_native_graphics_load import decode,data_buffers,data_hashes,source_data_hashes,fnv
from validate_native_world_map import map_data_hashes
MODULES=['source_room_finish','source_wait_restore',*HUD_MODULES]
PCS=[0x1706,0x170e,0x1720,0x1733,0x1748,0x24b9,0x192a,0x192d,0x24bc,0x1de5,0x1de8,0xb95,0xbb3,0x22a3,0x1deb,0x24bf]
WRAPPER='''#include "source_room_finish.h"
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
 static const u16 pcs[]={0x1706,0x170e,0x1720,0x1733,0x1748,0x24b9,0x192a,0x192d,0x24bc,0x1de5,0x1de8,0xb95,0xbb3,0x22a3,0x1deb,0x24bf};
 LoadTrace *p=(LoadTrace *)context;u8 *state;u16 n;
 if(p->points>=16 || pc!=pcs[p->points]) return 0;
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
u8 room_finish_case(const u32 *phase,u8 refresh,u8 *ram,u8 *audio,const u8 *low,
                      const u8 *bank6,u16 room,const u8 *map_bank,const u8 *patterns,const u8 *bank2,const u8 *bank11,const u8 *bank4,const u8 *hud,
                      u32 *out,u32 *events,u32 *points,u8 *states)
{
 SourceClock clock;SourceIrqContext ctx={0};LoadTrace log={0};SourceGraphicsData data;SourceRoomFinish finish;SourceWorldMapData map;
 static u8 pixels[16384],meta[2048],backup[16],terrain[1024],saved[1024],cells[256],tilemap[1536];u16 n;
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
 for(n=0;n<sizeof(cells);n++) cells[n]=0xa7;
 for(n=0;n<sizeof(tilemap);n++) tilemap[n]=0xa7;
 map.cells=cells;map.tilemap=tilemap;
 for(n=0;n<sizeof(pixels);n++) pixels[n]=0xa7;
 for(n=0;n<sizeof(meta);n++) meta[n]=0xa7;
 for(n=0;n<sizeof(terrain);n++) terrain[n]=0xa7;
 data.patterns=pixels;data.metatiles=meta;data.backup=backup;data.terrain=terrain;data.saved_terrain=saved;
 if(!source_graphics_load_class0(&clock,&ctx,patterns,bank2,bank11,&data,point,&log) || log.count>64 || log.points!=6) return 0;
 if(!source_world_map_load(&clock,&ctx,room,1,map_bank,bank2,&data,&map,point,&log) || log.count>64 || log.points!=9) return 0;
 if(!source_room_hud_prepare(&clock,&ctx,&data,&map,bank4,hud,point,&log) || log.count>64 || log.points!=11) return 0;
 if(!source_room_finish(&clock,&ctx,&data,&map,hud,&finish,point,&log) || log.count>64 || log.points!=16) return 0;
 snapshot(&clock,&ctx,out);out[18]=hash(pixels,sizeof(pixels));out[19]=hash(meta,sizeof(meta));
 out[20]=hash(backup,sizeof(backup));out[21]=hash(terrain,sizeof(terrain));out[22]=hash(saved,sizeof(saved));
 out[23]=hash(pixels,6176);out[24]=hash_more(meta+0x400,56,hash(meta,912));
 out[25]=hash(backup,16);out[26]=hash(terrain,512);out[27]=hash(saved,512);
 out[28]=hash(cells,sizeof(cells));out[29]=hash(tilemap,sizeof(tilemap));out[30]=hash(map.metadata,3);
 out[31]=hash(cells,160);out[32]=hash(map.metadata,3);
 {u8 patch[8];u16 address=0xd600+(map.metadata[1]&0xf0)*8+(map.metadata[1]&15)*4;
  for(n=0;n<8;n++) {u16 dest=address+(n<4?n:n+60);patch[n]=dest>=0xdd00?ram[80+dest-0xdd00]:tilemap[dest-0xd600];}
  out[33]=hash(patch,8);}
 {u16 cell=map.metadata[1],below=cell+16;u8 pair[2];pair[0]=cells[cell];pair[1]=below<256?cells[below]:ram[80+below-256];out[34]=hash(pair,2);}
 out[35]=hash(tilemap+0x500,256);out[36]=hash(tilemap,1280);
 out[37]=hash(pixels+0x3800,1536);out[38]=hash(cells+0xb0,16);out[39]=finish.wait_taken;out[40]=finish.error;
 return 1;
}
'''
def map_buffers(rom,room,ram):
    bank=8+(room>>7);table=bank*16384+((room*2)&255);pc=int.from_bytes(rom[table:table+2],'little')
    cells,_=decode(rom[bank*16384+(pc&16383):],1,256)
    tiles=data_buffers(rom)[1];tilemap=bytearray([0xa7])*1536
    meta=world_map_cost(rom,room)['metadata'];cell=meta[1];kind=meta[2]
    def patch(index,value):
        if index<256:cells[index]=value
        address=(index&240)*8+(index&15)*4
        if address<1536:
            for row in range(2):tilemap[address+row*64:address+row*64+4]=tiles[value*8+row*4:value*8+row*4+4]
    patch(cell,kind);below=cell+16;value=cells[below] if below<256 else ram[80+below-256]
    for n in range(4):
        if value==rom[0x1b05+n*2]:patch(below,rom[0x1b06+n*2]);break
    return cells,tilemap,meta


def hud_buffers(rom,room,ram,hud):
    cells,tilemap,meta=map_buffers(rom,room,ram);tiles=data_buffers(rom)[1]
    for y in range(20):
        for x in range(32):
            source=cells[(y//2)*16+x//2]*8+(y&1)*4+(x&1)*2;dst=y*64+x*2
            tilemap[dst:dst+2]=tiles[source:source+2]
    display,_=decode(rom[0x126ab:],2,256)
    for n in range(128):display[n*2]=(display[n*2]+0xd0)&255;display[n*2+1]|=0x18
    for row in range(2):display[0x58+row*64:0x5c+row*64]=rom[0x1e91+row*4:0x1e95+row*4]
    for n in range(9):
        if hud[5+n]&128:
            dst=rom[0x1edd+n*2];display[dst:dst+2]=bytes([rom[0x1edc+n*2],0x59])
    for n,digit in enumerate([hud[4]//100,hud[4]//10%10,hud[4]%10]):display[0xd0+n*2:0xd2+n*2]=bytes([0xf0+digit,0x18])
    for value,maximum,magic in [(hud[0],hud[1],False),(hud[2],hud[3],True)]:
        dst=0xde if magic else 0x5e;count=maximum>>3 or 256
        # Production route contexts fit in HUD; overflow is verified separately.
        assert dst+count*2<=256
        for n in range(count):
            if value>=8:low=0x90 if magic else 0x8b;value-=8
            else:low=0x91 if magic else 0x8f-(value//2);value=0
            display[dst+n*2:dst+n*2+2]=bytes([low,0x19])
    for n in range(128):display[n*2+1]|=0x40
    tilemap[1280:]=display
    return cells,tilemap,meta


def palette_bytes(rom,hud,counter):
    result=bytearray(rom[0x1e20:0x1e30]);offset=0x1e2e+hud[15]*2
    result[6:8]=rom[offset:offset+2]
    if hud[14] and not counter&2:result[6:8]=bytes([0x16,1])
    result[15]=2 if counter&2 else 1
    return result

def finish_hashes(rom,room,ram,hud,counter):
    cells,tiles,meta=hud_buffers(rom,room,ram,hud);palette=palette_bytes(rom,hud,counter)
    cells[0xb0:0xc0]=palette;vram,_=decode(rom[0x3c010:],4,16384);vram[0x3800:0x3e00]=tiles
    return [fnv(cells),fnv(tiles),fnv(meta)],fnv(tiles[1280:]),fnv(tiles[:1280]),fnv(vram),fnv(palette)

def compile_helper():
    folder=ROOT/'validation/native-room-finish';folder.mkdir(exist_ok=True)
    (folder/'wrapper.c').write_text(WRAPPER);sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ)
    env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(folder/'wrapper.c')]
    args.extend(str(ROOT/'megadrive/src'/f'{name}.c') for name in MODULES);args.extend(['-o',str(folder/'finish.dll')])
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr)
    assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'finish.dll'));fn=dll.room_finish_case
    fn.argtypes=[c.POINTER(c.c_uint32),c.c_uint8,*([c.POINTER(c.c_uint8)]*4),c.c_uint16,*([c.POINTER(c.c_uint8)]*6),*([c.POINTER(c.c_uint32)]*3),c.POINTER(c.c_uint8)]
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
            base=ROOT/f'validation/wait-refresh/{town:02x}-{mask:02x}'
            if not base.exists():continue
            for region in ['auto','pal']:
                cycles=json.loads((base/f'{region}-cycle-events.json').read_text())
                assert cycles==json.loads((ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json').read_text())
                raw=(base/f'{region}-foreground-phase-records.bin').read_bytes()
                assert raw==(ROOT/f'validation/map-hud-phase/{town:02x}-{mask:02x}/{region}-foreground-phase-records.bin').read_bytes()
                hud_context=(base/f'{region}-hud-context-records.bin').read_bytes()
                meta=(base/f'{region}-foreground-m1-records.bin').read_bytes();assert len(meta)==len(raw)//800*16
                records=[]
                for n in range(len(raw)//800):
                    pc,time=struct.unpack_from('<2Q',raw,n*800);m1,refresh,_=struct.unpack_from('<Q2I',meta,n*16)
                    records.append(dict(pc=pc,time=time,phase=struct.unpack_from('<12I',raw,n*800+16),ram=raw[n*800+64:n*800+400],sound=raw[n*800+400:n*800+800],m1=m1,refresh=refresh,hud=hud_context[n*16:(n+1)*16]))
                start=next(e[2] for e in cycles if e[1]==0x16d0 and e[4]==target)
                first=next(r for r in records if r['pc']==0x16d0 and r['time']==start);phase=first['phase'];tag=(town,mask,region)
                map_bank=(c.c_uint8*16384).from_buffer_copy(rom[(8+(target>>7))*16384:(9+(target>>7))*16384])
                ram=(c.c_uint8*336).from_buffer_copy(first['ram']);audio=(c.c_uint8*400).from_buffer_copy(first['sound'])
                bank4=(c.c_uint8*16384).from_buffer_copy(rom[0x10000:0x14000]);hud=(c.c_uint8*16).from_buffer_copy(first['hud'])
                output=(c.c_uint32*41)();events=(c.c_uint32*384)();points=(c.c_uint32*288)();states=(c.c_uint8*11776)()
                assert fn((c.c_uint32*12)(*phase),first['refresh'],ram,audio,low,banks[0],target,map_bank,patterns,banks[1],banks[2],bank4,hud,output,events,points,states),(tag,'rejected')
                observed=json.loads((base/f'{region}-audio-irq-events.json').read_text())
                for n,pc in enumerate(PCS):
                    last=next(r for r in records if r['pc']==pc and r['time']>start);p=list(points[n*18:(n+1)*18]);state=bytes(states[n*736:(n+1)*736]);ep=last['phase']
                    delta=((ep[0]-ep[2]+0x80000000)&0xffffffff)-0x80000000
                    assert state[336:]==last['sound'] and all(state[i]==last['ram'][i] for i in range(336) if i not in [0x1b,0x20,0x21,0x22,0x23]),(tag,hex(pc),'RAM/audio')
                    assert p[0]==(ep[1]*3420+delta)%(phase[3]*3420) and p[2]==last['time']-start,(tag,hex(pc),'phase/time',p)
                    assert p[10]==last['refresh'] and p[4]+p[6]==last['m1']-first['m1'],(tag,hex(pc),'M1/R')
                    assert (p[11],p[13],p[14])==(ep[8],ep[10],1) and not p[12] and not p[16],(tag,hex(pc),'latches')
                    accepted=[(e[2]-start,bool(e[5])) for e in observed if e[1]==0x137 and start<e[2]<last['time']]
                    actual=[(events[j*6],bool(events[j*6+5])) for j in range(p[7])]
                    assert accepted==actual,(tag,hex(pc),'IRQ schedule')
                end_ram=states[-736:-400];reference=finish_hashes(rom,target,first['ram'],first['hud'],end_ram[0x2f]);expected_hashes=list(hashes);expected_hashes[0]=reference[3]
                assert list(output[18:28])==expected_hashes,(tag,'decoded buffers',list(output[18:]),hashes)
                captured=next(r['hashes'] for r in source_data['rows'] if (r['town'],r['mask'],r['region'])==tag)
                assert list(output[23:28])==captured,(tag,'native/source buffer hashes')
                assert list(output[28:31])==reference[0],(tag,'map buffers',list(output[28:31]),map_data_hashes(rom,target,first['ram']))
                assert list(output[35:37])==list(reference[1:3]),(tag,'room/HUD bytes')
                assert output[37]==reference[0][1] and output[38]==reference[4] and not output[40],(tag,'VRAM/palette')
                waits=(base/f'{region}-save-wait-records.bin').read_bytes();wait_start=next(r['time'] for r in records if r['pc']==0xb95 and r['time']>start)
                wait=next(struct.unpack_from('<14Q',waits,n) for n in range(0,len(waits),112) if struct.unpack_from('<Q',waits,n)[0]==wait_start)
                assert output[39]==wait[4],(tag,'wait polling')
                cases.append(dict(room=target,hud=list(first['hud']),phase=list(phase),refresh=first['refresh'],ram=list(first['ram']),audio=list(first['sound']),expected=list(output),events=list(events[:output[7]*6]),points=list(points),states=list(states)))
                rows.append(dict(town=town,mask=mask,region=region,checkpoints=16,wait_taken=output[39],full_IRQs=sum(bool(events[n*6+5]) for n in range(output[7])),foreground_tstates=output[3],foreground_M1=output[4],IRQs=output[7],wall_master_cycles=output[2]))
                print(tag,'native16D0..24BF sixteen source checkpoints exact',flush=True)
    assert len(cases)==24
    (folder/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    report=dict(cases=len(cases),rows=rows,helpers={name:hashlib.sha256((ROOT/'megadrive/src'/f'{name}.c').read_bytes()).hexdigest() for name in MODULES},
                source_sha256=hashlib.sha256(rom).hexdigest(),production_clock_wired=False,
                limits=['Sixteen source checkpoints from one captured16D0 entry each: phase/R/M1/331RAM/400audio/IRQ offsets. No intermediate injection.',
                        'Native buffer hashes checked directly against new source observer over defined written ranges; full buffers/1024-byte copy also checked against separate decoder.',
                        'Changed class0/C0AC0 and six saved-bit0 rooms only; physical VRAM/mapper, global entry propagation and other graphics classes remain pending.'])
    (ROOT/'analysis/native_room_finish_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
