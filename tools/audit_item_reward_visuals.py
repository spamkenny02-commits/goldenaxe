"""Compare original reward-window VRAM, sprite positions and tile pixels."""
import hashlib,json
from extract_item_rewards import ROOT

def sha(b):return hashlib.sha256(b).hexdigest()

def sms_pixels(v,tile):
    return [sum(((v[tile*32+y*4+p]>>(7-x))&1)<<p for p in range(4)) for y in range(8) for x in range(8)]

def md_pixels(v,tile):
    start=tile*32
    return [(v[(start+y*4+x//2)^1]>>(4 if x%2==0 else 0))&15 for y in range(8) for x in range(8)]

def main():
    md_sha=sha((ROOT/'gaw-megadrive.bin').read_bytes());source_sha=sha((ROOT/'input/original.sms').read_bytes());results=[]
    for suffix in ['', '-pal']:
        gameplay=json.loads((ROOT/f'validation/item_rewards_gameplay{suffix}_report.json').read_bytes());assert gameplay['md_sha256']==md_sha
        for case in gameplay['cases']:
            if not case['reward_window_tile_words_exact']:continue
            paths={tag:ROOT/f"validation/{tag}-clear-gameplay-{case['room']:03x}-{case['already']}-item-rewards-{case['initial_weapon']}{suffix}" for tag in ['sms','md']}
            for tag,path in paths.items():assert json.loads((path/'capture.json').read_bytes())['rom_sha256']==(source_sha if tag=='sms' else md_sha)
            a=(paths['sms']/'vram_03500.bin').read_bytes();b=(paths['md']/'vram_03500.bin').read_bytes()
            for y in range(19,24):
                for x in range(1,31):
                    w=int.from_bytes(a[0x3800+y*64+x*2:0x3802+y*64+x*2],'little')
                    translated=((w>>11)&1)<<13|((w>>12)&1)<<15|((w>>10)&1)<<12|((w>>9)&1)<<11|16+(w&511)
                    p=0xe000+(y+2)*128+x*2
                    assert int.from_bytes(b[p:p+2],'little')==translated,(hex(case['room']),suffix,'window VRAM',x,y)
            for tile in list(range(208,236))+list(range(444,448))+list(range(496,502)):
                assert sms_pixels(a,tile)==md_pixels(b,tile+16),(hex(case['room']),suffix,'tile pixels',tile)
            source=[]
            for i in range(64):
                if a[0x3f00+i]==208:break
                source.append((a[0x3f80+i*2],a[0x3f00+i]+17,a[0x3f81+i*2]+272))
            native=[];i=0;seen=set()
            while i not in seen:
                seen.add(i);p=0xf400+i*8;word=lambda off:int.from_bytes(b[p+off:p+off+2],'little')
                native.append(((word(6)&511)-128,(word(0)&511)-128,word(4)&2047));i=word(2)&127
                if not i:break
            assert len(source)==8 and source==native,(hex(case['room']),suffix,'held-object pose',source,native)
            results.append(dict(room=case['room'],region='pal' if suffix else 'auto',window_words=150,tiles_pixels_exact=38,held_pose_sprites_exact=8,capture_files={tag:dict(folder=str(path.relative_to(ROOT)),vram_sha256=sha((path/'vram_03500.bin').read_bytes())) for tag,path in paths.items()}))
    assert len(results)==20
    report=dict(md_sha256=md_sha,source_sha256=source_sha,cases=results,full_game_ported=False,limits=['Stable acquisition display at frame 3500 only; no complete animation or framebuffer equivalence claim.','Controlled room and frozen actor setup; no natural dungeon progression.','Animated floor workload after message dismissal and audio waveforms remain unverified.'])
    (ROOT/'validation/item_rewards_visuals_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('20 stable reward windows: 3000 VRAM words, 760 tiles and 160 held-pose sprites match.')

if __name__=='__main__':main()
