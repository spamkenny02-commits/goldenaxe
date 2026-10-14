"""Bind title cadence evidence to the exact numbered cartridge binary."""
import hashlib,json
from run_core import ROOT
from finalize_md_rom import md_checksum

def main():
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest()
 assert len(rom)==524288 and md_checksum(rom)==int.from_bytes(rom[0x18e:0x190],'big')
 for path in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert (ROOT/path).read_bytes()==rom
 names=['title_cadence_report.json','title_cadence-pal_report.json','title_cadence-natural_report.json','title_cadence-pal-natural_report.json','intro_report.json','intro-pal_report.json','timing_report.json','timing-pal_report.json','merchant_report.json','service_transition_report.json','title_loading_model_report.json']
 evidence=[]
 for name in names:
  path=ROOT/'validation'/name;d=json.loads(path.read_text());assert d['md_sha256']==digest,name
  evidence.append(dict(file=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
  if name.startswith('title_cadence'):
   assert d['cape_poses']==33 and d['cape_pose_frames']==6
   assert d['warrior_palette_steps']==9 and d['warrior_palette_step_frames']==6
   assert d['title_rows']==8 and d['title_row_frames']==1
   assert len(d['pixel_checks'])==20 and all(x['normalized_pixel_mismatches']==0 for x in d['pixel_checks'])
   for field in ['map_start_offsets','palette_start_offsets']:assert len(set(d[field]))==1
 intervals=[]
 for suffix in ['', '-pal']:
  intro=json.loads((ROOT/f'validation/intro{suffix}_report.json').read_text())
  title=json.loads((ROOT/f'validation/title_cadence{suffix}-natural_report.json').read_text())
  source=title['sms_map_frames'][0]-intro['source_intro_completion_frame'];native=title['md_map_frames'][0]-intro['native_intro_completion_frame']
  assert source==native,(suffix,source,native)
  intervals.append(dict(region='pal' if suffix else 'auto',source_frames=source,native_frames=native,absolute_title_start_offset_frames=title['map_start_offsets'][0]))
 report=dict(md_sha256=digest,source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),rom_bytes=len(rom),additive_checksum_valid=True,aliases_equal=True,evidence=evidence,title_cadence_cases=4,normalized_pixel_checks=80,relative_title_animation_cadence_exact=True,intro_completion_to_first_cape=intervals,absolute_title_start_exact=False,remaining='Absolute title start retains the preceding intro offset. Resource-loading and title cadence after intro completion match the natural reference in both regions.')
 (ROOT/'validation/title_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Title patch audit OK:',digest)
if __name__=='__main__':main()
