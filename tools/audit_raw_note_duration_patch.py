"""Audit exact reader correction and current native/source audio regressions."""
import hashlib,json
from actor_reference import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 prior=ROOT/'versions/v0180-3f155979/source';before=(prior/'sound.inc').read_text()
 old='        if(note&128) { c[10]=c[13];cursor--; }'
 new='''        /* 83EC always sends raw16-bit note durations through839B. */
        if((note&128) && (noise || !(c[0]&8))) { c[10]=c[13];cursor--; }'''
 assert before.count(old)==1 and before.replace(old,new)==(ROOT/'megadrive/src/sound.inc').read_text()
 unchanged=[]
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file() and p.name!='sound.inc':assert p.read_bytes()==(prior/p.name).read_bytes();unchanged.append(p.name)
 source=(ROOT/'input/original.sms').read_bytes();assert source[0x183ec:0x183ef]==bytes.fromhex('c39b83')
 baseline_path=ROOT/'analysis/raw-note-duration-v0180/analysis/raw_note_duration_baseline_report.json';baseline=json.loads(baseline_path.read_text())
 assert baseline['md_sha256']==sha(ROOT/'versions/v0180-3f155979/gaw-megadrive-v0180.bin') and baseline['cases']==1080
 assert all(r['cases']==r['mismatches']==540 for r in baseline['rows'])
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest()
 assert len(rom)==1048576 and int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
 checksum=sum(int.from_bytes(rom[n:n+2],'big') for n in range(0x200,len(rom),2))&65535
 assert checksum==int.from_bytes(rom[0x18e:0x190],'big')
 for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert (ROOT/name).read_bytes()==rom
 evidence={}
 for name in ['analysis/raw_note_duration_report.json','validation/music_report.json','validation/sfx_report.json','validation/music_fade_dispatch_report.json']:
  p=ROOT/name;r=json.loads(p.read_text());assert r['md_sha256']==digest,(name,'stale ROM');evidence[name]=sha(p)
 raw=json.loads((ROOT/'analysis/raw_note_duration_report.json').read_text());assert raw['all_cases_exact'] and raw['cases']==1080
 music=json.loads((ROOT/'validation/music_report.json').read_text());sfx=json.loads((ROOT/'validation/sfx_report.json').read_text());fade=json.loads((ROOT/'validation/music_fade_dispatch_report.json').read_text())
 assert len(music['tracks'])==13 and sum(r['irq_states_exact'] for r in music['tracks'])==23400
 assert len(sfx['effects'])==29 and sum(r['irq_states_exact'] for r in sfx['effects'])==19140
 assert len(fade['cases'])==2 and all(r['IRQ_records_exact']==r['audible_PSG_register_states_exact']==900 for r in fade['cases'])
 report=dict(md_sha256=digest,bytes=len(rom),checksum=f'{checksum:04X}',only_raw_note_duration_reuse_condition_changed=True,unchanged_production_files=unchanged,baseline_sha256=sha(baseline_path),current_evidence=evidence,full_game_ported=False,limits=['83D1 raw16-bit tone path goes directly to839B multiplication after reading its duration byte,including bit7 set. Native now reuses old duration only outside raw-tone mode. Note/noise normal behavior otherwise unchanged.','1080 original/compiled-native boundary cases compare all400 audio state bytes,not a natural-song reachability claim. All13 music and29 effects plus87/B0/82 fade pass44340 aligned reader/audible PSG register snapshots. Muted noise frequency excluded;waveforms/hardware and full game progression unproved.','Physical loading work,sequencer command costs and whole reader/IRQ prediction remain incomplete.'])
 (ROOT/'validation/raw_note_duration_patch_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Raw-note reader correction audited:',digest[:8],f'{checksum:04X}')

if __name__=='__main__':main()
