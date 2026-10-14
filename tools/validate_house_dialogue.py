"""Six source/native village conversations; controlled NPC positions plus a walking case."""
import contextlib,hashlib,io,json,re
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def native(folder,frame):
    r=(folder/f'ram_{frame:05}.bin').read_bytes()
    return bytes(v for n in range(0,len(r),2) for v in(r[n+1],r[n]))

def main():
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
    cases=[]
    for index,(room,x,y) in enumerate([(0,88,72),(0,104,88),(0,184,88),(2,136,72),(2,152,88),(2,40,104)]):
        route=[(2950,2958,7),(3000,3020,4)] if room==0 else [(2950,2965,5),(3000,3023,6),(3050,3061,4),(3100,3110,4)]
        presses=PRESSES[:11]+route+[(3350,3550,4),(3800,3810,7 if index==4 else 8)]
        a=ROOT/f'validation/sms-house-dialogue-{index}';b=ROOT/f'validation/md-house-dialogue-{index}'
        source_writes=[(3300,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')),(3300,0x30a,b'\0')]
        target_writes=[(3300,sy['hero_x'],(x<<8).to_bytes(2,'big')),(3300,sy['hero_y'],(y<<8).to_bytes(2,'big')),(3300,sy['hero_direction'],bytes(2))]
        with contextlib.redirect_stdout(io.StringIO()):
            run(ROOT/'input/original.sms',3900,a,{3340,3600,3700,3900},[(200,220,0)]+presses,ram_writes=source_writes)
            run(ROOT/'gaw-megadrive.bin',3900,b,{3340,3600,3700,3900},presses,ram_writes=target_writes)
        sms=(a/'ram_03600.bin').read_bytes();md=native(b,3600)
        def val(name):return int.from_bytes(md[sy[name]:sy[name]+2],'big')
        assert val('house_dialogue_active')==1 and val('house_dialogue_index')==index,(index,'not active')
        assert md[sy['scratch']:sy['scratch']+0x410]==sms[0x1100:0x1510],(index,'bitmap')
        # Only the text window: room animation and HUD phases have separate tests.
        im=Image.open(a/'frame_03600.png').convert('RGB').crop((16,104,240,160))
        jm=Image.open(b/'frame_03600.png').convert('RGB').crop((16,120,240,176))
        pal=set(im.getdata());conv={c:min(pal,key=lambda d:sum((u-v)**2 for u,v in zip(c,d))) for c in set(jm.getdata())}
        # The continuation marker blinks with different startup phase.
        assert all(u==conv[v] for n,(u,v) in enumerate(zip(im.getdata(),jm.getdata())) if not (104<=n%224<112 and 48<=n//224<56)),(index,'window pixels')
        md=native(b,3900);sms=(a/'ram_03900.bin').read_bytes()
        assert val('house_dialogue_active')==0,(index,'not closed')
        for name,offset,length in [('room_id',0xb9,2),('hero_x',0x312,2),('hero_y',0x310,2),('hero_direction',0x30a,1),('hero_health',0x318,1)]:
            assert val(name)==int.from_bytes(sms[offset:offset+length],'little'),(index,'restore',name)
        before=native(b,3340);off=sy['sms_vram']
        # The window overwrites 130 patterns at 2000, including two hero tiles.
        # The first 128 must survive roundtrip; the last two follow hero pose updates.
        assert md[off+0x2000:off+0x3000]==before[off+0x2000:off+0x3000],(index,'restored pattern window')
        cases.append(dict(restored_window_pattern_bytes_exact=4096,index=index,room=room,position=[x,y],bitmap_bytes_exact=1040,text_window_exact_excluding_blink=True,restored_fields_exact=True,controlled_position_injection=True,confirmation="right_direction" if index==4 else "action_button"))
        print('NPC',index,'OK')
    # Reach the first room-2 speaker entirely with controller input.
    route=[(2950,2965,5),(3000,3023,6),(3050,3061,4),(3100,3110,4),(3350,3490,4),(3700,3710,8)]
    a=ROOT/'validation/sms-house-dialogue-walking';b=ROOT/'validation/md-house-dialogue-walking'
    with contextlib.redirect_stdout(io.StringIO()):
        run(ROOT/'input/original.sms',3900,a,{3340,3600,3900},[(200,220,0)]+PRESSES[:11]+route)
        run(ROOT/'gaw-megadrive.bin',3900,b,set(range(3340,3461))|set(range(3690,3731))|{3600,3900},PRESSES[:11]+route)
    checked=0
    for frame in list(range(3340,3461))+list(range(3690,3731)):
        regs=(b/f'vdp_regs_{frame:05}.bin').read_bytes()
        assert regs[1]&0x40,('NPC display disabled',frame)
        im=Image.open(b/f'frame_{frame:05}.png').convert('RGB').crop((0,16,256,176))
        assert any(pixel!=(0,0,0) for pixel in im.getdata()),('NPC black playfield',frame)
        checked+=1
    sms=(a/'ram_03600.bin').read_bytes();md=native(b,3600)
    assert val('house_dialogue_active')==1 and val('house_dialogue_index')==3
    assert md[sy['scratch']:sy['scratch']+0x410]==sms[0x1100:0x1510]
    sms=(a/'ram_03900.bin').read_bytes();md=native(b,3900)
    assert val('house_dialogue_active')==0 and val('room_id')==2
    for name,offset in [('hero_x',0x312),('hero_y',0x310)]:assert val(name)==int.from_bytes(sms[offset:offset+2],'little')
    report=dict(dialogue_entry_exit_frames_without_display_disable=checked,natural_walk_conversation_and_restore_verified=True,source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=cases,dialogue_timing_exact=False,village_save_menu_ported=True,first_village_merchant_ported=True,all_trade_menus_checked_by_this_test=False)
    (ROOT/'validation/house_dialogue_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
