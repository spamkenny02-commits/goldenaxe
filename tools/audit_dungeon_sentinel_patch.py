"""Restrict57/58 sentinel behavior and collision publication changes."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0140-cc830a82';old=(base/'actors.c').read_text();s=(ROOT/'megadrive/src/actors.c').read_text()
 a=s.index('/* 5014 ->A181:');b=s.index('/* 5071 -> A86D:',a);s=s[:a]+s[b:]
 d='            else if(entity[0]==0x57 || entity[0]==0x58) dungeon_sentinel_behavior(entity,tilemap,hero_x,hero_y,room,slot,NULL);\n';assert s.count(d)==1;s=s.replace(d,'')
 s=s.replace('(entity[0]>=0x4a && entity[0]<=0x5a)','((entity[0]>=0x4a && entity[0]<=0x56) || entity[0]==0x59 || entity[0]==0x5a)').replace('if(entity[0]<0x56 || entity[0]>0x5a)','if(entity[0]!=0x56 && entity[0]!=0x59 && entity[0]!=0x5a)')
 assert s==old,'Unrelated actor implementation changed'
 assert (ROOT/'megadrive/src/main.c').read_bytes()==(base/'main.c').read_bytes(),'Main game changed'
 source=(ROOT/'input/original.sms').read_bytes()
 assert source[0xa18f:0xa195]==bytes.fromhex('013900cd7858') and source[0xa1bc:0xa1be]==bytes.fromhex('fe18') and source[0xa1cb:0xa1cd]==bytes.fromhex('fe18')
 data=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(data)==1048576 and data==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(data[i:i+2],'big') for i in range(0x200,len(data),2))&65535;assert int.from_bytes(data[0x18e:0x190],'big')==checksum
 assert data[0x1a4:0x1a8]==bytes.fromhex('000fffff') and data[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 evidence={}
 for name in ['dungeon_sentinel_allocation_unit_report.json','dungeon_sentinel_gameplay_report.json','dungeon_sentinel_57_entry_report.json','dungeon_sentinel_58_entry_report.json','dungeon_sentinel_approach_57_entry_report.json','dungeon_sentinel_approach_58_entry_report.json','dungeon_sentinel_park_entry_report.json','dungeon_sentinel_unaligned_approach_diagnostic.json']:
  p=ROOT/'validation'/name;d=json.loads(p.read_text());assert d['md_sha256']==sha(ROOT/'gaw-megadrive.bin');evidence[name]=sha(p)
 park=json.loads((ROOT/'validation/dungeon_sentinel_park_entry_report.json').read_text());assert len(park['cases'])==2 and all(c['controlled_cycle_actor_frames_exact']==129 and c['controlled_cycle_sat_frames_exact']==128 and c['excluded_fixture_sat_frame']==3700 for c in park['cases'])
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),rom_bytes=len(data),checksum=checksum,aliases_and_header_verified=True,production_changes_confined_to_57_58_AI_dispatch_and_collision_publication=True,prior_actor_and_main_implementations_unchanged_since_v0140=True,literal_movement_arrays_reused=['85D9..85E9','85EA..85FA'],original_random_stream_reproduced=False,evidence_sha256=evidence,source_files={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'megadrive/src/main.c',ROOT/'megadrive/src/actors.c',ROOT/'tools/validate_dungeon_sentinel.py',ROOT/'tools/validate_dungeon_sentinel_gameplay.py',ROOT/'tools/validate_dungeon_sentinel_entry.py',ROOT/'tools/validate_dungeon_sentinel_approach.py',ROOT/'tools/validate_dungeon_sentinel_park.py']},full_game_ported=False,limits=['Initial production clock explicitly aligned; source random reads controlled only in isolated cases.','Actual181/15C hidden records align to first initialization; absolute load cadence not claimed.','Unaligned PAL58 approach failed with a one-tick animation difference. Controlled approach explicitly resets both first-sentinel animation counters11/14 at3600; this does not fix the underlying load cadence.','Actual15C park129 actor frames and128 SAT frames per region; injection frame3700 excluded from SAT and recorded, no timeline shift.','Full natural fights, RNG/global clock, full framebuffer, complete audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_sentinel_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Only57/58 AI and collision publication added; integrity and eight evidence files, including the unresolved PAL phase diagnostic, verified.')
if __name__=='__main__':main()
