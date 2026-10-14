"""Inspect sound requests/active effects in current gameplay regression captures."""
import hashlib,json,re
from actor_reference import ROOT
from validate_house_dialogue import native

def main():
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 rows=[]
 for name,pattern,command in [('hero_hurt','damage-detail',0x91),('shield','shield-detail',0x98),('pickup','loot-8',0x96),('enemy_hurt','enemy-hit-0-8-0-*',0x9c),('enemy_killed','enemy-hit-0-2-0-*',0xa0),('dialogue','house-dialogue-0',0x9f),('shop','merchant-*',0x95)]:
  found=[]
  for md in sorted((ROOT/'validation').glob('md-'+pattern)):
   metadata=md/'capture.json'
   if not metadata.exists():continue
   capture=json.loads(metadata.read_text())
   if capture['rom_sha256']!=digest:continue
   sms=md.with_name('sms-'+md.name[3:])
   for f in sorted(map(int,capture['captures'])):
    source=sms/f'ram_{f:05}.bin'
    if not source.exists():continue
    a=source.read_bytes();b=native(md,f);off=sy['sound_ram']
    sv={a[0x1e06],a[0x1e07],a[0x1e08],a[0x1e0f]}
    tv={b[off+6],b[off+7],b[off+8],b[off+15]}
    for var in ['sound_request','sound_effect_request']:tv.add(int.from_bytes(b[sy[var]:sy[var]+2],'big'))
    if command in sv and command in tv:found.append(dict(directory=md.name,frame=f));break
  assert found,(name,hex(command),'missing source/native sound event in current captures')
  rows.append(dict(event=name,command=command,evidence=found));print(f'{name}: {command:02X} source/native event observed',flush=True)
 report=dict(md_sha256=digest,events=rows,scope='Sound queue/active command in seven current gameplay regression capture sets; not waveform or full event timing equivalence',all_game_event_hooks_verified=False)
 (ROOT/'validation/sfx_event_records_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
