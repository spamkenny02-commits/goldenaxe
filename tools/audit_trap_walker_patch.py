"""Bind hidden-trap, default-placement and targeted regression evidence."""
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
 for name in ['trap_walker','trap_room','water_jump','water_rooms','jumping_actors','jumping_rooms','fixed_shooter','fixed_rooms','emerging_actors','actor_spawn','flying_actors','mobile_actors','mobile_room52','actor_ai','ranged','shield','damage','enemy_damage','fire_damage','all_save_points']:
  p=ROOT/f'validation/{name}_report.json';d=json.loads(p.read_text());assert d['md_sha256']==digest,(name,'stale report');reports.append(p.name)
 trap=json.loads((ROOT/'validation/trap_walker_report.json').read_text())
 assert trap['deterministic_cases']==16 and len(trap['placement_rooms'])==6
 assert len(trap['proximity_terrain_cases'])==8 and len(trap['controlled_decisions'])==3
 assert trap['projectile16_free_frames']==108 and len(trap['projectile16_four_direction_culls'])==4
 room=json.loads((ROOT/'validation/trap_room_report.json').read_text())
 assert room['real_movement_trigger_verified'] and room['hidden_positions_source_exact'] and not room['ram_mutations']
 assert len(room['rows'])==2 and all(r['events']['first_activation']==1755 for r in room['rows'])
 fixed=json.loads((ROOT/'validation/fixed_shooter_report.json').read_text());assert fixed['default_pointer_rooms']==[0xa4,0x1aa]
 previous=json.loads((ROOT/'validation/water_jump_patch_audit.json').read_text())
 old=json.loads((ROOT/'validation/full_milestone_audit.json').read_text())
 check=bytearray(data);check[0x18e:0x190]=bytes(2);folded=0
 for n in range(0,len(check),4):folded^=int.from_bytes(check[n:n+4],'big')
 assert int.from_bytes(data[0x18e:0x190],'big')==(folded^(folded>>16))&65535
 audit=dict(md_sha256=digest,md_size=len(data),original_unchanged=True,rom_aliases_exact=True,current_targeted_reports=reports,source_core_deterministic_cases=16,source_core_placement_cases=6,proximity_and_terrain_cases=8,controlled_decisions=3,projectile16_free_frames=108,projectile16_four_direction_culls_source_exact=True,real_movement_activation_frame_source_exact=1755,default_placement_in_both_regions_verified=True,prior_targeted_md_sha256=previous['md_sha256'],prior_full_regression_md_sha256=old['md_sha256'],full_regression_rerun_for_this_patch=False,full_game_ported=False,known_limits=['Original refresh-register RNG stream absent; controlled choices in isolated tests','Source495E sprite-overflow suppression remains absent; projectile16 fixtures do not validate it','Actor collision descriptor bytes1B/1C excluded from isolated record comparisons','CheckpointE3 walking starts1780 SMS/1782 MD despite matching activation1755','Other checkpoint combat/shot timing differences remain documented in their reports','Controlled checkpoints do not prove complete natural progression','Actor36 and remaining families, quests, dungeons, terrain classes and informative dialogues incomplete','Effects, rendering timing and standard additive MD checksum incomplete'])
 (ROOT/'validation/trap_walker_patch_audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
