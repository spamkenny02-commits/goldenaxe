"""Bind the paced production converter and its targeted release evidence."""
import hashlib,json,re,subprocess
from actor_reference import ROOT

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def body(text,name):
 start=text.index('static void '+name+'(');a=text.index('{',start);depth=1;n=a+1
 while depth:
  depth+=(text[n]=='{')-(text[n]=='}');n+=1
 return text[a:n]

def main():
 baseline=subprocess.run(['git','rev-parse','458dc5a'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
 old=subprocess.run(['git','show',baseline+':megadrive/src/main.c'],cwd=ROOT,capture_output=True,text=True,check=True).stdout
 current=(ROOT/'megadrive/src/main.c').read_text();intro=(ROOT/'megadrive/src/intro.inc').read_text()
 assert body(current,'convert_patterns_range')==body(old,'convert_patterns_range')
 assert current.count('convert_patterns_range_fast(')==6 and intro.count('convert_patterns_range_fast(')==2
 assert body(current,'title_sequence').count('convert_patterns_range_fast(')==1
 assert body(current,'show_inventory').count('convert_patterns_range_fast(')==4
 assert 'convert_patterns(512)' in body(current,'load_house_room') and 'convert_patterns_range_fast' not in body(current,'load_house_room')
 assert 'convert_patterns_range_fast' not in body(current,'enter_initial_room')
 assert 'wait_frame();memcpy(sms_palette,next_palette' in body(current,'fade_title_palette')
 assert body(current,'show_inventory').count('while(vtimer-menu_started<frames-2)')==2
 unchanged=[]
 files=subprocess.run(['git','ls-tree','-r','--name-only',baseline,'megadrive/src'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()
 for name in files:
  if name in ['megadrive/src/main.c','megadrive/src/intro.inc']:continue
  raw=subprocess.run(['git','show',baseline+':'+name],cwd=ROOT,capture_output=True,check=True).stdout
  assert raw==(ROOT/name).read_bytes(),('Unreviewed source change',name)
  unchanged.append(dict(file=name,sha256=hashlib.sha256(raw).hexdigest()))
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();sha=hashlib.sha256(rom).hexdigest()
 assert rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 assert len(rom)==1048576 and (sum(int.from_bytes(rom[n:n+2],'big') for n in range(512,len(rom),2))&65535)==int.from_bytes(rom[0x18e:0x190],'big')
 names=['pattern_pairs_report','menu_transition_report','inventory_restore_report','natural_start_menu_sfx_report','intro_report','intro-pal_report','title_cadence_report','title_cadence-pal_report','title_cadence-natural_report','title_cadence-pal-natural_report','standard_door_transitions_report'];reports=[]
 for name in names:
  path=ROOT/'validation'/(name+'.json');data=json.loads(path.read_text());assert data['md_sha256']==sha,(name,'stale ROM')
  reports.append(dict(file=path.relative_to(ROOT).as_posix(),sha256=digest(path)))
 unit=json.loads((ROOT/'validation/pattern_pairs_report.json').read_text())
 assert unit['exhaustive_pairs']==65536 and unit['each_half_independently'] and unit['host_pixel_parity']
 assert all(not r['failures'] and r['new_frames']<r['old_frames'] for r in unit['compiled'])
 changed=['megadrive/src/main.c','megadrive/src/intro.inc','megadrive/src/pattern_convert.c','megadrive/src/pattern_convert.h','megadrive/src/pattern_pair_lut.inc','build.ps1','tools/generate_pattern_pairs.py','tools/validate_pattern_pairs.py','tools/validate_title_cadence.py','tools/audit_pattern_pairs.py']
 result=dict(md_sha256=sha,baseline_commit=baseline,source_files={n:digest(ROOT/n) for n in changed},unchanged_native_files=unchanged,reports=reports,fast_conversion_scope=['intro','title','inventory'],unpaced_loaders_keep_old_converter=True,pal_menu_publication_corrected=True,title_palette_vblank_publication=True,full_game_ported=False,global_source_clock_wired=False,limits=['Targeted pixel,cadence and route checks only. Absolute boot phase,all intro sprite phases,all inventory ownerships/dungeon menus,full door loading timing and complete natural progression remain unverified.','CPU conversion benchmark is not a gameplay FPS improvement claim.'])
 (ROOT/'validation/pattern_pairs_patch_audit.json').write_text(json.dumps(result,indent=2)+'\n');print('Production scope,checksum and11 report bindings verified.')
if __name__=='__main__':main()
