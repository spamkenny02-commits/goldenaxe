"""Bind glyph equivalence and measured natural dialogue progress to v0222."""
import json
from run_core import ROOT
from archive_lossless_evidence import sha

def main():
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert digest=='13edb546df3bb0f6a5466843170323fbaa9b258355e171672391fcbef61b7ce8'
    cases=[];evidence={}
    for suffix in ['', '-pal']:
        old_path=ROOT/f'analysis/dialogue_preparation_v0221{suffix}_profile.json';new_path=ROOT/f'analysis/dialogue_preparation_v0222{suffix}_profile.json'
        old=json.loads(old_path.read_bytes());new=json.loads(new_path.read_bytes());assert old['md_sha256']=='0cc51636efdff6e1bed7c0e74808d0ce5589f9333718abdccb392cef7daa1013' and new['md_sha256']==digest
        assert old['source_sha256']==new['source_sha256']==sha((ROOT/'input/original.sms').read_bytes()) and old['results']['sms']==new['results']['sms']
        a=new['results']['sms'];b=new['results']['md'];source_page=next(e['frame'] for e in a['events'] if e['pc']==0x7f4)
        page=lambda r:next(e['frame'] for e in r['results']['md']['events'] if e['function']=='wait_dialog_continue')
        start=lambda r:next(e['frame'] for e in r['results']['md']['events'] if e['function']=='render_dialogue_text')
        assert start(old)==start(new) and source_page<page(new)<page(old)
        events=[e for e in a['events'] if e['pc']==0x7b3 and e['frame']<=source_page];previous=0;shapes=set()
        for e in events:
            h=a['hardware_bitmap_sha256'][str(e['frame'])];assert a['hardware_bitmap_colors_valid'][str(e['frame'])];shapes.add(h)
            matches=[int(f) for f,v in b['hardware_bitmap_sha256'].items() if v==h and b['hardware_bitmap_colors_valid'][f] and int(f)>=previous];assert matches;previous=min(matches)
        assert len(events)==37 and len(shapes)==29
        cases.append(dict(region=new['region'],source_page_wait_frame=source_page,previous_page_wait_frame=page(old),current_page_wait_frame=page(new),frames_gained=page(old)-page(new),remaining_delay_frames=page(new)-source_page,story_entry_unchanged=True,source_completed_uploads_preserved=len(events),source_distinct_complete_bitmaps_preserved_in_order=len(shapes)))
        for path in [old_path,new_path]:evidence[path.relative_to(ROOT).as_posix()]=sha(path.read_bytes())
    names=['analysis/dialogue_glyph_bytes_v0222_report.json','analysis/dialogue_vblank_v0222_report.json','validation/dialogue_controls_report.json','validation/house_dialogue_report.json','validation/dialogue_scroll_report.json']
    for name in names:
        path=ROOT/name;r=json.loads(path.read_bytes());assert r['md_sha256']==digest;evidence[name]=sha(path.read_bytes())
        if 'passed' in r:assert r['passed']
        if name.endswith('dialogue_controls_report.json'):assert len(r['cases'])==26 and all(c['passed'] for c in r['cases']) and not r['baseline_diagnostic']
    report=dict(md_sha256=digest,passed=True,cases=cases,evidence=evidence,source_files={'megadrive/src/main.c':sha((ROOT/'megadrive/src/main.c').read_bytes())},full_game_validated=False,complete_dialogue_timing_exact=False,audio_irq_scheduling_exact=False,scope='Exact OR/edge glyph rasterization plus actual production-ROM text fixtures and natural first-page snapshots. Improvements are measured on this route, not a global speed percentage. PAL next-word dwell and broader source clock/IRQ/RNG alignment remain open.')
    (ROOT/'analysis/dialogue_glyph_v0222_report.json').write_text(json.dumps(report,indent=2)+'\n');print(cases)

if __name__=='__main__':main()
