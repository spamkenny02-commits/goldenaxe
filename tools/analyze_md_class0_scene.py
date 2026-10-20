"""Physical scene DMA/phase/clock audit; no counter or duration-based commit inference."""
import argparse,gzip,hashlib,json,re
from bisect import bisect_left,bisect_right
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--variants',nargs='+',default=['class0-scene-bounded-proof','class0-scene-bounded-native']);p.add_argument('--archive',default='md-class0-scene-v0203');p.add_argument('--report-name',default='md_class0_scene_physical_report.json');args=p.parse_args()
 assert all(re.fullmatch('[a-z0-9-]+',v) for v in args.variants+[args.archive]);assert re.fullmatch('[a-z0-9_]+.json',args.report_name)
 archive=ROOT/'analysis'/args.archive;manifest=None
 def read(path):
  nonlocal manifest
  if path.exists():return path.read_bytes()
  if manifest is None:manifest=json.loads((archive/'manifest.json').read_bytes())
  name=path.relative_to(ROOT).as_posix()
  if name in manifest['files']:
   b=(archive/name).read_bytes();assert sha(b)==manifest['files'][name];return b
  item=manifest['compressed'][name];encoded=(archive/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];b=gzip.decompress(encoded);assert sha(b)==item['raw_sha256'] and len(b)==item['raw_bytes'];return b
 hvc=(ROOT.parents[1]/'work/genesis-plus-gx/core/hvc.h').read_bytes();section=hvc.decode().split('static const uint8 cycle2hc32[3420] =')[1].split('};')[0];h=[int(v,16) for v in re.findall('0x([0-9a-fA-F]+)',section)];assert len(h)==3420
 results=[]
 for variant in args.variants:
  folder=ROOT/('validation/md-z80-psg-'+variant);raw_report=read(ROOT/('analysis/md_z80_psg_'+variant.replace('-','_')+'_report.json'));report=json.loads(raw_report);assert report['video_scene']
  symbols={m[2]:int(m[1],16) for line in read(folder/'out/release/symbol.txt').decode().splitlines() if (m:=re.match('([0-9a-fA-F]+) [a-zA-Z] (.+)',line))}
  scene=next(v for k,v in symbols.items() if k.split('.')[0]=='scene');kernel=read(folder/'out/release/rom.bin');assert sha(kernel)==report['kernel_sha256']
  # Reviewed A1 control/D0 length/D4,D3,D1 source/A2 scene address,
  # scene+10/+12 command words and absolute BUSREQ release.
  signature=bytes.fromhex('227c00c00004328032bc940032843283328145f9')+scene.to_bytes(4,'big')+bytes.fromhex('3039')+(scene+10).to_bytes(4,'big')+bytes.fromhex('32803039')+(scene+12).to_bytes(4,'big')+bytes.fromhex('328033fc000000a11100')
  # Second reviewed allocation: A0 control/D4,D3,A1 source, then A1 scene.
  alternate=bytes.fromhex('207c00c00004308030bc940030843083308943f9')+scene.to_bytes(4,'big')+bytes.fromhex('3039')+(scene+10).to_bytes(4,'big')+bytes.fromhex('30803039')+(scene+12).to_bytes(4,'big')+bytes.fromhex('308033fc000000a11100')
  candidates=[signature,alternate];assert sum(kernel.count(v) for v in candidates)==1
  signature=next(v for v in candidates if kernel.count(v)==1);commit_pc=kernel.index(signature)+len(signature)
  driver=read(folder/'driver.bin');listing=read(folder/'driver.lst').decode();assert sha(driver)==report['driver_sha256']
  sample=int(re.search(r'^\d+\s+([0-9A-F]+)[^\n]*sample:\s+ld a,\(0x7f08\)',listing,re.M)[1],16);refresh=int(re.search(r'^\d+\s+([0-9A-F]+)[^\n]*resample:',listing,re.M)[1],16)
  assert driver[sample:sample+3]==driver[refresh:refresh+3]==bytes.fromhex('3a087f');pcs={sample+3,refresh+3}
  for rr in report['results']:
   region=rr['region'];lines=262 if region=='ntsc' else 313;raw=read(folder/(region+'-events.json'));assert sha(raw)==rr['events_sha256'];events=json.loads(raw)['events'];marks=[i for i,e in enumerate(events) if e[0]==3 and 128<=e[2]<176];assert len(marks)==48;rows=[]
   def blank(a,b):return all((line+224)%lines>=224 for line in range(a//3420,b//3420+1))
   def beam(e):
    physical=(e[1]//3420+224)%lines;v=(physical if physical<=(234 if lines==262 else 258) else physical-lines)&255
    assert e[2]==v*256+h[e[1]%3420];return v
   for n,mark in enumerate(marks):
    part=events[mark+1:marks[n+1] if n+1<len(marks) else len(events)];ref=rr['rows'][n];assert ref['marker']==events[mark][2]
    origin=next(e[1]//3420*3420 for e in part if e[0]==6 and e[2]>>8==100)
    phases={tag:[e[1] for e in part if e[0]==3 and e[2]==tag] for tag in [0x38,0x39,0x3a,0x3b,0x3c]}
    assert all(len(phases[tag])==1 for tag in [0x38,0x39,0x3a]);assert phases[0x38][0]<phases[0x39][0]<phases[0x3a][0]<origin+ref['loader_finish_master']
    start=None;commits=[]
    for e in part:
     if e[0]==7:
      if e[2] and start is None:start=e[1]
      elif not e[2] and start is not None:
       if e[3]==commit_pc:commits.append((start,e[1]))
       start=None
    assert len(commits)==73
    beams=[e for e in part if e[0]==4];bt=[e[1] for e in beams];zt=[e[1] for e in part if e[0]==6];hold=[]
    for k,(a,b) in enumerate(commits):
     assert a>=phases[0x38 if k<49 else 0x39][0] and blank(a,b)
     held=beams[bisect_right(bt,a):bisect_left(bt,b)];assert len(held)==1
     v=beam(held[0]);assert 224<=v<=228 or 235<=v<=252
     assert b-held[0][1]<6840 and b-a<17100
     assert bisect_right(zt,held[0][1])==bisect_left(zt,b);hold.append(b-a)
    private=[e[1] for e in part if e[0]==6 and e[3] in pcs];gaps=[b-a for a,b in zip(private,private[1:])];assert gaps and max(gaps)<17100
    palette_ticks=None
    trace=report.get('scene_palette_trace',True)
    if trace:
     assert len(phases[0x3b])==len(phases[0x3c])==1;a,b=phases[0x3b][0],phases[0x3c][0]
     assert a>=phases[0x3a][0] and a>commits[-1][1] and blank(a,b) and 0<b-a<27360
     assert not any(e[0]==7 and a<=e[1]<=b for e in part)
     guard=beams[bisect_left(bt,a)-1];assert 235<=beam(guard)<=243;palette_ticks=b-a
    else:assert not phases[0x3b] and not phases[0x3c]
    rows.append(dict(marker=ref['marker'],dma_commits=73,pattern_spans=49,map_rows=24,hold_max=max(hold),private_gap_max=max(gaps),during_loader=sum(b-origin<ref['loader_finish_master'] for a,b in commits),palette_trace_master=palette_ticks,last_dma_after_loader_frames=max(0,commits[-1][1]-origin-ref['loader_finish_master'])/(lines*3420)))
   results.append(dict(variant=variant,region=region,kernel_sha256=report['kernel_sha256'],report_sha256=sha(raw_report),events_sha256=sha(raw),signature_hex=signature.hex(),commit_pc=commit_pc,dma_commits=sum(r['dma_commits'] for r in rows),during_loader=sum(r['during_loader'] for r in rows),hold_max=max(r['hold_max'] for r in rows),private_gap_max=max(r['private_gap_max'] for r in rows),palette_trace=trace,rows=rows));print({k:v for k,v in results[-1].items() if k not in ['rows','signature_hex']},flush=True)
 output=dict(hvc_sha256=sha(hvc),results=results,limits=['Commits identified by unique reviewed native instruction signature, not counters/duration. All DMA holds and native HV guards independently checked in physical VBlank; FIFO49pattern spans then24map rows, phase availability and private clock gaps verified. Palette CPU write/readback span checked only in trace-enabled kernels; default path has final CRAM and native per-case readback evidence, not a physical CPU-span trace. Native IRQs masked, display remains enabled during pipeline, sprites absent. No fullboot/fullgame/real-hardware/frame-deadline/waveform claim.'])
 (ROOT/'analysis'/args.report_name).write_text(json.dumps(output,indent=2)+'\n')
if __name__=='__main__':main()
