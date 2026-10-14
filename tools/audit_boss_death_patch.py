"""Limit the production change to boss death and gem collision publication."""
import hashlib,json,difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'analysis/boss-death-baseline-v0105';src=ROOT/'megadrive/src';diff=[]
 for name in ['main.c','actors.c']:
  old=(base/name).read_text();new=(src/name).read_text();s=new
  if name=='main.c':
   start=s.index('/* 4BF5..4C3E:');end=s.index('/* 2A6B..2ACC:',start);s=s[:start]+s[end:]
   s=s.replace('\nstatic bool boss_death_music_hold;','').replace('    boss_death_music_hold=FALSE;\n','').replace('sound_effect(0x96);boss_death_music_hold=FALSE;','sound_effect(0x96);').replace('if(!boss_death_music_hold) update_world_music();','update_world_music();')
  else:
   s=s.replace('extern void tick_world_gem(u8 *entity),tick_world_boss_death(u8 *entity);','extern void tick_world_gem(u8 *entity);')
   s=s.replace('            else if(entity[0]==7) tick_world_boss_death(entity);\n','')
   start=s.index('        /* 0940 follows 26B6:') if '        /* 0940 follows 26B6:' in s else s.index('        /* 0940 follows 26B6 in')
   end=s.index('    }\n}\n\n/* 393A',start);s=s[:start]+s[end:]
  assert s==old,name
  diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='v0105/'+name,tofile='v0108/'+name))
 old_resources=json.loads((ROOT/'versions/v0105-5dbebb15/gem_patch_audit.json').read_text())['source_files']
 assert sha(src/'gem_data.c')==old_resources['gem_data.c']
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),production_source_files={n:sha(src/n) for n in ['main.c','actors.c']},only_boss_death_helpers_dispatch_music_retention_and_gem_collision_publication_changed=True,boss_music_hold_cleared_on_room_loading_and_collection=True,gem_resource_data_unchanged=True,original_random_stream_reproduced=False,ending_sequence_implemented=False,full_game_ported=False)
 (ROOT/'analysis/boss_death_patch.diff').write_text(''.join(diff));(ROOT/'validation/boss_death_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Boss death patch scope verified')
if __name__=='__main__':main()
