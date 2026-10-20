"""Compare hidden scene publication latency and PSG delays across scheduler trials."""
from pathlib import Path
import json,statistics
ROOT=Path(__file__).resolve().parents[1]
def main():
 rows=json.loads((ROOT/'analysis/md_class0_hidden_scheduling_baseline_physical_report.json').read_bytes())['results']+json.loads((ROOT/'analysis/md_class0_hidden_scheduling_physical_report.json').read_bytes())['results'];out=[]
 for r in rows:
  report=json.loads((ROOT/('analysis/md_z80_psg_'+r['variant'].replace('-','_')+'_report.json')).read_bytes());rr=next(x for x in report['results'] if x['region']==r['region']);frame=(262 if r['region']=='ntsc' else 313)*3420
  out.append(dict(variant=r['variant'],region=r['region'],frames=rr['frame'],dma_during_loader=r['during_loader'],psg_late_max_master=rr['errors_master'][1],reveal_after_source_mean_master=statistics.mean(x['reveal_after_source_master'] for x in r['rows']),reveal_after_source_max_master=max(x['reveal_after_source_master'] for x in r['rows']),reveal_after_source_max_frames=max(x['reveal_after_source_master'] for x in r['rows'])/frame,reveal_after_loader_max_frames=max(x['reveal_after_loader_master'] for x in r['rows'])/frame,private_gap_max=r['private_gap_max'],delivery_dma=sum(x.get('dma_during_delivery',0) for x in r['rows'])))
 for row in out:
  base=next(x for x in out if x['variant']=='class0-hidden-production' and x['region']==row['region'])
  row['psg_late_delta_master']=row['psg_late_max_master']-base['psg_late_max_master'];row['reveal_mean_delta_master']=row['reveal_after_source_mean_master']-base['reveal_after_source_mean_master'];row['reveal_max_delta_master']=row['reveal_after_source_max_master']-base['reveal_after_source_max_master']
 variants=sorted(set(r['variant'] for r in out)-{'class0-hidden-production'})
 for v in variants:assert any(x['psg_late_delta_master']>0 or x['reveal_mean_delta_master']>=0 or x['reveal_max_delta_master']>0 for x in out if x['variant']==v)
 (ROOT/'analysis/md_class0_hidden_scheduling_comparison_report.json').write_text(json.dumps(dict(results=out,not_promoted=variants,production_integration=False,limits=['Comparisons use all48 cases per physical region, final pixels/data and native source-state checks. Reveal is fixture display-on relative to modeled source end24BF, not a verified original SMS display-enable deadline. More overlap alone is not accepted as improved fidelity. All options remain off by default.']),indent=2)+'\n')
 print('Five scheduler policies measured; none promoted.')
if __name__=='__main__':main()
