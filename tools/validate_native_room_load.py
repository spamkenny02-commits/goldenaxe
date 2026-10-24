"""Continuous native16D0->1780 vs original paid exits, including live audio IRQs."""
import argparse,ctypes as c,json,os,struct,subprocess
from functools import lru_cache
from run_core import ROOT
from archive_lossless_evidence import sha
from validate_native_room_finish import MODULES as FINISH_MODULES,WRAPPER as FINISH_WRAPPER,PCS as FINISH_PCS

MODULES=['source_actor_list','source_room_load','source_room_history_timed','source_rng_timed',*FINISH_MODULES]
PCS=[*FINISH_PCS,0x1780]
WRAPPER=FINISH_WRAPPER.replace('#include "source_room_finish.h"','#include "source_room_load.h"')
WRAPPER=WRAPPER.replace('0x1deb,0x24bf};','0x1deb,0x24bf,0x1780};').replace('p->points>=16','p->points>=17')
WRAPPER=WRAPPER.replace('u8 room_finish_case(','u8 room_load_case(').replace('u32 *out,u32 *events,u32 *points,u8 *states)','u8 *history,u8 *masks,u32 *out,u32 *events,u32 *points,u8 *states)')
WRAPPER=WRAPPER.replace('SourceWorldMapData map;','SourceWorldMapData map;SourceRoomLoadInput input={patterns,bank2,bank11,map_bank,bank4,hud,1};SourceRoomLoadData loading;SourceRoomLoadOutput loaded;u8 room_bytes[2],flags[32],objects[336];')
start=WRAPPER.index(' if(!source_graphics_load_class0(')
end=WRAPPER.index(' snapshot(&clock,&ctx,out);',start)
WRAPPER=WRAPPER[:start]+''' for(n=0;n<16;n++) cells[0xf0+n]=history[n];
 for(n=0;n<32;n++) flags[n]=0xa7;
 for(n=0;n<336;n++) objects[n]=0xcc;
 room_bytes[0]=room;room_bytes[1]=room>>8;
 loading.graphics=&data;loading.map=&map;loading.room=room_bytes;loading.flags=flags;loading.objects=objects;loading.masks=masks;
 if(!source_room_load_class0(&clock,&ctx,&input,&loading,&loaded,point,&log) || log.count>64 || log.points!=17) return 0;
 finish=loaded.finish;
 for(n=0;n<16;n++) history[n]=cells[0xf0+n];
 out[41]=loaded.history.calls;out[42]=loaded.history.restored;out[43]=loaded.history.last_value;out[44]=loaded.completed;
 out[45]=hash(flags,32);out[46]=hash(objects,336);
'''+WRAPPER[end:]

def build_wrapper(actors=False):
 if not actors:return WRAPPER
 s=WRAPPER.replace('0x24bf,0x1780};','0x24bf,0x1780,0x17ae,0x17de,0x1805,0x1839,0x1853};').replace('p->points>=17','p->points>=22')
 s=s.replace('const u8 *hud,','const u8 *hud,const u8 *bank12,').replace('u8 *history,u8 *masks,u32 *out','u8 *history,u8 *masks,u8 *actors,u32 *out')
 s=s.replace('objects[336];','objects[336],progression[256]={0};SourceActorListData list={actors,flags+0x12,room_bytes,masks,progression};')
 s=s.replace('source_room_load_class0(&clock,&ctx,&input,&loading,&loaded,point,&log)','source_room_load_class0_actors(&clock,&ctx,&input,&loading,bank12,&list,&loaded,point,&log)').replace('log.points!=17','log.points!=22')
 return s.replace('out[45]=hash(flags,32);','out[47]=*list.active_count;out[45]=hash(flags,32);')

def compile_helper(actors=False):
 folder=ROOT/('validation/native-room-load-actors' if actors else 'validation/native-room-load');folder.mkdir(exist_ok=True);(folder/'wrapper.c').write_bytes(build_wrapper(actors).encode())
 env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];sdk=ROOT.parents[1]/'work/sgdk'
 built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O3','-Wall','-Wextra','-Werror','-shared','-I'+str(sdk/'inc'),'-I'+str(ROOT/'megadrive/src'),str(folder/'wrapper.c'),*[str(ROOT/'megadrive/src'/(n+'.c')) for n in MODULES],'-o',str(folder/'load.dll')],env=env,capture_output=True,text=True)
 (folder/'compile.log').write_bytes((built.stdout+built.stderr).encode());assert built.returncode==0,built.stderr[-4000:]
 dll=c.CDLL(str(folder/'load.dll'));fn=dll.room_load_case
 u8=c.POINTER(c.c_uint8);u32=c.POINTER(c.c_uint32)
 fn.argtypes=[u32,c.c_uint8,*([u8]*4),c.c_uint16,*([u8]*(10 if actors else 8)),u32,u32,u32,u8];fn.restype=c.c_uint8
 return folder,dll,fn

@lru_cache(maxsize=2)
def reference_manifest(actors):
 archive=ROOT/('analysis/actor-prefix-refresh-research-v0183' if actors else 'analysis/history-refresh-research-v0183')
 manifest=json.loads((archive/'manifest.json').read_bytes());assert manifest['source_sha256']==sha((ROOT/'input/original.sms').read_bytes())
 return archive,{i['path']:i['sha256'] for i in manifest['files']}

def read_reference(path,actors):
 archive,hashes=reference_manifest(actors);relative=path.relative_to(ROOT).as_posix();raw=(path if path.exists() else archive/relative).read_bytes();assert sha(raw)==hashes[relative],relative
 return raw

def records(folder,region,actors=False):
 raw=read_reference(folder/f'{region}-foreground-phase-records.bin',actors);meta=read_reference(folder/f'{region}-foreground-m1-records.bin',actors);hud=read_reference(folder/f'{region}-hud-context-records.bin',actors);history=read_reference(folder/f'{region}-history-context-records.bin',actors)
 count=len(raw)//800;assert len(raw)==count*800 and len(meta)==len(hud)==count*16 and len(history)==count*277
 rows=[]
 for n in range(count):
  pc,time=struct.unpack_from('<2Q',raw,n*800);m1,refresh,_=struct.unpack_from('<Q2I',meta,n*16)
  rows.append(dict(pc=pc,time=time,phase=list(struct.unpack_from('<12I',raw,n*800+16)),ram=raw[n*800+64:n*800+400],audio=raw[n*800+400:n*800+800],m1=m1,refresh=refresh,hud=hud[n*16:(n+1)*16],context=history[n*277:(n+1)*277]))
 if actors:
  raw=read_reference(folder/f'{region}-actor-load-context-records.bin',actors);assert len(raw)==count*769
  for n,r in enumerate(rows):r.update(actors=raw[n*769:n*769+768],active_count=raw[n*769+768])
 return rows

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--actors',action='store_true');args=parser.parse_args();actor_mode=args.actors;pcs=PCS+[0x17ae,0x17de,0x1805,0x1839,0x1853] if actor_mode else PCS
 folder,dll,fn=compile_helper(actor_mode);rom=(ROOT/'input/original.sms').read_bytes();source_report=json.loads((ROOT/'analysis/history_refresh_phase_report.json').read_bytes());assert source_report['cases']==24 and json.loads((ROOT/'analysis/paid_passage_reference.json').read_bytes())['source_sha256']==sha(rom)
 byte_array=lambda data:(c.c_uint8*len(data)).from_buffer_copy(data)
 low=byte_array(rom[:32768]);banks={n:byte_array(rom[n*16384:(n+1)*16384]) for n in [2,4,6,8,9,11,12]};patterns=byte_array(rom[0x3c010:]);cases=[];results=[]
 from validate_native_graphics_load import fnv
 for town,target,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_bytes())['routes']:
  for mask in [0,255]:
   source_folder=ROOT/f"validation/{'actor-prefix-refresh' if actor_mode else 'history-refresh'}/{town:02x}-{mask:02x}"
   for region in ['auto','pal']:
    observed=records(source_folder,region,actor_mode);cycles=json.loads(read_reference(source_folder/f'{region}-cycle-events.json',actor_mode));start=next(e[2] for e in cycles if e[1]==0x16d0 and e[4]==target);entry=next(r for r in observed if r['pc']==0x16d0 and r['time']==start)
    assert int.from_bytes(entry['context'][:2],'little')==target
    ram=byte_array(entry['ram']);audio=byte_array(entry['audio']);history=byte_array(entry['context'][2:18]);masks=byte_array(entry['context'][18:274]);hud=byte_array(entry['hud']);out=(c.c_uint32*(48 if actor_mode else 47))();events=(c.c_uint32*384)();points=(c.c_uint32*(len(pcs)*18))();states=(c.c_uint8*(len(pcs)*736))();actors=(c.c_uint8*768)();tag=(town,mask,region)
    tail=[hud]+([banks[12]] if actor_mode else [])+[history,masks]+([actors] if actor_mode else [])+[out,events,points,states]
    assert fn((c.c_uint32*12)(*entry['phase']),entry['refresh'],ram,audio,low,banks[6],target,banks[8+(target>>7)],patterns,banks[2],banks[11],banks[4],*tail),(tag,'rejected')
    irq_events=json.loads(read_reference(source_folder/f'{region}-audio-irq-events.json',actor_mode))
    for n,pc in enumerate(pcs):
     end=next(r for r in observed if r['pc']==pc and r['time']>start);p=list(points[n*18:(n+1)*18]);state=bytes(states[n*736:(n+1)*736]);phase=end['phase'];delta=((phase[0]-phase[2]+0x80000000)&0xffffffff)-0x80000000
     assert state[336:]==end['audio'] and all(state[i]==end['ram'][i] for i in range(336) if i not in [0x1b,0x20,0x21,0x22,0x23]),(tag,hex(pc),'RAM/audio')
     assert p[0]==(phase[1]*3420+delta)%(entry['phase'][3]*3420) and p[2]==end['time']-start,(tag,hex(pc),'phase/time')
     assert p[10]==end['refresh'] and p[4]+p[6]==end['m1']-entry['m1'],(tag,hex(pc),'M1/R')
     assert (p[11],p[13],p[14])==(phase[8],phase[10],1) and not p[12] and not p[16],(tag,hex(pc),'latches')
     expected=[(e[2]-start,bool(e[5])) for e in irq_events if e[1]==0x137 and start<e[2]<end['time']]
     assert expected==[(events[j*6],bool(events[j*6+5])) for j in range(p[7])],(tag,hex(pc),'IRQ schedule')
    assert bytes(history)==end['context'][2:18] and bytes(masks)==end['context'][18:274],(tag,'history/masks')
    flags=bytearray(32)
    if actor_mode:
     flags[0x12]=end['active_count'];assert bytes(actors)==end['actors'] and out[47]==end['active_count'],(tag,'actor records/count')
    assert out[41]==3 and out[44]==(6 if actor_mode else 5) and not out[40] and out[45]==fnv(flags) and out[46]==fnv(bytes(336)),(tag,'prefix')
    restored=sum(a==0 and b==255 for a,b in zip(entry['context'][18:274],masks));assert out[42]==restored
    result=dict(town=town,target=target,mask=mask,region=region,checkpoints=len(pcs),wall_master_cycles=out[2],foreground_tstates=out[3],foreground_m1=out[4],irq_m1=out[6],irqs=out[7],full_irqs=sum(bool(events[j*6+5]) for j in range(out[7])),calls=out[41],restored=out[42],exit_refresh=out[10],seed=int.from_bytes(bytes(ram[0x28:0x2a]),'little'))
    cases.append(dict(room=target,hud=list(entry['hud']),phase=entry['phase'],refresh=entry['refresh'],ram=list(entry['ram']),audio=list(entry['audio']),history=list(entry['context'][2:18]),masks=list(entry['context'][18:274]),expected=list(out),events=list(events[:out[7]*6]),points=list(points),states=list(states),after_history=list(history),after_masks=list(masks)))
    if actor_mode:cases[-1]['actors']=list(actors)
    results.append(result);print(result,flush=True)
 assert len(cases)==24
 (folder/'cases.json').write_bytes((json.dumps(cases,separators=(',',':'))+'\n').encode())
 report=dict(passed=True,actor_list_included=actor_mode,cases=len(cases),checkpoints=len(cases)*len(pcs),rng_calls=len(cases)*3,rows=results,module_sha256={n+'.c':sha((ROOT/'megadrive/src'/(n+'.c')).read_bytes()) for n in MODULES},source_sha256=sha(rom),playable_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_reference_manifest_sha256=sha((reference_manifest(actor_mode)[0]/'manifest.json').read_bytes()),headers_sha256={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['source_room_load.h','source_actor_list.h','source_room_history_timed.h']},production_clock_wired=False,limits=['Single observed16D0 entry R/phase/RAM/audio/HUD/history/masks for each unchanged source exit. No intermediate injection.',f'{len(pcs)} checkpoints include live audio IRQ/R/M1/time and331 compact RAM/400 audio bytes; final seed/history/masks and native clears also checked. Actor mode additionally compares final768 actor bytes/count.','Six controlled saved-bit0 class0 outdoor destinations, C0AC0. Actor graphics from1853, physical renderer/pacing, boot entry clock, other map classes, boss suppression and full campaign remain open.'])
 (ROOT/('analysis/native_room_load_actors_report.json' if actor_mode else 'analysis/native_room_load_report.json')).write_bytes((json.dumps(report,indent=2)+'\n').encode())

if __name__=='__main__':main()
