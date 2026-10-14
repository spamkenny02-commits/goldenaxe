"""Check production scope and the three literal resource slices."""
import difflib,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 src=ROOT/'megadrive/src';old=(ROOT/'analysis/first-boss-baseline-v0108/actors.c').read_text();new=(src/'actors.c').read_text();s=new
 start=s.index('extern const u8 first_boss_movement[]');end=s.index('static u8 *create_guarded_projectile_type',start);s=s[:start]+s[end:]
 for begin,end in [('static void projectile_behavior','static u16 attacking_hero_x'),('            else if((entity[0]>=0x10','            else if(entity[0]==7)'),('        /* 0940 follows 26B6','    }\n}\n\n/* 393A')]:
  a=s.index(begin);b=s.index(end,a);x=old.index(begin);y=old.index(end,x);s=s[:a]+old[x:y]+s[b:]
 assert s==old,'Unrelated actor implementation changed'
 previous=json.loads((ROOT/'versions/v0108-3e9ced37/boss_death_patch_audit.json').read_text())
 assert sha(src/'main.c')==previous['production_source_files']['main.c']
 rom=(ROOT/'input/original.sms').read_bytes();resources=(src/'first_boss_data.c').read_text()
 for name,start,size in [('first_boss_movement',0x87cd,17),('first_boss_aimed',0x4405,38),('first_boss_fan',0x443d,26)]:
  values=re.search(name+r'\[\]=\{([^}]+)',resources)[1]
  assert bytes(int(v,0) for v in values.split(','))==rom[start:start+size]
 (ROOT/'analysis/first_boss_patch.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='v0108/actors.c',tofile='v0110/actors.c')))
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),source_files={n:sha(src/n) for n in ['main.c','actors.c','first_boss_data.c']},only_first_boss_behavior_projectile_dispatch_and_collision_publication_changed=True,literal_resources_exact=True,original_random_stream_reproduced=False,full_game_ported=False)
 (ROOT/'validation/first_boss_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('First-boss production scope and literal resources verified')
if __name__=='__main__':main()
