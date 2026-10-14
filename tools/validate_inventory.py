"""Inventory navigation and ROM layout; controlled initial ownership/clock."""
import hashlib,json,re
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
    rom=ROOT/'input/original.sms';md=ROOT/'gaw-megadrive.bin';symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        m=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if m:symbols[m[2].split('.lto_priv.')[0]]=int(m[1],16)&65535
    source=ROOT/'validation/sms-inventory-test';target=ROOT/'validation/md-inventory-test'
    owned=bytes([1,1,0,1,0,0,1,0,0,1,0,1,0,0,0,0,0])
    navigation=[(2800,2805,0),(2825,2827,7),(2830,2832,8),(2835,2837,7),(2840,2842,8),(2845,2847,5),(2850,2852,8),(2855,2857,7),(2860,2862,7),(2865,2867,5),(2870,2872,8),(2875,2877,6),(2880,2882,4),(2885,2887,6),(2890,2892,4),(2895,2897,6),(2900,2902,7),(2905,2907,8),(2910,2915,0),(2940,2955,8)]
    presses=PRESSES[:8]+navigation;points=set(range(2820,2971))
    sw=[(2800,0xe0,owned),(2800,0xde,bytes([123])),(2800,0x600,bytes(768))]
    run(rom,2970,source,points,[(200,220,0)]+presses,ram_writes=sw)
    initial=(source/'ram_02820.bin').read_bytes()
    tw=[(2800,symbols['hero_items'],owned),(2800,symbols['hero_weapon_level'],(1).to_bytes(2,'big')),(2800,symbols['hero_keys'],(123).to_bytes(2,'big')),(2800,symbols['world_actor_state'],bytes(768)),(2821,symbols['vtimer'],int(initial[0x2f]).to_bytes(4,'big'))]
    run(md,2970,target,points,presses,ram_writes=tw)
    images=0;states=0;preview=[];diffs=[]
    for frame in range(2821,2910):
        sms=(source/f'ram_{frame:05}.bin').read_bytes();raw=(target/f'ram_{frame:05}.bin').read_bytes();data=bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]))
        for name,address in [('inventory_slot',0xa0),('hero_selected_item',0xdf)]:
            off=symbols[name];actual=int.from_bytes(data[off:off+2],'big');assert actual==sms[address],('selection',frame,name,actual,sms[address])
        off=symbols['sms_vram'];a=(source/f'vram_{frame:05}.bin').read_bytes();assert data[off+0x3800:off+0x3d00]==a[0x3800:0x3d00],('inventory map',frame)
        states+=1
        left=Image.open(source/f'frame_{frame:05}.png').convert('RGB');right=Image.open(target/f'frame_{frame:05}.png').convert('RGB').crop((0,16,256,208));colors=set(left.getdata());conv={v:min(colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(right.getdata())};diff=sum(x!=conv[y] for x,y in zip(left.getdata(),right.getdata()))
        if diff:diffs.append((frame,diff))
        else:images+=1
        if frame%2==0:
            picture=Image.new('RGB',(512,224));picture.paste(left,(0,16));picture.paste(Image.open(target/f'frame_{frame:05}.png'),(256,0));preview.append(picture.resize((1024,448),Image.Resampling.NEAREST))
    transfer_frames={f for start in [2830,2850,2870,2905] for f in range(start,start+3)}
    assert all(frame in transfer_frames for frame,diff in diffs),('inventory stable images',diffs)
    # Selected secondary weapon is exercised by normal input after closing.
    for frame in range(2940,2971):
        sms=(source/f'ram_{frame:05}.bin').read_bytes();raw=(target/f'ram_{frame:05}.bin').read_bytes();data=bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]))
        off=symbols['hero_selected_item'];assert int.from_bytes(data[off:off+2],'big')==sms[0xdf]==1
        for name,address in [('hero_state',0x301),('hero_animation',0x30b),('hero_attack_phase',0x30e)]:
            off=symbols[name];assert int.from_bytes(data[off:off+2],'big')==sms[address],('return attack',frame,name,int.from_bytes(data[off:off+2],'big'),sms[address])
    equipment_cases=[]
    for level in [1,2,3]:
        owned=bytes([level,min(level,2)]+[1]*15);source_case=ROOT/f'validation/sms-inventory-equipment-{level}';target_case=ROOT/f'validation/md-inventory-equipment-{level}'
        run(rom,2850,source_case,{2849,2850},[(200,220,0)]+PRESSES[:8]+[(2800,2805,0)],ram_writes=[(2800,0xe0,owned),(2800,0xf1,bytes([level,level])),(2800,0xde,bytes([255])),(2800,0x600,bytes(768))])
        clock=(source_case/'ram_02849.bin').read_bytes()[0x2f]
        run(md,2850,target_case,{2850},PRESSES[:8]+[(2800,2805,0)],ram_writes=[(2800,symbols['hero_items'],owned),(2800,symbols['hero_basic_level'],level.to_bytes(2,'big')),(2800,symbols['hero_weapon_level'],min(level,2).to_bytes(2,'big')),(2800,symbols['hero_armor_level'],level.to_bytes(2,'big')),(2800,symbols['hero_shield_level'],level.to_bytes(2,'big')),(2800,symbols['hero_keys'],(255).to_bytes(2,'big')),(2800,symbols['world_actor_state'],bytes(768)),(2850,symbols['vtimer'],int(clock).to_bytes(4,'big'))])
        a=Image.open(source_case/'frame_02850.png').convert('RGB');b=Image.open(target_case/'frame_02850.png').convert('RGB').crop((0,16,256,208));colors=set(a.getdata());conv={v:min(colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())};diff=sum(x!=conv[y] for x,y in zip(a.getdata(),b.getdata()));assert diff==0,('equipment image',level,diff)
        equipment_cases.append(dict(armor=level,shield=level,basic=level,secondary=min(level,2),all_17_owned_icons=True,keys=255,image_exact=True))
    preview[0].save(ROOT/'validation/inventory_sms_vs_md.gif',save_all=True,append_images=preview[1:],duration=40,loop=0)
    report=dict(md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),equipment_cases=equipment_cases,menu_states_exact=states,menu_images_exact=images,selection_transfer_image_differences=diffs,selection_transfer_pixels_exact=False,return_secondary_attack_states_exact=31,scope='Exterior initial room, controlled ownership/keys and one initial clock alignment; fresh presses, bounds, unavailable objects, normal menu close and secondary activation',global_entry_exit_timing_exact=False,other_item_behaviors_verified_by_this_test=False)
    (ROOT/'validation/inventory_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
