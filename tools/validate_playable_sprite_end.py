"""Playable SMS SAT D0 terminator, including leading marker and visible prefix."""
import contextlib,gzip,io,json,sys
from pathlib import Path
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols,reference
from validate_sprite_scene_timed import sha

def prior_symbols():
 folder=ROOT/'analysis/playable-sprite-limit-v0210';m=json.loads((folder/'manifest.json').read_bytes());name='megadrive/out/release/symbol.txt';b=(folder/name).read_bytes() if name in m['files'] else gzip.decompress((folder/m['compressed'][name]['stored']).read_bytes());assert sha(b)==(m['files'][name] if name in m['files'] else m['compressed'][name]['raw_sha256']);p=ROOT/'validation/v0210-symbols.txt';p.write_bytes(b);return p

def entries(v):
 raw=bytes(v[n^1] for n in range(65536));out=[];index=0;seen=set()
 while index not in seen:
  seen.add(index);e=raw[0xf400+index*8:0xf408+index*8];out.append(e);index=e[3]&127
  if not index:break
 return out

def main():
 folder=ROOT/'validation/playable-sprite-end-v0218';folder.mkdir(exist_ok=True);new=ROOT/'gaw-megadrive.bin';old=ROOT/'versions/v0210-4678a4f4/gaw-megadrive-v0210.bin';oldsy=prior_symbols();results=[]
 for region in ['auto','pal']:
  for label,count,marker in [('leading',1,0),('prefix',12,5)]:
   snapshots={}
   for tag,rom,syfile in [('old',old,oldsy),('new',new,ROOT/'megadrive/out/release/symbol.txt')]:
    sy=symbols(syfile);actors=bytearray(768);template=(ROOT/'validation/sms-vertical-check/ram_03120.bin').read_bytes()[0x600:0x630]
    for slot in range(count):
     e=bytearray(template);e[3]=1;e[4]=120;e[5]=0;e[6]=255;e[0x11]=225 if slot==marker else 64;e[0x13]=16+slot*18;actors[slot*48:(slot+1)*48]=e
    writes=[write for f in range(3127,3141) for write in [(f,sy['world_actor_state'],bytes(actors)),(f,sy['world_clock_shift'],f.to_bytes(4,'big'))]];states={};sat={}
    def ram(f,r):
     if f<3129:return
     def data(address,n):return bytes(r[(address+i)^1] for i in range(n))
     cache=data(sy['vdpSpriteCache'],64*8);markers=[n for n in range(64) if (int.from_bytes(cache[n*8:n*8+2],'big')-145)&255==208]
     states[f]=dict(state=int.from_bytes(data(sy['game_state'],2),'big'),room=int.from_bytes(data(sy['room_id'],2),'big'),marker=markers[0] if markers else None,actor_types=data(sy['world_actor_state'],768)[::48].hex())
    def video(f,v):
     if f>=3129:sat[f]=entries(v);(folder/(region+'-'+label+'-'+tag+'-'+str(f)+'-vram.bin')).write_bytes(v)
    natural={60,300,1000,1500,2300,2700,3000,3120}
    with contextlib.redirect_stdout(io.StringIO()):run(rom,3140,folder/(region+'-'+label+'-'+tag),natural,PRESSES,ram_writes=writes,ram_observer=ram,vram_observer=video,core_options={'genesis_plus_gx_region_detect':region})
    snapshots[tag]=(states,sat)
   removed=[];prefixes=[]
   for f in range(3131,3141):
    before,oldentries=snapshots['old'][0][f],snapshots['old'][1][f];after,newentries=snapshots['new'][0][f],snapshots['new'][1][f]
    assert before['state']==after['state']==12 and before['room']==after['room'] and before['actor_types']==after['actor_types'],(region,label,f,'simulation')
    if label=='leading':
     assert before['marker']==0 and len(oldentries)>1,(region,label,f,'source marker absent')
     assert len(newentries)==1 and newentries[0][2:6]==bytes(4),(region,label,f,'leading marker must hide all')
     plane,_=reference((folder/(region+'-'+label+'-new-'+str(f)+'-vram.bin')).read_bytes(),0xf400,16);assert plane==bytes(49152),(region,label,f,'visible sprites after leading marker')
     visible=0
    else:
     visible=after['marker'];assert visible is not None and visible>0 and len(newentries)==visible,(region,label,f,after,len(newentries))
     assert all((int.from_bytes(e[:2],'big')-145)&255!=208 for e in newentries)
    removed.append(len(oldentries)-visible);prefixes.append(visible)
   differences=[]
   for f in natural:
    if (folder/(region+'-'+label+'-old')/f'frame_{f:05d}.png').read_bytes()==(folder/(region+'-'+label+'-new')/f'frame_{f:05d}.png').read_bytes():continue
    from PIL import Image,ImageChops
    box=ImageChops.difference(Image.open(folder/(region+'-'+label+'-old')/f'frame_{f:05d}.png').convert('RGB'),Image.open(folder/(region+'-'+label+'-new')/f'frame_{f:05d}.png').convert('RGB')).getbbox();differences.append(dict(frame=f,box=box))
   coherent=False
   if differences:
    proof=json.loads((ROOT/'analysis/world_frame_coherence_v0218_report.json').read_bytes())
    coherent=proof['passed'] and proof['md_sha256']==sha(new.read_bytes()) and all(any(c['region']==region and c['frame']==d['frame'] and not c['differing_pixels'] for c in proof['cases']) for d in differences)
   if '--diagnostic' not in sys.argv:assert not differences or coherent,(region,label,'incoherent natural changes',differences)
   results.append(dict(region=region,case=label,frames=10,visible_prefix_lengths=prefixes,discarded_entries=removed,natural_frames_identical=[f for f in sorted(natural) if f not in [r['frame'] for r in differences]],natural_raster_differences=differences,natural_changes_verified_coherent=coherent,actor_state_preserved=True));print(results[-1],flush=True)
 (ROOT/'analysis/playable_sprite_end_v0218_report.json').write_text(json.dumps(dict(md_sha256=sha(new.read_bytes()),baseline_sha256=sha(old.read_bytes()),cases=results,release_accepted=all(not r['natural_raster_differences'] or r['natural_changes_verified_coherent'] for r in results),scope='Full playable boot/controller route, then controlled actor Y=225 to emit source SAT D0. Leading marker hides all; marker after visible prefix terminates the hardware MD SAT. Types/simulation remain. Changed natural images must pass the independently linked VRAM/CRAM full-frame coherence gate. NPC chronology can differ with the provisional native RNG and earlier publication; no source RNG fidelity claim. No whole-game/timing claim.'),indent=2)+'\n')
if __name__=='__main__':main()
