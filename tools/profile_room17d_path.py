"""Read-only traces of the long DOWN hold after room-clear return to 17D."""
import ctypes as c,hashlib,json,re,sys
import run_core
from actor_reference import ROOT
import validate_room_clear_gameplay as scenario

def main():
    pal='--pal' in sys.argv;tag_suffix='-pal' if pal else ''
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    real=run_core.run;traces={};events=[]
    timing='--timing' in sys.argv
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_key_timing_libretro.dll'
    if timing:
        dll=c.CDLL(str(core));dll.gaw_timing_events.restype=c.POINTER(c.c_uint64)
    def profile(path,frames,out,captures,presses,**kwargs):
        if 'clear-gameplay-17d-' not in str(out):raise StopIteration
        tag='sms' if path.suffix=='.sms' else 'md';rows=[];observe=kwargs['ram_observer']
        def watch(frame,raw):
            observe(frame,raw)
            if tag=='sms' and timing:
                if frame==3550:dll.gaw_timing_reset()
                if frame==3750:
                    p=dll.gaw_timing_events();events.extend([int(p[n*8+i]) for i in range(8)] for n in range(dll.gaw_timing_count()))
            if frame<3550:return
            if tag=='sms':
                def val(a):return int.from_bytes(raw[a:a+2],'little')
                row=dict(frame=frame,room=val(0xb9),game=raw[0x1d],hero_state=raw[0x301],x=val(0x312),y=val(0x310),counter=raw[0x304],hurt=raw[0x305],dx=val(0x316),dy=val(0x314),scan=raw[0xaa],phase=raw[0xab])
                tilemap=raw[0x1600:0x1b00];cells=raw[0x1c00:0x1ca0]
            else:
                def data(k,n,off=0):
                    a=sy[k]+off;return bytes(raw[(a+i)^1] for i in range(n))
                def val(k):return int.from_bytes(data(k,2),'big')
                row={k:val(v) for k,v in dict(room='room_id',game='game_state',hero_state='hero_state',x='hero_x',y='hero_y',counter='hero_counter',hurt='hero_hurt',dx='hero_dx',dy='hero_dy').items()};row['loading']=val('transition_loading_frames');row['stage']=val('transition_stage');row['frame']=frame;row['scan']=data('dungeon_animation_scan',1)[0];row['phase']=data('dungeon_animation_phase',1)[0]
                tilemap=data('sms_vram',1280,0x3800);cells=data('scratch',160,0x800)
            x=row['x']>>8;y=row['y']>>8
            offset=(((y+0)&248)*8)+(((x-8)>>2)&62)
            row['below_tiles']=tilemap[offset:offset+4].hex();row['cells']=cells.hex() if frame in (3610,3650,3700,3750) else None
            rows.append(row)
        kwargs['ram_observer']=watch
        if tag=='sms' and timing:kwargs['core']=core
        presses=[(a,3700 if a==3550 else b,k) for a,b,k in presses]
        result=real(path,frames,ROOT/f'validation/{tag}-room17d-long{tag_suffix}',set(captures)|{3610,3650,3700},presses,**kwargs)
        traces[tag]=rows;return result
    run_core.run=profile;sys.argv=['validate_room_clear_gameplay.py','--cross']+(['--pal'] if pal else [])
    failure=None
    try:scenario.main()
    except StopIteration:pass
    except AssertionError as exc:failure=str(exc)
    assert set(traces)=={'sms','md'}
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),research_core_sha256=hashlib.sha256(core.read_bytes()).hexdigest() if timing else None,region='pal' if pal else 'ntsc',scenario_assertion=failure,traces=traces,source_timing_events=events)
    (ROOT/f'analysis/room17d_long_profile{tag_suffix}.json').write_text(json.dumps(report,indent=2)+'\n')
    for tag,rows in traces.items():
        print(tag,[(r['frame'],hex(r['room']),r['y']//256,r['hero_state'],r['counter']) for r in rows if r['frame'] in (3610,3650,3700,3750)])
if __name__=='__main__':main()
