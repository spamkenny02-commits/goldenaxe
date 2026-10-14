"""Audit source portal arrivals and the exact 1F78 nametable wipe model."""
import hashlib,json
from actor_reference import ROOT
from pathlib import Path
from extract_world import initial_room
from extract_title import rle_planes

def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    rom=(ROOT/'input/original.sms').read_bytes();_,_,_,_,arrays,_=initial_room(rom)
    assert Path(r'D:\Cartmod\GoldenAxeWarrior\chat\Golden Axe Warrior (USA, Europe).sms').read_bytes()==rom
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_portal_timing_libretro.dll'
    def cells(room):
        out=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][room*2:room*2+2],'little');rle_planes(arrays['world_room_streams'],offset,out,0,1);return out
    records=[r for r in json.loads((ROOT/'analysis/contact_script_reference.json').read_bytes())['records'] if r['target']==0x5cfb]
    results=[];evidence=[]
    for suffix in ['', '-pal']:
        path=ROOT/f'analysis/portal_profile{suffix}.json';raw=path.read_bytes();profile=json.loads(raw);evidence.append(dict(file=str(path.relative_to(ROOT)),sha256=sha(raw)))
        assert profile['source_sha256']==sha(rom) and profile['core_sha256']==sha(core.read_bytes()) and len(profile['cases'])==36
        assert {c['room'] for c in profile['cases']}=={r['room'] for r in records}
        for case in profile['cases']:
            room=case['room'];expected=next(r for r in records if r['room']==room);assert case['destination']==expected['destination_room']
            steps=[e for e in case['phases'] if e['pc']==0x1f83];assert len(steps)==20
            assert [e['de'] for e in steps]==list(range(0x7800,0x7828,2))
            assert all(b['frame']-a['frame']==1 for a,b in zip(steps,steps[1:]))
            end=next(e for e in case['phases'] if e['pc']==0x1fa4);assert end['frame']==steps[-1]['frame']+1
            target_cells=cells(case['destination']);marker=target_cells.find(12)
            xy=(128,88) if marker<0 else ((marker&15)*16+8,(marker&240)+16)
            arrival=next(v for v in case['states'] if v['frame']==case['script_return_frame'])
            assert (arrival['x']//256,arrival['y']//256)==xy,(room,xy,arrival)
            assert arrival['direction']==1 and arrival['state']==8 and arrival['mask']==128
            assert arrival['destination_flag']&16
            folder=ROOT/f"validation/source-portal-{room:03x}-{case['approach_direction']}{suffix}"
            baseline=bytes.fromhex(case['wipe_initial_map']);model=bytearray(baseline);checked=0;positions_checked=0;written=set()
            times={v['frame']:v for v in case['nametable_frames']}
            for n in range(20):
                for word in range(n,769,20):
                    if word>=768:continue
                    model[word*2:word*2+2]=b'\xff\x18';written.add(word)
                frame=steps[n+1]['frame'] if n<19 else end['frame']
                assert sha(model)==times[frame]['map_sha256'],(suffix,hex(room),n,'wipe map differs')
                checked+=1
                for capture in [3420,3430,3440]:
                    if capture==frame:
                        actual=(folder/f'vram_{frame:05d}.bin').read_bytes()[0x3800:0x3e00]
                        assert all(actual[w*2:w*2+2]==b'\xff\x18' for w in written),(room,frame,'written word')
                        positions_checked+=len(written)
            assert len(written)==768
            resume=next(v['frame'] for v in case['states'] if v['frame']>case['script_return_frame'] and v['state']==12)
            finish=next(e for e in case['phases'] if e['pc']==0x5d4b)
            start=next(e for e in case['loader_phases'] if e['pc']==0x24c5)
            end_loader=next(e for e in case['loader_phases'] if e['pc']==0x24f2)
            foreground=lambda a,b:((b['master_cycles']-a['master_cycles'])-(b['irq_master_cycles']-a['irq_master_cycles']))//15
            results.append(dict(loader_prefix_foreground_tstates=foreground(finish,start),actor_loader_foreground_tstates=foreground(start,end_loader),region=profile['region'],room=room,destination=case['destination'],arrival=list(xy),default_arrival=marker<0,wipe_steps=20,full_wipe_frame_maps_verified=checked,captured_written_words_verified=positions_checked,trigger_frame=case['trigger_frame'],script_return_frame=case['script_return_frame'],gameplay_resume_frame=resume))
    files=['tools/profile_portals.py','tools/capture_portal_prepared_rooms.py','tools/audit_portal_source.py','analysis/portal_prepared_rooms.json']
    baseline_rom=ROOT/'versions/v0051-3161f829/gaw-megadrive-v0051.bin'
    assert (ROOT/'gaw-megadrive.bin').read_bytes()==baseline_rom.read_bytes()
    report=dict(md_sha256=sha(baseline_rom.read_bytes()),source_only_evidence=True,source_files={n:sha((ROOT/n).read_bytes()) for n in files},research_core_source_sha256=sha((ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c').read_bytes()),source_sha256=sha(rom),profiles=evidence,cases=results,source_portals_checked=72,full_wipe_frame_maps_checked=sum(r['full_wipe_frame_maps_verified'] for r in results),all_arrivals_flags_actor_masks_exact=True,native_portals_implemented=False,full_game_ported=False,limits=['Source research only. Production remains v0051 and does not implement these portals.','Solved-origin flag and source-prepared map are injected; controller input then triggers the original routine. Natural dungeon progression remains unverified.','The wipe model starts with the actual VRAM map at the first wipe wait, preserving preceding shutter redraws and floor-animation updates.','Arrival assertions use the script return frame, before subsequent buffered input can move the hero.'])
    (ROOT/'analysis/portal_source_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('72 source portals and arrivals verified;',report['full_wipe_frame_maps_checked'],'full wipe frame maps match the translated model.')
if __name__=='__main__':main()
