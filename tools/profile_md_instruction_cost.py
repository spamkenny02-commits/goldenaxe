"""Attribute unmodified loading wall cycles to64-byte instruction PC bins."""
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
    current='--current' in sys.argv
    folder=ROOT/('validation/md-instruction-cost-current' if current else 'validation/md-instruction-cost');folder.mkdir(exist_ok=True)
    archive=ROOT/'analysis/native-divu-loading-v0203';manifest=json.loads((archive/'manifest.json').read_text())
    def read(name):
        if name in manifest['files']:
            raw=(archive/name).read_bytes();assert sha(raw)==manifest['files'][name]
        else:
            item=manifest['compressed'][name];stored=(archive/item['stored']).read_bytes();assert sha(stored)==item['stored_sha256']
            raw=gzip.decompress(stored);assert sha(raw)==item['raw_sha256']
        return raw
    base='validation/native-planned-loading-budget-bare-precise-physical-video-fast-timed-audio/out/release/'
    for name in ['rom.bin','rom.out','symbol.txt']:(folder/name).write_bytes((ROOT/base/name).read_bytes() if current else read(base+name))
    report_name='analysis/native_planned_loading_budget_bare_precise_physical_video_fast_timed_audio_report.json'
    budget_raw=(ROOT/report_name).read_bytes() if current else read(report_name);budget=json.loads(budget_raw)
    assert sha((folder/'rom.bin').read_bytes())==budget['kernel_sha256']
    symbols={m[2]:int(m[1],16) for line in (folder/'symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    begin,end=symbols['gaw_budget_begin'],symbols['gaw_budget_end']
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_cost_libretro.dll';observer=c.CDLL(str(core))
    observer.gaw_cost_config.argtypes=[c.c_uint,c.c_uint,c.c_uint];observer.gaw_cost_config.restype=None
    observer.gaw_cost_next_frame.restype=None;observer.gaw_cost_cases.restype=observer.gaw_cost_errors.restype=c.c_uint
    observer.gaw_cost_master_data.restype=c.POINTER(c.c_ulonglong);observer.gaw_cost_instruction_data.restype=c.POINTER(c.c_uint)
    observer.gaw_md_config.argtypes=[c.c_uint,c.POINTER(c.c_uint)];observer.gaw_md_event_count.restype=c.c_uint;observer.gaw_md_event_data.restype=c.POINTER(c.c_uint)
    results=[];functions=sorted((v,k) for k,v in symbols.items() if v<0x40000)
    for reg in budget['results']:
        region=reg['region'];period=(313 if region=='pal' else 262)*3420;events=[];previous=[0];observed={}
        observer.gaw_md_config(2,(c.c_uint*2)(begin,end));observer.gaw_cost_config(begin,end,period)
        def observe(frame,ram):
            count=observer.gaw_md_event_count();assert count<8192;ptr=observer.gaw_md_event_data()
            for n in range(previous[0],count):events.append([int(ptr[n*3]),(frame-1)*period+int(ptr[n*3+1])])
            previous[0]=count
            def value(name,width):return int.from_bytes(bytes(ram[((symbols[name]&65535)+i)^1] for i in range(width)),'big')
            observed.update(frame=frame,done=value('gaw_budget_done',2),cases=value('gaw_budget_cases',4),failures=value('gaw_budget_failures',4))
            observer.gaw_cost_next_frame()
        with contextlib.redirect_stdout(io.StringIO()):
            run(folder/'rom.bin',60000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core=core,
                core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        assert observed.get('done') and observed['cases']==12 and not observed['failures'],observed
        assert observer.gaw_cost_cases()==12 and not observer.gaw_cost_errors()
        assert len(events)==24;master=observer.gaw_cost_master_data();instructions=observer.gaw_cost_instruction_data();rows=[]
        for n,expected in enumerate(reg['rows']):
            a,b=events[n*2:n*2+2];assert a[0]==begin and b[0]==end and b[1]-a[1]==expected['measured_master']
            bins=[dict(pc=k*64,master=int(master[n*4097+k]),instructions=int(instructions[n*4097+k])) for k in range(4097) if master[n*4097+k] or instructions[n*4097+k]]
            assert sum(item['master'] for item in bins)==expected['measured_master'],(region,n,'histogram lost or invented cycles')
            rows.append(dict(case=expected['case'],room=expected['room'],whole_master=expected['measured_master'],bins=bins))
        totals={}
        for row in rows:
            for item in row['bins']:
                pair=totals.setdefault(item['pc'],[0,0]);pair[0]+=item['master'];pair[1]+=item['instructions']
        hottest=[]
        for pc,(cost,count) in sorted(totals.items(),key=lambda item:item[1][0],reverse=True):
            preceding=[(v,k) for v,k in functions if v<=pc]
            owner=preceding[-1] if preceding else (0,'unknown')
            hottest.append(dict(pc=pc,master=cost,instructions=count,nearest_symbol=owner[1],symbol_offset=pc-owner[0]))
        results.append(dict(region=region,rows=rows,hottest=hottest,observed=observed))
        print(region,'total master',sum(x['whole_master'] for x in rows),'top bins',hottest[:8],flush=True)
    assembly=subprocess.check_output([str(ROOT.parents[1]/'work/sgdk/bin/objdump.exe'),'-d',str(folder/'rom.out')],text=True);(folder/'disassembly.txt').write_text(assembly)
    report=dict(current=current,kernel_sha256=budget['kernel_sha256'],observer_core_sha256=sha(core.read_bytes()),budget_report_sha256=sha(budget_raw),bin_bytes=64,results=results,
        limits=['Host-only observation attributes the next instruction-entry cycle delta to the preceding PC. Per-frame cycle origin is adjusted explicitly. Histogram sum equals every exact baseline whole-chain duration and diagnostic endpoint checks still pass.',
                '64-byte bins can straddle functions. nearest_symbol is an address hint only; use disassembly for attribution. Bin0x40000 aggregates all PCs outside0..0x3ffff. Physical IRQ acceptance and DMA waits are wall time attributed to the preceding observed PC. This is not intrinsic opcode timing.',
                '24 source-checked loading contexts only. Does not establish physical PSG deadline pacing,global boot alignment or full gameplay fidelity.'])
    (ROOT/('analysis/md_loading_instruction_cost_current_report.json' if current else 'analysis/md_loading_instruction_cost_report.json')).write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
