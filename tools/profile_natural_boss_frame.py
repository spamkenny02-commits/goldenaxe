"""Read-only 68000 entry timestamps around the natural boss-death frame miss."""
import ctypes as c,json,re
import natural_dungeon_combat as game
from run_core import ROOT
from archive_lossless_evidence import sha

def main():
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_clock_libretro.dll';dll=c.CDLL(str(core))
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16) for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    wanted=['world_vint','prepare_world_sms_sprite_overflow','update_hero_sprites_for_frame','tick_world_simulation','tick_world_actors.constprop.0']
    watched={v:k for k,v in sy.items() if k in wanted}
    dll.gaw_md_config.argtypes=[c.c_uint,c.POINTER(c.c_uint)];dll.gaw_md_event_data.restype=c.POINTER(c.c_uint);dll.gaw_md_event_count.restype=c.c_uint
    pcs=(c.c_uint*len(watched))(*watched);dll.gaw_md_config(len(watched),pcs)
    original=game.run;events=[];metrics=[];previous=0;folder=None;death_at=None
    def wrapped(*args,**kwargs):
        nonlocal folder
        folder=args[2];observer=kwargs['ram_observer'];kwargs['core']=core
        def observe(f,r):
            nonlocal previous,death_at
            observer(f,r)
            data=lambda name,n:bytes(r[((sy[name]&65535)+i)^1] for i in range(n))
            if death_at is None and data('world_actor_state',1)[0]==7:death_at=f
            if death_at is not None and f==death_at+60:dll.gaw_md_config(len(watched),pcs);previous=0
            count=dll.gaw_md_event_count();p=dll.gaw_md_event_data()
            if death_at is not None and death_at+80<=f<=death_at+110:
                for n in range(previous,count):
                    pc,cycles,sp=[int(p[n*3+j]) for j in range(3)];events.append(dict(frame=f,function=watched[pc],master_cycles=cycles,sp=sp))
                metrics.append(dict(frame=f,timer=data('world_actor_state',48)[0x28],jobs=int.from_bytes(data('world_tile_job_count',2),'big'),sprites=int.from_bytes(data('world_video_sat_count',2),'big'),pending=int.from_bytes(data('world_video_pending',2),'big'),preparing=data('world_video_preparing',1)[0]))
                args[3].add(f)
            previous=count
        kwargs['ram_observer']=observe
        return original(*args,**kwargs)
    game.run=wrapped;game.main()
    result=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),core_sha256=sha(core.read_bytes()),watched=watched,events=events,metrics=metrics,read_only_observation=True)
    (folder/'frame_profile.json').write_text(json.dumps(result,indent=2)+'\n');print(metrics)

if __name__=='__main__':main()
