"""Observe production CPU spans during the controlled dense screen spell."""
import contextlib,ctypes as c,hashlib,io,json,re,subprocess,sys
from pathlib import Path
import validate_screen_spell as probe
from run_core import ROOT

def main():
    tag=sys.argv[1];sy={m[2]:int(m[1],16) for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
    watched={};functions={}
    for prefix in ['source_audio_reader_stream.','source_sprite_scene_tstates.','prepare_world_sms_sprite_overflow.','world_vint.']:
        for name,pc in sy.items():
            if not name.startswith(prefix):continue
            dump=subprocess.check_output([str(ROOT.parents[1]/'work/sgdk/bin/objdump.exe'),'-d','--disassemble='+name,str(ROOT/'megadrive/out/release/rom.out')],text=True)
            returns=[int(m[1],16) for l in dump.splitlines() if(m:=re.match(r'\s*([0-9a-fA-F]+):.*\trts\s*$',l))]
            if not returns:continue
            functions[name]=dict(entry=pc,returns=returns);watched[pc]=name+':entry'
            for p in returns:watched[p]=name+':return'
    assert len(watched)<=32
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_clock_libretro.dll';dll=c.CDLL(str(core));dll.gaw_md_config.argtypes=[c.c_uint,c.POINTER(c.c_uint)];dll.gaw_md_event_count.restype=c.c_uint;dll.gaw_md_event_data.restype=c.POINTER(c.c_uint)
    events=[];previous=0;pcs=(c.c_uint*len(watched))(*watched);original=probe.run
    def run(rom,*args,**kw):
        nonlocal previous
        if Path(rom).suffix=='.sms':return original(rom,*args,**kw)
        old=kw['ram_observer'];dll.gaw_md_config(len(watched),pcs)
        def observe(f,r):
            nonlocal previous
            old(f,r)
            if f<2999:dll.gaw_md_config(len(watched),pcs);previous=0;return
            count=dll.gaw_md_event_count();p=dll.gaw_md_event_data();assert count<8192
            for n in range(previous,count):
                pc,cycles,sp=[int(p[n*3+k]) for k in range(3)];events.append(dict(frame=f,event=watched[pc],master=(f-1)*262*3420+cycles,sp=sp))
            previous=count
        kw['core']=core;kw['ram_observer']=observe
        return original(rom,*args,**kw)
    probe.run=run;sys.argv=['probe','--tag',tag,'--level','2','--actors'];probe.main()
    pending={};spans=[]
    for e in events:
        name,phase=e['event'].rsplit(':',1);key=name,e['sp']
        if phase=='entry':pending[key]=e
        elif key in pending:
            a=pending.pop(key)
            if 3004<=a['frame']<=3083:spans.append(dict(function=name,frame=a['frame'],master=e['master']-a['master']))
    summary={}
    for s in spans:
        name=s['function'];summary.setdefault(name,[]).append(s['master']/7)
    summary={n:dict(count=len(v),min=min(v),mean=sum(v)/len(v),max=max(v)) for n,v in summary.items()}
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),read_only_cpu_observer=True,controlled_fixture=True,functions=functions,spans=spans,summary_cycles_68k=summary)
    (ROOT/f'analysis/screen_spell_{tag}_cpu_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(summary)
if __name__=='__main__':main()
