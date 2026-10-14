"""Actual six paid passage entrances, confirmation/payment and opposite exits."""
import contextlib,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_key_door_gameplay import initial_room,rle_planes,maps
def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 source=(ROOT/'input/original.sms').read_bytes();_,ext,_,_,arrays,_=initial_room(source);doors=json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_doors'];cases=[]
 for region in ['auto','pal']:
  matrix=[('%02x'%t,t,20,True,False) for t in [0x1a,0x3c,0x36,0x87,0x6d,0x96]]
  matrix += [('exact',0x1a,10,True,False),('poor',0x1a,9,True,False),('decline',0x1a,20,False,False),('menu',0x1a,20,True,True)]
  routes=json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']
  for name,town,initial_gold,accepted,menu in matrix:
   house=159;x,y=136,72;route=next(r for r in routes if r[0]==town);target=route[1];paid=accepted and initial_gold>=10
   door=next(d for d in doors if d['room']==town and d['target']==house)
   cells=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][town*2:town*2+2],'little');rle_planes(arrays['world_room_streams'],offset,cells,0,1);osms,omd=maps(cells,ext)
   traces={};patterns={};source_clock=[];births={};gold_changes={};huds={};cell_samples={};confirm_maps={}
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    writes=[]
    def add(f,k,v):writes.append((f,sy[k],v.to_bytes(2,'big')))
    if tag=='sms':
     writes=[(3100,0x200+target,b'\0'),(3100,0x100+target,b'\1'),(3100,0xdd,bytes([initial_gold])),(3100,0x100+town,b'\0'),(3120,0xb9,town.to_bytes(2,'little')),(3120,0xa4,door['script_entry'].to_bytes(2,'little')),(3120,0x1c00,bytes(cells)),(3120,0x1600,osms),(3120,0x600,bytes(768)),(3120,0x304,b'\x01'),(3120,0x301,b'\x01'),(3120,0x303,b'\x03'),(3120,0x30a,b'\0'),(3120,0x310,(door['y']<<8).to_bytes(2,'little')+((door['x']-1)<<8).to_bytes(2,'little')+bytes(2)+(256).to_bytes(2,'little')),(3400,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')+bytes(4)),(3400,0x301,b'\x01'),(3400,0x303,b'\x03\0\0'),(3400,0x30a,b'\0')]
    else:
     writes=[(3100,sy['game_save_state']+0x150+target,b'\0'),(3100,sy['game_save_state']+0x50+target,b'\1'),(3100,sy['game_save_state']+0x50+town,b'\0'),(3120,sy['scratch']+0x800,bytes(cells)),(3120,sy['sms_vram']+0x3800,osms),(3120,sy['world_new_md'],omd),(3120,sy['world_actor_state'],bytes(768))]
     for f,k,v in [(3100,'hero_gold',initial_gold),(3120,'room_id',town),(3120,'world_graphics_class',0),(3120,'hero_y',door['y']<<8),(3120,'hero_x',(door['x']-1)<<8),(3120,'hero_dy',0),(3120,'hero_dx',256),(3120,'hero_counter',1),(3120,'hero_state',1),(3120,'hero_flags',3),(3120,'hero_direction',0),(3400,'hero_y',y<<8),(3400,'hero_x',x<<8),(3400,'hero_dy',0),(3400,'hero_dx',0),(3400,'hero_state',1),(3400,'hero_flags',3),(3400,'hero_counter',0),(3400,'hero_hurt',0),(3400,'hero_direction',0)]:add(f,k,v)
    rows={};tiles={};arrival=[None];changes=[];last_gold=[initial_gold];hud=[None];samples={};confirm=[None]
    def observe(f,r):
     if f==3399:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');delta=((read32('vtimer')-shift)&255)-source_clock[0];writes.append((3400,sy['world_clock_shift'],((shift+delta)&0xffffffff).to_bytes(4,'big')))
     if f<3400:return
     if tag=='sms':
      fields=[r[0xdd],r[0xbb],r[0xbd],r[0xbe],r[0x100+target]];current_room=int.from_bytes(r[0xb9:0xbb],'little');active=False;room_cells=bytes(r[0x1c00:0x1ca0]);position=[int.from_bytes(r[a:a+2],'little') for a in [0x312,0x310]]
     else:
      data=lambda k,n:bytes(r[(sy[k]+i)^1] for i in range(n));w=lambda k:int.from_bytes(data(k,2),'big');fields=[w('hero_gold'),w('house_return_room'),w('house_return_y')>>8,w('house_return_x')>>8,data('game_save_state',0x250)[0x50+target]];current_room=w('room_id');active=w('house_dialogue_active');room_cells=data('scratch',0x8a0)[0x800:0x8a0];position=[w('hero_x'),w('hero_y')]
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
    with contextlib.redirect_stdout(io.StringIO()):run(rom,4800,ROOT/f'validation/paid-passage-{name}-{region}-{tag}',{3600,4100,4500,4800},presses,ram_writes=sorted(writes,key=lambda x:x[0]),ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
    assert tag=='sms' or arrival[0] is not None,(region,hex(town),tag,'gold interaction not reached',rows);traces[tag]=rows;patterns[tag]=tiles;births[tag]=arrival[0];gold_changes[tag]=changes;cell_samples[tag]=samples;confirm_maps[tag]=confirm[0]
   levels=[0,3,5,7]
   cram={tag:(ROOT/f'validation/paid-passage-{name}-{region}-{tag}/cram_04800.bin').read_bytes() for tag in ['sms','md']}
   for n in range(16,31):
    color=int.from_bytes(cram['sms'][n*2:n*2+2],'little')&63;expected=levels[color&3]|(levels[(color>>2)&3]<<3)|(levels[(color>>4)&3]<<6)
    actual=int.from_bytes(cram['md'][n*2:n*2+2],'little')&511;assert actual==expected,(region,name,'foreground palette',n,color,expected,actual)
   assert confirm_maps['sms']==confirm_maps['md'],('confirmation frame',name,region,confirm_maps)
   for tag,changes in gold_changes.items():assert all(changes[n][0]-changes[n-1][0]==2 for n in range(1,len(changes))),(tag,changes)
   assert [g for f,g in gold_changes['sms']]==[g for f,g in gold_changes['md']]
   assert traces['sms']==traces['md'],(region,hex(town),'gift fields/restore',traces)
   assert patterns['sms']==patterns['md'],(region,hex(town),'dialogue bitmap','retained differing patterns')
   assert traces['md'][4100]['room']==house and traces['md'][4500]['room']==(target if paid else house),traces
   assert traces['md'][4800]['fields'][0]==initial_gold-(10 if paid else 0)
   assert cell_samples['md'][4100][0x38]==1 if paid else cell_samples['md'][4100][0x38]!=1
   differences={}
   for f in [4100,4500,4800]:
    a=cell_samples['sms'][f];b=cell_samples['md'][f];diff=[n for n in range(160) if a[n]!=b[n]]
    assert all(0x24<=a[n]<0x30 and a[n]^b[n]==1 for n in diff),(region,name,'static room cells',f,diff)
    differences[f]=diff
   if paid:assert traces['md'][4800]['position']==[route[3]<<8,route[2]<<8] and traces['md'][4800]['fields'][4]==1
   cases.append(dict(region=region,scenario=name,town=town,target=target,initial_gold=initial_gold,paid=paid,inventory_roundtrip=menu,native_dialogue_active_first_observed_frame=births['md'],gold_change_frames=gold_changes,unit_cadence_two_frames_exact=True,final_fields=traces['md'][4800],prompt_bitmap_bytes_exact=1040,final_foreground_colors_exact=15,confirmation_frame_bytes_exact=48,static_cells_samples_exact=3,animated_cell_difference_indices=differences,normal_UP_walk_to_opposite_exit=paid));print(region,name,'price/payment/opening/opposite exit exact',flush=True)
 limits=['Original source ROM unpatched. Controlled actual six town doors, hero setup and initial clock alignment. Destination enemy mask is seeded0 before entry to isolate the exit from unrelated encounters/RNG; no post-load actor mutation. Normal UP/C payment, refusal/poor/exact funds and inventory roundtrip; successful cases walk UP through the top exit to the other town.', 'Prompt1040-byte bitmap and48 confirmation frame bytes, gold sequence/two-frame cadence, origin/target/return coordinates, final hero position, destination bit marking and15 static foreground colors compare (clock-animated color31 excluded). Static160-cell samples exclude animated NPC poses and retain differences. Absolute fade/loading/text timing and natural full progression unproved.']
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=limits)
 (ROOT/'validation/paid_passage_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
