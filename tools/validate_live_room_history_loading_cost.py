"""Validate instruction counts for class0 room-history work in24 live exits."""
import hashlib,json
from actor_reference import ROOT
from source_rng_reference import source_rng
from room_history_loading_cost import clear_and_history_cost

def main():
 matrix=json.loads((ROOT/'analysis/paid_passage_transition_matrix_report.json').read_text());rows=[]
 for row in matrix['rows']:
  path=ROOT/row['raw_events_path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['raw_events_sha256']
  events=json.loads(path.read_text());target=row['target']
  start=next(e for e in events if e[1]==0x24c5 and e[4]==target)
  end=next(e for e in events if e[1]==0x1780 and e[2]>start[2])
  inside=[e for e in events if start[2]<e[2]<end[2]]
  history=[e for e in inside if e[1]==0x1c40];seeds=[e for e in inside if e[1]==0x4e4]
  misses=[e for e in inside if e[1]==0x1c88]
  assert len(history)==len(seeds)==len(misses)==3,(row['town'],row['mask'],row['region'])
  assert all(e[6]==0xdd00 for e in misses),'Random CPIR did not scan all16 recent entries'
  attempts=[]
  for h,s in zip(history,seeds):
   # A miss shifts15 entries with LDDR,leaving HL=DCEF; a match leaves
   # HL one past the matching entry,DCF1..DD00.
   position=h[6]-0xdcf0;assert position==-1 or 1<=position<=16
   attempts.append(dict(history_position=None if position==-1 else position,random_position=None,seed=s[6],flag_nonzero=True))
  for begin in [e for e in inside if e[1]==0x4e1]:
   finish=next(e for e in inside if e[1]==0x4fd and e[2]>begin[2])
   seed=next(e[6] for e in inside if e[1]==0x4e4 and e[2]>begin[2])
   observed=((finish[2]-begin[2])-(finish[3]-begin[3]))//15+10
   model=source_rng(seed,0);assert (observed,finish[6])==(model['foreground_tstates'],model['seed'])
  model=clear_and_history_cost(attempts)
  observed=((end[2]-start[2])-(end[3]-start[3]))//15
  assert observed==model['foreground_tstates'],(row['town'],row['mask'],row['region'],observed,model)
  rows.append(dict(town=row['town'],target=target,mask=row['mask'],region=row['region'],attempts=attempts,foreground_tstates=observed))
 report=dict(source_sha256=matrix['source_sha256'],cases=len(rows),rng_calls_checked=len(rows)*3,rows=rows,production_ROM_changed=False,full_game_ported=False,limits=[
  'Uses retained actual unpatched paid-exit source traces. Instruction-derived clears and three recent-room attempts match10466T on24 paths;72 actual RNG seed/cost calls match separately. Match positions and seed inputs are observed branch inputs,not a prediction of refresh-register output.',
  'Live cases insert the new destination once,then find it first;all three random values miss the recent history and address nonzero persistence bytes. Model supports other match positions/zero flag paths but those branches are not validated here.',
  'No replacement of native room-history/RNG behavior or physical timing. Hero initialization,IRQ work,source refresh evolution and complete faithful transitions remain open.'])
 (ROOT/'analysis/live_room_history_loading_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(len(rows),'live24C5 history prefixes and',len(rows)*3,'RNG seed/cost calls exact',flush=True)

if __name__=='__main__':main()
