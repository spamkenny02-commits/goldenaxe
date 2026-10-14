"""Bounded merchant patch audit; preserve the earlier complete regression identity."""
import hashlib,json
from pathlib import Path
from actor_reference import ROOT

def main():
 def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 data=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(ROOT/'gaw-megadrive.bin')
 assert len(data)==524288 and int.from_bytes(data[0x1a4:0x1a8],'big')==len(data)-1
 assert all(sha(ROOT/p)==digest for p in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin'])
 source=sha(ROOT/'input/original.sms')
 assert source==sha(Path(r'D:/Cartmod/GoldenAxeWarrior/chat/Golden Axe Warrior (USA, Europe).sms'))=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
 names=['merchant','save','inventory','village_doors','house_dialogue'];reports=[]
 for name in names:
  p=ROOT/f'validation/{name}_report.json';d=json.loads(p.read_text());assert d['md_sha256']==digest,(name,'stale report');reports.append(p.name)
 merchant=json.loads((ROOT/'validation/merchant_report.json').read_text())
 assert len(merchant['cases'])==7 and merchant['natural_walk_refusal_exit_without_ram_injection']
 previous=json.loads((ROOT/'validation/save_milestone_audit.json').read_text())
 check=bytearray(data);check[0x18e:0x190]=bytes(2);folded=0
 for n in range(0,len(check),4):folded^=int.from_bytes(check[n:n+4],'big')
 folded=(folded^(folded>>16))&65535;assert int.from_bytes(data[0x18e:0x190],'big')==folded
 audit=dict(md_sha256=digest,md_size=len(data),original_unchanged=True,rom_aliases_exact=True,sgdk_folded_xor_checksum_correct=True,current_targeted_reports=reports,prior_full_regression_md_sha256=previous['md_sha256'],full_regression_rerun_for_this_patch=False,first_village_merchant_purchases_and_refusals_verified=True,full_game_ported=False,known_limits=['Other merchant and healer services absent','Original sound effects absent','Absolute transaction and transition timing incomplete','Persistent progression and original RNG remain incomplete','Standard additive Mega Drive checksum remains to normalize'])
 (ROOT/'validation/merchant_patch_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
