"""Observe source intermediate-page reset, blink and confirmation."""
import contextlib,ctypes as c,io,json,sys
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols
from archive_lossless_evidence import sha

def main():
    diagnostic='--diagnostic' in sys.argv;rom=ROOT/'gaw-megadrive.bin';digest=sha(rom.read_bytes())
    version=next(e['version'] for e in json.loads((ROOT/'versions/index.json').read_bytes()) if e['sha256']==digest)
    sy=symbols(ROOT/'megadrive/out/release/symbol.txt');core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_clock_libretro.dll';dll=c.CDLL(str(core))
    dll.gaw_timing_events.restype=c.POINTER(c.c_uint64);dll.gaw_timing_count.restype=c.c_uint
    dll.gaw_md_event_data.restype=c.POINTER(c.c_uint);dll.gaw_md_event_count.restype=c.c_uint;dll.gaw_md_config.argtypes=[c.c_uint,c.POINTER(c.c_uint)]
    results=[]
    for region in ['auto','pal']:
        data={};starts={};evidence={}
        for tag,path in [('sms',ROOT/'input/original.sms'),('md',rom)]:
            rows={};events=[];previous=[0];pins=(c.c_uint*1)(0)
            # Symbol table is24-bit ROM addresses, while symbols() returns RAM
            # offsets. Fetch the function's actual ROM address separately.
            if tag=='md':
                import re
                address=next(int(m[1],16) for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)) and m[2].split('.lto_priv.')[0]=='wait_dialog_continue')
                pins=(c.c_uint*1)(address)
            dll.gaw_md_config(1,pins)
            def observe(f,r):
                if tag=='sms':
                    if f==1:dll.gaw_timing_reset()
                    count=dll.gaw_timing_count();p=dll.gaw_timing_events()
                    for n in range(previous[0],count):
                        pc=int(p[n*8])
                        if pc in [0x7f4,0x803]:events.append(dict(frame=f,pc=pc))
                    previous[0]=count;clock=r[0x2f]
                else:
                    count=dll.gaw_md_event_count();p=dll.gaw_md_event_data()
                    for n in range(previous[0],count):events.append(dict(frame=f,pc=int(p[n*3])))
                    previous[0]=count
                    value=lambda name:int.from_bytes(bytes(r[(sy[name]+i)^1] for i in range(4)),'big')
                    clock=(value('vtimer')-value('world_clock_shift'))&255
                if 1450<=f<=2250:rows[f]=dict(clock=clock)
            def video(f,v):
                if f not in rows:return
                rows[f]['marker']=v[0x3cde] if tag=='sms' else ((int.from_bytes(v[0xe000+21*128+30:0xe000+21*128+32],'little')&2047)-16)&255
            folder=ROOT/f'validation/dialogue-waits-v{version:04d}/opening-{region}-{tag}'
            with contextlib.redirect_stdout(io.StringIO()):run(path,2250,folder,set(),([(200,220,0)] if tag=='sms' else [])+PRESSES[:6]+[(2200,2210,8)],ram_observer=observe,vram_observer=video,core=core,core_options={'genesis_plus_gx_region_detect':region})
            start=next(e['frame'] for e in events if tag=='md' or e['pc']==0x7f4);starts[tag]=start;data[tag]=rows
            retained=dict(start=start,events=events,rows=rows);p=folder/'observations.json';p.write_text(json.dumps(retained,indent=2)+'\n');evidence[tag]=dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p.read_bytes()))
        aligned=[dict(offset=n,sms=data['sms'][starts['sms']+n],md=data['md'][starts['md']+n]) for n in range(64)]
        clock_bad=[r['offset'] for r in aligned if r['sms']['clock']!=r['md']['clock']];marker_bad=[r['offset'] for r in aligned if r['sms']['marker']!=r['md']['marker']]
        confirm={tag:{f:rows[f] for f in [2200,2201]} for tag,rows in data.items()}
        good=not clock_bad and not marker_bad and all(confirm[tag][2200]['clock']==255 and confirm[tag][2200]['marker']==252 and confirm[tag][2201]['clock']==0 for tag in ['sms','md'])
        results.append(dict(region=region,starts=starts,relative_frames_compared=64,clock_mismatch_offsets=clock_bad,marker_mismatch_offsets=marker_bad,confirmation=confirm,passed=good,evidence=evidence));print(region,'page wait',good,'clock mismatches',len(clock_bad),'marker mismatches',len(marker_bad),flush=True)
    report=dict(md_sha256=digest,source_sha256=sha((ROOT/'input/original.sms').read_bytes()),passed=all(r['passed'] for r in results),diagnostic_only=diagnostic,cases=results,scope='Natural opening page:64 aligned relative RAM-clock and physical marker frames; confirmation FF and next IRQ0 at2200/2201. Page starts differ and are not claimed synchronized. No whole-world/source IRQ clock proof.')
    (ROOT/f'analysis/dialogue_waits_v{version:04d}_report.json').write_text(json.dumps(report,indent=2)+'\n')
    if not diagnostic:assert report['passed']

if __name__=='__main__':main()
