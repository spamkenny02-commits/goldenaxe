"""Bind targeted flying/combat/save checks to the delivered immutable ROM."""
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
 for name in ['flying_actors','mobile_actors','mobile_room52','actor_ai','ranged','shield','damage','enemy_damage','fire_damage','all_save_points']:
  p=ROOT/f'validation/{name}_report.json';d=json.loads(p.read_text());assert d['md_sha256']==digest,(name,'stale report');reports.append(p.name)
 flight=json.loads((ROOT/'validation/flying_actors_report.json').read_text())
 assert flight['arithmetic_cases']==60 and flight['aim_targets']==11
 assert flight['free_motion_frames']==160 and flight['projectile_lifetime_frames']==108
 assert flight['projectile_births_source_exact'] and len(flight['projectile_culls'])==2
 previous=json.loads((ROOT/'validation/mobile_actors_patch_audit.json').read_text())
 old=json.loads((ROOT/'validation/full_milestone_audit.json').read_text())
 check=bytearray(data);check[0x18e:0x190]=bytes(2);folded=0
 for n in range(0,len(check),4):folded^=int.from_bytes(check[n:n+4],'big')
 assert int.from_bytes(data[0x18e:0x190],'big')==(folded^(folded>>16))&65535
 audit=dict(md_sha256=digest,md_size=len(data),original_unchanged=True,rom_aliases_exact=True,current_targeted_reports=reports,source_core_flying_arithmetic_cases=60,aimed_projectile_initialization_cases=22,free_flying_frames=160,aimed_projectile_births_and_culls_source_exact=True,prior_targeted_md_sha256=previous['md_sha256'],prior_full_regression_md_sha256=old['md_sha256'],full_regression_rerun_for_this_patch=False,full_game_ported=False,known_limits=['Actor collision descriptor bytes1B/1C excluded from record comparisons','Fixtures isolate arithmetic and projectiles; natural global progression not proven','Original refresh-register RNG stream absent','Room52 combat still has an absolute timing difference','Other actor families, quests, dungeons, terrain classes and informative dialogues incomplete','Sprite-overflow suppression, original effects, rendering timing and standard additive MD checksum incomplete'])
 (ROOT/'validation/flying_actors_patch_audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
