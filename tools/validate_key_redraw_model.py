"""Check instruction-derived redraw cost and source/native resumption profiles."""
import hashlib,json
from extract_key_redraw_cost import ROOT,room_map_cost


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());cases=[];profiles=[]
    model=json.loads((ROOT/'analysis/key_redraw_cost_model.json').read_bytes())
    assert room_map_cost()==model['map_rebuild_tstates']==192686
    for direction in ['up','left','right']:
        for suffix in ['', '-pal']:
            name=f'analysis/key_redraw_profile-{direction}{suffix}.json'
            raw=(ROOT/name).read_bytes();report=json.loads(raw)
            assert report['md_sha256']==digest and report['source_rom_unmodified']
            map_phase=next(p for p in report['phases'] if p['start_pc']=='0x2279')
            assert map_phase['foreground_tstates']==room_map_cost()
            axis='y' if direction=='up' else 'x';wall=40 if direction=='up' else 32 if direction=='left' else 224
            rows={tag:{r['frame']:r for r in trace} for tag,trace in report['hero_traces'].items()}
            restart={tag:next(f for f,r in trace.items() if f>3414 and r[axis]//256!=wall) for tag,trace in rows.items()}
            offset=restart['md']-restart['sms']
            assert offset==(-1 if not suffix else 0),(direction,suffix,offset)
            for frame in range(restart['sms'],restart['sms']+8):
                a,b=rows['sms'][frame],rows['md'][frame+offset]
                assert all(a[k]==b[k] for k in ['x','y','counter']),(direction,suffix,frame)
            baseline_name=name.replace('key_redraw_profile-','key_redraw_baseline-')
            baseline=json.loads((ROOT/baseline_name).read_bytes())
            before={tag:next(r['frame'] for r in trace if r['frame']>3414 and r[axis]//256!=wall) for tag,trace in baseline['hero_traces'].items()}
            previous_offset=before['md']-before['sms']
            assert previous_offset==(-4 if not suffix else -3)
            cases.append(dict(direction=direction,region='pal' if suffix else 'auto',
                              prior_movement_resume_offset=previous_offset,movement_resume_offset=offset,
                              aligned_post_resume_motion_frames_exact=8))
            profiles.append(dict(file=name,sha256=sha(raw),baseline_file=baseline_name,baseline_sha256=sha((ROOT/baseline_name).read_bytes())))
    report=dict(md_sha256=digest,source_map_loop_tstates_exact=192686,cases=cases,profiles=profiles,
                model=model,source_rom_unmodified=True,full_redraw_pixels_verified=False,
                all_irq_phases_cycle_exact=False,full_game_ported=False)
    (ROOT/'validation/key_redraw_model_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Six source profiles verify map work and improved redraw pause; PAL exact, NTSC one frame early.')


if __name__=='__main__':main()
