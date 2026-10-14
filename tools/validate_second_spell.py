"""Controlled controller casts of slot 5 through original SMS/native code."""
import contextlib,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from audit_item_reward_visuals import sms_pixels,md_pixels

def main():
    focused='--focus' in sys.argv
    walking='--walk' in sys.argv
    fast='--fast' in sys.argv
    baseline='--baseline' in sys.argv
    md=ROOT.parents[1]/'work/gaw-baseline-v0082/megadrive/out/release' if baseline else ROOT/'megadrive/out/release'
    mdrom=md/'rom.bin' if baseline else ROOT/'gaw-megadrive.bin'
    fire='--fire' in sys.argv;axe='--axe' in sys.argv;kind=4 if axe or fire else 5;object_type=5 if axe else 3 if fire else 4
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (md/'symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    cases=[]
    for region in (['auto'] if focused else ['auto','pal']):
        for direction,level,magic in ([(0,1,24),(1,1,24),(2,1,24),(3,1,24)] if focused else [(d,l,24) for d in range(4) for l in [1,2]]+[(0,1,0),(0,1,7),(0,1,8)]):
            name=f'{region}-{direction}-{level}-{magic}'
            if walking and magic!=24:continue
            if '--case' in sys.argv and name!=sys.argv[sys.argv.index('--case')+1]:continue
            items=bytearray(17);items[0]=level if axe else 1;items[kind]=1 if axe else level
            records={};clock=[0];patterns={}
            for tag,path in [('sms',ROOT/'input/original.sms'),('md',mdrom)]:
                writes=[(2800,0x600,bytes(768)),(2800,0xdf,b'\x05'),(2800,0xe0,bytes(items)),(2800,0x30a,bytes([direction])),(2800,0x310,bytes.fromhex('00700080')),(2800,0xdb,bytes([magic]))] if tag=='sms' else [(2800,sy['world_actor_state'],bytes(768)),(2800,sy['hero_selected_item'],(5).to_bytes(2,'big')),(2800,sy['hero_items'],bytes(items)),(2800,sy['hero_direction'],direction.to_bytes(2,'big')),(2800,sy['hero_y'],(0x7000).to_bytes(2,'big')),(2800,sy['hero_x'],(0x8000).to_bytes(2,'big')),(2800,sy['hero_magic'],magic.to_bytes(2,'big')),(2800,sy['vtimer'],clock[0].to_bytes(4,'big'))]
                writes=[(f,a,bytes([kind]) if tag=='sms' else kind.to_bytes(2,'big')) if a==(0xdf if tag=='sms' else sy['hero_selected_item']) else (f,a,v) for f,a,v in writes]
                if axe:
                    terrain=bytes([0x11,0xc0])*640
                    writes += [(2800,0x1600,terrain),(2800,0xf0,b'\x01'),(2800,0xee,bytes([int(fast)]))] if tag=='sms' else [(2800,sy['sms_vram']+0x3800,terrain),(2800,sy['hero_basic_level'],level.to_bytes(2,'big')),(2800,sy['hero_items']+16,b'\x01'),(2800,sy['hero_attack_speed'],int(fast).to_bytes(2,'big'))]
                rows={};tiles={}
                def observe(frame,raw):
                    if tag=='sms' and frame==2799:clock[0]=raw[0x2f]
                    if not 2800<=frame<=2920:return
                    if tag=='sms':
                        rows[frame]=dict(spell=bytes(raw[0x330:0x360]).hex(),fields=[raw[x] for x in [0xdb,0xdf,0x301,0x30b,0x319,0x30e,0xc6]],cells=bytes(raw[0x1c00:0x1ca0]).hex())
                    else:
                        def data(k,size):
                            a=sy[k];return bytes(raw[(a+n)^1] for n in range(size))
                        rows[frame]=dict(spell=data('world_spell_state',48).hex(),fields=[int.from_bytes(data(k,2),'big') for k in ['hero_magic','hero_selected_item','hero_state','hero_animation','hero_attack','hero_attack_phase','hero_fire_charge']],cells=data('scratch',0x8a0)[0x800:0x8a0].hex())
                    if axe and frame in rows:
                        rows[frame]['context']=raw[0x41] if tag=='sms' else int.from_bytes(data('hero_terrain_context',2),'big')
                        rows[frame]['motion']=list(raw[0x310:0x318])+[raw[0x304]] if tag=='sms' else list(data('hero_y',2)[::-1]+data('hero_x',2)[::-1]+data('hero_dy',2)[::-1]+data('hero_dx',2)[::-1])+[int.from_bytes(data('hero_counter',2),'big')]
                def vram(frame,v):
                    if frame not in rows:return
                    if axe and frame>=2803:
                        hero=[sms_pixels(v,496+n) if tag=='sms' else md_pixels(v,512+n) for n in range(4)]
                        tiles[-frame]=hero
                    e=bytes.fromhex(rows[frame]['spell'])
                    if e[0]!=object_type or not e[3]&1:return
                    rom=(ROOT/'input/original.sms').read_bytes()
                    offset=lambda address:address if address<0x8000 else 0x30000+(address&0x3fff)
                    word=lambda address:int.from_bytes(rom[offset(address):offset(address)+2],'little')
                    table=word((e[8]|e[9]<<8)+e[10]*2);address=word(table+e[11]*2)
                    pose=rom[offset(address):];count=pose[0]&127;base=0 if pose[0]&128 else e[2]
                    values=[]
                    for n in range(count):
                        tile=(base+pose[4+count+n*2])&255
                        values.append(sms_pixels(v,256+tile) if tag=='sms' else md_pixels(v,272+tile))
                    tiles[frame]=values
                with contextlib.redirect_stdout(io.StringIO()):run(path,2920,ROOT/f'validation/{"thrown-axe-walk-fast" if axe and walking and fast else "thrown-axe-walk" if axe and walking else "thrown-axe" if axe else "second-spell-fire-regression" if fire else "second-spell"}-{name}-{tag}',set(),([(200,220,0)] if tag=='sms' else [])+PRESSES[:8]+([(2808,2819,4+direction)] if walking else [(2808,2815,8),(2818,2822,8),(2870,2875,8)]),ram_writes=writes,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
                records[tag]=rows;patterns[tag]=tiles
            differences=[(f,[k for k in a if a[k]!=records['md'][f][k]]) for f,a in records['sms'].items() if a!=records['md'][f]]
            if differences:
                f,keys=differences[0];print('first difference',name,f,keys,records['sms'][f],records['md'][f],flush=True)
            if baseline:
                diagnostic=dict(md_sha256=hashlib.sha256(mdrom.read_bytes()).hexdigest(),case=name,diagnostic_only=True,differences=differences,first_states={tag:records[tag][differences[0][0]] for tag in records} if differences else {})
                (ROOT/f'validation/fire_insufficient_baseline_{name}.json').write_text(json.dumps(diagnostic,indent=2)+'\n')
                print('Baseline differences',differences[:5],flush=True);continue
            known=False
            if differences and fire:
                bp=ROOT/f'validation/fire_insufficient_baseline_{name}.json'
                if bp.exists():
                    previous=json.loads(bp.read_bytes())
                    assert previous['md_sha256']==hashlib.sha256((ROOT/'versions/v0082-365b546d/gaw-megadrive-v0082.bin').read_bytes()).hexdigest()
                    known=previous['differences']==[[f,k] for f,k in differences] and previous['first_states']=={tag:records[tag][differences[0][0]] for tag in records}
            assert not differences or known,(name,differences[:5])
            assert patterns['sms']==patterns['md'],(name,'projectile tile patterns')
            if magic>=8 or axe:assert patterns['sms'],(name,'no projectile patterns checked')
            cases.append(dict(region=region,direction=direction,level=level,initial_magic=magic,frames_exact=121-len(differences),source_differences=differences,known_baseline_difference=known,spell_record_bytes=48,cells_bytes=160,active_projectile_pattern_frames_exact=sum(f>0 for f in patterns['sms']),hero_water_pattern_frames_exact=sum(f<0 for f in patterns['sms'])));print(name,'unchanged baseline discrepancy' if known else 'exact',flush=True)
    if baseline:return
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),selected_item=kind,water_walking=walking,fast_movement=fast,cases=cases,production_roms_unmodified=True,controlled_initial_ram_injections=True,full_game_ported=False,limits=['Initial exterior room, initial ownership/stats/position/clock/enemies controlled.','No complete sprite/framebuffer, terrain progression, damage, acquisition or save proof.'])
    (ROOT/f'validation/{"thrown_axe_walk_fast" if axe and walking and fast else "thrown_axe_walk" if axe and walking else "thrown_axe" if axe else "second_spell"}{"_fire_regression" if fire else "_focus" if focused else ""}_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
