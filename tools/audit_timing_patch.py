"""Bind timing/service checks and explicit remaining differences to one immutable ROM."""
import hashlib,json
from actor_reference import ROOT

def main():
 data=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(data).hexdigest()
 assert len(data)==524288
 assert int.from_bytes(data[0x18e:0x190],'big')==sum(int.from_bytes(data[n:n+2],'big') for n in range(0x200,len(data),2))&65535
 assert int.from_bytes(data[0x1a4:0x1a8],'big')==len(data)-1
 for alias in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert (ROOT/alias).read_bytes()==data
 reports=[]
 for name in ['intro_report','intro-pal_report','timing_report','timing-pal_report','merchant_report','service_transition_report','sfx_report','save_report','paid_healer_report','house_dialogue_report']:
  p=ROOT/f'validation/{name}.json';raw=p.read_bytes();d=json.loads(raw);assert d['md_sha256']==digest,name
  reports.append(dict(file=p.name,sha256=hashlib.sha256(raw).hexdigest()))
 for suffix in ['', '-pal']:
  d=json.loads((ROOT/f'validation/intro{suffix}_report.json').read_text());assert d['no_accumulating_text_delay'] and len(d['story_lines'])==65
  d=json.loads((ROOT/f'validation/timing{suffix}_report.json').read_text());assert all(x['differing_state_frames']==0 for x in d['natural_input_sequences'] if x['sequence']!='vertical');assert d['enemy']['differing_motion_counter_frames']==0
 d=json.loads((ROOT/'validation/service_transition_report.json').read_text());assert len(d['cases'])==7 and all(not x['unknown_or_corrupted_portrait_frames'] and x['clean_portrait_frames']>=90 for x in d['cases'])
 entries=json.loads((ROOT/'versions/index.json').read_text());entry=next(x for x in entries if x['sha256']==digest);assert (ROOT/'versions'/entry['rom']).read_bytes()==data
 report=dict(md_sha256=digest,version=entry['version'],rom_bytes=len(data),aliases_identical=True,standard_additive_checksum_valid=True,targeted_reports=reports,full_game_regression_run=False,known_remaining_timing_differences=['Small absolute intro offsets: NTSC 13..14 frames per line, PAL -5..-4.','Destination preparation after vertical scroll remains shorter: 27 frames in NTSC, 22 in PAL, on route94->A4.','All monster AI and original Z80 random stream are not covered.'])
 (ROOT/'validation/timing_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('v%04d: ten targeted reports, ROM aliases and checksum bound; remaining timing differences retained'%entry['version'])
if __name__=='__main__':main()
