"""Freeze verified physical transfers and the exact endpoint extracts."""
import hashlib,json,shutil
from pathlib import Path
from validate_native_room_finish import MODULES
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((ROOT/name).read_text())

def main():
 out=ROOT/'analysis/class0-video-v0203';assert not out.exists(),'Archive is immutable'
 report_name='analysis/native_planned_loading_budget_bare_precise_physical_video_report.json';p=read(report_name)
 assert p['physical_video'] and p['physical_psg_writes'] and not p['audio_deadline_pacing']
 assert p['cases_sha256']==sha(ROOT/'validation/native-planned-room-finish/cases.json')
 for n,h in p['helpers'].items():assert sha(ROOT/'megadrive/src'/n)==h,n
 for field,name in [('video_module_sha256','source_class0_video.c'),('video_header_sha256','source_class0_video.h'),('video_assets_sha256','source_class0_video_assets_generated.h')]:assert p[field]==sha(ROOT/'megadrive/src'/name),name
 host=read('analysis/class0_video_conversion_report.json');native=read('analysis/class0_video_68k_report.json')
 assert host['attribute_words']==65536 and native['cases']==65536 and len(native['regions'])==2
 assert all(r['done'] and r['words']==65536 and r['tails']==8 and not r['failures'] for r in native['regions'])
 assert native['module_sha256']==host['module_sha256']==p['video_module_sha256'] and native['assets_sha256']==p['video_assets_sha256']
 files={report_name,'analysis/class0_video_assets_report.json','analysis/class0_video_conversion_report.json','analysis/class0_video_68k_report.json','analysis/class0_video_milestone.md','analysis/native_planned_room_finish_report.json','analysis/native_planned_room_finish_68k_report.json','analysis/native_irq_context_boundaries_report.json','analysis/native_source_wait_unit_report.json','analysis/graphics_classes_prefix_report.json','analysis/graphics_classes_prefix_68k_report.json','validation/native-planned-room-finish/cases.json','validation/cleanup_states_plan.json','build.ps1'}
 case_ids=[];minimum={}
 base=ROOT/'validation/native-planned-loading-budget-bare-precise-physical-video'
 for region in p['results']:
  assert region['done'] and region['cases']==12 and not region['failures'] and len(region['rows'])==12
  minimum[region['region']]=min(r['remaining_source_master']/3420 for r in region['rows']);assert minimum[region['region']]>0
  folder=base/region['region'];files.add(str((folder/'capture.json').relative_to(ROOT)).replace('\\','/'))
  for row in region['rows']:
   case_ids.append(row['case']);assert row['physical_map_words']==768 and row['physical_pattern_pixels']==12352 and row['physical_palette_words']==32
   assert row['pattern_guard_tiles']==2 and row['visible_width_restored']==256 and row['physical_plane']==[64,32] and row['display_disabled']
   for prefix in ['ram','vram','cram','vdp_regs']:
    path=folder/f"{prefix}_{row['extract_frame']:05d}.bin"
    if prefix in ['vram','cram']:assert sha(path)==row[prefix+'_sha256']
    files.add(str(path.relative_to(ROOT)).replace('\\','/'))
 assert sorted(case_ids)==list(range(24))
 for name in ['native_planned_room_finish_report.json','native_planned_room_finish_68k_report.json']:
  r=read('analysis/'+name);assert r['cases']==24 and not r['production_clock_wired']
  for n,h in r['helpers'].items():assert sha(ROOT/'megadrive/src'/f'{n}.c')==h
  if 'results' in r:assert all(x['done'] and not x['failures'] for x in r['results'])
 for n in set(MODULES)|{'source_class0_video','source_class0_video_assets_generated','source_pattern_plan_generated'}:
  for suffix in ['.c','.h']:
   if (ROOT/'megadrive/src'/(n+suffix)).exists():files.add('megadrive/src/'+n+suffix)
 for n in ['generate_class0_video.py','validate_class0_video.py','profile_native_loading_budget.py','validate_native_irq_context_boundaries.py','archive_class0_video.py']:files.add('tools/'+n)
 files.update(str(q.relative_to(ROOT)).replace('\\','/') for q in (ROOT/'analysis/class0-video-first-pass').iterdir() if q.is_file())
 for name in sorted(files):
  dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
 playable=sha(ROOT/'gaw-megadrive.bin');assert playable=='7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7'
 manifest={str(q.relative_to(out)).replace('\\','/'):sha(q) for q in sorted(out.rglob('*')) if q.is_file()}
 (out/'manifest.json').write_text(json.dumps(dict(playable_sha256=playable,minimum_remaining_scanlines=minimum,production_video_wired=False,files=manifest),indent=2)+'\n')
 print(len(manifest),'source/proof/extract files frozen;',minimum,'scanlines remaining. Playable ROM is v0203.')

if __name__=='__main__':main()
