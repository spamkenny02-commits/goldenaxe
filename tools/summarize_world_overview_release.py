"""Bind overview fixtures and verify the restored playfield from saved evidence."""
import gzip,json
from PIL import Image
from run_core import ROOT
from validate_playable_sprite_limit import symbols
from archive_lossless_evidence import sha

def read(path):
    if path.exists():return path.read_bytes()
    archive=ROOT/'analysis/world-overview-v0240';m=json.loads((archive/'manifest.json').read_bytes());name=path.relative_to(ROOT).as_posix();i=m['compressed'][name];encoded=(archive/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==i['raw_sha256'];return raw

def main():
    md=sha((ROOT/'gaw-megadrive.bin').read_bytes());source=sha((ROOT/'input/original.sms').read_bytes());sy=symbols(ROOT/'megadrive/out/release/symbol.txt');cases=[];returns=[];timings=[];frames=0
    paths=sorted((ROOT/'analysis').glob('world_overview_v0240*_report.json'));assert len(paths)==16
    for path in paths:
        r=json.loads(path.read_bytes());assert r['passed'] and r['md_sha256']==md and r['source_sha256']==source
        if r['graphics']:cases.append(path.name);continue
        if not r.get('held_close_during_generation',False):
            assert r['overview_planar_5120_bytes_exact'] and r['overview_tilemap_1280_bytes_exact'] and all(not x['differences'] for x in r['pixel_comparisons'])
            frames+=len(r['pixel_comparisons'])
        name=path.stem.removeprefix('world_overview_').removesuffix('_report');a=ROOT/f'validation/world-overview-{name}-sms';b=ROOT/f'validation/world-overview-{name}-md'
        before={tag:read(folder/'ram_02859.bin') for tag,folder in [('sms',a),('md',b)]};after={tag:read(folder/'ram_08500.bin') for tag,folder in [('sms',a),('md',b)]}
        data=lambda raw,key,n:bytes(raw[(sy[key]+i)^1] for i in range(n))
        assert before['sms'][0x1c00:0x1ca0]==after['sms'][0x1c00:0x1ca0] and data(before['md'],'scratch',0x8a0)[0x800:]==data(after['md'],'scratch',0x8a0)[0x800:]
        assert data(before['md'],'room_metadata',3)==data(after['md'],'room_metadata',3)
        assert before['sms'][0x100:0x200]==after['sms'][0x100:0x200] and data(before['md'],'game_save_state',0x150)[0x50:]==data(after['md'],'game_save_state',0x150)[0x50:]
        assert data(after['md'],'sms_vram',0x3e00)[0x3800:]==read(a/'vram_08500.bin')[0x3800:0x3e00]
        for key in ['health','magic','gold','x','y']:assert r['final']['sms'][key]==r['final']['md'][key]
        left=Image.open(a/'frame_08500.png').convert('RGB');right=Image.open(b/'frame_08500.png').convert('RGB').crop((0,16,256,208));palette=set(left.getdata());conv={v:min(palette,key=lambda c:sum((x-y)**2 for x,y in zip(v,c))) for v in set(right.getdata())};diff=sum(x!=conv[y] for x,y in zip(left.getdata(),right.getdata()));assert diff==0,(name,diff)
        returns.append(dict(case=name,room_cells_preserved_bytes_per_machine=160,room_flags_preserved_bytes_per_machine=256,final_map_hud_bytes_exact=1536,settled_normalized_pixel_differences=diff))
        ends={tag:r['room_progress'][tag][-1]['frame'] for tag in ['sms','md']};timings.append(dict(case=name,**ends,md_minus_sms_frames=ends['md']-ends['sms']));cases.append(path.name)
    assert len(returns)==12 and frames==90
    base=ROOT/'validation/world-overview-v0240-sms/vram_07000.bin';edited=ROOT/'validation/world-overview-v0240-edited-sms/vram_07000.bin';changed=sum(x!=y for x,y in zip(read(base)[:5120],read(edited)[:5120]));assert changed>0
    report=dict(md_sha256=md,source_sha256=source,passed=True,cases=cases,controlled_cases=16,exterior_overview_cases=10,held_close_cases=2,source_quest_edit_changes_planar_bytes=changed,overview_normalized_pixel_frames_exact=frames,return_checks=returns,generation_finish_frames=timings,setup_and_return_timing_exact=False,full_game_verified=False,limits=['Initial ownership, optional quest/treasure flags and one clock phase alignment are controlled. No natural item acquisition is established.','Color-normalized pixel comparisons cover settled UI and restored exterior only; incremental raster publication and loading duration remain incomplete.'])
    (ROOT/'analysis/world_overview_release_v0240_report.json').write_text(json.dumps(report,indent=2)+'\n');print(dict(passed=True,overview_frames=frames,restored_exterior_frames=len(returns),quest_edit_changed_bytes=changed,generation_offsets=sorted(set(x['md_minus_sms_frames'] for x in timings))))

if __name__=='__main__':main()
