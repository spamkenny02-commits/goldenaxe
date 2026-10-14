"""Bind gold-house source data, narrowly scoped native changes and current tests."""
import hashlib,json,re
from actor_reference import ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0162-233c614a';main=(ROOT/'megadrive/src/main.c').read_text()
 main=main.replace('#include "house_gold.inc"\n','').replace('    if(check_house_gold(old_x,old_y,flags)) return;\n','')
 assert main==(base/'main.c').read_text(),'Unrelated main code changed'
 for name in ['actors.c','plain_house_data.c']:assert (ROOT/'megadrive/src'/name).read_bytes()==(base/name).read_bytes()
 source=(ROOT/'input/original.sms').read_bytes();reference=json.loads((ROOT/'analysis/house_gold_reference.json').read_text());p=0x651c;amount=0;records=[]
 while len(records)<33:
  town=source[p];p+=1
  if town==0:amount=source[p];p+=1;continue
  records.append([town,amount])
 assert records==reference['records'] and len(records)==33
 asset=(ROOT/'megadrive/src/house_gold_data.c').read_text()
 def data(name):return bytes(int(x,16) for x in re.findall(r'0x([0-9a-f]{2})',asset.split('const u8 '+name+'[]={')[1].split('};')[0]))
 assert data('house_gold_towns')==bytes(r[0] for r in records)
 assert data('house_gold_amounts')==bytes(r[1]&255 for r in records)
 for name,pc in [('house_gold_gain_text',0x8e30),('house_gold_loss_text',0x8df6)]:
  a=0xc000+(pc&0x3fff);assert data(name)==source[a:source.index(0,a)+1]
 evidence={}
 for name in ['house_gold_unit_report.json','house_gold_gameplay_report.json','house_dialogue_report.json']:
  p=ROOT/'validation'/name;d=json.loads(p.read_text());assert d['md_sha256']==sha(ROOT/'gaw-megadrive.bin');evidence[name]=sha(p)
 d=json.loads((ROOT/'validation/house_gold_unit_report.json').read_text());assert d['cases']==13992 and d['all_256_gold_values']
 d=json.loads((ROOT/'validation/house_gold_gameplay_report.json').read_text());assert len(d['cases'])==8 and all(c['restored_gold_HUD_exact'] and c['unit_cadence_two_frames_exact'] for c in d['cases'])
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(rom[i:i+2],'big') for i in range(512,len(rom),2))&65535
 assert int.from_bytes(rom[0x18e:0x190],'big')==checksum and rom[0x1a4:0x1a8]==bytes.fromhex('000fffff') and rom[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),checksum=checksum,rom_bytes=len(rom),aliases_header_verified=True,main_change_only_gold_include_and_hook=True,actors_and_ordinary_dialogue_data_unchanged=True,all_33_source_amounts_and_both_texts_exact=True,evidence_sha256=evidence,full_game_ported=False,limits=['Gold-only controlled scope, not full game completion. Original/live gold arithmetic, visit flag, stable bitmap, HUD restoration and two-frame unit cadence covered.','Text publication start frames can differ; full audio waveforms, all natural routes, minigame and other quest families, RNG, scanline clipping and hardware remain incomplete/unverified.'])
 (ROOT/'validation/house_gold_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Gold-only changes, source33 amounts/texts, ROM integrity and current evidence verified.')
if __name__=='__main__':main()
