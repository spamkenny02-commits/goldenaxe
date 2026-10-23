"""Bind natural v0274 campaign evidence and fixed replays; no whole-game claim."""
import gzip,json
from pathlib import Path
from run_core import ROOT
from archive_lossless_evidence import sha
from validate_playable_sprite_limit import symbols
from verify_first_dungeon_story import read as legacy_read,BASE

def read(path):
 if path.exists():return path.read_bytes()
 archive=ROOT/'analysis/natural-campaign-v0274';m=json.loads((archive/'manifest.json').read_bytes());name=path.relative_to(ROOT).as_posix()
 if name in m['files']:
  raw=(archive/name).read_bytes();assert sha(raw)==m['files'][name];return raw
 i=m['compressed'][name];raw=(archive/i['stored']).read_bytes();assert sha(raw)==i['stored_sha256'];raw=gzip.decompress(raw);assert sha(raw)==i['raw_sha256'];return raw

def main():
 sy=symbols(ROOT/'megadrive/out/release/symbol.txt');digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert digest=='6af186deca6c86bfdeccaa607aab39f31345349b4d3a5861ad4d912b084c87f4';assert (ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'gaw-megadrive.bin').read_bytes()
 evidence={}
 def load(p):
  raw=read(p);evidence[p.relative_to(ROOT).as_posix()]=sha(raw);return json.loads(raw)
 def case(name):
  folder=BASE/name;c=load(folder/'capture.json');r=load(folder/'report.json');load(folder/'controls.json');assert c['rom_sha256']==r['rom_sha256'] and not c['test_ram_writes'] and c['sram_input'] is None
  return folder,c,r
 def ram(folder,c):return read(folder/f"ram_{c['frames']:05d}.bin")
 def fields(raw,native):
  if not native:return raw[0x100:0x200],raw[0x1600:0x1b00]
  d=lambda name,n:bytes(raw[(sy[name]+i)^1] for i in range(n))
  return d('game_save_state',592)[0x50:0x150],d('sms_vram',0x4000)[0x3800:0x3d00]
 first,fc,fr=case('md-auto-v0274-exit01');assert fr['full_dungeon_cleared'] and fr['failure'] is None and fr['deaths']==0 and fr['last_state']['first_gem']==128 and fr['last_state']['max_health']==32
 old=legacy_read(BASE/'sms-auto-17/ram_25998.bin');assert fields(old,False)==fields(ram(first,fc),True)
 records=[];endpoints=[]
 for name in ['sms-auto-v0274-d2-key01','md-auto-v0274-d2-key02']:
  folder,c,r=case(name);assert r['room_cleared'] and r['failure'] is None and not r['deaths'];st=r['last_state'];assert st['room']==0x152 and st['keys']==1 and st['dungeon']==2
  replay=folder.with_name(folder.name+'-fixed-replay');proof=load(replay/'replay_report.json');assert proof['passed'] and proof['rom_sha256']==c['rom_sha256'] and proof['frames']==c['frames'] and not proof['feedback_reads']
  for stem,ext in [('ram','bin'),('frame','png')]:assert read(folder/f"{stem}_{c['frames']:05d}.{ext}")==read(replay/f"{stem}_{c['frames']:05d}.{ext}")
  endpoints.append(fields(ram(folder,c),name.startswith('md')));records.append(dict(case=name,frames=c['frames'],deaths=0,health=st['health'],keys=1,whole_ram_fixed_replay_bytes=proof['whole_ram_bytes'],fixed_png_exact=True))
 assert endpoints[0]==endpoints[1]
 trials=[]
 for name in ['sms-auto-v0274-d2-boss05','md-auto-v0274-d2-boss05']:
  folder,c,r=case(name);events=load(folder/'events.json');rooms=sorted({e['room'] for e in events if 'room' in e});assert r['failure']=='death_retry_limit' and not r['room_cleared'];trials.append(dict(case=name,entered_rooms=rooms,final_room=r['last_state']['room'],deaths=r['deaths'],failure=r['failure'],weapon=r['last_state']['weapon'],boss_reached=r['entered_room']))
 report=dict(passed=True,md_sha256=digest,source_sha256=sha((ROOT/'input/original.sms').read_bytes()),game_code_changed=False,new_rom_created=False,first_dungeon=dict(native_deaths=0,crystal=True,max_health=32,exit_room=0xb9,source_flags_exact_bytes=256,source_map_exact_bytes=1280),second_dungeon_key=dict(cases=records,source_flags_exact_bytes=256,source_map_exact_bytes=1280),later_trials=trials,evidence=evidence,full_game_validated=False,limits=['NTSC natural paths use normal buttons from cold boot; no ROM/RAM/SRAM injection.','Fixed-input replay equality is per machine; source/native random encounters, timings, health and buttons differ.','First-dungeon SMS comparison uses its previously verified immutable cold-boot record.','Second boss not reached: controller retries die with the starting weapon. Later trials are failures, not evidence of a game bug or completed dungeon.','Original R/IRQ random stream, waveform, PAL campaign and hardware remain unfinished or unverified.'])
 (ROOT/'analysis/natural_campaign_v0274_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
