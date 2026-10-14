"""Bind standard-door changes and regression evidence to the released ROM."""
import hashlib,json,difflib
from actor_reference import ROOT

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
 prior=ROOT/'versions/v0178-a8d8ee11/source';current=ROOT/'megadrive/src'
 changed=[];unchanged=[];diffs=[]
 for p in current.iterdir():
  if not p.is_file():continue
  old=prior/p.name
  if not old.exists():assert p.name=='door_transition.inc';changed.append(p.name);continue
  if old.read_bytes()==p.read_bytes():unchanged.append(p.name);continue
  assert p.name in ['main.c','paid_passage.inc'],p.name
  changed.append(p.name);diffs.extend(difflib.unified_diff(old.read_text().splitlines(True),p.read_text().splitlines(True),fromfile='v0178/'+p.name,tofile='v0179/'+p.name))
 assert set(changed)=={'main.c','paid_passage.inc','door_transition.inc'}
 main_text=(current/'main.c').read_text()
 assert main_text.count('load_door_room(')==5 # declaration + four standard doors
 assert 'if(!door_transition_loading) VDP_setEnable(TRUE)' in main_text
 door=(current/'door_transition.inc').read_text()
 assert door.index('fade_world_palette(black,FALSE)')<door.index('load_house_room(')<door.index('update_world_music()')<door.index('reveal_world()')
 assert 'world_clock_shift+=vtimer-started-1' in door
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(rom)
 assert len(rom)==1048576 and int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
 checksum=sum(int.from_bytes(rom[n:n+2],'big') for n in range(0x200,len(rom),2))&65535
 assert checksum==int.from_bytes(rom[0x18e:0x190],'big')
 for path in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert (ROOT/path).read_bytes()==rom
 evidence={}
 for name,count in [('standard_door_transitions_report.json',4),('dungeon_doors_report.json',10),('dungeon_doors-pal_report.json',10),('house_quest_persistence_gameplay_report.json',16),('house_quest_revisit_gameplay_report.json',12),('paid_passage_gameplay_report.json',20),('paid_exit_music_report.json',24),('paid_passage_native_loading_clock_report.json',3072),('save_report.json',3)]:
  p=ROOT/'validation'/name;r=json.loads(p.read_text());assert r['md_sha256']==digest,(name,'stale ROM')
  assert (len(r['cases']) if isinstance(r['cases'],list) else r['cases'])==count,(name,count)
  evidence[name]=sha(p.read_bytes())
 baseline=ROOT/'analysis/standard-door-baseline-v0178/analysis/standard_door_music_report.json'
 b=json.loads(baseline.read_text());assert b['md_sha256']==sha((ROOT/'versions/v0178-a8d8ee11/gaw-megadrive-v0178.bin').read_bytes())
 assert all(not any(x['command']==0xb0 for x in r['music_sequences']['md']) for r in b['cases'])
 report=dict(md_sha256=digest,bytes=len(rom),checksum=f'{checksum:04X}',changed_production_files=changed,unchanged_production_files=unchanged,production_diff=''.join(diffs),current_evidence=evidence,baseline_sha256=sha(baseline.read_bytes()),full_game_ported=False,limits=['Standard doors now fade out,hide loading,request B0 and destination music,restore foreground palette and reveal through existing source-derived contours. Paid loading also remains hidden until reveal.','Targeted controlled gameplay and three-slot save/Continue regressions only. Remaining load duration,pending-VBlank phase boundaries,RNG/combat differences,intermediate pixel/audio equality and full natural playthrough remain open.'])
 (ROOT/'validation/standard_door_patch_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Standard-door patch and current regression reports audited:',digest[:8],f'{checksum:04X}')

if __name__=='__main__':main()
