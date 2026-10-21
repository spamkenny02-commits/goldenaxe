"""Compare visible dialogue pixels with completed VDP memory on each frame."""
import contextlib,gzip,io,json,sys
from PIL import Image
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols
from archive_lossless_evidence import sha

def reference_symbols():
    folder=ROOT/'analysis/sprite-viewport-v0219';m=json.loads((folder/'manifest.json').read_bytes());name='megadrive/out/release/symbol.txt'
    if name in m['files']:
        b=(folder/name).read_bytes();assert sha(b)==m['files'][name]
    else:
        i=m['compressed'][name];encoded=(folder/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256'];b=gzip.decompress(encoded);assert sha(b)==i['raw_sha256']
    p=ROOT/'validation/v0219-symbols.txt';p.write_bytes(b);return symbols(p)

def text_pixels(vram,cram):
    v=bytes(vram[n^1] for n in range(65536));colors=[]
    for n in range(64):
        c=int.from_bytes(cram[n*2:n*2+2],'little');r=(c&7)*2;g=((c>>3)&7)*2;b=((c>>6)&7)*2
        rgb=r<<12|(r>>3)<<11|g<<7|(g>>2)<<5|b<<1|b>>3
        colors.append((((rgb>>11)&31)*255//31,((rgb>>5)&63)*255//63,(rgb&31)*255//31))
    out=[]
    for y in range(128,168):
        for x in range(24,232):
            a=0xe000+(y//8)*128+(x//8)*2;attr=int.from_bytes(v[a:a+2],'big');row=y%8;col=x%8
            if attr&4096:row=7-row
            if attr&2048:col=7-col
            byte=v[(attr&2047)*32+row*4+col//2];color=(byte>>(0 if col&1 else 4))&15
            out.append(colors[color+((attr>>13)&3)*16])
    return out

def main():
    baseline='--baseline' in sys.argv
    rom=ROOT/'versions/v0219-7518d3c1/gaw-megadrive-v0219.bin' if baseline else ROOT/'gaw-megadrive.bin'
    sy=reference_symbols() if baseline else symbols(ROOT/'megadrive/out/release/symbol.txt')
    version=next(e['version'] for e in json.loads((ROOT/'versions/index.json').read_bytes()) if e['sha256']==sha(rom.read_bytes()))
    cases=[]
    for region in ['auto','pal']:
        folder=ROOT/f'validation/dialogue-vblank-v{version:04d}/{region}';active=set()
        def observe(f,r):
            if 3340<=f<=3500 and int.from_bytes(bytes(r[(sy['house_dialogue_active']+i)^1] for i in range(2)),'big'):active.add(f)
        writes=[(3300,sy[name],value.to_bytes(2,'big')) for name,value in [('hero_x',88<<8),('hero_y',72<<8),('hero_direction',0)]]
        presses=PRESSES[:11]+[(2950,2958,7),(3000,3020,4),(3350,3550,4)]
        with contextlib.redirect_stdout(io.StringIO()):run(rom,3500,folder,set(range(3340,3501)),presses,ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
        assert len(active)>=100,(region,'conversation not reached',len(active))
        rows=[]
        for f in sorted(active):
            expected=text_pixels((folder/f'vram_{f:05d}.bin').read_bytes(),(folder/f'cram_{f:05d}.bin').read_bytes())
            actual=list(Image.open(folder/f'frame_{f:05d}.png').convert('RGB').crop((24,128,232,168)).getdata())
            differences=sum(a!=b for a,b in zip(actual,expected));rows.append(dict(frame=f,differing_pixels=differences))
        cases.append(dict(region=region,frames=rows,differing_frames=sum(bool(r['differing_pixels']) for r in rows)))
        print(region,'dialogue mismatching frames',cases[-1]['differing_frames'],flush=True)
    result=dict(md_sha256=sha(rom.read_bytes()),passed=not any(c['differing_frames'] for c in cases),diagnostic_only=baseline,cases=cases,scope='First village NPC0 reached with normal input after controlled hero positioning. Every active-frame208x40 text area compared with independent tilemap/pattern/palette decoding. No source absolute cadence or whole-game claim.')
    (ROOT/f'analysis/dialogue_vblank_v{version:04d}_report.json').write_text(json.dumps(result,indent=2)+'\n')
    if not baseline:assert result['passed']

if __name__=='__main__':main()
