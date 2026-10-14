"""Audit two paid-loader music hooks against current source/native evidence."""
import hashlib,json
from actor_reference import ROOT

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
 prior=ROOT/'versions/v0177-3f4dbbc9';before=(prior/'source/paid_passage.inc').read_text()
 anchor='    load_house_room(paid_passage_target,0);'
 added='''    sound_music(0xb0); /*16D0:fade the previous room music while loading. */
    load_house_room(paid_passage_target,0);
    update_world_music(); /*1CAF runs before1FA7 reveals the destination. */'''
 assert before.count(anchor)==1 and before.replace(anchor,added)==(ROOT/'megadrive/src/paid_passage.inc').read_text()
 unchanged=[]
 for p in (ROOT/'megadrive/src').iterdir():
  if not p.is_file() or p.name=='paid_passage.inc':continue
  assert p.read_bytes()==(prior/'source'/p.name).read_bytes(),('unexpected production change',p.name)
  unchanged.append(p.name)
 source=(ROOT/'input/original.sms').read_bytes()
 assert source[0x16df:0x16e7]==bytes.fromhex('3eb03265c03206de')
 assert source[0x24ea:0x24ed]==bytes.fromhex('cdaf1c') and source[0x24c2:0x24c5]==bytes.fromhex('c3a71f')
 baseline_path=ROOT/'analysis/paid_exit_music_baseline_report.json';baseline=json.loads(baseline_path.read_text())
 assert baseline['md_sha256']==sha((prior/'gaw-megadrive-v0177.bin').read_bytes())
 assert baseline['missing_native_B0_fade_command_reproduced']
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(rom)
 assert len(rom)==1048576 and int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
 checksum=sum(int.from_bytes(rom[n:n+2],'big') for n in range(0x200,len(rom),2))&65535
 assert checksum==int.from_bytes(rom[0x18e:0x190],'big')
 for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert (ROOT/name).read_bytes()==rom
 evidence={}
 for name,count in [('paid_exit_music_report.json',24),('music_fade_dispatch_report.json',2),('paid_passage_native_loading_clock_report.json',3072),('paid_passage_gameplay_report.json',20)]:
  p=ROOT/'validation'/name;r=json.loads(p.read_text());assert r['md_sha256']==digest
  assert (len(r['cases']) if isinstance(r['cases'],list) else r['cases'])==count
  evidence[name]=sha(p.read_bytes())
 driver=json.loads((ROOT/'validation/music_fade_dispatch_report.json').read_text())
 assert all(r['IRQ_records_exact']==900 and r['audible_PSG_register_states_exact']==900 for r in driver['cases'])
 report=dict(md_sha256=digest,checksum=f'{checksum:04X}',bytes=len(rom),only_two_paid_exit_music_hooks_added=True,unchanged_production_sources=unchanged,current_evidence=evidence,prior_baseline_sha256=sha(baseline_path.read_bytes()),full_game_ported=False,limits=[
  'Original16D0 B0 fade request and1CAF world request precede1FA7. Native paid loader now dispatches B0 before conversion and world music before reveal;existing single-tick clock adjustment includes this work. Sound reader,main,actors,gifts/save and other production modules byte-identical to v0177.',
  '24 live route/mask/region music cases,1800 aligned driver/PSG snapshots,3072 compiled loader-clock cases and20 payment/exit/menu regressions pass on this ROM.',
  'Actual command timestamps/PSG waveforms still differ with physical load duration and prior music phase. No fixed wait,whole IRQ model,other loading callers,refresh RNG,hardware or complete natural progression is claimed.'])
 (ROOT/'validation/paid_exit_music_patch_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Paid-exit music hook patch audited;',digest[:8],'checksum',f'{checksum:04X}')

if __name__=='__main__':main()
