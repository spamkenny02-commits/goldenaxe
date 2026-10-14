"""Bind water-actor source checks and targeted regressions to delivered ROM."""
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
 for name in ['water_jump','water_rooms','jumping_actors','jumping_rooms','fixed_shooter','fixed_rooms','emerging_actors','actor_spawn','flying_actors','mobile_actors','mobile_room52','actor_ai','ranged','shield','damage','enemy_damage','fire_damage','all_save_points']:
  p=ROOT/f'validation/{name}_report.json';d=json.loads(p.read_text());assert d['md_sha256']==digest,(name,'stale report');reports.append(p.name)
 water=json.loads((ROOT/'validation/water_jump_report.json').read_text())
 assert water['deterministic_cases']==96 and len(water['controlled_decisions'])==8
 assert len(water['appearance_cases'])==3 and water['ground_refusal_types']==[0x33,0x34]
 assert water['walking_special_source_frame']>=3102 and water['free_leap_frames']==38 and water['free_leap_vectors']==4
 assert water['aimed13_active_frames']
 rooms=json.loads((ROOT/'validation/water_rooms_report.json').read_text())
 assert rooms['three_water_rooms_verified'] and not rooms['ram_mutations'] and len(rooms['rows'])==6
 assert all(row['aimed13_births'] for row in rooms['rows'])
 previous=json.loads((ROOT/'validation/jumping_actors_patch_audit.json').read_text())
 old=json.loads((ROOT/'validation/full_milestone_audit.json').read_text())
 check=bytearray(data);check[0x18e:0x190]=bytes(2);folded=0
 for n in range(0,len(check),4):folded^=int.from_bytes(check[n:n+4],'big')
 assert int.from_bytes(data[0x18e:0x190],'big')==(folded^(folded>>16))&65535
 audit=dict(md_sha256=digest,md_size=len(data),original_unchanged=True,rom_aliases_exact=True,current_targeted_reports=reports,source_core_deterministic_cases=96,controlled_decisions=8,appearance_cases=3,ground_refusals=2,free_ballistic_frames=38,cold_load_water_rooms=3,prior_targeted_md_sha256=previous['md_sha256'],prior_full_regression_md_sha256=old['md_sha256'],full_regression_rerun_for_this_patch=False,full_game_ported=False,known_limits=['Original refresh-register RNG stream absent; choices/phase controlled in isolated appearance tests','Cold room6A first shot SMS2292/MD3490; absolute timing differs and cause is not fully isolated','Mixed room19 fixture observes34 walking but no34 leap before combat stops','Actor collision descriptor bytes1B/1C excluded from isolated record comparisons','Controlled checkpoints do not prove complete natural progression','Room52 combat retains an absolute timing difference','Actor35 and remaining families, quests, dungeons, terrain classes and informative dialogues incomplete','Sprite-overflow suppression, effects, rendering timing and standard additive MD checksum incomplete'])
 (ROOT/'validation/water_jump_patch_audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
