"""Exercise real healing inputs with floor tiles selecting the source terrain path."""
import argparse,contextlib,io,json
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols
from archive_lossless_evidence import sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--pal',action='store_true');a=p.parse_args()
    sy=symbols(ROOT/'megadrive/out/release/symbol.txt');cases=[];region='pal' if a.pal else 'auto'
    fixtures=[('ordinary',0,0x25,0,9,48),('enhanced',0,0xa0,2,9,48),('clamped',0,0xa1,2,89,24),('full',0,0xa0,2,96,24),('insufficient',0,0xa0,2,9,23),('dungeon',2,0x0c,2,9,48)]
    for name,graphics,tile,context,hp,magic in fixtures:
        rows={};clock=0
        for tag in ['sms','md']:
            source=tag=='sms';out=ROOT/f'validation/heal-terrain-v0243-{region}-{name}-{tag}';assert not out.exists();observed=[]
            floor=(((112-4)&248)*8)+(((136-4)>>2)&62)
            if source:
                writes=[(2810,0x40,bytes([graphics])),(2810,0xdf,b'\7'),(2810,0xe7,b'\1'),(2810,0xda,bytes([96,magic,72])),(2810,0x318,bytes([hp])),(2810,0x301,b'\1'),(2810,0x304,b'\0'),(2810,0x310,b'\0\x70\0\x88'),(2810,0x314,bytes(4)),(2810,0x330,bytes(0x120)),(2810,0x600,bytes(768)),(2810,0x1600+floor,bytes([tile,0,tile,0]))]
            else:
                w=lambda n,v:(2810,sy[n],v.to_bytes(2,'big'))
                writes=[w('world_graphics_class',graphics),w('hero_selected_item',7),w('hero_health',hp),w('hero_max_health',96),w('hero_magic',magic),w('hero_max_magic',72),w('hero_state',1),w('hero_counter',0),w('hero_x',136<<8),w('hero_y',112<<8),w('hero_dx',0),w('hero_dy',0),(2810,sy['hero_items']+7,b'\1'),(2810,sy['world_actor_state'],bytes(768)),(2810,sy['world_spell_state'],bytes(48)),(2810,sy['world_loot_state'],bytes(336)),(2810,sy['sms_vram']+0x3800+floor,bytes([tile,0,tile,0])),(2810,sy['vtimer'],clock.to_bytes(4,'big')),(2810,sy['world_clock_shift'],bytes(4))]
            def observe(f,r):
                nonlocal clock
                if source and f==2809:clock=r[0x2f]
                if f<2819:return
                data=lambda n,k:bytes(r[(sy[n]+i)^1] for i in range(k))
                word=lambda n:int.from_bytes(data(n,2),'big')
                observed.append(dict(frame=f,health=r[0x318] if source else word('hero_health'),magic=r[0xdb] if source else word('hero_magic'),selected=r[0xdf] if source else word('hero_selected_item'),terrain=r[0x41] if source else word('hero_terrain_context'),owned=r[0xe7] if source else data('hero_items',17)[7]))
            presses=([(200,220,0)] if source else [])+PRESSES[:8]+[(2820,2839,8),(2860,2861,8)]
            with contextlib.redirect_stdout(io.StringIO()):run(ROOT/('input/original.sms' if source else 'gaw-megadrive.bin'),2870,out,{2819,2821,2839,2861,2870},presses,ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
            rows[tag]=observed;(out/'states.json').write_bytes((json.dumps(observed,indent=2)+'\n').encode())
        assert rows['sms']==rows['md'],(name,next((x,y) for x,y in zip(rows['sms'],rows['md']) if x!=y))
        casts=min(2,magic//24);amount=32 if context==2 else 16
        assert all(r['terrain']==context for r in rows['sms']),(name,'terrain')
        final=rows['sms'][-1];assert final['health']==min(96,hp+casts*amount) and final['magic']==magic-casts*24 and final['owned']==1 and final['selected']==7
        assert rows['sms'][20]['magic']==magic-min(1,casts)*24 # held button never repeats
        cases.append(dict(case=name,graphics=graphics,floor_tile=tile,terrain=context,initial_health=hp,initial_magic=magic,activations=casts,heal_per_activation=amount,consecutive_frames_exact=len(rows['sms']),final=final))
    report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha((ROOT/'input/original.sms').read_bytes()),passed=True,region=region,cases=cases,full_game_verified=False,limits=['Controlled ownership, room class, floor words, resources and initial clock; terrain classification itself runs normally.','No full-frame pixel, audio waveform or natural acquisition claim.'])
    (ROOT/f'analysis/heal_terrain_v0243_{region}_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(region,': six healing cases pass, 52 consecutive state frames each.')

if __name__=='__main__':main()
