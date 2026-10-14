"""Read-only natural first-page preparation and word publication timings."""
import contextlib,ctypes as c,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
    pal='--pal' in sys.argv;suffix='-pal' if pal else ''
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_clock_libretro.dll'
    dll=c.CDLL(str(core));dll.gaw_timing_events.restype=c.POINTER(c.c_uint64);dll.gaw_timing_count.restype=c.c_uint
    dll.gaw_md_event_data.restype=c.POINTER(c.c_uint);dll.gaw_md_event_count.restype=c.c_uint
    dll.gaw_md_config.argtypes=[c.c_uint,c.POINTER(c.c_uint)]
    symbols={m[2].split('.lto_priv.')[0]:int(m[1],16) for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    watched={v:k for k,v in symbols.items() if k in ['render_dialogue_text','upload_dialog_bitmap','draw_dialog_glyph','wait_dialog_continue','draw_map','draw_frame']}
    pcs=(c.c_uint*len(watched))(*watched);dll.gaw_md_config(len(watched),pcs)
    selected=[0x7444,0x779b,0x0524,0x0554,0x057d,0x0595,0x059b,0x0666,0x066b,0x0677,0x06d6,0x0786,0x078e,0x07b3,0x0914,0x07ee,0x07f4]
    results={}
    for tag,path in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
        events=[];rows=[];previous=[0];patterns={};valid={}
        def observe(frame,raw):
            if frame==1440:
                if tag=='sms':dll.gaw_timing_reset()
                previous[0]=0
            if frame<1440:return
            if tag=='sms':
                count=dll.gaw_timing_count();p=dll.gaw_timing_events()
                for n in range(previous[0],count):
                    pc,cycles,irq,room,clock,hl,de,bc=[int(p[n*8+j]) for j in range(8)]
                    if pc in selected:events.append(dict(frame=frame,pc=pc,clock=clock,hl=hl,de=de,bc=bc,master_cycles=cycles,irq_master_cycles=irq))
                bitmap=raw[0x1100:0x1510]
                rows.append(dict(frame=frame,bitmap_sha256=hashlib.sha256(bitmap).hexdigest(),position=raw[0x1cc8:0x1ccc].hex(),text_pointer=int.from_bytes(raw[0x1cc0:0x1cc2],'little')))
            else:
                count=dll.gaw_md_event_count();p=dll.gaw_md_event_data()
                for n in range(previous[0],count):
                    pc,cycles,sp=[int(p[n*3+j]) for j in range(3)]
                    if frame>=1440:events.append(dict(frame=frame,pc=pc,function=watched[pc],master_cycles_in_frame=cycles,sp=sp))
                a=symbols['scratch']&65535;bitmap=bytes(raw[(a+n)^1] for n in range(1040))
                rows.append(dict(frame=frame,bitmap_sha256=hashlib.sha256(bitmap).hexdigest()))
            previous[0]=count
        def vram(frame,v):
            if frame<1489:return
            if tag=='sms':
                bitmap=bytes(v[0x2001+n*4] for n in range(1040))
                valid[frame]=all(v[0x2000+n*4]==255 and v[0x2002+n*4]==v[0x2003+n*4]==0 for n in range(1040))
            else:
                bitmap=bytearray();valid[frame]=True
                for row in range(1040):
                    start=(272+row//8)*32+(row%8)*4;value=0
                    for x in range(8):
                        color=(v[(start+x//2)^1]>>(4 if x%2==0 else 0))&15
                        if color not in [1,3]:valid[frame]=False
                        value|=((color>>1)&1)<<(7-x)
                    bitmap.append(value)
            patterns[frame]=hashlib.sha256(bitmap).hexdigest()
        with contextlib.redirect_stdout(io.StringIO()):run(path,1620,ROOT/f'validation/dialogue-preparation-{tag}{suffix}',set(),([(200,220,0)] if tag=='sms' else [])+PRESSES[:6],core=core,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':'pal' if pal else 'auto'})
        results[tag]=dict(events=[x for x in events if x['frame']>=1489],traces=rows,hardware_bitmap_sha256=patterns,hardware_bitmap_colors_valid=valid)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),region='pal' if pal else 'auto',diagnostic_only=True,production_roms_unmodified=True,ram_injections=False,results=results,limits=['One natural name A and scripted confirmation frame per region.','End-of-frame bitmap hashes and selected entry PCs; no full native instruction accounting.'])
    (ROOT/f'validation/dialogue_preparation{suffix}_profile.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['region'],'source publications',[(x['frame'],hex(x['pc'])) for x in results['sms']['events'] if x['pc'] in [0x7444,0x059b,0x0786,0x07f4]])
    print('native publications',[(x['frame'],x['function']) for x in results['md']['events'] if x['function'] in ['render_dialogue_text','upload_dialog_bitmap','wait_dialog_continue']])

if __name__=='__main__':main()
