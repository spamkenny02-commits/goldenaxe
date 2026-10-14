"""Check cumulative source work to fade entry against24 retained live exits."""
import hashlib,json
from actor_reference import ROOT
from paid_exit_foreground_cost import paid_exit_foreground_cost

def main():
 source=(ROOT/'input/original.sms').read_bytes();live=json.loads((ROOT/'analysis/live_hero_initialization_cost_report.json').read_text());rows=[]
 for case in live['rows']:
  path=ROOT/case['snapshot_path'];r=path.read_bytes();assert hashlib.sha256(r).hexdigest()==case['entry_sha256']
  events=json.loads((path.parent/f"{case['region']}-cycle-events.json").read_text());target=case['target']
  def entry(pc,after=0):return next(e for e in events if e[1]==pc and e[4]==target and e[2]>after)
  def interval(start,end):
   delta=(end[2]-start[2])-(end[3]-start[3]);assert delta%15==0;return delta//15
  history_start=entry(0x24c5);history_end=entry(0x1780,history_start[2])
  inside=[e for e in events if history_start[2]<e[2]<history_end[2]]
  history=[e for e in inside if e[1]==0x1c40];seeds=[e for e in inside if e[1]==0x4e4];misses=[e for e in inside if e[1]==0x1c88]
  assert len(history)==len(seeds)==len(misses)==3 and all(e[6]==0xdd00 for e in misses)
  attempts=[dict(history_position=None if h[6]==0xdcef else h[6]-0xdcf0,random_position=None,seed=s[6],flag_nonzero=True) for h,s in zip(history,seeds)]
  model=paid_exit_foreground_cost(source,r,attempts)
  start=entry(0x16d0);reveal=entry(0x1fa7,start[2]);prepare=entry(0xaa4,reveal[2]);fade=entry(0xace,prepare[2])
  waits=[e for e in events if e[1]==0xb95 and start[2]<e[2]<fade[2]];assert len(waits)==2
  save_spins=[interval(e,entry(0xbb3,e[2])) for e in waits]
  loading=interval(start,reveal)-save_spins[0]
  to_fade=interval(start,fade)-sum(save_spins)
  assert loading==model['to1FA7_excluding_HUD_save_spin'],(case,loading,model)
  assert to_fade==model['to0ACE_excluding_two_save_spins'],(case,to_fade,model)
  prepare_work=interval(prepare,fade)-save_spins[1]
  assert prepare_work==model['components']['reveal_prepare_excluding_save_spin']
  rows.append(dict(town=case['town'],target=target,mask=case['mask'],region=case['region'],loading_foreground_excluding_save_spin=loading,to_fade_foreground_excluding_two_save_spins=to_fade,reveal_prepare_foreground_excluding_save_spin=prepare_work,observed_save_spin_tstates=save_spins,observed_IRQ_master_cycles=fade[3]-start[3],components=model['components']))
 report=dict(md_sha256=live['md_sha256'],source_sha256=live['source_sha256'],cases=len(rows),cumulative_and_prepare_comparisons=len(rows)*3,rows=rows,production_ROM_changed=False,full_game_ported=False,limits=[
  'All foreground loader components now combine without a fitted constant on24 actual ordinary paid-exit paths. Full16D0..1FA7 and16D0..0ACE work exclude only anchored0B95..0BB3 save/spin spans and source IRQ cycles. Both register restores remain counted. Initial reveal preparation1842T matches separately.',
  'Hero entry state and three history/RNG branch inputs are supplied from observed snapshots/traces. This predicts instruction work for those states;it does not predict refresh outputs or arbitrary history branches/native game states.',
  'Wait lengths and audio IRQ work are recorded,not modeled. No physical frame budget or native wait has been integrated. Other graphics classes,C0AC!=0,boss/story actors,physical VDP contention and complete natural progression remain unproved.'])
 (ROOT/'analysis/paid_exit_foreground_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(len(rows),'cumulative paid-exit foreground paths and',len(rows)*3,'comparisons exact',flush=True)

if __name__=='__main__':main()
