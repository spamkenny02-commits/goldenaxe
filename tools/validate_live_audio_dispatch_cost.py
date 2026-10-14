"""Predict four original reader helpers during actual controlled gameplay."""
import hashlib,json
from actor_reference import ROOT
from audio_arbitration_cost import arbitration_cost
from audio_dispatch_cost import dispatch_cost
from audio_prefix_cost import tempo_cost,fade_cost

def main():
 source=(ROOT/'input/original.sms').read_bytes();folder=ROOT/'validation/audio-dispatch-live/6d-ff';rows=[]
 for region in ['auto','pal']:
  cycles=folder/f'{region}-cycle-events.json';reference=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/6d-ff/{region}-cycle-events.json'
  assert json.loads(cycles.read_text())==json.loads(reference.read_text()),'observer changed original source trace'
  path=folder/f'{region}-live-prefix-records.bin';raw=path.read_bytes();assert len(raw)%808==0
  counts=[0,0,0,0];commands={};previous_state=None;order=[];chain_checks=0
  for n in range(0,len(raw),808):
   kind=int.from_bytes(raw[n:n+4],'little');cost=int.from_bytes(raw[n+4:n+8],'little');assert kind in range(4)
   before=raw[n+8:n+408];after=raw[n+408:n+808]
   if kind==2:predicted=arbitration_cost(source,before)
   elif kind==3:predicted=dispatch_cost(source,before)
   else:predicted=[tempo_cost,fade_cost][kind](before)
   assert predicted['tstates']==cost,(region,n//808,kind,cost,predicted['tstates'])
   assert predicted['state']==after,(region,n//808,kind,'RAM')
   if kind!=2:assert before==previous_state,(region,n//808,'helper state chain');chain_checks+=1
   previous_state=after;counts[kind]+=1;order.append(kind)
   if kind==3:commands[hex(before[5])]=commands.get(hex(before[5]),0)+1
  assert counts==[601]*4 and order==[2,0,1,3]*601,(counts,order[:8])
  rows.append(dict(region=region,cases=sum(counts),tempo=counts[0],fade=counts[1],arbitration=counts[2],dispatch=counts[3],dispatch_commands=commands,consecutive_helper_state_checks=chain_checks,raw_sha256=hashlib.sha256(raw).hexdigest(),source_cycle_array_identical_to_v0179=True))
  print(region,counts,'live helper costs/state chains exact;',commands,flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=sum(r['cases'] for r in rows),dispatch_cases=sum(r['dispatch'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Controlled actual6D->96/full-mask paid route,PAL/NTSC,601 IRQs per region. Four independent state/cost models compare all400 audio RAM bytes and each helper cost. Consecutive arbitration->tempo->fade->dispatch snapshots chain exactly;original cycle arrays equal retained source reference.','This route does not exercise all29 effects/all13 music tracks;isolated suite supplies those command cases. B4 and five out-of-table commands remain excluded. Seven channel/envelope processing and full future IRQ cost/phase/physical loading prediction remain open.'])
 (ROOT/'analysis/live_audio_dispatch_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
