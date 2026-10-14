"""Verify added re-entry/SRAM/cold-house evidence on unchanged production v0177."""
import hashlib,json
from actor_reference import ROOT

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
 prior=ROOT/'versions/v0177-3f4dbbc9';rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(rom)
 assert rom==(prior/'gaw-megadrive-v0177.bin').read_bytes()
 for path in (ROOT/'megadrive/src').iterdir():
  if path.is_file():assert path.read_bytes()==(prior/'source'/path.name).read_bytes(),('production changed',path.name)
 evidence={};srams=[]
 for name in ['house_quest_revisit_gameplay_report.json','quest_gift_save_report.json','house_quest_cold_persistence_gameplay_report.json']:
  path=ROOT/'validation'/name;r=json.loads(path.read_text());assert r['md_sha256']==digest and len(r['cases'])==12
  evidence[name]=sha(path.read_bytes())
  if name.startswith('house_quest_revisit'):
   assert r['revisit'] and r['initial_outside_flag']==1
   for case in r['cases']:
    assert not case['outside_context_replaced_after_door'] and case['reward_count']==dict(sms=1,md=1)
    assert case['persistent_flag_and_static_cells_exact']
    for tag,walk in case['controller_walk_exit_reentry'].items():
     assert walk['outside_frame']<walk['reentered_frame']<walk['finished_frame']<6500
     assert walk['stage']=='finished' and walk['last_room']==case['house']
  elif name.startswith('house_quest_cold'):
   assert r['cold'] and r['initial_outside_flag'] is None
   for case in r['cases']:
    assert case['cold_saved_state_only'] and case['reward_count']==dict(sms=0,md=0)
    assert case['persistent_flag_and_static_cells_exact'] and not case['outside_context_replaced_after_door']
  else:
   for case in r['cases']:
    assert case['save_payload_bytes_exact']==592 and case['cold_flags_bytes_exact']==256 and case['cold_inventory_bytes_exact']==17
    assert case['cold_fields']['sms']==case['cold_fields']['md']
    assert case['cold_fields']['sms']['gift_town_flag']&2
    for tag in ['sms','md']:
     p=ROOT/f"validation/quest-gift-save-{case['town']:02x}-{case['region']}-{tag}.srm"
     srams.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p.read_bytes())))
 report=dict(md_sha256=digest,source_sha256=sha((ROOT/'input/original.sms').read_bytes()),production_ROM_changed=False,production_source_changed=False,controller_exit_reentry_cases=12,actual_save_cold_load_cases=12,cold_house_no_second_gift_cases=12,current_evidence=evidence,SRAM_files=srams,full_game_ported=False,limits=[
  'Native ROM/source byte-identical to numbered v0177. All six naturally defined gift-house doors,both video regions. Re-entry route uses read-only observations and ordinary buttons after setup;fixtures include world visited1/traversal item and initial cleared exterior actors.',
  'Actual controller-generated gift fields transferred to established save-point fixture;production slot1 save and fresh-core Continue execute. Full592-byte payload and loaded256 flags/17 items/equipment/curse/story/capacity compare. New cold-house tests inject no gift inventory or flag;only exterior/door/hero relocation and clock alignment after Continue.',
  'No uninterrupted route from each gift to save point and back from checkpoint,all slots,complete natural progression or exact transition/refresh-RNG fidelity is proved. Static maps exclude remaining NPC animation poses,with differences recorded.'])
 (ROOT/'validation/quest_gift_persistence_followup_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Unchanged v0177:12 re-entry,12 save/cold-load and12 cold-house cases audited.')

if __name__=='__main__':main()
