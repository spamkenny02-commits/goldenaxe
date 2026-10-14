"""Restrict56/59/5A teleport behavior and collision publication changes."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0138-39058dcb';old=(base/'actors.c').read_text();s=(ROOT/'megadrive/src/actors.c').read_text()
 a=s.index('/* 500E/A0E6 and501A/A29A:');b=s.index('/* 5071 -> A86D:',a);s=s[:a]+s[b:]
 d='            else if(entity[0]==0x56 || entity[0]==0x59 || entity[0]==0x5a) dungeon_teleport_behavior(entity,cells,hero_x,hero_y,frame,slot,NULL);\n';assert s.count(d)==1;s=s.replace(d,'')
 s=s.replace('entity[0]==0x14 || entity[0]==0x17 || entity[0]==0x18','entity[0]==0x14 || entity[0]==0x18').replace('((entity[0]>=0x4a && entity[0]<=0x56) || entity[0]==0x59 || entity[0]==0x5a)','(entity[0]>=0x4a && entity[0]<=0x55)')
 block="""        /* Teleport flash state is published after AI by0940. Cached sprite
         * ordering must not publish the preceding visible pose's boxes. */
        if(entity[0]!=0x56 && entity[0]!=0x59 && entity[0]!=0x5a)
        { entity[0x1b]=frame[1];entity[0x1c]=frame[2]; }"""
 assert s.count(block)==1;s=s.replace(block,'        entity[0x1b]=frame[1];entity[0x1c]=frame[2];')
 assert s==old,'Unrelated actor implementation changed'
 assert (ROOT/'megadrive/src/main.c').read_bytes()==(base/'main.c').read_bytes(),'Main game changed'
 data=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(data)==1048576 and data==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(data[i:i+2],'big') for i in range(0x200,len(data),2))&65535;assert int.from_bytes(data[0x18e:0x190],'big')==checksum
 assert data[0x1a4:0x1a8]==bytes.fromhex('000fffff') and data[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 evidence={}
 for name in ['dungeon_teleport_allocation_unit_report.json','dungeon_teleport_gameplay_report.json','dungeon_teleport_56_entry_report.json','dungeon_teleport_59_entry_report.json','dungeon_teleport_5a_entry_report.json','dungeon_teleport_cycle_entry_report.json']:
  p=ROOT/'validation'/name;d=json.loads(p.read_text());assert d['md_sha256']==sha(ROOT/'gaw-megadrive.bin');evidence[name]=sha(p)
 cycle=json.loads((ROOT/'validation/dungeon_teleport_cycle_entry_report.json').read_text());assert len(cycle['cases'])==2 and all(c['controlled_cycle_actor_frames_exact']==96 and c['controlled_cycle_sat_frames_exact']==95 and c['excluded_fixture_sat_frame']==3700 for c in cycle['cases'])
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),rom_bytes=len(data),checksum=checksum,aliases_and_header_verified=True,production_changes_confined_to_56_59_5A_AI_dispatch_and_collision_publication=True,prior_actor_and_main_implementations_unchanged_since_v0138_except_correct_17_same_frame_boxes=True,renderer_does_not_republish_cached_pre_flash_boxes_for_new_teleport_types=True,original_random_stream_reproduced=False,evidence_sha256=evidence,source_files={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'megadrive/src/main.c',ROOT/'megadrive/src/actors.c',ROOT/'tools/validate_dungeon_teleport.py',ROOT/'tools/validate_dungeon_teleport_gameplay.py',ROOT/'tools/validate_dungeon_teleport_entry.py',ROOT/'tools/validate_dungeon_teleport_cycle.py']},full_game_ported=False,limits=['Initial production clock explicitly aligned for controlled segments; source random reads controlled only in isolated cases. Parent random timer4 excluded for recorded reveal/shot frames.','Actual room appearance records exclude random X/Y/direction and align to first initialization; other actors and absolute load cadence not compared.','Controlled actual12C cycle: all768 actor bytes96 frames per region and actual SAT95 frames per region. Injection frame3700 is excluded from SAT comparison and recorded; no timeline shift applied.','Full natural fights, RNG/global clock, full framebuffer, complete audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_teleport_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Teleport AI and collision publication only; ROM integrity and six current evidence reports verified.')
if __name__=='__main__':main()
