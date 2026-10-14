"""Actual six paid passage entrances, confirmation/payment and opposite exits."""
import contextlib,hashlib,io,json,re,sys,ctypes as c
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_key_door_gameplay import initial_room,rle_planes,maps
def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 source=(ROOT/'input/original.sms').read_bytes();_,ext,_,_,arrays,_=initial_room(source);doors=json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_doors'];cases=[]
 for region in ['auto','pal']:
  matrix=[('combat',0x6d,20,True,False)]
  routes=json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']
  for name,town,initial_gold,accepted,menu in matrix:
   house=159;x,y=136,72;route=next(r for r in routes if r[0]==town);target=route[1];paid=accepted and initial_gold>=10
   door=next(d for d in doors if d['room']==town and d['target']==house)
   cells=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][town*2:town*2+2],'little');rle_planes(arrays['world_room_streams'],offset,cells,0,1);osms,omd=maps(cells,ext)
   profiles={};traces={};patterns={};source_clock=[];births={};gold_changes={};huds={};cell_samples={};confirm_maps={}
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    writes=[]
    def add(f,k,v):writes.append((f,sy[k],v.to_bytes(2,'big')))
    if tag=='sms':
     writes=[(3100,0x100+target,b'\1'),(3100,0xdd,bytes([initial_gold])),(3100,0x100+town,b'\0'),(3120,0xb9,town.to_bytes(2,'little')),(3120,0xa4,door['script_entry'].to_bytes(2,'little')),(3120,0x1c00,bytes(cells)),(3120,0x1600,osms),(3120,0x600,bytes(768)),(3120,0x304,b'\x01'),(3120,0x301,b'\x01'),(3120,0x303,b'\x03'),(3120,0x30a,b'\0'),(3120,0x310,(door['y']<<8).to_bytes(2,'little')+((door['x']-1)<<8).to_bytes(2,'little')+bytes(2)+(256).to_bytes(2,'little')),(3400,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')+bytes(4)),(3400,0x301,b'\x01'),(3400,0x303,b'\x03\0\0'),(3400,0x30a,b'\0')]
    else:
     writes=[(3100,sy['game_save_state']+0x50+target,b'\1'),(3100,sy['game_save_state']+0x50+town,b'\0'),(3120,sy['scratch']+0x800,bytes(cells)),(3120,sy['sms_vram']+0x3800,osms),(3120,sy['world_new_md'],omd),(3120,sy['world_actor_state'],bytes(768))]
     for f,k,v in [(3100,'hero_gold',initial_gold),(3120,'room_id',town),(3120,'world_graphics_class',0),(3120,'hero_y',door['y']<<8),(3120,'hero_x',(door['x']-1)<<8),(3120,'hero_dy',0),(3120,'hero_dx',256),(3120,'hero_counter',1),(3120,'hero_state',1),(3120,'hero_flags',3),(3120,'hero_direction',0),(3400,'hero_y',y<<8),(3400,'hero_x',x<<8),(3400,'hero_dy',0),(3400,'hero_dx',0),(3400,'hero_state',1),(3400,'hero_flags',3),(3400,'hero_counter',0),(3400,'hero_hurt',0),(3400,'hero_direction',0)]:add(f,k,v)
    timing=[];previous_event=[0];core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_timing_libretro.dll';dll=c.CDLL(str(core));dll.gaw_timing_reset();dll.gaw_timing_count.restype=c.c_uint;dll.gaw_timing_events.restype=c.POINTER(c.c_uint64)
    profile={};rows={};tiles={};arrival=[None];changes=[];last_gold=[initial_gold];hud=[None];samples={};confirm=[None]
    def observe(f,r):
     if tag=='sms':
      count=dll.gaw_timing_count();events=dll.gaw_timing_events()
      for i in range(previous_event[0],count):
       if f>=4200:timing.append([f]+[events[i*8+k] for k in range(8)])
      previous_event[0]=count
     if f==3399:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');delta=((read32('vtimer')-shift)&255)-source_clock[0];writes.append((3400,sy['world_clock_shift'],((shift+delta)&0xffffffff).to_bytes(4,'big')))
     if f<3400:return
     if tag=='sms':
      fields=[r[0xdd],r[0xbb],r[0xbd],r[0xbe],r[0x100+target]];current_room=int.from_bytes(r[0xb9:0xbb],'little');active=False;room_cells=bytes(r[0x1c00:0x1ca0]);position=[int.from_bytes(r[a:a+2],'little') for a in [0x312,0x310]]
     else:
      data=lambda k,n:bytes(r[(sy[k]+i)^1] for i in range(n));w=lambda k:int.from_bytes(data(k,2),'big');fields=[w('hero_gold'),w('house_return_room'),w('house_return_y')>>8,w('house_return_x')>>8,data('game_save_state',0x250)[0x50+target]];current_room=w('room_id');active=w('house_dialogue_active');room_cells=data('scratch',0x8a0)[0x800:0x8a0];position=[w('hero_x'),w('hero_y')]
     if f>=4200:
      if tag=='sms':actors=bytes(r[0x600:0x900]);hero=[r[0x301],r[0x305],r[0x30a],r[0x30b],r[0x318]]+position;clock=r[0x2f];state=r[0x1d]
      else:
       actors=data('world_actor_state',768);hero=[w(k) for k in ['hero_state','hero_hurt','hero_direction','hero_animation','hero_health']]+position;u32=lambda k:int.from_bytes(data(k,4),'big');clock=(u32('vtimer')-u32('world_clock_shift'))&255;state=w('game_state')
      profile[f]=dict(room=current_room,hero=hero,state=state,clock=clock,actors=actors.hex(),resume_phase=w('resume_phase') if tag=='md' else None)
     if fields[0]!=last_gold[0]:changes.append((f,fields[0]));last_gold[0]=fields[0]
     if tag=='md' and f==3600:
      v=data('sms_vram',0x4000);confirm[0]=b''.join(v[0x39a6+n*64:0x39b2+n*64] for n in range(4))
     if active and arrival[0] is None:arrival[0]=f
     if f in [4100,4500,4800]:
      rows[f]=dict(fields=fields,room=current_room,position=position);samples[f]=room_cells
     if f==3600:tiles[f]=bytes(r[0x1100:0x1510]) if tag=='sms' else data('scratch',1040)
    def vram(f,v):
     if tag=='sms' and f==3600:confirm[0]=b''.join(bytes(v[0x39a6+n*64:0x39b2+n*64]) for n in range(4))
    presses=([(200,220,0)] if tag=='sms' else [])+PRESSES[:8]+[(3125,3145,4),(3410,3410,4),(3700,3704,8),(3900,3904,8)]
    if not accepted:presses.append((3690,3694,5))
    if paid:presses.append((4200,4240,4))
    if menu:presses.extend([(4000,4004,0),(4070,4074,0)])
    with contextlib.redirect_stdout(io.StringIO()):run(rom,4800,ROOT/f'validation/paid-passage-{name}-{region}-{tag}',{3600,4100,4500,4800},presses,ram_writes=sorted(writes,key=lambda x:x[0]),ram_observer=observe,vram_observer=vram,core=core if tag=='sms' else None,core_options={'genesis_plus_gx_region_detect':region})
    if tag=='sms':(ROOT/f'validation/paid-passage-combat/{region}-cycle-events.json').write_text(json.dumps(timing)+'\n')
    assert tag=='sms' or arrival[0] is not None,(region,hex(town),tag,'gold interaction not reached',rows);traces[tag]=rows;patterns[tag]=tiles;births[tag]=arrival[0];gold_changes[tag]=changes;cell_samples[tag]=samples;confirm_maps[tag]=confirm[0];profiles[tag]=profile
   folder=ROOT/'validation/paid-passage-combat';folder.mkdir(exist_ok=True)
   (folder/f'{region}-profiles.json').write_text(json.dumps(profiles,separators=(',',':'))+'\n')
   summary={}
   for tag,p in profiles.items():
    loaded=next((f for f,r in p.items() if r['room']==target and bytes.fromhex(r['actors'])[0]),None)
    ready=next((f for f,r in p.items() if r['room']==target and r['state']==12),None)
    first_hit=next((f for f,r in p.items() if r['hero'][4]<24),None)
    zero=next((f for f,r in p.items() if loaded and f>=loaded and r['hero'][0]==0),None)
    idle=next((f for f,r in p.items() if zero and f>zero and r['hero'][0]==1),None)
    spawn=[]
    for slot in range(6):
     spawn.append(next((dict(frame=f,x=a[0x13],y=a[0x11],direction=a[10]) for f,r in p.items() if loaded and f>=loaded and (a:=bytes.fromhex(r['actors'])[slot*48:(slot+1)*48])[1]!=0),None))
    summary[tag]=dict(first_loaded=loaded,first_state12_observed=ready,first_hit=first_hit,first_idle_after_load=idle,idle_clock=p[idle]['clock'] if idle else None,spawn_events=spawn,loaded_row=p.get(loaded))
   (folder/f'{region}-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
   print(region,{tag:{k:v for k,v in r.items() if not k.endswith('_row')} for tag,r in summary.items()},flush=True)
   cases.append(dict(region=region,summary=summary))
 limits=['Diagnostic only: unpatched original SMS and current native ROM, controlled actual6D paid passage/hero/initial clock, original destination enemies retained. No per-choice RNG injection or actor clearing.', '601 frame samples4200..4800 capture room/hero/clock/full768-byte actor state in PAL/NTSC. Source/native profiles are not asserted equal. Native first_state12_observed includes synchronous frontend work and is not a gameplay-ready boundary; first_idle_after_load uses the transition from initialized hero0 to idle1.', 'Differences in initialization/spawn positions/contact remain open. Absolute load work, original refresh-register RNG and natural full progression are unproved.']
 report=dict(diagnostic_only=True,md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=limits)
 (ROOT/'validation/paid_passage_combat_cycle_profile_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
