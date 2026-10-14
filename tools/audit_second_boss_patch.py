"""Check native change scope and source literal resources."""
import difflib,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 src=ROOT/'megadrive/src';old=(ROOT/'analysis/second-boss-baseline-v0110/actors.c').read_text();new=(src/'actors.c').read_text();s=new
 a=s.index('extern const u8 second_boss_turns[]');b=s.index('/* 9730..983E:',a);s=s[:a]+s[b:]
 a=s.index('            else if(entity[0]==0x65)');b=s.index('            else if(entity[0]==7)',a);s=s[:a]+s[b:]
 s=s.replace(' || entity[0]==0x65 || entity[0]==0x66','')
 assert s==old,'Unrelated actor implementation changed'
 previous=json.loads((ROOT/'versions/v0110-c64afe1e/first_boss_patch_audit.json').read_text())
 for n in ['main.c','first_boss_data.c']:assert sha(src/n)==previous['source_files'][n]
 rom=(ROOT/'input/original.sms').read_bytes();resources=(src/'second_boss_data.c').read_text()
 for name,start,size in [('second_boss_turns',0x4efb,32),('second_boss_fast',0x4f1b,41),('second_boss_slow',0xa949,41)]:
  values=re.search(name+r'\[\]=\{([^}]+)',resources)[1]
  assert bytes(int(v,0) for v in values.split(','))==rom[start:start+size]
 (ROOT/'analysis/second_boss_patch.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='v0110/actors.c',tofile='v0111/actors.c')))
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),source_files={n:sha(src/n) for n in ['main.c','actors.c','second_boss_data.c']},only_type65_type66_behavior_dispatch_and_collision_publication_changed=True,main_and_first_boss_resources_unchanged=True,literal_resources_exact=True,original_random_stream_reproduced=False,full_game_ported=False)
 (ROOT/'validation/second_boss_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Second-boss production scope and literal resources verified')
if __name__=='__main__':main()
