"""Compare native hidden DMA admission policies against the captured reference."""
from pathlib import Path
import hashlib,json,statistics,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 rows=json.loads((ROOT/'analysis/md_class0_admission_baseline_physical_report.json').read_bytes())['results']+json.loads((ROOT/'analysis/md_class0_admission_physical_report.json').read_bytes())['results'];out=[]
 for r in rows:
  report=json.loads((ROOT/('analysis/md_z80_psg_'+r['variant'].replace('-','_')+'_report.json')).read_bytes());rr=next(x for x in report['results'] if x['region']==r['region']);frame=(262 if r['region']=='ntsc' else 313)*3420
  covered=sorted(set(v for row in r['rows'] for v in row['successful_guard_raw_v']))
  out.append(dict(variant=r['variant'],region=r['region'],psg_late_max_master=rr['errors_master'][1],held_checks=sum(x['held_beam_checks'] for x in r['rows']),held_checks_without_commit=sum(x['held_checks_without_commit'] for x in r['rows']),failed_hold_master_total=sum(x['failed_hold_master_total'] for x in r['rows']),reveal_after_source_mean_master=statistics.mean(x['reveal_after_source_master'] for x in r['rows']),reveal_after_source_max_master=max(x['reveal_after_source_master'] for x in r['rows']),reveal_after_source_max_frames=max(x['reveal_after_source_master'] for x in r['rows'])/frame,private_gap_max=r['private_gap_max'],guard_raw_v_coverage=covered,readback_words=rr['scene_readback_words'],state_checks=rr['scene_state_checks']))
 for row in out:
  base=next(x for x in out if x['variant']=='class0-hidden-production' and x['region']==row['region'])
  row['psg_late_delta_master']=row['psg_late_max_master']-base['psg_late_max_master'];row['reveal_mean_delta_master']=row['reveal_after_source_mean_master']-base['reveal_after_source_mean_master'];row['reveal_max_delta_master']=row['reveal_after_source_max_master']-base['reveal_after_source_max_master']
 old=subprocess.check_output(['git','show','aef3df4:megadrive/src/md_z80_video_span.c'],cwd=ROOT);current=(ROOT/'megadrive/src/md_z80_video_span.c').read_bytes();assert current.startswith(old)
 report=dict(results=out,native_existing_prefix_bytes=len(old),native_existing_prefix_sha256=hashlib.sha256(old).hexdigest(),native_existing_functions_preserved=True,rejected_preflight=['class0-hidden-preflight','class0-hidden-prepared-preflight'],experimental_candidate='class0-hidden-grant-stamp',default_changed=False,production_integration=False,limits=['Bare scene trials use all48cases/region and independent final VRAM/map/CRAM/source checks; grant-proof additionally checks all16states and per-case readbacks. Publication latency is relative to modeled source end24BF, not original SMS display-enable deadline. Fresh grant improves video latency but worsens worst PSG delay, so it is not promoted. Latest grant-read proximity is independently bounded; actual encoded-byte selection remains the reviewed native gate, not a traced store assertion.'])
 (ROOT/'analysis/md_class0_admission_comparison_report.json').write_text(json.dumps(report,indent=2)+'\n')
 for row in out:print(row['variant'],row['region'],row['held_checks_without_commit'],row['psg_late_max_master'],round(row['reveal_after_source_max_frames'],3))
if __name__=='__main__':main()
