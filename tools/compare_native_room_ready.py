"""Compare preserved pre-row-batching and current identical native loading workloads."""
import json
from run_core import ROOT
from archive_lossless_evidence import sha
def main():
 before=json.loads((ROOT/'validation/native-room-ready-baseline/report.json').read_bytes());after=json.loads((ROOT/'analysis/native_room_ready_68k_report.json').read_bytes())
 assert before['passed'] and after['passed'] and before['source_cases_sha256']==after['source_cases_sha256'] and before['headers_sha256']==after['headers_sha256']
 assert sha((ROOT/'validation/native-room-ready-baseline/rom.bin').read_bytes())==before['test_rom_sha256']
 changed=[n for n,h in before['module_sha256'].items() if after['module_sha256'][n]!=h];assert changed==['source_actor_graphics.c'],changed
 rows=[]
 for a,b in zip(before['results'],after['results']):
  assert a['region']==b['region'] and a['cases']==b['cases']==24 and not a['failures'] and not b['failures'] and a['done'] and b['done']
  rows.append(dict(region=a['region'],baseline_frames=a['frame'],current_frames=b['frame'],reduction_percent=round((1-b['frame']/a['frame'])*100,2)))
 report=dict(passed=True,rows=rows,changed_modules=changed,source_cases_sha256=after['source_cases_sha256'],baseline_test_rom_sha256=before['test_rom_sha256'],current_test_rom_sha256=after['test_rom_sha256'],method='Same24 continuous-loading cases and diagnostic comparisons. Only actor remap implementation changed: stable2290T/351M1 rows batch when no IRQ can occur.',limits=['Diagnostic CPU elapsed frames include setup/state/pixel comparisons and SGDK initialization; not playable FPS or standalone room pacing. Physical IRQs disabled, virtual IRQ/audio unchanged.','Playable v0275 is unchanged; this does not establish physical render deadlines or hardware behavior.'])
 (ROOT/'analysis/native_room_ready_performance_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(rows)
if __name__=='__main__':main()
