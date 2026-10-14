"""Original toll tables, scoped native integration and current evidence."""
import hashlib,json,re
from actor_reference import ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0170-a4972307';s=(ROOT/'megadrive/src/main.c').read_text()
 s=s.replace('#include "paid_passage.inc"\n','').replace('    if(check_paid_passage(old_x,old_y,flags)) return;\n','')
 assert s==(base/'main.c').read_text(),'Unrelated main code changed'
 for name in ['actors.c','plain_house_data.c','house_gold.inc','house_gold_data.c','minigame.inc','minigame_core.inc','minigame_data.c','house_quest.inc','house_quest_data.c','save.inc','conditional_house.inc','conditional_house_data.c','fairy.inc','fairy_data.c']:assert (ROOT/'megadrive/src'/name).read_bytes()==(base/name).read_bytes()
 source=(ROOT/'input/original.sms').read_bytes();ref=json.loads((ROOT/'analysis/paid_passage_reference.json').read_text());asset=(ROOT/'megadrive/src/paid_passage_data.c').read_text()
 def data(name):return bytes(int(v) for v in asset.split('const u8 '+name+'[]={')[1].split('};')[0].split(','))
 towns=[];prices=[];p=0x6087;price=0
 while p<0x6093:
  town=source[p];p+=1
  if not town:price=source[p];p+=1;continue
  towns.append(town);prices.append(price)
 assert towns==ref['towns'] and prices==ref['prices'] and data('paid_passage_towns')==bytes(towns) and data('paid_passage_prices')==bytes(prices)
 assert data('paid_passage_text')==source[0xd11e:source.index(0,0xd11e)+1]
 routes=[[source[p],*source[p+9:p+12]] for p in range(0x61a8,0x61ba,3)]
 assert routes==ref['routes'] and routes==[[int(v) for v in r.split(',')] for r in re.findall(r'\{([0-9,]+)\}',asset.split('const u8 paid_passage_routes[][4]=')[1])]
 evidence={}
 for name in ['paid_passage_unit_report.json','paid_passage_gameplay_report.json','minigame_gameplay_report.json','fairy_walk_gameplay_report.json']:
  p=ROOT/'validation'/name;d=json.loads(p.read_text());assert d['md_sha256']==sha(ROOT/'gaw-megadrive.bin');evidence[name]=sha(p)
 d=json.loads((ROOT/'validation/paid_passage_unit_report.json').read_text());assert d['cases']==18528 and d['fields_cells_price_text_gold_count_request_and_exit_exact']
 d=json.loads((ROOT/'validation/paid_passage_gameplay_report.json').read_text());assert len(d['cases'])==20 and sum(c['paid'] for c in d['cases'])==16 and sum(c['inventory_roundtrip'] for c in d['cases'])==2
 assert all(c['prompt_bitmap_bytes_exact']==1040 and c['confirmation_frame_bytes_exact']==48 for c in d['cases'])
 d=json.loads((ROOT/'validation/minigame_gameplay_report.json').read_text());assert len(d['cases'])==12
 d=json.loads((ROOT/'validation/fairy_walk_gameplay_report.json').read_text());assert len(d['cases'])==2 and all(c['natural_approach_after_door_fixture'] for c in d['cases'])
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(rom[i:i+2],'big') for i in range(512,len(rom),2))&65535
 assert int.from_bytes(rom[0x18e:0x190],'big')==checksum and rom[0x1a4:0x1a8]==bytes.fromhex('000fffff') and rom[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),checksum=checksum,rom_bytes=len(rom),aliases_header_verified=True,main_change_only_paid_passage_include_and_hook=True,prior_actor_dialogue_fairy_quest_save_gold_minigame_sources_unchanged=True,six_original_prices_routes_prompt_exact=True,evidence_sha256=evidence,full_game_ported=False,limits=['18528 source/native rule cases and20 live controlled passage integrations,16 walking opposite exits and2 menu roundtrips. Original live source unpatched; destination enemy mask0 seeded before entry to isolate encounters. Animated NPC cells excluded and differences retained.','Uncontrolled6D->96 route encountered native damage/knockback after correct exit; diagnostic retained. Combat RNG/global timing remains unresolved, not claimed fixed by this passage change.','Absolute fade/load/text cadence, complete natural progression/SRAM/hardware/audio/video equivalence, sprite scanline clipping, auxiliary entities and inherited loot expiry visuals remain incomplete/unverified.'])
 (ROOT/'validation/paid_passage_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Paid-passage-only source changes, ROM integrity and four current reports verified.')
if __name__=='__main__':main()
