"""Audit the resting/emerging actor milestone against the delivered ROM."""
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
 for name in ['emerging_actors','actor_spawn','flying_actors','mobile_actors','mobile_room52','actor_ai','ranged','shield','damage','enemy_damage','fire_damage','all_save_points']:
  p=ROOT/f'validation/{name}_report.json';d=json.loads(p.read_text());assert d['md_sha256']==digest,(name,'stale report');reports.append(p.name)
 new=json.loads((ROOT/'validation/emerging_actors_report.json').read_text())
 assert new['deterministic_cases']==32 and len(new['random_branches'])==6
 assert len(new['terrain_appearances'])==3 and len(new['terrain_refusals'])==3
 assert new['projectile14_aim_cases']==11 and new['projectile14_15_births_source_exact']
 assert new['free_animation_frames']==150 and new['free_animation_states']==[2,4,6,8]
 assert new['vertical_decision_states']==[4,6,10] and new['blocked_cases']==4 and new['horizontal_cases']==2
 previous=json.loads((ROOT/'validation/flying_actors_patch_audit.json').read_text())
 old=json.loads((ROOT/'validation/full_milestone_audit.json').read_text())
 check=bytearray(data);check[0x18e:0x190]=bytes(2);folded=0
 for n in range(0,len(check),4):folded^=int.from_bytes(check[n:n+4],'big')
 assert int.from_bytes(data[0x18e:0x190],'big')==(folded^(folded>>16))&65535
 audit=dict(md_sha256=digest,md_size=len(data),original_unchanged=True,rom_aliases_exact=True,current_targeted_reports=reports,source_core_deterministic_cases=32,controlled_random_cases=6,terrain_appearances=3,terrain_refusals=3,projectile14_aim_cases=11,projectile14_15_motion_frames=108,free_animation_frames=150,prior_targeted_md_sha256=previous['md_sha256'],prior_full_regression_md_sha256=old['md_sha256'],full_regression_rerun_for_this_patch=False,full_game_ported=False,known_limits=['Controlled RNG and phase for appearance tests; original Z80R stream absent','Actor collision descriptor bytes1B/1C excluded from record comparisons','Isolated simulations do not prove complete natural progression','Room52 absolute combat timing still differs','Actor2D and other families, quests, dungeons, terrain classes and informative dialogues incomplete','Sprite-overflow suppression, effects, rendering timing and standard additive MD checksum incomplete'])
 (ROOT/'validation/emerging_actors_patch_audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
