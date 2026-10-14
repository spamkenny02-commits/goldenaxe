"""Independent arbitration/tempo/fade state/cost checks during an actual exit."""
import hashlib,json
from actor_reference import ROOT
from audio_arbitration_cost import arbitration_cost
from audio_prefix_cost import tempo_cost,fade_cost

def main():
 source=(ROOT/'input/original.sms').read_bytes();folder=ROOT/'validation/audio-arbitration-live/6d-ff';rows=[]
 for region in ['auto','pal']:
  cycles=folder/f'{region}-cycle-events.json';reference=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/6d-ff/{region}-cycle-events.json'
  assert json.loads(cycles.read_text())==json.loads(reference.read_text()),'observer changed original trace'
  path=folder/f'{region}-live-prefix-records.bin';raw=path.read_bytes();assert len(raw)%808==0
  counts=[0,0,0];decisions={}
  for n in range(0,len(raw),808):
   kind=int.from_bytes(raw[n:n+4],'little');cost=int.from_bytes(raw[n+4:n+8],'little');assert kind in [0,1,2]
   before=raw[n+8:n+408];after=raw[n+408:n+808]
   predicted=arbitration_cost(source,before) if kind==2 else [tempo_cost,fade_cost][kind](before)
   assert predicted['tstates']==cost and predicted['state']==after,(region,n//808,kind,cost,predicted['tstates'])
   counts[kind]+=1
   if kind==2:
    for decision in predicted['decisions']:decisions[decision]=decisions.get(decision,0)+1
  assert counts==[601,601,601],counts
  rows.append(dict(region=region,cases=sum(counts),tempo=counts[0],fade=counts[1],arbitration=counts[2],arbitration_decisions=decisions,raw_sha256=hashlib.sha256(raw).hexdigest(),source_cycle_array_identical_to_v0179=True))
  print(region,counts,'live tempo/fade/arbitration cost and400 bytes exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=sum(r['cases'] for r in rows),arbitration_cases=sum(r['arbitration'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Controlled actual6D->96 paid route,full destination mask,PAL/NTSC,601 audio IRQs observed per region. All three independently modeled helper costs and400-byte states compare;original cycle arrays identical to retained source reference.','Other routes/phase histories,dispatch,channel/envelope costs,source RNG and native IRQ/load scheduling are not established.'])
 (ROOT/'analysis/live_audio_arbitration_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
