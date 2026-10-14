"""Bind fairy source resources, original rules and controlled rendering evidence."""
import hashlib,json,re
from actor_reference import ROOT
from extract_title import rle_planes
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0167-cbcbfa73';s=(ROOT/'megadrive/src/main.c').read_text()
 for change in ['#include "fairy.inc"\n','    if(check_fairy(old_x,old_y,flags)) return;\n','extern const u8 fairy_heart_icon[],fairy_magic_icon[];\n','    else if(item==42) memcpy(sms_vram+0x3780,fairy_heart_icon,128);\n','    else if(item==28) memcpy(sms_vram+0x3780,fairy_magic_icon,128);\n']:s=s.replace(change,'')
 assert s==(base/'main.c').read_text(),'Unrelated main code changed'
 for name in ['actors.c','plain_house_data.c','house_gold.inc','house_gold_data.c','minigame.inc','minigame_core.inc','minigame_data.c','house_quest.inc','house_quest_data.c','save.inc','conditional_house.inc','conditional_house_data.c']:assert (ROOT/'megadrive/src'/name).read_bytes()==(base/name).read_bytes()
 source=(ROOT/'input/original.sms').read_bytes();ref=json.loads((ROOT/'analysis/fairy_reference.json').read_text());asset=(ROOT/'megadrive/src/fairy_data.c').read_text()
 def data(name):return bytes(int(x,16) for x in re.findall(r'0x([0-9a-f]{2})',asset.split('const u8 '+name+'[]={')[1].split('};')[0]))
 records=[];p=0x602a;kind=0
 while p<0x6036:
  town=source[p];p+=1
  if not town:kind=source[p];p+=1;continue
  records.append([town,kind])
 assert records==ref['records'] and len(records)==8
 assert data('fairy_towns')==bytes(t for t,k in records) and data('fairy_kinds')==bytes(k for t,k in records)
 for name,pc in zip(['fairy_life_text','fairy_magic_text','fairy_life_label','fairy_magic_label'],ref['text_pcs']+ref['label_pcs']):
  a=0xc000+(pc&0x3fff);assert data(name)==source[a:source.index(0,a)+1]
 icon=bytearray(128);end,_=rle_planes(source,0x13bb9,icon,0,4);assert end==ref['heart_rle_end'] and data('fairy_heart_icon')==bytes(icon)
 assert data('fairy_magic_icon')==source[0x13601:0x13681]
 evidence={}
 for name in ['fairy_unit_report.json','fairy_gameplay_report.json','fairy_walk_gameplay_report.json','house_quest_gameplay_report.json']:
  p=ROOT/'validation'/name;d=json.loads(p.read_text());assert d['md_sha256']==sha(ROOT/'gaw-megadrive.bin');evidence[name]=sha(p)
 d=json.loads((ROOT/'validation/fairy_unit_report.json').read_text());assert d['cases']==11200 and d['save_HP_MP_capacities_item_text_refill_count_request_exact']
 d=json.loads((ROOT/'validation/fairy_gameplay_report.json').read_text());assert len(d['cases'])==24 and all(c['final_HUD_visual_words_exact']==128 and c['reward_pattern_tiles_exact']==38 and c['transformed_cells_exact']==160 for c in d['cases'])
 d=json.loads((ROOT/'validation/fairy_walk_gameplay_report.json').read_text());assert len(d['cases'])==2 and all(c['natural_approach_after_door_fixture'] and c['final_HUD_visual_words_exact']==128 for c in d['cases'])
 d=json.loads((ROOT/'validation/house_quest_gameplay_report.json').read_text());assert len(d['cases'])==12 and all(c['reward_pattern_tiles_exact']==38 for c in d['cases'])
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(rom[i:i+2],'big') for i in range(512,len(rom),2))&65535
 assert int.from_bytes(rom[0x18e:0x190],'big')==checksum and rom[0x1a4:0x1a8]==bytes.fromhex('000fffff') and rom[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),checksum=checksum,rom_bytes=len(rom),aliases_header_verified=True,main_change_only_fairy_include_hook_two_icon_branches=True,prior_actor_dialogue_quest_save_gold_minigame_sources_unchanged=True,eight_source_contexts_texts_labels_icons_exact=True,evidence_sha256=evidence,full_game_ported=False,limits=['11200 actualB205 rule comparisons and24 placed and2 walking live integrations cover source carry/borrow behavior, once-only flag, full byte capacities/refill and controlled frontend restoration. Source ROM unpatched for live checks.','128 final HUD words compare after masking unused SMS attribute bits13..15. Static room maps exclude animated NPC words and retain differences. Full frame/publication/music timing and natural acquisition/progression remain unproved.','Paid gate6036/616F is still unported. Provisional RNG, global timing, scanline clipping, inherited loot expiry visuals and complete hardware/audio/video fidelity remain open.'])
 (ROOT/'validation/fairy_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Fairy-only source changes/assets, ROM integrity and four current reports verified.')
if __name__=='__main__':main()
