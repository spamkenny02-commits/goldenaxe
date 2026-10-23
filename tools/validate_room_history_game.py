"""Exercise history and mask restoration in the playable ROM, via normal room crossings."""
import hashlib,json,re
from run_core import ROOT,run
from validate_actor_tick import PRESSES

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
 results=[]
 for region in ['auto','pal']:
  events=[];previous=[None];restored=[];observed=[0];initial=[False]
  masks=bytes(0 if i&1 else 1 for i in range(256))
  def read(r,key,n):return bytes(r[(sy[key]+i)^1] for i in range(n))
  def observe(frame,ram):
   h=read(ram,'world_recent_rooms',16);state=read(ram,'game_save_state',592);room=int.from_bytes(read(ram,'room_id',2),'big');m=state[0x150:]
   if frame==2500:assert h[0]==0x95 and h[1:]==bytes(15);initial[0]=True
   if frame>=2550:
    observed[0]+=1
    if previous[0] is not None:
     oldh,oldm,oldroom=previous[0]
     if h!=oldh:
      assert h[1:]==oldh[:15],('queue shift',region,frame,h.hex(),oldh.hex())
      events.append(dict(frame=frame,room=room,history=h.hex()))
     for i,(a,b) in enumerate(zip(oldm,m)):
      if a==0 and b==255 and i!=oldroom:
       assert i not in h,('recent room restored',region,frame,i,h.hex());restored.append(dict(frame=frame,room=i))
      if a==1 and i!=oldroom:assert b==1,('partially cleared room reset',region,frame,i,b)
    previous[0]=(h,m,room)
  run(ROOT/'gaw-megadrive.bin',3600,ROOT/f'validation/room-history/{region}',{2500,3100,3500},PRESSES,ram_writes=[(2550,sy['game_save_state']+0x150,masks)],ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert initial[0] and len(events)>=2 and len(restored)>=1,(region,events,restored)
  results.append(dict(region=region,history_events=events,restored=restored,observed_frames=observed[0],initial_history_exact=True))
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();report=dict(passed=True,md_sha256=hashlib.sha256(rom).hexdigest(),results=results,rules=json.loads((ROOT/'analysis/room_history_rules_report.json').read_bytes()),limits=['Native room crossings with controlled persistence masks; partial masks protected.','Exact RNG stream, Continue/death flows and complete campaign remain unvalidated.'])
 (ROOT/'analysis/room_history_v0274_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
