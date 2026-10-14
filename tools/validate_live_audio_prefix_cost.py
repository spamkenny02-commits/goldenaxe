"""Compare independent tempo/fade models with actual unpatched SMS passage."""
import hashlib,json
from actor_reference import ROOT
from audio_prefix_cost import tempo_cost,fade_cost

def main():
 folder=ROOT/'validation/audio-prefix-live/6d-ff';rows=[]
 for region in ['auto','pal']:
  source_path=folder/f'{region}-cycle-events.json'
  reference=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/6d-ff/{region}-cycle-events.json'
  assert json.loads(source_path.read_text())==json.loads(reference.read_text()),'live prefix observer altered source trace'
  path=folder/f'{region}-live-prefix-records.bin';raw=path.read_bytes();assert len(raw)%808==0
  counts=[0,0];costs=[[],[]]
  for n in range(0,len(raw),808):
   kind=int.from_bytes(raw[n:n+4],'little');observed=int.from_bytes(raw[n+4:n+8],'little');assert kind in [0,1]
   before=raw[n+8:n+408];after=raw[n+408:n+808];predicted=[tempo_cost,fade_cost][kind](before)
   assert observed==predicted['tstates'],(region,n//808,kind,observed,predicted['tstates'])
   assert after==predicted['state'],(region,n//808,kind,'RAM mismatch')
   counts[kind]+=1;costs[kind].append(observed)
  assert all(n>=500 for n in counts),counts
  rows.append(dict(region=region,cases=sum(counts),tempo_cases=counts[0],fade_cases=counts[1],tempo_cost_range=[min(costs[0]),max(costs[0])],fade_cost_range=[min(costs[1]),max(costs[1])],raw_sha256=hashlib.sha256(raw).hexdigest(),source_trace_identical_to_v0179=True))
  print(region,counts,'actual tempo/fade costs and400 RAM bytes exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['One actual controlled paid route6D->96 with full destination actor mask,in PAL/NTSC. Original helper input/output snapshots and wall T states are observed read-only. Independent state/cost models compare all400 audio RAM bytes per call. Original cycle arrays remain identical to archived source.','Includes surrounding game/audio phase during4200..4800,not all command/envelope paths. Isolated helper suite covers additional fade end/zero/wrap states. Remaining arbitration/dispatch/channel costs and full future IRQ scheduling/physical load prediction remain open.'])
 (ROOT/'analysis/live_audio_prefix_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
