"""Production scope and three source formation tables."""
import difflib,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 src=ROOT/'megadrive/src';old=(ROOT/'analysis/composite-boss-baseline-v0111/actors.c').read_text();new=(src/'actors.c').read_text();s=new
 a=s.index('extern const u8 composite_boss_positions[]');b=s.index('/* 506B ->',a);s=s[:a]+s[b:]
 a=s.index('            else if(entity[0]==0x67)');b=s.index('            else if(entity[0]==7)',a);s=s[:a]+s[b:]
 s=s.replace(' || entity[0]==0x67','');assert s==old,'Unrelated actor implementation changed'
 previous=json.loads((ROOT/'versions/v0111-26d75abb/second_boss_patch_audit.json').read_text())
 for n in ['main.c','second_boss_data.c']:assert sha(src/n)==previous['source_files'][n]
 rom=(ROOT/'input/original.sms').read_bytes();expected=bytearray()
 for n in range(3):
  a=int.from_bytes(rom[0xab1c+n*2:0xab1e+n*2],'little');expected.extend(rom[a:a+10])
 values=re.search(r'\[\]=\{([^}]+)',(src/'composite_boss_data.c').read_text())[1]
 assert bytes(int(v,0) for v in values.split(','))==expected
 (ROOT/'analysis/composite_boss_patch.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='v0111/actors.c',tofile='v0112/actors.c')))
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),source_files={n:sha(src/n) for n in ['main.c','actors.c','composite_boss_data.c']},only_type67_behavior_dispatch_and_collision_publication_changed=True,main_and_second_boss_resources_unchanged=True,formation_resources_exact=True,original_random_stream_reproduced=False,full_game_ported=False)
 (ROOT/'validation/composite_boss_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Composite-boss production scope and formations verified')
if __name__=='__main__':main()
