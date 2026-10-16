"""Actual six paid passage entrances, confirmation/payment and opposite exits."""
import contextlib,hashlib,io,json,re,sys,ctypes as c
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_key_door_gameplay import initial_room,rle_planes,maps
def main(town_id=0x6d,enemy_mask=None,output_name='paid-passage-loader',core_name='genesis_plus_gx_loader_libretro.dll',capture_music=False):
 folder=ROOT/'validation'/output_name;folder.mkdir(parents=True,exist_ok=True)
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 source=(ROOT/'input/original.sms').read_bytes();_,ext,_,_,arrays,_=initial_room(source);doors=json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_doors'];cases=[]
 for region in ['auto','pal']:
  matrix=[('combat',town_id,20,True,False)]
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
    if enemy_mask is not None:writes.append((3100,0x200+target if tag=='sms' else sy['game_save_state']+0x150+target,bytes([enemy_mask])))
    timing=[];previous_event=[0];core=ROOT.parents[1]/'work/genesis-plus-gx'/core_name;dll=c.CDLL(str(core));dll.gaw_timing_reset();dll.gaw_timing_count.restype=c.c_uint;dll.gaw_timing_events.restype=c.POINTER(c.c_uint64)
    profile={};rows={};tiles={};arrival=[None];changes=[];last_gold=[initial_gold];hud=[None];samples={};confirm=[None];previous_hero=[0];audio_events=[];audio_m1=bytearray();previous_audio=[0]
    if hasattr(dll,'gaw_audio_irq_m1_events'):dll.gaw_audio_irq_m1_events.restype=c.POINTER(c.c_uint8)
    live_prefix_records=bytearray();previous_prefix=[0]
    live_envelope_records=bytearray();live_envelope_m1=bytearray();previous_envelope=[0]
    if hasattr(dll,'gaw_live_envelope_m1_events'):dll.gaw_live_envelope_m1_events.restype=c.POINTER(c.c_uint8)
    wait_records=bytearray();previous_wait=[0];wait_entries=bytearray();foreground_phases=bytearray();foreground_extra=bytearray();previous_fore=[0]
    if hasattr(dll,'gaw_map_extra_events'):dll.gaw_map_extra_events.restype=c.POINTER(c.c_uint8)
    hud_context=bytearray();foreground_m1=bytearray()
    if hasattr(dll,'gaw_foreground_m1_events'):dll.gaw_foreground_m1_events.restype=c.POINTER(c.c_uint8)
    rng_refresh=bytearray();previous_rng=[0]
    if hasattr(dll,'gaw_rng_refresh_samples'):
     dll.gaw_rng_refresh_samples.restype=c.c_uint;dll.gaw_rng_refresh_events.restype=c.POINTER(c.c_uint64)
    if hasattr(dll,'gaw_hud_context_events'):dll.gaw_hud_context_events.restype=c.POINTER(c.c_uint8)
    if hasattr(dll,"gaw_foreground_phase_samples"):
     dll.gaw_foreground_phase_samples.restype=c.c_uint;dll.gaw_foreground_phase_events.restype=c.POINTER(c.c_uint8)
    if hasattr(dll,"gaw_wait_entry_events"):dll.gaw_wait_entry_events.restype=c.POINTER(c.c_uint8)
    full_records=bytearray();full_m1=bytearray();previous_full=[0];irq_phases=bytearray()
    if hasattr(dll,'gaw_full_irq_m1_events'):dll.gaw_full_irq_m1_events.restype=c.POINTER(c.c_uint8)
    if hasattr(dll,"gaw_irq_phase_events"):dll.gaw_irq_phase_events.restype=c.POINTER(c.c_uint32)
    if hasattr(dll,"gaw_full_irq_samples"):
     dll.gaw_full_irq_samples.restype=c.c_uint;dll.gaw_full_irq_records.restype=c.POINTER(c.c_uint8);dll.gaw_full_irq_nested.restype=c.c_uint
    if hasattr(dll,"gaw_wait_samples"):
     dll.gaw_wait_samples.restype=c.c_uint;dll.gaw_wait_events.restype=c.POINTER(c.c_uint64);dll.gaw_wait_nested_calls.restype=c.c_uint
    if hasattr(dll,'gaw_live_envelope_samples'):
     dll.gaw_live_envelope_samples.restype=c.c_uint;dll.gaw_live_envelope_events.restype=c.POINTER(c.c_uint8)
    if hasattr(dll,'gaw_live_prefix_samples'):
     dll.gaw_live_prefix_samples.restype=c.c_uint;dll.gaw_live_prefix_events.restype=c.POINTER(c.c_uint8)
    if hasattr(dll,'gaw_audio_irq_count'):
     dll.gaw_audio_irq_count.restype=c.c_uint;dll.gaw_audio_irq_events.restype=c.POINTER(c.c_uint64)
    if hasattr(dll,'gaw_hero_samples'):
     dll.gaw_hero_samples.restype=c.c_uint;dll.gaw_hero_entry.restype=c.POINTER(c.c_uint8);dll.gaw_hero_return.restype=c.POINTER(c.c_uint8)
    def observe(f,r):
     if tag=='sms':
      if f==4199:dll.gaw_timing_reset();previous_event[0]=0;previous_hero[0]=0;previous_audio[0]=0;previous_prefix[0]=0;previous_envelope[0]=0;previous_wait[0]=0;previous_full[0]=0;previous_fore[0]=0;previous_rng[0]=0
      if hasattr(dll,'gaw_rng_refresh_samples'):
       count=dll.gaw_rng_refresh_samples()
       if f>=4200 and count>previous_rng[0]:
        base=c.addressof(dll.gaw_rng_refresh_events().contents);rng_refresh.extend(c.string_at(base+previous_rng[0]*64,(count-previous_rng[0])*64))
       previous_rng[0]=count
      if hasattr(dll,'gaw_foreground_phase_samples'):
       fore_count=dll.gaw_foreground_phase_samples()
       if f>=4200 and fore_count>previous_fore[0]:
        base=c.addressof(dll.gaw_foreground_phase_events().contents);foreground_phases.extend(c.string_at(base+previous_fore[0]*800,(fore_count-previous_fore[0])*800))
        if hasattr(dll,'gaw_foreground_m1_events'):
         base=c.addressof(dll.gaw_foreground_m1_events().contents);foreground_m1.extend(c.string_at(base+previous_fore[0]*16,(fore_count-previous_fore[0])*16))
        if hasattr(dll,'gaw_map_extra_events'):
         base=c.addressof(dll.gaw_map_extra_events().contents);foreground_extra.extend(c.string_at(base+previous_fore[0]*8,(fore_count-previous_fore[0])*8))
        if hasattr(dll,'gaw_hud_context_events'):
         base=c.addressof(dll.gaw_hud_context_events().contents);hud_context.extend(c.string_at(base+previous_fore[0]*16,(fore_count-previous_fore[0])*16))
       previous_fore[0]=fore_count
      if hasattr(dll,'gaw_full_irq_samples'):
       assert dll.gaw_full_irq_nested()==0
       full_count=dll.gaw_full_irq_samples()
       if f>=4200 and full_count>previous_full[0]:
        base=c.addressof(dll.gaw_full_irq_records().contents);full_records.extend(c.string_at(base+previous_full[0]*800,(full_count-previous_full[0])*800))
        if hasattr(dll,'gaw_full_irq_m1_events'):
         base=c.addressof(dll.gaw_full_irq_m1_events().contents);full_m1.extend(c.string_at(base+previous_full[0]*152,(full_count-previous_full[0])*152))
        if hasattr(dll,'gaw_irq_phase_events'):
         base=c.addressof(dll.gaw_irq_phase_events().contents);irq_phases.extend(c.string_at(base+previous_full[0]*32,(full_count-previous_full[0])*32))
       previous_full[0]=full_count
      if hasattr(dll,'gaw_wait_samples'):
       assert dll.gaw_wait_nested_calls()==0
       wait_count=dll.gaw_wait_samples()
       if f>=4200 and wait_count>previous_wait[0]:
        base=c.addressof(dll.gaw_wait_events().contents);wait_records.extend(c.string_at(base+previous_wait[0]*112,(wait_count-previous_wait[0])*112))
        if hasattr(dll,'gaw_wait_entry_events'):
         base=c.addressof(dll.gaw_wait_entry_events().contents);wait_entries.extend(c.string_at(base+previous_wait[0]*784,(wait_count-previous_wait[0])*784))
       previous_wait[0]=wait_count
      if hasattr(dll,'gaw_live_envelope_samples'):
       envelope_count=dll.gaw_live_envelope_samples()
       if f>=4200 and envelope_count>previous_envelope[0]:
        base=c.addressof(dll.gaw_live_envelope_events().contents)
        live_envelope_records.extend(c.string_at(base+previous_envelope[0]*824,(envelope_count-previous_envelope[0])*824))
        if hasattr(dll,'gaw_live_envelope_m1_events'):
         base=c.addressof(dll.gaw_live_envelope_m1_events().contents);live_envelope_m1.extend(c.string_at(base+previous_envelope[0]*12,(envelope_count-previous_envelope[0])*12))
       previous_envelope[0]=envelope_count
      if hasattr(dll,'gaw_live_prefix_samples'):
       prefix_count=dll.gaw_live_prefix_samples()
       if f>=4200 and prefix_count>previous_prefix[0]:
        raw=c.string_at(dll.gaw_live_prefix_events(),prefix_count*808)
        live_prefix_records.extend(raw[previous_prefix[0]*808:])
       previous_prefix[0]=prefix_count
      if hasattr(dll,'gaw_audio_irq_count'):
       count_audio=dll.gaw_audio_irq_count();raw_audio=dll.gaw_audio_irq_events()
       if f>=4200 and count_audio>previous_audio[0] and hasattr(dll,'gaw_audio_irq_m1_events'):
        base=c.addressof(dll.gaw_audio_irq_m1_events().contents);audio_m1.extend(c.string_at(base+previous_audio[0]*40,(count_audio-previous_audio[0])*40))
       for i in range(previous_audio[0],count_audio):
        if f>=4200:audio_events.append([f]+[raw_audio[i*14+k] for k in range(14)])
       previous_audio[0]=count_audio
      count=dll.gaw_timing_count();events=dll.gaw_timing_events()
      for i in range(previous_event[0],count):
       if f>=4200:timing.append([f]+[events[i*8+k] for k in range(8)])
      previous_event[0]=count
      if hasattr(dll,'gaw_hero_samples'):
       n=dll.gaw_hero_samples()
       if n!=previous_hero[0] and f>=4200:
        assert n==previous_hero[0]+1,('multiple hero initializations in one observed frame',f,n,previous_hero[0])
        for phase,reader in [('before',dll.gaw_hero_entry),('after',dll.gaw_hero_return)]:
         (folder/f'{region}-hero-{n:03d}-{phase}.bin').write_bytes(c.string_at(reader(),8192))
       previous_hero[0]=n
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
      if capture_music:
       profile[f]['music_track']=r[0x65] if tag=='sms' else w('sound_current_track')
       profile[f]['music_request']=r[0x1e06] if tag=='sms' else w('sound_request')
       profile[f]['music_fade']=(bytes(r[0x1e0b:0x1e0e]) if tag=='sms' else data('sound_ram',0x190)[0xb:0xe]).hex()
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
    with contextlib.redirect_stdout(io.StringIO()):run(rom,4800,folder/f'captures-{region}-{tag}',{3600,4100,4500,4800},presses,ram_writes=sorted(writes,key=lambda x:x[0]),ram_observer=observe,vram_observer=vram,core=core if tag=='sms' else None,core_options={'genesis_plus_gx_region_detect':region})
    if tag=='sms':
     (folder/f'{region}-cycle-events.json').write_text(json.dumps(timing)+'\n')
     if hasattr(dll,'gaw_audio_irq_count'):(folder/f'{region}-audio-irq-events.json').write_text(json.dumps(audio_events)+'\n')
     if hasattr(dll,'gaw_audio_irq_m1_events'):(folder/f'{region}-audio-irq-m1-records.bin').write_bytes(audio_m1)
     if hasattr(dll,'gaw_live_prefix_samples'):(folder/f'{region}-live-prefix-records.bin').write_bytes(live_prefix_records)
     if hasattr(dll,'gaw_irq_phase_events'):(folder/f'{region}-irq-raster-records.bin').write_bytes(irq_phases)
     if hasattr(dll,'gaw_full_irq_samples'):(folder/f'{region}-full-irq-records.bin').write_bytes(full_records)
     if hasattr(dll,'gaw_full_irq_m1_events'):(folder/f'{region}-full-irq-m1-records.bin').write_bytes(full_m1)
     if hasattr(dll,'gaw_foreground_phase_samples'):(folder/f'{region}-foreground-phase-records.bin').write_bytes(foreground_phases)
     if hasattr(dll,'gaw_map_extra_events'):(folder/f'{region}-map-extra-records.bin').write_bytes(foreground_extra)
     if hasattr(dll,'gaw_foreground_m1_events'):(folder/f'{region}-foreground-m1-records.bin').write_bytes(foreground_m1)
     if hasattr(dll,'gaw_hud_context_events'):(folder/f'{region}-hud-context-records.bin').write_bytes(hud_context)
     if hasattr(dll,'gaw_rng_refresh_samples'):(folder/f'{region}-rng-refresh-records.bin').write_bytes(rng_refresh)
     if hasattr(dll,'gaw_wait_entry_events'):(folder/f'{region}-wait-entry-records.bin').write_bytes(wait_entries)
     if hasattr(dll,'gaw_wait_samples'):(folder/f'{region}-save-wait-records.bin').write_bytes(wait_records)
     if hasattr(dll,'gaw_live_envelope_samples'):(folder/f'{region}-live-envelope-records.bin').write_bytes(live_envelope_records)
     if hasattr(dll,'gaw_live_envelope_m1_events'):(folder/f'{region}-live-envelope-m1-records.bin').write_bytes(live_envelope_m1)
    assert tag=='sms' or arrival[0] is not None,(region,hex(town),tag,'gold interaction not reached',rows);traces[tag]=rows;patterns[tag]=tiles;births[tag]=arrival[0];gold_changes[tag]=changes;cell_samples[tag]=samples;confirm_maps[tag]=confirm[0];profiles[tag]=profile
   (folder/f'{region}-profiles.json').write_text(json.dumps(profiles,separators=(',',':'))+'\n')
   summary={}
   for tag,p in profiles.items():
    loaded=next((f for f,r in p.items() if r['room']==target and bytes.fromhex(r['actors'])[0]),None)
    ready=next((f for f,r in p.items() if r['room']==target and r['state']==12),None)
    first_hit=next((f for f,r in p.items() if r['hero'][4]<24),None)
    room_arrival=next((f for f,r in p.items() if r['room']==target),None)
    zero=next((f for f,r in p.items() if room_arrival and f>=room_arrival and r['hero'][0]==0),None)
    idle=next((f for f,r in p.items() if zero and f>zero and r['hero'][0]==1),None)
    spawn=[]
    for slot in range(6):
     spawn.append(next((dict(frame=f,x=a[0x13],y=a[0x11],direction=a[10]) for f,r in p.items() if loaded and f>=loaded and (a:=bytes.fromhex(r['actors'])[slot*48:(slot+1)*48])[1]!=0),None))
    summary[tag]=dict(first_room_arrival=room_arrival,first_loaded=loaded,first_state12_observed=ready,first_hit=first_hit,first_idle_after_load=idle,idle_clock=p[idle]['clock'] if idle else None,spawn_events=spawn,loaded_row=p.get(loaded))
   (folder/f'{region}-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
   print(output_name,region,{tag:{k:v for k,v in r.items() if not k.endswith('_row')} for tag,r in summary.items()},flush=True)
   cases.append(dict(region=region,summary=summary))
 limits=[f'Diagnostic only: unpatched original SMS and current native ROM,controlled actual{town_id:02X} paid passage/hero/initial clock. Destination persistence mask before entry:{enemy_mask}. No per-choice RNG injection or post-load actor clearing.', '601 frame samples4200..4800 capture room/hero/clock/full768-byte actor state in PAL/NTSC. Source/native profiles are not asserted equal. Native first_state12_observed includes synchronous frontend work and is not a gameplay-ready boundary; first_idle_after_load uses the transition from initialized hero0 to idle1.', 'Differences in initialization/spawn positions/contact remain open. Absolute load work, original refresh-register RNG and natural full progression are unproved.']
 report=dict(diagnostic_only=True,md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),timing_core=core_name,cases=cases,full_game_ported=False,limits=limits)
 report_path=ROOT/'validation/paid_passage_loader_phases_report.json' if output_name=='paid-passage-loader' else folder/'phases_report.json'
 report_path.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
