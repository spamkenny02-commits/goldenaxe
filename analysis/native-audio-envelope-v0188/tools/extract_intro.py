"""Pre-title assets referenced by native translations of Z80 0C98..10BE."""
import json
from actor_reference import ROOT
from extract_title import rle_planes

def main():
    rom=(ROOT/'input/original.sms').read_bytes();vram=bytearray(0x4000)
    end,_=rle_planes(rom,0x127d0,vram,0x3400,4)
    arrays={'intro_bank6':rom[0x18000:0x1c000],
            'sound_low_rom':rom[:0x8000],
            'world_music_rooms':rom[0x1d02:0x1d0d],
            'intro_fixed':rom[0xf95:0x10df],
            'intro_mono_font':rom[0xc7c6:0xc8d6],
            'intro_symbols_rle':rom[0x127d0:end],
            'intro_fire_colors':rom[0x17e13:0x17e25],
            'intro_lightning_colors':rom[0x17e57:0x17e7a]}
    messages=bytearray();index=bytearray()
    for address in [0xdacc,0xdb3d,0xdb72,0xdbc5,0xdbfe,0xdc09]:
        index.extend(len(messages).to_bytes(2,'little'));messages.extend(rom[address:rom.index(0,address)+1])
    arrays['house_npc_text']=bytes(messages);arrays['house_npc_text_index']=bytes(index)
    lines=['#include <genesis.h>']
    for name,data in arrays.items():
        lines+=['const u8 %s[] = {'%name]+['    '+','.join('0x%02x'%b for b in data[p:p+16])+',' for p in range(0,len(data),16)]+['};']
    (ROOT/'megadrive/src/intro_data.c').write_text('\n'.join(lines)+'\n')
    (ROOT/'analysis/intro_assets.json').write_text(json.dumps({'source':'Original ROM resources, no emulator image/audio captures','native_routines':['0C98','0D10','0E4A','0E3F','0DD2','0D8C','1061'],'scene_headers':['bank6:9D70','bank6:A655','bank6:AF1F'],'event_lines':[18,19,39,40,44],'text_lines':65,'music_command':133,'arrays':{k:len(v) for k,v in arrays.items()}},indent=2)+'\n')
if __name__=='__main__':main()
