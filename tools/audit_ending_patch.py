"""Verify ending-only integration, original resources and live current evidence."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0152-398b2f20';old=(base/'main.c').read_text();s=(ROOT/'megadrive/src/main.c').read_text()
 a=old.index('        if(game_state==12)\n        {',old.index('static void enter_initial_room'));b=old.index('        }\n        else step_room_transition();',a)+10;oldblock=old[a:b]
 a=s.index('static bool tick_world_simulation');b=s.index('#include "ending.inc"',a);body=s[a:b];body=body[body.index('{\n')+2:body.rindex('    return FALSE;')];body=body.replace(')) return TRUE;', ')) continue;')
 restored=''.join('        '+l+'\n' for l in body.splitlines());assert restored==oldblock[len('        if(game_state==12)\n        {\n'):-10],'World helper body changed'
 s=s[:a]+s[b+len('#include "ending.inc"\n\n'):]
 s=s.replace('        if(game_state==12) { if(tick_world_simulation()) continue; }\n',oldblock).replace('        if(game_state==14) { run_ending();return_to_title=TRUE;return; }\n','').replace('static u16 ending_hero_descriptor;\nextern const u8 ending_held_frame[],ending_axe_frame[];\n\n','').replace('ending_hero_descriptor==0x8495?ending_held_frame:ending_hero_descriptor==0x84e1?ending_axe_frame:','').replace('hero_casting=0;ending_hero_descriptor=0;','hero_casting=0;').replace('else game_state=14; /* 6EBE ending dispatch. */','else game_state=14; /* Original ending handoff; ending remains to port. */')
 assert s==old,'Unrelated main change'
 assert (ROOT/'megadrive/src/actors.c').read_bytes()==(base/'actors.c').read_bytes()
 source=(ROOT/'input/original.sms').read_bytes();assets=(ROOT/'megadrive/src/ending_data.c').read_text()
 def array(name):return bytes(int(x,16) for x in re.findall(r'0x([0-9a-f]{2})',assets.split('const u8 '+name+'[]={')[1].split('};')[0]))
 assert array('ending_text')==source[0x3334e:0x3384e]+bytes(1)
 assert array('ending_gem_bitmap')==source[0x12a81:0x12b01] and array('ending_held_bitmap')==source[0x12241:0x122d2]
 names=['ending_gameplay_report.json','ending_credits_unit_report.json','ending_native_terminal_profile.json','ending_native_profile.json','timing_report.json','timing-pal_report.json','inventory_restore_report.json','start_menu_audio_report.json']
 evidence={}
 for name in names:
  p=ROOT/'validation'/name;d=json.loads(p.read_text());assert d['md_sha256']==sha(ROOT/'gaw-megadrive.bin');evidence[name]=sha(p)
 d=json.loads((ROOT/'validation'/names[0]).read_text());assert len(d['cases'])==2 and all(c['credits_state_and_vscroll_steps_exact']==7424 and len(c['credits_images'])==5 and c['nine_gem_normalized_image_exact'] and c['music_8D_88_request_frames_exact'] for c in d['cases'])
 d=json.loads((ROOT/'validation'/names[1]).read_text());assert d['ticks']==7425 and d['all_8_state_bytes_vscroll_and_64_row_bytes_exact']
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 full=json.loads((ROOT/'validation/ending_native_profile.json').read_text());assert all(c['ending_entered']==3881 and c['returned_to_title']==19000 for c in full['cases'])
 for region in ['auto','pal']:
  r=(ROOT/f'validation/ending-native-{region}/ram_03900.bin').read_bytes();assert r[(sy['game_save_state']+0x28)^1]==1
  assert (ROOT/f'validation/ending-source-{region}/ram_03900.bin').read_bytes()[0xd8]==1
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(rom[i:i+2],'big') for i in range(512,len(rom),2))&65535
 assert int.from_bytes(rom[0x18e:0x190],'big')==checksum and rom[0x1a4:0x1a8]==bytes.fromhex('000fffff') and rom[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),checksum=checksum,rom_bytes=len(rom),aliases_header_verified=True,world_simulation_body_exactly_preserved=True,prior_actor_AI_unchanged_since_v0152=True,changes_confined_to_ending_and_shared_world_helper=True,source_ending_resources_verified=True,full_death_records_final_dungeon_defeat_flag=True,evidence_sha256=evidence,source_files_sha256={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'megadrive/src/main.c',ROOT/'megadrive/src/actors.c',ROOT/'megadrive/src/ending.inc',ROOT/'megadrive/src/ending_credits.inc',ROOT/'megadrive/src/ending_data.c',ROOT/'tools/validate_ending_gameplay.py']},ending_integrated=True,full_game_ported=False,limits=['Clock-aligned controlled terminal checkpoint verifies all credits steps, gem records and twelve normalized full scene captures. Absolute scene initialization and occasional original NTSC row-work IRQ differ by1..2 frames; the report retains times and aligns images by algorithm tick.','Full death profile includes native/source particles and final-dungeon defeat flag. Original random stream differs, so final particle drain and subsequent absolute sequence timing are not claimed equal.','Native28-row source map is displayed with a32-row MD ring and one new row per eight pixels; pixel captures include scroll wrap and late credits.','Natural complete final dungeon/victory, all intermediate video/audio frames, full music waveforms, source auxiliary objects, global RNG/clock/loading, SMS scanline clipping and hardware remain incomplete or unverified.'])
 (ROOT/'validation/ending_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Ending integration/resources and eight current reports verified; gameplay body/AI unchanged.')
if __name__=='__main__':main()
