"""Audit borrowed-noise rest correction and current source/native evidence."""
import hashlib,json
from actor_reference import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 prior=ROOT/'analysis/audio-ownership-v0182/source-v0182';before=(prior/'sound.inc').read_text();after=(ROOT/'megadrive/src/sound.inc').read_text()
 old='    else { c[0]|=16;PSG_write(c[1]+31);return; }'
 new="""    /* 863E keeps the borrowed channel's PSG output when marking a rest. */
    else { c[0]|=16;if(!(c[0]&4)) PSG_write(c[1]+31);return; }"""
 assert before.count(old)==1 and before.replace(old,new)==after
 unchanged=[]
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file() and p.name!='sound.inc':assert p.read_bytes()==(prior/p.name).read_bytes();unchanged.append(p.name)
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest()
 assert len(rom)==1048576 and int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
 checksum=sum(int.from_bytes(rom[n:n+2],'big') for n in range(0x200,len(rom),2))&65535
 assert checksum==int.from_bytes(rom[0x18e:0x190],'big')
 for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert (ROOT/name).read_bytes()==rom
 baseline=json.loads((ROOT/'analysis/noise_note_baseline_report.json').read_text());fixed=json.loads((ROOT/'analysis/noise_note_report.json').read_text())
 assert baseline['md_sha256']==sha(ROOT/'versions/v0182-f41db51b/gaw-megadrive-v0182.bin') and baseline['cases']==18432
 assert [r['mismatches'] for r in baseline['rows']]==[72,72]
 assert all(not d['ram_byte_indices'] and d['fixture'][0]&63==0 and d['fixture'][1]&4 for r in baseline['rows'] for d in r['differences'])
 assert fixed['md_sha256']==digest and fixed['cases']==18432 and fixed['all_cases_exact']
 evidence={}
 for name in ['analysis/noise_note_report.json','validation/music_report.json','validation/sfx_report.json','validation/music_fade_dispatch_report.json']:
  p=ROOT/name;r=json.loads(p.read_text());assert r['md_sha256']==digest,(name,'stale ROM');evidence[name]=sha(p)
 music=json.loads((ROOT/'validation/music_report.json').read_text());sfx=json.loads((ROOT/'validation/sfx_report.json').read_text());fade=json.loads((ROOT/'validation/music_fade_dispatch_report.json').read_text())
 assert len(music['tracks'])==13 and sum(r['irq_states_exact'] for r in music['tracks'])==23400
 assert len(sfx['effects'])==29 and sum(r['irq_states_exact'] for r in sfx['effects'])==19140
 assert len(fade['cases'])==2 and all(r['IRQ_records_exact']==r['audible_PSG_register_states_exact']==900 for r in fade['cases'])
 report=dict(md_sha256=digest,bytes=len(rom),checksum=f'{checksum:04X}',only_noise_rest_mute_borrow_guard_added=True,unchanged_production_files=unchanged,current_evidence=evidence,full_game_ported=False,limits=['Original8679 noise selection falls through863E for rest; SET4 then BIT2 returns without PSG mute when the channel is borrowed. Native now preserves that PSG output.','18432 source/model/compiled-native cases compare400 driver bytes and noise PSG control/volume registers. Baseline144 PSG divergences with identical RAM;currentzero. Source helper instruction cost matches independently. All256 note bytes and boundary flags/global offsets;synthetic contexts,not natural occurrence evidence.','13 music,29 effects and87/B0/82 fade compare44340 reader/audiblePSG states. Muted noise frequency excluded only in general regressions;targeted helper compares both noise registers even if muted. Waveforms/hardware,full progression and complete channel/reader/loading prediction remain open.'])
 (ROOT/'validation/noise_note_patch_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Borrowed noise rest correction audited:',digest[:8],f'{checksum:04X}')
if __name__=='__main__':main()
