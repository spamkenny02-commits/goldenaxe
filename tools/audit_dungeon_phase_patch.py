"""Verify v0126 changes only current-frame type14 collision publication since125."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 baseline=ROOT/'versions/v0125-e361feb5';old=(baseline/'actors.c').read_text();new=(ROOT/'megadrive/src/actors.c').read_text();assert new.count('entity[0]==0x0f || entity[0]==0x14 ||')==1
 assert new.replace('entity[0]==0x0f || entity[0]==0x14 ||','entity[0]==0x0f ||')==old
 assert (ROOT/'megadrive/src/main.c').read_bytes()==(baseline/'main.c').read_bytes()
 data=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(data)==1048576 and data==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(data[i:i+2],'big') for i in range(0x200,len(data),2))&65535;assert int.from_bytes(data[0x18e:0x190],'big')==checksum
 assert data[0x1a4:0x1a8]==bytes.fromhex('000fffff') and data[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 previous=json.loads((baseline/'menu_dungeon_patch_audit.json').read_text());assert previous['actor_changes_confined_to_46_49_helpers_dispatch_and_collision_publication']
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),rom_bytes=len(data),checksum=checksum,aliases_and_header_verified=True,production_change_since_v0125='Publish type14 aimed projectile collision descriptor in current frame, as original0940 does; all other actor source and all main source bytes unchanged.',prior_scope_audit_sha256=sha(baseline/'menu_dungeon_patch_audit.json'),source_files={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'megadrive/src/main.c',ROOT/'megadrive/src/actors.c',ROOT/'tools/validate_dungeon_phase.py',ROOT/'tools/validate_dungeon_phase_gameplay.py',ROOT/'tools/validate_dungeon_proximity_entry.py']},full_game_ported=False,limits=['Controlled segments use explicit initial clock alignment and stop before random choices.','Actual112 entry compares first46 record, resource pixels and its SAT; random44/45 neighbors excluded.','Original RNG/global clock, full natural dungeon combat/progression and remaining25 actor types are unfinished.'])
 (ROOT/'validation/dungeon_phase_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('v0126 integrity and sole type14 collision-publication source change verified.')
if __name__=='__main__':main()
