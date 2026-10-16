"""Instruction-derived16D0 world graphics load after an indoor exit.

Scope: class0, changed graphics bank, display already disabled, C0AC=0.
"""
from actor_loading_cost import rle_cost
from ram_plane_loading_cost import ram_plane_cost
def ldir(n):return (n-1)*21+16
def class0_graphics_cost(rom):
 parts={};classify=sum([13,4,7,7,13,7,7,7,13,7,7,7,7,4,13,10])
 parts['classify_and_bank_change']=17+classify+sum([10,7,7,10,7,7,5,7,13,13,13,7,10])
 rle=rle_cost(rom,0x3c010,0x4000)
 parts['palette_and_patterns']=sum([13,13,10,10,10,ldir(16),10,17])+rle['tstates']
 meta=ram_plane_cost(rom,rle['source_end'],0xc900,2)
 parts['metatiles']=10+7+17+meta['tstates']
 parts['metatile_backup']=10+10+10+ldir(8)+10+7+ldir(8)
 parts['terrain_patch']=sum([17,13,4,5,13,4,7,10,10,10,11,11,ldir(8),10,10,10,ldir(8),10])
 parts['dungeon_palette_skip']=7+13+17+13+4+11
 table=int.from_bytes(rom[0x8259:0x825b],'little');n=0
 while rom[table+n]<128:n+=1
 lookup=11+sum([4,4,12,7,6,7,4,10])
 per_meta=sum([7,6,4,10,11,11,4,7,11,11,11,10,11,10,ldir(8),10,10,4,12])
 attr_loop=sum([4,5,7,7,7,7,6,6,6,12])
 extra=sum([10,13,4,lookup,10,7])+n*per_meta+sum([7,6,4,10,10,8,8])+n*4*attr_loop+4+11
 parts['extra_metatiles']=7+13+17+extra
 parts['terrain_pointer']=13+4+10
 terrain_pc=int.from_bytes(rom[0x1759:0x175b],'little')
 terrain=ram_plane_cost(rom,11*0x4000+(terrain_pc&0x3fff),0xd100,4)
 parts['terrain_decode']=lookup+7+13+10+7+17+terrain['tstates']
 parts['SRAM_enable']=17+sum([4,13,7,13,10])
 parts['terrain_SRAM_copy']=10+10+10+ldir(1024)
 parts['SRAM_disable_return']=10+sum([13,7,13,4,10])
 return dict(foreground_tstates=sum(parts.values()),components=parts,extra_metatile_count=n,scope='World class0 graphics bank change, display off,C0AC0; other branches not modeled.')
