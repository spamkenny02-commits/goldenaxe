"""Read-only stage and IRQ costs on the unchanged retained loading cartridge."""
import contextlib
import ctypes as c
import gzip
import hashlib
import io
import json
import re
import subprocess
import sys
from actor_reference import ROOT
from run_core import run


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    clock_calls='--clock-calls' in sys.argv
    current='--current' in sys.argv
    label='timed-loading-cost'+('-current' if current else '')+('-clock-calls' if clock_calls else '')
    folder=ROOT/'validation'/label;folder.mkdir(exist_ok=True)
    archive=ROOT/'analysis/master-reader-research-v0203';manifest=json.loads((archive/'manifest.json').read_text())
    source='validation/native-planned-loading-budget-bare-precise-physical-video-fast-timed-audio/out/release/'
    for name in ['rom.bin','rom.out','symbol.txt']:
        if current:raw=(ROOT/source/name).read_bytes()
        else:
            item=manifest['compressed'][source+name];stored=(archive/item['stored']).read_bytes();assert sha(stored)==item['stored_sha256']
            raw=gzip.decompress(stored);assert sha(raw)==item['raw_sha256']
        (folder/name).write_bytes(raw)
    baseline_name='analysis/native_planned_loading_budget_bare_precise_physical_video_fast_timed_audio_report.json'
    if current:baseline_raw=(ROOT/baseline_name).read_bytes()
    elif baseline_name in manifest['files']:
        baseline_raw=(archive/baseline_name).read_bytes();assert sha(baseline_raw)==manifest['files'][baseline_name]
    else:
        item=manifest['compressed'][baseline_name];baseline_raw=gzip.decompress((archive/item['stored']).read_bytes());assert sha(baseline_raw)==item['raw_sha256']
    baseline=json.loads(baseline_raw)
    assert sha((folder/'rom.bin').read_bytes())==baseline['kernel_sha256']
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_clock_libretro.dll'
    assert sha(core.read_bytes())==baseline['observer_core_sha256']
    symbols={m[2]:int(m[1],16) for line in (folder/'symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    def address(name):
        hits={v for k,v in symbols.items() if k.split('.lto_priv.')[0]==name};assert len(hits)==1,(name,hits)
        return hits.pop()
    irq=address('source_irq_fast_timed_interrupt')
    full_disasm=subprocess.check_output([str(ROOT.parents[1]/'work/sgdk/bin/objdump.exe'),'-d',str(folder/'rom.out')],text=True)
    (folder/'disassembly.txt').write_text(full_disasm)
    # LTO inlines two of six callback sites. Observe the array-address LEA
    # common to the outlined recorder and both inline copies, not just entry.
    mark_pcs=[int(m[1],16) for line in full_disasm.splitlines() if '<gaw_graphics_marks>' in line and
              (m:=re.match(r'\s*([0-9a-fA-F]+):\s+.*\blea\b',line))]
    assert len(mark_pcs)==3,mark_pcs
    following=min(v for v in symbols.values() if v>irq)
    disasm=subprocess.check_output([str(ROOT.parents[1]/'work/sgdk/bin/objdump.exe'),'-d','--start-address='+str(irq),'--stop-address='+str(following),str(folder/'rom.out')],text=True)
    (folder/'irq-disassembly.txt').write_text(disasm)
    returns=[int(m[1],16) for line in disasm.splitlines() if (m:=re.match(r'\s*([0-9a-fA-F]+):\s+4e75\s+rts\b',line))]
    assert returns and len(returns)<20,returns
    begin,end=address('gaw_budget_begin'),address('gaw_budget_end');convert,dma=address('gaw_video_convert'),address('gaw_video_dma')
    clock_pcs={v:('block' if k.startswith('source_clock_block') else 'execute' if k.startswith('source_clock_execute') else 'repeat')
               for k,v in symbols.items() if k.startswith(('source_clock_block','source_clock_execute','source_clock_repeat.part.'))} if clock_calls else {}
    if clock_calls:
        for name in ['__mulsi3','__udivsi3','__umodsi3']:clock_pcs[address(name)]=name
    watched=[begin,end,convert,dma,*mark_pcs,irq,*returns,*clock_pcs];assert len(set(watched))==len(watched) and len(watched)<=32
    observer=c.CDLL(str(core));observer.gaw_md_config.argtypes=[c.c_uint,c.POINTER(c.c_uint)];observer.gaw_md_event_count.restype=c.c_uint;observer.gaw_md_event_data.restype=c.POINTER(c.c_uint)
    cases=json.loads((ROOT/'validation/native-planned-room-finish/cases.json').read_text());results=[]
    for reg in baseline['results']:
        region=reg['region'];lines=313 if region=='pal' else 262;events=[];previous=[0];observed={}
        counts=[[{} for _ in range(9)] for _ in range(12)];active=[-1,0,False];max_events=[0]
        observer.gaw_md_config(len(watched),(c.c_uint*len(watched))(*watched))
        def observe(frame,ram):
            count=observer.gaw_md_event_count();assert previous[0]<=count<8192
            max_events[0]=max(max_events[0],count)
            ptr=observer.gaw_md_event_data()
            for n in range(previous[0],count):
                pc=int(ptr[n*3]);stamp=(frame-1)*lines*3420+int(ptr[n*3+1]);sp=int(ptr[n*3+2])
                if pc==begin:active[0]+=1;active[1]=0;active[2]=True
                elif pc in mark_pcs:active[1]+=1
                elif pc==convert:active[1]=7
                elif pc==dma:active[1]=8
                if pc in clock_pcs:
                    if active[2]:
                        bucket=counts[active[0]][active[1]];name=clock_pcs[pc];bucket[name]=bucket.get(name,0)+1
                else:events.append([pc,stamp,sp])
                if pc==end:active[2]=False
            previous[0]=count
            if clock_calls:
                # This core API clears observer storage only, never CPU state.
                observer.gaw_md_config(len(watched),(c.c_uint*len(watched))(*watched));previous[0]=0
            def value(name,width):
                offset=address(name)&65535;return int.from_bytes(bytes(ram[(offset+i)^1] for i in range(width)),'big')
            observed.update(done=value('gaw_budget_done',2),cases=value('gaw_budget_cases',4),failures=value('gaw_budget_failures',4),frame=frame)
        with contextlib.redirect_stdout(io.StringIO()):
            run(folder/'rom.bin',60000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core=core,
                core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        assert observed.get('done') and observed['cases']==12 and not observed['failures'],observed
        (folder/(region+'-events.json')).write_text(json.dumps(events)+'\n')
        starts=[event for event in events if event[0]==begin];ends=[event for event in events if event[0]==end]
        assert len(starts)==len(ends)==12;rows=[]
        for original,start,stop in zip(reg['rows'],starts,ends):
            group=[event for event in events if start[1]<=event[1]<=stop[1]];assert group[0]==start and group[-1]==stop
            assert stop[1]-start[1]==original['measured_master'],(region,original['case'],'observer changed timing')
            checkpoints=[event for event in group if event[0] in mark_pcs];assert len(checkpoints)==6,(region,original['case'],len(checkpoints))
            cv,=[event for event in group if event[0]==convert];transfer,=[event for event in group if event[0]==dma]
            boundaries=[start,*checkpoints,cv,transfer,stop]
            intervals=[boundaries[n+1][1]-boundaries[n][1] for n in range(len(boundaries)-1)]
            entries=[event for event in group if event[0]==irq];exits=[event for event in group if event[0] in returns]
            assert len(entries)==len(exits)==cases[original['case']]['expected'][7]
            calls=[];active=None
            for pc,stamp,sp in group:
                if pc==irq:
                    assert active is None;active=(stamp,sp)
                elif pc in returns:
                    assert active is not None and sp==active[1],(region,original['case'],'IRQ return stack mismatch')
                    calls.append(dict(begin_master=active[0]-start[1],end_master=stamp-start[1],duration_master=stamp-active[0]));active=None
            assert active is None
            irq_by_interval=[sum(max(0,min(call['end_master'],boundaries[n+1][1]-start[1])-max(call['begin_master'],boundaries[n][1]-start[1])) for call in calls) for n in range(len(intervals))]
            rows.append(dict(case=original['case'],room=original['room'],whole_master=stop[1]-start[1],source_master=original['source_master'],
                intervals_master=intervals,irq_master=irq_by_interval,foreground_master=[a-b for a,b in zip(intervals,irq_by_interval)],irq_calls=calls))
            if clock_calls:rows[-1]['outlined_clock_calls']=counts[len(rows)-1]
        (folder/(region+'-events.json')).write_text(json.dumps(events)+'\n')
        results.append(dict(region=region,rows=rows,observed=observed,max_observer_events=max_events[0]))
        totals=[sum(row['intervals_master'][n] for row in rows) for n in range(9)];irq_totals=[sum(row['irq_master'][n] for row in rows) for n in range(9)]
        print(region,'interval totals',totals,'IRQ totals',irq_totals,flush=True)
    report=dict(current=current,kernel_sha256=baseline['kernel_sha256'],observer_core_sha256=sha(core.read_bytes()),baseline_report_sha256=sha(baseline_raw),
        intervals=['entry_to1706','1706_to170e','170e_to1720','1720_to1733','1733_to1748','1748_to24b9','24b9_to_video_convert','video_conversion','physical_transfer'],
        checkpoint_record_pcs=mark_pcs,irq_entry_pc=irq,irq_return_pcs=returns,clock_entry_pcs=clock_pcs,results=results,
        limits=['Unmodified retained kernel with read-only PC observations. Every whole-chain duration equals the previous exact measurement; all six graphics callbacks and every source IRQ are paired,including return SP.',
                'IRQ duration stops before final RTS (its execution is attributed to foreground); native hardware interrupts inside this interval are included. Foreground is the residual wall cost,not a statistical instruction profile.',
                'Only source-checked24 retained loading contexts. Six checkpoint record LEAs (outlined callback and two LTO-inlined copies) split near original1706/170E/1720/1733/1748/24B9 with recorder bookkeeping included. The residual includes graphics return,map,HUD,finish and their IRQs. No physical PSG pacing or full gameplay proof.'])
    if clock_calls:report['limits'].append('Outlined block/execute/repeat call counts only; LTO-inline clock operations are not counted. Observer storage is drained/reset every physical frame and overflow is rejected. This changes host observation only; exact whole-chain durations remain required.')
    (ROOT/('analysis/timed_loading_'+('clock_calls' if clock_calls else 'cost')+('_current' if current else '')+'_report.json')).write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
