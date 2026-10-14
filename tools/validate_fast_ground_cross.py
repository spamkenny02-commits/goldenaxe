"""Measure corrected approach speed without claiming arrival equivalence."""
import hashlib,json
from actor_reference import ROOT

def main():
    base=ROOT/'analysis/fast-ground-baseline-v0093/ground_cross_all_scroll_cycles_diagnostic.json'
    p=ROOT/'validation/ground_cross_all_diagnostic.json'
    b=json.loads(base.read_bytes());d=json.loads(p.read_bytes());rows=[]
    assert b['md_sha256']==hashlib.sha256((ROOT/'versions/v0093-28ce141a/gaw-megadrive-v0093.bin').read_bytes()).hexdigest()
    assert d['md_sha256']==hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
    for c in d['cases']:
        old=next(o for o in b['cases'] if o['direction']==c['direction'] and o['region']==c['region'])
        entry=c['changes']['sms']['state'][0];native=c['changes']['md']['state'][0]
        assert entry==native
        before=old['changes']['md']['state'][0]
        assert before-entry==(6 if c['direction']==1 else 4)
        pre=[int(f) for f in c['records']['sms'] if int(f)<entry]
        assert pre and all(c['records']['sms'][str(f)]['hero']==c['records']['md'][str(f)]['hero'] for f in pre)
        rows.append(dict(region=c['region'],direction=c['direction'],source_transition_entry=entry,native_transition_entry_before=before,native_transition_entry_after=native,pre_transition_hero_frames_exact=len(pre),remaining_differences={k:len(v) for k,v in c['differences'].items()}))
    assert len(rows)==8
    result=dict(md_sha256=d['md_sha256'],source_sha256=d['source_sha256'],cases=rows,diagnostic_input_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),baseline_input_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),diagnostic_only=True,full_transition_equivalence=False)
    (ROOT/'validation/fast_ground_cross_improvement.json').write_text(json.dumps(result,indent=2)+'\n');print('Eight approach speeds corrected; arrival differences retained.')
if __name__=='__main__':main()
