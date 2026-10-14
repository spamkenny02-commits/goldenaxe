"""Read-only confirmation/fade entry timing for the free healer regression."""
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
    sy={m[2]:int(m[1],16) for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    simple={k.split('.lto_priv.')[0]:v&65535 for k,v in sy.items()}
    watched={v:k for k,v in sy.items() if k.startswith('fade_world_palette')}
    watch=(c.c_uint*len(watched))(*watched);dll.gaw_md_config(len(watched),watch)
    events={}
    inputs=PRESSES[:11]+[(2950,2958,7),(3000,3020,4),(3350,3500,4),(3700,3710,8)]
    for tag,path in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
        previous=[0];rows=[]
        if tag=='sms':writes=[(3300,0x310,(88<<8).to_bytes(2,'little')+(216<<8).to_bytes(2,'little')),(3300,0x30a,b'\0'),(3300,0x318,b'\x09'),(3300,0xda,bytes([24,11,24,87]))]
        else:writes=[(3300,simple[k],v.to_bytes(2,'big')) for k,v in [('hero_x',216<<8),('hero_y',88<<8),('hero_direction',0),('hero_health',9),('hero_max_health',24),('hero_magic',11),('hero_max_magic',24),('hero_gold',87)]]
        def observe(frame,raw):
            if tag=='sms':
                if frame==3600:dll.gaw_timing_reset();previous[0]=0
                if frame<3600:return
                count=dll.gaw_timing_count();p=dll.gaw_timing_events()
                for n in range(previous[0],count):
                    vals=[int(p[n*8+j]) for j in range(8)]
                    if vals[0] in [0x6147,0x76c3,0x0b12,0x0b24]:rows.append(dict(frame=frame,pc=vals[0],master_cycles=vals[1],irq_master_cycles=vals[2]))
            else:
                count=dll.gaw_md_event_count();p=dll.gaw_md_event_data()
                for n in range(previous[0],count):
                    pc,cycles,sp=[int(p[n*3+j]) for j in range(3)]
                    rows.append(dict(frame=frame,pc=pc,function=watched[pc],master_cycles_in_frame=cycles))
            previous[0]=count
        with contextlib.redirect_stdout(io.StringIO()):run(path,3800,ROOT/f'validation/healer-fade-profile-{tag}{suffix}',set(),([(200,220,0)] if tag=='sms' else [])+inputs,core=core,ram_observer=observe,ram_writes=writes,core_options={'genesis_plus_gx_region_detect':'pal' if pal else 'auto'})
        events[tag]=rows
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),events=events,limits=['Controlled free-healer position/stats; source/native instruction entry observations only.'])
    report['region']='pal' if pal else 'auto'
    (ROOT/f'validation/healer_fade{suffix}_profile.json').write_text(json.dumps(report,indent=2)+'\n');print(events)

if __name__=='__main__':main()
