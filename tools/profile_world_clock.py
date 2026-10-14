"""Observe natural new-game dialogue clock resets without changing either ROM."""
import contextlib,ctypes as c,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
    region='pal' if '--pal' in sys.argv else 'auto'
    suffix='-pal' if region=='pal' else ''
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_clock_libretro.dll'
    dll=c.CDLL(str(core));dll.gaw_timing_events.restype=c.POINTER(c.c_uint64)
    dll.gaw_timing_count.restype=c.c_uint
    symbols={m[2].split('.lto_priv.')[0]:int(m[1],16) for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    dll.gaw_md_config.argtypes=[c.c_uint,c.POINTER(c.c_uint)]
    dll.gaw_md_event_count.restype=c.c_uint
    dll.gaw_md_event_data.restype=c.POINTER(c.c_uint)
    watched={symbols[k]:k for k in ['wait_dialog_continue','render_dialogue_text','enter_initial_room']}
    watch=(c.c_uint*len(watched))(*watched)
    results={};events=[];native_events=[]
    for tag,path in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
        rows=[];previous=[0];native_previous=[0]
        dll.gaw_md_config(len(watched),watch)
        def observe(frame,raw):
            if tag=='sms':
                if frame==1:dll.gaw_timing_reset();previous[0]=0
                count=dll.gaw_timing_count();pointer=dll.gaw_timing_events()
                for n in range(previous[0],count):
                    pc,cycles,irq,room,clock,hl,de,bc=[int(pointer[n*8+j]) for j in range(8)]
                    if pc in [0x07ee,0x07f4,0x07f6,0x0803,0x0805,0x16d0,0x190b,0x2279,0x1e4e,0x7444,0x7447,0x7451,0x779b,0x11b7,0x175f]:
                        events.append(dict(frame=frame,pc=pc,clock=clock,hl=hl,master_cycles=cycles,irq_master_cycles=irq))
                previous[0]=count
                rows.append(dict(frame=frame,clock=raw[0x2f],state=raw[0x1d],room=int.from_bytes(raw[0xb9:0xbb],'little')))
            else:
                count=dll.gaw_md_event_count();pointer=dll.gaw_md_event_data()
                for n in range(native_previous[0],count):
                    pc,cycles,sp=[int(pointer[n*3+j]) for j in range(3)]
                    native_events.append(dict(frame=frame,pc=pc,function=watched[pc],master_cycles_in_frame=cycles,sp=sp))
                native_previous[0]=count
                def val(k,size=2):
                    a=symbols[k]&65535;return int.from_bytes(bytes(raw[(a+i)^1] for i in range(size)),'big')
                rows.append(dict(frame=frame,clock=(val('vtimer',4)-val('world_clock_shift',4))&255,state=val('game_state'),room=val('room_id'),vtimer=val('vtimer',4),shift=val('world_clock_shift',4)))
        with contextlib.redirect_stdout(io.StringIO()):
            run(path,2600,ROOT/f'validation/world-clock-{tag}{suffix}',set(),([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],core=core,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
        results[tag]=rows
        print(tag,region,'observed',flush=True)
    resets=[e for e in events if e['pc'] in [0x07f4,0x0803]]
    assert resets and all(e['hl']==0xc02f for e in resets)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),region=region,production_roms_unmodified=True,ram_injections=False,source_events=events,native_events=native_events,source_reset_registers_verified=True,traces=results,limits=['Natural scripted new-game input only; NPC/merchant and Continue paths not covered.','Read-only PC/clock observers; selected function entries only, no complete native cycle accounting.'])
    (ROOT/f'validation/world_clock{suffix}_profile.json').write_text(json.dumps(report,indent=2)+'\n')
    print('reset events',resets,flush=True)

if __name__=='__main__':main()
