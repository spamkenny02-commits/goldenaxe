"""One native loading clock16D0->18E1, including original enemy RLE/remap bytes."""
import ctypes as c,json,os,struct,subprocess
from run_core import ROOT
from archive_lossless_evidence import sha
from validate_native_room_load import MODULES,build_wrapper,PCS,records,read_reference,reference_manifest
from actor_reference import load_room_actors
from validate_native_room_finish import hud_buffers
from validate_native_graphics_load import decode
PREFIX_PCS=PCS+[0x17ae,0x17de,0x1805,0x1839,0x1853]
WRAPPER=build_wrapper(True).replace('#include "source_room_load.h"','#include "source_room_load.h"\nstatic u8 pixels[16384];')
WRAPPER=WRAPPER.replace('static u8 pixels[16384],meta[2048]','static u8 meta[2048]')
WRAPPER=WRAPPER.replace('const u8 *bank12,','const u8 *rom,')
WRAPPER=WRAPPER.replace('SourceActorListData list={actors,flags+0x12,room_bytes,masks,progression};','SourceActorListData list={actors,flags+0x12,room_bytes,masks,progression};SourceActorGraphicsData actor_graphics;u8 allocation;')
WRAPPER=WRAPPER.replace(' if(!source_room_load_class0_actors(', ' actor_graphics.actors=actors;actor_graphics.patterns=pixels;actor_graphics.terrain=terrain;actor_graphics.allocated=&allocation;\n if(!source_room_load_class0_actors(')
WRAPPER=WRAPPER.replace('source_room_load_class0_actors(&clock,&ctx,&input,&loading,bank12,&list,&loaded,point,&log)','source_room_load_class0_graphics(&clock,&ctx,&input,&loading,rom,&list,&actor_graphics,&loaded,point,&log)').replace('log.points!=22','(log.points<23 || log.points>32)')
WRAPPER=WRAPPER.replace('if(p->points>=22 || pc!=pcs[p->points]) return 0;','if(p->points>=32 || (p->points<22 && pc!=pcs[p->points]) || (p->points>=22 && pc!=0x18ac && pc!=0x18af && pc!=0x18b7 && pc!=0x18e1)) return 0;')
WRAPPER=WRAPPER.replace('p->snapshots+p->points*18','p->snapshots+p->points*19').replace('p->points++;return 1;','p->snapshots[p->points*19+18]=pc;p->points++;return 1;')
WRAPPER=WRAPPER.replace('out[47]=*list.active_count;','out[47]=*list.active_count;out[48]=allocation;out[49]=log.points;')
WRAPPER+='\nconst u8 *room_load_patterns(void){return pixels;}\n'

def main():
 folder=ROOT/'validation/native-room-graphics';folder.mkdir(exist_ok=True);(folder/'wrapper.c').write_bytes(WRAPPER.encode());sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O3','-shared','-Wall','-Wextra','-Werror','-I'+str(sdk/'inc'),'-I'+str(ROOT/'megadrive/src'),*[str(ROOT/'megadrive/src'/(n+'.c')) for n in MODULES],str(folder/'wrapper.c'),'-o',str(folder/'graphics.dll')],env=env,capture_output=True,text=True)
 (folder/'compile.log').write_bytes((built.stdout+built.stderr).encode());assert built.returncode==0,built.stderr[-3000:]
 lib=c.CDLL(str(folder/'graphics.dll'));u8=c.POINTER(c.c_uint8);u32=c.POINTER(c.c_uint32);lib.room_load_case.argtypes=[u32,c.c_uint8,*([u8]*4),c.c_uint16,*([u8]*10),u32,u32,u32,u8];lib.room_load_case.restype=c.c_uint8;lib.room_load_patterns.restype=u8
 original=(ROOT/'input/original.sms').read_bytes();arr=lambda b:(c.c_uint8*len(b)).from_buffer_copy(b);rom=arr(original);cases=[];results=[];background,_=decode(original[0x3c010:],4,16384)
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_bytes())['routes']:
  for mask in [0,255]:
   source=ROOT/f'validation/actor-graphics-refresh/{town:02x}-{mask:02x}'
   for region in ['auto','pal']:
    rows=records(source,region,'graphics');cycles=json.loads(read_reference(source/f'{region}-cycle-events.json','graphics'));start=next(e[2] for e in cycles if e[1]==0x16d0 and e[4]==target);entry=next(e for e in rows if e['pc']==0x16d0 and e['time']==start);tag=(town,mask,region)
    initial_mask=entry['context'][18+target];resources=load_room_actors(original,target,initial_mask)[4];pcs=PREFIX_PCS+[v for _ in resources for v in [0x18ac,0x18af,0x18b7]]+[0x18e1];assert len(pcs)<=32
    ram=arr(entry['ram']);audio=arr(entry['audio']);history=arr(entry['context'][2:18]);masks=arr(entry['context'][18:274]);hud=arr(entry['hud']);actors=(c.c_uint8*768)();out=(c.c_uint32*50)();events=(c.c_uint32*384)();points=(c.c_uint32*608)();states=(c.c_uint8*23552)()
    bank=lambda n:c.cast(c.addressof(rom)+n*16384,u8)
    assert lib.room_load_case((c.c_uint32*12)(*entry['phase']),entry['refresh'],ram,audio,rom,bank(6),target,bank(8+(target>>7)),c.cast(c.addressof(rom)+0x3c010,u8),bank(2),bank(11),bank(4),hud,rom,history,masks,actors,out,events,points,states),(tag,'rejected')
    assert out[49]==len(pcs) and out[44]==7 and not out[40],(tag,'completion')
    irq=json.loads(read_reference(source/f'{region}-audio-irq-events.json','graphics'));cursor=start
    for n,pc in enumerate(pcs):
     end=next(r for r in rows if r['pc']==pc and r['time']>cursor);cursor=end['time'];p=list(points[n*19:(n+1)*19]);state=bytes(states[n*736:(n+1)*736]);phase=end['phase'];delta=((phase[0]-phase[2]+0x80000000)&0xffffffff)-0x80000000
     assert p[18]==pc and p[0]==(phase[1]*3420+delta)%(phase[3]*3420) and p[2]==cursor-start,(tag,hex(pc),'phase/time')
     assert p[10]==end['refresh'] and p[4]+p[6]==end['m1']-entry['m1'],(tag,hex(pc),'M1/R')
     assert state[336:]==end['audio'] and all(state[i]==end['ram'][i] for i in range(336) if i not in [0x1b,0x20,0x21,0x22,0x23]),(tag,hex(pc),'RAM/audio')
     assert (p[11],p[13],p[14])==(phase[8],phase[10],1) and not p[12] and not p[16]
     assert [(events[j*6],bool(events[j*6+5])) for j in range(p[7])]==[(e[2]-start,bool(e[5])) for e in irq if e[1]==0x137 and start<e[2]<cursor],(tag,'IRQ schedule')
    assert bytes(history)==end['context'][2:18] and bytes(masks)==end['context'][18:274] and bytes(actors)==end['actors'] and out[47]==end['active_count'],(tag,'history/masks/actors/count')
    graph=read_reference(source/f'{region}-actor-graphics-records.bin','graphics');record=next(graph[n:n+8208] for n in range(0,len(graph),8208) if struct.unpack_from('<Q',graph,n)[0]==cursor);allocation=struct.unpack_from('<I',record,8)[0];assert out[48]==allocation
    pixels=c.string_at(lib.room_load_patterns(),16384);assert pixels[0x2000:0x2000+allocation*32]==record[16:16+allocation*32],(tag,'actor patterns')
    assert pixels[:6176]==background[:6176],(tag,'background patterns')
    expected_hud=hud_buffers(original,target,entry['ram'],entry['hud'])[1];assert pixels[0x3800:0x3e00]==expected_hud,(tag,'map/HUD mirror')
    cases.append(dict(room=target,phase=entry['phase'],refresh=entry['refresh'],ram=list(entry['ram']),audio=list(entry['audio']),hud=list(entry['hud']),history=list(entry['context'][2:18]),masks=list(entry['context'][18:274]),expected=list(out),events=list(events[:out[7]*6]),points=list(points[:len(pcs)*19]),states=list(states[:len(pcs)*736]),after_history=list(history),after_masks=list(masks),actors=list(actors),patterns=list(pixels)))
    results.append(dict(town=town,target=target,mask=mask,region=region,checkpoints=len(pcs),pattern_bytes=allocation*32,foreground_tstates=out[3],foreground_m1=out[4],irqs=out[7],exit_refresh=out[10]));print(results[-1],flush=True)
 assert len(cases)==24
 (folder/'cases.json').write_bytes((json.dumps(cases,separators=(',',':'))+'\n').encode())
 report=dict(passed=True,cases=24,checkpoints=sum(r['checkpoints'] for r in results),rng_calls=72,rows=results,source_sha256=sha(original),playable_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),module_sha256={n+'.c':sha((ROOT/'megadrive/src'/(n+'.c')).read_bytes()) for n in MODULES},headers_sha256={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['source_actor_graphics.h','source_pattern_clock.h','source_room_load.h']},reference_manifest_sha256=sha((reference_manifest('graphics')[0]/'manifest.json').read_bytes()),production_clock_wired=False,limits=['Single16D0 entry, no intermediate R/phase/seed/audio/history injection; live source IRQ/audio. Source331RAM/400audio/time/R/M1/IRQ offsets at all checkpoints, final history/masks/actors/count/allocation/enemy pattern bytes checked.','Six ordinary class0 exterior destinations, masks00/FF. Lower6176 pattern bytes and1536 map/HUD bytes also checked against ROM-derived data. Scratch terrain hash remains host parity.','No physical MD uploads/pacing, boot entry clock, other classes, hero/tail, or full campaign proof.'])
 (ROOT/'analysis/native_room_graphics_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())

if __name__=='__main__':main()
