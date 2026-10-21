"""Recover v0218 physical RGB, source cadence and DMA timing after cleanup."""
import gzip,json
from PIL import Image
import io
from run_core import ROOT
from validate_sprite_scene_timed import sha
from validate_world_frame_coherence import render

def read(path):
 if path.exists():return path.read_bytes()
 archive=ROOT/'analysis/world-publication-v0218';m=json.loads((archive/'manifest.json').read_bytes());name=path.relative_to(ROOT).as_posix()
 if name in m['files']:
  b=(archive/name).read_bytes();assert sha(b)==m['files'][name];return b
 item=m['compressed'][name];encoded=(archive/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded);assert len(raw)==item['raw_bytes'] and sha(raw)==item['raw_sha256'];return raw

def main():
 release=json.loads(read(ROOT/'analysis/world_publication_v0218_report.json'));coherence=json.loads(read(ROOT/'analysis/world_frame_coherence_v0218_report.json'));assert release['passed'] and release['md_sha256']==coherence['md_sha256']==sha(read(ROOT/'gaw-megadrive.bin'));pixels=0
 for name,digest in release['reports'].items():assert sha(read(ROOT/name))==digest,name
 for row in coherence['cases']:
  region=row['region'];f=row['frame'];folder=ROOT/('validation/world-frame-coherence-v0218/'+region);expected=render(read(folder/f'vram_{f:05d}.bin'),read(folder/f'cram_{f:05d}.bin'),read(folder/f'vdp_regs_{f:05d}.bin'));actual=Image.open(io.BytesIO(read(folder/f'frame_{f:05d}.png'))).convert('RGB')
  assert actual.crop((0,16,256,216)).tobytes()==expected.crop((0,16,256,216)).tobytes();pixels+=51200
 steps=0
 for region in ['auto','pal']:
  events=json.loads(read(ROOT/('validation/sms-scroll-cadence/'+region+'-events.json')));groups=[]
  for f,pc,cycles,b,line in events:
   if pc in [0x20ca,0x208a] and b==20:groups.append(dict(direction=1 if pc==0x20ca else 0,rows=[]))
   if pc in [0x20d0,0x2090]:groups[-1]['rows'].append((21-b,f))
  assert len(groups)==2
  states=json.loads(read(ROOT/('validation/world-publish-regression-v0218/'+region+'-vertical-new/states.json')))
  for group in groups:
   native=[];previous=0
   for f,s in states.items():
    if s['game_state']==10 and s['transition_direction']==group['direction'] and s['transition_step']!=previous:
     if s['transition_step']:native.append((s['transition_step'],int(f)+1))
     previous=s['transition_step']
   assert native==group['rows'] and [s for s,f in native]==list(range(1,21));steps+=len(native)
  folder=ROOT/('validation/md-sprite-publish'+('_ntsc' if region=='auto' else ''));events=json.loads(read(folder/'v0218-events.json'));transfers=[e for e in events if 0xf400<=e[2]<0xf600];assert len(transfers)==5
  assert all(e[3]&0x80000000 and e[5]>=224 and e[7]>=224 for e in transfers)
  assert read(folder/'v0218/frame_03120.png')==read(ROOT/('validation/world-frame-coherence-v0218/'+region+'/frame_03120.png'))
 report=dict(md_sha256=release['md_sha256'],rgb_pixels_recovered=pixels,source_published_steps_recovered=steps,sat_dma_transfers_recovered=10,passed=True,limits=['Recovery repeats614400 RGB comparisons and80 source/native frame comparisons from verified immutable evidence. It does not extend release test scope or prove all game paths.'])
 (ROOT/'analysis/world_publication_recovery_v0218_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Recovered',pixels,'RGB pixels,',steps,'source steps and10 VBlank DMA records.')
if __name__=='__main__':main()
