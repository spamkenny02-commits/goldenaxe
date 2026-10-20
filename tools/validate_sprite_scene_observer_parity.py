"""Plain-core parity and independently recovered intermediate SAT snapshots."""
import contextlib,io,json,struct
from run_core import run
from validate_source_sprite_scene import ROOT,vectors,fixture
from validate_sprite_scene_timed import sha
def body(ram):
 return bytes(ram[0x24:0x28])+bytes([ram[0x303]])+bytes(ram[0x1100:0x1180])+b''.join(bytes(ram[0x300+n*48+0x1b:0x300+n*48+0x1d]) for n in range(32))+bytes(ram[0x1d40:0x1e00])+bytes(ram[0x1f00:0x1fc0])
def main():
 rom,rows=vectors();old=json.loads((ROOT/'analysis/source_sprite_scene_report.json').read_bytes());assert sha(fixture(rom,rows))==old['fixture_sha256']
 results=[];folder=ROOT/'validation/sprite-scene-observer-parity';folder.mkdir(parents=True,exist_ok=True)
 for mode in ['','-irq']:
  source=ROOT/('validation/sprite-scene-timed'+mode);parent=ROOT/('analysis/sprite_scene_timed'+mode.replace('-','_')+'_report.json');reference=json.loads(parent.read_bytes())
  for region in ['ntsc','pal']:
   raw=(source/(region+'-records.bin')).read_bytes();assert sha(raw)==next(x['records_sha256'] for x in reference['results'] if x['region']==region);pos=0;expected={};pcs=set();partial=irqs=0
   while pos<len(raw):
    tag,size=struct.unpack_from('<II',raw,pos);pos+=8;b=raw[pos:pos+size];pos+=size;expected[tag]=b[len(b)-608+24:len(b)-608+24+581]
    active=False
    for i in range(1,size//608):
     delta=(struct.unpack_from('<I',b,i*608+4)[0]-struct.unpack_from('<I',b,(i-1)*608+4)[0])&0xffffffff
     if delta>=4179*15:pcs.add(struct.unpack_from('<I',b,i*608)[0]);irqs+=1;active=True
    final=expected[tag]
    if active and final[389:581] not in (b[24+197:24+389],final[197:389]):partial+=1
   observed={}
   def observe(frame,ram):
    index=int.from_bytes(ram[:2],'little')
    if index<len(rows):observed[index]=body(ram)
   target=folder/(('irq' if mode else 'di')+'-'+region)
   with contextlib.redirect_stdout(io.StringIO()):run(source/'source-fixture.sms',len(rows)*8+25,target,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
   assert observed==expected,(mode,region,[n for n in expected if observed.get(n)!=expected[n]][:5])
   packed=b''.join(struct.pack('<I',n)+observed[n] for n in range(len(rows)));(target/'final-snapshots.bin').write_bytes(packed)
   if mode:assert irqs==84 and partial==10 and len(pcs)>=27
   else:assert not irqs and not partial
   results.append(dict(interrupts=bool(mode),region=region,cases=len(observed),plain_core_same=True,final_snapshots_sha256=sha(packed),source_report_sha256=sha(parent.read_bytes()),irqs=irqs,distinct_irq_resume_pcs=sorted(pcs),partial_sat_snapshots=partial));print(mode or 'di',region,len(observed),'plain-core RAM results identical',flush=True)
 report=dict(previous_fixture_generator_identical=True,plain_core_sha256=sha((ROOT.parents[1]/'work/libretro/genesis_plus_gx_libretro.dll').read_bytes()),results=results,limits=['Read-only observer and official plain core agree on final581-byte scene/snapshot RAM in all cases, same fixture and inputs. Intermediate native/source equivalence uses separate instruction-trace reports. Each controlled IRQ copies192 SAT bytes; ten cases per region retain a snapshot different from both initial and final SAT, demonstrating observation of a genuinely partial table. This is a custom ISR, not the original game IRQ or physical VDP publication proof.'])
 (ROOT/'analysis/sprite_scene_observer_parity_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
