"""Save/cold-load actual quest gifts through unpatched production save frontends.

Gift snapshots are transferred to the established save-point fixture;an
uninterrupted journey from each gift house to that save point is not implied.
"""
import contextlib,hashlib,io,json,re,sys
from validate_save import ROUTE,native
from run_core import ROOT,run

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
 source=ROOT/'input/original.sms';md=ROOT/'gaw-megadrive.bin';digest=hashlib.sha256(md.read_bytes()).hexdigest()
 gameplay=json.loads((ROOT/'validation/house_quest_persistence_gameplay_report.json').read_text());assert gameplay['md_sha256']==digest
 matrix=[r for r in gameplay['cases'] if not r['outside_context_replaced_after_door']]
 if '--first-only' in sys.argv:matrix=matrix[:1]
 results=[]
 for case in matrix:
  town=case['town'];region=case['region'];name=f'{town:02x}-{region}'
  sf=ROOT/f'validation/house-quest-persistence-{name}-sms';nf=ROOT/f'validation/house-quest-persistence-{name}-md'
  for folder in [sf,nf]:assert json.loads((folder/'capture.json').read_text())['rom_sha256']==(hashlib.sha256(source.read_bytes()).hexdigest() if folder==sf else digest)
  s=(sf/'ram_04800.bin').read_bytes();n=native(nf,4800)
  read=lambda key:int.from_bytes(n[sy[key]:sy[key]+2],'big')
  flags=s[0x100:0x200];items=s[0xe0:0xf1];armor=s[0xf1];shield=s[0xf2];curse=s[0xbf];capacity=s[0xda];story=s[0xd4]
  assert flags[town]&2
  assert n[sy['game_save_state']+0x50:sy['game_save_state']+0x150]==flags,('live gift flags',name)
  assert bytes([read('hero_basic_level'),read('hero_weapon_level')])+n[sy['hero_items']+2:sy['hero_items']+17]==items,('live gift inventory',name)
  assert [read('hero_armor_level'),read('hero_shield_level'),n[sy['game_save_state']+15],read('hero_max_health'),n[sy['game_save_state']+0x24]]==[armor,shield,curse,capacity,story],('live gift equipment',name)
  srams={};cold_fields={}
  for tag,path in [('sms',source),('md',md)]:
   folder=ROOT/f'validation/quest-gift-save-{name}-{tag}';sram=folder.with_suffix('.srm')
   if tag=='sms':writes=[(3340,0x100,flags),(3340,0xe0,items),(3340,0xf1,bytes([armor,shield])),(3340,0xbf,bytes([curse])),(3340,0xda,bytes([capacity])),(3340,0xd4,bytes([story]))]
   else:
    writes=[(3340,sy['game_save_state']+0x50,flags),(3340,sy['hero_items'],items),(3340,sy['game_save_state']+15,bytes([curse])),(3340,sy['game_save_state']+0x24,bytes([story]))]
    writes += [(3340,sy[k],v.to_bytes(2,'big')) for k,v in [('hero_basic_level',items[0]),('hero_weapon_level',items[1]),('hero_armor_level',armor),('hero_shield_level',shield),('hero_max_health',capacity)]]
   with contextlib.redirect_stdout(io.StringIO()):
    run(path,4400,folder,{4400},([(200,220,0)] if tag=='sms' else [])+ROUTE+[(3700,3710,8),(3900,3910,8),(4200,4210,8)],ram_writes=writes,sram_out=sram,core_options={'genesis_plus_gx_region_detect':region})
   raw=sram.read_bytes();srams[tag]=(raw[1::2] if tag=='md' else raw).ljust(8192,b'\xff')
   cold=ROOT/f'validation/quest-gift-cold-{name}-{tag}'
   with contextlib.redirect_stdout(io.StringIO()):
    run(path,1920,cold,{1920},([(200,220,0)] if tag=='sms' else [])+[(920,935,0),(1000,1005,5),(1050,1065,8),(1300,1310,8)],sram_in=sram,core_options={'genesis_plus_gx_region_detect':region})
   r=(cold/'ram_01920.bin').read_bytes() if tag=='sms' else native(cold,1920)
   if tag=='sms':actual=dict(flags=r[0x100:0x200],items=r[0xe0:0xf1],armor=r[0xf1],shield=r[0xf2],curse=r[0xbf],capacity=r[0xda],story=r[0xd4])
   else:
    value=lambda k:int.from_bytes(r[sy[k]:sy[k]+2],'big')
    actual=dict(flags=r[sy['game_save_state']+0x50:sy['game_save_state']+0x150],items=bytes([value('hero_basic_level'),value('hero_weapon_level')])+r[sy['hero_items']+2:sy['hero_items']+17],armor=value('hero_armor_level'),shield=value('hero_shield_level'),curse=r[sy['game_save_state']+15],capacity=value('hero_max_health'),story=r[sy['game_save_state']+0x24])
   expected=dict(flags=flags,items=items,armor=armor,shield=shield,curse=curse,capacity=capacity,story=story)
   assert actual==expected,(name,tag,'cold gift state',actual,expected)
   cold_fields[tag]=dict(gift_town_flag=actual['flags'][town],inventory=actual['items'].hex(),armor=actual['armor'],shield=actual['shield'],curse=actual['curse'])
  assert srams['sms'][0x400:0x650]==srams['md'][0x400:0x650],(name,'complete592-byte payload')
  results.append(dict(town=town,region=region,item=case['item'],slot=1,save_payload_bytes_exact=592,cold_flags_bytes_exact=256,cold_inventory_bytes_exact=17,cold_fields=cold_fields))
  print(name,'actual quest gift saved and cold-loaded',flush=True)
 report=dict(md_sha256=digest,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),cases=results,full_game_ported=False,limits=[
  'State comes from current ROM controller-triggered gift snapshots. All256 room flags,17 item bytes,equipment,curse,maximum health and dungeon6 story flag compare before transfer. No fabricated grant or persistence flag.',
  'Fixture transfers that state to the established save-point route at3340;actual save-slot1 menus,SRAM write,fresh core boot and Continue execute unpatched in each video region. Full592-byte SMS/native payloads and loaded gift fields compare.',
  'Uninterrupted gift-to-save-point walking route,all save slots,post-cold-load house revisit and complete natural progression are not asserted by this validator.'])
 (ROOT/'validation/quest_gift_save_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
