"""Controlled actual gold-house door, original dialogue and restoration."""
import contextlib,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_key_door_gameplay import initial_room,rle_planes,maps
def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 source=(ROOT/'input/original.sms').read_bytes();_,ext,_,_,arrays,_=initial_room(source);doors=json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_doors'];cases=[]
 for region in ['auto','pal']:
  for town,initial_gold in [(0x54,20),(0x90,20),(0x80,250),(0x16,5)]:
   door=next(d for d in doors if d['room']==town and d['target']==63);house=63;x,y=136,88
   cells=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][town*2:town*2+2],'little');rle_planes(arrays['world_room_streams'],offset,cells,0,1);osms,omd=maps(cells,ext)
   traces={};patterns={};source_clock=[];births={};gold_changes={};huds={}
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    writes=[]
    def add(f,k,v):writes.append((f,sy[k],v.to_bytes(2,'big')))
    if tag=='sms':
     writes=[(3100,0xdd,bytes([initial_gold])),(3100,0x100+town,b'\0'),(3120,0xb9,town.to_bytes(2,'little')),(3120,0xa4,door['script_entry'].to_bytes(2,'little')),(3120,0x1c00,bytes(cells)),(3120,0x1600,osms),(3120,0x600,bytes(768)),(3120,0x304,b'\x01'),(3120,0x301,b'\x01'),(3120,0x303,b'\x03'),(3120,0x30a,b'\0'),(3120,0x310,(door['y']<<8).to_bytes(2,'little')+((door['x']-1)<<8).to_bytes(2,'little')+bytes(2)+(256).to_bytes(2,'little')),(3400,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')+bytes(4)),(3400,0x301,b'\x01'),(3400,0x303,b'\x03\0\0'),(3400,0x30a,b'\0')]
    else:
     writes=[(3100,sy['game_save_state']+0x50+town,b'\0'),(3120,sy['scratch']+0x800,bytes(cells)),(3120,sy['sms_vram']+0x3800,osms),(3120,sy['world_new_md'],omd),(3120,sy['world_actor_state'],bytes(768))]
     for f,k,v in [(3100,'hero_gold',initial_gold),(3120,'room_id',town),(3120,'world_graphics_class',0),(3120,'hero_y',door['y']<<8),(3120,'hero_x',(door['x']-1)<<8),(3120,'hero_dy',0),(3120,'hero_dx',256),(3120,'hero_counter',1),(3120,'hero_state',1),(3120,'hero_flags',3),(3120,'hero_direction',0),(3400,'hero_y',y<<8),(3400,'hero_x',x<<8),(3400,'hero_dy',0),(3400,'hero_dx',0),(3400,'hero_state',1),(3400,'hero_flags',3),(3400,'hero_counter',0),(3400,'hero_hurt',0),(3400,'hero_direction',0)]:add(f,k,v)
    rows={};tiles={};arrival=[None];changes=[];last_gold=[initial_gold];hud=[None]
    def observe(f,r):
     if f==3399:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');delta=((read32('vtimer')-shift)&255)-source_clock[0];writes.append((3400,sy['world_clock_shift'],((shift+delta)&0xffffffff).to_bytes(4,'big')))
     if f<3400:return
     if tag=='sms':
      fields=[r[0xdd],r[0x100+town]];current_room=int.from_bytes(r[0xb9:0xbb],'little');active=bool(r[0x100+town]&2)
     else:
      data=lambda k,n:bytes(r[(sy[k]+i)^1] for i in range(n));w=lambda k:int.from_bytes(data(k,2),'big');fields=[w('hero_gold'),data('game_save_state',0x250)[0x50+town]];current_room=w('room_id');active=w('house_dialogue_active')
     if fields[0]!=last_gold[0]:changes.append((f,fields[0]));last_gold[0]=fields[0]
     if tag=='md' and f==4300:hud[0]=data('sms_vram',0x4000)[0x3dd0:0x3dd6]
     if active and arrival[0] is None:arrival[0]=f
     if f in [4000,4300,4600]:
      rows[f]=dict(fields=fields,room=current_room)
      if f==4000:tiles[f]=bytes(r[0x1100:0x1510]) if tag=='sms' else data('scratch',1040)
    def vram(f,v):
     if tag=='sms' and f==4300:hud[0]=bytes(v[0x3dd0:0x3dd6])
    with contextlib.redirect_stdout(io.StringIO()):run(rom,4600,ROOT/f'validation/house-gold-{town:02x}-{region}-{tag}',{4000,4300,4600},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8]+[(3125,3145,4),(3410,3410,4),(3600,3604,8),(4100,4104,8),(4400,4400,4)],ram_writes=sorted(writes,key=lambda x:x[0]),ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
    assert arrival[0] is not None,(region,hex(town),tag,'gold interaction not reached',rows);traces[tag]=rows;patterns[tag]=tiles;births[tag]=arrival[0];gold_changes[tag]=changes;huds[tag]=hud[0]
   assert huds['sms']==huds['md'],('restored gold HUD',huds)
   for tag,changes in gold_changes.items():assert all(changes[n][0]-changes[n-1][0]==2 for n in range(1,len(changes))),(tag,changes)
   assert [g for f,g in gold_changes['sms']]==[g for f,g in gold_changes['md']]
   assert traces['sms']==traces['md'],(region,hex(town),'gift fields/restore',traces)
   assert patterns['sms']==patterns['md'],(region,hex(town),'dialogue bitmap','retained differing patterns')
   assert all(r['room']==house for r in traces['md'].values())
   a=(ROOT/f'validation/house-gold-{town:02x}-{region}-sms/ram_04300.bin').read_bytes();b=(ROOT/f'validation/house-gold-{town:02x}-{region}-md/ram_04300.bin').read_bytes();restored=bytes(b[(sy['sms_vram']+0x3800+n)^1] for n in range(1280))
   animated=set()
   for n in range(160):
    if 0x24<=a[0x1c00+n]<0x30:
     for dy in range(2):
      for dx in range(2):animated.add(((n//16)*2+dy)*32+(n%16)*2+dx)
   map_differences=[n for n in range(640) if restored[n*2:n*2+2]!=a[0x1600+n*2:0x1602+n*2]]
   assert set(map_differences)<=animated,(region,'gold house static restored room map',map_differences,animated)
   assert traces['md'][4300]==traces['md'][4600], 'repeat visit changed reward'
   cases.append(dict(region=region,town=town,house=house,initial_gold=initial_gold,request_frames=births,gold_change_frames=gold_changes,unit_cadence_two_frames_exact=True,restored_gold_HUD_exact=True,final_gold=traces['md'][4600]['fields'][0],dialogue_bitmap_bytes_exact=1040,restored_static_map_words_exact=640-len(animated),animated_map_difference_indices=map_differences,repeat_interaction_no_second_reward=True));print(region,hex(town),'gold/dialogue/restoration exact',flush=True)
 limits=['Controlled actual door entry; hero placed in front of NPC, initial clock aligned. Four gain/loss/saturation cases in PAL/NTSC. Original source executes without routine patches.', 'Final bitmap and gold/save fields compare; animated NPC cells excluded from static map check with raw differences retained. Full frame timing/audio and natural progression remain unproved.']
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=limits)
 (ROOT/'validation/house_gold_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
