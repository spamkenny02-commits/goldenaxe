"""Bind quest-gift persistence fix to reproduced v0176 failures/current evidence."""
import hashlib,json
from actor_reference import ROOT

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
 prior=ROOT/'versions/v0176-9a4471c0';source=(ROOT/'input/original.sms').read_bytes()
 assert source[0x631a:0x6320]==bytes.fromhex('cd3d19cd7c1a')
 baseline=(prior/'source/house_quest.inc').read_text()
 block='''        /* 631A:193D marks the outside town's class1 flag,then1A7C
         * transforms the room before the reward window backs it up. */
        game_save_state[0x50+(house_return_room&255)]|=2;
        prepare_room_cells(room_id);build_room_map(sms_vram+0x3800,world_new_md);
'''
 anchor='        show_item_reward_text(item,0,house_quest_labels+house_quest_label_index[item]);'
 assert baseline.count(anchor)==1
 assert baseline.replace(anchor,block+anchor)==(ROOT/'megadrive/src/house_quest.inc').read_text()
 unchanged=[]
 for path in (ROOT/'megadrive/src').iterdir():
  if not path.is_file() or path.name=='house_quest.inc':continue
  assert path.read_bytes()==(prior/'source'/path.name).read_bytes(),('unexpected production change',path.name)
  unchanged.append(path.name)
 baseline_folder=ROOT/'analysis/quest-gift-persistence-v0176'
 armor=json.loads((baseline_folder/'armor2-baseline.json').read_text())
 repeat=json.loads((baseline_folder/'primary3-baseline.json').read_text())
 assert armor['traces']['sms']['3500']['fields'][-1]==2 and armor['traces']['md']['3500']['fields'][-1]==0
 assert repeat['reward_counts']==dict(sms=1,md=2)
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(rom)
 assert len(rom)==1048576 and int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
 checksum=sum(int.from_bytes(rom[n:n+2],'big') for n in range(0x200,len(rom),2))&65535
 assert checksum==int.from_bytes(rom[0x18e:0x190],'big')
 for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert (ROOT/name).read_bytes()==rom
 evidence={};gift_count=0
 for name,initial in [('house_quest_persistence_gameplay_report.json',0),('house_quest_persistence_high_gameplay_report.json',128)]:
  path=ROOT/'validation'/name;report=json.loads(path.read_text());assert report['md_sha256']==digest and report['initial_outside_flag']==initial
  assert len(report['cases'])==16
  assert sum(bool(r['outside_context_replaced_after_door']) for r in report['cases'])==4
  for case in report['cases']:
   assert case['persistent_flag_and_static_cells_exact'] and case['inventory_roundtrip_and_second_UP']
   assert case['reward_count']==dict(sms=1,md=1) and case['reward_pattern_tiles_exact']==38
  gift_count+=len(report['cases']);evidence[name]=sha(path.read_bytes())
 for name,count in [('house_quest_unit_report.json',1836),('house_quest_hint_gameplay_report.json',2),('paid_passage_gameplay_report.json',20)]:
  path=ROOT/'validation'/name;report=json.loads(path.read_text());assert report['md_sha256']==digest
  assert (len(report['cases']) if isinstance(report['cases'],list) else report['cases'])==count
  evidence[name]=sha(path.read_bytes())
 report=dict(md_sha256=digest,checksum=f'{checksum:04X}',bytes=len(rom),only_quest_gift_persistence_block_changed=True,unchanged_production_source_files=unchanged,reproduced_prior_v0176_missing_flag=True,reproduced_prior_v0176_primary3_repeat=True,baseline_armor_evidence_sha256=sha((baseline_folder/'armor2-baseline.json').read_bytes()),baseline_repeat_evidence_sha256=sha((baseline_folder/'primary3-baseline.json').read_bytes()),current_evidence=evidence,gift_context_cases=gift_count,full_game_ported=False,limits=[
  'Only successful quest-gift branch changes. Outside town bit2 is ORed,then existing class1 room transformation/map construction runs before reward modal backup. Hints,conditions,equipment effects,save layout,actors,timing and other production modules byte-identical to v0176.',
  '32 controlled PAL/NTSC contexts:24 actual town-door cases plus8 explicit C7/55 context fixtures;initial flags0/128. Current exact visit flag/static cells/maps,one reward,menu/second UP and38 held-pattern tiles checked;remaining animated NPC poses excluded and retained as differences.',
  '1836 decision/effect cases,two long-hint and20 actual paid-passage regressions pass. Full natural progression,exterior leave/re-entry and SRAM persistence of these gifts remain unverified. Physical transition timing and source refresh RNG remain open.'])
 (ROOT/'validation/quest_gift_persistence_patch_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Quest-gift persistence patch audited; current ROM',digest[:8],flush=True)

if __name__=='__main__':main()
