"""Compare four natural opening-dialogue scroll poses against original VRAM."""
import contextlib,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def sha(data):return hashlib.sha256(data).hexdigest()

def shifted(bitmap,count):
    return b''.join(bitmap[x*40+count:(x+1)*40]+bytes(count) for x in range(26))

def main():
    baseline='--baseline' in sys.argv
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    cases=[]
    for region in ['auto','pal']:
        records={}
        for tag,path in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
            bitmaps={};patterns={}
            def observe(frame,raw):
                if not 2199<=frame<=2250:return
                if tag=='sms':bitmap=bytes(raw[0x1100:0x1510])
                else:
                    a=sy['scratch'];bitmap=bytes(raw[(a+i)^1] for i in range(1040))
                bitmaps[frame]=bitmap
            def vram(frame,v):
                if not 2199<=frame<=2250:return
                if tag=='sms':
                    assert all(v[0x2000+n*4]==255 and v[0x2002+n*4]==v[0x2003+n*4]==0 for n in range(1040))
                    patterns[frame]=bytes(v[0x2001+n*4] for n in range(1040))
                else:
                    out=bytearray()
                    for row in range(1040):
                        start=(272+row//8)*32+(row%8)*4
                        value=0
                        for x in range(8):
                            color=(v[(start+x//2)^1]>>(4 if x%2==0 else 0))&15
                            assert color in [1,3],(frame,row,x,color)
                            value|=((color>>1)&1)<<(7-x)
                        out.append(value)
                    patterns[frame]=bytes(out)
            with contextlib.redirect_stdout(io.StringIO()):
                run(path,2250,ROOT/f'validation/dialogue-scroll-{region}-{tag}',set(),([(200,220,0)] if tag=='sms' else [])+PRESSES[:6]+[(2200,2210,8)],ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
            records[tag]=dict(bitmaps=bitmaps,patterns=patterns)
        base=records['sms']['bitmaps'][2199]
        assert base==records['md']['bitmaps'][2199]
        poses=[]
        for shift in [2,5,8,10]:
            expected=shifted(base,shift)
            matching={tag:{kind:[f for f,b in values.items() if b==expected] for kind,values in rec.items()} for tag,rec in records.items()}
            assert matching['sms']['patterns'],(region,shift,'source complete pose not observed',matching)
            if not baseline:
                assert matching['md']['patterns'],(region,shift,'native complete pose missing',matching)
                assert matching['sms']['patterns'][0]==matching['md']['patterns'][0],(region,shift,'first presentation frame',matching)
                assert matching['sms']['patterns']==matching['md']['patterns'],(region,shift,'complete pose duration',matching)
            poses.append(dict(cumulative_shift=shift,bitmap_sha256=sha(expected),matching_frames=matching))
        cases.append(dict(region=region,poses=poses,all_native_vram_poses_present=all(p['matching_frames']['md']['patterns'] for p in poses),first_presentation_frames_exact=all(p['matching_frames']['md']['patterns'] and p['matching_frames']['sms']['patterns'][0]==p['matching_frames']['md']['patterns'][0] for p in poses),complete_pose_frame_lists_exact=all(p['matching_frames']['sms']['patterns']==p['matching_frames']['md']['patterns'] for p in poses),all_pattern_pixel_colors_verified=True))
        print(region,'poses',[(p['cumulative_shift'],p['matching_frames']) for p in poses],flush=True)
    report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha((ROOT/'input/original.sms').read_bytes()),cases=cases,production_roms_unmodified=True,ram_injections=False,full_game_ported=False,limits=['Natural first page scroll only; four complete pattern poses including their observed durations, without full framebuffer equivalence.','Partial upload frames, subsequent word timing, whole dialogue timing and suppressed IRQ counts remain unproven or different.'])
    (ROOT/f'validation/dialogue_scroll{"_baseline" if baseline else ""}_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
