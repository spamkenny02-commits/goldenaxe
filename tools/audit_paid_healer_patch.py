"""Bind targeted inn comparisons to the delivered ROM; keep full audit history."""
import hashlib,json
from pathlib import Path
from actor_reference import ROOT

def main():
 def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 rom=ROOT/'gaw-megadrive.bin';digest=sha(rom);data=rom.read_bytes()
 assert len(data)==524288 and int.from_bytes(data[0x1a4:0x1a8],'big')==len(data)-1
 for p in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert sha(ROOT/p)==digest
 original=Path(r'D:/Cartmod/GoldenAxeWarrior/chat/Golden Axe Warrior (USA, Europe).sms')
 assert sha(original)==sha(ROOT/'input/original.sms')=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
 reports=[]
 for name in ['paid_healer','healer','healer_natural','merchant','save','house_dialogue','village_doors']:
  p=ROOT/f'validation/{name}_report.json';d=json.loads(p.read_text());assert d['md_sha256']==digest,(name,'stale');reports.append(p.name)
 paid=json.loads((ROOT/'validation/paid_healer_report.json').read_text())
 assert len(paid['cases'])==14 and paid['all_eleven_price_table_towns_checked']
 old=json.loads((ROOT/'validation/full_milestone_audit.json').read_text())
 check=bytearray(data);check[0x18e:0x190]=bytes(2);folded=0
 for n in range(0,len(check),4):folded^=int.from_bytes(check[n:n+4],'big')
 assert int.from_bytes(data[0x18e:0x190],'big')==(folded^(folded>>16))&65535
 result=dict(md_sha256=digest,md_size=len(data),original_unchanged=True,rom_aliases_exact=True,current_targeted_reports=reports,inn_cases=14,inn_towns=11,prior_full_regression_md_sha256=old['md_sha256'],full_regression_rerun_for_this_patch=False,full_game_ported=False,known_limits=['Other village merchants and informative dialogues remain incomplete','World access to all inns not validated by natural routes','Absolute transition and transaction timing incomplete','Quests, dungeons, other graphics classes, effects and original RNG remain incomplete','Checksum is SGDK folded XOR; standard additive checksum still pending'])
 (ROOT/'validation/paid_healer_patch_audit.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
