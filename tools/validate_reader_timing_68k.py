"""Compiled8000 timed stream: full states and source-observed event lists."""
import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from actor_reference import ROOT
from run_core import run
from validate_reader_timing import MODULES

def main():
    master='--master' in sys.argv;fast='--fast' in sys.argv or master;modules=MODULES+(['source_audio_fast_timed'] if fast else [])+(['source_audio_reader_master'] if master else [])
    data_base=ROOT/'validation/reader-timing';base=ROOT/('validation/master-reader-timing' if master else 'validation/fast-reader-timing' if fast else 'validation/reader-timing');suites=[s for p in ['cases.json','extension-cases.json'] for s in json.loads((ROOT/'validation/native-audio-reader'/p).read_text())];events=json.loads((data_base/'events.json').read_text());rows=[];lows=[]
    for index,(suite,observed) in enumerate(zip(suites,events)):
        image=(ROOT/suite['fixture']).read_bytes();assert hashlib.sha256(image).hexdigest()==suite['fixture_sha256']
        assert suite['kind']==observed['kind'] and len(suite['cases'])==len(observed['events'])
        lows.append(image[:32768]);rows.extend((index,row,event) for row,event in zip(suite['cases'],observed['events']))
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']=str(sdk/'bin')+';'+env['PATH'];bank=(ROOT/'input/original.sms').read_bytes()[0x18000:0x1c000];results=[]
    for part,start in enumerate(range(0,len(rows),3500)):
        selected=rows[start:start+3500];kernel=base/f'kernel-{part}';src=kernel/'src';src.mkdir(parents=True,exist_ok=True);max_events=max(1,max(len(event['writes']) for _,_,event in selected));capacity=1
        while capacity<max_events:capacity*=2
        lines=['static const u8 low[][32768]={'+','.join('{'+','.join(map(str,raw))+'}' for raw in lows)+'};','static const u8 bank6[]={'+','.join(map(str,bank))+'};',f'#define MAX_EVENTS {max_events}\n#define QUEUE_CAPACITY {capacity}',f'typedef struct {{u8 suite,track,before[400],after[400],writes[{max_events}];u16 de_in,de,count;u32 tstates,fetches,times[{max_events}];}} ReaderCase;','static const ReaderCase cases[]={']
        for index,row,event in selected:
            lines.append('{'+str(index)+','+str(event['track'])+',{'+','.join(map(str,row['before']))+'},{'+','.join(map(str,row['after']))+'},{'+','.join(map(str,event['writes']))+'},'+str(row['de_in'])+','+str(row['de'])+','+str(len(event['writes']))+','+str(row['tstates'])+'UL,'+str(row['fetches'])+'UL,{'+','.join(str(t)+'UL' for t in event['times'])+'}},')
        lines.append('};');(src/'expected.h').write_text('\n'.join(lines)+'\n')
        for name in modules+['source_psg_queue']:(src/(name+'.c')).write_text('#include "../../../../megadrive/src/'+name+'.c"\n')
        (src/'main.c').write_text('''#include <genesis.h>
#include "../../../../megadrive/src/source_audio_timed.h"
#include "expected.h"
volatile u32 gaw_reader_cases,gaw_reader_failures,gaw_reader_writes;volatile u16 gaw_reader_done;
static const ReaderCase *current;static u16 position;static u32 epoch;
static SourcePsgQueue queue;static SourcePsgEvent storage[QUEUE_CAPACITY],pending[MAX_EVENTS];
static void sink(void *unused,const u8 *writes,const u32 *times,u16 count)
{
 u16 n;SourcePsgEvent delivered;(void)unused;
 if(count>MAX_EVENTS) {gaw_reader_failures++;return;}
 for(n=0;n<count;n++)
 {
  if(position>=current->count || writes[n]!=current->writes[position] || times[n]!=current->times[position]) gaw_reader_failures++;
  position++;pending[n].due=epoch+times[n]*15;pending[n].value=writes[n];
 }
 if(source_psg_queue_push(&queue,pending,count)!=SOURCE_PSG_QUEUE_OK) gaw_reader_failures++;
 for(n=0;n<count;n++)
 {
  if(source_psg_queue_take(&queue,pending[n].due-1,&delivered)!=SOURCE_PSG_QUEUE_WAIT) gaw_reader_failures++;
  if(source_psg_queue_take(&queue,pending[n].due,&delivered)!=SOURCE_PSG_QUEUE_OK || delivered.value!=pending[n].value || delivered.due!=pending[n].due) gaw_reader_failures++;
  gaw_reader_writes++;
 }
}
int main(bool hard_reset)
{
 u16 n,de;u32 row;u8 state[400];SourceClockWork work;SourceAudioReaderStatus status;SourcePsgEvent empty;VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  current=cases+row;de=current->de_in;position=0;epoch=0xffff0000UL+row*225;
  for(n=0;n<400;n++) state[n]=current->before[n];source_psg_queue_init(&queue,storage,QUEUE_CAPACITY);
  if(!source_audio_reader_stream_timed(state,low[current->suite],32768,bank6,&de,&work,&status,sink,0) || status.error || status.track!=current->track || status.count!=current->count || position!=current->count || de!=current->de || work.tstates!=current->tstates || work.fetches!=current->fetches) gaw_reader_failures++;
  for(n=0;n<400;n++) if(state[n]!=current->after[n]) gaw_reader_failures++;
  if(source_psg_queue_take(&queue,epoch,&empty)!=SOURCE_PSG_QUEUE_EMPTY) gaw_reader_failures++;
  gaw_reader_cases++;
 }
 gaw_reader_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
'''.replace('source_audio_reader_stream_timed(','source_audio_reader_stream_fast_timed(' if fast else 'source_audio_reader_stream_timed('))
        if master:
            main=src/'main.c';body=main.read_text().replace('source_audio_reader_stream_fast_timed(','source_audio_reader_stream_fast_master(')
            body=body.replace('&status,sink,0','&status,epoch,sink,0').replace('times[n]!=current->times[position]','times[n]!=(u32)(epoch+current->times[position]*15)')
            body=body.replace('pending[n].due=epoch+times[n]*15;','pending[n].due=times[n];');main.write_text(body)
        path=str(sdk).replace('\\','/');unix='/'+path[0].lower()+path[2:]
        # Keep GCC/MSYS temporary paths absolute with forward slashes. A
        # backslash TEMP can become a relative c/Users path in nested make.
        temporary=kernel/'compiler-tmp';temporary.mkdir(exist_ok=True)
        for key in ['TMPDIR','TMP','TEMP']:env[key]=temporary.resolve().as_posix()
        built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=kernel,env=env,capture_output=True,text=True);(kernel/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2000:]
        sy={m[2]:int(m[1],16)&65535 for line in (kernel/'out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};cartridge=kernel/'out/release/rom.bin';assert cartridge.stat().st_size<=4*1024*1024
        for region in ['auto','pal']:
            observed={}
            def observe(frame,ram):
                def value(name,width):return int.from_bytes(bytes(ram[(sy[name]+i)^1] for i in range(width)),'big')
                observed.update(frame=frame,done=value('gaw_reader_done',2),cases=value('gaw_reader_cases',4),writes=value('gaw_reader_writes',4),failures=value('gaw_reader_failures',4))
            with contextlib.redirect_stdout(io.StringIO()):run(cartridge,30000,kernel/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
            assert observed.get('done') and observed['cases']==len(selected) and not observed['failures'] and observed['writes']==sum(len(event['writes']) for _,_,event in selected),(part,region,observed)
            results.append(dict(part=part,region=region,max_events=max_events,queue_capacity=capacity,kernel_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),**observed));print(results[-1],flush=True)
    report=dict(fast=fast,fused_master=master,results=results,sources={name:hashlib.sha256((ROOT/'megadrive/src'/(name+'.c')).read_bytes()).hexdigest() for name in modules},events_sha256=hashlib.sha256((data_base/'events.json').read_bytes()).hexdigest(),limits=['Compiled68000 full8000 stream compares all400 bytes,T/M1,DE/status/track and source-observed byte/timestamp lists. Bounded diagnostic cartridges below4MiB; queue checks early WAIT and exact supplied logical due time, with32-bit epoch wrap.','Temporary stream buffers are copied synchronously by the test sink. No physical pacing clock,live IRQ PSG consumer,global source phase,production CPU budget or full-game fidelity proof.'])
    (ROOT/('analysis/master_reader_timing_68k_report.json' if master else 'analysis/fast_reader_timing_68k_report.json' if fast else 'analysis/reader_timing_68k_report.json')).write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
