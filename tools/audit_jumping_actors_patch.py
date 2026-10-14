"""Bind jumping-body/shadow and targeted regression evidence to the ROM."""
import hashlib,json
from pathlib import Path
from actor_reference import ROOT

def main():
 def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 data=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(ROOT/'gaw-megadrive.bin')
 assert len(data)==524288 and int.from_bytes(data[0x1a4:0x1a8],'big')==len(data)-1
 for p in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert sha(ROOT/p)==digest
 assert sha(ROOT/'input/original.sms')==sha(Path(r'D:/Cartmod/GoldenAxeWarrior/chat/Golden Axe Warrior (USA, Europe).sms'))=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
 reports=[]
 for name in ['jumping_actors','jumping_rooms','fixed_shooter','fixed_rooms','emerging_actors','actor_spawn','flying_actors','mobile_actors','mobile_room52','actor_ai','ranged','shield','damage','enemy_damage','fire_damage','all_save_points']:
  p=ROOT/f'validation/{name}_report.json';d=json.loads(p.read_text());assert d['md_sha256']==digest,(name,'stale report');reports.append(p.name)
 jump=json.loads((ROOT/'validation/jumping_actors_report.json').read_text())
 assert jump['arithmetic_body_cases']==32 and len(jump['controlled_random_cases'])==12
 assert len(jump['all_sixteen_vector_cases'])==16 and jump['free_body_shadow_frames']==18
 assert jump['adjacent_shadow_removal_source_exact']
 assert jump['shadow_birth_into_empty_record_verified'] and jump['appearance_wait_without_shadow_verified']
 rooms=json.loads((ROOT/'validation/jumping_rooms_report.json').read_text())
 assert rooms['two_jumping_types_and_shadows_verified'] and not rooms['ram_mutations'] and len(rooms['rows'])==4
 assert all(row['attached_shadow_frame_checks']>0 and 10 in row['body_states'] for row in rooms['rows'])
 previous=json.loads((ROOT/'validation/fixed_shooter_patch_audit.json').read_text())
 old=json.loads((ROOT/'validation/full_milestone_audit.json').read_text())
 check=bytearray(data);check[0x18e:0x190]=bytes(2);folded=0
 for n in range(0,len(check),4):folded^=int.from_bytes(check[n:n+4],'big')
 assert int.from_bytes(data[0x18e:0x190],'big')==(folded^(folded>>16))&65535
 audit=dict(md_sha256=digest,md_size=len(data),original_unchanged=True,rom_aliases_exact=True,current_targeted_reports=reports,source_core_arithmetic_cases=32,controlled_random_branches=12,source_core_vector_cases=16,cold_load_jumping_rooms=2,free_body_shadow_frames=18,adjacent_shadow_removal_source_exact=True,prior_targeted_md_sha256=previous['md_sha256'],prior_full_regression_md_sha256=old['md_sha256'],full_regression_rerun_for_this_patch=False,full_game_ported=False,known_limits=['Original refresh-register RNG stream absent; controlled RNG in isolated decision tests','Actor collision descriptor bytes1B/1C excluded from isolated record comparisons','Controlled checkpoints verify moving bodies/attached shadows, not complete progression or natural timing','Room52 combat retains an absolute timing difference','Actor33 and remaining families, quests, dungeons, terrain classes and informative dialogues incomplete','Sprite-overflow suppression, effects, rendering timing and standard additive MD checksum incomplete'])
 (ROOT/'validation/jumping_actors_patch_audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
