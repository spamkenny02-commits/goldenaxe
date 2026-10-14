"""Compare natural intro actor states at matching source counter/clock phases."""
import contextlib, hashlib, io, json, re
from collections import Counter
from actor_reference import ROOT
from run_core import run


def main():
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    regions={}
    for pal in (False,True):
        systems={}
        for md in (False,True):
            tag='md' if md else 'sms'; rows=[]; current=None
            def observe(frame, raw):
                nonlocal current
                current=None
                if md:
                    d=bytearray(raw);d[::2],d[1::2]=raw[1::2],raw[::2]
                    def word(name, index=0):
                        off=sy[name]+index*2
                        return int.from_bytes(d[off:off+2],'big')
                    scene=word('intro_scene')
                    if scene not in (2,3): return
                    count=9 if scene==2 else 6
                    # SGDK vtimer is a 32-bit big-endian counter.
                    counter=word('intro_counter'); clock=word('vtimer',1)&3
                    states=[word('intro_actor_state',i)+1 for i in range(count)]
                    poses=[word('intro_actor_pose',i) for i in range(count)]
                else:
                    callback=int.from_bytes(raw[0x1cec:0x1cee],'little')
                    scene={0x1055:2,0x104a:3}.get(callback)
                    if not scene: return
                    count=9 if scene==2 else 6
                    counter=raw[0x1ce2];clock=raw[0x2f]&3
                    states=[raw[0x300+i*48] for i in range(count)]
                    poses=[raw[0x30b+i*48] for i in range(count)]
                current=dict(frame=frame,scene=scene,counter=counter,clock=clock,states=states,poses=poses)
                rows.append(current)
            def vram(frame, v):
                if current is None: return
                sprites=[]
                if md:
                    index=0;seen=set()
                    while index not in seen and len(seen)<80:
                        seen.add(index);p=0xf400+index*8
                        y=int.from_bytes(v[p:p+2],'little')&511
                        x=int.from_bytes(v[p+6:p+8],'little')&511
                        tile=int.from_bytes(v[p+4:p+6],'little')&2047
                        if x and y: sprites.append((x-128,y-128-17,tile-272))
                        index=int.from_bytes(v[p+2:p+4],'little')&127
                        if not index: break
                else:
                    for i in range(64):
                        y=v[0x3f00+i]
                        if y==208: break
                        sprites.append((v[0x3f80+i*2],y if y<208 else y-256,v[0x3f81+i*2]))
                current['sprites']=tuple(sprites)
            with contextlib.redirect_stdout(io.StringIO()):
                run(ROOT/('gaw-megadrive.bin' if md else 'input/original.sms'),6000,ROOT/(f'validation/{tag}-intro-actors'+('-pal' if pal else '')),set(),[],skip_intro=False,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':'pal' if pal else 'auto'})
            systems[tag]=rows
        source={}
        for r in systems['sms']:
            source.setdefault((r['scene'],r['counter'],r['clock']),set()).add((tuple(r['states']),tuple(r['poses'])))
        sprite_source={}
        for r in systems['sms']:
            sprite_source.setdefault((r['scene'],r['counter'],r['clock'],tuple(r['states']),tuple(r['poses'])),set()).add(r['sprites'])
        sprite_matches=0;sprite_differences=[]
        matches=[];differences=[];missing=[]
        for r in systems['md']:
            key=(r['scene'],r['counter'],r['clock'])
            if key not in source: missing.append(r);continue
            if (tuple(r['states']),tuple(r['poses'])) in source[key]: matches.append(r)
            else: differences.append(dict(native=r,source=[dict(states=s,poses=p) for s,p in source[key]]))
            sprite_key=key+(tuple(r['states']),tuple(r['poses']))
            if r['sprites'] in sprite_source.get(sprite_key,set()): sprite_matches+=1
            else: sprite_differences.append(dict(native=r,source=list(sprite_source.get(sprite_key,set()))))
        assert not differences and not missing, 'Logical animation state differs from source at matching phase'
        regions['pal' if pal else 'ntsc']=dict(source_samples=len(systems['sms']),native_samples=len(systems['md']),matching_samples=len(matches),difference_count=len(differences),missing_count=len(missing),differences=differences[:30],missing=missing[:10],sprite_matching_samples=sprite_matches,sprite_difference_count=len(sprite_differences),sprite_differences=sprite_differences[:30],sprite_differences_by_scene=dict(Counter(r['native']['scene'] for r in sprite_differences)),sprite_differences_by_clock_phase=dict(Counter(r['native']['clock'] for r in sprite_differences)))
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),no_ram_mutations=True,natural_boot=True,regions=regions,hardware_sprite_pixels_verified=False,hardware_sat_equivalence_verified=False,comparison_key='scene, 8-bit animation counter, clock modulo 4, logical states/poses; not absolute frame alignment',vtimer_width_bytes=4)
    (ROOT/'analysis/intro_actors_profile.json').write_text(json.dumps(report,indent=2)+'\n')
    print({region:{k:v for k,v in data.items() if k not in ('differences','missing','sprite_differences')} for region,data in regions.items()})


if __name__=='__main__': main()
