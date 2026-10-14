"""Observe real SMS loading clocks on six paid routes with empty/full enemy masks."""
import hashlib,json
from actor_reference import ROOT
from profile_paid_passage_loader_phases import main as profile

def main():
 rows=[]
 routes=json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']
 for town,target,*_ in routes:
  for mask in [0,255]:
   output=f'paid-passage-clocks/{town:02x}-{mask:02x}'
   profile(town,mask,output)
   folder=ROOT/'validation'/output
   for region in ['auto','pal']:
    path=folder/f'{region}-cycle-events.json';events=json.loads(path.read_text())
    a=next(e for e in events if e[1]==0x16d0 and e[4]==target)
    b=next(e for e in events if e[1]==0x1fa7 and e[2]>a[2])
    assert (b[5]-a[5])&255==1,(hex(town),mask,region,a,b)
    waits=[e for e in events if e[1]==0xb95 and a[2]<e[2]<b[2]]
    assert len(waits)==1,(hex(town),mask,region,len(waits))
    rows.append(dict(town=town,target=target,mask=mask,region=region,begin_frame=a[0],end_frame=b[0],begin_clock=a[5],end_clock=b[5],logical_ticks=1,original_wait_calls=1,raw_events_path=str(path.relative_to(ROOT)),raw_events_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
   print('Source loading clock verified',hex(town),hex(target),mask,flush=True)
 report=dict(source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=len(rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=[
  'Real paid-passage interactions and exits; unpatched SMS routines. Entrance/hero/initial clock controlled; destination persistence seeded before entrance at0/FF. No actor or RNG mutation during loading/play.',
  'All six routes,both video regions,two extreme actor masks.16D0 entry to1FA7 entry advances source clock exactly once despite varying real loading durations. Exactly one0B95 call is observed inside this interval.',
  'Does not prove native clock equivalence,all256 mask timings,all story states,whole transitions,RNG or full game fidelity. Raw profiles retain native diagnostics.'])
 (ROOT/'analysis/paid_passage_source_loading_clock_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(len(rows),'live paid-exit source loading clock cases exact',flush=True)

if __name__=='__main__':main()
