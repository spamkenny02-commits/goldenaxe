"""Restrict4D/4E helpers, collision publication and hero magic accessor changes."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0130-ee2d31fc';old=(base/'actors.c').read_text();new=(ROOT/'megadrive/src/actors.c').read_text();s=new
 a=s.index('extern const u8 dungeon_drain_vectors[];');b=s.index('/* 5071 -> A86D:',a);s=s[:a]+s[b:]
 dispatch='            else if(entity[0]==0x4d || entity[0]==0x4e) dungeon_drain_behavior(entity,cells,hero_x,hero_y,frame,slot,NULL,0);\n';assert s.count(dispatch)==1;s=s.replace(dispatch,'')
 condition='(entity[0]>=0x4a && entity[0]<=0x4e)';assert s.count(condition)==1;s=s.replace(condition,'(entity[0]>=0x4a && entity[0]<=0x4c)');assert s==old,'Unrelated actor code changed'
 accessor='/* 4FC2..4FCA: contact with4D/4E subtracts eight magic, clamped at zero. */\nvoid world_drain_hero_magic(void) { hero_magic=hero_magic>=8?hero_magic-8:0; }\n';main=(ROOT/'megadrive/src/main.c').read_text();assert main.count(accessor)==1 and main.replace(accessor,'')==(base/'main.c').read_text()
 source=(ROOT/'input/original.sms').read_bytes();asset=ROOT/'megadrive/src/dungeon_drain_data.c';literal=bytes(int(x,16) for x in re.findall(r'0x([0-9a-fA-F]{2})',asset.read_text()));assert literal==source[0x9d86:0x9da6]
 data=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(data)==1048576 and data==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes();checksum=sum(int.from_bytes(data[i:i+2],'big') for i in range(0x200,len(data),2))&65535;assert int.from_bytes(data[0x18e:0x190],'big')==checksum
 assert data[0x1a4:0x1a8]==bytes.fromhex('000fffff') and data[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),rom_bytes=len(data),checksum=checksum,aliases_and_header_verified=True,production_changes_confined_to_4D_4E_behavior_dispatch_collision_publication_and_magic_accessor=True,prior_actor_and_main_implementations_unchanged_since_v0130=True,literal_table_bytes_exact=32,source_files={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'megadrive/src/main.c',ROOT/'megadrive/src/actors.c',asset,ROOT/'tools/validate_dungeon_drain.py',ROOT/'tools/validate_dungeon_drain_gameplay.py',ROOT/'tools/validate_dungeon_drain_hud.py',ROOT/'tools/prove_dungeon_drain_bounds.py']},full_game_ported=False,limits=['Controlled state injection and native initial clock alignment; whole original RNG/global clock not reproduced.','Natural hero contact after controlled relocation and actual magic HUD tile timing checked. Full natural fights and full framebuffer/SAT/audio remain unproved.','Interior expiry inherits sourceE; explicit0..3 tested and nonzero-vector bound derived under documented invariant.'])
 (ROOT/'validation/dungeon_drain_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Only4D/4E helpers/dispatch/publication and magic accessor added;32 literal bytes and ROM integrity verified.')
if __name__=='__main__':main()
