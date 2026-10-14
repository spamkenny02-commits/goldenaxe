"""Audit save-node coverage without claiming complete world/combat fidelity."""
import hashlib,json
from pathlib import Path
from actor_reference import ROOT

def main():
 def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 data=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(ROOT/'gaw-megadrive.bin')
 assert len(data)==524288 and int.from_bytes(data[0x1a4:0x1a8],'big')==len(data)-1
 for p in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert sha(ROOT/p)==digest
 assert sha(ROOT/'input/original.sms')==sha(Path(r'D:/Cartmod/GoldenAxeWarrior/chat/Golden Axe Warrior (USA, Europe).sms'))=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
 reports=[]
 for name in ['all_save_points','save','house_dialogue','all_merchants','paid_healer','village_doors']:
  p=ROOT/f'validation/{name}_report.json';d=json.loads(p.read_text());assert d['md_sha256']==digest,(name,'stale report');reports.append(p.name)
 saved=json.loads((ROOT/'validation/all_save_points_report.json').read_text())
 assert len(saved['cases'])==17 and len({c['town'] for c in saved['cases']})==14
 assert {c['house'] for c in saved['cases']}=={0,1,4,0x6f}
 assert all(c['payload_bytes_source_exact']==592 and c['ui_pixels_source_exact'] for c in saved['cases'])
 combat=json.loads((ROOT/'analysis/checkpoint_52_combat_difference.json').read_text());assert combat['md_sha256']==digest
 source=next(c for c in combat['rows'] if c['system']=='sms' and c['frame']==1900)
 native=next(c for c in combat['rows'] if c['system']=='md' and c['frame']==1900)
 assert source['hp']==0 and native['hp']==9
 previous=json.loads((ROOT/'validation/all_merchants_patch_audit.json').read_text())
 old=json.loads((ROOT/'validation/full_milestone_audit.json').read_text())
 check=bytearray(data);check[0x18e:0x190]=bytes(2);folded=0
 for n in range(0,len(check),4):folded^=int.from_bytes(check[n:n+4],'big')
 assert int.from_bytes(data[0x18e:0x190],'big')==(folded^(folded>>16))&65535
 audit=dict(md_sha256=digest,md_size=len(data),original_unchanged=True,rom_aliases_exact=True,current_targeted_reports=reports,save_locations=14,save_cases=17,save_nodes=4,prior_targeted_md_sha256=previous['md_sha256'],prior_full_regression_md_sha256=old['md_sha256'],full_regression_rerun_for_this_patch=False,full_game_ported=False,known_limits=['Checkpoint tests clear actors to isolate saved-state restoration','Room52 source combat kills the wounded hero; native actor29/2B behaviors remain absent','Upper SRAM writes outside canonical slot records not reproduced or explained','Other village informative dialogues incomplete','Natural world access, quests, dungeons, graphics classes, effects and original RNG incomplete','Absolute timing and standard additive Mega Drive checksum remain incomplete'])
 (ROOT/'validation/all_save_patch_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
