"""Bind all merchant variants and affected regression reports to this ROM."""
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
 for name in ['all_merchants','merchant','paid_healer','healer','healer_natural','save','house_dialogue','village_doors','inventory']:
  p=ROOT/f'validation/{name}_report.json';d=json.loads(p.read_text());assert d['md_sha256']==digest,(name,'stale report');reports.append(p.name)
 merchant=json.loads((ROOT/'validation/all_merchants_report.json').read_text());cases=merchant['cases']
 assert len(cases)==43 and merchant['all_23_towns_checked']
 assert len({c['town'] for c in cases})==23 and {c['mode'] for c in cases}=={0,1,2}
 assert all(c['currency_intervals_source_exact'] and c['initial_panel_pixels_exact'] and c['settled_states_source_exact']==2 for c in cases)
 check=bytearray(data);check[0x18e:0x190]=bytes(2);folded=0
 for n in range(0,len(check),4):folded^=int.from_bytes(check[n:n+4],'big')
 assert int.from_bytes(data[0x18e:0x190],'big')==(folded^(folded>>16))&65535
 previous=json.loads((ROOT/'validation/paid_healer_patch_audit.json').read_text())
 old=json.loads((ROOT/'validation/full_milestone_audit.json').read_text())
 audit=dict(md_sha256=digest,md_size=len(data),original_unchanged=True,rom_aliases_exact=True,sgdk_folded_xor_checksum_correct=True,current_targeted_reports=reports,merchant_towns=23,merchant_cases=43,compared_currency_decrements=sum(c['currency_decrements'] for c in cases),prior_targeted_md_sha256=previous['md_sha256'],prior_full_regression_md_sha256=old['md_sha256'],full_regression_rerun_for_this_patch=False,full_game_ported=False,known_limits=['Natural world access to all services unverified','Other village informative dialogues and save selectors incomplete','Absolute dialog, sprite and transition timing incomplete','Quests, dungeons, other graphics classes, effects and original RNG incomplete','Standard additive Mega Drive checksum still pending'])
 (ROOT/'validation/all_merchants_patch_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
