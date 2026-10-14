"""Validate both ground/water arrival poses, keeping unresolved up NTSC explicit."""
import hashlib,json
from actor_reference import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    digest=sha(ROOT/'gaw-megadrive.bin');cases=[];unresolved=[];inputs=[]
    keys=['state','room','hero','animation','hero_state','hero_flags','hero_counter','context','hero_pattern_sha256']
    for kind in ['ground','water']:
        p=ROOT/f'validation/{kind}_cross_all_diagnostic.json';d=json.loads(p.read_bytes());assert d['md_sha256']==digest and len(d['cases'])==8
        b=json.loads((ROOT/f'analysis/arrival-pose-baseline-v0097/{kind}_cross_all_diagnostic.json').read_bytes());assert b['md_sha256']==sha(ROOT/'versions/v0097-51363105/gaw-megadrive-v0097.bin')
        inputs.append(dict(file=p.name,sha256=sha(p)))
        for c in d['cases']:
            before=next(x for x in b['cases'] if x['region']==c['region'] and x['direction']==c['direction'])
            counts={k:[len(before['differences'][k]),len(c['differences'][k])] for k in ['state','hero','animation','context','hero_pattern_sha256']}
            if c['region']=='auto' and c['direction']==0:
                assert c['differences']['state'] and c['hero_pattern_difference_frames']
                unresolved.append(dict(kind=kind,region=c['region'],direction=0,differences=c['differences'],baseline_current_difference_counts=counts));continue
            assert all(not c['differences'][k] for k in keys),(kind,c['region'],c['direction'],{k:c['differences'][k] for k in keys if c['differences'][k]})
            rows=c['records'];frames=[int(f) for f,a in rows['sms'].items() if a['state']==rows['md'][f]['state']==10]
            assert frames and all(rows['sms'][str(f)]['sprite_entries']==rows['md'][str(f)]['sprite_entries'] and len(rows['sms'][str(f)]['sprite_entries'])==4 for f in frames)
            cases.append(dict(kind=kind,region=c['region'],direction=c['direction'],pose_and_state_frames_exact=len(rows['sms']),transition_hero_only_sprite_frames_exact=len(frames),baseline_current_difference_counts=counts,mutable_cells_difference_frames=c['differences']['cells'],software_map_difference_frames=c['differences']['map'],post_arrival_sprite_difference_frames=[f for f in c['differences']['sprite_entries'] if f not in frames]))
    assert len(cases)==14 and len(unresolved)==2
    result=dict(md_sha256=digest,source_sha256=sha(ROOT/'input/original.sms'),cases=cases,unresolved_up_ntsc=unresolved,fields_exact_in_passing_cases=keys,inputs=inputs,full_game_ported=False,limits=['Controlled all-ground/all-water maps, ownership, equipment, positions, cleared departing actors and one clock seed. Natural complete shore routes are unverified.','Up NTSC remains incorrect on both terrains; ground resumed state has two differing frames versus one in v0097. Pattern mismatches improve but timing is not solved.','Software-map staging, one-frame NTSC cell publication and post-arrival enemy sprite differences remain. No complete framebuffer/audio or all scroll routes proof.'])
    (ROOT/'validation/arrival_pose_report.json').write_text(json.dumps(result,indent=2)+'\n');print('14 arrival pose/state cases passed; 2 up NTSC cases remain explicit.')
if __name__=='__main__':main()
