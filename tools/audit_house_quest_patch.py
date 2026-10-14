"""Verify quest-giver integration, independent equipment load and current evidence."""
import hashlib,json,re
from actor_reference import ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0158-ae1a4d11';old=(base/'main.c').read_text();s=(ROOT/'megadrive/src/main.c').read_text()
 s=s.replace('static void prepare_hero_armor_palette(void);\nstatic void show_item_reward_text(u16 item,u16 index,const u8 *custom_label)','static void show_item_reward(u16 item,u16 index)').replace('custom_label?custom_label:labels+label','labels+label').replace('    if(custom_label) { prepare_hero_armor_palette();sms_palette[31]=(world_clock()&2)?2:1;set_world_palette(); }\n','').replace('static void show_item_reward(u16 item,u16 index)\n{ show_item_reward_text(item,index,NULL); }\n\n','').replace('#include "house_quest.inc"\n\n','').replace('check_house_talk(u16 old_x,u16 old_y,u8 flags)','check_house_talk(u16 old_x,u16 old_y)').replace('check_house_talk(old_x,old_y,script_flags)','check_house_talk(old_x,old_y)').replace('    if(check_house_quest(old_x,old_y,flags)) return;\n','').replace('u8 expanded[512];','u8 expanded[256];').replace('u8 substitution_end[512]={0};','u8 substitution_end[256]={0};')
 assert s==old,'Unrelated main behavior changed'
 save=(ROOT/'megadrive/src/save.inc').read_text().replace('hero_armor_level=game_save_state[0x41];hero_basic_level=game_save_state[0x30];','hero_armor_level=hero_basic_level=game_save_state[0x41];')
 assert save==(ROOT/'analysis/house-quest-baseline-v0158/save.inc').read_text()
 for name in ['actors.c','ending.inc','ending_credits.inc','ending_data.c']:assert (ROOT/'megadrive/src'/name).read_bytes()==(base/name).read_bytes()
 source=(ROOT/'input/original.sms').read_bytes();assets=(ROOT/'megadrive/src/house_quest_data.c').read_text()
 data=lambda name:bytes(int(x,16) for x in re.findall(r'0x([0-9a-f]{2})',assets.split('const u8 '+name+'[]={')[1].split('};')[0]))
 text=data('house_quest_text');index=data('house_quest_text_index');pcs=[0xac1e,0xa52f,0x8e5c,0x8e94,0x8ed9,0x8bea,0x8fe3,0x90bf,0x905b]
 for n,pc in enumerate(pcs):
  offset=int.from_bytes(index[n*2:n*2+2],'little');a=0xc000+(pc&0x3fff);want=source[a:source.index(0,a)+1];assert text[offset:offset+len(want)]==want
 assert source.index(0,0xced9)-0xced9==265
 names=['house_quest_unit_report.json','house_quest_gameplay_report.json','house_quest_hint_gameplay_report.json','independent_equipment_load_report.json','save_report.json','house_dialogue_report.json']
 evidence={}
 for name in names:
  p=ROOT/'validation'/name;d=json.loads(p.read_text());assert d['md_sha256']==sha(ROOT/'gaw-megadrive.bin');evidence[name]=sha(p)
 d=json.loads((ROOT/'validation'/names[0]).read_text());assert d['cases']==1836 and d['all_inventory_equipment_curse_capacity_defeat_and_action_fields_exact']
 d=json.loads((ROOT/'validation'/names[1]).read_text());assert len(d['cases'])==12 and all(c['reward_pattern_tiles_exact']==38 for c in d['cases'])
 d=json.loads((ROOT/'validation'/names[2]).read_text());assert len(d['cases'])==2 and all(c['long_dialogue_bitmap_bytes_exact']==1040 and c['restored_static_map_words_exact']==636 for c in d['cases'])
 d=json.loads((ROOT/'validation'/names[3]).read_text());assert len(d['cases'])==6 and all(c['loaded_equipment_curse_attack_defense_and_inventory_frames_exact']==21 and c['basic']!=c['armor'] for c in d['cases'])
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(rom[i:i+2],'big') for i in range(512,len(rom),2))&65535
 assert int.from_bytes(rom[0x18e:0x190],'big')==checksum and rom[0x1a4:0x1a8]==bytes.fromhex('000fffff') and rom[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),rom_bytes=len(rom),checksum=checksum,aliases_header_verified=True,prior_AI_and_ending_unchanged_since_v0158=True,changes_confined_to_house_quests_custom_reward_labels_dialogue_capacity_and_primary_load_offset=True,source_strings_verified=True,independent_primary_armor_load_verified=True,evidence_sha256=evidence,source_files_sha256={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'megadrive/src/main.c',ROOT/'megadrive/src/save.inc',ROOT/'megadrive/src/house_quest.inc',ROOT/'megadrive/src/house_quest_data.c',ROOT/'tools/validate_house_quest.py',ROOT/'tools/validate_house_quest_gameplay.py',ROOT/'tools/validate_independent_equipment_load.py']},full_game_ported=False,limits=['Actual town door dispatch follows controlled exterior/one-pixel entry fixture; NPC position and native clock align explicitly. Normal UP/C trigger and dismiss gifts/text.','Long265-byte refusal compares stable1040 bitmap bytes and636 static room words; four animated NPC words are excluded, with actual differences retained. Publication/animation phase and full framebuffer are not claimed equal.','Cold-load fixtures have identical source/native SRAM payloads with distinct primary/armor/curse fields; complete natural quest-to-save progression is not established.','Remaining NPC families, natural quest routes/victory, original RNG/global timing, scanline clipping, full audio/video and hardware remain incomplete or unverified.'])
 (ROOT/'validation/house_quest_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Quest integration/resources, independent load, ROM integrity and six current reports verified.')
if __name__=='__main__':main()
