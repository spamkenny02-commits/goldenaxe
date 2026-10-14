"""Restrict ordinary NPC lookup extension and bind current selection/live evidence."""
import hashlib,json,re
from actor_reference import ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0161-e14b3079';old=(base/'main.c').read_text();s=(ROOT/'megadrive/src/main.c').read_text()
 a=old.index('extern const u8 house_npc_text[]');b=old.index('    /* Keep the live room',a);c=s.index('extern const u8 plain_house_text[]');d=s.index('    /* Keep the live room',c)
 s=s[:c]+old[a:b]+s[d:];s=s.replace('show_dialogue_text(plain_house_text+number,TRUE);','show_dialogue_text(house_npc_text+number,TRUE);');assert s==old,'Unrelated gameplay changed'
 for name in ['actors.c','save.inc','house_quest.inc','house_quest_data.c']:assert (ROOT/'megadrive/src'/name).read_bytes()==(base/name).read_bytes()
 reference=json.loads((ROOT/'analysis/plain_house_dialogue_reference.json').read_text());assert len(reference['nodes'])==21 and len(reference['contexts'])==65
 source=(ROOT/'input/original.sms').read_bytes();asset=(ROOT/'megadrive/src/plain_house_data.c').read_text();text=bytes(int(x,16) for x in re.findall(r'0x([0-9a-f]{2})',asset.split('const u8 plain_house_text[]={')[1].split('};')[0]));rows=[[int(x) for x in r.split(',')] for r in re.findall(r'\{([0-9,]+)\}',asset)]
 assert len(rows)==65
 for row,r in zip(rows,reference['contexts']):
  assert row[:3]==[r['room'],r['coordinate'],r['outside']];a=0xc000+(r['text_pc']&0x3fff);want=source[a:source.index(0,a)+1];assert text[row[3]:row[3]+len(want)]==want
 names=['plain_house_unit_report.json','plain_house_gameplay_report.json','house_dialogue_report.json'];evidence={}
 for name in names:
  p=ROOT/'validation'/name;d=json.loads(p.read_text());assert d['md_sha256']==sha(ROOT/'gaw-megadrive.bin');evidence[name]=sha(p)
 d=json.loads((ROOT/'validation'/names[0]).read_text());assert d['cases']==1560 and d['contexts']==65 and d['source_text_pointer_exact']
 d=json.loads((ROOT/'validation'/names[1]).read_text());assert len(d['cases'])==2 and all(c['long_dialogue_bitmap_bytes_exact']==1040 and c['restored_static_map_words_exact']==636 for c in d['cases'])
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(rom[i:i+2],'big') for i in range(512,len(rom),2))&65535;assert int.from_bytes(rom[0x18e:0x190],'big')==checksum and rom[0x1a4:0x1a8]==bytes.fromhex('000fffff') and rom[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),checksum=checksum,rom_bytes=len(rom),aliases_header_verified=True,changes_confined_to_plain_house_dialogue_selection_and_ROM_text_data=True,prior_quest_save_AI_unchanged_since_v0161=True,all_65_source_texts_exact=True,evidence_sha256=evidence,full_game_ported=False,limits=['1560 original667E selector cases cover all65 exported context rows plus rejected flags/coordinates. No text/condition shim except the observed frontend return.','Actual townB3/house8F263-byte dialogue uses controlled entry/hero setup and initial clock alignment, normal UP/C, stable bitmap and static restoration. Four animated NPC words remain outside static equality; publication cadence and all natural routes are unproved.','Six prior village conversations and walking regression pass. Other NPC handlers/minigame/scripts, natural full progression, RNG/global timing, scanline clipping and full audio/video/hardware remain incomplete or unverified.'])
 (ROOT/'validation/plain_house_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Ordinary NPC-only scope,65 source strings, ROM integrity and three current reports verified.')
if __name__=='__main__':main()
