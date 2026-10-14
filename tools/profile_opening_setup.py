"""Observe original name-to-story palette/font/fade stages and native setup."""
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
    watched={v:k for k,v in symbols.items() if k in ['render_dialogue_text','finish_name'] or k.startswith(('fade_world_palette','fade_opening_palette'))}
    pcs=(c.c_uint*len(watched))(*watched);dll.gaw_md_config(len(watched),pcs)
    results={}
    selected=[0x1197,0x119a,0x119d,0x11a5,0x11a8,0x11ab,0x0aa4,0x0b12,0x0b24,0x1deb,0x1e1f,0x032a,0x7444,0x779b]
    for tag,path in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
        events=[];rows=[];previous=[0]
        def observe(frame,raw):
            if tag=='sms':
                if frame==1440:dll.gaw_timing_reset();previous[0]=0
                if frame<1440:return
                count=dll.gaw_timing_count();p=dll.gaw_timing_events()
                for n in range(previous[0],count):
                    pc,cycles,irq,room,clock,hl,de,bc=[int(p[n*8+j]) for j in range(8)]
                    if pc in selected:events.append(dict(frame=frame,pc=pc,clock=clock,hl=hl,de=de,bc=bc,master_cycles=cycles,irq_master_cycles=irq))
                rows.append(dict(frame=frame,palette=list(raw[0x1ca0:0x1cc0]),target=list(raw[0x1cc0:0x1ce0]),clock=raw[0x2f],state=raw[0x1d]))
            else:
                count=dll.gaw_md_event_count();p=dll.gaw_md_event_data()
                for n in range(previous[0],count):
                    pc,cycles,sp=[int(p[n*3+j]) for j in range(3)]
                    if frame>=1440:events.append(dict(frame=frame,pc=pc,function=watched[pc],master_cycles_in_frame=cycles))
                if frame>=1440:
                    def data(k,n):
                        a=symbols[k]&65535;return bytes(raw[(a+i)^1] for i in range(n))
                    colors=data('sms_palette',64)
                    rows.append(dict(frame=frame,palette=[int.from_bytes(colors[n:n+2],'big') for n in range(0,64,2)],clock=(int.from_bytes(data('vtimer',4),'big')-int.from_bytes(data('world_clock_shift',4),'big'))&255))
            previous[0]=count
        folder=ROOT/f'validation/opening-setup-{tag}{suffix}'
        with contextlib.redirect_stdout(io.StringIO()):run(path,1610,folder,set(range(1449,1491))|{1500,1510},([(200,220,0)] if tag=='sms' else [])+PRESSES[:6],core=core,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':'pal' if pal else 'auto'})
        cram={frame:[int.from_bytes((folder/f'cram_{frame:05}.bin').read_bytes()[n*2:n*2+2],'little') for n in range(32)] for frame in range(1449,1491)}
        results[tag]=dict(events=events,traces=rows,cram=cram)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),region='pal' if pal else 'auto',production_roms_unmodified=True,ram_injections=False,results=results,limits=['One natural name A and scripted new-game sequence per region.','Selected entry observations and end-of-frame RAM palettes; no full instruction trace.'])
    (ROOT/f'validation/opening_setup{suffix}_profile.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['region'],results['sms']['events']);print('native',results['md']['events'])

if __name__=='__main__':main()
