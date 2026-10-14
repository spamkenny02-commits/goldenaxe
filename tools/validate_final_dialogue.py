"""Natural opening story: all six SMS final inputs, held-input edge and stable marker."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
    symbols={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    cases=[]
    for region in ['auto','pal']:
        for button in [0,8,4,5,6,7]:
            records={}
            for tag,path in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
                rows=[];patterns={};markers={};shifts=[]
                def observe(frame,raw):
                    if frame<2200:return
                    if tag=='sms':
                        rows.append((frame,raw[0x1d],int.from_bytes(raw[0xb9:0xbb],'little')))
                        if frame in [2350,2360,2370,2380]:patterns[frame]=bytes(raw[0x1100:0x1510]).hex()
                    else:
                        def data(k,n,off=0):
                            a=symbols[k]+off;return bytes(raw[(a+i)^1] for i in range(n))
                        val=lambda k:int.from_bytes(data(k,2),'big')
                        rows.append((frame,val('game_state'),val('room_id')))
                        if frame in [2350,2360,2370,2380]:
                            patterns[frame]=data('scratch',1040).hex()
                            markers[frame]=data('sms_vram',2,0x3cde).hex()
                            shifts.append(int.from_bytes(data('world_clock_shift',4),'big'))
                def vram(frame,raw):
                    if tag=='sms' and frame in [2350,2360,2370,2380]:markers[frame]=raw[0x3cde:0x3ce0].hex()
                # Keep the first confirmation held until both final waits have
                # started. Final acknowledgement must require a new press.
                inputs=PRESSES[:6]+[(2200,2330,8),(2400,2400,button)]
                with contextlib.redirect_stdout(io.StringIO()):
                    run(path,2500,ROOT/f'validation/final-dialogue-{region}-{button}-{tag}',set(),([(200,220,0)] if tag=='sms' else [])+inputs,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
                ready=next((f for f,state,room in rows if state==12 and room==0x95),None)
                assert ready is not None and ready>=2400,(region,button,tag,ready)
                assert len(set(markers.values()))==1,(tag,markers)
                assert len(set(patterns.values()))==1,(tag,'final text changes')
                records[tag]=dict(first_gameplay=ready,patterns=patterns,markers=markers,shifts=shifts)
            assert records['sms']['patterns']==records['md']['patterns'],(region,button,'bitmap')
            assert records['sms']['markers']==records['md']['markers'],(region,button,'marker',records['sms']['markers'],records['md']['markers'])
            cases.append(dict(region=region,button=button,first_gameplay={tag:r['first_gameplay'] for tag,r in records.items()},held_confirmation_does_not_dismiss_final=True,stable_final_bitmap_bytes_exact=1040,stable_final_marker_exact=True,native_clock_shift_during_final=records['md']['shifts']))
            print(region,button,'final acknowledgement verified',flush=True)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),production_roms_unmodified=True,ram_injections=False,cases=cases,full_game_ported=False,limits=['Natural opening story only; six final controller inputs in PAL/NTSC.','Initial loading timing and natural absolute world-clock phase remain different.','Inter-page blinking/clock reset and dialogue scrolling timing remain to be corrected.'])
    (ROOT/'validation/final_dialogue_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
