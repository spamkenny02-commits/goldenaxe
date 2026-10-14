"""Measure recovery-to-floor timing separately from absolute IRQ clock phase."""
import hashlib,json
from run_core import ROOT

def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());results=[];evidence=[]
    for suffix in ['', '-pal']:
        path=ROOT/f'validation/reward_floor_phase{suffix}_profile.json';raw=path.read_bytes();profile=json.loads(raw);assert profile['md_sha256']==digest
        assert profile['source_sha256']==sha((ROOT/'input/original.sms').read_bytes())
        evidence.append(dict(file=path.name,sha256=sha(raw)))
        for case in profile['cases']:
            traces=case['traces'];resumed={tag:next(int(f) for f,v in rows.items() if int(f)>3700 and (v['scan'],v['phase'])!=(rows['3690']['scan'],rows['3690']['phase'])) for tag,rows in traces.items()}
            delta=resumed['md']-resumed['sms'];assert -1<=delta<=1,(suffix,case['room'],delta)
            frames=range(3720,3900)
            def aligned(shift):
                return all((traces['sms'][str(f-shift)]['scan'],traces['sms'][str(f-shift)]['phase'])==(traces['md'][str(f)]['scan'],traces['md'][str(f)]['phase']) for f in frames)
            steady=next((shift for shift in [0,-1,1] if aligned(shift)),None)
            assert steady is not None,(suffix,case['room'],'steady floor drift greater than one frame')
            results.append(dict(region=profile['region'],room=case['room'],first_floor_step=resumed,resume_delta=delta,steady_scan_phase_frame_shift=steady,aligned_scan_phase_frames_exact=len(frames)))
    assert len(results)==6
    report=dict(md_sha256=digest,source_sha256=sha((ROOT/'input/original.sms').read_bytes()),cases=results,evidence=evidence,full_game_ported=False,limits=['Three controlled item-reward rooms per region; confirmation is a single controller press at frame 3700.','Residual zero/one-frame recovery offsets are reported, not hidden by phase alignment.','The absolute source/native IRQ clock phase is not synchronized in these runs; full bitmap presentation after reward dismissal remains unverified.'])
    (ROOT/'validation/reward_floor_phase_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Recovery deltas:',[x['resume_delta'] for x in results])

if __name__=='__main__':main()
