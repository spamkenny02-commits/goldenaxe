"""Execute original sprite/wait/IRQ frame comparisons on native68000."""
import contextlib,io,json,os,re,struct,subprocess
from pathlib import Path
from game_sprite_frame_fixture import ROOT,generate,unpack_body
from validate_game_sprite_frame import WRAPPER,MODULES
from validate_sprite_scene_timed import sha
from run_core import run
MAIN=r'''
extern const u8 frame_inputs[][8192],frame_low[],frame_bank6[],frame_bank12[],frame_ntsc[],frame_pal[];
static u8 ram[8192],saved[8192];
volatile u32 gaw_checks,gaw_failures,gaw_case,gaw_kind,gaw_error,gaw_detail,gaw_expected,gaw_actual,gaw_irqs,gaw_sat,gaw_psg;
volatile u16 gaw_done;
static void seed(const u8 *input,const u8 *point) {
 u16 n;const u8 *p=point+28;memcpy(ram,input,8192);memcpy(ram,p,80);p+=80;ram[0x303]=*p++;
 memcpy(ram+0x1100,p,128);p+=128;
 for(n=0;n<32;n++) {memcpy(ram+0x300+n*48+0x1b,p,2);p+=2;}
 memcpy(ram+0x1d00,p,256);p+=256;memcpy(ram+0x1e00,p,400);p+=400;ram[0x1fff]=*p;
}
int main(bool reset) {
 u16 row,region=SYS_isPAL()?1:0;const u8 *all=region?frame_pal:frame_ntsc,*p,*psg,*sat,*statuses;
 u32 first[32],second[32];const u32 *h;(void)reset;SYS_disableInts();VDP_setEnable(FALSE);
 if(!game_frame_contracts(frame_low,frame_bank6,region?313:262)) {gaw_failures++;gaw_kind=6;}
 for(row=0;row<FRAME_CASES && !gaw_failures;row++) {
  gaw_case=row;h=frame_offsets[region][row];p=all+h[0];psg=all+h[2];sat=all+h[4];statuses=all+h[6];
  seed(frame_inputs[row],p);
  if(!game_frame_case(ram,frame_low,frame_bank6,frame_bank12,region?313:262,p,h[1],psg,h[3],sat,h[5],statuses,h[7],1,first)) {
   gaw_failures++;gaw_kind=first[0];gaw_detail=first[1];gaw_error=first[2];gaw_expected=first[3];gaw_actual=first[4];break;
  }
  memcpy(saved,ram,8192);seed(frame_inputs[row],p);
  if(!game_frame_case(ram,frame_low,frame_bank6,frame_bank12,region?313:262,p,h[1],psg,h[3],sat,h[5],statuses,h[7],0,second) ||
     memcmp(saved,ram,8192) || memcmp(first+9,second+9,92)) {
   gaw_failures++;gaw_kind=5;gaw_error=second[2];gaw_detail=second[1];break;
  }
  gaw_checks++;gaw_irqs+=first[9];gaw_sat+=first[10];gaw_psg+=first[11];
 }
 gaw_done=1;while(TRUE) __asm__ volatile("nop");return 0;
}
'''
def records(path):
 b=path.read_bytes();p=0;rows=[]
 while p<len(b):
  tag,size=struct.unpack_from('<II',b,p);p+=8;assert tag==len(rows);rows.append(b[p:p+size]);p+=size
 assert p==len(b);return rows

def main():
 image,rows,_=generate();source=ROOT/'validation/game-sprite-frame';folder=ROOT/'validation/game-sprite-frame-68k';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
 parent=ROOT/'analysis/game_sprite_frame_report.json';report=json.loads(parent.read_bytes());offsets=[];totals={}
 for region in ['ntsc','pal']:
  points=records(source/(region+'-points.bin'));ports=records(source/(region+'-ports.bin'));packed=bytearray();headers=[];irqs=sat=psg=0
  assert sha((source/(region+'-points.bin')).read_bytes())==next(r['points_sha256'] for r in report['results'] if r['region']==region)
  assert sha((source/(region+'-ports.bin')).read_bytes())==next(r['ports_sha256'] for r in report['results'] if r['region']==region)
  for raw,port in zip(points,ports):
   selected=[b''.join(raw[k:k+960] for k in range(0,len(raw),960) if (struct.unpack_from('<I',raw,k)[0]==0x137)==flag) for flag in [False,True]]
   streams=[b''.join(port[k:k+20] for k in range(0,len(port),20) if struct.unpack_from('<I',port,k)[0]==kind) for kind in [1,2]]
   h=[]
   for b,size in [(selected[0],960),(streams[0],20),(streams[1],20),(selected[1],960)]:h.extend([len(packed),len(b)//size]);packed.extend(b)
   headers.append(h);irqs+=len(selected[1])//960;sat+=len(streams[1])//(20*192);psg+=len(streams[0])//20
  (src/(region+'.bin')).write_bytes(packed);offsets.append(headers);totals[region]=dict(irqs=irqs,sat=sat,psg=psg)
 (src/'inputs.bin').write_bytes(b''.join(raw for _,raw in rows));(src/'low.bin').write_bytes(image[:32768]);(src/'bank6.bin').write_bytes(image[0x18000:0x1c000]);(src/'bank12.bin').write_bytes(image[0x30000:0x34000])
 asm='.section .rodata\n.align 2\n'
 for label in ['inputs','low','bank6','bank12','ntsc','pal']:asm+='.global frame_'+label+'\nframe_'+label+':\n.incbin "src/'+label+'.bin"\n.align 2\n'
 (src/'assets.s').write_bytes(asm.encode());(src/'offsets.h').write_text('#define FRAME_CASES '+str(len(rows))+'\nstatic const u32 frame_offsets[2][FRAME_CASES][8]={'+','.join('{'+','.join('{'+','.join(map(str,h))+'}' for h in region)+'}' for region in offsets)+'};\n')
 (src/'main.c').write_bytes(('#include <genesis.h>\n#include "offsets.h"\n'+WRAPPER+MAIN).encode())
 for name in dict.fromkeys(MODULES):(src/(name+'.c')).write_text('#include "../../../megadrive/src/'+name+'.c"\n')
 (src/'source_game_irq.h').write_text('#include "../../../megadrive/src/source_game_irq.h"\n')
 sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];temp=folder/'compiler-tmp';temp.mkdir(exist_ok=True)
 for key in ['TMPDIR','TMP','TEMP']:env[key]=temp.as_posix()
 path=sdk.as_posix();unix='/'+path[0].lower()+path[2:];built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True);(folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,(built.stdout+built.stderr)[-4000:]
 kernel=folder/'out/release/rom.bin';symbols={m[2]:int(m[1],16) for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match('([0-9a-fA-F]+) [a-zA-Z] (.+)',line))};results=[]
 for region in ['ntsc','pal']:
  observed={}
  def observe(frame,ram):
   def value(name,width):return int.from_bytes(bytes(ram[(((symbols[name]&65535)+n)&65535)^1] for n in range(width)),'big')
   observed.update(frame=frame,done=value('gaw_done',2))
   for name in ['checks','failures','case','kind','error','detail','expected','actual','irqs','sat','psg']:observed[name]=value('gaw_'+name,4)
  with contextlib.redirect_stdout(io.StringIO()):run(kernel,60000,folder/region,set(),[],skip_intro=False,ram_observer=observe,stop_when=lambda:bool(observed.get('done')),core_options={'genesis_plus_gx_region_detect':region})
  assert observed['done'] and observed['checks']==len(rows) and not observed['failures'] and all(observed[k]==v for k,v in totals[region].items()),observed
  results.append(dict(region=region,**observed));print(results[-1],flush=True)
 final=dict(kernel_sha256=sha(kernel.read_bytes()),kernel_bytes=kernel.stat().st_size,source_report_sha256=sha(parent.read_bytes()),results=results,contract_checks_per_region=5,limits=['Native68000 executes the shared-RAM sprite/wait/full IRQ/audio composition. All four checkpoints compare PC/master/raster/R/IFF and930 RAM bytes; every SAT/PSG byte/date and each IRQ entry compare to unchanged original SMS routines. Status and initial entry RAM are supplied hardware inputs, not predicted. Trace-disabled execution also compares full8192-byte final RAM and clock/work results. Diagnostic kernel only; renderer delivery, hardware deadlines and whole-game integration are not proved.'])
 (ROOT/'analysis/game_sprite_frame_68k_report.json').write_text(json.dumps(final,indent=2)+'\n')
if __name__=='__main__':main()
