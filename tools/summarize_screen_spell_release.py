"""Bind v0249 ordered map sequences, patterns, settled returns and timing limits."""
import gzip,json
from PIL import Image
from run_core import ROOT
from archive_lossless_evidence import sha
from audit_item_reward_visuals import sms_pixels,md_pixels
def read(path):
    if path.exists():return path.read_bytes()
    archive=ROOT/'analysis/screen-spell-v0249';m=json.loads((archive/'manifest.json').read_bytes());item=m['compressed'][path.relative_to(ROOT).as_posix()];encoded=(archive/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'];return raw

def main():
    md=sha((ROOT/'gaw-megadrive.bin').read_bytes());cases=[];timings=[];returns=[];tiles=0;maps=0
    paths=[ROOT/f'analysis/screen_spell_v0249-{name}_report.json' for name in ['level1','level2','level1-pal','level2-pal','actors1','actors2','no-magic','house-real','dungeon-real']];assert all(p.exists() for p in paths)
    for path in paths:
        r=json.loads(path.read_bytes());assert r['passed'] and r['md_sha256']==md
        assert r['ordered_display_sequence_equal'] and r['final_fields_equal'] and r['damage_latch_actor_bytes_equal']
        tag=path.stem.removeprefix('screen_spell_').removesuffix('_report');folders={s:ROOT/f'validation/screen-spell-{tag}-{s}' for s in ['sms','md']}
        maps+=r['display_sequence_lengths']['sms']
        if r['magic']>=32:
            a=read(folders['sms']/'vram_03040.bin');b=read(folders['md']/'vram_03040.bin')
            count=47 if r['level']==1 else 79
            for tile in list(range(count))+list(range(496,502)):assert sms_pixels(a,tile)==md_pixels(b,tile+16),(tag,tile)
            tiles+=count+6
            ends={}
            for s,folder in folders.items():
                rows=json.loads((folder/'states.json').read_bytes());ends[s]=max(x['frame'] for x in rows if x['level'])+1
            timings.append(dict(case=tag,effect_end_frame=ends,md_minus_sms_frames=ends['md']-ends['sms']))
        if not r['actors']:
            a=Image.open(folders['sms']/'frame_03400.png').convert('RGB');b=Image.open(folders['md']/'frame_03400.png').convert('RGB').crop((0,16,256,208));pal=set(a.getdata());conv={v:min(pal,key=lambda c:sum((x-y)**2 for x,y in zip(v,c))) for v in set(b.getdata())}
            diff=sum(x!=conv[y] for x,y in zip(a.getdata(),b.getdata()));assert diff==0 or r['graphics']!=0,(tag,diff)
            returns.append(dict(case=tag,normalized_pixel_differences=diff))
        cases.append(path.name)
    report=dict(md_sha256=md,source_sha256=r['source_sha256'],passed=True,cases=cases,controlled_cases=9,ordered_display_map_states_exact=maps,display_map_bytes_per_state=1280,pattern_tiles_exact=tiles,settled_returns=returns,effect_end_timing=timings,timing_exact=False,full_game_verified=False,limits=['Ownership, resources, optional frozen actors, room class/background bank and one initial clock phase are controlled; natural acquisition and full campaign are not established.','Ordered physical name-table states and pattern pixels match; full animated sprite positions, raster writes and audio waveforms remain unverified.','Animation cadence and restoration duration remain approximate; measured end offsets are retained in this report. The two indoor return captures retain pixel differences and are not visually exact.'])
    (ROOT/'analysis/screen_spell_release_v0249_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(dict(cases=9,ordered_maps=maps,tiles=tiles,settled_returns=len(returns),timing=timings))
if __name__=='__main__':main()
