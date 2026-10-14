"""Bind source0940 order selection, unchanged AI and current rendering evidence."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0149-4ba31d49'
 old=(base/'actors.c').read_text();s=(ROOT/'megadrive/src/actors.c').read_text()
 a=old.index('        u16 table=entity[8]',old.index('u16 add_world_actor_sprites'));b=old.index('    }\n    return index;\n}',a);body=old[a:b]
 a=s.index('static u16 add_world_entity_sprites');b=s.index('/* 0951:',a);actual=s[a:b];start=actual.index('    u16 table=');end=actual.rindex('    return index;');actual=actual[start:end]
 expected='\n'.join(l[4:] if l.startswith('    ') else l for l in body.splitlines())+'\n';expected=expected.replace('if(!count || index+count>64) break;','if(!count || index+count>64) return index;');assert actual==expected,'Descriptor emission changed'
 source=(ROOT/'input/original.sms').read_bytes()
 table=re.search(r'static const u8 order\[\]=\{([^}]+)\};',s).group(1)
 slots=[int(x) for x in table.split(',')]
 assert slots==[(int.from_bytes(source[0x30000+i*2:0x30002+i*2],'little')-0xc300)//48 for i in range(80)]
 a=s.index('/* 09EE: one actor descriptor');b=s.index('/* 097E/09EE:',a);s=s[:a]+s[b:]
 s=s.replace('        { u16 next=add_world_entity_sprites(index,entity);if(next==index) break;index=next; }\n',body)
 s=s.replace(',world_object_tick_count;',';').replace('        if(type) world_object_tick_count++;\n','').replace('        world_object_tick_count++;\n','').replace('    if(e[0]) world_object_tick_count++;\n','')
 assert s==old,'Unrelated actor implementation changed'
 old=(base/'main.c').read_text();s=(ROOT/'megadrive/src/main.c').read_text()
 a=s.index('/* Source0940 selects');b=s.index('static void update_hero_sprites_for_frame',a);s=s[:a]+s[b:]
 s=s.replace('static void update_hero_sprites_for_frame(u16 order_phase,bool order_overflow)','static void update_hero_sprites(void)').replace('\nstatic void update_hero_sprites(void)\n{ update_hero_sprites_for_frame(world_clock(),world_sms_sprite_overflow); }\n','')
 a=old.index('    count=game_state==10?0:add_world_actor_sprites');b=old.index('    prepare_world_sms_sprite_overflow(count);',a)
 line='    count=add_world_sprite_scene(order_phase,order_overflow,hero_casting?world_cast_frames+hero_direction*13:world_combat_frames+frame_offset,(hero_x>>8)+hero_scroll_x,(hero_y>>8)+hero_scroll_y,hero_flags&1,game_state!=10);\n'
 assert line in s;s=s.replace(line,old[a:b])
 s=s.replace('    VDP_resetSprites();count=add_world_sprite_scene(world_clock(),world_sms_sprite_overflow,hero_frame,hero_x>>8,hero_y>>8,TRUE,TRUE);\n    prepare_world_sms_sprite_overflow(count);','    VDP_resetSprites();count=add_world_actor_sprites(0,hero_y>>8,255);\n    count=add_sms_sprite_frame(count,hero_x>>8,hero_y>>8,hero_frame,0);\n    count=add_world_actor_sprites(count,-1,hero_y>>8);prepare_world_sms_sprite_overflow(count);')
 s=s.replace('        { u16 order_phase=world_clock();bool order_overflow=world_sms_sprite_overflow;\n          wait_frame();update_hero_sprites_for_frame(order_phase,order_overflow); }','        wait_frame();update_hero_sprites();').replace('            world_object_tick_count=1; /* 26B6 counts the hero before spell/loot/actor visits. */\n','')
 assert s==old,'Unrelated main implementation changed'
 names=['sprite_order_gameplay_report.json','sprite_overflow_report.json','dungeon_melee_attack_5f_entry_report.json','dungeon_melee_attack_60_entry_report.json','dungeon_melee_attack_60_pal_diagnostic.json','dungeon_patrol_61_room_entry_report.json','dungeon_patrol_62_room_entry_report.json','gem_gameplay_report.json','inventory_restore_report.json']+[f'dungeon_guard_combat_{typ}_{mode}_entry_report.json' for typ in ['5c','5d'] for mode in ['allowed','blocked']]
 evidence={}
 for name in names:
  p=ROOT/'validation'/name;d=json.loads(p.read_text());assert d['md_sha256']==sha(ROOT/'gaw-megadrive.bin');evidence[name]=sha(p)
 d=json.loads((ROOT/'validation'/names[0]).read_text());assert len(d['cases'])==18 and all(c['sat_frames_exact']==18 and c['all_four_phases'] for c in d['cases'])
 assert all(c['source_object_counts']==[6] and c['source_overflow_phases']==[0,1,2,3] for c in d['cases'] if c['segment']=='overflow')
 d=json.loads((ROOT/'validation'/names[4]).read_text());assert d['sat_exact_frames']==33 and not d['sat_differences'] and d['attack_reset_and_reversal_exact']
 for name in names[2:4]:
  d=json.loads((ROOT/'validation'/name).read_text());assert all(c['controlled_cycle_sat_frames_exact']==33 and c['controlled_cycle_actor_hero_gold_sound_frames_exact']==34 for c in d['cases'])
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(rom[i:i+2],'big') for i in range(512,len(rom),2))&65535
 assert int.from_bytes(rom[0x18e:0x190],'big')==checksum and rom[0x1a4:0x1a8]==bytes.fromhex('000fffff') and rom[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),rom_bytes=len(rom),checksum=checksum,aliases_header_verified=True,source_80_order_indices_exact=True,prior_AI_unchanged_since_v0149=True,descriptor_emission_unchanged=True,changes_confined_to_object_visit_count_rotating_order_scene_composition_and_pre_IRQ_order_context=True,actual_60_PAL_3702_gap_resolved=True,evidence_sha256=evidence,full_game_ported=False,limits=['Controlled initial world clocks and object fixtures in ordering matrix; source status and VRAM are not overwritten.','Actual-room attack cases use controlled combat setup and exclude injection SAT frame. Room appearance alignment does not establish absolute loading cadence.','Source auxiliary slots2..8 have no native records yet. The MD still draws beyond eight SMS sprites per scanline; source-equivalent pixel clipping/flicker is not established by SAT order/status equality.','Original RNG/global clock, full framebuffer/audio, progression/quests/ending and a complete natural playthrough remain incomplete or unverified.'])
 (ROOT/'validation/sprite_order_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Source order table, unchanged AI/emission, ROM integrity and thirteen current reports verified; PAL3702 gap resolved.')
if __name__=='__main__':main()
