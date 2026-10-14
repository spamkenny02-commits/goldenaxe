"""Bind original minigame tables/texts, contained native changes and evidence."""
import hashlib,json,re
from actor_reference import ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0163-cd04a76a';s=(ROOT/'megadrive/src/main.c').read_text()
 s=s.replace('#include "minigame.inc"\n','').replace('    if(check_minigame(old_x,old_y,flags)) return;\n','')
 assert s==(base/'main.c').read_text(),'Unrelated main code changed'
 for name in ['actors.c','plain_house_data.c','house_gold.inc','house_gold_data.c']:assert (ROOT/'megadrive/src'/name).read_bytes()==(base/name).read_bytes()
 source=(ROOT/'input/original.sms').read_bytes();reference=json.loads((ROOT/'analysis/minigame_reference.json').read_text());asset=(ROOT/'megadrive/src/minigame_data.c').read_text()
 def data(name):return bytes(int(x,16) for x in re.findall(r'0x([0-9a-f]{2})',asset.split('const u8 '+name+'[]={')[1].split('};')[0]))
 ranges={'minigame_weights':(0x6776,0x6796),'minigame_pairs':(0x6796,0x67a2),'minigame_inverse':(0x67f9,0x6809),'minigame_lucky':(0x6801,0x6809),'minigame_scores':(0x68c3,0x68c7),'minigame_coordinates':(0x68ec,0x68f6),'minigame_confirm_words':(0x614e,0x6160)}
 for name,(a,b) in ranges.items():assert data(name)==source[a:b]
 assert data('minigame_confirm_font')==b''.join(source[0xc7c6+(c-65)*8:0xc7c6+(c-65)*8+8] for c in b'OUIN')
 for pc,offset in zip(reference['text_pcs'],reference['text_offsets']):
  a=0xc000+(pc&0x3fff);want=source[a:source.index(0,a)+1];assert data('minigame_text')[offset:offset+len(want)]==want
 evidence={}
 for name in ['minigame_unit_report.json','minigame_gameplay_report.json','house_gold_gameplay_report.json','house_dialogue_report.json']:
  p=ROOT/'validation'/name;d=json.loads(p.read_text());assert d['md_sha256']==sha(ROOT/'gaw-megadrive.bin');evidence[name]=sha(p)
 d=json.loads((ROOT/'validation/minigame_unit_report.json').read_text());assert d['cases']==19491 and d['cells_stage_gold_text_count_requests_exact']
 d=json.loads((ROOT/'validation/minigame_gameplay_report.json').read_text());assert len(d['cases'])==12 and sum(c['inventory_roundtrip_during_game'] for c in d['cases'])==2
 assert sum(c['replay_deducts_ten_and_resets_cards'] for c in d['cases'])==2 and sum(c['entry_refused_without_payment'] for c in d['cases'])==4
 assert all(c['confirmation_font_tiles_exact']==4 and c['confirmation_frame_bytes_exact']==48 and c['dialogue_bitmap_bytes_exact']==1040 for c in d['cases'])
 d=json.loads((ROOT/'validation/house_gold_gameplay_report.json').read_text());assert len(d['cases'])==8 and all(c['restored_gold_HUD_exact'] for c in d['cases'])
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(rom[i:i+2],'big') for i in range(512,len(rom),2))&65535
 assert int.from_bytes(rom[0x18e:0x190],'big')==checksum and rom[0x1a4:0x1a8]==bytes.fromhex('000fffff') and rom[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),checksum=checksum,rom_bytes=len(rom),aliases_header_verified=True,main_change_only_minigame_include_and_hook=True,actors_ordinary_dialogues_gold_unchanged=True,original_card_tables_nine_texts_confirmation_font_exact=True,evidence_sha256=evidence,full_game_ported=False,limits=['Minigame rules and controlled frontends verified, not original RNG/refresh timing. Production still uses the existing provisional SGDK RNG with original32-way mapping and repeat-special rejection.','Live source RNG inputs controlled, native randbase seeded. Absolute transition/text cadence and full audio/video/hardware equivalence remain unverified.','Other conditional quest families, full natural progression, inherited loot expiry visuals and scanline sprite clipping remain incomplete/unverified.'])
 (ROOT/'validation/minigame_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Minigame-only scope, original resources, ROM integrity and four current reports verified.')
if __name__=='__main__':main()
