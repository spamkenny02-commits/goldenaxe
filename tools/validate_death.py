"""Death animation/menu and resume/quit contracts against controlled SMS runs."""
import hashlib,json,re
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_damage import FIELDS


def main():
    rom=ROOT/'input/original.sms';md=ROOT/'gaw-megadrive.bin';symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        m=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if m:symbols[m[2].split('.lto_priv.')[0]]=int(m[1],16)&65535
    def native(folder,frame):
        raw=(folder/f'ram_{frame:05}.bin').read_bytes()
        return bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]))
    def value(data,name):return int.from_bytes(data[symbols[name]:symbols[name]+2],'big')
    def image_difference(source,target,frame):
        a=Image.open(source/f'frame_{frame:05}.png').convert('RGB')
        b=Image.open(target/f'frame_{frame:05}.png').convert('RGB').crop((0,16,256,208))
        palette=set(a.getdata());conversion={v:min(palette,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())}
        return sum(x!=conversion[y] for x,y in zip(a.getdata(),b.getdata()))
    def capture(mode,frames,last,presses,source_extra=(),target_extra=()):
        source=ROOT/f'validation/sms-death-{mode}';target=ROOT/f'validation/md-death-{mode}'
        run(rom,last,source,frames,[(200,220,0)]+presses,ram_writes=[
            (3741,0x318,bytes((0,))),(3741,0x600,bytes(0x300)),*source_extra])
        run(md,last,target,frames,presses,ram_writes=[
            (3741,symbols['hero_health'],bytes(2)),(3741,symbols['world_actor_state'],bytes(0x300)),
            (3741,symbols['vtimer'],(167).to_bytes(4,'big')),*target_extra])
        assert json.loads((source/'capture.json').read_text())['rom_sha256']==hashlib.sha256(rom.read_bytes()).hexdigest()
        assert json.loads((target/'capture.json').read_text())['rom_sha256']==hashlib.sha256(md.read_bytes()).hexdigest()
        return source,target
    frames=set(range(3740,3861))|{3900,4000}
    source,target=capture('isolated',frames,4000,PRESSES)
    fields=dict(FIELDS,game_state=(0x1d,1));state_steps=0
    for frame in range(3741,3833):
        sms=(source/f'ram_{frame:05}.bin').read_bytes();data=native(target,frame)
        for name,(offset,size) in fields.items():
            assert value(data,name)==int.from_bytes(sms[offset:offset+size],'little'),('death field',frame,name)
        off=symbols['world_actor_state'];assert data[off:off+0x300]==sms[0x600:0x900],('death actors',frame)
        state_steps+=1
    for frame in range(3743,3861):assert not image_difference(source,target,frame),('death image',frame)
    actions={};menu_images=0
    for mode in ('continue','quit'):
        inputs=PRESSES+[(3900,3904,5)]+([(3930,3934,4)] if mode=='continue' else [])+[(3960,3964,8)]
        points=set(range(3895,3977))|{4000,4050,4060,4100}
        a,b=capture(mode,points,4100,inputs,[(3960,0xdd,bytes((100,)))],[(3960,symbols['hero_gold'],(100).to_bytes(2,'big'))])
        for frame in range(3895,3960):
            sms=(a/f'ram_{frame:05}.bin').read_bytes();data=native(b,frame)
            assert value(data,'death_menu_selection')==sms[0x1cc0],('menu selection',mode,frame)
            assert not image_difference(a,b,frame),('menu image',mode,frame)
            menu_images+=1
        sms=(a/'ram_03960.bin').read_bytes();data=native(b,3960)
        expected=75 if mode=='continue' else 100
        assert sms[0xdd]==value(data,'hero_gold')==expected
        if mode=='continue':
            assert sms[0x318]==value(data,'hero_health')==24
            late=(a/'ram_04100.bin').read_bytes();native_late=native(b,4100)
            for name,(offset,size) in FIELDS.items():
                assert value(native_late,name)==int.from_bytes(late[offset:offset+size],'little'),('resumed field',name)
            assert value(native_late,'room_id')==late[0xb9]==0x95
            assert value(native_late,'game_state')==late[0x1d]==12
            assert not image_difference(a,b,4100),'resumed image'
            mismatches=[]
            for frame in sorted(points):
                if frame>=3960:
                    count=image_difference(a,b,frame)
                    if count:mismatches.append((frame,count))
            actions[mode]=dict(health_restored=24,gold_after=expected,checkpoint_room=0x95,
                               resumed_scene_and_fields_exact=True,preparation_images_different=mismatches,
                               preparation_timing_exact=False)
        else:
            late=(a/'ram_04100.bin').read_bytes();native_late=native(b,4100)
            assert late[0x1d]==0
            # SGDK bool is u8; inspect the explicit title-return flags.
            intro_running=int.from_bytes(native_late[symbols['intro_running']:symbols['intro_running']+2],'big')
            assert (native_late[symbols['title_phase']] or intro_running) and native_late[symbols['return_to_title']]
            actions[mode]=dict(gold_after=expected,source_title_state=True,native_boot_sequence_entered=True,pretitle_intro_replayed=True,title_timing_exact=False)
    preview=[]
    for frame in range(3743,3861,2):
        picture=Image.new('RGB',(512,224),(0,0,0))
        picture.paste(Image.open(source/f'frame_{frame:05}.png'),(0,16))
        picture.paste(Image.open(target/f'frame_{frame:05}.png'),(256,0))
        preview.append(picture.resize((1024,448),Image.Resampling.NEAREST))
    preview[0].save(ROOT/'validation/death_sms_vs_md.gif',save_all=True,append_images=preview[1:],duration=33,loop=0)
    report=dict(md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),
                controlled_death_steps_exact=state_steps,hero_fields=list(fields),actor_bytes_per_frame=768,
                death_fade_and_menu_images_exact=118,selection_images_exact=menu_images,actions=actions,
                scope='Initial exterior checkpoint, controlled death and clock; original ROM graphics/font/palette rules',
                complete_death_and_respawn_timing_exact=False,other_checkpoint_classes_ported=False,sound_ported=False)
    (ROOT/'validation/death_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
