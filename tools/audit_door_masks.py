"""Audit original/native persisted actor masks in the full direct-door capture set."""
import hashlib,json,re
from actor_reference import ROOT
from validate_house_dialogue import native
def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
 rows=json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_doors'];checks=[]
 report=json.loads((ROOT/'validation/expanded_doors_report.json').read_text());assert report['md_sha256']==digest and report['all_direct_prefix_doors_checked']
 for index,row in enumerate(rows):
  a=ROOT/f'validation/sms-expanded-door-{index}';b=ROOT/f'validation/md-expanded-door-{index}'
  assert json.loads((b/'capture.json').read_text())['rom_sha256']==digest
  for frame,room in [(2300,row['room']),(2800,row['target'])]:
   source=(a/f'ram_{frame:05}.bin').read_bytes()[0x200+room]
   target=native(b,frame)[sy['game_save_state']+0x150+room]
   assert target==source,(index,frame,hex(room),'actor mask',target,source)
   checks.append(dict(door=index,frame=frame,room=room,mask=source))
 patterns=[]
 for mask in [0x80,0x01,0x55,0xaa]:
  p=ROOT/f'validation/door_living_mask_{mask:02x}_report.json';d=json.loads(p.read_text());assert d['md_sha256']==digest
  assert d['cases'][0]['persisted_mask_source_exact']==mask;patterns.append(mask)
 (ROOT/'validation/door_masks_report.json').write_text(json.dumps(dict(md_sha256=digest,persisted_actor_masks_source_exact=len(checks),cases=checks,living_mask_patterns_source_exact=patterns,all_eight_live_actors_game_fixture_verified=False),indent=2)+'\n')
 print('Persisted masks match SMS:',len(checks))
if __name__=='__main__':main()
