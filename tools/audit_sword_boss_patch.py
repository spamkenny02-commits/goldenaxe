"""Verify type6C/projectile changes and the large actor descriptor fix."""
import difflib,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 src=ROOT/'megadrive/src';old=(ROOT/'analysis/sword-boss-baseline-v0114/actors.c').read_text();new=(src/'actors.c').read_text();s=new
 a=s.index('extern const u8 sword_boss_walk[]');b=s.index('extern const u8 actor_homing_template[]',a);s=s[:a]+s[b:]
 a=s.index('            else if(entity[0]==0x6c)');b=s.index('            else if(entity[0]==7)',a);s=s[:a]+s[b:]
 old_condition=next(l for l in old.splitlines() if 'if((entity[0]==0x0f' in l);new_condition=next(l for l in s.splitlines() if 'if((entity[0]==0x0f' in l)
 s=s.replace(new_condition,old_condition)
 s=s.replace('        /* 09EE emits the complete descriptor; large bosses exceed16 parts. */\n        if(!count || index+count>64) break;','        if(!count || count>16 || index+count>64) break;')
 assert s==old,'Unrelated actor implementation changed'
 previous=json.loads((ROOT/'versions/v0114-fa929315/burst_boss_patch_audit.json').read_text())
 for n in ['main.c','burst_boss_data.c']:assert sha(src/n)==previous['source_files'][n]
 rom=(ROOT/'input/original.sms').read_bytes();resources=(src/'sword_boss_data.c').read_text()
 for name,start,size in [('sword_boss_walk',0x55d0,33),('sword_boss_shot',0x468e,38),('sword_boss_paths',0x4745,0xb2)]:
  values=re.search(name+r'\[\]=\{([^}]+)',resources)[1];assert bytes(int(v,0) for v in values.split(','))==rom[start:start+size]
 (ROOT/'analysis/sword_boss_patch.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='v0114/actors.c',tofile='v0116/actors.c')))
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),source_files={n:sha(src/n) for n in ['main.c','actors.c','sword_boss_data.c']},only_sword_boss_projectile_satellite_dispatch_collision_publication_and_large_descriptor_limit_changed=True,main_and_burst_resources_unchanged=True,literal_resources_exact=True,original_random_stream_reproduced=False,full_game_ported=False)
 (ROOT/'validation/sword_boss_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Sword boss scope/literals verified, including removal of unsupported16-part renderer cap')
if __name__=='__main__':main()
