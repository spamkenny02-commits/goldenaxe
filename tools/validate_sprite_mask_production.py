"""Compare actual playable225/226 sprite planes and entry-to-return mask time."""
import contextlib,ctypes as c,gzip,io,json,re,statistics,subprocess,sys
from run_core import ROOT,run
from archive_lossless_evidence import sha
from validate_playable_sprite_limit import symbols,reference
from validate_actor_tick import PRESSES

def old_symbols(descriptors=False):
    archive=ROOT/('analysis/first-dungeon-v0226' if descriptors else 'analysis/terrain-publication-v0225');m=json.loads((archive/'manifest.json').read_bytes());name='megadrive/out/release/symbol.txt'
    if name in m['files']:data=(archive/name).read_bytes();assert sha(data)==m['files'][name]
    else:
        item=m['compressed'][name];encoded=(archive/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];data=gzip.decompress(encoded);assert sha(data)==item['raw_sha256']
    path=ROOT/('validation/v0226-descriptor-symbols.txt' if descriptors else 'validation/v0225-mask-symbols.txt');path.write_bytes(data);return path

def main():
    descriptors='--descriptors' in sys.argv
    old=ROOT/('versions/v0226-36ad2e99/gaw-megadrive-v0226.bin' if descriptors else 'versions/v0225-71b56c3c/gaw-megadrive-v0225.bin');new=ROOT/'gaw-megadrive.bin';oldsy=old_symbols(descriptors)
    version=next(e['version'] for e in json.loads((ROOT/'versions/index.json').read_bytes()) if e['sha256']==sha(new.read_bytes()));stem='actor-descriptor' if descriptors else 'sprite-mask';root=ROOT/f'validation/{stem}-production-v{version:04d}';root.mkdir(exist_ok=True)
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_clock_libretro.dll';dll=c.CDLL(str(core));dll.gaw_md_config.argtypes=[c.c_uint,c.POINTER(c.c_uint)];dll.gaw_md_event_count.restype=c.c_uint;dll.gaw_md_event_data.restype=c.POINTER(c.c_uint)
    template=(ROOT/'validation/sms-vertical-check/ram_03120.bin').read_bytes()[0x600:0x630];results=[]
    for region in ['auto','pal']:
        period=3420*(313 if region=='pal' else 262)
        for label,count,y in [('hero_only',0,64),('overlap',12,64),('top_clip',1,5),('bottom_clip',1,205),('terminator',1,225)]:
            records={}
            for tag,rom,syfile in [('old',old,oldsy),('new',new,ROOT/'megadrive/out/release/symbol.txt')]:
                sy=symbols(syfile);full={m[2].split('.lto_priv.')[0]:int(m[1],16) for line in syfile.read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
                entry=full['prepare_world_sms_sprite_overflow'];start=full['update_hero_sprites_for_frame']
                if descriptors:ret=entry;entry=start
                else:
                    asm=subprocess.check_output([str(ROOT.parents[1]/'work/sgdk/bin/objdump.exe'),'-D','-b','binary','-m','m68k',f'--start-address={start}',f'--stop-address={start+4096}',str(rom)],text=True)
                    instructions=[(int(m[1],16),m[2]) for line in asm.splitlines() if(m:=re.match(r'\s*([0-9a-f]+):\s+(.*)',line))]
                    calls=[i for i,(_,text) in enumerate(instructions) if 'jsr' in text and f'(0x{entry:x})' in text];assert calls
                    ret=instructions[calls[0]+1][0]
                pcs=(c.c_uint*2)(entry,ret);dll.gaw_md_config(2,pcs)
                actors=bytearray(768)
                for slot in range(count):
                    e=bytearray(template);e[3]=1;e[4]=120;e[5]=0;e[6]=255;e[0x11]=y+(slot%3)*3 if count>1 else y;e[0x13]=16+slot*18;actors[slot*48:(slot+1)*48]=e
                writes=[w for f in range(3127,3141) for w in [(f,sy['world_actor_state'],bytes(actors)),(f,sy['world_loot_state'],bytes(336)),(f,sy['world_spell_state'],bytes(48)),(f,sy['world_clock_shift'],f.to_bytes(4,'big'))]]
                for name,value in [('hero_x',128<<8),('hero_y',144<<8),('hero_hurt',0),('hero_flags',3),('hero_state',1),('hero_counter',0),('hero_dx',0),('hero_dy',0),('hero_direction',1)]:writes.append((3127,sy[name],value.to_bytes(2,'big')))
                events=[];previous=0;planes={}
                def observe(f,r):
                    nonlocal previous
                    if f==3100:dll.gaw_md_config(2,pcs);previous=0
                    total=dll.gaw_md_event_count();p=dll.gaw_md_event_data()
                    if f>=3127:
                        for n in range(previous,total):events.append(dict(frame=f,pc=int(p[n*3]),cycles=int(p[n*3+1])))
                    previous=total
                def video(f,v):
                    if f>=3132:planes[f]=reference(v,0xf400,16)[0]
                folder=root/f'{region}-{label}-{tag}'
                with contextlib.redirect_stdout(io.StringIO()):run(rom,3140,folder,{3132,3140},PRESSES,core=core,ram_writes=writes,ram_observer=observe,vram_observer=video,core_options={'genesis_plus_gx_region_detect':region})
                spans=[];pending=None
                for e in events:
                    if e['pc']==entry:pending=e
                    elif pending is not None:
                        if pending['frame']>=3132:spans.append((e['frame']-pending['frame'])*period+e['cycles']-pending['cycles'])
                        pending=None
                (folder/'mask-timing.json').write_text(json.dumps(dict(entry=entry,return_pc=ret,events=events,elapsed_master_cycles=spans),indent=2)+'\n')
                assert len(spans)>=2 and all(t>0 for t in spans),(region,label,tag,spans)
                records[tag]=dict(planes=planes,spans=spans)
            assert records['old']['planes']==records['new']['planes'],(region,label,'sprite plane differs')
            before=statistics.median(records['old']['spans']);after=statistics.median(records['new']['spans'])
            if not descriptors or label=='overlap':assert after<before,(region,label,before,after)
            results.append(dict(region=region,case=label,identical_physical_sprite_frames=len(records['new']['planes']),sprite_pixels_compared=len(records['new']['planes'])*256*192,previous_timing_samples=len(records['old']['spans']),current_timing_samples=len(records['new']['spans']),previous_median_elapsed_master_cycles=before,current_median_elapsed_master_cycles=after,reduction_percent=round((before-after)*100/before,2)));print(results[-1],flush=True)
    report=dict(md_sha256=sha(new.read_bytes()),reference_sha256=sha(old.read_bytes()),passed=True,cases=results,timing_stage='scene_before_mask' if descriptors else 'mask_entry_to_return',scope='Actual old/new playable ROMs, same controlled frozen actor/hero setup after normal boot. Physical masked sprite pixels match in NTSC/PAL including clipping and terminator. Timings use the declared stage instruction boundaries and elapsed master cycles, potentially including interrupt work; not a global FPS percentage or a whole-game deadline proof.')
    prefix='actor_descriptor' if descriptors else 'sprite_mask'
    (ROOT/f'analysis/{prefix}_production_v{version:04d}_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
