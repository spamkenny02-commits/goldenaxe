"""Actor milestone audit: verified branches, explicit RNG/timing limits."""
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
 for name in ['mobile_actors','mobile_room52','actor_ai','ranged','shield','damage','enemy_damage','fire_damage','all_save_points']:
  p=ROOT/f'validation/{name}_report.json';d=json.loads(p.read_text());assert d['md_sha256']==digest,(name,'stale report');reports.append(p.name)
 mobile=json.loads((ROOT/'validation/mobile_actors_report.json').read_text())
 assert mobile['deterministic_initial_record_cases']==48 and len(mobile['direction_cases'])==6
 assert mobile['projectile17_free_motion_compared_frames']==99 and len(mobile['projectile17_source_culls_exact'])==4
 assert mobile['terrain_change_verified'] and mobile['terrain_tilemap_bytes_source_exact']==1280
 room=json.loads((ROOT/'validation/mobile_room52_report.json').read_text())
 assert room['both_versions_enemy_contact_and_death_verified'] and not room['ram_mutations']
 previous=json.loads((ROOT/'validation/all_save_patch_audit.json').read_text())
 old=json.loads((ROOT/'validation/full_milestone_audit.json').read_text())
 check=bytearray(data);check[0x18e:0x190]=bytes(2);folded=0
 for n in range(0,len(check),4):folded^=int.from_bytes(check[n:n+4],'big')
 assert int.from_bytes(data[0x18e:0x190],'big')==(folded^(folded>>16))&65535
 audit=dict(md_sha256=digest,md_size=len(data),original_unchanged=True,rom_aliases_exact=True,current_targeted_reports=reports,source_core_mobile_transition_cases=48,controlled_direction_cases=6,projectile17_lifetime_frames_compared=99,terrain_buffer_bytes_source_exact=1280,room52_death_events=room['events'],prior_targeted_md_sha256=previous['md_sha256'],prior_full_regression_md_sha256=old['md_sha256'],full_regression_rerun_for_this_patch=False,full_game_ported=False,known_limits=['Original refresh-register RNG stream absent; controlled RNG only in branch tests','Room52 natural combat death is297 frames later in the current fixture','Collision descriptor bytes1B/1C excluded from actor record comparisons','Projectile sprite-overflow suppression and dungeon bounds remain incomplete','Global natural progression, other actors, quests, dungeons, terrain classes and informative dialogues incomplete','Original effects, absolute rendering timing and standard additive MD checksum remain incomplete'])
 (ROOT/'validation/mobile_actors_patch_audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
