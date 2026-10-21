"""Playable SMS192-line viewport: no sprites in the MD letterbox bands."""
import contextlib,gzip,io,json
from PIL import Image
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols
from validate_playable_sprite_end import entries
from validate_sprite_scene_timed import sha

def previous_symbols():
 folder=ROOT/'analysis/world-publication-v0218';m=json.loads((folder/'manifest.json').read_bytes());name='megadrive/out/release/symbol.txt'
 if name in m['files']:b=(folder/name).read_bytes();assert sha(b)==m['files'][name]
 else:
  item=m['compressed'][name];encoded=(folder/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];b=gzip.decompress(encoded);assert sha(b)==item['raw_sha256']
 path=ROOT/'validation/v0218-symbols.txt';path.write_bytes(b);return path

def sprite_plane(vram,limit=16):
 v=bytes(vram[n^1] for n in range(65536));sprites=entries(vram);out=bytearray(256*224)
 for y in range(224):
  selected=[(e,y-((int.from_bytes(e[:2],'big')&511)-128)) for e in sprites if (int.from_bytes(e[:2],'big')&511)-128<=y<(int.from_bytes(e[:2],'big')&511)-120][:limit]
  for e,row in reversed(selected):
   x=(int.from_bytes(e[6:8],'big')&511)-128;tile=int.from_bytes(e[4:6],'big')&2047;word=int.from_bytes(v[tile*32+row*4:tile*32+row*4+4],'big')
   for column in range(8):
    color=(word>>((7-column)*4))&15
    if color and 0<=x+column<256:out[y*256+x+column]=color
 return bytes(out)

def main():
 folder=ROOT/'validation/playable-sprite-viewport-v0219';folder.mkdir(exist_ok=True);new=ROOT/'gaw-megadrive.bin';old=ROOT/'versions/v0218-399be6a3/gaw-megadrive-v0218.bin';oldsy=previous_symbols();results=[];regs=(ROOT/'validation/sms-vertical-check/vdp_regs_03120.bin').read_bytes();assert regs[0]&4 and not regs[0]&40 and not regs[1]&0x1b
 for region in ['auto','pal']:
  for label,y in [('above_all',0),('above_partial',5),('top_partial',12),('bottom_partial',205),('below_all',209)]:
   rows={}
   for tag,rom,syfile in [('old',old,oldsy),('new',new,ROOT/'megadrive/out/release/symbol.txt')]:
    sy=symbols(syfile);actors=bytearray(768);e=bytearray((ROOT/'validation/sms-vertical-check/ram_03120.bin').read_bytes()[0x600:0x630]);e[3]=1;e[4]=120;e[5]=0;e[6]=255;e[0x11]=y;e[0x13]=64;actors[:48]=e
    writes=[write for f in range(3127,3141) for write in [(f,sy['world_actor_state'],bytes(actors)),(f,sy['world_loot_state'],bytes(336)),(f,sy['world_spell_state'],bytes(48))]];states={};d=folder/(region+'-'+label+'-'+tag)
    def ram(f,r):
     if f<3131:return
     value=lambda name:int.from_bytes(bytes(r[(sy[name]+i)^1] for i in range(2)),'big');states[f]={name:value(name) for name in ['game_state','room_id','hero_x','hero_y','world_sms_sprite_prepared_overflow']}
    with contextlib.redirect_stdout(io.StringIO()):run(rom,3140,d,set(range(3131,3141)),PRESSES,ram_writes=writes,ram_observer=ram,core_options={'genesis_plus_gx_region_detect':region})
    rows[tag]=(states,d)
   assert rows['old'][0]==rows['new'][0],(region,label,'gameplay/overflow state changed');assert all(not r['world_sms_sprite_prepared_overflow'] for r in rows['new'][0].values())
   removed=0;matte_pixels=0
   for f in range(3131,3141):
    before=(rows['old'][1]/f'vram_{f:05d}.bin').read_bytes();after=(rows['new'][1]/f'vram_{f:05d}.bin').read_bytes();original=sprite_plane(before,8);actual=sprite_plane(after,16);expected=bytes(256*16)+original[256*16:256*208]+bytes(256*16)
    assert actual==expected,(region,label,f,'SMS viewport mismatch');assert len(entries(before))==len(entries(after))==8,(region,label,f,'fixture/SAT entry count')
    removed+=sum(a!=b for a,b in zip(original,actual))
    image=Image.open(rows['new'][1]/f'frame_{f:05d}.png').convert('RGB')
    assert all(image.getpixel((x,yy))==(0,0,0) for yy in list(range(16))+list(range(208,224)) for x in range(256)),(region,label,f,'non-black matte')
    matte_pixels+=32*256
   assert removed>0,(region,label,'fixture did not expose original leak')
   results.append(dict(region=region,case=label,entity_y=y,frames=10,sprite_plane_pixels_compared=10*256*224,matte_rgb_pixels_compared=matte_pixels,removed_outside_sms_pixels=removed,inside_sms_pixels_identical=True,sat_count_preserved=True,overflow_status_preserved=True));print(results[-1],flush=True)
 report=dict(md_sha256=sha(new.read_bytes()),reference_sha256=sha(old.read_bytes()),cases=results,passed=True,scope='Full playable boot/controller path then one frozen actor at five boundary heights; no overflow fixture. Physical224-line MD sprite plane equals original source192-line crop. Every matte RGB pixel is black; valid rows, list length and overflow state unchanged. World source mode4/192,8x8/nozoom, no horizontal shift/left mask. No whole-game/hardware-console claim.')
 (ROOT/'analysis/playable_sprite_viewport_v0219_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
