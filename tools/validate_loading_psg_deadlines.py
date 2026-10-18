"""Compare physical batch readiness with original SMS per-byte PSG deadlines.

Original8000 is replayed under DI with each retained loading-IRQ reader input.
This establishes reader-relative IO timestamps, not a global playback clock.
"""
import contextlib
import ctypes as c
import hashlib
import io
import json
import os
import struct
import subprocess
from actor_reference import ROOT
from audio_irq_wrapper_cost import audio_irq_wrapper_cost
from run_core import run
from validate_native_room_finish import MODULES,WRAPPER

CAPTURE=r'''
#include "source_audio_fast.h"
static u8 before[1024][400],after[1024][400],bytes[1024][512];
static u32 info[1024][8];static u16 batches[1024][32],samples;
unsigned capture_count(void) {return samples;}
const u8 *capture_before(unsigned n) {return before[n];}
const u8 *capture_after(unsigned n) {return after[n];}
const u8 *capture_bytes(unsigned n) {return bytes[n];}
const u32 *capture_info(unsigned n) {return info[n];}
const u16 *capture_batches(unsigned n) {return batches[n];}
void capture_reset(void) {samples=0;}
static void capture_sink(void *unused,const u8 *writes,u16 count)
{
 u16 n;(void)unused;
 if(info[samples][6]+count>512 || info[samples][7]>=32) return;
 batches[samples][info[samples][7]++]=count;
 for(n=0;n<count;n++) bytes[samples][info[samples][6]++]=writes[n];
}
u8 capture_reader(u8 *state,const u8 *low,u16 low_bytes,const u8 *bank,u16 *de,
 SourceClockWork *work,SourceAudioReaderStatus *out,SourceAudioReaderSink sink,void *user)
{
 u16 n;u8 ok;(void)sink;(void)user;if(samples>=1024) return 0;
 for(n=0;n<400;n++) before[samples][n]=state[n];
 info[samples][0]=*de;info[samples][6]=info[samples][7]=0;
 ok=source_audio_reader_stream_fast(state,low,low_bytes,bank,de,work,out,capture_sink,0);
 for(n=0;n<400;n++) after[samples][n]=state[n];
 info[samples][1]=*de;info[samples][2]=work->tstates;info[samples][3]=work->fetches;
 return ok;
}
static void capture_irq(const SourceIrqContext *ctx,const SourceClockIrq *entry)
{
 u16 n;u32 prefix=0;
 if(ctx->last_irq.stages[SOURCE_IRQ_SAT64].tstates)
 {
  for(n=0;n<SOURCE_IRQ_AUDIO;n++) prefix+=ctx->last_irq.stages[n].tstates;
  prefix+=17;
 }
 else prefix=AUDIO_ONLY_PREFIX;
 info[samples][4]=entry->entry_elapsed;info[samples][5]=prefix;samples++;
}
'''

def inputs(base,cases):
    sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    cost=audio_irq_wrapper_cost(False)
    prefix=cost['gate']+cost['save_and_map']+cost['audio_call']
    wrapper=WRAPPER.replace('typedef struct {u32 count',CAPTURE.replace('AUDIO_ONLY_PREFIX',str(prefix))+'\ntypedef struct {u32 count')
    wrapper=wrapper.replace('LoadTrace *p=(LoadTrace *)context;u32 *row;', 'LoadTrace *p=(LoadTrace *)context;u32 *row;capture_irq(p->irq,entry);')
    # Use the same planned path as the measured 68000 producer.
    wrapper=wrapper.replace('#include "source_room_finish.h"','#include "source_room_finish.h"\n#include "source_pattern_plan_generated.h"')
    wrapper=wrapper.replace('source_graphics_load_class0(&clock,&ctx,patterns,bank2,bank11,&data,point,&log)', 'source_graphics_load_class0_planned(&clock,&ctx,patterns,bank2,bank11,&data,point,&log,&gaw_class0_pattern_plan)')
    (base/'capture.c').write_text(wrapper)
    context=(ROOT/'megadrive/src/source_irq_context.c').read_text()
    prototype='u8 capture_reader(u8 *,const u8 *,u16,const u8 *,u16 *,SourceClockWork *,SourceAudioReaderStatus *,SourceAudioReaderSink,void *);\n'
    context=context.replace('#include "source_audio_fast.h"','#include "source_audio_fast.h"\n'+prototype).replace('source_audio_reader_stream_fast(', 'capture_reader(')
    (base/'context.c').write_text(context)
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(base/'capture.c'),str(base/'context.c')]
    args += [str(ROOT/'megadrive/src'/(name+'.c')) for name in MODULES if name!='source_irq_context']
    args += ['-o',str(base/'capture.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True);(base/'compile.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(base/'capture.dll'));fn=dll.room_finish_case
    fn.argtypes=[c.POINTER(c.c_uint32),c.c_uint8,*([c.POINTER(c.c_uint8)]*4),c.c_uint16,*([c.POINTER(c.c_uint8)]*6),*([c.POINTER(c.c_uint32)]*3),c.POINTER(c.c_uint8)]
    fn.restype=c.c_uint8
    for name,typ in [('capture_before',c.c_uint8),('capture_after',c.c_uint8),('capture_bytes',c.c_uint8),('capture_info',c.c_uint32),('capture_batches',c.c_uint16)]:
        getattr(dll,name).argtypes=[c.c_uint];getattr(dll,name).restype=c.POINTER(typ)
    image=(ROOT/'input/original.sms').read_bytes()
    def data(raw):return (c.c_uint8*len(raw)).from_buffer_copy(bytes(raw))
    result=[]
    for row,case in enumerate(cases):
        dll.capture_reset();out=(c.c_uint32*41)();events=(c.c_uint32*384)();points=(c.c_uint32*288)();states=(c.c_uint8*11776)()
        assert fn((c.c_uint32*12)(*case['phase']),case['refresh'],data(case['ram']),data(case['audio']),data(image[:32768]),data(image[0x18000:0x1c000]),case['room'],data(image[(8+(case['room']>>7))*16384:(9+(case['room']>>7))*16384]),data(image[0x3c010:]),data(image[0x8000:0xc000]),data(image[0x2c000:0x30000]),data(image[0x10000:0x14000]),data(case['hud']),out,events,points,states)
        assert list(out)==case['expected'] and list(events[:out[7]*6])==case['events']
        assert dll.capture_count()==case['expected'][7]
        for irq in range(dll.capture_count()):
            values=list(dll.capture_info(irq)[:8]);de,de_after,t,m,entry,prefix,count,batch_count=values
            assert sum(dll.capture_batches(irq)[:batch_count])==count
            result.append(dict(case=row,irq=irq,before=list(dll.capture_before(irq)[:400]),after=list(dll.capture_after(irq)[:400]),de=de,de_after=de_after,tstates=t,fetches=m,source_reader_entry_master=entry+prefix*15,writes=list(dll.capture_bytes(irq)[:count]),batches=list(dll.capture_batches(irq)[:batch_count])))
    (base/'inputs.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
    return result

def fixture(base,records):
    original=(ROOT/'input/original.sms').read_bytes();image=bytearray(original)+bytearray(0x100000-len(original))
    code=bytearray();labels={};fix=[]
    def emit(h):code.extend(bytes.fromhex(h))
    def label(name):labels[name]=0x3100+len(code)
    def jump(op,name):emit(op);fix.append((len(code),name));emit('0000')
    emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf2100802206c03e203208c0')
    label('case');emit('3a08c032ffff2a06c01100de019001edb02a06c0119001195e23563e0632ffffcd00302a06c011000219cb74')
    jump('ca','pointer');emit('2100803a08c03c3208c0')
    label('pointer');emit('2206c02a00c0232200c001'+len(records).to_bytes(2,'little').hex()+'b7ed42')
    jump('c2','case');emit('3e013204c0');label('done');jump('c3','done')
    for pos,name in fix:code[pos:pos+2]=labels[name].to_bytes(2,'little')
    image[:3]=bytes.fromhex('c30031');image[0x3000:0x3004]=bytes.fromhex('cd0080c9');image[0x3100:0x3100+len(code)]=code
    table=b''.join(bytes(record['before'])+record['de'].to_bytes(2,'little')+bytes(110) for record in records)
    image[0x80000:0x80000+len(table)]=table
    assert image[0x18000:0x1c000]==original[0x18000:0x1c000] and image[0x4000:0x8000]==original[0x4000:0x8000]
    path=base/'source.sms';path.write_bytes(image);return path

def main():
    base=ROOT/'validation/loading-psg-deadlines';base.mkdir(exist_ok=True)
    source_cases=ROOT/'validation/native-planned-room-finish/cases.json';cases=json.loads(source_cases.read_text())
    records=inputs(base,cases);cartridge=fixture(base,records)
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_audioports_libretro.dll';dll=c.CDLL(str(core))
    for name in ['gaw_port_samples','gaw_port_write_samples']:getattr(dll,name).restype=c.c_uint
    for name in ['gaw_port_call_data','gaw_port_write_data']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
    measured=json.loads((ROOT/'analysis/native_planned_loading_budget_bare_precise_physical_video_audio_readiness_report.json').read_text())
    regions=[];relative_io=None
    for region in ['auto','pal']:
        dll.gaw_timing_reset();done=[]
        def observe(frame,ram):
            if ram[4]:done.append(frame)
        with contextlib.redirect_stdout(io.StringIO()):
            run(cartridge,10000,base/region,set(),[],skip_intro=False,core=core,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(done))
        assert done and dll.gaw_port_samples()==len(records) and dll.gaw_port_write_samples()<32768
        calls=c.string_at(dll.gaw_port_call_data(),len(records)*824)
        ports=c.string_at(dll.gaw_port_write_data(),dll.gaw_port_write_samples()*16)
        (base/(region+'-calls.bin')).write_bytes(calls);(base/(region+'-ports.bin')).write_bytes(ports)
        grouped=[[] for _ in records]
        for pos in range(0,len(ports),16):
            time,index,value=struct.unpack_from('<QII',ports,pos);grouped[index].append((time,value))
        rows=[];relative=[];physical={x['case']:x for x in next(r for r in measured['results'] if r['region']==region)['rows']}
        for n,record in enumerate(records):
            begin,end,de,de_after=struct.unpack_from('<2Q2I',calls,n*824)
            assert calls[n*824+24:n*824+424]==bytes(record['before']) and calls[n*824+424:n*824+824]==bytes(record['after']),(region,n,'reader state')
            assert (end-begin,de,de_after)==(record['tstates']*15,record['de'],record['de_after']),(region,n,'source reader result')
            writes=grouped[n];assert [value for time,value in writes]==record['writes'],(region,n,'PSG bytes')
            assert all(begin<=time<=end for time,value in writes)
            assert all(a[0]<=b[0] for a,b in zip(writes,writes[1:]))
            relative.append([(time-begin,value) for time,value in writes])
            deadlines=[record['source_reader_entry_master']+time-begin for time,value in writes]
            row=dict(case=record['case'],irq=record['irq'],source_psg_master=deadlines,psg_bytes=len(writes))
            if record['case'] in physical:
                ready=physical[record['case']]['audio_readiness'][record['irq']]['batch_ready_master']
                assert len(ready)==len(record['batches'])
                per_byte=[stamp for stamp,count in zip(ready,record['batches']) for _ in range(count)]
                assert len(per_byte)==len(deadlines)
                row['readiness_margin_master']=[deadline-stamp for deadline,stamp in zip(deadlines,per_byte)]
            rows.append(row)
        if relative_io is None:relative_io=relative
        else:assert relative==relative_io,'Reader-relative IO differs by physical region'
        margins=[margin for row in rows for margin in row.get('readiness_margin_master',[])]
        regions.append(dict(region=region,frames=done[0],reader_calls=len(records),source_psg_writes=len(ports)//16,compared_bytes=len(margins),minimum_margin_master=min(margins),late_bytes=sum(x<0 for x in margins),calls_sha256=hashlib.sha256(calls).hexdigest(),ports_sha256=hashlib.sha256(ports).hexdigest(),rows=rows))
        print(region,len(records),'original readers;',len(margins),'matching-region byte deadlines;',sum(x<0 for x in margins),'late;',min(margins),'master minimum margin',flush=True)
    report=dict(results=regions,source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),fixture_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases_sha256=hashlib.sha256(source_cases.read_bytes()).hexdigest(),producer_report_sha256=hashlib.sha256((ROOT/'analysis/native_planned_loading_budget_bare_precise_physical_video_audio_readiness_report.json').read_bytes()).hexdigest(),limits=['Original bank6 reader replay under DI with each native loading IRQ input; all400 state bytes,DE,cost and emitted PSG byte order verified. Both physical regions replay the same492 contexts. Reader-relative timestamps come from the exact cycles passed to the emulated PSG port.','Reader-entry offset inside IRQ comes from the existing source-verified IRQ model, not a new full-loader source replay. Physical producer epochs are budget-begin relative and include readiness instrumentation. No global boot/source phase alignment, hardware pacing,queue delivery,PSG chip equivalence or audible waveform proof.','Batch readiness is observed at sink function entry. Actual consumer copy/enqueue/port-write overhead remains to be budgeted; nonnegative margins only establish producer readiness for these retained contexts.'])
    (ROOT/'analysis/loading_psg_deadlines_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
