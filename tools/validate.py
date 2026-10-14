"""Independent checks: original byte roundtrip, emulated 68000 RAM and rendered pixels."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parents[1]/'work'

def main():
    original=(ROOT/'input/original.sms').read_bytes()
    banks=[]
    for bank in range(16):
        dst=WORK/f'roundtrip_bank_{bank:02x}.bin'
        result=subprocess.run([str(WORK/'sgdk/bin/sjasm.exe'),'-q',str(ROOT/f'analysis/bank_{bank:02x}.asm'),str(dst)],capture_output=True,text=True)
        assert result.returncode==0 and 'Errors: 0' in result.stdout,(bank,result.stdout,result.stderr)
        banks.append(dst.read_bytes())
    rebuilt=b''.join(banks)
    assert rebuilt==original,'Z80 assembly does not reproduce source ROM'
    validation=ROOT/'validation'
    (validation/'reassembled.sms').write_bytes(rebuilt)
    symbols={}
    for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines():
        m=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)
        if m: symbols[m[2].split('.lto_priv.')[0]]=int(m[1],16)&0xffff
    native=(validation/'md/ram_00800.bin').read_bytes()
    # Genesis Plus GX stores 68000 word RAM in host-endian order.
    native=bytes(v for n in range(0,len(native),2) for v in (native[n+1],native[n]))
    sms=(validation/'sms/ram_00900.bin').read_bytes()
    patterns=(ROOT/'analysis/title_patterns.sms.bin').read_bytes()
    def region(name,n): return native[symbols[name]:symbols[name]+n]
    assert region('title_map',0x600)==sms[0x1600:0x1c00], 'Native 0BD3/0BFE title map differs from SMS RAM'
    assert region('animation_map',0x600)==sms[0x900:0xf00], 'Native animation map differs from SMS RAM'
    assert region('sms_vram',len(patterns))==patterns, 'Native 032A pattern stream differs'
    planar=region('sms_vram',0x4000); packed=region('md_patterns',0x4000)
    tile_count=len(patterns)//32
    for tile in range(tile_count):
        for y in range(8):
            row=0
            for x in range(8):
                value=sum(((planar[tile*32+y*4+p]>>(7-x))&1)<<p for p in range(4))
                row=(row<<4)|value
            assert int.from_bytes(packed[(tile*8+y)*4:(tile*8+y+1)*4],'big')==row
    source=Image.open(validation/'sms/frame_00900.png').convert('RGB')
    target=Image.open(validation/'md/frame_00800.png').convert('RGB').crop((0,16,256,208))
    colors=set(source.getdata())
    color_map={v:min(colors,key=lambda t:sum((a-b)**2 for a,b in zip(v,t))) for v in set(target.getdata())}
    raw=sum(a!=b for a,b in zip(source.getdata(),target.getdata()))
    normalized=sum(a!=color_map[b] for a,b in zip(source.getdata(),target.getdata()))
    assert normalized==0, f'{normalized} mismatching pixels after palette normalization'
    # The dialog wait uses a local blink counter. Preserve the previous capture's
    # phase discrepancy rather than claiming equality at the old frame alignment.
    opening_source=Image.open(validation/'sms-dialogue/frame_02000.png').convert('RGB')
    opening_prior=Image.open(validation/'md-opening/frame_02008.png').convert('RGB').crop((0,16,256,208))
    opening_colors=set(opening_source.getdata())
    opening_conversion={v:min(opening_colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(opening_prior.getdata())}
    opening_diff=[(i%256,i//256) for i,(x,y) in enumerate(zip(opening_source.getdata(),opening_prior.getdata())) if x!=opening_conversion[y]]
    assert all(120<=x<128 and 152<=y<160 for x,y in opening_diff), 'Opening content changed outside confirmation arrow'
    ui={}
    for label,sms_dir,md_dir,source_frame,target_frame in [('menu','sms-menu','md-menu',1000,1000),
                                     ('name_entry','sms-new','md-new',1300,1300),
                                     ('name_edit_backspace','sms-edit','md-edit',1450,1450),
                                     ('opening_first_page','sms-dialogue','md-opening',2000,2012),
                                     ('initial_room','sms-world-check','md-world',2800,2800)]:
        a=Image.open(validation/sms_dir/f'frame_{source_frame:05d}.png').convert('RGB')
        b=Image.open(validation/md_dir/f'frame_{target_frame:05d}.png').convert('RGB').crop((0,16,256,208))
        palette=set(a.getdata())
        conversion={v:min(palette,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())}
        differences=sum(x!=conversion[y] for x,y in zip(a.getdata(),b.getdata()))
        assert differences==0,(label,differences)
        ui[label]={'pixels':256*192,'normalized_mismatches':differences,'source_frame':source_frame,'target_frame':target_frame}
    menu_ref=(ROOT/'analysis/menu_reference.sms.vram.bin').read_bytes()
    menu_sms=(validation/'sms-menu/vram_01000.bin').read_bytes()
    assert menu_ref[0x3800:0x3e00]==menu_sms[0x3800:0x3e00]
    assert menu_ref[0x1a00:0x2000]==menu_sms[0x1a00:0x2000]
    dialog_sms=(validation/'sms-dialogue/ram_02000.bin').read_bytes()[0x1100:0x1510]
    dialog_native=(validation/'md-opening/ram_02008.bin').read_bytes()
    dialog_native=bytes(v for n in range(0,len(dialog_native),2) for v in (dialog_native[n+1],dialog_native[n]))
    bitmap_address=symbols['scratch']
    assert dialog_native[bitmap_address:bitmap_address+0x410]==dialog_sms
    name_address=symbols['character_name']
    assert dialog_native[name_address:name_address+2]==b'A\0'
    world_native=(validation/'md-world/ram_02800.bin').read_bytes()
    world_native=bytes(v for n in range(0,len(world_native),2) for v in (world_native[n+1],world_native[n]))
    world_vram=world_native[symbols['sms_vram']:symbols['sms_vram']+0x4000]
    world_sms=(validation/'sms-world/ram_02800.bin').read_bytes()
    assert world_vram[0x3800:0x3e00]==world_sms[0x1600:0x1c00]
    world_patterns=(validation/'sms-world/vram_02800.bin').read_bytes()
    used={int.from_bytes(world_vram[n:n+2],'little')&511 for n in range(0x3800,0x3e00,2)}|set(range(496,500))
    assert all(world_vram[tile*32:(tile+1)*32]==world_patterns[tile*32:(tile+1)*32] for tile in used)
    rom=(ROOT/'gaw-title-megadrive.bin').read_bytes()
    assert rom[0x100:0x110].startswith(b'SEGA MEGA DRIVE')
    from finalize_md_rom import md_checksum
    checksum=md_checksum(rom)
    assert checksum==int.from_bytes(rom[0x18e:0x190],'big')
    # Side by side at integer scale; screenshots are from actual core execution.
    preview=Image.new('RGB',(512,224),(0,0,0))
    preview.paste(source,(0,16)); preview.paste(Image.open(validation/'md/frame_00800.png'),(256,0))
    preview.resize((1024,448),Image.Resampling.NEAREST).save(validation/'sms_vs_md.png')
    name_preview=Image.new('RGB',(512,224),(0,0,0))
    name_preview.paste(Image.open(validation/'sms-edit/frame_01450.png'),(0,16))
    name_preview.paste(Image.open(validation/'md-edit/frame_01450.png'),(256,0))
    name_preview.resize((1024,448),Image.Resampling.NEAREST).save(validation/'name_sms_vs_md.png')
    dialog_preview=Image.new('RGB',(512,224),(0,0,0))
    dialog_preview.paste(Image.open(validation/'sms-dialogue/frame_02000.png'),(0,16))
    dialog_preview.paste(Image.open(validation/'md-opening/frame_02008.png'),(256,0))
    dialog_preview.resize((1024,448),Image.Resampling.NEAREST).save(validation/'dialogue_sms_vs_md.png')
    world_preview=Image.new('RGB',(512,224),(0,0,0))
    world_preview.paste(Image.open(validation/'sms-world/frame_02800.png'),(0,16))
    world_preview.paste(Image.open(validation/'md-world/frame_02800.png'),(256,0))
    world_preview.resize((1024,448),Image.Resampling.NEAREST).save(validation/'world_sms_vs_md.png')
    report={'source_sha256':hashlib.sha256(original).hexdigest(),
            'z80_roundtrip_bytes':len(rebuilt),'z80_roundtrip_identical':True,
            'native_title_map_identical_to_sms_ram':True,'native_animation_map_identical_to_sms_ram':True,
            'native_patterns_identical':True,'converted_tiles_checked':tile_count,
            'source_frame':900,'target_frame':800,'compared_pixels':256*192,
            'raw_rgb_mismatches':raw,'mismatches_after_palette_normalization':normalized,
            'ui_scenarios':ui,'menu_font_and_map_reconstructed_from_rom':True,
            'opening_first_page_bitmap_identical':True,'accepted_character_name':'A',
            'opening_prior_target_frame':2008,'opening_prior_frame_mismatches':len(opening_diff),
            'opening_prior_mismatches_confined_to_blink_arrow':True,
            'opening_target_phase_alignment_shift_frames':4,'opening_absolute_timing_exact':False,
            'initial_room_map_identical':True,'initial_room_visible_patterns_identical':True,
            'md_size':len(rom),'md_additive_checksum':checksum,'md_sha256':hashlib.sha256(rom).hexdigest(),
            'limits':['Title, menu, naming, opening message and normal-ground movement are ported. Actor movement/projectiles, shield reflection and normal-ground hero damage are partial; death animation/menu and initial-checkpoint resume are partial; primary/secondary hero attacks and first enemy damage are ported; original RNG, faithful loading/title timing, full combat, sound effects and saves remain pending.',
                      'Normal exterior maps are extracted; rooms 0095/0094, their horizontal transition and village houses 0000/0002 are verified by separate reports. Other room classes, quest/shop/save interactions and Continue save selection are pending.',
                      'Dialogue renderer covers opening-message tokens and six village conversations, not all scripting controls.',
                      'Comparison aligns title states, not absolute frame times.',
                      'Master System and Mega Drive palettes cannot reproduce identical RGB values with this conversion.',
                      'DB bytes preserve all unclassified code and data; roundtrip does not establish complete decompilation.']}
    (validation/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
