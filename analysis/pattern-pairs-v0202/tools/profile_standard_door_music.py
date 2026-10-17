"""Actual standard house/dungeon entry and exit music ordering diagnostics."""
import contextlib,ctypes as c,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_key_door_gameplay import initial_room,rle_planes,maps

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 source=(ROOT/'input/original.sms').read_bytes();_,ext,_,_,arrays,_=initial_room(source)
 doors=json.loads((ROOT/'analysis/doors_reference.json').read_text());rows=[]
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_hero_libretro.dll'
 for region in ['auto','pal']:
  for name,town,house,kind in [('house',0x50,0x4f,'direct_unconditional_doors'),('dungeon',0x10,0x1f0,'direct_unconditional_dungeon_doors')]:
   door=next(d for d in doors[kind] if d['room']==town and d['target']==house)
   cells=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][town*2:town*2+2],'little');rle_planes(arrays['world_room_streams'],offset,cells,0,1);osms,omd=maps(cells,ext)
   folder=ROOT/f'validation/standard-door-music/{name}-{region}';folder.mkdir(parents=True,exist_ok=True);profiles={};all_events=[]
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    writes=[]
    if tag=='sms':
     writes=[(3100,0x100+town,b'\1'),(3120,0xb9,town.to_bytes(2,'little')),(3120,0xa4,door['script_entry'].to_bytes(2,'little')),(3120,0x1c00,bytes(cells)),(3120,0x1600,osms),(3120,0x600,bytes(768)),(3120,0x304,b'\1'),(3120,0x301,b'\1'),(3120,0x303,b'\3'),(3120,0x30a,b'\0'),(3120,0x310,(door['y']<<8).to_bytes(2,'little')+((door['x']-1)<<8).to_bytes(2,'little')+bytes(2)+(256).to_bytes(2,'little'))]
    else:
     writes=[(3100,sy['game_save_state']+0x50+town,b'\1'),(3120,sy['scratch']+0x800,bytes(cells)),(3120,sy['sms_vram']+0x3800,osms),(3120,sy['world_new_md'],omd),(3120,sy['world_actor_state'],bytes(768))]
     for k,v in [('room_id',town),('world_graphics_class',0),('hero_y',door['y']<<8),('hero_x',(door['x']-1)<<8),('hero_dy',0),('hero_dx',256),('hero_counter',1),('hero_state',1),('hero_flags',3),('hero_direction',0)]:writes.append((3120,sy[k],v.to_bytes(2,'big')))
    dll=c.CDLL(str(core));dll.gaw_timing_reset();dll.gaw_timing_count.restype=c.c_uint;dll.gaw_timing_events.restype=c.POINTER(c.c_uint64);previous=[0];p={}
    video_dll=c.CDLL(str(core if tag=='sms' else ROOT.parents[1]/'work/libretro/genesis_plus_gx_libretro.dll'))
    video_dll.retro_serialize_size.restype=c.c_size_t;video_dll.retro_serialize.argtypes=[c.c_void_p,c.c_size_t];video_dll.retro_serialize.restype=c.c_bool
    def observe(f,r):
     if tag=='sms':
      if f==3099:dll.gaw_timing_reset();previous[0]=0
      count=dll.gaw_timing_count();events=dll.gaw_timing_events()
      for n in range(previous[0],count):
       if f>=3100:all_events.append([f]+[events[n*8+i] for i in range(8)])
      previous[0]=count
     if f<3100:return
     if tag=='sms':room=int.from_bytes(r[0xb9:0xbb],'little');track=r[0x65];state=r[0x301];graphics=r[0x40];fade=bytes(r[0x1e0b:0x1e0e]);clock=r[0x2f]
     else:
      data=lambda k,n:bytes(r[(sy[k]+i)^1] for i in range(n));word=lambda k:int.from_bytes(data(k,2),'big')
      room=word('room_id');track=word('sound_current_track');state=word('hero_state');graphics=word('world_graphics_class');fade=data('sound_ram',0x190)[0xb:0xe];clock=(int.from_bytes(data('vtimer',4),'big')-int.from_bytes(data('world_clock_shift',4),'big'))&255
     buffer=c.create_string_buffer(video_dll.retro_serialize_size());assert video_dll.retro_serialize(buffer,len(buffer))
     base=16+(0x2000 if tag=='sms' else 0x10000+0x2000+5)+16+0x400
     display=bool(buffer.raw[base+0x10101]&64)
     p[f]=dict(room=room,track=track,hero_state=state,graphics=graphics,fade=fade.hex(),clock=clock,display_enabled=display,resume_phase=word('resume_phase') if tag=='md' else None,resume_fade_step=word('resume_fade_step') if tag=='md' else None,resume_contour=word('resume_contour') if tag=='md' else None)
    presses=([(200,220,0)] if tag=='sms' else [])+PRESSES[:8]+[(3125,3145,4),(3400,3415,5)]
    with contextlib.redirect_stdout(io.StringIO()):run(rom,3700,folder/tag,{3300,3600},presses,ram_writes=writes,ram_observer=observe,core=core if tag=='sms' else None,core_options={'genesis_plus_gx_region_detect':region})
    assert any(r['room']==house for r in p.values()),(name,region,tag,'entrance not reached')
    assert p[3700]['room']==town,(name,region,tag,'exit not reached',p[3700])
    profiles[tag]=p
   (folder/'profiles.json').write_text(json.dumps(profiles,separators=(',',':'))+'\n');(folder/'source-events.json').write_text(json.dumps(all_events)+'\n')
   sequences={}
   for tag,p in profiles.items():
    seq=[];last=None
    for f,r in p.items():
     if r['track']!=last:seq.append(dict(frame=f,command=r['track'],room=r['room']));last=r['track']
    sequences[tag]=seq
   rows.append(dict(name=name,town=town,house=house,region=region,music_sequences=sequences))
   print(name,region,sequences,flush=True)
 report=dict(diagnostic_only=True,md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=rows,full_game_ported=False,limits=['Actual standard house/dungeon doors and normal DOWN exit. Controlled exterior/hero fixture at3120;no interior/exit/audio request/state injection. Source ROM unpatched;read-only source cycle markers retained.','Diagnostic source/native music ordering and fade bytes,not waveform/full physical duration equality. Initial cleared outside actors and visited flag are explicit fixtures.'])
 (ROOT/'analysis/standard_door_music_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
