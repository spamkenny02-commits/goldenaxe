"""Compare normal/fast ground movement with original SMS execution."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from audit_item_reward_visuals import sms_pixels,md_pixels

def main():
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
    fields=[('hero_y',0x310,2),('hero_x',0x312,2),('hero_dy',0x314,2),('hero_dx',0x316,2),('hero_counter',0x304,1),('hero_animation',0x30b,1),('hero_direction',0x30a,1),('hero_state',0x301,1),('hero_terrain_context',0x41,1)]
    cases=[]
    for region in ['auto','pal']:
      for fast in [0,1]:
       for direction in range(4):
        records={};patterns={};clock=[0]
        for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
            items=bytearray(17);items[0]=1;items[14]=fast
            if tag=='sms':
                writes=[(2800,0x600,bytes(768)),(2800,0xe0,items),(2800,0xdf,b'\0'),(2800,0x1600,bytes(1280)),(2800,0x310,bytes.fromhex('0050008000000000')),(2800,0x301,b'\1'),(2800,0x304,b'\0'),(2800,0x30a,bytes([direction,0])),(2800,0x68,b'\0')]
            else:
                words={'hero_y':0x5000,'hero_x':0x8000,'hero_dy':0,'hero_dx':0,'hero_state':1,'hero_counter':0,'hero_animation':0,'hero_pending':0,'hero_direction':direction,'hero_selected_item':0,'hero_basic_level':1,'hero_attack_speed':fast}
                writes=[(2800,sy[k],v.to_bytes(2,'big')) for k,v in words.items()]+[(2800,sy['world_actor_state'],bytes(768)),(2800,sy['hero_items'],items),(2800,sy['sms_vram']+0x3800,bytes(1280)),(2800,sy['vtimer'],clock[0].to_bytes(4,'big'))]
            rows={};tiles={}
            def observe(f,r):
                if tag=='sms' and f==2799:clock[0]=r[0x2f]
                if not 2800<=f<=2920:return
                def word(k):return int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(2)),'big')
                rows[f]=[int.from_bytes(r[a:a+n],'little') if tag=='sms' else word(k) for k,a,n in fields]
            def vram(f,v):
                if 2803<=f<=2920:tiles[f]=[sms_pixels(v,496+n) if tag=='sms' else md_pixels(v,512+n) for n in range(4)]
            with contextlib.redirect_stdout(io.StringIO()):run(rom,2920,ROOT/f'validation/ground-walk-{region}-{fast}-{direction}-{tag}',set(),([(200,220,0)] if tag=='sms' else [])+PRESSES[:8]+[(2808,2827,4+direction)],ram_writes=writes,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
            records[tag]=rows;patterns[tag]=tiles
        differing=[f for f in records['sms'] if records['sms'][f]!=records['md'][f]]
        assert not differing,(region,fast,direction,differing[:4],[(records['sms'][f],records['md'][f]) for f in differing[:1]])
        assert patterns['sms']==patterns['md'],(region,fast,direction,'hero tile pixels')
        end=records['sms'][2830];delta=[end[0]-0x5000,end[1]-0x8000]
        assert sum(abs(x) for x in delta)==(40 if fast else 32)*256,(region,fast,direction,delta)
        cases.append(dict(region=region,fast=bool(fast),direction=direction,frames_exact=len(records['sms']),hero_pattern_frames_exact=len(patterns['sms']),displacement_pixels=[x/256 for x in delta]))
        print(region,fast,direction,'exact',flush=True)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=cases,fields=[x[0] for x in fields],controlled_initial_state=True,full_game_ported=False,limits=['Controlled flat ground, ownership and cleared departing enemies; no equipment acquisition, obstacles, combat or other terrain physics proof.','Four hero VRAM tiles compared; complete framebuffer/audio and transition timing are outside these within-room tests.'])
    (ROOT/'validation/ground_walk_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
