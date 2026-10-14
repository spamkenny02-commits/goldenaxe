"""Read-only source PC/cycle and live hero traces around key-door redraw."""
import ctypes as c
import hashlib,json,re,sys
import validate_key_door_gameplay as gameplay
from run_core import ROOT


def main():
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_key_timing_libretro.dll'
    dll=c.CDLL(str(core));dll.gaw_timing_events.restype=c.POINTER(c.c_uint64);dll.gaw_timing_count.restype=c.c_uint
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in
        (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
        if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    original_run=gameplay.run;events=[];traces={};previous=0
    def observed_run(*args,**kwargs):
        tag='sms' if args[0].suffix=='.sms' else 'md'
        observer=kwargs['ram_observer'];traces[tag]=[]
        if tag=='sms':kwargs['core']=core
        def observe(frame,raw):
            nonlocal previous
            observer(frame,raw)
            if tag=='sms':
                if frame==3390:dll.gaw_timing_reset();previous=0
                if frame>3390:
                    count=dll.gaw_timing_count();pointer=dll.gaw_timing_events()
                    for i in range(previous,count):
                        pc,cycles,irq,room,clock,hl,de,bc=[pointer[i*8+j] for j in range(8)]
                        events.append(dict(frame=frame,pc=pc,master_cycles=cycles,irq_master_cycles=irq,room=room,clock=clock,hl=hl,de=de,bc=bc))
                    previous=count
            if 3408<=frame<=3530:
                if tag=='sms':
                    word=lambda a:int.from_bytes(raw[a:a+2],'little')
                    state=dict(x=word(0x312),y=word(0x310),counter=raw[0x304],room=word(0xb9),state=raw[0x1d],clock=raw[0x2f])
                else:
                    def word(name):
                        a=sy[name];return int.from_bytes(bytes(raw[(a+i)^1] for i in range(2)),'big')
                    state=dict(x=word('hero_x'),y=word('hero_y'),counter=word('hero_counter'),room=word('room_id'),state=word('game_state'))
                traces[tag].append(dict(frame=frame,**state))
        kwargs['ram_observer']=observe
        return original_run(*args,**kwargs)
    gameplay.run=observed_run
    if '--first' not in sys.argv:sys.argv.append('--first')
    gameplay.main()
    start=next(e for e in events if e['pc']==0x5e90)
    end=next(e for e in events if e['pc']==0x5e96 and e['master_cycles']>start['master_cycles'])
    interval=[e for e in events if start['master_cycles']<=e['master_cycles']<=end['master_cycles']]
    markers=[e for e in interval if e['pc'] in [0x5e90,0x5e93,0x1de2,0x2279,0x1de5,0x1e4e,0x1de8,0x229c,0x0b95,0x0bb3,0x22bf,0x1deb,0x1e1f,0x5e96]]
    phases=[]
    for a,b in zip(markers,markers[1:]):
        total=(b['master_cycles']-a['master_cycles'])//15;irq=(b['irq_master_cycles']-a['irq_master_cycles'])//15
        phases.append(dict(start_pc=hex(a['pc']),end_pc=hex(b['pc']),start_frame=a['frame'],end_frame=b['frame'],tstates=total,irq_tstates=irq,foreground_tstates=total-irq))
    suffix='-pal' if '--pal' in sys.argv else ''
    direction=next((a.split('=',1)[1] for a in sys.argv if a.startswith('--direction=')),'up')
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),
                core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),direction=direction,region='pal' if suffix else 'auto',
                redraw_start_frame=start['frame'],redraw_end_frame=end['frame'],
                redraw_tstates=(end['master_cycles']-start['master_cycles'])//15,phases=phases,hero_traces=traces,
                read_only_instruction_cycle_hook=True,source_rom_unmodified=True)
    (ROOT/f'analysis/key_redraw_profile-{direction}{suffix}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(direction,suffix,'redraw',start['frame'],end['frame'],report['redraw_tstates'],'T')


if __name__=='__main__':main()
