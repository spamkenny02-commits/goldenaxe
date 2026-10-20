"""Ensure optional experiments do not alter default kernel generation."""
import json,subprocess
from pathlib import Path
import md_class0_scene_fixture as scene
import md_clock_service_kernel as service
from md_live_z80_kernel import sources
ROOT=Path(__file__).resolve().parents[1]
def main():
 old_scene={'__name__':'old_scene'};exec(subprocess.check_output(['git','show','1652230:tools/md_class0_scene_fixture.py'],cwd=ROOT).decode(),old_scene)
 old_service={};exec(subprocess.check_output(['git','show','1652230:tools/md_clock_service_kernel.py'],cwd=ROOT).decode(),old_service)
 checks=[]
 for bare in [False,True]:
  for hidden in [False,True]:
   for verify in [False,True]:
    main,body=sources(bare,True,False,False,True,128)
    assert scene.instrument(main,body,verify=verify,proof=not bare,hidden=hidden)==old_scene['instrument'](main,body,verify=verify,proof=not bare,hidden=hidden)
    checks.append(dict(bare=bare,hidden=hidden,verify=verify))
 for video in [False,True]:
  for kind in ['all','repeat-disabled']:assert service.source(video,kind)==old_service['source'](video,kind)
 report=dict(scene_default_combinations=checks,clock_default_combinations=4,generated_text_identical=True,limits=['Generated kernel text regression against HEAD1652230; does not replace emulator execution for new options.'])
 (ROOT/'analysis/md_class0_scheduling_default_regression_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Eight scene defaults and four clock defaults identical to1652230.')
if __name__=='__main__':main()
