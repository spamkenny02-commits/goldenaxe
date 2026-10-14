"""Verify source complete first-page poses, including the name-only bitmap."""
import hashlib,json
from actor_reference import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    digest=sha(ROOT/'gaw-megadrive.bin');source=ROOT/'input/original.sms';cases=[]
    baseline=json.loads((ROOT/'versions/v0076-a171c534/opening_setup_patch_audit.json').read_bytes())
    assert sha(ROOT/'analysis/dialogue-publication-baseline-v0076/main.c')==baseline['source_files']['megadrive/src/main.c']
    for suffix in ['', '-pal']:
        path=ROOT/f'validation/dialogue_preparation{suffix}_profile.json';d=json.loads(path.read_bytes())
        assert d['md_sha256']==digest and d['source_sha256']==sha(source)
        assert d['production_roms_unmodified'] and not d['ram_injections']
        a=d['results']['sms'];b=d['results']['md']
        page=next(x['frame'] for x in a['events'] if x['pc']==0x07f4)
        native_page=next(x['frame'] for x in b['events'] if x['function']=='wait_dialog_continue')
        done=[x for x in a['events'] if x['pc']==0x07b3 and x['frame']<=page]
        assert len(done)==37
        matches=[];previous=0
        for event in done:
            frame=str(event['frame']);h=a['hardware_bitmap_sha256'][frame]
            assert a['hardware_bitmap_colors_valid'][frame]
            frames=[int(f) for f,v in b['hardware_bitmap_sha256'].items() if v==h and b['hardware_bitmap_colors_valid'][f]]
            ordered=[f for f in frames if f>=previous]
            assert ordered,(d['region'],event['frame'])
            previous=ordered[0]
            matches.append(dict(source_upload_complete_frame=event['frame'],bitmap_sha256=h,native_matching_complete_frames=frames))
        assert len({x['bitmap_sha256'] for x in matches})==29
        # Negative baseline result does not need color normalization: this hash
        # was absent even from the less restrictive old bit-plane projection.
        oldpath=ROOT/f'analysis/dialogue-publication-baseline-v0076/dialogue_preparation{suffix}_profile.json'
        old=json.loads(oldpath.read_bytes());assert old['md_sha256']==baseline['md_sha256']
        assert matches[0]['bitmap_sha256'] not in old['results']['md']['hardware_bitmap_sha256'].values()
        ev=a['events'];stages=[]
        for start,end,cost in [(0x7444,0x0524,9465),(0x0524,0x0554,22011),(0x0554,0x057d,25553),(0x057d,0x0595,157371),(0x0914,0x059b,44825)]:
            x=next(x for x in ev if x['pc']==start);y=next(x for x in ev if x['pc']==end)
            measured=(y['master_cycles']-x['master_cycles']-(y['irq_master_cycles']-x['irq_master_cycles']))//15
            assert measured==cost
            stages.append(dict(start_pc=start,end_pc=end,foreground_z80_tstates=cost))
        cases.append(dict(region=d['region'],source_complete_uploads=37,source_distinct_complete_bitmaps=29,all_complete_source_bitmaps_present_in_order=True,name_only_pose_missing_in_v0076_and_present_now=True,source_first_page_wait=page,native_first_page_wait=native_page,first_page_delta=native_page-page,matching_complete_bitmaps=matches,preparation_foreground_costs=stages,profile=path.name,profile_sha256=sha(path),baseline_profile_sha256=sha(oldpath)))
    report=dict(md_sha256=digest,source_sha256=sha(source),cases=cases,full_game_ported=False,limits=['One natural name A / new-game sequence per region.','Matching bitmap shapes and order do not prove equal publication counts, dwell times, partial transfers, whole framebuffer or audio timing.','Native first-page wait still differs; actual differences are listed.','Case controls, substitution edge cases, all other dialogue sequences and source IRQ/transfer ordering remain incomplete or unproven.'])
    (ROOT/'validation/dialogue_publications_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Publication shapes/order verified:',[(x['region'],x['first_page_delta']) for x in cases])

if __name__=='__main__':main()
