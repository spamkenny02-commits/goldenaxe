"""Controlled original/native terrain records reached by a controller cast."""
import contextlib,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
    special='--special' in sys.argv
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    fixtures=[(1,0,0x13,0x29),(1,0,0x86,4),(1,0,0x38,0x29),(2,0,0x38,0x29),(2,0,0x85,4),(2,0,0x3d,0x39),(2,0,0x13,0x29),(2,0,0x86,4),(1,1,0x0b,4),(2,1,0x31,4)]
    if special:fixtures=[(2,prior,0x38,4) for prior in [0,1]]
    cases=[]
    for region in ['auto','pal']:
        for level,high,cell,below in fixtures:
            name=f'{region}-{level}-{high}-{cell:02x}-{below:02x}';items=bytearray(17);items[0]=1;items[5]=level
            index=0x2a if special else 0x67
            cells=bytearray([4]*160);cells[index]=cell;cells[index+16]=below
            records={};clock=[0]
            for tag,path in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
                writes=[(2800,0x600,bytes(768)),(2800,0xdf,b'\x05'),(2800,0xe0,bytes(items)),(2800,0x30a,b'\0'),(2800,0x310,bytes.fromhex('00700080')),(2800,0xdb,b'\x18'),(2800,0x1c00,bytes(cells)),(2800,0x6e,b'\xff'),(2800,0xba,bytes([high]))] if tag=='sms' else [(2800,sy['world_actor_state'],bytes(768)),(2800,sy['hero_selected_item'],(5).to_bytes(2,'big')),(2800,sy['hero_items'],bytes(items)),(2800,sy['hero_direction'],bytes(2)),(2800,sy['hero_y'],(0x7000).to_bytes(2,'big')),(2800,sy['hero_x'],(0x8000).to_bytes(2,'big')),(2800,sy['hero_magic'],(24).to_bytes(2,'big')),(2800,sy['scratch']+0x800,bytes(cells)),(2800,sy['room_metadata'],b'\xff'),(2800,sy['room_id'],(0x95+high*256).to_bytes(2,'big')),(2800,sy['vtimer'],clock[0].to_bytes(4,'big'))]
                rows={};visible={}
                if special:
                    if tag=='sms':
                        writes += [(2800,0x310,bytes.fromhex('003000b0')),(2800,0xb9,bytes.fromhex('0900')),(2800,0x6e,bytes.fromhex('2a3101')),(2800,0x109,bytes([high]))]
                    else:
                        writes += [(2800,sy['hero_y'],(0x3000).to_bytes(2,'big')),(2800,sy['hero_x'],(0xb000).to_bytes(2,'big')),(2800,sy['room_id'],(9).to_bytes(2,'big')),(2800,sy['room_metadata'],bytes.fromhex('2a3101')),(2800,sy['game_save_state']+0x59,bytes([high]))]
                def observe(frame,raw):
                    if tag=='sms' and frame==2799:clock[0]=raw[0x2f]
                    if not 2800<=frame<=2860:return
                    if tag=='sms':
                        rows[frame]=dict(spell=bytes(raw[0x330:0x360]).hex(),cells=bytes(raw[0x1c00:0x1ca0]).hex(),map=bytes(raw[0x1600:0x1b00]).hex(),magic=raw[0xdb])
                        if special:rows[frame]['persistent_flag']=raw[0x109]
                    else:
                        def data(k,n,offset=0):
                            a=sy[k]+offset;return bytes(raw[(a+i)^1] for i in range(n))
                        rows[frame]=dict(spell=data('world_spell_state',48).hex(),cells=data('scratch',160,0x800).hex(),map=data('sms_vram',1280,0x3800).hex(),magic=int.from_bytes(data('hero_magic',2),'big'))
                        if special:rows[frame]['persistent_flag']=data('game_save_state',1,0x59)[0]
                def vram(frame,raw):
                    if frame!=2860:return
                    if tag=='sms':
                        # SMS ignores name-table bits 13..15 used by game terrain.
                        value=bytearray(raw[0x3800:0x3d00])
                        for n in range(1,len(value),2):value[n]&=31
                        visible[frame]=bytes(value)
                    else:
                        # Native BG_A has 64 words per row and a two-row margin.
                        words=[]
                        for y in range(20):
                            for x in range(32):
                                a=0xe000+(y+2)*128+x*2
                                word=int.from_bytes(bytes([raw[a^1],raw[(a+1)^1]]),'big')
                                smsword=((word&0x7ff)-16)&511
                                smsword|=((word>>13)&1)<<11|((word>>15)&1)<<12|((word>>11)&1)<<9|((word>>12)&1)<<10
                                words.extend(smsword.to_bytes(2,'little'))
                        visible[frame]=bytes(words)
                with contextlib.redirect_stdout(io.StringIO()):run(path,2860,ROOT/f'validation/second-spell-terrain-{"special-" if special else ""}{name}-{tag}',set(),([(200,220,0)] if tag=='sms' else [])+PRESSES[:8]+[(2808,2815,8)],ram_writes=writes,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
                records[tag]=(rows,visible)
            a,av=records['sms'];b,bv=records['md'];diff=[(f,[k for k in a[f] if a[f][k]!=b[f][k]]) for f in a if a[f]!=b[f]]
            if diff:
                f,keys=diff[0];print(name,'first difference',f,keys,{k:(a[f][k],b[f][k]) for k in keys},flush=True)
            assert not diff,(name,diff[:3])
            assert av[2860]==bv[2860],(name,'stable hardware map')
            final=bytes.fromhex(a[2860]['cells']);changed=final!=cells
            if special:
                assert a[2860]['persistent_flag']==1
                assert final[index]==(0x31 if not high else 0)
            assert changed==(not (level==1 and high==0 and cell==0x38))
            cases.append(dict(region=region,level=level,room_high_byte=high,initial_cell=cell,initial_below=below,frames_exact=61,stable_hardware_map_bytes_exact=1280,final_cells_hex=final.hex(),terrain_changed=changed));print(name,'exact',flush=True)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=cases,production_roms_unmodified=True,controlled_room_cell_ownership_position_clock_ram_injections=True,full_game_ported=False,limits=['Terrain dispatch isolates room-high-byte selection using current exterior resources, not a natural dungeon entry.','Metadata special cell disabled; persistent passage flags/save/re-entry remain unverified.','Stable hardware map only; intermediate transfer frames, sprite pixels and audio remain unverified.'])
    if special:report['limits']=['Actual room-09 metadata and persistent flag, but controlled exterior resources/position/cells; no natural arrival, save or re-entry proof.','Stable hardware map and per-frame software states only; transfer phase and audio remain unverified.']
    (ROOT/f'validation/second_spell_terrain{"_special" if special else ""}_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
