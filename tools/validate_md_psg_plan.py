"""Planner preserves full timed event streams and rejects errors atomically."""
import contextlib
import ctypes as c
import hashlib
import io
import json
import os
import re
import subprocess
from actor_reference import ROOT
from run_core import run

TEST=r'''
#include "source_md_psg_plan.h"
#include "beam_ref.h"
volatile u32 gaw_plan_checks,gaw_plan_failures,gaw_plan_failure_line,gaw_plan_cases;
volatile u32 gaw_plan_beam_cases;
volatile u16 gaw_plan_done;
static SourcePsgEvent events[512];static SourceMdPsgBlock blocks[512];
#define CHECK(x) do {gaw_plan_checks++;if(!(x)) {gaw_plan_failures++;if(!gaw_plan_failure_line) gaw_plan_failure_line=__LINE__;}} while(0)
static u32 random_state=0xc01275ab;
static u32 random_word(void) {random_state=random_state*1664525UL+1013904223UL;return random_state;}
static void validate(u16 count) {
 u16 used=0xffff,k,i,n=0,same=1;u32 time;
 CHECK(source_md_psg_plan(events,count,blocks,512,&used)==0);
 CHECK(used<=count && (used || !count));
 for(k=0;k<used;k++) {
  SourceMdPsgBlock *b=blocks+k;
  if(!b->count || b->count>16 || (b->spacing!=315 && b->spacing!=630 && b->spacing!=0) || (b->spacing==630 && b->count>8) || (!b->spacing && b->count!=1)) {same=0;break;}
  if(b->skip!=(b->spacing==315?(16-b->count)*18:b->spacing==630?(8-b->count)*40:0)) same=0;
  time=b->due;
  for(i=0;i<b->count;i++,n++,time+=b->spacing) {
   if(n>=count || events[n].due!=time || events[n].value!=b->values[16-b->count+i]) same=0;
  }
 }
 CHECK(same && n==count);gaw_plan_cases++;
}
static void rejects(u8 expected,const SourcePsgEvent *input,u16 count,u16 capacity) {
 u16 used=0x5aa5,i;u8 *raw=(u8 *)blocks;
 for(i=0;i<sizeof(SourceMdPsgBlock)*4;i++) raw[i]=0xa5;
 CHECK(source_md_psg_plan(input,count,blocks,capacity,&used)==expected && used==0x5aa5);
 for(i=0;i<sizeof(SourceMdPsgBlock)*4;i++) if(raw[i]!=0xa5) {CHECK(0);return;}
 CHECK(1);
}
static void beam_tests(void) {
 static const u16 phases[]={0,1,19,20,299,300,759,760,3399,3400,3419};
 SourceMdPsgBlock copy;u16 pal,lines,line,p,wrap,rounded,wanted_line,i;u32 epoch,period,offset;u8 same;
 CHECK(source_md_psg_plan_beam(0,0,262,100,0)==0);
 CHECK(source_md_psg_plan_beam(0,1,262,100,0)==1);
 blocks[0].due=0;blocks[0].target_hv=0xa5a5;copy=blocks[0];
 CHECK(source_md_psg_plan_beam(blocks,1,0,0,0)==1 && blocks[0].target_hv==0xa5a5);
 CHECK(source_md_psg_plan_beam(blocks,1,262,262,0)==1 && blocks[0].target_hv==0xa5a5);
 blocks[1]=copy;blocks[1].due=0xffffffffUL;
 CHECK(source_md_psg_plan_beam(blocks,2,262,100,0)==3 && blocks[0].target_hv==0xa5a5 && blocks[1].target_hv==0xa5a5);
 for(pal=0;pal<2;pal++) {
  lines=pal?313:262;period=(u32)lines*3420;
  for(wrap=0;wrap<2;wrap++) for(line=0;line<lines;line++) for(p=0;p<11;p++) {
   epoch=wrap?0xffff0000UL:0;offset=(u32)line*3420+phases[p];
   if(offset<342000UL) offset+=period;
   offset-=342000UL;
   blocks[0].due=epoch+offset;blocks[0].skip=0x1234;blocks[0].count=16;blocks[0].spacing=315;
   for(i=0;i<16;i++) blocks[0].values[i]=(u8)(i*13+p);
   copy=blocks[0];rounded=(phases[p]+19)/20;wanted_line=line;
   if(rounded==171) {rounded=0;wanted_line++;if(wanted_line==lines) wanted_line=0;}
   CHECK(source_md_psg_plan_beam(blocks,1,lines,100,epoch)==0);
   CHECK(blocks[0].target_hv==((pal?v_pal[wanted_line]:v_ntsc[wanted_line])*256+h_reference[rounded]));
   same=blocks[0].due==copy.due && blocks[0].skip==copy.skip && blocks[0].count==copy.count && blocks[0].spacing==copy.spacing;
   for(i=0;i<16;i++) if(blocks[0].values[i]!=copy.values[i]) same=0;
   CHECK(same);gaw_plan_beam_cases++;
  }
 }
}
void plan_test(void) {
 static const u16 gaps[]={0,1,314,315,316,629,630,631,5670};
 u16 n,count,spacing,turn,used;u32 time;
 CHECK(source_md_psg_plan(0,0,0,0,0)==1);
 used=99;CHECK(source_md_psg_plan(0,0,0,0,&used)==0 && !used);
 rejects(1,0,1,4);
 events[0].due=0xfffffff0UL;events[0].value=7;
 rejects(2,events,1,0);
 events[1].due=events[0].due-1;events[1].value=8;rejects(3,events,2,4);
 events[1].due=events[0].due+0x80000000UL;rejects(3,events,2,4);
 events[1].due=events[0].due+0x40000000UL;events[2].due=events[0].due+0x80000000UL;rejects(3,events,3,4);
 for(spacing=315;spacing<=630;spacing+=315) for(count=1;count<=512;count++) {
  for(n=0;n<count;n++) {events[n].due=0xffff0000UL+(u32)n*spacing;events[n].value=(u8)(n*13+count);}
  validate(count);
 }
#ifdef SGDK_GCC
 for(turn=0;turn<1000;turn++)
#else
 for(turn=0;turn<20000;turn++)
#endif
 {
  count=1+(random_word()>>16)%64;time=random_word();
  for(n=0;n<count;n++) {time+=gaps[(random_word()>>16)%9];events[n].due=time;events[n].value=(u8)random_word();}
  validate(count);
 }
 beam_tests();gaw_plan_done=1;
}
'''


def main():
    folder=ROOT/'validation/md-psg-plan';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    core=ROOT.parents[1]/'work/genesis-plus-gx/core'
    hvc_raw=(core/'hvc.h').read_bytes();ctrl_raw=(core/'vdp_ctrl.c').read_bytes()
    h_text=hvc_raw.decode().split('static const uint8 cycle2hc32[3420] =')[1].split('};')[0]
    h=[int(x,16) for x in re.findall(r'0x([0-9a-fA-F]+)',h_text)];assert len(h)==3420
    vc_section=ctrl_raw.decode().split('static const uint16 vc_table[4][2] =')[1].split('};')[0]
    maxima=[tuple(int(x,16) for x in pair) for pair in re.findall(r'\{\s*0x([0-9a-fA-F]+)\s*,\s*0x([0-9a-fA-F]+)',vc_section)][1]
    ref='static const u16 h_reference[]={'+','.join(str(h[n]) for n in range(0,3420,20))+'};\n'
    for name,lines,maximum in [('ntsc',262,maxima[0]),('pal',313,maxima[1])]:
        ref+='static const u16 v_'+name+'[]={'+','.join(str((line if line<=maximum else line-lines)&255) for line in range(lines))+'};\n'
    (src/'beam_ref.h').write_text(ref)
    (src/'test.h').write_text(TEST);(folder/'host.c').write_text('#ifndef SGDK_GCC\n#include "src/test.h"\n#endif\n')
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(folder/'host.c'),str(ROOT/'megadrive/src/source_md_psg_plan.c'),'-o',str(folder/'host.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'host-build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
    dll=c.CDLL(str(folder/'host.dll'));dll.plan_test();host={n:c.c_uint32.in_dll(dll,'gaw_plan_'+n).value for n in ['checks','failures','failure_line','cases','beam_cases']};assert not host['failures'],host
    print('Host',host,flush=True)
    (src/'source_md_psg_plan.c').write_text('#include "../../../megadrive/src/source_md_psg_plan.c"\n')
    (src/'source_md_psg_plan.h').write_text('#include "../../../megadrive/src/source_md_psg_plan.h"\n')
    (src/'main.c').write_text('#include <genesis.h>\n#include "test.h"\nint main(bool hard_reset) {(void)hard_reset;VDP_setEnable(FALSE);SYS_disableInts();plan_test();while(TRUE) {}return 0;}\n')
    env['PATH']=str(sdk/'bin')+';'+env['PATH'];temporary=folder/'compiler-tmp';temporary.mkdir(exist_ok=True)
    for key in ['TMPDIR','TMP','TEMP']:env[key]=temporary.resolve().as_posix()
    path=sdk.as_posix();unix='/'+path[0].lower()+path[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True)
    (folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2000:]
    symbols={m[2]:int(m[1],16)&65535 for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};results=[]
    for region in ['ntsc','pal']:
        observed={}
        def observe(frame,ram):
            def value(name,width):return int.from_bytes(bytes(ram[(symbols['gaw_plan_'+name]+i)^1] for i in range(width)),'big')
            observed.update(frame=frame,done=value('done',2),**{n:value(n,4) for n in ['checks','failures','failure_line','cases','beam_cases']})
        with contextlib.redirect_stdout(io.StringIO()):
            run(folder/'out/release/rom.bin',20000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        assert observed.get('done') and not observed['failures'] and observed['cases']==2024 and observed['beam_cases']==12650,observed
        results.append(dict(region=region,**observed));print(results[-1],flush=True)
    sha=lambda raw:hashlib.sha256(raw).hexdigest()
    report=dict(host=host,results=results,kernel_sha256=sha((folder/'out/release/rom.bin').read_bytes()),sources={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['source_md_psg_plan.c','source_md_psg_plan.h']},reference_sha256={'hvc.h':sha(hvc_raw),'vdp_ctrl.c':sha(ctrl_raw)},
        limits=['Reconstruct every original due/value pair from prepared blocks,not just counts. All315/630run lengths1..512 include split and partial tails; random mixed/equal deadlines/u32wrap. Invalid/FULL/order/horizon errors leave count/output bytes intact.',
                'Host21024cases and2024cases per native region.12650beam-mapping cases per host/native region cover every physical line,11boundaryphases andtwoepochs against core H32/VC tables,plus atomic invalid setup/horizon checks. Actual timing/suffixes are checked separately by validate_md_psg_replay --beam and the beam sweep. No async/fullgame proof.'])
    (ROOT/'analysis/md_psg_plan_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
