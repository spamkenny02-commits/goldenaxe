"""Bind natural axe acquisition, equip/first crystal, and later dungeon-two attempts."""
import gzip,json
from run_core import ROOT
from archive_lossless_evidence import sha
from validate_playable_sprite_limit import symbols
BASE=ROOT/'validation/natural-dungeon-combat'
def read(p):
 if p.exists():return p.read_bytes()
 out=ROOT/'analysis/natural-axe-campaign-v0274';m=json.loads((out/'manifest.json').read_bytes());n=p.relative_to(ROOT).as_posix()
 if n in m['files']:
  r=(out/n).read_bytes();assert sha(r)==m['files'][n];return r
 i=m['compressed'][n];r=(out/i['stored']).read_bytes();assert sha(r)==i['stored_sha256'];r=gzip.decompress(r);assert sha(r)==i['raw_sha256'];return r

def main():
 sy=symbols(ROOT/'megadrive/out/release/symbol.txt');evidence={};cases=[];endpoints=[]
 def load(p):
  r=read(p);evidence[p.relative_to(ROOT).as_posix()]=sha(r);return json.loads(r)
 def trace(name):
  folder=BASE/name;c=load(folder/'capture.json');r=load(folder/'report.json');load(folder/'controls.json');assert c['rom_sha256']==r['rom_sha256'] and not c['test_ram_writes'] and c['sram_input'] is None;return folder,c,r
 for tag in ['sms','md']:
  acq,ac,ar=trace(tag+'-auto-v0274-axe01');boss,bc,br=trace(tag+'-auto-v0274-axe-boss01');out,oc,orr=trace(tag+'-auto-v0274-axe-exit01')
  assert all(r['room_cleared'] and r['failure'] is None and r['deaths']==0 for r in [ar,br,orr]);assert ar['last_state']['weapon']==1 and ar['last_state']['item_value']==1;assert br['last_state']['selected']==1 and br['last_state']['progress']==128;assert orr['full_dungeon_cleared'] and orr['last_state']['max_health']==32
  replay=out.with_name(out.name+'-fixed-replay');proof=load(replay/'replay_report.json');assert proof['passed'] and proof['rom_sha256']==oc['rom_sha256'] and not proof['feedback_reads']
  for stem,ext in [('ram','bin'),('frame','png')]:assert read(out/f"{stem}_{oc['frames']:05d}.{ext}")==read(replay/f"{stem}_{oc['frames']:05d}.{ext}")
  ram=read(out/f"ram_{oc['frames']:05d}.bin")
  if tag=='sms':endpoints.append((ram[0x100:0x200],ram[0x1600:0x1b00]))
  else:
   d=lambda n,k:bytes(ram[(sy[n]+i)^1] for i in range(k));endpoints.append((d('game_save_state',592)[0x50:0x150],d('sms_vram',0x4000)[0x3800:0x3d00]))
  trials=[];hp=[];boss_rows=[]
  for suffix in ['05','06']:
   later,lc,lr=trace(tag+'-auto-v0274-axe-d2-boss'+suffix);events=load(later/'events.json');rows=[v for v in events if v.get('room')==0x144 and any(a['type']==0x63 for a in v.get('actors',[]))];boss_rows+=rows;hp += [a['hp'] for v in rows for a in v['actors'] if a['type']==0x63];trials.append(dict(case=later.name,reached_boss=bool(rows),deaths=lr['deaths'],failure=lr['failure']))
  cases.append(dict(system=tag,axe_acquired=True,equipped_by_inventory=True,first_crystal=True,first_dungeon_exited=True,first_dungeon_deaths=0,fixed_replay_ram_bytes=proof['whole_ram_bytes'],fixed_png_exact=True,later_trials=trials,second_boss_reached=bool(boss_rows),second_crystal=lr['room_cleared'] and lr['last_state']['progress']==128,minimum_second_boss_hp=min(hp) if hp else None,later_deaths=lr['deaths'],later_failure=lr['failure'],later_final_room=lr['last_state']['room']))
 assert endpoints[0]==endpoints[1]
 r=dict(passed=True,md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha((ROOT/'input/original.sms').read_bytes()),game_code_changed=False,cases=cases,source_first_exit_flags_exact_bytes=256,source_first_exit_map_exact_bytes=1280,evidence=evidence,full_game_validated=False,limits=['Natural NTSC button-only paths, no ROM/RAM/SRAM injections. First axe/equip/boss/crystal/exit pass without deaths on both systems.','Each final first-dungeon state/image is reproduced by a cold fixed-input replay. Source/native encounters, controls, health and timings differ.','Later dungeon-two attempts are reported with their real outcome; reaching a boss is not completing its fight.','Original R/IRQ random stream, global timing, waveform, PAL campaign and hardware remain incomplete or unverified.'])
 (ROOT/'analysis/natural_axe_campaign_v0274_report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()
