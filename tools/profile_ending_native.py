"""Observe complete original ending after controlled actual final-room boss death."""
import contextlib,hashlib,io,json,sys,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_key_door_gameplay import initial_room,rle_planes,maps

def main():
 source=(ROOT/'input/original.sms').read_bytes();_,ext,_,_,arrays,_=initial_room(source)
 outside=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][32:34],'little');rle_planes(arrays['world_room_streams'],offset,outside,0,1);osms,_=maps(outside,ext)
 door=next(x for x in json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_dungeon_doors'] if x['room']==16)
 writes=[(3120,0xb9,b'\x10\0'),(3120,0xa4,door['script_entry'].to_bytes(2,'little')),(3120,0x1c00,bytes(outside)),(3120,0x1600,osms),(3120,0x600,bytes(768)),(3120,0x310,((door['y']+8)<<8).to_bytes(2,'little')+(door['x']<<8).to_bytes(2,'little')),
 (3400,0xb9,(0x14b).to_bytes(2,'little')),(3400,0xa4,b'\x61\xb7'),(3400,0x14c,b'\x10'),(3400,0x6e,b'\xff\xff\0'),(3400,0x600,bytes(768)),(3400,0xa2,b'\0'),(3400,0x301,b'\0'),(3400,0x303,b'\x03\0'),(3400,0x30a,b'\x03'),(3400,0x310,(80<<8).to_bytes(2,'little')+(241<<8).to_bytes(2,'little')+bytes(4)),(3400,0x1600,bytes(1280)),(3400,0x305,b'\xff'),(3400,0x318,b'\x18')]
 boss=bytearray(768);boss[0]=7;boss[3]=0x40;boss[0x11]=72;boss[0x13]=128
 terminal='--terminal' in sys.argv
 if terminal:boss[1]=4;writes.append((3700,0x301,b'\x0c'))
 writes += [(3700,0x37,b'\x0a'),(3700,0x600,boss),(3700,0x305,b'\0'),(3700,0x318,b'\x18'),(3700,0x310,(112<<8).to_bytes(2,'little')+(168<<8).to_bytes(2,'little')+bytes(4))]
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 converted=[]
 for f,a,b in writes:
  if a in [0xa4]:continue
  if a in [0x600,0x1600,0x1c00,0x6e,0x14c]:
   address={0x600:sy['world_actor_state'],0x1600:sy['sms_vram']+0x3800,0x1c00:sy['scratch']+0x800,0x6e:sy['room_metadata'],0x14c:sy['game_save_state']+0x9c}[a];converted.append((f,address,b));continue
  if a==0x310:
   for n,k in enumerate(['hero_y','hero_x','hero_dy','hero_dx']):
    if n*2<len(b):converted.append((f,sy[k],int.from_bytes(b[n*2:n*2+2],'little').to_bytes(2,'big')))
   continue
  if a==0x303:
   for n,k in enumerate(['hero_flags','hero_counter']):converted.append((f,sy[k],bytes([0,b[n]])))
   continue
  k={0xb9:'room_id',0xa2:'world_actor_count',0x301:'hero_state',0x30a:'hero_direction',0x305:'hero_hurt',0x318:'hero_health',0x37:'world_dungeon_number'}[a]
  converted.append((f,sy[k],int.from_bytes(b,'little').to_bytes(2,'big')))
 converted.append((3120,sy['world_graphics_class'],bytes(2)));writes=sorted(converted,key=lambda x:x[0])
 cases=[]
 for region in ['auto','pal']:
  credit_trace=[];credit_ticks=[0];credit_scroll_previous=[0];credit_captures=[];capture_targets=set();captures={3699,3700,3900,4200,4500,4800,5000,5500,6000,8000,12000,18000,19020};events=[];last=[None];ending=[None];credits=[None];complete=[None];returned=[None];tracks=[];track_last=[None]
  def observe(f,raw):
   if f==3699:
    read32=lambda k:int.from_bytes(bytes(raw[(sy[k]+i)^1] for i in range(4)),'big')
    reference=(ROOT/f'validation/ending-source-{region}/ram_03699.bin').read_bytes()[0x2f]
    shift=read32('world_clock_shift');delta=((read32('vtimer')-shift)&255)-reference
    writes.append((3700,sy['world_clock_shift'],((shift+delta)&0xffffffff).to_bytes(4,'big')))
   if f<3700:return
   data=lambda k,n:bytes(raw[(sy[k]+i)^1] for i in range(n))
   value=lambda k:int.from_bytes(data(k,2),'big')
   r=bytearray(8192)
   for a,k in [(0xb9,'room_id'),(0x310,'hero_y'),(0x312,'hero_x')]:r[a:a+2]=value(k).to_bytes(2,'little')
   for a,k in [(0x1d,'game_state'),(0x37,'world_dungeon_number'),(0x301,'hero_state'),(0x30b,'hero_animation')]:r[a]=value(k)&255
   r[0x308:0x30a]=value('ending_hero_descriptor').to_bytes(2,'little');r[0x600:0x900]=data('world_actor_state',768)
   credit=data('ending_credits',10)
   r[0x1cc0:0x1cc2]=credit[:2]
   for n in [2,4]:r[0x1cc0+n:0x1cc2+n]=int.from_bytes(credit[n:n+2],'big').to_bytes(2,'little')
   r[0x1cc6:0x1cc8]=(0xc900+int.from_bytes(credit[6:8],'big')).to_bytes(2,'little');r[0x19]=credit[8]
   colors=data('sms_palette',64)
   r[0x1ca0:0x1cc0]=bytes(colors[n*2+1] for n in range(32))
   r[0x1e06]=value('sound_request')&255
   word=lambda a:int.from_bytes(r[a:a+2],'little')
   current=dict(frame=f,state=r[0x1d],room=word(0xb9),dungeon=r[0x37],hero_state=r[0x301],hero_y=word(0x310),hero_x=word(0x312),hero_descriptor=word(0x308),hero_pose=r[0x30b],objects=list(r[0x600:0x900:48]),visible_flags=list(r[0x603:0x900:48]),credit_wait=r[0x1cc0],credit_done=r[0x1cc1],credit_scroll=word(0x1cc2),credit_row_address=word(0x1cc4),credit_text_pointer=word(0x1cc6),vscroll=r[0x19],palette=bytes(r[0x1ca0:0x1cc0]).hex())
   key=tuple(str(v) for k,v in current.items() if k not in ['frame','credit_scroll','palette'])
   if key!=last[0]:events.append(current);last[0]=key
   if r[0x1d]==14 and ending[0] is None:ending[0]=f
   if ending[0] is not None and 0xc900<=word(0x1cc6)<=0xce01 and 0x7800<=word(0x1cc4)<0x7f00 and word(0x308)==0x84e1 and credits[0] is None:credits[0]=f
   if credits[0] is not None and r[0x1cc1] and complete[0] is None:complete[0]=f
   if ending[0] is not None and r[0x1d]==0 and returned[0] is None:returned[0]=f
   if ending[0] is not None and word(0x308)==0x84e1 and 0x7800<=word(0x1cc4)<0x7f00 and word(0x1cc6)>0xc900 and (not credit_trace or not credit_trace[-1]['done']):
    credit_ticks[0]+=((word(0x1cc2)-credit_scroll_previous[0])&65535)//48;credit_scroll_previous[0]=word(0x1cc2)
    credit_trace.append(dict(tick=credit_ticks[0],frame=f,state=bytes(r[0x1cc0:0x1cc8]).hex(),vscroll=r[0x19],scroll=word(0x1cc2),done=bool(r[0x1cc1])))
    for tick in [32,600,2000,4000,7000]:
     if tick not in capture_targets and credit_ticks[0]==tick:
      capture_targets.add(tick);captures.add(f+1);credit_captures.append(dict(tick=tick+1,frame=f+1))
   if r[0x1e06] and r[0x1e06]!=track_last[0]:tracks.append([f,r[0x1e06]]);track_last[0]=r[0x1e06]
  folder=ROOT/f'validation/ending-native{"-terminal" if terminal else ""}-{region}'
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'gaw-megadrive.bin',19500,folder,captures,PRESSES+[(3125,3129,4),(3400,3403,7),(19000,19002,8)],ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert ending[0] and credits[0] and complete[0] and returned[0],(region,ending,credits,complete,returned)
  assert any(e['room']==0x14c and e['dungeon']==10 for e in events)
  cases.append(dict(region=region,ending_entered=ending[0],credits_started=credits[0],credits_finished=complete[0],returned_to_title=returned[0],music_requests=tracks,events=events,credit_trace=credit_trace,credit_captures=credit_captures,capture_folder=str(folder.relative_to(ROOT))))
  print(region,'ending',ending[0],'credits',credits[0],complete[0],'title',returned[0],flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,terminal_death_checkpoint_fixture=terminal,limits=['Controlled exterior doorway/departure relocation, normal right scroll into actual14C. Hero invulnerability/HP protect setup. At3700 dungeon number is set10 and all actors are replaced by final-boss death state0 at128,72 and hero168,112/hurt0/HP24. Source death, particles, ending and credits then execute without further RAM/VRAM writes. Normal C at19000 acknowledges completed credits.','Native world clock explicitly aligned to source at3700. Controlled ending profile; compare to original reference before claiming equivalence. Natural victory remains unproved.'])
 (ROOT/f'validation/ending_native{"_terminal" if terminal else ""}_profile.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
