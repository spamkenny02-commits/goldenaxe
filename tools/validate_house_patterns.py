"""Compare actual house animation patterns with original SMS IRQ publication."""
import contextlib,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from audit_item_reward_visuals import sms_pixels,md_pixels

def main():
    baseline='--baseline' in sys.argv
    md=ROOT/('versions/v0096-0faff7e5/gaw-megadrive-v0096.bin' if baseline else 'gaw-megadrive.bin')
    symbols=ROOT/('analysis/house-animation-baseline-v0096/symbol.txt' if baseline else 'megadrive/out/release/symbol.txt')
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in symbols.read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
    cases=[]
    for region in ['auto','pal']:
      for name,route,room in [('first_house',[(2950,2958,7),(3000,3020,4)],0),('second_house',[(2950,2965,5),(3000,3023,6),(3050,3061,4),(3100,3110,4)],2)]:
        clock=[0];base=[0];records={}
        for tag,rom in [('sms',ROOT/'input/original.sms'),('md',md)]:
            rows={};words={}
            def observe(f,r):
                if tag=='sms' and f==3299:clock[0]=r[0x2f];base[0]=r[0x9e0]
                if f in [3300,3420]:
                    actual=int.from_bytes(r[0xb9:0xbb],'little') if tag=='sms' else int.from_bytes(bytes(r[(sy['room_id']+i)^1] for i in range(2)),'big')
                    assert actual==room,(name,tag,f,actual)
            def vram(f,v):
                if 3303<=f<=3420:rows[f]=[sms_pixels(v,base[0]+n) if tag=='sms' else md_pixels(v,16+base[0]+n) for n in range(4)]
            writes=[] if tag=='sms' else [(3300,sy['world_clock_shift'],bytes(4)),(3300,sy['vtimer'],clock[0].to_bytes(4,'big'))]
            inputs=([(200,220,0)] if tag=='sms' else [])+PRESSES[:11]+route
            with contextlib.redirect_stdout(io.StringIO()):run(rom,3420,ROOT/f'validation/house-patterns-{name}-{region}-{tag}{"-baseline" if baseline else ""}',set(),inputs,ram_writes=writes,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
            records[tag]=rows
        diffs=[f for f in records['sms'] if records['sms'][f]!=records['md'][f]]
        if not baseline:assert not diffs,(name,region,diffs[:12])
        assert len({json.dumps(v) for v in records['sms'].values()})==2,'Animation did not change'
        cases.append(dict(name=name,region=region,room=room,source_animation_tile=base[0],frames_compared=118,difference_frames=diffs,frames_exact=118-len(diffs)))
        print(name,region,'differing frames',len(diffs),flush=True)
    result=dict(md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=cases,diagnostic_only=baseline,full_game_ported=False,limits=['Two normal village-house routes PAL/NTSC; one native clock alignment at frame 3300. No ongoing animation injections.','Four actual animated VRAM tile pixel arrays compared. Complete room framebuffer, all house rooms and global timing remain unverified.'])
    (ROOT/f'validation/house_patterns{"_baseline" if baseline else ""}_report.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
