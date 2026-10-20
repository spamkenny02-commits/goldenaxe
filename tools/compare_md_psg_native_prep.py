"""Compare selected native PSG preparation against matching captured controls."""
from pathlib import Path
import hashlib,json,statistics
ROOT=Path(__file__).resolve().parents[1]
PAIRS={'class0-grant-native-prep':'class0-hidden-grant-stamp','class0-refresh-native-prep':'class0-hidden-production','class0-refresh-native-prep-proof':'class0-hidden-proof'}
def main():
 rows=[];inputs={}
 for new,old in PAIRS.items():
  reports=[]
  for name in [old,new]:
   path=ROOT/('analysis/md_z80_psg_'+name.replace('-','_')+'_report.json');raw=path.read_bytes();inputs[path.relative_to(ROOT).as_posix()]=hashlib.sha256(raw).hexdigest();reports.append(json.loads(raw))
  for region in ['ntsc','pal']:
   before,after=[next(x for x in r['results'] if x['region']==region) for r in reports]
   assert before['cases']==after['cases']==48 and before['bytes']==after['bytes']==2976
   for field in ['vram_sha256','image_sha256','cram_sha256']:assert before['video'][field]==after['video'][field]
   assert [x['source_finish_master'] for x in before['rows']]==[x['source_finish_master'] for x in after['rows']]
   a=[e for x in before['rows'] for e in x['errors_master']];b=[e for x in after['rows'] for e in x['errors_master']];assert len(a)==len(b)==2976 and min(b)>=0
   rows.append(dict(variant=new,control=old,region=region,psg_late_max_before=max(a),psg_late_max_after=max(b),psg_late_mean_before=statistics.mean(a),psg_late_mean_after=statistics.mean(b),writes_less_late=sum(y<x for x,y in zip(a,b)),writes_more_late=sum(y>x for x,y in zip(a,b)),writes_equal=sum(y==x for x,y in zip(a,b)),publisher_master_before=sum(x['publisher_total_master'] for x in before['rows']),publisher_master_after=sum(x['publisher_total_master'] for x in after['rows']),readback_words=after['scene_readback_words'],state_checks=after['scene_state_checks']))
 source=(ROOT/'megadrive/src/md_z80_psg.c').read_bytes();assert b'#define MD_PSG_NATIVE_PREP 1' in source
 host=json.loads((ROOT/'analysis/md_z80_bridge_native_prep_report.json').read_bytes());polled=json.loads((ROOT/'analysis/md_z80_polled_native_prep_report.json').read_bytes())
 output=dict(results=rows,input_sha256=inputs,selected_source_default=True,host_descriptor_checks=host['checks'],host_polled_checks=polled['checks'],source_sha256=hashlib.sha256(source).hexdigest(),playable_unchanged=True,full_game_verified=False,limits=['Same48source cases and2976PSGbytes per region; all logical source finish dates and final VRAM/map/CRAM/image preserved. Native proof checks16states and readback words. Individual physical write lateness can improve or regress when bus phase shifts; worst delay and mean are reported, not a hard deadline guarantee. Native source default uses optimized preparation; test fixtures explicitly select legacy unless --psg-native-prep.'])
 (ROOT/'analysis/md_psg_native_prep_comparison_report.json').write_text(json.dumps(output,indent=2)+'\n')
 for row in rows:print(row['variant'],row['region'],row['psg_late_max_before'],row['psg_late_max_after'],row['writes_less_late'],row['writes_more_late'])
if __name__=='__main__':main()
