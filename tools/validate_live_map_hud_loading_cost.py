"""Check190B and1DE2 models against retained live6D->96 source profiles."""
import hashlib,json
from actor_reference import ROOT
from world_map_loading_cost import world_map_cost
from map_hud_loading_cost import map_hud_cost,wait_save_spin_cost

def main():
 source=(ROOT/'input/original.sms').read_bytes();rows=[];evidence=[]
 for region in ['auto','pal']:
  path=ROOT/f'validation/paid-passage-loader/{region}-cycle-events.json'
  events=json.loads(path.read_text());evidence.append(dict(path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
  def interval(start,end,after=0):
   a=next(e for e in events if e[1]==start and e[4]==0x96 and e[2]>after)
   b=next(e for e in events if e[1]==end and e[2]>a[2])
   delta=(b[2]-a[2])-(b[3]-a[3]);assert delta%15==0,(region,start,end,delta)
   return delta//15
  clock=next(e[5] for e in events if e[1]==0x1deb and e[4]==0x96)
  model=map_hud_cost(source,24,24,24,24,10,0,clock,0)
  checked={}
  for name,start,end,expected in [
   ('world_map_caller',0x24b9,0x24bc,17+world_map_cost(source,0x96,1)['foreground_tstates']),
   ('HUD',0x1de5,0x1de8,model['components']['HUD']),
   ('palette',0x1deb,0x24bf,model['components']['palette'])]:
   observed=interval(start,end);assert observed==expected,(region,name,observed,expected)
   checked[name]=observed
  commit_start=next(e[2] for e in events if e[1]==0x1de8 and e[4]==0x96)
  spin=interval(0xb95,0xbb3,after=commit_start)
  # Recover busy-loop iteration count only to audit the wait's instruction shape.
  loops,remainder=divmod(spin-wait_save_spin_cost(0),29)
  assert loops>=0 and not remainder,(region,spin,loops,remainder)
  commit=interval(0x1de8,0x1deb)-spin
  assert commit==model['components']['map_transfer_excluding_save_spin'],(region,commit,model)
  complete=interval(0x24bc,0x24bf)-spin
  assert complete==17+model['foreground_excluding_wait_save_spin'],(region,complete,model)
  checked.update(transfer_excluding_save_spin=commit,map_HUD_caller_excluding_save_spin=complete)
  rows.append(dict(region=region,post_wait_clock=clock,exact_phases=checked,wait_save_spin_tstates=spin,observed_repeated_busy_loops=loops))
 report=dict(source_sha256=hashlib.sha256(source).hexdigest(),evidence=evidence,regions=rows,exact_phase_comparisons=len(rows)*5,production_ROM_changed=False,full_game_ported=False,limits=[
  'Retained live original6D->96 paid-exit profiles; source routines unpatched,controlled entrance/hero/initial clock. Default health/magic24/max24,gold10,no gems or curse. End-of-wait clock is observed rather than predicted.',
  '190B,HUD,palette,VDP map transfer excluding save/spin,and full1DE2 caller excluding save/spin match independently in both regions. Loop counts are recovered for auditing instruction shape,not a prediction of wait length or a native delay.',
  'Whole loading/interrupt phase,source logical-clock freeze,native elapsed work,RNG and complete transition fidelity remain unfinished.'])
 (ROOT/'analysis/live_map_hud_loading_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(report['exact_phase_comparisons'],'live190B/HUD/VDP/palette phases exact',flush=True)

if __name__=='__main__':main()
