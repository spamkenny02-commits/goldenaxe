"""Verify gem patch scope and original resource provenance."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'analysis/gem-baseline-v0101';p=ROOT/'megadrive/src/main.c';s=p.read_text()
 start=s.index('/* 2A6B..2ACC:');end=s.index('/* 5D59:',start);s=s[:start]+s[end:]
 s=s.replace('\nstatic volatile u8 world_boss_state; /* C0AE, cleared by gem appearance. */\nextern const u8 gem_labels[],gem_label_index[],gem_window_icons[],gem_reward_hero_frame[],gem_tile_table[];','')
 start=s.index('    bool gem=index>=10;');end=s.index('    u32 started;',start)
 s=s[:start]+"    u16 n,count,label=reward_label_index[index*2]|((u16)reward_label_index[index*2+1]<<8);\n"+s[end:]
 s=s.replace('    if(gem) memcpy(sms_vram+0x3780,gem_window_icons+index*32,32);\n    else memcpy(sms_vram+0x3780,inventory_icons+item*128,128);\n    draw_text(0x3d46,labels+label);','    memcpy(sms_vram+0x3780,inventory_icons+item*128,128);\n    draw_text(0x3d46,reward_labels+label);')
 s=s.replace('count=add_sms_sprite_frame(count,hero_x>>8,hero_y>>8,hero_frame,0);','count=add_sms_sprite_frame(count,hero_x>>8,hero_y>>8,reward_hero_frame,0);')
 assert s==(base/'main.c').read_text()
 a=ROOT/'megadrive/src/actors.c';s=a.read_text()
 s=s.replace('\nstatic const u8 *descriptor_frame(u16 address);\nextern const u8 gem_descriptor_data[];\nextern void tick_world_gem(u8 *entity);','')
 s=s.replace('            else if(entity[0]==0x0f) tick_world_gem(entity);\n','')
 start=s.index('static const u8 *descriptor_frame(u16 address)\n{');end=s.index('static u16 descriptor_word(u16 address)\n{',start);s=s[:start]+s[end:]
 s=s.replace('    if(address>=0x2acd && address<0x2adc) return gem_descriptor_data[address-0x2acd]|((u16)gem_descriptor_data[address-0x2acc]<<8);\n','')
 s=s.replace('descriptor_frame(table)','table>=0x3d8d && table<0x3da5?world_axe_descriptors+table-0x3d8d:actor_descriptors+(table&0x3fff)')
 assert s==(base/'actors.c').read_text()
 r=(ROOT/'input/original.sms').read_bytes();meta=json.loads((ROOT/'analysis/gem_resources.json').read_text());assert meta['source_sha256']==hashlib.sha256(r).hexdigest()
 for row in meta['records']:
  assert row['tile']==r[0x1edc+(row['dungeon']-1)*2] and row['item']==((row['tile']+0x9f)&255)
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),source_files={n:sha(ROOT/'megadrive/src'/n) for n in ['main.c','actors.c','gem_data.c']},only_gem_dispatch_descriptors_reward_variant_and_collection_added=True,existing_actor_loader_and_non_gem_behaviors_unchanged=True,all_nine_original_tile_and_item_indices_verified=True,source_resource_metadata_sha256=sha(ROOT/'analysis/gem_resources.json'),full_game_ported=False)
 (ROOT/'validation/gem_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Gem patch scope and source provenance verified')
if __name__=='__main__':main()
