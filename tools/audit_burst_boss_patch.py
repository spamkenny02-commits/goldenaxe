"""Verify the production diff and projectile literals for milestone114."""
import difflib,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 src=ROOT/'megadrive/src';old=(ROOT/'analysis/burst-boss-baseline-v0113/actors.c').read_text();new=(src/'actors.c').read_text();s=new
 a=s.index('/* 57F8 with BC=0004');b=s.index('extern const u8 composite_boss_positions[]',a);s=s[:a]+s[b:]
 a=s.index('extern const u8 burst_boss_shot_template[]');b=s.index('static u16 attacking_hero_x',a);s=s[:a]+s[b:]
 a=s.index('            else if(entity[0]==0x6a ||');b=s.index('            else if(entity[0]==7)',a);s=s[:a]+s[b:]
 old_condition=next(l for l in old.splitlines() if 'if((entity[0]==0x0f' in l);new_condition=next(l for l in s.splitlines() if 'if((entity[0]==0x0f' in l)
 s=s.replace(new_condition,old_condition);assert s==old,'Unrelated actor implementation changed'
 previous=json.loads((ROOT/'versions/v0113-58543772/charging_boss_patch_audit.json').read_text())
 for n in ['main.c','charging_boss_data.c']:assert sha(src/n)==previous['source_files'][n]
 rom=(ROOT/'input/original.sms').read_bytes();resources=(src/'burst_boss_data.c').read_text()
 for name,start,size in [('burst_boss_shot_template',0x44f2,38),('burst_boss_shot_facing',0x44ea,8)]:
  values=re.search(name+r'\[\]=\{([^}]+)',resources)[1];assert bytes(int(v,0) for v in values.split(','))==rom[start:start+size]
 (ROOT/'analysis/burst_boss_patch.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='v0113/actors.c',tofile='v0114/actors.c')))
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),source_files={n:sha(src/n) for n in ['main.c','actors.c','burst_boss_data.c']},only_burst_boss_projectile_behavior_dispatch_and_collision_publication_changed=True,main_and_charging_resources_unchanged=True,literal_resources_exact=True,original_random_stream_reproduced=False,full_game_ported=False)
 (ROOT/'validation/burst_boss_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Burst boss scope and original projectile literals verified')
if __name__=='__main__':main()
