"""Bind original conditional scripts/resources and narrowly scoped native change."""
import hashlib,json,re
from actor_reference import ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0166-f3cb9b5b';s=(ROOT/'megadrive/src/main.c').read_text()
 s=s.replace('#include "conditional_house.inc"\n','').replace('    if(check_conditional_house(old_x,old_y,flags)) return;\n','')
 assert s==(base/'main.c').read_text(),'Unrelated main code changed'
 for name in ['actors.c','plain_house_data.c','house_gold.inc','house_gold_data.c','minigame.inc','minigame_core.inc','minigame_data.c','house_quest.inc','house_quest_data.c','save.inc']:assert (ROOT/'megadrive/src'/name).read_bytes()==(base/name).read_bytes()
 source=(ROOT/'input/original.sms').read_bytes();reference=json.loads((ROOT/'analysis/conditional_house_reference.json').read_text());asset=(ROOT/'megadrive/src/conditional_house_data.c').read_text()
 text=bytes(int(x,16) for x in re.findall(r'0x([0-9a-f]{2})',asset.split('const u8 conditional_house_text[]={')[1].split('};')[0]))
 for pc,offset in zip(reference['text_pcs'],reference['text_offsets']):
  a=0xc000+(pc&0x3fff);want=source[a:source.index(0,a)+1];assert text[offset:offset+len(want)]==want
 for name,key in [('conditional_house_pcs','text_pcs'),('conditional_house_offsets','text_offsets')]:
  values=[int(v) for v in asset.split('const u16 '+name+'[]={')[1].split('};')[0].split(',')];assert values==reference[key]
 for node,site in zip(reference['nodes'],[0xacfa,0xad03,0xad0c,0xad6c]):
  assert source[site:site+9]==b'\x01'+node[2].to_bytes(2,'little')+b'\x11'+node[3].to_bytes(2,'little')+bytes.fromhex('cd0366')
 assert source[0xacb9:0xacc0]==bytes.fromhex('3abbc0fece283a') and source[0xad55:0xad5c]==bytes.fromhex('3abbc0fe222810')
 evidence={}
 for name in ['conditional_house_unit_report.json','conditional_house_gameplay_report.json','house_dialogue_report.json']:
  p=ROOT/'validation'/name;d=json.loads(p.read_text());assert d['md_sha256']==sha(ROOT/'gaw-megadrive.bin');evidence[name]=sha(p)
 d=json.loads((ROOT/'validation/conditional_house_unit_report.json').read_text());assert d['cases']==5040 and d['text_flags_gold_counts_and_requests_exact']
 d=json.loads((ROOT/'validation/conditional_house_gameplay_report.json').read_text());assert len(d['cases'])==24 and all(c['dialogue_bitmap_bytes_exact']==1040 and c['restored_gold_HUD_exact'] for c in d['cases'])
 assert sum(c['scenario']=='wrapped' and c['observed_gold_unit_count']==256 for c in d['cases'])==2
 assert all(c['repeat_interaction_no_second_reward'] for c in d['cases'] if c['house']==7)
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(rom[i:i+2],'big') for i in range(512,len(rom),2))&65535
 assert int.from_bytes(rom[0x18e:0x190],'big')==checksum and rom[0x1a4:0x1a8]==bytes.fromhex('000fffff') and rom[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),checksum=checksum,rom_bytes=len(rom),aliases_header_verified=True,main_change_only_conditional_house_include_and_hook=True,prior_actors_plain_dialogues_gold_minigame_quest_save_unchanged=True,nine_source_texts_and_four_actual_call_operands_verified=True,evidence_sha256=evidence,full_game_ported=False,limits=['5040 actual room-script/routine comparisons and24 controlled live integrations. Source ROM unpatched for live tests. No original absolute text publication timing claim; animated NPC map words excluded and differences retained.','Natural acquisition of prerequisites, full SRAM quest progression and complete playthrough remain unproved. Fairy5FC7 and paid gate6036 source handlers are next unported classes to investigate.','Provisional RNG, global timing, scanline clipping, inherited loot expiry visuals and complete audio/video/hardware fidelity remain incomplete/unverified.'])
 (ROOT/'validation/conditional_house_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Conditional-only scope, source calls/texts, prior systems, ROM integrity and three current reports verified.')
if __name__=='__main__':main()
