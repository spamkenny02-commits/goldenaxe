"""Physical SGDK output of full native-room mirrors versus planar SMS pixels."""
import contextlib,gzip,io,json,os,random,subprocess
from PIL import Image
from run_core import ROOT,run
from archive_lossless_evidence import sha
from validate_playable_sprite_limit import symbols
from validate_sms_sprite8 import source_plane
def load_cases():
 archive=ROOT/'analysis/native-room-contours-v0275';manifest=json.loads((archive/'manifest.json').read_bytes());e=manifest['compressed']['validation/native-room-contours/cases.json'];encoded=(archive/e['stored']).read_bytes();assert sha(encoded)==e['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==e['raw_sha256'];vectors=json.loads(raw);out=[]
 for i,v in enumerate(vectors):out.append(dict(name='native-room-'+str(i),vram=v['patterns'],cram=v['after_body'][0x1ca0:0x1cc0],regs=[6,224,4,0,0,0]))
 source=ROOT/'validation/sms-vertical-check';capture=json.loads((source/'capture.json').read_bytes());assert capture['rom_sha256']==sha((ROOT/'input/original.sms').read_bytes())
 for frame in [3101,3120,3160]:
  vram=(source/f'vram_{frame:05d}.bin').read_bytes();raw_cram=(source/f'cram_{frame:05d}.bin').read_bytes();regs=(source/f'vdp_regs_{frame:05d}.bin').read_bytes();assert not regs[8] and not regs[9] and (regs[2]&14)==14 and (regs[5]&126)==126
  out.append(dict(name='original-sms-'+str(frame),vram=list(vram[:16384]),cram=[raw_cram[n*2]&63 for n in range(32)],regs=[regs[n] for n in [0,1,6,7,8,9]],capture_sha256={k:sha(v) for k,v in [('vram',vram),('cram',raw_cram),('registers',regs)]}))
 rng=random.Random(0x5e002002)
 for reg0 in [4,12,36,44]:
  for count in [0,9,64]:
   v=bytearray(rng.randbytes(16384));palette=list(range(0,64,2));sat=bytearray([208]*192)
   for i in range(count):sat[i]=255 if i==0 else 191 if i==1 else 63;sat[64+i*2]=(i*23)&255;sat[65+i*2]=(i*7)&255
   v[0x3f00:0x3f40]=sat[:64];v[0x3f80:0x4000]=sat[64:]
   for n in range(768):
    word=(n%256)|((n&1)<<9)|((n&2)<<9)|((n&4)<<9)|((n&8)<<9);v[0x3800+n*2:0x3802+n*2]=word.to_bytes(2,'little')
   out.append(dict(name=f'synthetic-{reg0}-{count}',vram=list(v),cram=palette,regs=[reg0,224,4,7,0,0]))
 return out,sha(raw)
def expected(case,colors):
 v=case['vram'];cram=case['cram'];reg0,_,reg6,reg7,*_=case['regs'];sat=bytes(v[0x3f00:0x3f40]+v[0x3f80:0x4000]);sprites,overflow,count=source_plane(sat,v,reg0,reg6);pixels=[]
 for y in range(192):
  for x in range(256):
   a=0x3800+(y//8*32+x//8)*2;word=v[a]|(v[a+1]<<8);xx=(7-(x&7)) if word&512 else x&7;yy=(7-(y&7)) if word&1024 else y&7;address=(word&511)*32+yy*4;color=sum(((v[address+p]>>(7-xx))&1)<<p for p in range(4));sprite=sprites[y*256+x]
   index=(16 if word&2048 else 0)+color
   if sprite and not (word&4096 and color):index=16+sprite
   if reg0&32 and x<8:index=16+(reg7&15)
   value=cram[index]&63;pixels.append(tuple(colors[ch][(value>>(ch*2))&3] for ch in range(3)))
 result=Image.new('RGB',(256,192));result.putdata(pixels);return result,count,overflow
def main():
 cases,provenance=load_cases();folder=ROOT/'validation/md-source-room-frame';src=folder/'src';src.mkdir(parents=True,exist_ok=True);array=lambda v:'{'+','.join(str(n)+'UL' for n in v)+'}'
 lines=['typedef struct {u8 vram[16384],cram[32],regs[6];} Case;','static const Case cases[]={']
 for case in cases:lines.append('{'+','.join(array(case[k]) for k in ['vram','cram','regs'])+'},')
 lines.append('};');(src/'cases.h').write_bytes(('\n'.join(lines)+'\n').encode())
 for n in ['md_source_room_frame','pattern_convert','source_sms_sprite8']:(src/(n+'.c')).write_bytes(('#include "../../../megadrive/src/'+n+'.c"\n').encode())
 (src/'main.c').write_bytes(r'''#include <genesis.h>
#include "../../../megadrive/src/md_source_room_frame.h"
#include "cases.h"
static MdSourceRoomFrame frame;
volatile u16 gaw_case,gaw_ready,gaw_request,gaw_status,gaw_done;
int main(bool reset)
{
 u16 n;VDP_setScreenWidth256();VDP_setPlaneSize(64,32,TRUE);VDP_setScrollingMode(HSCROLL_PLANE,VSCROLL_PLANE);
 for(n=0;n<sizeof(cases)/sizeof(cases[0]);n++)
 {
  const Case *c=cases+n;gaw_ready=0;SYS_disableInts();VDP_setEnable(FALSE);
  gaw_status=md_source_room_frame_upload(&frame,c->vram,c->cram,c->regs[0],c->regs[1],c->regs[2],c->regs[3],c->regs[4],c->regs[5]);
  VDP_setEnable(TRUE);SYS_enableInts();gaw_case=n;gaw_ready=1;
  while(!gaw_request){SYS_doVBlankProcess();}gaw_request=0;
 }
 gaw_done=1;while(TRUE)SYS_doVBlankProcess();return 0;
}
'''.encode())
 sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];sdkpath=str(sdk).replace('\\','/');sdkunix='/'+sdkpath[0].lower()+sdkpath[2:]
 built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',sdkpath,sdkunix],cwd=folder,env=env,capture_output=True,text=True);(folder/'build.log').write_bytes((built.stdout+built.stderr).encode());assert built.returncode==0,built.stderr[-3000:]
 cart=folder/'out/release/rom.bin';sy=symbols(folder/'out/release/symbol.txt');calibration=json.loads((ROOT/'analysis/md_sprite8_palette_report.json').read_bytes());results=[]
 for region,label in [('auto','ntsc'),('pal','pal')]:
  capture=set();pending=[];schedule={};seen=set();state={};dest=folder/region
  def observe(f,r):
   value=lambda n:int.from_bytes(bytes(r[((sy[n]&65535)+i)^1] for i in range(2)),'big');state.update(done=value('gaw_done'))
   if value('gaw_ready'):
    index=value('gaw_case');assert not value('gaw_status'),(region,index,'upload rejected')
    if index not in seen:seen.add(index);schedule[index]=f+1;capture.add(f+1)
    if f==schedule[index]:pending[:]=[(f+1,sy['gaw_request']&65535,b'\0\1')]
  with contextlib.redirect_stdout(io.StringIO()):run(cart,2000,dest,capture,[],skip_intro=False,ram_writes=pending,ram_observer=observe,stop_when=lambda:bool(state.get('done')),core_options={'genesis_plus_gx_region_detect':region})
  assert len(seen)==len(cases) and state['done'];cal=next(c for c in calibration['results'] if c['region']==label);rgb=[{}, {}, {}]
  for packed,values in zip(cal['palette_packed'],cal['colors']):
   for ch,v in enumerate(values):rgb[ch][(packed>>(ch*3))&7]=v
  colors=[[rgb[ch][n] for n in [0,3,5,7]] for ch in range(3)]
  for index,case in enumerate(cases):
   image_path=dest/f'frame_{schedule[index]:05d}.png';actual=Image.open(image_path).convert('RGB');oracle,count,overflow=expected(case,colors);assert actual.size==(256,224)
   viewport=actual.crop((0,16,256,208));differences=sum(a!=b for a,b in zip(viewport.getdata(),oracle.getdata()));oracle.save(dest/f'expected-{index:02d}.png');assert not differences,(region,index,case['name'],differences)
   assert all(pixel==(0,0,0) for pixel in actual.crop((0,0,256,16)).getdata()) and all(pixel==(0,0,0) for pixel in actual.crop((0,208,256,224)).getdata())
   results.append(dict(region=region,name=case['name'],frame=schedule[index],sprites=count,overflow=overflow,differences=differences,image_sha256=sha(image_path.read_bytes()),source_capture_sha256=case.get('capture_sha256')));print(results[-1],flush=True)
 report=dict(passed=True,cases=len(cases),native_images=len(results),results=results,module_sha256={n+'.c':sha((ROOT/'megadrive/src'/(n+'.c')).read_bytes()) for n in ['md_source_room_frame','pattern_convert','source_sms_sprite8']},headers_sha256={'md_source_room_frame.h':sha((ROOT/'megadrive/src/md_source_room_frame.h').read_bytes())},input_native_chain_cases_sha256=provenance,calibration_sha256=sha((ROOT/'analysis/md_sprite8_palette_report.json').read_bytes()),test_rom_sha256=sha(cart.read_bytes()),production_clock_wired=False,limits=['Physical SGDK output,24 final native-loader mirrors,3 original SMS VDP captures and12 synthetic mode4 scenes in both regions. Entire256x192 RGB viewport compared to an independent planar pixel oracle; padding must be black.','Static unscrolled3800 room,8x8/no zoom only. Mirror inputs outside already source-checked ranges retain native provenance; no natural campaign or transition/scroll/byte-deadline proof.'])
 (ROOT/'analysis/md_source_room_frame_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
if __name__=='__main__':main()
