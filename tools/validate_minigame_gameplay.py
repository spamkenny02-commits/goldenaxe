"""Actual minigame frontends with controlled RNG inputs, not RNG equivalence."""
import contextlib,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from audit_item_reward_visuals import sms_pixels,md_pixels
from validate_key_door_gameplay import initial_room,rle_planes,maps
def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 source=(ROOT/'input/original.sms').read_bytes();image=bytearray(source);image[0x3a20:0x3a3d]=source[0x4e1:0x4fe];image[0x4e1:0x4e4]=bytes.fromhex('c3003a');image[0x3a00:0x3a0d]=bytes.fromhex('3a7ec0b728043a7fc0c9c3203a');source_test=ROOT/'validation/minigame-live-source.sms';source_test.write_bytes(image);_,ext,_,_,arrays,_=initial_room(source);doors=json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_doors'];cases=[]
 for region in ['auto','pal']:
  for name,rolls,initial_gold,mode in [('ordinary',[0,4,16],80,'decline'),('lucky',[28,16,25,4],80,'decline'),('inverse',[29,0,4,16],80,'decline'),('replay',[0,4,16],80,'replay'),('poor',[],9,'poor'),('entry-no',[],80,'entry-no')]:
   town=0x13
   door=next(d for d in doors if d['room']==town and d['target']==95);house=95;x,y=136,88
   cells=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][town*2:town*2+2],'little');rle_planes(arrays['world_room_streams'],offset,cells,0,1);osms,omd=maps(cells,ext)
   traces={};patterns={};source_clock=[];births={};gold_changes={};huds={};cell_samples={};confirm_tiles={};confirm_maps={}
   for tag,rom in [('sms',source_test),('md',ROOT/'gaw-megadrive.bin')]:
    writes=[]
    def add(f,k,v):writes.append((f,sy[k],v.to_bytes(2,'big')))
    if tag=='sms':
     writes=[(3100,0xdd,bytes([initial_gold])),(3100,0x100+town,b'\0'),(3120,0xb9,town.to_bytes(2,'little')),(3120,0xa4,door['script_entry'].to_bytes(2,'little')),(3120,0x1c00,bytes(cells)),(3120,0x1600,osms),(3120,0x600,bytes(768)),(3120,0x304,b'\x01'),(3120,0x301,b'\x01'),(3120,0x303,b'\x03'),(3120,0x30a,b'\0'),(3120,0x310,(door['y']<<8).to_bytes(2,'little')+((door['x']-1)<<8).to_bytes(2,'little')+bytes(2)+(256).to_bytes(2,'little')),(3400,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')+bytes(4)),(3400,0x301,b'\x01'),(3400,0x303,b'\x03\0\0'),(3400,0x30a,b'\0')]
    else:
     writes=[(3100,sy['game_save_state']+0x50+town,b'\0'),(3120,sy['scratch']+0x800,bytes(cells)),(3120,sy['sms_vram']+0x3800,osms),(3120,sy['world_new_md'],omd),(3120,sy['world_actor_state'],bytes(768))]
     for f,k,v in [(3100,'hero_gold',initial_gold),(3120,'room_id',town),(3120,'world_graphics_class',0),(3120,'hero_y',door['y']<<8),(3120,'hero_x',(door['x']-1)<<8),(3120,'hero_dy',0),(3120,'hero_dx',256),(3120,'hero_counter',1),(3120,'hero_state',1),(3120,'hero_flags',3),(3120,'hero_direction',0),(3400,'hero_y',y<<8),(3400,'hero_x',x<<8),(3400,'hero_dy',0),(3400,'hero_dx',0),(3400,'hero_state',1),(3400,'hero_flags',3),(3400,'hero_counter',0),(3400,'hero_hurt',0),(3400,'hero_direction',0)]:add(f,k,v)
    def seed_for(roll):
     for seed in range(1,65536):
      n=seed^(seed>>5);n=(n^(n<<9))&65535;n^=n>>7
      if n&31==roll:return seed
    for n,roll in enumerate(rolls):
     f=3990+n*400;hx=56+n*16;hy=72
     if tag=='sms':
      writes.extend([(f,0x7e,bytes([1,roll])),(f,0x310,(hy<<8).to_bytes(2,'little')+(hx<<8).to_bytes(2,'little')+bytes(4)),(f,0x301,b'\1'),(f,0x303,b'\3\0\0'),(f,0x30a,b'\0')])
     else:
      writes.append((f,sy['randbase'],seed_for(roll).to_bytes(2,'big')))
      for k,v in [('hero_y',hy<<8),('hero_x',hx<<8),('hero_dy',0),('hero_dx',0),('hero_state',1),('hero_flags',3),('hero_counter',0),('hero_hurt',0),('hero_direction',0)]:add(f,k,v)
    rows={};tiles={};arrival=[None];changes=[];last_gold=[initial_gold];samples={};fonts=[];confirm=[None]
    def observe(f,r):
     if f==3399:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');delta=((read32('vtimer')-shift)&255)-source_clock[0];writes.append((3400,sy['world_clock_shift'],((shift+delta)&0xffffffff).to_bytes(4,'big')))
     if f<3400:return
     if tag=='sms':
      fields=[r[0xdd]];current_room=int.from_bytes(r[0xb9:0xbb],'little');active=current_room==11;cells=bytes(r[0x1c00:0x1ca0])
     else:
      data=lambda k,n:bytes(r[(sy[k]+i)^1] for i in range(n));w=lambda k:int.from_bytes(data(k,2),'big');fields=[w('hero_gold')];current_room=w('room_id');active=w('minigame_active');cells=data('scratch',0x8a0)[0x800:0x8a0]
     if tag=='md' and f==3480:
      v=data('sms_vram',0x4000);confirm[0]=b''.join(v[0x3a26+n*64:0x3a32+n*64] for n in range(4))
     if fields[0]!=last_gold[0]:changes.append((f,fields[0]));last_gold[0]=fields[0]
     if active and arrival[0] is None:arrival[0]=f
     if f in [5700,6600]:
      rows[f]=dict(fields=fields,room=current_room);samples[f]=cells
     if f==(3600 if mode in ['poor','entry-no'] else 5700):tiles[f]=bytes(r[0x1100:0x1510]) if tag=='sms' else data('scratch',1040)
    def vram(f,v):
     if f==3480:
      fonts.extend(sms_pixels(v,n) if tag=='sms' else md_pixels(v,n+16) for n in range(203,207))
      if tag=='sms':confirm[0]=b''.join(bytes(v[0x3a26+n*64:0x3a32+n*64]) for n in range(4))
    presses=([(200,220,0)] if tag=='sms' else [])+PRESSES[:8]+[(3125,3145,4),(3410,3410,4),(3500,3504,8),(3800,3804,8)]
    for n,roll in enumerate(rolls):
     presses.append((4000+n*400,4000+n*400,4))
     if roll>=28:presses.append((4200+n*400,4204+n*400,8))
    if name=='ordinary':presses.extend([(4210,4214,0),(4300,4304,0)])
    if mode=='entry-no':presses.append((3490,3494,5))
    presses.extend([(5800,5804,8),(6100,6104,8),(6300,6304,8)])
    if mode=='decline':presses.append((6000,6004,5))
    with contextlib.redirect_stdout(io.StringIO()):run(rom,6600,ROOT/f'validation/minigame-live-{name}-{region}-{tag}',{3480,3600,3900,4100,4500,4900,5300,5700,6000,6600},presses,ram_writes=sorted(writes,key=lambda x:x[0]),ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
    assert arrival[0] is not None or mode in ['poor','entry-no'],(region,hex(town),tag,'gold interaction not reached',rows);traces[tag]=rows;patterns[tag]=tiles;births[tag]=arrival[0];gold_changes[tag]=changes;cell_samples[tag]=samples;confirm_tiles[tag]=fonts;confirm_maps[tag]=confirm[0]
   assert confirm_tiles['sms']==confirm_tiles['md'],('confirmation font',name,region)
   assert confirm_maps['sms']==confirm_maps['md'],('confirmation frame',name,region,confirm_maps)
   assert [g for f,g in gold_changes['sms']]==[g for f,g in gold_changes['md']]
   assert traces['sms']==traces['md'],(region,hex(town),'gift fields/restore',traces)
   assert patterns['sms']==patterns['md'],(region,hex(town),'dialogue bitmap','retained differing patterns')
   assert traces['md'][5700]['room']==(95 if mode in ['poor','entry-no'] else 11) and traces['md'][6600]['room']==(11 if mode=='replay' else 95), traces
   if mode not in ['poor','entry-no']:assert cell_samples['sms'][5700]==cell_samples['md'][5700],(name,'game cards')
   if mode=='replay':assert traces['md'][6600]['fields'][0]==90 and all(cell_samples['md'][6600][n]==0x3a for n in [3,6,9]+list(range(0x33,0x3d)))
   if mode in ['poor','entry-no']:assert traces['md'][6600]['fields'][0]==initial_gold
   animated_differences=[n for n,(a,b) in enumerate(zip(cell_samples['sms'][6600],cell_samples['md'][6600])) if a!=b]
   assert all(0x24<=cell_samples['sms'][6600][n]<0x30 and cell_samples['sms'][6600][n]^cell_samples['md'][6600][n]==1 for n in animated_differences),(name,'restored static house',animated_differences)
   cases.append(dict(region=region,scenario=name,initial_gold=initial_gold,roll_inputs=rolls,all_observed_unit_gold_changes_exact=True,request_frames=births,gold_change_frames=gold_changes,final_gold=traces['md'][6600]['fields'][0],dialogue_bitmap_bytes_exact=1040,game_and_static_return_cells_exact=(160 if mode in ['poor','entry-no'] else 320)-len(animated_differences),animated_return_difference_indices=animated_differences,confirmation_font_tiles_exact=4,confirmation_frame_bytes_exact=48,inventory_roundtrip_during_game=name=='ordinary',mode=mode,entry_payment_reward_and_decline_return=mode=='decline',replay_deducts_ten_and_resets_cards=mode=='replay',entry_refused_without_payment=mode in ['poor','entry-no']));print(region,name,'payment/cards/bitmap/return exact',flush=True)
 limits=['Actual town13 door into house5F, normal UP/C to accept10-piece cost and original instructions, then ordinary/lucky/inverse selections, reward and decline replay return; also accepted replay with reset and10-piece deduction, insufficient funds and entry refusal. Hero setup and initial clock controlled.', 'SMS04E1 branches to a supplied roll only while overrideC07E is set; otherwise relocated original RNG executes. Native SGDK randbase seeded before each choice to produce the same first five bits. This verifies card mapping/frontends, NOT RNG equivalence or natural probability/timing.', '160 game cells and static return-house cells (animated differences retained) and reward1040-byte bitmap compare; 4 confirmation font tiles/48 frame bytes also compare; ordinary cases open/close inventory after first draw. Absolute entry/exit and publication timing, full frames/audio and natural progression unproved.']
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=limits)
 (ROOT/'validation/minigame_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
