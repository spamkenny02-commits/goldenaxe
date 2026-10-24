"""Compare preserved scalar and stable-word68000 runs on identical vectors."""
import json
from run_core import ROOT
from archive_lossless_evidence import sha
def main():
 folder=ROOT/'validation/native-room-contours-baseline';a=json.loads((folder/'report.json').read_bytes());b=json.loads((ROOT/'analysis/native_room_contours_68k_report.json').read_bytes())
 assert a['passed'] and b['passed'] and a['source_cases_sha256']==b['source_cases_sha256'] and a['headers_sha256']==b['headers_sha256']
 assert sha((folder/'cases.json').read_bytes())==a['source_cases_sha256'] and sha((folder/'rom.bin').read_bytes())==a['test_rom_sha256']
 assert sha((folder/'source_room_contours.c').read_bytes())==a['module_sha256']['source_room_contours.c']
 changed=[n for n in a['module_sha256'] if a['module_sha256'][n]!=b['module_sha256'][n]];assert changed==['source_room_contours.c']
 rows=[]
 for old,new in zip(a['results'],b['results']):
  assert old['region']==new['region'] and old['done'] and new['done'] and not old['failures'] and not new['failures'] and old['cases']==new['cases']==24
  rows.append(dict(region=old['region'],scalar_frames=old['frame'],batched_frames=new['frame'],reduction_percent=100*(old['frame']-new['frame'])/old['frame']))
 report=dict(passed=True,rows=rows,changed_module=changed[0],baseline_module_sha256=a['module_sha256'][changed[0]],current_module_sha256=b['module_sha256'][changed[0]],cases_sha256=b['source_cases_sha256'],limits=['Diagnostic68000 CPU execution frames for24 virtual-clock cases per region, physical IRQs disabled. Not playable game FPS or physical loading pacing.'])
 (ROOT/'analysis/native_room_contours_performance_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(report)
if __name__=='__main__':main()
