"""Validate stated pose/SAT scope without hiding unresolved up-crossing timing."""
import hashlib,json
from actor_reference import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=ROOT/'validation/water_cross_all_diagnostic.json';d=json.loads(p.read_bytes());digest=sha(ROOT/'gaw-megadrive.bin')
    assert d['md_sha256']==digest and d['source_sha256']==sha(ROOT/'input/original.sms') and len(d['cases'])==8
    cases=[];unresolved=[]
    for c in d['cases']:
        if c['direction']==0 and c['region']=='auto':
            assert c['differences']['state'] and c['hero_pattern_difference_frames']
            unresolved.append(dict(region=c['region'],direction=0,differences=c['differences']));continue
        for key in ['state','room','hero','animation','context','hero_pattern_sha256']:assert not c['differences'][key],(c['region'],c['direction'],key)
        rows=c['records'];frames=[int(f) for f,a in rows['sms'].items() if a['state']==rows['md'][f]['state']==10]
        assert frames
        assert all(rows['sms'][str(f)]['sprite_entries']==rows['md'][str(f)]['sprite_entries'] and len(rows['sms'][str(f)]['sprite_entries'])==4 for f in frames)
        cases.append(dict(region=c['region'],direction=c['direction'],pose_state_frames_exact=len(rows['sms']),hero_pattern_frames_exact=len(rows['sms']),transition_frames_with_four_hero_sprites_exact=len(frames),transition_intervals_source=c['changes']['sms']['state'],transition_intervals_native=c['changes']['md']['state'],mutable_cells_difference_frames=c['differences']['cells'],software_map_difference_frames=c['differences']['map'],post_arrival_sprite_difference_frames=[f for f in c['differences']['sprite_entries'] if f not in frames]))
    base=ROOT/'analysis/water-cross-baseline-v0089/water_cross_diagnostic.json';b=json.loads(base.read_bytes());assert b['md_sha256']==sha(ROOT/'versions/v0089-1942f987/gaw-megadrive-v0089.bin')
    assert len(b['cases'])==2 and all(c['direction']==1 if 'direction' in c else True for c in b['cases'])
    removed={c['region']:len(c['hero_pattern_difference_frames']) for c in b['cases']}
    assert removed=={'auto':27,'pal':24}
    up_path=ROOT/'analysis/up-scroll-baseline-v0092/water_cross_all_diagnostic.json'
    up_base=json.loads(up_path.read_bytes())
    assert up_base['md_sha256']==sha(ROOT/'versions/v0092-602393fc/gaw-megadrive-v0092.bin')
    improvement=[]
    for region in ['auto','pal']:
        before=next(c for c in up_base['cases'] if c['region']==region and c['direction']==0)
        after=next(c for c in d['cases'] if c['region']==region and c['direction']==0)
        fields=['state','hero','animation','context','hero_pattern_sha256']
        counts={k:[len(before['differences'][k]),len(after['differences'][k])] for k in fields}
        assert all(new<old for old,new in counts.values()),(region,counts)
        improvement.append(dict(region=region,differing_frame_counts_before_after=counts))
    result=dict(upward_improvement_vs_v0092=improvement,md_sha256=digest,source_sha256=d['source_sha256'],cases=cases,unresolved_up_cases=unresolved,baseline_removed_hero_pattern_difference_frames=removed,diagnostic_input_sha256=sha(p),baseline_diagnostic_sha256=sha(base),full_game_ported=False,limits=['Controlled all-water software map, equipment, ownership, position, clock and cleared departing enemies. Natural shore routes, acquisition and combat remain unverified.','Seven directional pose/state cases pass; NTSC up remains incorrect. This is not full transition equivalence.','Mutable cells are loaded one frame early NTSC; software map staging differs during scrolling.','Four hero-only sprites match during the seven passing transitions; enemy sprites after arrival and full framebuffer/audio are not validated.'])
    (ROOT/'validation/water_cross_pose_report.json').write_text(json.dumps(result,indent=2)+'\n');print('Seven directional water pose cases passed; NTSC up explicitly unresolved.')
if __name__=='__main__':main()
