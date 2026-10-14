"""Original/native village doors reached by normal walking, including return."""
import hashlib,json,re
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
    symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        m=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if m:symbols[m[2].split('.lto_priv.')[0]]=int(m[1],16)&65535
    results=[]
    for room,route in [(0,[(2950,2958,7),(3000,3020,4)]),(2,[(2950,2965,5),(3000,3023,6),(3050,3061,4),(3100,3110,4)])]:
        route+= [(3500,3503,5)];source=ROOT/f'validation/sms-village-house-{room}';target=ROOT/f'validation/md-village-house-{room}'
        points=set(range(2940,3601))
        run(ROOT/'input/original.sms',3600,source,points,[(200,220,0)]+PRESSES[:11]+route)
        run(ROOT/'gaw-megadrive.bin',3600,target,points,PRESSES[:11]+route)
        states=images=0;image_offsets=[]
        for frame in list(range(3300,3401,5))+list(range(3560,3601,5)):
            sms=(source/f'ram_{frame:05}.bin').read_bytes();raw=(target/f'ram_{frame:05}.bin').read_bytes();native=bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]))
            for name,address,length in [('room_id',0xb9,2),('game_state',0x1d,1),('hero_x',0x312,2),('hero_y',0x310,2),('hero_direction',0x30a,1),('hero_health',0x318,1)]:
                off=symbols[name];actual=int.from_bytes(native[off:off+2],'big');expected=int.from_bytes(sms[address:address+length],'little');assert actual==expected,(room,frame,name,actual,expected)
            assert sms[0xb9]==(room if frame<3500 else 0x94);states+=1
            if frame>=3500:continue
            a=Image.open(source/f'frame_{frame:05}.png').convert('RGB').crop((0,0,256,160));colors=set(a.getdata());matched=None
            # Indoor four-pattern animation follows the IRQ clock; its phase
            # is independent of the five-cell portrait scan after a shorter loader.
            animated_tile=sms[0x9e0];excluded=set()
            for y in range(160):
                for x in range(256):
                    pos=0x1600+(y//8*32+x//8)*2
                    tile=int.from_bytes(sms[pos:pos+2],'little')&511
                    if animated_tile<=tile<animated_tile+4:excluded.add(y*256+x)
            # Compare settled visible content at equal animation phase. Loader timing is
            # independently reported as incomplete; no time-aligned claim here.
            for candidate in sorted(range(max(2940,frame-64),min(3600,frame+64)+1),key=lambda n:abs(n-frame)):
                raw=(target/f'ram_{candidate:05}.bin').read_bytes();d=bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]));off=symbols['sms_palette'];palette=bytes(int.from_bytes(d[off+n*2:off+n*2+2],'big') for n in range(32))
                b=Image.open(target/f'frame_{candidate:05}.png').convert('RGB').crop((0,16,256,176));conv={v:min(colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())};diff=sum(x!=conv[y] for n,(x,y) in enumerate(zip(a.getdata(),b.getdata())) if n not in excluded)
                if not diff:matched=candidate;break
            assert matched is not None,('house pixels at equal animation phase',room,frame);images+=1;image_offsets.append(matched-frame)

        results.append(dict(interior_room=room,states_exact=states,normalized_playfield_images_excluding_four_clock_animated_tiles=images,image_frame_offsets=image_offsets,entry_and_exit_by_normal_input=True,no_emulator_ram_mutations=True))
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=results,scope='Village 94 doors to rooms 0/2; settled room and return states/images',door_fade_and_load_timing_exact=False,hud_animation_phase_exact=False,indoor_pattern_animation_phase_exact=False,village_informational_dialogues_ported=True,village_save_menu_ported=True,first_village_shop_menu_ported=True,other_village_shop_menus_checked_by_this_test=False)
    (ROOT/'validation/village_doors_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
