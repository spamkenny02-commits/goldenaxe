"""Restrict5C/5D directional guards andA5 secondary sound changes."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0144-4fb44220';old=(base/'actors.c').read_text();s=(ROOT/'megadrive/src/actors.c').read_text()
 a=s.index('extern u16 world_hero_direction(void);');b=s.index('/* 5071 -> A86D:',a);s=s[:a]+s[b:]
 d='            else if(entity[0]==0x5c || entity[0]==0x5d) dungeon_guard_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot,NULL);\n';assert s.count(d)==1;s=s.replace(d,'').replace('(entity[0]>=0x4a && entity[0]<=0x5d)','(entity[0]>=0x4a && entity[0]<=0x5b)').replace('if(entity[0]<0x56 || entity[0]>0x5d)','if(entity[0]<0x56 || entity[0]>0x5b)');assert s==old,'Unrelated actor implementation changed'
 main=(ROOT/'megadrive/src/main.c').read_text();getter='u16 world_hero_direction(void) { return hero_direction; }\n';assert main.count(getter)==1;main=main.replace(getter,'');assert main.count('sound_effect(0xa5)')==3;main=main.replace('sound_effect(0xa5)','sound_effect_main(0xa5)');assert main==(base/'main.c').read_text(),'Unrelated main implementation changed'
 source=(ROOT/'input/original.sms').read_bytes();assert source[0x5c4e:0x5c53]==bytes.fromhex('3ea53208de')
 for address,want in [(0xa4e2,1),(0xa4ed,0),(0xa4f8,3),(0xa503,2)]:assert source[address:address+2]==bytes([0xfe,want])
 assert source[0xa485:0xa489]==bytes.fromhex('d985d985')
 data=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(data)==1048576 and data==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(data[i:i+2],'big') for i in range(0x200,len(data),2))&65535;assert int.from_bytes(data[0x18e:0x190],'big')==checksum
 assert data[0x1a4:0x1a8]==bytes.fromhex('000fffff') and data[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 evidence={};combat=[]
 names=['dungeon_guard_allocation_unit_report.json','dungeon_guard_gameplay_report.json','dungeon_guard_5c_entry_report.json','dungeon_guard_5d_entry_report.json']+[f'dungeon_guard_combat_{typ}_{mode}_entry_report.json' for typ in ['5c','5d'] for mode in ['allowed','blocked']]
 for name in names:
  p=ROOT/'validation'/name;d=json.loads(p.read_text());assert d['md_sha256']==sha(ROOT/'gaw-megadrive.bin');evidence[name]=sha(p)
  if 'combat_' in name:combat+=d['cases']
 assert len(combat)==8 and all(c['controlled_cycle_actor_hero_gold_sound_frames_exact']==32 and c['controlled_cycle_sat_frames_exact']==31 and c['hero_and_guard_sat_order_compared'] for c in combat)
 assert all(any(x[0]==0xa5 for x in c['setup_door_sound_request_and_effect_exact']['sms'].values()) for c in combat if c['type']==0x5d)
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),rom_bytes=len(data),checksum=checksum,aliases_and_header_verified=True,production_changes_confined_to_5C_5D_AI_damage_gate_dispatch_publication_hero_direction_getter_and_three_A5_secondary_requests=True,prior_actor_implementations_unchanged_since_v0144=True,facing_gate_uses_post_AI_facing=True,source_A5_secondary_queue_corrected=True,source_half_pixel16_movement_bytes_reused=True,original_random_stream_reproduced=False,evidence_sha256=evidence,source_files={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'megadrive/src/main.c',ROOT/'megadrive/src/actors.c',ROOT/'tools/validate_dungeon_guard.py',ROOT/'tools/validate_dungeon_guard_gameplay.py',ROOT/'tools/validate_dungeon_guard_entry.py',ROOT/'tools/validate_dungeon_guard_combat.py']},full_game_ported=False,limits=['Initial controlled clocks explicitly aligned; source random reads controlled only in isolated cases.','Normal C-button attacks from all four sides in passable controlled-map segments; actual16A/129 combat retains room terrain/resources and uses controlled actors/hero.','Setup hero invulnerability255 protects travel; hero-only relocation at3650 allows foreground door/shutter work to finish before3700 combat injection. Setup A5 request/current effect is compared.','Eight actual-room combat cases compare256 actor/hero/effect frames and248 hero+guard SAT frames; injection frame3700 excluded and retained, no timeline shift.','Natural room appearances exclude random X/Y/direction and align to initialization. Full natural fights, original RNG/global clock, full framebuffer/audio waveforms, prior loading-phase/loot presentation issues and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_guard_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Only5C/5D, hero-direction getter and three correctedA5 queue calls added; source gate, integrity and eight current reports verified.')
if __name__=='__main__':main()
