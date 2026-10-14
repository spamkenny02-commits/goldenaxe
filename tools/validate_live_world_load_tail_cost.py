"""Verify source script/music/return instruction counts in24 actual exits."""
import hashlib,json
from actor_reference import ROOT
from world_load_tail_cost import room_script_setup_cost,world_music_setup_cost,load_return_cost

def main():
 source=(ROOT/'input/original.sms').read_bytes()
 matrix=json.loads((ROOT/'analysis/paid_passage_transition_matrix_report.json').read_text());rows=[]
 for row in matrix['rows']:
  expected=dict(room_script_setup=17+room_script_setup_cost(0x80 if not row['mask'] else 1),
                music_setup=17+world_music_setup_cost(source,row['target'],0xb0)['foreground_tstates'],
                load_return=load_return_cost())
  for name,cost in expected.items():
   assert row['source_phases'][name]['foreground_tstates']==cost,(row['town'],row['mask'],row['region'],name,cost,row['source_phases'][name])
  rows.append(dict(town=row['town'],target=row['target'],mask=row['mask'],region=row['region'],exact_foreground_tstates=expected))
 report=dict(source_sha256=hashlib.sha256(source).hexdigest(),cases=len(rows),phase_comparisons=len(rows)*3,rows=rows,production_ROM_changed=False,full_game_ported=False,limits=[
  'Instruction-derived actual5B20,world-class1CAF and24ED return tail match72 phase comparisons across six paid exits,two extreme masks and PAL/NTSC. Empty count high bit takes15T more in5B20; source previous musicB0 changes to82 on these destinations.',
  'World-music listed-room84 and unchanged-command branches are modeled from instructions but not validated by these six unlisted live destinations. Other classes/boss music are outside scope.',
  'Hero2C63 initialization,complete history/random paths,source audio IRQ work and native full duration remain unfinished.'])
 (ROOT/'analysis/live_world_load_tail_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(report['phase_comparisons'],'live script/music/return costs exact',flush=True)

if __name__=='__main__':main()
