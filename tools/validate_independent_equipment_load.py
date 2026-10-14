"""Cold Continue must preserve distinct primary weapon/armor and saved curse."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))};cases=[]
 for region in ['auto','pal']:
  for basic,armor,curse in [(1,2,1),(3,1,0),(2,3,1)]:
   records={};payloads={}
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    original=(ROOT/f'validation/{tag}-save-slot-0.srm').read_bytes();logical=bytearray((original[1::2] if tag=='md' else original).ljust(8192,b'\xff'))
    logical[0x30]=1;logical[0x430]=basic;logical[0x441]=armor;logical[0x40f]=curse;logical[0x42f]=0
    payloads[tag]=bytes(logical[0x400:0x650])
    if tag=='md':physical=bytearray([255])*16384;physical[1::2]=logical
    else:physical=logical
    path=ROOT/f'validation/equipment-{basic}-{armor}-{curse}-{region}-{tag}.srm';path.write_bytes(physical);rows={}
    def observe(f,r):
     if not 1900<=f<=1920:return
     if tag=='sms':rows[f]=bytes([r[0xe0],r[0xf1],r[0xbf],r[0xf2],r[0x319],r[0x31a]])+bytes(r[0xe0:0xf1])
     else:
      data=lambda k,n:bytes(r[(sy[k]+i)^1] for i in range(n));w=lambda k:int.from_bytes(data(k,2),'big')
      rows[f]=bytes([w('hero_basic_level'),w('hero_armor_level'),data('game_save_state',16)[15],w('hero_shield_level'),w('hero_attack'),w('hero_defense')])+data('hero_items',17)
    with contextlib.redirect_stdout(io.StringIO()):run(rom,2000,ROOT/f'validation/equipment-load-{basic}-{armor}-{curse}-{region}-{tag}',set(),([(200,220,0)] if tag=='sms' else [])+[(920,935,0),(1000,1005,5),(1050,1065,8),(1300,1310,8)],sram_in=path,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    assert len(rows)==21;records[tag]=rows
   assert payloads['sms']==payloads['md'],'Equipment fixture source/native payloads differ'
   assert records['sms']==records['md'],(region,basic,armor,curse,[(f,records['sms'][f].hex(),records['md'][f].hex()) for f in records['sms'] if records['sms'][f]!=records['md'][f]][:3])
   assert all(r[:3]==bytes([basic,armor,curse]) for r in records['md'].values())
   cases.append(dict(region=region,basic=basic,armor=armor,curse=curse,loaded_equipment_curse_attack_defense_and_inventory_frames_exact=21,sram_payload_sha256=hashlib.sha256(payloads['sms']).hexdigest(),normal_cold_Continue=True));print(region,basic,armor,curse,'independent equipment cold-load exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=cases,full_game_ported=False,limits=['Identical logical592-byte existing valid save payloads with controlled primary/armor/curse/selected fields. Normal cold-boot Continue reads real native/source SRAM.','Checks126 loaded frames across six cases, including attack strength and curse-dependent defense. This does not test natural quest-to-save writing or all progression fields.'])
 (ROOT/'validation/independent_equipment_load_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
