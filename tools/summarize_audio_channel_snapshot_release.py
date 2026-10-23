"""Bind v0267 spell pacing, sprite tables and restored displays to the ROM."""
import gzip,json
from PIL import Image
from run_core import ROOT
from archive_lossless_evidence import sha
from validate_playable_sprite_limit import symbols
def read(path):
    if path.exists():return path.read_bytes()
    archive=ROOT/'analysis/audio-channel-snapshot-v0267';m=json.loads((archive/'manifest.json').read_bytes());i=m['compressed'][path.relative_to(ROOT).as_posix()];encoded=(archive/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==i['raw_sha256'];return raw
def main():
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());sy=symbols(ROOT/'megadrive/out/release/symbol.txt');cases=[];returns=[];timings=[];maps=0;clock_rows=0
    for name in ['level1','level1-pal','level2','level2-pal','actors1','actors2','actors2-pal','house','dungeon','no-magic','menu','menu-pal']:
        report=ROOT/f'analysis/screen_spell_v0267-{name}_report.json';r=json.loads(report.read_bytes());assert r['passed'] and r['md_sha256']==digest
        assert r['display_sprite_positions_equal'] and r['display_sprite_tiles_equal'] and r['ordered_display_sequence_equal'] and r['loop_clock_matches_source_iteration']
        folders={s:ROOT/f'validation/screen-spell-v0267-{name}-{s}' for s in ['sms','md']};maps+=r['display_sequence_lengths']['sms'];clock_rows+=r['loop_clock_rows']
        if r['magic']>=32:
            ends={s:max(x['frame'] for x in json.loads((folder/'states.json').read_bytes()) if x['level'])+1 for s,folder in folders.items()}
            timings.append(dict(case=name,**ends,md_minus_sms_frames=ends['md']-ends['sms']))
        if not r['actors']:
            source_frame=3700 if r['post_menu'] else 3400;native_frame=source_frame if r['post_menu'] else r['aligned_native_return_frame'];assert native_frame is not None
            if not r['post_menu']:
                a=read(folders['sms']/f'ram_{source_frame:05d}.bin');b=read(folders['md']/f'ram_{native_frame:05d}.bin')
                data=lambda n,k:int.from_bytes(bytes(b[(sy[n]+i)^1] for i in range(k)),'big')
                assert ((data('vtimer',4)-data('world_clock_shift',4))&255)==a[0x2f]
            a=Image.open(folders['sms']/f'frame_{source_frame:05d}.png').convert('RGB');b=Image.open(folders['md']/f'frame_{native_frame:05d}.png').convert('RGB').crop((0,16,256,208));pal=set(a.getdata());conv={v:min(pal,key=lambda c:sum((x-y)**2 for x,y in zip(v,c))) for v in set(b.getdata())}
            diff=sum(x!=conv[y] for x,y in zip(a.getdata(),b.getdata()));assert diff==0,(name,diff)
            returns.append(dict(case=name,source_frame=source_frame,native_frame=native_frame,comparison='same physical frame after inventory' if r['post_menu'] else 'same logical game clock',normalized_pixel_differences=diff))
        cases.append(report.name)
    audio=json.loads((ROOT/'analysis/audio_channel_snapshot_equivalence_report.json').read_bytes())
    assert audio['md_sha256']==digest and audio['all_400_bytes_work_DE_PSG_status_exact'] and audio['direct_channel_cases']==2840 and audio['source_vector_cases']==25644
    native=json.loads((ROOT/'analysis/audio_channel_snapshot_68k_report.json').read_bytes())
    assert native['cases']==25644 and sum(x['cases'] for x in native['results'])==51288 and all(x['done'] and not x['failures'] for x in native['results'])
    for report in [audio,native]:
        assert all(sha((ROOT/'megadrive/src'/f'{n}.c').read_bytes())==h for n,h in report['module_sha256'].items())
    coherence=json.loads((ROOT/'analysis/world_frame_coherence_v0267_report.json').read_bytes());assert coherence['passed'] and coherence['md_sha256']==digest
    profiles={v:json.loads((ROOT/f'analysis/screen_spell_v{v:04d}-cpu_cpu_report.json').read_bytes()) for v in [264,267]}
    assert profiles[267]['md_sha256']==digest
    cpu={v:next(x for n,x in r['summary_cycles_68k'].items() if n.startswith('source_audio_reader_stream.')) for v,r in profiles.items()}
    assert cpu[267]['mean']<cpu[264]['mean']
    cost=json.loads((ROOT/'analysis/screen_spell_cost_report.json').read_bytes());assert cost['passed'] and cost['md_sha256']==digest
    assert maps==626 and len(returns)==9
    result=dict(md_sha256=digest,source_sha256=sha((ROOT/'input/original.sms').read_bytes()),passed=True,controlled_cases=12,cases=cases,ordered_map_and_sprite_states_exact=maps,logical_loop_clock_observations=clock_rows,returns=returns,effect_end_timing=timings,audio_reader_cpu_cycles=cpu,audio_host_source_vectors=25644,audio_host_mutations=6000,audio_host_direct_channels=2840,audio_native_region_cases=51288,physical_timing_exact=False,full_game_verified=False,limits=['Initial ownership, resources, room class, optional frozen actors and one clock alignment are controlled. Natural acquisition and full campaign remain unverified.','Nine restored pixel comparisons normalize the palette and MD viewport. Seven align the logical game clock; two compare the same physical frame after opening/closing inventory.','Runtime pacing uses source foreground work and previous live audio work, with a fixed empty-queue IRQ raster assumption. Initial raster, future audio work and whole interrupt scheduling remain approximate.','Timing is reported per controlled fixture. No whole-game timing or analogue waveform claim; The initial blank is included even when the native setup phase is still1; its VRAM words and SAT are compared. The extra final-frame wait experiment266 was rejected.'])
    (ROOT/'analysis/audio_channel_snapshot_release_v0267_report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(dict(cases=12,ordered_maps_and_sprites=maps,restored_pixels=len(returns),timing=timings))
if __name__=='__main__':main()
