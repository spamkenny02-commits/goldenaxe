"""Audit disappearance of old world objects during four-direction exterior scrolls."""
import hashlib,json
from run_core import ROOT
from finalize_md_rom import md_checksum

def main():
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest();evidence=[];frames=0
 assert len(rom)==524288 and md_checksum(rom)==int.from_bytes(rom[0x18e:0x190],'big')
 for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert (ROOT/name).read_bytes()==rom
 for name in ['scroll_objects_report.json','scroll_objects-pal_report.json','timing_report.json','timing-pal_report.json','title_cadence_report.json','title_cadence-pal_report.json']:
  path=ROOT/'validation'/name;d=json.loads(path.read_text());assert d['md_sha256']==digest,name
  evidence.append(dict(file=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
  if name.startswith('scroll_objects'):
   assert {x['direction'] for x in d['cases']}=={'left','right','up','down'}
   for case in d['cases']:
    for tag,c in case['checks'].items():
     assert c['nonhero_sprites_before_scroll']==10 and c['nonhero_sprite_errors']==0
     assert c['old_object_flags_cleared'] and c['primary_living_mask_preserved'] and c['gameplay_resumes']
     assert c['hero_sprite_frames']==c['checked_transition_frames']
     if case['direction']!='up':assert c['destination_nonhero_sprite_frames']>0
     if tag=='md':frames+=c['checked_transition_frames']
  elif name.startswith('timing'):
   assert all(x['differing_state_frames']==0 for x in d['natural_input_sequences']) and d['enemy']['differing_motion_counter_frames']==0
  else:assert d['relative_timing_exact'] and all(x['normalized_pixel_mismatches']==0 for x in d['pixel_checks'])
 report=dict(md_sha256=digest,source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),evidence=evidence,rom_bytes=len(rom),additive_checksum_valid=True,aliases_equal=True,controlled_scroll_cases=8,native_transition_sat_frames_without_old_objects=frames,hero_retained=True,destination_actors_reappear=True,persistence_retained=True,complete_transition_pixel_and_timing_equivalence=False,notes='SMS can retain its old hardware SAT for 5..8 setup frames after state 10 begins; its rebuilt SAT contains only the hero before scrolling. Native hides old objects immediately. Controlled north transition/loading is 4..5 frames shorter; other controlled paths can differ by one frame. Natural timing routes still pass.')
 (ROOT/'validation/scroll_objects_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Scroll object audit OK:',digest,'clean native SAT frames:',frames)
if __name__=='__main__':main()
