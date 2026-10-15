"""Audit exact F3 branch and source/native evidence for the current release."""
import hashlib,json
from actor_reference import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 prior=ROOT/'versions/v0181-97313b55/source';before=(prior/'sound.inc').read_text();after=(ROOT/'megadrive/src/sound.inc').read_text()
 added='''                    /* 8786..87AE stops this sequence if the borrowed tone is active. */
                    if(!(sound_ram[0xf]&128) && (value&3)==3 && (sound_ram[0x130]&128))
                    {
                        sound_ram[0xd0]=(sound_ram[0xd0]&~4)|16;
                        c[0]=0;sound_ram[0xf]=255;PSG_write(255);return FALSE;
                    }
'''
 assert after.count(added)==1 and after.replace(added,'')==before
 unchanged=[]
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file() and p.name!='sound.inc':assert p.read_bytes()==(prior/p.name).read_bytes();unchanged.append(p.name)
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest()
 assert len(rom)==1048576 and int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
 checksum=sum(int.from_bytes(rom[n:n+2],'big') for n in range(0x200,len(rom),2))&65535
 assert checksum==int.from_bytes(rom[0x18e:0x190],'big')
 for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert (ROOT/name).read_bytes()==rom
 baseline=json.loads((ROOT/'analysis/audio_ownership_baseline_report.json').read_text());fixed=json.loads((ROOT/'analysis/audio_ownership_report.json').read_text())
 assert baseline['md_sha256']==sha(ROOT/'versions/v0181-97313b55/gaw-megadrive-v0181.bin') and baseline['cases']==400
 assert [r['mismatches'] for r in baseline['rows']]==[60,60]
 assert fixed['md_sha256']==digest and fixed['cases']==400 and fixed['all_cases_exact']
 evidence={}
 for name in ['analysis/audio_ownership_report.json','validation/music_report.json','validation/sfx_report.json','validation/music_fade_dispatch_report.json']:
  p=ROOT/name;r=json.loads(p.read_text());assert r['md_sha256']==digest,(name,'stale ROM');evidence[name]=sha(p)
 music=json.loads((ROOT/'validation/music_report.json').read_text());sfx=json.loads((ROOT/'validation/sfx_report.json').read_text());fade=json.loads((ROOT/'validation/music_fade_dispatch_report.json').read_text())
 assert len(music['tracks'])==13 and sum(r['irq_states_exact'] for r in music['tracks'])==23400
 assert len(sfx['effects'])==29 and sum(r['irq_states_exact'] for r in sfx['effects'])==19140
 assert len(fade['cases'])==2 and all(r['IRQ_records_exact']==r['audible_PSG_register_states_exact']==900 for r in fade['cases'])
 report=dict(md_sha256=digest,bytes=len(rom),checksum=f'{checksum:04X}',only_F3_ownership_stop_branch_added=True,unchanged_production_files=unchanged,current_evidence=evidence,full_game_ported=False,limits=['Original8786..87AE ends sequence when DE0F is nonnegative,argument low2bits=3 and DF30 active. Clears current flags,restoresDED0 borrow/release flags,setsDE0F=FF and writesFF toPSG. Native now reproduces this early return.','400 source/compiled-native cases compare400 driver bytes: baseline120 mismatches,currentzero. Actual ROM9B2B bytes interpreted by synthetic channel contexts;not a natural-event reachability assertion.','13 music,29 effects and87/B0/82 fade compare44340 reader/audiblePSG states. Muted noise frequency excluded;waveform/hardware,full progression,whole reader instruction prediction and physical loading correction remain open.'])
 (ROOT/'validation/audio_ownership_patch_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('F3 ownership correction audited:',digest[:8],f'{checksum:04X}')
if __name__=='__main__':main()
