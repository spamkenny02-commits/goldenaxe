"""Observe a real terrain-changing actor's software and physical map writes."""
import contextlib,gzip,io,json,sys
from PIL import Image
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols
from archive_lossless_evidence import sha

def main():
    pal='--pal' in sys.argv;region='pal' if pal else 'auto'
    baseline='--baseline-v0224' in sys.argv
    if baseline:
        archive=ROOT/'analysis/dialogue-lookup-v0224';manifest=json.loads((archive/'manifest.json').read_bytes());name='megadrive/out/release/symbol.txt'
        if name in manifest['files']:
            data=(archive/name).read_bytes();assert sha(data)==manifest['files'][name]
        else:
            item=manifest['compressed'][name];encoded=(archive/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256']
            data=gzip.decompress(encoded);assert sha(data)==item['raw_sha256']
        symbol_path=ROOT/'validation/v0224-cell-symbols.txt';symbol_path.write_bytes(data)
    else:symbol_path=ROOT/'megadrive/out/release/symbol.txt'
    sy=symbols(symbol_path);rom=ROOT/'versions/v0224-6be955fd/gaw-megadrive-v0224.bin' if baseline else ROOT/'gaw-megadrive.bin';digest=sha(rom.read_bytes())
    version=next(e['version'] for e in json.loads((ROOT/'versions/index.json').read_bytes()) if e['sha256']==digest)
    records={};offset=8*64+14*2
    actor=bytearray(768);actor[0]=0x2b;actor[1]=8;actor[2]=6;actor[3]=0x28;actor[8:10]=bytes.fromhex('2c87');actor[12]=2;actor[13]=16;actor[0x11]=80;actor[0x13]=120;actor[0x18]=32
    for tag,path in [('sms',ROOT/'input/original.sms'),('md',rom)]:
        rows={}
        def observe(f,r):
            if f<2500:return
            data=lambda a,n:bytes(r[a:a+n]) if tag=='sms' else bytes(r[(a+i)^1] for i in range(n))
            base=0x1600 if tag=='sms' else sy['sms_vram']+0x3800
            words=b''.join(data(base+offset+dy*64,4) for dy in [0,1])
            rows[f]=dict(software_words=words.hex(),cell=data(0x1c47 if tag=='sms' else sy['scratch']+0x847,1)[0])
        def vram(f,v):
            if f<2500:return
            raw=bytes(v) if tag=='sms' else bytes(v[n^1] for n in range(65536))
            physical=b''.join(raw[0x3800+offset+dy*64:0x3800+offset+dy*64+4] for dy in [0,1]) if tag=='sms' else b''.join(raw[0xe000+(10+dy)*128+14*2:0xe000+(10+dy)*128+14*2+4] for dy in [0,1])
            rows[f]['physical_words']=physical.hex()
        writes=[(f,0x600 if tag=='sms' else sy['world_actor_state'],bytes(actor)) for f in range(2502,2630)]
        writes.append((2502,0x1c47 if tag=='sms' else sy['scratch']+0x847,b'\x03'))
        folder=ROOT/f'validation/cell-publication-v{version:04d}/{region}-{tag}'
        with contextlib.redirect_stdout(io.StringIO()):run(path,2632,folder,set(range(2500,2633)),([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],ram_writes=writes,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
        if tag=='md':
            for f,row in rows.items():
                v=(folder/f'vram_{f:05d}.bin').read_bytes();v=bytes(v[n^1] for n in range(65536));cram=(folder/f'cram_{f:05d}.bin').read_bytes();image=Image.open(folder/f'frame_{f:05d}.png').convert('RGB');compared=bad=0
                for y in range(80,96):
                    for x in range(112,128):
                        a=0xe000+(y//8)*128+(x//8)*2;attr=int.from_bytes(v[a:a+2],'big');cy=y%8;cx=x%8
                        if attr&4096:cy=7-cy
                        if attr&2048:cx=7-cx
                        b=v[(attr&2047)*32+cy*4+cx//2];color=(b>>(0 if cx&1 else 4))&15
                        if not color:continue # Transparent BG_A depends on BG_B/backdrop.
                        palette=((attr>>13)&3)*16+color;c=int.from_bytes(cram[palette*2:palette*2+2],'little');r=(c&7)*2;g=((c>>3)&7)*2;b=((c>>6)&7)*2
                        rgb=r<<12|(r>>3)<<11|g<<7|(g>>2)<<5|b<<1|b>>3
                        expected=(((rgb>>11)&31)*255//31,((rgb>>5)&63)*255//63,(rgb&31)*255//31)
                        compared+=1;bad+=image.getpixel((x,y))!=expected
                assert compared>0
                row.update(framebuffer_pixels_compared=compared,framebuffer_differing_pixels=bad)
        records[tag]=rows
    cases=[]
    for tag,rows in records.items():
        changed=next(f for f,row in rows.items() if row['cell']==0x66)
        hardware=next(f for f,row in rows.items() if row['physical_words']!=rows[2501]['physical_words'])
        cases.append(dict(system=tag,software_change_frame=changed,hardware_change_frame=hardware,publication_delay=hardware-changed))
    mismatched=sum(bool(row['framebuffer_differing_pixels']) for row in records['md'].values())
    assert records['sms'][2632]['software_words']==records['md'][2632]['software_words']
    source_words=bytes.fromhex(records['sms'][2632]['physical_words']);native_words=bytes.fromhex(records['md'][2632]['physical_words'])
    expected=bytearray()
    for n in range(0,8,2):
        w=int.from_bytes(source_words[n:n+2],'little')
        attr=((w>>11)&1)<<13|((w>>12)&1)<<15|((w>>10)&1)<<12|((w>>9)&1)<<11|16+(w&511)
        expected.extend(attr.to_bytes(2,'big'))
    assert native_words==expected
    result=dict(md_sha256=digest,source_sha256=sha((ROOT/'input/original.sms').read_bytes()),region=region,cases=cases,records=records,framebuffer_mismatching_frames=mismatched,passed=cases[0]['publication_delay']==cases[1]['publication_delay'] and not mismatched,diagnostic_only=baseline,scope='Controlled actor2B state8 repeatedly supplied until its own random branch changes one terrain cell, at normal new-game room95. Four terrain words and cell read every frame. Different decision frames are allowed; only subsequent software-to-VDP delay is compared. Native opaque BG_A pixels in the16x16 patch are independently decoded and compared with its framebuffer for133 frames; transparent pixels are excluded. Production ROMs/publication routines remain unchanged; this is not a natural combat, RNG, full-frame or full-timing equivalence test.')
    (ROOT/f'analysis/cell_publication_v{version:04d}{"-pal" if pal else ""}_report.json').write_text(json.dumps(result,indent=2)+'\n');print(cases,'incoherent frames',mismatched)
    if not baseline:assert result['passed']

if __name__=='__main__':main()
